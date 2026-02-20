import { grappleApi } from '../api/client';
import { logger } from './logger';

/**
 * Fire-and-forget call to generate a new insight.
 * If sessionId is provided, generates a post_session insight;
 * otherwise generates a weekly insight.
 */
export function triggerInsightRefresh(sessionId?: number): void {
  const data = sessionId
    ? { insight_type: 'post_session', session_id: sessionId }
    : { insight_type: 'weekly' };

  grappleApi.generateInsight(data).catch((err) => {
    logger.debug('Insight generation fire-and-forget failed', err);
  });
}

/**
 * Check if the latest insight is stale (>12h old) or missing,
 * and regenerate if so.
 */
export function refreshIfStale(): void {
  grappleApi
    .getInsights({ limit: 1 })
    .then((res) => {
      const insights = res.data?.insights || [];
      if (insights.length === 0) {
        triggerInsightRefresh();
        return;
      }
      const createdAt = new Date(insights[0].created_at);
      const hoursAgo = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60);
      if (hoursAgo > 12) {
        triggerInsightRefresh();
      }
    })
    .catch((err) => {
      logger.debug('Insight staleness check failed — user may not have grapple access', err);
    });
}

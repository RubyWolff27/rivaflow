import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, ChevronRight, Loader2, Share2, Sparkles } from 'lucide-react';
import { grappleApi } from '../../api/client';
import { logger } from '../../utils/logger';
import type { AIInsight } from '../../types';

export default function LatestInsightWidget() {
  const navigate = useNavigate();
  const [insight, setInsight] = useState<AIInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await grappleApi.getInsights({ limit: 1 });
        if (!cancelled) {
          const insights = response.data.insights || [];
          setInsight(insights.length > 0 ? insights[0] : null);
        }
      } catch (err) {
        logger.debug('Insights not available', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return null;
  if (!insight) return null;

  const categoryColors: Record<string, string> = {
    observation: '#3B82F6',
    pattern: '#8B5CF6',
    focus: '#F59E0B',
    recovery: '#10B981',
    weekly: '#3B82F6',
  };
  const color = categoryColors[insight.category] || categoryColors[insight.insight_type] || 'var(--accent)';

  const handleClick = async () => {
    setOpening(true);
    try {
      const res = await grappleApi.createInsightChat(insight.id);
      navigate(`/grapple?session=${res.data.chat_session_id}`);
    } catch (err) {
      logger.debug('Insight chat creation fallback to grapple page', err);
      navigate('/grapple');
    }
  };

  // Format time since insight was generated
  const hoursAgo = Math.round((Date.now() - new Date(insight.created_at).getTime()) / (1000 * 60 * 60));
  const timeLabel = hoursAgo < 1 ? 'Just now' : hoursAgo < 24 ? `${hoursAgo}h ago` : `${Math.round(hoursAgo / 24)}d ago`;

  return (
    <div
      onClick={handleClick}
      onKeyDown={e => e.key === 'Enter' && handleClick()}
      role="button"
      tabIndex={0}
      aria-label="View training insight"
      className="cursor-pointer rounded-[14px] p-5 transition-all hover:scale-[1.01]"
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
      }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center"
            style={{ backgroundColor: color + '20' }}
          >
            <Sparkles className="w-3.5 h-3.5" style={{ color }} />
          </div>
          <div>
            <span className="text-xs font-medium uppercase tracking-wide" style={{ color }}>
              {insight.insight_type === 'weekly' ? 'Weekly Insight' : insight.category || 'Training Insight'}
            </span>
            <span className="text-[10px] ml-2" style={{ color: 'var(--muted)' }}>{timeLabel}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {navigator.share && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigator.share({
                  title: insight.title,
                  text: `${insight.title}\n${insight.content}`,
                  url: window.location.origin,
                }).catch(() => {});
              }}
              className="p-1.5 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
              aria-label="Share insight"
            >
              <Share2 className="w-4 h-4" style={{ color: 'var(--muted)' }} />
            </button>
          )}
          {opening ? (
            <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--muted)' }} />
          ) : (
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          )}
        </div>
      </div>

      {/* Insight title — prominent like Strava's "Holding Steady" */}
      <h3 className="text-base font-bold mb-1.5" style={{ color }}>
        {insight.title}
      </h3>

      {/* Insight body */}
      <p className="text-sm leading-relaxed line-clamp-3" style={{ color: 'var(--muted)' }}>
        {insight.content}
      </p>

      {/* Tap to explore hint */}
      <div className="flex items-center gap-1 mt-3">
        <Brain className="w-3 h-3" style={{ color: 'var(--muted)' }} />
        <span className="text-[10px]" style={{ color: 'var(--muted)' }}>Tap to discuss with Grapple AI</span>
      </div>
    </div>
  );
}

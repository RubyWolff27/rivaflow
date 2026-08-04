import { useEffect, useState } from 'react';
import { analyticsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Card } from '../ui';

const MILESTONES = [100, 250, 500, 1000, 2500, 5000, 10000];
const JOURNEY_TOTAL = 10000;

interface MilestonesResponse {
  rolling_totals?: { lifetime?: { hours?: number } };
  first_session_date?: string | null;
}

const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0);

function nextMilestone(hours: number): number {
  return MILESTONES.find((m) => m > hours) ?? JOURNEY_TOTAL;
}

function formatJourneyPct(pct: number): string {
  return pct < 10 ? pct.toFixed(1) : String(Math.round(pct));
}

export default function LifetimeJourneyBar() {
  const [data, setData] = useState<MilestonesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const res = await analyticsApi.milestones();
        if (!cancelled) setData(res.data ?? null);
      } catch (err) {
        if (!cancelled) logger.error('Failed to load lifetime totals:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <Card>
        <div className="animate-pulse">
          <div className="h-4 w-40 rounded mb-4" style={{ backgroundColor: 'var(--surfaceElev)' }} />
          <div className="h-8 w-24 rounded mb-3" style={{ backgroundColor: 'var(--surfaceElev)' }} />
          <div className="h-2 w-full rounded" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        </div>
      </Card>
    );
  }

  const hours = num(data?.rolling_totals?.lifetime?.hours);
  const target = nextMilestone(hours);
  const progressPct = Math.max(0, Math.min(100, (hours / target) * 100));
  const journeyPct = Math.min(100, (hours / JOURNEY_TOTAL) * 100);
  const startYear = data?.first_session_date ? String(data.first_session_date).slice(0, 4) : null;

  return (
    <Card>
      <h2 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>
        10,000-Hour Journey
      </h2>

      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-3xl font-bold tabular-nums" style={{ color: 'var(--text)' }}>
          {hours.toFixed(1)}
        </span>
        <span className="text-sm" style={{ color: 'var(--muted)' }}>mat hours</span>
      </div>

      <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${progressPct}%`, backgroundColor: 'var(--accent)' }}
        />
      </div>

      <p className="text-xs mt-2" style={{ color: 'var(--text)' }}>
        {Math.round(hours)} h → next: {target} h
      </p>
      <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
        {formatJourneyPct(journeyPct)}% of the 10,000-hour journey
        {startYear ? ` · since ${startYear}` : ''}
      </p>
    </Card>
  );
}

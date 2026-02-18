import { useState, useEffect, memo } from 'react';
import { dashboardApi } from '../../api/client';
import type { WeekStats } from '../../types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string;
  delta: number;
  format?: (v: number) => string;
}

function StatCard({ label, value, delta }: StatCardProps) {
  const isPositive = delta > 0;
  const isNeutral = delta === 0;

  const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
  const color = isNeutral
    ? 'var(--muted)'
    : isPositive
      ? '#10B981'
      : '#EF4444';

  const sign = isPositive ? '+' : '';

  return (
    <div className="flex-1 min-w-0 text-center">
      <p className="text-lg font-bold tabular-nums" style={{ color: 'var(--text)' }}>
        {value}
      </p>
      <p className="text-xs font-medium mb-1" style={{ color: 'var(--muted)' }}>
        {label}
      </p>
      <span
        className="inline-flex items-center gap-0.5 text-[11px] font-medium px-1.5 py-0.5 rounded-full"
        style={{ backgroundColor: `${color}15`, color }}
      >
        <Icon className="w-3 h-3" />
        {sign}{delta === Math.floor(delta) ? delta : delta.toFixed(1)}
      </span>
    </div>
  );
}

const WeekComparison = memo(function WeekComparison() {
  const [currentWeek, setCurrentWeek] = useState<WeekStats | null>(null);
  const [previousWeek, setPreviousWeek] = useState<WeekStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      const results = await Promise.allSettled([
        dashboardApi.getWeekSummary(0),
        dashboardApi.getWeekSummary(-1),
      ]);
      if (cancelled) return;
      if (results[0].status === 'fulfilled') setCurrentWeek(results[0].value.data.stats);
      if (results[1].status === 'fulfilled') setPreviousWeek(results[1].value.data.stats);
      setLoading(false);
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div
        className="rounded-[14px] px-4 py-3"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <div className="animate-pulse flex gap-4">
          <div className="flex-1 h-12 bg-[var(--surfaceElev)] rounded" />
          <div className="flex-1 h-12 bg-[var(--surfaceElev)] rounded" />
          <div className="flex-1 h-12 bg-[var(--surfaceElev)] rounded" />
        </div>
      </div>
    );
  }

  if (!currentWeek && !previousWeek) return null;

  const sessions = currentWeek?.total_sessions ?? 0;
  const prevSessions = previousWeek?.total_sessions ?? 0;
  const hours = currentWeek?.total_hours ?? 0;
  const prevHours = previousWeek?.total_hours ?? 0;

  // Derive average intensity from total_hours / total_sessions (as rough proxy)
  // The API doesn't return avg intensity, so we use total_rolls as a training volume proxy
  const rolls = currentWeek?.total_rolls ?? 0;
  const prevRolls = previousWeek?.total_rolls ?? 0;

  return (
    <div
      className="rounded-[14px] px-4 py-3"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <p className="text-[10px] font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>
        vs Last Week
      </p>
      <div className="flex divide-x divide-[var(--border)]">
        <StatCard
          label="Sessions"
          value={String(sessions)}
          delta={sessions - prevSessions}
        />
        <StatCard
          label="Hours"
          value={hours.toFixed(1)}
          delta={parseFloat((hours - prevHours).toFixed(1))}
        />
        <StatCard
          label="Rolls"
          value={String(rolls)}
          delta={rolls - prevRolls}
        />
      </div>
    </div>
  );
});

export default WeekComparison;

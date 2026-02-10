import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { dashboardApi, goalsApi, whoopApi } from '../../api/client';
import { Card } from '../ui';
import MiniZoneBar from '../MiniZoneBar';

interface WeekStats {
  total_sessions: number;
  total_hours: number;
  total_rolls: number;
  class_types: Record<string, number>;
}

interface GoalProgress {
  targets: {
    sessions?: number;
    hours?: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
  };
  actual: {
    sessions?: number;
    hours?: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
  };
  progress: {
    sessions_pct?: number;
    hours_pct?: number;
    bjj_sessions_pct?: number;
    sc_sessions_pct?: number;
    mobility_sessions_pct?: number;
  };
}

const ACTIVITY_COLORS: Record<string, string> = {
  'gi': '#3B82F6',
  'no-gi': '#8B5CF6',
  's&c': '#EF4444',
  'drilling': '#F59E0B',
  'open-mat': '#10B981',
  'competition': '#EC4899',
};

const ACTIVITY_LABELS: Record<string, string> = {
  'gi': 'Gi',
  'no-gi': 'No-Gi',
  's&c': 'S&C',
  'drilling': 'Drilling',
  'open-mat': 'Open Mat',
  'competition': 'Competition',
};

export default function ThisWeek() {
  const [currentWeek, setCurrentWeek] = useState<WeekStats | null>(null);
  const [previousWeek, setPreviousWeek] = useState<WeekStats | null>(null);
  const [goals, setGoals] = useState<GoalProgress | null>(null);
  const [weeklyZones, setWeeklyZones] = useState<Record<string, number> | null>(null);
  const [weeklyZoneCount, setWeeklyZoneCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      const results = await Promise.allSettled([
        dashboardApi.getWeekSummary(0),
        dashboardApi.getWeekSummary(-1),
        goalsApi.getCurrentWeek(),
        whoopApi.getZonesWeekly(0, Intl.DateTimeFormat().resolvedOptions().timeZone),
      ]);

      if (cancelled) return;

      if (results[0].status === 'fulfilled') setCurrentWeek(results[0].value.data.stats);
      if (results[1].status === 'fulfilled') setPreviousWeek(results[1].value.data.stats);
      if (results[2].status === 'fulfilled') setGoals(results[2].value.data);
      if (results[3].status === 'fulfilled' && results[3].value.data?.session_count > 0) {
        setWeeklyZones(results[3].value.data.totals);
        setWeeklyZoneCount(results[3].value.data.session_count);
      }
      setLoading(false);
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-3.5 h-3.5 text-green-500" />;
    if (current < previous) return <TrendingDown className="w-3.5 h-3.5 text-red-500" />;
    return <Minus className="w-3.5 h-3.5 text-[var(--muted)]" />;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-[var(--surfaceElev)] rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-full"></div>
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-full"></div>
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (!currentWeek && !goals) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>This Week</h3>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          Log your first session to see weekly stats
        </p>
      </Card>
    );
  }

  const sessions = currentWeek?.total_sessions || 0;
  const hours = currentWeek?.total_hours || 0;
  const prevSessions = previousWeek?.total_sessions || 0;
  const prevHours = previousWeek?.total_hours || 0;
  const sessionsDiff = sessions - prevSessions;
  const hoursDiff = hours - prevHours;

  // Goal data
  const hasGoals = goals?.targets?.sessions != null;
  const targetSessions = goals?.targets?.sessions || 0;
  const targetHours = goals?.targets?.hours || 0;
  const goalRows = hasGoals ? [
    {
      label: 'Sessions',
      actual: goals!.actual?.sessions || 0,
      target: targetSessions,
      pct: goals!.progress?.sessions_pct || 0,
      color: 'var(--accent)',
    },
    {
      label: 'Hours',
      actual: goals!.actual?.hours || 0,
      target: targetHours,
      pct: goals!.progress?.hours_pct || 0,
      color: 'var(--accent)',
      format: (v: number) => v.toFixed(1),
    },
  ] : [];

  const activityGoals = hasGoals ? [
    { label: 'BJJ', actual: goals!.actual?.bjj_sessions || 0, target: goals!.targets?.bjj_sessions || 0, pct: goals!.progress?.bjj_sessions_pct || 0, color: '#3B82F6' },
    { label: 'S&C', actual: goals!.actual?.sc_sessions || 0, target: goals!.targets?.sc_sessions || 0, pct: goals!.progress?.sc_sessions_pct || 0, color: '#EF4444' },
    { label: 'Mobility', actual: goals!.actual?.mobility_sessions || 0, target: goals!.targets?.mobility_sessions || 0, pct: goals!.progress?.mobility_sessions_pct || 0, color: '#10B981' },
  ].filter(g => g.target > 0) : [];

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>This Week</h3>
        {hasGoals ? (
          <Link to="/profile" className="text-xs font-medium hover:underline" style={{ color: 'var(--accent)' }}>
            Edit Goals →
          </Link>
        ) : (
          <Link to="/profile" className="text-xs font-medium hover:underline" style={{ color: 'var(--accent)' }}>
            Set Goals →
          </Link>
        )}
      </div>

      {/* Key metrics row */}
      <div className="grid grid-cols-2 gap-4 mb-5">
        <div>
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{sessions}</span>
            {getTrendIcon(sessions, prevSessions)}
          </div>
          <p className="text-sm font-medium" style={{ color: 'var(--muted)' }}>Sessions</p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {sessionsDiff >= 0 ? '+' : ''}{sessionsDiff} vs last week
          </p>
        </div>
        <div>
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{hours.toFixed(1)}</span>
            {getTrendIcon(hours, prevHours)}
          </div>
          <p className="text-sm font-medium" style={{ color: 'var(--muted)' }}>Hours</p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {hoursDiff >= 0 ? '+' : ''}{hoursDiff.toFixed(1)}h vs last week
          </p>
        </div>
      </div>

      {/* Goal progress bars */}
      {goalRows.length > 0 && (
        <div className="space-y-3 mb-5">
          {goalRows.map((g) => (
            <div key={g.label}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{g.label}</span>
                <span className="text-xs tabular-nums" style={{ color: 'var(--muted)' }}>
                  {g.format ? g.format(g.actual) : g.actual} / {g.format ? g.format(g.target) : g.target}
                </span>
              </div>
              <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                <div
                  className="h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, g.pct)}%`, backgroundColor: g.color }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Activity breakdown */}
      {activityGoals.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium uppercase tracking-wide mb-3" style={{ color: 'var(--muted)' }}>
            Activity Goals
          </p>
          <div className="space-y-2.5">
            {activityGoals.map((g) => (
              <div key={g.label}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: g.color }} />
                    <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{g.label}</span>
                  </div>
                  <span className="text-xs tabular-nums" style={{ color: 'var(--muted)' }}>
                    {g.actual} / {g.target}
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                  <div
                    className="h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.min(100, g.pct)}%`, backgroundColor: g.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity mix from actual sessions */}
      {currentWeek?.class_types && Object.keys(currentWeek.class_types).length > 0 && (
        <div className={activityGoals.length > 0 ? 'pt-4' : ''} style={activityGoals.length > 0 ? { borderTop: '1px solid var(--border)' } : {}}>
          <p className="text-xs font-medium uppercase tracking-wide mb-3" style={{ color: 'var(--muted)' }}>
            Activity Mix
          </p>
          {/* Stacked bar */}
          <div className="flex h-3 rounded-full overflow-hidden mb-2" style={{ backgroundColor: 'var(--border)' }}>
            {Object.entries(currentWeek.class_types)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => {
                const total = currentWeek.total_sessions || 1;
                const pct = (count / total) * 100;
                return (
                  <div
                    key={type}
                    className="h-full transition-all"
                    style={{ width: `${pct}%`, backgroundColor: ACTIVITY_COLORS[type] || '#6B7280' }}
                    title={`${ACTIVITY_LABELS[type] || type}: ${count}`}
                  />
                );
              })}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {Object.entries(currentWeek.class_types)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div key={type} className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ACTIVITY_COLORS[type] || '#6B7280' }} />
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>
                    {ACTIVITY_LABELS[type] || type} {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Weekly HR Zones */}
      {weeklyZones && weeklyZoneCount > 0 && (() => {
        const totalMs = Object.values(weeklyZones).reduce((a, b) => a + b, 0);
        if (totalMs <= 0) return null;
        const highMs = (weeklyZones.zone_four_milli || 0) + (weeklyZones.zone_five_milli || 0);
        const highMins = Math.round(highMs / 60000);
        const totalMins = Math.round(totalMs / 60000);
        return (
          <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>HR Zones</p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>{weeklyZoneCount} sessions</p>
            </div>
            <MiniZoneBar zones={weeklyZones} height="h-2.5" />
            <div className="flex justify-between mt-1.5 text-xs" style={{ color: 'var(--muted)' }}>
              <span>{totalMins} min total</span>
              <span>{highMins} min high intensity</span>
            </div>
          </div>
        );
      })()}
    </Card>
  );
}

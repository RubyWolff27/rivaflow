import { useState, useEffect } from 'react';
import { dashboardApi, whoopApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { WeekStats } from '../../types';
import { ACTIVITY_COLORS, ACTIVITY_LABELS } from '../../constants/activity';
import { Card } from '../ui';
import MiniZoneBar from '../MiniZoneBar';

export function WeekAtGlance() {
  const [currentWeek, setCurrentWeek] = useState<WeekStats | null>(null);
  const [previousWeek, setPreviousWeek] = useState<WeekStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [weeklyZones, setWeeklyZones] = useState<Record<string, number> | null>(null);
  const [weeklyZoneCount, setWeeklyZoneCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [current, previous] = await Promise.all([
          dashboardApi.getWeekSummary(0),
          dashboardApi.getWeekSummary(-1),
        ]);
        if (!cancelled) {
          setCurrentWeek(current.data.stats);
          setPreviousWeek(previous.data.stats);
        }
        // Fetch weekly zone data
        try {
          const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
          const zRes = await whoopApi.getZonesWeekly(0, tz);
          if (!cancelled && zRes.data?.session_count > 0) {
            setWeeklyZones(zRes.data.totals);
            setWeeklyZoneCount(zRes.data.session_count);
          }
        } catch { /* WHOOP not connected */ }
      } catch (error) {
        if (!cancelled) logger.error('Failed to load week summary:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-[var(--muted)]" />;
  };

  const getTrendText = (current: number, previous: number) => {
    const diff = current - previous;
    if (diff === 0) return 'No change';
    const sign = diff > 0 ? '+' : '';
    return `${sign}${diff} vs last week`;
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

  if (!currentWeek) {
    return (
      <Card className="p-6">
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          No data available for this week
        </p>
      </Card>
    );
  }

  const hoursDelta = (currentWeek.total_hours || 0) - (previousWeek?.total_hours || 0);

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
          Week at a Glance
        </h3>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Current week activity breakdown
        </p>
      </div>

      {/* Key Metrics with Trends */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
              {currentWeek.total_sessions || 0}
            </span>
            {getTrendIcon(currentWeek.total_sessions || 0, previousWeek?.total_sessions || 0)}
          </div>
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>Sessions</p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {getTrendText(currentWeek.total_sessions || 0, previousWeek?.total_sessions || 0)}
          </p>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
              {currentWeek.total_hours?.toFixed(1) || '0.0'}
            </span>
            {getTrendIcon(currentWeek.total_hours || 0, previousWeek?.total_hours || 0)}
          </div>
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>Hours</p>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            {hoursDelta >= 0 ? '+' : ''}{hoursDelta.toFixed(1)}h vs last week
          </p>
        </div>
      </div>

      {/* Activity Type Breakdown */}
      {currentWeek.class_types && Object.keys(currentWeek.class_types).length > 0 && (
        <div>
          <p className="text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>
            Activity Breakdown
          </p>
          <div className="space-y-2">
            {Object.entries(currentWeek.class_types)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => {
                const color = ACTIVITY_COLORS[type] || '#6B7280';
                const label = ACTIVITY_LABELS[type] || type;
                const prevCount = previousWeek?.class_types?.[type] || 0;
                const total = currentWeek.total_sessions || 1;
                const percentage = ((count / total) * 100).toFixed(0);

                return (
                  <div key={type}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                          {label}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm" style={{ color: 'var(--muted)' }}>
                          {count} ({percentage}%)
                        </span>
                        {getTrendIcon(count, prevCount)}
                      </div>
                    </div>
                    <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
                      <div
                        className="h-2 rounded-full"
                        style={{ width: `${percentage}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Weekly HR Zones */}
      {weeklyZones && weeklyZoneCount > 0 && (() => {
        const totalMs = Object.values(weeklyZones).reduce((a, b) => a + b, 0);
        if (totalMs <= 0) return null;
        const highIntensityMs = (weeklyZones.zone_four_milli || 0) + (weeklyZones.zone_five_milli || 0);
        const highIntensityMins = Math.round(highIntensityMs / 60000);
        const totalMins = Math.round(totalMs / 60000);
        return (
          <div className="mt-6 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                HR Zones
              </p>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                {weeklyZoneCount} sessions
              </p>
            </div>
            <MiniZoneBar zones={weeklyZones} height="h-3" />
            <div className="flex justify-between mt-1.5 text-xs" style={{ color: 'var(--muted)' }}>
              <span>{totalMins} min total</span>
              <span>{highIntensityMins} min high intensity</span>
            </div>
          </div>
        );
      })()}
    </Card>
  );
}

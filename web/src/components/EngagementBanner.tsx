import { useEffect, useState } from 'react';
import { checkinsApi, streaksApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Insight, StreakStatus } from '../types';
import { Flame, CheckCircle2, AlertCircle } from 'lucide-react';

export default function EngagementBanner() {
  const [checkedIn, setCheckedIn] = useState(false);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [streaks, setStreaks] = useState<StreakStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [checkinRes, streaksRes] = await Promise.all([
          checkinsApi.getToday(),
          streaksApi.getStatus(),
        ]);
        if (cancelled) return;

        setCheckedIn(checkinRes.data.checked_in);

        // Parse insight from morning slot if available
        const morningInsight = checkinRes.data.morning?.insight_shown;
        if (morningInsight) {
          try {
            const parsedInsight = JSON.parse(morningInsight);
            setInsight(parsedInsight);
          } catch (e) {
            logger.error('Error parsing insight:', e);
          }
        }

        setStreaks(streaksRes.data);
      } catch (error) {
        if (!cancelled) logger.error('Error loading engagement data:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return null;
  }

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="space-y-4">
      {/* Check-in Status Bar */}
      <div className="card border-2" style={
        checkedIn
          ? { backgroundColor: 'var(--success-bg)', borderColor: 'var(--success)' }
          : { backgroundColor: 'var(--warning-bg)', borderColor: 'var(--warning)' }
      }>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {checkedIn ? (
                <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--success)' }} />
              ) : (
                <AlertCircle className="w-5 h-5" style={{ color: 'var(--warning)' }} />
              )}
              <span className="font-semibold">
                {getGreeting()} — {checkedIn ? '✅ Checked in' : '⚠️ Not checked in yet'}
              </span>
            </div>
            {!checkedIn && (
              <p className="text-sm text-[var(--muted)]">
                Log a session, readiness, or rest day to check in
              </p>
            )}
          </div>

          {/* Streaks */}
          {streaks && streaks.checkin.current_streak > 0 && (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="flex items-center gap-1.5 justify-end">
                  <Flame className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                  <span className="text-2xl font-bold" style={{ color: 'var(--accent)' }}>
                    {streaks.checkin.current_streak}
                  </span>
                </div>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>day streak</p>
                {streaks.checkin.longest_streak > streaks.checkin.current_streak && (
                  <p className="text-xs mt-0.5" style={{ color: 'var(--accent)' }}>
                    {streaks.checkin.longest_streak - streaks.checkin.current_streak <= 3
                      ? `${streaks.checkin.longest_streak - streaks.checkin.current_streak} more to beat your best!`
                      : `Best: ${streaks.checkin.longest_streak}`}
                  </p>
                )}
                {streaks.checkin.current_streak >= streaks.checkin.longest_streak && streaks.checkin.current_streak >= 3 && (
                  <p className="text-xs mt-0.5 font-medium" style={{ color: 'var(--accent)' }}>
                    Personal best!
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Insight (if checked in) */}
      {checkedIn && insight && (
        <div className="card border" style={{ backgroundColor: 'var(--primary-bg)', borderColor: 'var(--primary)' }}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">{insight.icon || '💡'}</span>
            <div className="flex-1">
              <h4 className="font-semibold text-sm uppercase tracking-wide mb-1" style={{ color: 'var(--primary)' }}>
                {insight.title}
              </h4>
              <p className="text-sm text-[var(--text)]">
                {insight.message}
              </p>
              {insight.action && (
                <p className="text-sm text-[var(--muted)] italic mt-1">
                  {insight.action}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

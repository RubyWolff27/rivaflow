import { useEffect, useState } from 'react';
import { checkinsApi, streaksApi, milestonesApi } from '../api/client';
import type { Insight, StreakStatus, MilestoneProgress } from '../types';
import { Flame, CheckCircle2, AlertCircle, Target } from 'lucide-react';

export default function EngagementBanner() {
  const [checkedIn, setCheckedIn] = useState(false);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [streaks, setStreaks] = useState<StreakStatus | null>(null);
  const [closestMilestone, setClosestMilestone] = useState<MilestoneProgress & { has_milestone: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [checkinRes, streaksRes, milestoneRes] = await Promise.all([
          checkinsApi.getToday(),
          streaksApi.getStatus(),
          milestonesApi.getClosest(),
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
            console.error('Error parsing insight:', e);
          }
        }

        setStreaks(streaksRes.data);
        setClosestMilestone(milestoneRes.data);
      } catch (error) {
        if (!cancelled) console.error('Error loading engagement data:', error);
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
          ? { backgroundColor: 'rgba(34,197,94,0.1)', borderColor: 'var(--success)' }
          : { backgroundColor: 'rgba(234,179,8,0.1)', borderColor: '#ca8a04' }
      }>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {checkedIn ? (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-600" />
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
                  <Flame className="w-5 h-5 text-orange-500" />
                  <span className="text-2xl font-bold text-orange-600">
                    {streaks.checkin.current_streak}
                  </span>
                </div>
                <p className="text-xs text-[var(--muted)]">day streak</p>
                {streaks.checkin.longest_streak > streaks.checkin.current_streak && (
                  <p className="text-xs text-orange-500 mt-0.5">
                    {streaks.checkin.longest_streak - streaks.checkin.current_streak <= 3
                      ? `${streaks.checkin.longest_streak - streaks.checkin.current_streak} more to beat your best!`
                      : `Best: ${streaks.checkin.longest_streak}`}
                  </p>
                )}
                {streaks.checkin.current_streak >= streaks.checkin.longest_streak && streaks.checkin.current_streak >= 3 && (
                  <p className="text-xs text-orange-500 mt-0.5 font-medium">
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
        <div className="card border" style={{ backgroundColor: 'rgba(59,130,246,0.1)', borderColor: 'rgba(59,130,246,0.3)' }}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">{insight.icon || '💡'}</span>
            <div className="flex-1">
              <h4 className="font-semibold text-sm uppercase tracking-wide mb-1" style={{ color: 'rgb(59,130,246)' }}>
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

      {/* Closest Milestone Progress */}
      {closestMilestone && closestMilestone.has_milestone && closestMilestone.percentage >= 50 && (
        <div className="card border" style={{ backgroundColor: 'rgba(139,92,246,0.1)', borderColor: 'rgba(139,92,246,0.3)' }}>
          <div className="flex items-start gap-3">
            <Target className="w-5 h-5 mt-0.5" style={{ color: 'rgb(139,92,246)' }} />
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-2" style={{ color: 'var(--text)' }}>NEXT MILESTONE</h4>
              <p className="text-sm text-[var(--text)] mb-2">
                {closestMilestone.next_label}
              </p>
              <div className="w-full bg-[var(--surfaceElev)] rounded-full h-2.5">
                <div
                  className="bg-purple-600 h-2.5 rounded-full transition-all"
                  style={{ width: `${Math.min(closestMilestone.percentage, 100)}%` }}
                />
              </div>
              <p className="text-xs text-[var(--muted)] mt-1.5">
                {closestMilestone.percentage}% complete • {closestMilestone.remaining} to go
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

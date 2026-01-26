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
    loadEngagementData();
  }, []);

  const loadEngagementData = async () => {
    try {
      const [checkinRes, streaksRes, milestoneRes] = await Promise.all([
        checkinsApi.getToday(),
        streaksApi.getStatus(),
        milestonesApi.getClosest(),
      ]);

      setCheckedIn(checkinRes.data.checked_in);

      // Parse insight if available
      if (checkinRes.data.insight_shown) {
        try {
          const parsedInsight = JSON.parse(checkinRes.data.insight_shown);
          setInsight(parsedInsight);
        } catch (e) {
          console.error('Error parsing insight:', e);
        }
      }

      setStreaks(streaksRes.data);
      setClosestMilestone(milestoneRes.data);
    } catch (error) {
      console.error('Error loading engagement data:', error);
    } finally {
      setLoading(false);
    }
  };

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
      <div className={`card border-2 ${
        checkedIn
          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
          : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
      }`}>
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
              <p className="text-sm text-gray-600 dark:text-gray-400">
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
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {streaks.checkin.current_streak}
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">day streak</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Insight (if checked in) */}
      {checkedIn && insight && (
        <div className="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <span className="text-2xl">{insight.icon || '💡'}</span>
            <div className="flex-1">
              <h4 className="font-semibold text-sm uppercase tracking-wide text-blue-900 dark:text-blue-300 mb-1">
                {insight.title}
              </h4>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {insight.message}
              </p>
              {insight.action && (
                <p className="text-sm text-gray-600 dark:text-gray-400 italic mt-1">
                  {insight.action}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Closest Milestone Progress */}
      {closestMilestone && closestMilestone.has_milestone && closestMilestone.percentage >= 50 && (
        <div className="card bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
          <div className="flex items-start gap-3">
            <Target className="w-5 h-5 text-purple-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-sm mb-2">NEXT MILESTONE</h4>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                {closestMilestone.next_label}
              </p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div
                  className="bg-purple-600 h-2.5 rounded-full transition-all"
                  style={{ width: `${Math.min(closestMilestone.percentage, 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1.5">
                {closestMilestone.percentage}% complete • {closestMilestone.remaining} to go
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

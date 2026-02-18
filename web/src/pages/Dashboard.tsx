import { useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useDashboardData } from '../hooks/useDashboardData';
import { profileApi } from '../api/client';
import { refreshIfStale } from '../utils/insightRefresh';
import { CardSkeleton } from '../components/ui';
import { LastSession } from '../components/dashboard/LastSession';
import GreetingBar from '../components/dashboard/GreetingBar';
import HeroScore from '../components/dashboard/HeroScore';
import ActiveCheckinPrompt from '../components/dashboard/ActiveCheckinPrompt';
import WeeklyProgress from '../components/dashboard/WeeklyProgress';
import WeekComparison from '../components/dashboard/WeekComparison';
import QuickLinks from '../components/dashboard/QuickLinks';
import GettingStarted from '../components/dashboard/GettingStarted';
import ErrorBoundary from '../components/ErrorBoundary';

export default function Dashboard() {
  usePageTitle('Dashboard');

  const data = useDashboardData();

  // Auto-sync browser timezone to profile
  useEffect(() => {
    const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!browserTz) return;
    const lastSynced = sessionStorage.getItem('tz_synced');
    if (lastSynced === browserTz) return;
    (async () => {
      try {
        const { data: profile } = await profileApi.get();
        if (profile.timezone === browserTz) {
          sessionStorage.setItem('tz_synced', browserTz);
          return;
        }
        await profileApi.update({ timezone: browserTz });
        sessionStorage.setItem('tz_synced', browserTz);
      } catch { /* best-effort */ }
    })();
  }, []);

  // Fire-and-forget staleness check for AI insights
  useEffect(() => {
    refreshIfStale();
  }, []);

  if (data.loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={3} />
        <CardSkeleton lines={2} />
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-5">
      <ErrorBoundary compact>
        {/* 1. Greeting bar */}
        <GreetingBar
          streakCount={data.streaks?.checkin.current_streak ?? 0}
          longestStreak={data.streaks?.checkin.longest_streak ?? 0}
        />

        {/* Getting Started — onboarding for new users */}
        <GettingStarted />

        {/* 2. Hero score + Log Session CTA */}
        <HeroScore
          readinessScore={data.readinessScore}
          whoopRecovery={data.whoopRecovery}
          hasCheckedIn={data.hasCheckedIn}
          suggestion={data.suggestion}
          whoopSyncing={data.whoopSyncing}
          onSyncWhoop={data.syncWhoop}
          weeklyGoals={data.weeklyGoals}
          streaks={data.streaks}
        />

        {/* 3. Active check-in prompt */}
        <ActiveCheckinPrompt
          dayCheckins={data.dayCheckins}
          todayPlan={data.todayPlan}
          onCheckinUpdated={data.refetchCheckins}
        />

        {/* 4. Weekly hours progress */}
        <WeeklyProgress weeklyGoals={data.weeklyGoals} />

        {/* 4b. Week-over-week comparison */}
        <WeekComparison />

        {/* 5. Last session (compact) */}
        <LastSession />

        {/* 6. Grapple AI quick actions */}
        <QuickLinks />
      </ErrorBoundary>
    </div>
  );
}

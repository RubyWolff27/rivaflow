import { useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useDashboardData } from '../hooks/useDashboardData';
import { profileApi } from '../api/client';
import { logger } from '../utils/logger';
import { refreshIfStale } from '../utils/insightRefresh';
import { CardSkeleton } from '../components/ui';
import { LastSession } from '../components/dashboard/LastSession';
import GreetingBar from '../components/dashboard/GreetingBar';
import HeroScore from '../components/dashboard/HeroScore';
import ActiveCheckinPrompt from '../components/dashboard/ActiveCheckinPrompt';
import WeekComparison from '../components/dashboard/WeekComparison';
import QuickLinks from '../components/dashboard/QuickLinks';
import GettingStarted from '../components/dashboard/GettingStarted';
import TrainingSnapshot from '../components/dashboard/TrainingSnapshot';
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
      } catch (err) { logger.debug('Timezone sync best-effort', err); }
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
      <h1 className="sr-only">Dashboard</h1>
      <ErrorBoundary compact>
        {/* Greeting bar — full width above the grid */}
        <GreetingBar
          streakCount={data.streaks?.checkin.current_streak ?? 0}
          longestStreak={data.streaks?.checkin.longest_streak ?? 0}
        />

        {/* Getting Started — onboarding for new users */}
        <GettingStarted />

        {/* 2-column layout: sidebar + main */}
        <div className="lg:grid lg:grid-cols-[320px_1fr] lg:gap-5 space-y-4 lg:space-y-0">
          {/* Left: Training Snapshot sidebar */}
          <TrainingSnapshot
            readinessScore={data.readinessScore}
            streakCount={data.streaks?.checkin.current_streak ?? 0}
            whoopRecovery={data.whoopRecovery?.recovery_score ?? null}
          />

          {/* Right: Main dashboard content */}
          <div className="space-y-4 sm:space-y-5">
            {/* Hero readiness score */}
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

            {/* Active check-in prompt */}
            <ActiveCheckinPrompt
              dayCheckins={data.dayCheckins}
              todayPlan={data.todayPlan}
              onCheckinUpdated={data.refetchCheckins}
            />

            {/* Grapple AI quick actions */}
            <QuickLinks />

            {/* Week-over-week comparison */}
            <WeekComparison />

            {/* Last session */}
            <LastSession />
          </div>
        </div>
      </ErrorBoundary>
    </div>
  );
}

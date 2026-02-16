import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { Sparkles, MessageCircle, Mic, BookOpen } from 'lucide-react';
import { Card } from '../components/ui';
import { LastSession } from '../components/dashboard/LastSession';
import { JourneyProgress } from '../components/dashboard/JourneyProgress';
import { profileApi } from '../api/client';
import { refreshIfStale } from '../utils/insightRefresh';
import DailyActionHero from '../components/dashboard/DailyActionHero';
import GettingStarted from '../components/dashboard/GettingStarted';
import TodayClassesWidget from '../components/dashboard/TodayClassesWidget';
import ThisWeek from '../components/dashboard/ThisWeek';
import MyGameWidget from '../components/dashboard/MyGameWidget';
import LatestInsightWidget from '../components/dashboard/LatestInsightWidget';
import EngagementBanner from '../components/EngagementBanner';
import ErrorBoundary from '../components/ErrorBoundary';

export default function Dashboard() {
  const navigate = useNavigate();

  // Auto-sync browser timezone to profile — reload if corrected
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
      } catch { /* best-effort, will retry next load */ }
    })();
  }, []);

  usePageTitle('Dashboard');

  // Fire-and-forget staleness check for AI insights
  useEffect(() => {
    refreshIfStale();
  }, []);

  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Dashboard widgets wrapped in ErrorBoundary */}
      <ErrorBoundary compact>
        {/* 1. Engagement Banner — streaks, check-in status, motivation */}
        <EngagementBanner />

        {/* Getting Started — onboarding checklist for new users */}
        <GettingStarted />

        {/* 2. Daily Action Hero — THE primary card */}
        <DailyActionHero />

        {/* 3. Today's gym classes */}
        <TodayClassesWidget />

        {/* 4. Last Session — "What did I do last?" */}
        <LastSession />

        {/* 5. This Week — weekly goals + progress */}
        <ThisWeek />

        {/* 6. Grapple AI Coach — key differentiator */}
        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 opacity-[0.04]">
            <Sparkles className="w-full h-full" />
          </div>
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--accent)' }}>
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-base font-semibold" style={{ color: 'var(--text)' }}>Grapple AI Coach</h2>
                <p className="text-xs" style={{ color: 'var(--muted)' }}>Voice-powered BJJ coaching and session logging</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2" style={{ minHeight: '44px' }}>
            <button
              onClick={() => navigate('/grapple?panel=chat')}
              className="flex flex-col items-center gap-1.5 py-3 rounded-lg text-xs font-medium transition-all hover:opacity-80"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            >
              <MessageCircle className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              Ask Coach
            </button>
            <button
              onClick={() => navigate('/grapple?panel=extract')}
              className="flex flex-col items-center gap-1.5 py-3 rounded-lg text-xs font-medium transition-all hover:opacity-80"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            >
              <Mic className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              Voice Log
            </button>
            <button
              onClick={() => navigate('/grapple?panel=technique')}
              className="flex flex-col items-center gap-1.5 py-3 rounded-lg text-xs font-medium transition-all hover:opacity-80"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
            >
              <BookOpen className="w-4 h-4" style={{ color: 'var(--accent)' }} />
              Technique QA
            </button>
          </div>
        </Card>

        {/* 7. Journey Progress — belt + milestone + stats */}
        <JourneyProgress />

        {/* 8. Latest AI Insight */}
        <LatestInsightWidget />

        {/* 9. My Game Plan */}
        <MyGameWidget />
      </ErrorBoundary>
    </div>
  );
}

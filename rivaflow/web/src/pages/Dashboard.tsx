import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, MessageCircle, Mic, BookOpen } from 'lucide-react';
import { Card } from '../components/ui';
import { LastSession } from '../components/dashboard/LastSession';
import { JourneyProgress } from '../components/dashboard/JourneyProgress';
import { BetaBadge } from '../components/UpgradePrompt';
import { useTier } from '../hooks/useTier';
import { profileApi } from '../api/client';
import { refreshIfStale } from '../hooks/useInsightRefresh';
import DailyActionHero from '../components/dashboard/DailyActionHero';
import GettingStarted from '../components/dashboard/GettingStarted';
import ThisWeek from '../components/dashboard/ThisWeek';
import NextGoal from '../components/dashboard/NextGoal';
import MyGameWidget from '../components/dashboard/MyGameWidget';
import LatestInsightWidget from '../components/dashboard/LatestInsightWidget';

export default function Dashboard() {
  const navigate = useNavigate();
  const tierInfo = useTier();

  // Auto-sync browser timezone to profile (once per session)
  useEffect(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const synced = sessionStorage.getItem('tz_synced');
    if (!synced && tz) {
      profileApi.update({ timezone: tz }).catch(() => {});
      sessionStorage.setItem('tz_synced', '1');
    }
  }, []);

  // Fire-and-forget staleness check for AI insights
  useEffect(() => {
    refreshIfStale();
  }, []);

  return (
    <div className="space-y-4 sm:space-y-5">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-[var(--text)]" id="page-title">Dashboard</h1>
        {tierInfo.isBeta && <BetaBadge />}
      </div>

      {/* 0. Getting Started — onboarding checklist for new users */}
      <GettingStarted />

      {/* 1. Daily Action Hero — THE primary card */}
      <DailyActionHero />

      {/* 2. Grapple AI Coach — key differentiator */}
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

      {/* 3. Latest AI Insight */}
      <LatestInsightWidget />

      {/* 4. Last Session */}
      <LastSession />

      {/* 5. Journey Progress — moved up for motivation */}
      <JourneyProgress />

      {/* 6. This Week — merged weekly stats + goals */}
      <ThisWeek />

      {/* 7. My Game Plan */}
      <MyGameWidget />

      {/* 8. Next Goal — comp countdown or milestone progress */}
      <NextGoal />
    </div>
  );
}

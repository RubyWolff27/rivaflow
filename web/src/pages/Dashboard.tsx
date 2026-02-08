import { useEffect, useState } from 'react';
import { getLocalDateString } from '../utils/date';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Activity, Scale, Sparkles, MessageCircle, Mic, BookOpen } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton, CardSkeleton } from '../components/ui';
import { WeekAtGlance } from '../components/dashboard/WeekAtGlance';
import { LastSession } from '../components/dashboard/LastSession';
import { JourneyProgress } from '../components/dashboard/JourneyProgress';
import { WeeklyGoalsBreakdown } from '../components/dashboard/WeeklyGoalsBreakdown';
import { BetaBadge } from '../components/UpgradePrompt';
import { useTier } from '../hooks/useTier';
import { useToast } from '../contexts/ToastContext';
import { profileApi, readinessApi, weightLogsApi } from '../api/client';
import { refreshIfStale, triggerInsightRefresh } from '../hooks/useInsightRefresh';
import ReadinessRecommendation from '../components/dashboard/ReadinessRecommendation';
import NextEvent from '../components/dashboard/NextEvent';
import MyGameWidget from '../components/dashboard/MyGameWidget';
import LatestInsightWidget from '../components/dashboard/LatestInsightWidget';

export default function Dashboard() {
  const navigate = useNavigate();
  const tierInfo = useTier();
  const toast = useToast();
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedInToday, setHasCheckedInToday] = useState(false);
  const [loading, setLoading] = useState(true);
  const [weightInput, setWeightInput] = useState('');
  const [lastWeight, setLastWeight] = useState<number | null>(null);
  const [savingWeight, setSavingWeight] = useState(false);

  // Auto-sync browser timezone to profile (once per session)
  useEffect(() => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const synced = sessionStorage.getItem('tz_synced');
    if (!synced && tz) {
      profileApi.update({ timezone: tz }).catch(() => {});
      sessionStorage.setItem('tz_synced', '1');
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const loadAll = async () => {
      try {
        const today = getLocalDateString();
        const response = await readinessApi.getByDate(today);
        if (!controller.signal.aborted && response.data) {
          setReadinessScore(response.data.composite_score);
          setHasCheckedInToday(true);
        }
      } catch {
        // Readiness not found for today is expected
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }

      try {
        const response = await weightLogsApi.getLatest();
        if (!controller.signal.aborted && response.data?.weight) {
          setLastWeight(response.data.weight);
        }
      } catch {
        // No weight logged yet — expected
      }

      // Fire-and-forget staleness check for AI insights
      refreshIfStale();
    };

    loadAll();
    return () => { controller.abort(); };
  }, []);

  const handleQuickWeight = async () => {
    const weight = parseFloat(weightInput);
    if (!weight || weight < 20 || weight > 300) return;
    setSavingWeight(true);
    try {
      await weightLogsApi.create({ weight });
      setLastWeight(weight);
      setWeightInput('');
      toast.success(`Weight logged: ${weight} kg`);
      triggerInsightRefresh();
    } catch {
      toast.error('Failed to log weight.');
    } finally {
      setSavingWeight(false);
    }
  };

  const getReadinessColor = (score: number): string => {
    if (score >= 16) return '#10B981'; // Green
    if (score >= 12) return '#F59E0B'; // Yellow
    return '#EF4444'; // Red
  };

  const getReadinessLabel = (score: number): string => {
    if (score >= 16) return 'Excellent';
    if (score >= 12) return 'Good';
    if (score >= 8) return 'Fair';
    return 'Low';
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <CardSkeleton lines={2} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CardSkeleton lines={4} />
          <CardSkeleton lines={4} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-[var(--text)]" id="page-title">Dashboard</h1>
        {tierInfo.isBeta && <BetaBadge />}
      </div>

      {/* Primary CTA */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-[var(--text)] mb-1">How was training?</h2>
            <p className="text-sm text-[var(--muted)]">Log your session and track your progress</p>
          </div>
          <PrimaryButton onClick={() => navigate('/log')} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Log Session
          </PrimaryButton>
        </div>
      </Card>

      {/* Grapple AI Coach — prominent CTA */}
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
        <div className="grid grid-cols-3 gap-2">
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

      {/* Latest AI Insight — prominent placement */}
      <LatestInsightWidget />

      {/* Readiness Score - Prominent Display with Color Coding */}
      {hasCheckedInToday && readinessScore !== null ? (
        <Link to="/readiness">
          <Card interactive>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-medium" style={{ color: 'var(--muted)' }}>Today's Readiness</h3>
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded"
                    style={{ backgroundColor: getReadinessColor(readinessScore), color: 'white' }}
                  >
                    {getReadinessLabel(readinessScore)}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-4xl font-bold" style={{ color: getReadinessColor(readinessScore) }}>
                    {readinessScore}
                  </span>
                  <span className="text-sm" style={{ color: 'var(--text)' }}>/ 20</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5" style={{ color: getReadinessColor(readinessScore) }} />
                <span className="text-sm" style={{ color: 'var(--accent)' }}>View Details →</span>
              </div>
            </div>
          </Card>
        </Link>
      ) : (
        <Card className="bg-gradient-to-r from-[var(--accent)]/10 to-transparent">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--text)' }}>Today's Check-in</h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>Track your readiness and optimize your training</p>
            </div>
            <PrimaryButton onClick={() => navigate('/readiness')} className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Check In
            </PrimaryButton>
          </div>
        </Card>
      )}

      {/* Readiness Recommendation */}
      <ReadinessRecommendation />

      {/* Quick Weight Log */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Scale className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            <div>
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Quick Weight Log</h3>
              {lastWeight && (
                <p className="text-xs" style={{ color: 'var(--muted)' }}>Last: {lastWeight} kg</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              className="input w-24 text-sm"
              placeholder="kg"
              value={weightInput}
              onChange={(e) => setWeightInput(e.target.value)}
              step="0.1"
              min="20"
              max="300"
              onKeyDown={(e) => e.key === 'Enter' && handleQuickWeight()}
            />
            <button
              onClick={handleQuickWeight}
              disabled={savingWeight || !weightInput}
              className="px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
            >
              {savingWeight ? '...' : 'Log'}
            </button>
          </div>
        </div>
      </Card>

      {/* My Game */}
      <MyGameWidget />

      {/* Next Event */}
      <NextEvent />

      {/* Main Grid - Week at Glance and Weekly Goals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WeekAtGlance />
        <WeeklyGoalsBreakdown />
      </div>

      {/* Journey Progress and Last Session */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <JourneyProgress />
        <LastSession />
      </div>

      {/* Quick Links */}
      <Card>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SecondaryButton onClick={() => navigate('/sessions')} className="text-sm">
            All Sessions
          </SecondaryButton>
          <SecondaryButton onClick={() => navigate('/reports')} className="text-sm">
            Analytics
          </SecondaryButton>
          <SecondaryButton onClick={() => navigate('/friends')} className="text-sm">
            Friends
          </SecondaryButton>
          <SecondaryButton onClick={() => navigate('/profile')} className="text-sm">
            Profile
          </SecondaryButton>
        </div>
      </Card>
    </div>
  );
}

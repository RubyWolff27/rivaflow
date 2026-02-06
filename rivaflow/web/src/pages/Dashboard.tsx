import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Activity } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton, CardSkeleton } from '../components/ui';
import { WeekAtGlance } from '../components/dashboard/WeekAtGlance';
import { LastSession } from '../components/dashboard/LastSession';
import { JourneyProgress } from '../components/dashboard/JourneyProgress';
import { WeeklyGoalsBreakdown } from '../components/dashboard/WeeklyGoalsBreakdown';
import { BetaBadge } from '../components/UpgradePrompt';
import { useTier } from '../hooks/useTier';
import { readinessApi } from '../api/client';

export default function Dashboard() {
  const navigate = useNavigate();
  const tierInfo = useTier();
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedInToday, setHasCheckedInToday] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReadinessData();
  }, []);

  const loadReadinessData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await readinessApi.getByDate(today);

      if (response.data) {
        setReadinessScore(response.data.composite_score);
        setHasCheckedInToday(true);
      }
    } catch (error) {
      // Readiness not found for today is expected - user hasn't logged yet
      // Silently handle 404 since it's normal behavior
    } finally {
      setLoading(false);
    }
  };

  const getReadinessColor = (score: number): string => {
    if (score >= 80) return '#10B981'; // Green
    if (score >= 60) return '#F59E0B'; // Yellow
    return '#EF4444'; // Red
  };

  const getReadinessLabel = (score: number): string => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
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

      {/* Readiness Score - Prominent Display with Color Coding */}
      {hasCheckedInToday && readinessScore !== null ? (
        <Link to="/readiness">
          <Card className="cursor-pointer hover:border-[var(--accent)] transition-colors">
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
                  <span className="text-sm" style={{ color: 'var(--text)' }}>/ 100</span>
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

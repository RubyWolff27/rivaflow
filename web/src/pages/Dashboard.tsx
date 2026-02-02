import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { dashboardApi } from '../api/client';
import { Plus, Activity } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';
import { WeekAtGlance } from '../components/dashboard/WeekAtGlance';
import { LastSession } from '../components/dashboard/LastSession';
import { JourneyProgress } from '../components/dashboard/JourneyProgress';
import { WeeklyGoalsBreakdown } from '../components/dashboard/WeeklyGoalsBreakdown';

export default function Dashboard() {
  const navigate = useNavigate();
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedInToday, setHasCheckedInToday] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReadinessData();
  }, []);

  const loadReadinessData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch(`/api/v1/readiness?date=${today}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.length > 0) {
          setReadinessScore(data[0].overall_score);
          setHasCheckedInToday(true);
        }
      }
    } catch (error) {
      console.error('Error loading readiness:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text)]" id="page-title">Dashboard</h1>
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

      {/* Readiness Score - Prominent Display */}
      {hasCheckedInToday && readinessScore !== null ? (
        <Link to="/readiness">
          <Card className="cursor-pointer hover:border-[var(--accent)] transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--muted)' }}>Today's Readiness</h3>
                <div className="flex items-center gap-3">
                  <span className="text-4xl font-bold" style={{ color: 'var(--accent)' }}>
                    {readinessScore}
                  </span>
                  <span className="text-sm" style={{ color: 'var(--text)' }}>/ 100</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5" style={{ color: 'var(--accent)' }} />
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

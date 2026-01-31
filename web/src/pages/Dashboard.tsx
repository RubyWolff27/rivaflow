import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { sessionsApi, goalsApi } from '../api/client';
import type { Session, WeeklyGoalProgress } from '../types';
import { Plus, Activity, Calendar, Target, TrendingUp } from 'lucide-react';
import { Card, Chip, PrimaryButton, SecondaryButton } from '../components/ui';

export default function Dashboard() {
  const navigate = useNavigate();
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [weeklyGoals, setWeeklyGoals] = useState<WeeklyGoalProgress | null>(null);

  // Stats for Performance Snapshot (last 7 days)
  const [stats, setStats] = useState({
    sessions: 0,
    avgIntensity: 0,
    totalRolls: 0,
    currentStreak: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7);

      const [recentSessionsRes, weekSessionsRes, goalsRes, streaksRes] = await Promise.all([
        sessionsApi.list(3),
        sessionsApi.getByRange(startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]),
        goalsApi.getCurrentWeek(),
        goalsApi.getTrainingStreaks(),
      ]);

      setRecentSessions(recentSessionsRes.data ?? []);
      setWeeklyGoals(goalsRes.data ?? null);

      // Calculate stats from last 7 days
      const weekSessions = weekSessionsRes.data ?? [];
      const totalIntensity = weekSessions.reduce((sum: number, s: any) => sum + (s.intensity ?? 0), 0);
      const totalRolls = weekSessions.reduce((sum: number, s: any) => sum + (s.rolls ?? 0), 0);

      setStats({
        sessions: weekSessions.length,
        avgIntensity: weekSessions.length > 0 ? totalIntensity / weekSessions.length : 0,
        totalRolls,
        currentStreak: streaksRes.data?.current_streak ?? 0,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  // For now, assume not checked in (can be enhanced later with actual check-in API)
  const hasCheckedInToday = false;

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

      {/* Performance Snapshot */}
      <Card>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-[var(--text)]">Performance Snapshot</h2>
          <p className="text-xs text-[var(--muted)] mt-1">Last 7 days</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {/* Sessions */}
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Sessions</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{stats.sessions}</p>
          </div>

          {/* Avg Intensity */}
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Intensity</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{stats.avgIntensity.toFixed(1)}/5</p>
          </div>

          {/* Total Rolls */}
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Rolls</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{stats.totalRolls}</p>
          </div>

          {/* Current Streak */}
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <Calendar className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Streak</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{stats.currentStreak} days</p>
          </div>
        </div>
      </Card>

      {/* Readiness Check-in */}
      {!hasCheckedInToday && (
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>Today's Check-in</h3>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>How are you feeling today?</p>
            </div>
            <SecondaryButton onClick={() => navigate('/readiness')} className="text-sm">
              Check In
            </SecondaryButton>
          </div>
        </Card>
      )}

      {/* Weekly Goals Progress */}
      {weeklyGoals && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--text)]">Weekly Goals</h2>
            <Link to="/goals" className="text-sm text-[var(--accent)] hover:opacity-80">
              View All
            </Link>
          </div>

          <div className="space-y-3">
            {/* Sessions Goal */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-[var(--text)]">Training Sessions</span>
                <span className="text-sm font-medium text-[var(--text)]">
                  {weeklyGoals.actual?.sessions ?? 0} / {weeklyGoals.targets?.sessions ?? 3}
                </span>
              </div>
              <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, weeklyGoals.progress?.sessions_pct ?? 0)}%`,
                    backgroundColor: 'var(--accent)',
                  }}
                />
              </div>
            </div>

            {/* Hours Goal */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-[var(--text)]">Training Hours</span>
                <span className="text-sm font-medium text-[var(--text)]">
                  {weeklyGoals.actual?.hours ?? 0} / {weeklyGoals.targets?.hours ?? 5}
                </span>
              </div>
              <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--border)' }}>
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, weeklyGoals.progress?.hours_pct ?? 0)}%`,
                    backgroundColor: 'var(--accent)',
                  }}
                />
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Recent Sessions */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--text)]">Recent Sessions</h2>
          <Link to="/reports" className="text-sm text-[var(--accent)] hover:opacity-80">
            View All
          </Link>
        </div>

        {recentSessions.length === 0 ? (
          <p className="text-sm text-[var(--muted)] text-center py-8">
            No sessions logged yet. Start training!
          </p>
        ) : (
          <div className="space-y-2">
            {recentSessions.map((session) => (
              <Link
                key={session.id}
                to={`/session/${session.id}`}
                className="block p-4 rounded-[14px] transition-all"
                style={{
                  backgroundColor: 'var(--surfaceElev)',
                  border: '1px solid var(--border)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{session.gym_name ?? 'Unknown Gym'}</span>
                  <span className="text-xs" style={{ color: 'var(--muted)' }}>{session.session_date ?? 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <Chip>{session.class_type ?? 'N/A'}</Chip>
                  <Chip>{session.duration_mins ?? 0}m</Chip>
                  <Chip>{session.intensity ?? 0}/5</Chip>
                  {(session.rolls ?? 0) > 0 && <Chip>{session.rolls} rolls</Chip>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

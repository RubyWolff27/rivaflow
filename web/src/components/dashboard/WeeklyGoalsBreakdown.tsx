import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../api/client';
import { Card } from '../ui';

interface WeeklyGoalProgress {
  targets: {
    sessions?: number;
    hours?: number;
  };
  actual: {
    sessions?: number;
    hours?: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
  };
  progress: {
    sessions_pct?: number;
    hours_pct?: number;
  };
}

export function WeeklyGoalsBreakdown() {
  const [goals, setGoals] = useState<WeeklyGoalProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await goalsApi.getCurrentWeek();
      setGoals(response.data);
    } catch (error) {
      console.error('Failed to load weekly goals:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded w-full"></div>
            <div className="h-4 bg-gray-700 rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (!goals) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
            Weekly Goals
          </h3>
          <Link
            to="/goals"
            className="text-xs font-medium hover:underline"
            style={{ color: 'var(--accent)' }}
          >
            Set Goals →
          </Link>
        </div>
        <p className="text-sm text-center py-8" style={{ color: 'var(--muted)' }}>
          Set weekly goals to track your training consistency
        </p>
      </Card>
    );
  }

  const bjjSessions = goals.actual?.bjj_sessions || 0;
  const scSessions = goals.actual?.sc_sessions || 0;
  const mobilitySessions = goals.actual?.mobility_sessions || 0;
  const totalSessions = goals.actual?.sessions || 0;
  const targetSessions = goals.targets?.sessions || 3;
  const targetHours = goals.targets?.hours || 5;
  const actualHours = goals.actual?.hours || 0;

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
            Weekly Goals
          </h3>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            This week's training progress
          </p>
        </div>
        <Link
          to="/goals"
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--accent)' }}
        >
          Edit Goals →
        </Link>
      </div>

      {/* Overall Progress */}
      <div className="space-y-4 mb-6">
        {/* Sessions */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              Training Sessions
            </span>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>
              {totalSessions} / {targetSessions}
            </span>
          </div>
          <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, (goals.progress?.sessions_pct || 0))}%`,
                backgroundColor: 'var(--accent)',
              }}
            />
          </div>
        </div>

        {/* Hours */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              Training Hours
            </span>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>
              {actualHours.toFixed(1)} / {targetHours}
            </span>
          </div>
          <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, (goals.progress?.hours_pct || 0))}%`,
                backgroundColor: 'var(--accent)',
              }}
            />
          </div>
        </div>
      </div>

      {/* Activity Breakdown */}
      <div>
        <p className="text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>
          Activity Breakdown
        </p>
        <div className="grid grid-cols-3 gap-3">
          <div
            className="p-3 rounded-lg text-center"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
          >
            <p className="text-2xl font-bold" style={{ color: '#3B82F6' }}>{bjjSessions}</p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>BJJ</p>
          </div>
          <div
            className="p-3 rounded-lg text-center"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
          >
            <p className="text-2xl font-bold" style={{ color: '#EF4444' }}>{scSessions}</p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>S&C</p>
          </div>
          <div
            className="p-3 rounded-lg text-center"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
          >
            <p className="text-2xl font-bold" style={{ color: '#10B981' }}>{mobilitySessions}</p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>Mobility</p>
          </div>
        </div>
      </div>
    </Card>
  );
}

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { goalsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Card } from '../ui';

interface WeeklyGoalProgress {
  targets: {
    sessions?: number;
    hours?: number;
    bjj_sessions?: number;
    sc_sessions?: number;
    mobility_sessions?: number;
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
    bjj_sessions_pct?: number;
    sc_sessions_pct?: number;
    mobility_sessions_pct?: number;
  };
}

export function WeeklyGoalsBreakdown() {
  const [goals, setGoals] = useState<WeeklyGoalProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        const response = await goalsApi.getCurrentWeek();
        if (!cancelled) setGoals(response.data);
      } catch (error) {
        if (!cancelled) logger.error('Failed to load weekly goals:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-[var(--surfaceElev)] rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-full"></div>
            <div className="h-4 bg-[var(--surfaceElev)] rounded w-2/3"></div>
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
            to="/profile"
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
  const targetBjj = goals.targets?.bjj_sessions || 3;
  const targetSC = goals.targets?.sc_sessions || 1;
  const targetMobility = goals.targets?.mobility_sessions || 0;

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
          to="/profile"
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

      {/* Activity-Specific Goals */}
      <div className="space-y-3">
        <p className="text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>
          Activity Goals
        </p>

        {/* BJJ Sessions */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
              BJJ Sessions
            </span>
            <span className="text-xs" style={{ color: 'var(--muted)' }}>
              {bjjSessions} / {targetBjj}
            </span>
          </div>
          <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, (goals.progress?.bjj_sessions_pct || 0))}%`,
                backgroundColor: '#3B82F6',
              }}
            />
          </div>
        </div>

        {/* S&C Sessions */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
              S&C Sessions
            </span>
            <span className="text-xs" style={{ color: 'var(--muted)' }}>
              {scSessions} / {targetSC}
            </span>
          </div>
          <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, (goals.progress?.sc_sessions_pct || 0))}%`,
                backgroundColor: '#EF4444',
              }}
            />
          </div>
        </div>

        {/* Mobility Sessions */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
              Mobility Sessions
            </span>
            <span className="text-xs" style={{ color: 'var(--muted)' }}>
              {mobilitySessions} / {targetMobility}
            </span>
          </div>
          <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-2 rounded-full transition-all"
              style={{
                width: `${Math.min(100, (goals.progress?.mobility_sessions_pct || 0))}%`,
                backgroundColor: '#10B981',
              }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
}

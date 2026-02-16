import { Link } from 'react-router-dom';
import { Flame } from 'lucide-react';
import { Card } from '../ui';
import type { WeeklyGoalProgress } from '../../types';

interface WeeklyProgressProps {
  weeklyGoals: WeeklyGoalProgress | null;
  streakCount: number;
}

function ProgressRing({
  value,
  target,
  label,
  display,
  icon,
}: {
  value: number;
  target: number;
  label: string;
  display: string;
  icon?: React.ReactNode;
}) {
  const size = 48;
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = target > 0 ? Math.min(value / target, 1) : 0;
  const dashOffset = circumference * (1 - progress);
  const isComplete = target > 0 && value >= target;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--border)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={isComplete ? 'var(--success)' : 'var(--accent)'}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="score-ring"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          {icon || (
            <span
              className="text-xs font-bold"
              style={{ color: 'var(--text)' }}
            >
              {display}
            </span>
          )}
        </div>
      </div>
      <span className="text-xs" style={{ color: 'var(--muted)' }}>
        {label}
      </span>
    </div>
  );
}

export default function WeeklyProgress({
  weeklyGoals,
  streakCount,
}: WeeklyProgressProps) {
  const hasGoals = weeklyGoals?.targets?.sessions != null;
  const actualSessions = weeklyGoals?.actual?.sessions ?? 0;
  const actualHours = weeklyGoals?.actual?.hours ?? 0;
  const targetSessions = weeklyGoals?.targets?.sessions ?? 4;
  const targetHours = weeklyGoals?.targets?.hours ?? 6;

  const isEmpty = actualSessions === 0 && actualHours === 0 && streakCount === 0;

  return (
    <Card variant="compact">
      <div className="flex items-center justify-between mb-3">
        <h3
          className="text-sm font-semibold"
          style={{ color: 'var(--text)' }}
        >
          This Week
        </h3>
        <Link
          to="/goals"
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--accent)' }}
        >
          {hasGoals ? 'Edit Goals' : 'Set Goals'}
        </Link>
      </div>

      {isEmpty ? (
        <p className="text-sm py-2" style={{ color: 'var(--muted)' }}>
          Start your week strong — log a session to track progress
        </p>
      ) : (
        <div className="grid grid-cols-3 gap-2 py-1">
          <ProgressRing
            value={actualSessions}
            target={targetSessions}
            label="Sessions"
            display={`${actualSessions}/${targetSessions}`}
          />
          <ProgressRing
            value={actualHours}
            target={targetHours}
            label="Hours"
            display={`${actualHours.toFixed(1)}`}
          />
          <ProgressRing
            value={streakCount}
            target={Math.max(streakCount, 1)}
            label="Streak"
            display=""
            icon={
              <div className="flex items-center gap-0.5">
                <Flame
                  className="w-3 h-3"
                  style={{ color: 'var(--accent)' }}
                />
                <span
                  className="text-xs font-bold"
                  style={{ color: 'var(--text)' }}
                >
                  {streakCount}
                </span>
              </div>
            }
          />
        </div>
      )}
    </Card>
  );
}

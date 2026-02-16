import { Link } from 'react-router-dom';
import { Clock } from 'lucide-react';
import type { WeeklyGoalProgress } from '../../types';

interface WeeklyProgressProps {
  weeklyGoals: WeeklyGoalProgress | null;
}

export default function WeeklyProgress({
  weeklyGoals,
}: WeeklyProgressProps) {
  const hasGoals = weeklyGoals?.targets?.hours != null;
  const actualHours = weeklyGoals?.actual?.hours ?? 0;
  const targetHours = weeklyGoals?.targets?.hours ?? 0;
  const pct = targetHours > 0 ? Math.min((actualHours / targetHours) * 100, 100) : 0;
  const isComplete = targetHours > 0 && actualHours >= targetHours;

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-[14px]"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <Clock className="w-4 h-4 shrink-0" style={{ color: 'var(--muted)' }} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            This Week
          </span>
          <span className="text-xs tabular-nums" style={{ color: 'var(--muted)' }}>
            {actualHours.toFixed(1)}{targetHours > 0 ? ` / ${targetHours.toFixed(1)}h` : 'h'}
          </span>
        </div>
        {targetHours > 0 && (
          <div className="w-full h-1.5 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
            <div
              className="h-1.5 rounded-full transition-all"
              style={{
                width: `${pct}%`,
                backgroundColor: isComplete ? 'var(--success)' : 'var(--accent)',
              }}
            />
          </div>
        )}
      </div>

      <Link
        to="/goals"
        className="text-xs font-medium shrink-0 hover:underline"
        style={{ color: 'var(--accent)' }}
      >
        {hasGoals ? 'Edit Goals' : 'Set Goals'}
      </Link>
    </div>
  );
}

import { memo } from 'react';
import { Check, Pencil, Trash2 } from 'lucide-react';
import type { TrainingGoal } from '../../types';
import { Card } from '../ui';

interface TrainingGoalCardProps {
  goal: TrainingGoal;
  onEdit: (goal: TrainingGoal) => void;
  onDelete: (goalId: number) => void;
}

const METRIC_LABELS: Record<string, string> = {
  sessions: 'Sessions',
  hours: 'Hours',
  rolls: 'Rolls',
  submissions: 'Submissions',
  technique_count: 'Times Practiced',
};

function formatActual(metric: string, value: number): string {
  if (metric === 'hours') return value.toFixed(1);
  return String(value);
}

const TrainingGoalCard = memo(function TrainingGoalCard({ goal, onEdit, onDelete }: TrainingGoalCardProps) {
  const title = goal.goal_type === 'technique' && goal.movement_name
    ? goal.movement_name
    : `${METRIC_LABELS[goal.metric] || goal.metric}${goal.class_type_filter ? ` (${goal.class_type_filter})` : ''}`;

  const barColor = goal.completed ? '#10B981' : 'var(--accent)';

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
              {title}
            </h4>
            {goal.completed && (
              <span className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-500">
                <Check className="w-3 h-3" /> Done
              </span>
            )}
          </div>
          <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
            {goal.goal_type === 'technique' ? 'Technique Goal' : 'Frequency Goal'}
            {!goal.is_active && ' (paused)'}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => onEdit(goal)}
            className="p-1.5 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
            style={{ color: 'var(--muted)' }}
            aria-label="Edit goal"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(goal.id)}
            className="p-1.5 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
            style={{ color: 'var(--muted)' }}
            aria-label="Delete goal"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
          {METRIC_LABELS[goal.metric] || goal.metric}
        </span>
        <span className="text-sm" style={{ color: 'var(--muted)' }}>
          {formatActual(goal.metric, goal.actual_value)} / {goal.target_value}
        </span>
      </div>
      <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--border)' }}>
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width: `${Math.min(100, goal.progress_pct)}%`,
            backgroundColor: barColor,
          }}
        />
      </div>
    </Card>
  );
});

export default TrainingGoalCard;

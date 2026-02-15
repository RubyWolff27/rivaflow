import { Check, Clock, AlertTriangle, CalendarCheck } from 'lucide-react';
import { computeSmartStatus } from './computeSmartStatus';
import type { Session, WeeklyGoalProgress, GymClass } from '../../types';

export default function SmartPlanBanner({
  intention,
  todaySessions,
  todaysClasses,
  weeklyGoals,
  onLog,
}: {
  intention?: string;
  todaySessions: Session[];
  todaysClasses: GymClass[];
  weeklyGoals: WeeklyGoalProgress | null;
  onLog: () => void;
}) {
  const status = computeSmartStatus(intention, todaySessions, todaysClasses, weeklyGoals);
  if (!status) return null;

  const IconComponent = status.icon === 'check' ? Check
    : status.icon === 'clock' ? Clock
    : status.icon === 'alert' ? AlertTriangle
    : CalendarCheck;

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-xl mb-4"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <div
        className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
        style={{ backgroundColor: status.iconBg }}
      >
        <IconComponent className="w-4 h-4" style={{ color: status.iconColor }} />
      </div>
      <div className="flex-1 min-w-0">
        {status.subtext && (
          <p className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
            {status.subtext}
          </p>
        )}
        <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
          {status.headline}
        </p>
      </div>
      {status.showLogButton ? (
        <button
          onClick={onLog}
          className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          Log it
        </button>
      ) : (status.type === 'trained-planned' || status.type === 'trained') ? (
        <span
          className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold"
          style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
        >
          Done ✓
        </span>
      ) : null}
    </div>
  );
}

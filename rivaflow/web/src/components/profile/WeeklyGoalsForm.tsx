import { Target } from 'lucide-react';

export interface WeeklyGoalsFormProps {
  formData: {
    weekly_bjj_sessions_target: number;
    weekly_sc_sessions_target: number;
    weekly_mobility_sessions_target: number;
    weekly_hours_target: number;
    weekly_rolls_target: number;
    show_weekly_goals: boolean;
    show_streak_on_dashboard: boolean;
    activity_visibility: 'friends' | 'private';
  };
  onChange: (data: WeeklyGoalsFormProps['formData']) => void;
  saving: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export default function WeeklyGoalsForm({
  formData,
  onChange,
  saving,
  onSubmit,
}: WeeklyGoalsFormProps) {
  return (
    <form onSubmit={onSubmit} className="card">
      <div className="flex items-center gap-3 mb-4">
        <Target className="w-6 h-6 text-green-600" />
        <h2 className="text-xl font-semibold">Weekly Goals</h2>
      </div>

      <p className="text-sm text-[var(--muted)] mb-4">
        Set your weekly training targets. These will be tracked on your dashboard.
      </p>

      {/* Activity Goals Explanation */}
      <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'rgba(59,130,246,0.1)', border: '1px solid var(--accent)' }}>
        <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--accent)' }}>
          How Activity Goals Work
        </h3>
        <div className="text-xs space-y-1" style={{ color: 'var(--accent)' }}>
          <p>Set specific goals for each training type:</p>
          <ul className="list-disc list-inside ml-2 mt-1 space-y-0.5">
            <li><strong>BJJ:</strong> Gi, No-Gi, Open Mat, Competition sessions</li>
            <li><strong>S&C:</strong> Strength & Conditioning sessions</li>
            <li><strong>Mobility:</strong> Mobility, Recovery, Physio sessions</li>
          </ul>
          <p className="mt-2">Your dashboard will track progress for each activity type separately.</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Activity-Specific Goals */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="label">BJJ Sessions / Week</label>
            <input
              type="number"
              className="input"
              value={formData.weekly_bjj_sessions_target}
              onChange={(e) => onChange({ ...formData, weekly_bjj_sessions_target: parseInt(e.target.value) || 0 })}
              min="0"
              max="20"
            />
            <p className="text-xs text-[var(--muted)] mt-1">Gi, No-Gi, Open Mat</p>
          </div>

          <div>
            <label className="label">S&C Sessions / Week</label>
            <input
              type="number"
              className="input"
              value={formData.weekly_sc_sessions_target}
              onChange={(e) => onChange({ ...formData, weekly_sc_sessions_target: parseInt(e.target.value) || 0 })}
              min="0"
              max="20"
            />
            <p className="text-xs text-[var(--muted)] mt-1">Strength & Conditioning</p>
          </div>

          <div>
            <label className="label">Mobility / Week</label>
            <input
              type="number"
              className="input"
              value={formData.weekly_mobility_sessions_target}
              onChange={(e) => onChange({ ...formData, weekly_mobility_sessions_target: parseInt(e.target.value) || 0 })}
              min="0"
              max="20"
            />
            <p className="text-xs text-[var(--muted)] mt-1">Mobility, Recovery</p>
          </div>
        </div>

        {/* Overall Goals */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Hours / Week</label>
            <input
              type="number"
              className="input"
              value={formData.weekly_hours_target}
              onChange={(e) => onChange({ ...formData, weekly_hours_target: parseFloat(e.target.value) || 0 })}
              min="0"
              max="40"
              step="0.5"
            />
            <p className="text-xs text-[var(--muted)] mt-1">Total training time</p>
          </div>

          <div>
            <label className="label">Rolls / Week</label>
            <input
              type="number"
              className="input"
              value={formData.weekly_rolls_target}
              onChange={(e) => onChange({ ...formData, weekly_rolls_target: parseInt(e.target.value) || 0 })}
              min="0"
              max="100"
            />
            <p className="text-xs text-[var(--muted)] mt-1">Live sparring rounds</p>
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.show_weekly_goals}
              onChange={(e) => onChange({ ...formData, show_weekly_goals: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm">Show weekly goals on dashboard</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.show_streak_on_dashboard}
              onChange={(e) => onChange({ ...formData, show_streak_on_dashboard: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm">Show training streaks on dashboard</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.activity_visibility === 'friends'}
              onChange={(e) => onChange({ ...formData, activity_visibility: e.target.checked ? 'friends' : 'private' })}
              className="rounded"
            />
            <span className="text-sm">Show my sessions on friends' feeds</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="btn-primary w-full"
        >
          {saving ? 'Saving...' : 'Save Goals'}
        </button>
      </div>
    </form>
  );
}

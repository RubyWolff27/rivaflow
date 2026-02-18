import { Plus, X } from 'lucide-react';
import { Card } from '../ui';

export interface Injury {
  area: string;
  side: string;
  severity: string;
  notes: string;
  status: string;
  resolved_date: string;
  start_date: string;
}

const INJURY_AREAS = [
  'knee', 'shoulder', 'back', 'neck', 'elbow', 'wrist',
  'ankle', 'hip', 'ribs', 'fingers', 'other',
];

const INJURY_SIDES = ['left', 'right', 'both', 'n/a'];
const INJURY_SEVERITIES = ['mild', 'moderate', 'severe'];
const INJURY_STATUSES = [
  { id: 'active', label: 'Active', color: '#EF4444' },
  { id: 'managing', label: 'Managing', color: '#F59E0B' },
  { id: 'recovered', label: 'Recovered', color: '#10B981' },
];

export interface InjuryManagerProps {
  injuries: Injury[];
  onAdd: () => void;
  onRemove: (index: number) => void;
  onUpdate: (index: number, field: keyof Injury, value: string) => void;
}

export default function InjuryManager({
  injuries,
  onAdd,
  onRemove,
  onUpdate,
}: InjuryManagerProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Injuries</h2>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>Persist across sessions, unlike your daily check-in hotspot</p>
        </div>
        <button
          onClick={onAdd}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
          style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--accent)' }}
        >
          <Plus className="w-3.5 h-3.5" /> Add
        </button>
      </div>

      {injuries.length === 0 && (
        <p className="text-xs py-4 text-center" style={{ color: 'var(--muted)' }}>
          No injuries recorded. Grapple will assume you're healthy.
        </p>
      )}

      <div className="space-y-3">
        {injuries.map((inj, i) => (
          <div
            key={i}
            className="p-3 rounded-lg"
            style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>Injury {i + 1}</span>
              <button onClick={() => onRemove(i)} className="p-1 rounded hover:bg-[var(--border)]">
                <X className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-2">
              <select className="input text-xs" value={inj.area} onChange={e => onUpdate(i, 'area', e.target.value)}>
                {INJURY_AREAS.map(a => <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>)}
              </select>
              <select className="input text-xs" value={inj.side} onChange={e => onUpdate(i, 'side', e.target.value)}>
                {INJURY_SIDES.map(s => <option key={s} value={s}>{s === 'n/a' ? 'N/A' : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
              <select className="input text-xs" value={inj.severity} onChange={e => onUpdate(i, 'severity', e.target.value)}>
                {INJURY_SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
              <div>
                <label className="text-[10px] font-medium block mb-0.5" style={{ color: 'var(--muted)' }}>Status</label>
                <div className="flex gap-1.5">
                  {INJURY_STATUSES.map(st => (
                    <button
                      key={st.id}
                      type="button"
                      onClick={() => onUpdate(i, 'status', st.id)}
                      className="flex-1 py-1 rounded-md text-[10px] font-semibold transition-all"
                      style={{
                        backgroundColor: (inj.status || 'active') === st.id ? `${st.color}20` : 'var(--surface)',
                        color: (inj.status || 'active') === st.id ? st.color : 'var(--muted)',
                        border: (inj.status || 'active') === st.id ? `1px solid ${st.color}` : '1px solid var(--border)',
                      }}
                    >
                      {st.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[10px] font-medium block mb-0.5" style={{ color: 'var(--muted)' }}>Start Date</label>
                <input
                  type="date"
                  className="input w-full text-xs"
                  value={inj.start_date || ''}
                  onChange={e => onUpdate(i, 'start_date', e.target.value)}
                />
              </div>
            </div>
            {(inj.status || 'active') === 'recovered' && (
              <div className="mb-2">
                <label className="text-[10px] font-medium block mb-0.5" style={{ color: 'var(--muted)' }}>Resolved Date</label>
                <input
                  type="date"
                  className="input w-full text-xs"
                  value={inj.resolved_date || ''}
                  onChange={e => onUpdate(i, 'resolved_date', e.target.value)}
                />
              </div>
            )}
            <input
              className="input w-full text-xs"
              placeholder="Notes (e.g. ACL sprain, 3 months ago)"
              value={inj.notes}
              onChange={e => onUpdate(i, 'notes', e.target.value)}
            />
          </div>
        ))}
      </div>
    </Card>
  );
}

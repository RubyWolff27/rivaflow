import { useState } from 'react';
import { AlertCircle, Check, Pencil } from 'lucide-react';
import type { HardGate, MetaPayload } from '../../types/curriculum';

interface HardGatesStripProps {
  gates: HardGate[];
  onSave: (payload: MetaPayload) => Promise<void>;
  /** The coach tab renders the same gates but never offers the edit affordance. */
  readOnly?: boolean;
}

function gateValue(gate: HardGate): string {
  if (gate.value === null || gate.value === undefined || gate.value === '') return 'Not set';
  // A count against a requirement reads as progress, not a bare number — the
  // classes gate is only meaningful next to AJJ's 50.
  if (gate.target) return `${gate.value} / ${gate.target}`;
  return String(gate.value);
}

/**
 * The gates that actually decide purple — competition experience, classes,
 * stripes — sit above the tabs because the syllabus is not the binding
 * constraint and the page should never imply otherwise.
 */
export default function HardGatesStrip({ gates, onSave, readOnly = false }: HardGatesStripProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<MetaPayload>({});

  const startEdit = () => {
    const byKey = Object.fromEntries(gates.map((g) => [g.key, g.value]));
    setForm({
      competition_date: (byKey.competition as string) ?? '',
      blue_promoted_at: gates.find((g) => g.key === 'classes')?.since ?? '',
      classes_logged: null,
      stripes: (byKey.stripes as number) ?? null,
    });
    setEditing(true);
  };

  const submit = async () => {
    setSaving(true);
    try {
      await onSave({
        competition_date: form.competition_date || null,
        blue_promoted_at: form.blue_promoted_at || null,
        classes_logged: form.classes_logged ?? null,
        stripes: form.stripes ?? null,
      });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="rounded-2xl p-3 sm:p-4"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
      data-testid="hard-gates-strip"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Hard gates
          </h2>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            What actually decides the belt. The syllabus is not the binding constraint.
          </p>
        </div>
        {!readOnly && !editing && (
          <button
            type="button"
            onClick={startEdit}
            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-lg"
            style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
          >
            <Pencil className="w-3 h-3" />
            Edit
          </button>
        )}
      </div>

      {editing ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="text-xs" style={{ color: 'var(--muted)' }}>
            Competition date
            <input
              type="date"
              className="input mt-1 w-full text-sm"
              value={(form.competition_date as string) ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, competition_date: e.target.value }))}
            />
          </label>
          <label className="text-xs" style={{ color: 'var(--muted)' }}>
            Blue belt from
            <input
              type="date"
              className="input mt-1 w-full text-sm"
              value={(form.blue_promoted_at as string) ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, blue_promoted_at: e.target.value }))}
            />
            <span className="block mt-1 text-[10px]">Classes are counted from here</span>
          </label>
          <label className="text-xs" style={{ color: 'var(--muted)' }}>
            Override class count
            <input
              type="number"
              min={0}
              placeholder="auto"
              className="input mt-1 w-full text-sm"
              value={form.classes_logged ?? ''}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  classes_logged: e.target.value === '' ? null : Number(e.target.value),
                }))
              }
            />
          </label>
          <label className="text-xs" style={{ color: 'var(--muted)' }}>
            Stripes on blue
            <input
              type="number"
              min={0}
              max={4}
              className="input mt-1 w-full text-sm"
              value={form.stripes ?? ''}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  stripes: e.target.value === '' ? null : Number(e.target.value),
                }))
              }
            />
          </label>
          <div className="sm:col-span-2 flex gap-2">
            <button type="button" className="btn-primary text-sm" onClick={submit} disabled={saving}>
              {saving ? 'Saving…' : 'Save gates'}
            </button>
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={() => setEditing(false)}
              disabled={saving}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {gates.map((gate) => (
            <div
              key={gate.key}
              className="rounded-xl p-3"
              style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
            >
              <div className="flex items-center gap-1.5 text-xs mb-1" style={{ color: 'var(--muted)' }}>
                {gate.met === true ? (
                  <Check className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
                ) : gate.met === false ? (
                  <AlertCircle className="w-3.5 h-3.5" />
                ) : null}
                {gate.label}
              </div>
              <div className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                {gateValue(gate)}
              </div>
              {/* A derived number must say it's derived — otherwise a typed
                  override and a counted one look identical on screen. */}
              {gate.source === 'manual' && (
                <div className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                  Manual override
                </div>
              )}
              {gate.source === 'unset' && (
                <div className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                  Set your blue-belt date to start counting
                </div>
              )}
              {gate.note && (
                <div className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                  {gate.note}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

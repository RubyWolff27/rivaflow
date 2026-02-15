import { useState } from 'react';
import { Sun, ChevronDown, ChevronUp, CalendarCheck } from 'lucide-react';
import { checkinsApi, getErrorMessage } from '../../api/client';

export default function MiddayPrompt({ onSubmitted, todayPlan }: { onSubmitted: () => void; todayPlan?: string }) {
  const [expanded, setExpanded] = useState(false);
  const [energy, setEnergy] = useState(3);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setSaving(true);
    setError('');
    try {
      await checkinsApi.createMidday({ energy_level: energy, midday_note: note || undefined });
      onSubmitted();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const energyLabels = ['', 'Very Low', 'Low', 'Moderate', 'Good', 'Great'];

  return (
    <div
      className="mt-3 rounded-xl overflow-hidden"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <div className="flex items-center gap-2">
          <Sun className="w-4 h-4" style={{ color: '#F59E0B' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Midday Energy Check
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          {todayPlan && (
            <div
              className="flex items-center gap-2 p-2 rounded-lg text-xs"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <CalendarCheck className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--accent)' }} />
              <span style={{ color: 'var(--muted)' }}>Today's plan: <strong style={{ color: 'var(--text)' }}>{todayPlan}</strong> — still on?</span>
            </div>
          )}

          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
              Energy Level: <span style={{ color: 'var(--text)' }}>{energy}/5 — {energyLabels[energy]}</span>
            </label>
            <input
              type="range" min={1} max={5} value={energy}
              onChange={(e) => setEnergy(Number(e.target.value))}
              className="w-full mt-1 accent-[var(--accent)]"
            />
          </div>

          <input
            type="text"
            placeholder="Quick note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="w-full text-sm rounded-lg px-3 py-2"
            style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
          />

          {error && <p className="text-xs" style={{ color: 'var(--error)' }}>{error}</p>}

          <button
            onClick={submit}
            disabled={saving}
            className="w-full py-2 rounded-lg text-sm font-semibold transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#fff', opacity: saving ? 0.6 : 1 }}
          >
            {saving ? 'Saving...' : 'Save Midday Check-in'}
          </button>
        </div>
      )}
    </div>
  );
}

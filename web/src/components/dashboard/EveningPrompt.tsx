import { useState } from 'react';
import { Moon, ChevronDown, ChevronUp, Coffee, Briefcase, AlertTriangle, Plane } from 'lucide-react';
import { checkinsApi, getErrorMessage } from '../../api/client';

export const REST_TYPES = [
  { id: 'recovery', label: 'Recovery', icon: Coffee, color: '#10B981' },
  { id: 'life', label: 'Life', icon: Briefcase, color: '#3B82F6' },
  { id: 'injury', label: 'Injury', icon: AlertTriangle, color: '#EF4444' },
  { id: 'travel', label: 'Travel', icon: Plane, color: '#8B5CF6' },
];

export default function EveningPrompt({ onSubmitted }: { onSubmitted: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [didNotTrain, setDidNotTrain] = useState(false);
  const [quality, setQuality] = useState(3);
  const [recoveryNote, setRecoveryNote] = useState('');
  const [tomorrow, setTomorrow] = useState('');
  const [restType, setRestType] = useState<string | null>(null);
  const [restNote, setRestNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    setSaving(true);
    setError('');
    try {
      await checkinsApi.createEvening({
        did_not_train: didNotTrain,
        rest_type: didNotTrain ? (restType || undefined) : undefined,
        rest_note: didNotTrain ? (restNote || undefined) : undefined,
        training_quality: didNotTrain ? undefined : quality,
        recovery_note: recoveryNote || undefined,
        tomorrow_intention: tomorrow || undefined,
      });
      onSubmitted();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const qualityLabels = ['', 'Poor', 'Below Avg', 'Average', 'Good', 'Excellent'];

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
          <Moon className="w-4 h-4" style={{ color: '#8B5CF6' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Evening Reflection
          </span>
        </div>
        {expanded
          ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
          : <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }}>
            <button
              onClick={() => setDidNotTrain(false)}
              className="flex-1 py-2 text-sm font-semibold transition-colors"
              style={{
                backgroundColor: !didNotTrain ? 'var(--accent)' : 'var(--surface)',
                color: !didNotTrain ? '#fff' : 'var(--muted)',
              }}
            >
              I trained
            </button>
            <button
              onClick={() => setDidNotTrain(true)}
              className="flex-1 py-2 text-sm font-semibold transition-colors"
              style={{
                backgroundColor: didNotTrain ? 'var(--surfaceElev)' : 'var(--surface)',
                color: didNotTrain ? 'var(--text)' : 'var(--muted)',
                borderLeft: '1px solid var(--border)',
              }}
            >
              Rest day
            </button>
          </div>

          {!didNotTrain ? (
            <>
              <div>
                <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                  Training Quality: <span style={{ color: 'var(--text)' }}>{quality}/5 — {qualityLabels[quality]}</span>
                </label>
                <input
                  type="range" min={1} max={5} value={quality}
                  onChange={(e) => setQuality(Number(e.target.value))}
                  className="w-full mt-1 accent-[var(--accent)]"
                />
              </div>

              <textarea
                placeholder="How does your body feel? Any notes on recovery..."
                value={recoveryNote}
                onChange={(e) => setRecoveryNote(e.target.value)}
                rows={2}
                className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />
            </>
          ) : (
            <>
              <div>
                <label className="text-xs font-medium mb-2 block" style={{ color: 'var(--muted)' }}>
                  Why no training?
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {REST_TYPES.map((rt) => {
                    const Icon = rt.icon;
                    const selected = restType === rt.id;
                    return (
                      <button
                        key={rt.id}
                        onClick={() => setRestType(selected ? null : rt.id)}
                        className="flex flex-col items-center gap-1 py-2 rounded-lg text-xs font-medium transition-all"
                        style={{
                          backgroundColor: selected ? 'var(--surfaceElev)' : 'var(--surface)',
                          border: selected ? `1px solid ${rt.color}` : '1px solid var(--border)',
                          color: selected ? rt.color : 'var(--muted)',
                        }}
                      >
                        <Icon className="w-4 h-4" />
                        {rt.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <input
                type="text"
                placeholder="Quick note (optional)"
                value={restNote}
                onChange={(e) => setRestNote(e.target.value)}
                className="w-full text-sm rounded-lg px-3 py-2"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />

              <textarea
                placeholder="How does your body feel?"
                value={recoveryNote}
                onChange={(e) => setRecoveryNote(e.target.value)}
                rows={2}
                className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
              />
            </>
          )}

          <input
            type="text"
            placeholder="Tomorrow's plan (e.g. 5km jog, BJJ Gi at 17:30)"
            value={tomorrow}
            onChange={(e) => setTomorrow(e.target.value)}
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
            {saving ? 'Saving...' : 'Save Evening Reflection'}
          </button>
        </div>
      )}
    </div>
  );
}

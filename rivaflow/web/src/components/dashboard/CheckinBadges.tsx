import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sun, Coffee, Moon, Check } from 'lucide-react';
import { checkinsApi, getErrorMessage } from '../../api/client';
import { REST_TYPES } from './EveningPrompt';
import type { DayCheckins } from '../../types';

export default function CheckinBadges({
  dayCheckins,
  onUpdated,
}: {
  dayCheckins: DayCheckins | null;
  onUpdated: () => void;
}) {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState<'morning' | 'midday' | 'evening' | null>(null);
  const [editing, setEditing] = useState(false);

  // Midday edit state
  const [editEnergy, setEditEnergy] = useState(3);
  const [editMiddayNote, setEditMiddayNote] = useState('');

  // Evening edit state
  const [editQuality, setEditQuality] = useState(3);
  const [editRecoveryNote, setEditRecoveryNote] = useState('');
  const [editTomorrow, setEditTomorrow] = useState('');
  const [editDidNotTrain, setEditDidNotTrain] = useState(false);
  const [editRestType, setEditRestType] = useState<string | null>(null);
  const [editRestNote, setEditRestNote] = useState('');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  if (!dayCheckins) return null;

  const slots: { key: 'morning' | 'midday' | 'evening'; label: string; icon: typeof Sun }[] = [
    { key: 'morning', label: 'Morning', icon: Sun },
    { key: 'midday', label: 'Midday', icon: Coffee },
    { key: 'evening', label: 'Evening', icon: Moon },
  ];

  const energyLabels = ['', 'Very Low', 'Low', 'Moderate', 'Good', 'Great'];
  const qualityLabels = ['', 'Poor', 'Below Avg', 'Average', 'Good', 'Excellent'];

  const toggle = (key: 'morning' | 'midday' | 'evening') => {
    if (expanded === key) {
      setExpanded(null);
      setEditing(false);
    } else {
      setExpanded(key);
      setEditing(false);
    }
  };

  const startEdit = () => {
    const checkin = expanded ? dayCheckins[expanded] : null;
    if (!checkin) return;

    if (expanded === 'midday') {
      setEditEnergy(checkin.energy_level ?? 3);
      setEditMiddayNote(checkin.midday_note ?? '');
    } else if (expanded === 'evening') {
      const isRest = checkin.checkin_type === 'rest';
      setEditDidNotTrain(isRest);
      setEditQuality(checkin.training_quality ?? 3);
      setEditRecoveryNote(checkin.recovery_note ?? '');
      setEditTomorrow(checkin.tomorrow_intention ?? '');
      setEditRestType(isRest ? (checkin.rest_type ?? null) : null);
      setEditRestNote(isRest ? (checkin.rest_note ?? '') : '');
    }
    setEditing(true);
    setError('');
  };

  const saveEdit = async () => {
    setSaving(true);
    setError('');
    try {
      if (expanded === 'midday') {
        await checkinsApi.createMidday({
          energy_level: editEnergy,
          midday_note: editMiddayNote || undefined,
        });
      } else if (expanded === 'evening') {
        await checkinsApi.createEvening({
          did_not_train: editDidNotTrain,
          rest_type: editDidNotTrain ? (editRestType || undefined) : undefined,
          rest_note: editDidNotTrain ? (editRestNote || undefined) : undefined,
          training_quality: editDidNotTrain ? undefined : editQuality,
          recovery_note: editRecoveryNote || undefined,
          tomorrow_intention: editTomorrow || undefined,
        });
      }
      setEditing(false);
      onUpdated();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const checkin = expanded ? dayCheckins[expanded] : null;

  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-2">
        {slots.map(({ key, label, icon: Icon }) => {
          const data = dayCheckins[key];
          if (!data) return null;
          const isOpen = expanded === key;
          return (
            <button
              key={key}
              onClick={() => toggle(key)}
              className="text-xs px-2.5 py-1 rounded-full flex items-center gap-1.5 transition-all"
              style={{
                backgroundColor: isOpen ? 'var(--accent)' : 'var(--success-bg)',
                color: isOpen ? '#fff' : 'var(--success)',
                border: isOpen ? '1px solid var(--accent)' : '1px solid transparent',
              }}
            >
              {isOpen ? <Icon className="w-3 h-3" /> : <Check className="w-3 h-3" />}
              {label} logged
            </button>
          );
        })}
        {dayCheckins.evening?.checkin_type === 'rest' && (
          <span
            className="text-xs px-2.5 py-1 rounded-full"
            style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
          >
            Rest day
          </span>
        )}
      </div>

      {checkin && expanded && (
        <div
          className="mt-2 p-3 rounded-xl text-sm space-y-2"
          style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
        >
          {!editing ? (
            <>
              {expanded === 'morning' && (
                <>
                  {checkin.checkin_type === 'session' && (
                    <p style={{ color: 'var(--muted)' }}>Logged with a session</p>
                  )}
                  {checkin.checkin_type === 'readiness_only' && (
                    <p style={{ color: 'var(--muted)' }}>Readiness check-in</p>
                  )}
                  {checkin.tomorrow_intention && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Plan: </span>
                      {checkin.tomorrow_intention}
                    </p>
                  )}
                </>
              )}

              {expanded === 'midday' && (
                <>
                  {checkin.energy_level != null && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Energy: </span>
                      {checkin.energy_level}/5 — {energyLabels[checkin.energy_level]}
                    </p>
                  )}
                  {checkin.midday_note && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Note: </span>
                      {checkin.midday_note}
                    </p>
                  )}
                  {!checkin.energy_level && !checkin.midday_note && (
                    <p style={{ color: 'var(--muted)' }}>Checked in</p>
                  )}
                </>
              )}

              {expanded === 'evening' && (
                <>
                  {checkin.checkin_type === 'rest' && checkin.rest_type && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Rest: </span>
                      {checkin.rest_type.charAt(0).toUpperCase() + checkin.rest_type.slice(1)}
                      {checkin.rest_note && ` — ${checkin.rest_note}`}
                    </p>
                  )}
                  {checkin.training_quality != null && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Training: </span>
                      {checkin.training_quality}/5 — {qualityLabels[checkin.training_quality]}
                    </p>
                  )}
                  {checkin.recovery_note && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Recovery: </span>
                      {checkin.recovery_note}
                    </p>
                  )}
                  {checkin.tomorrow_intention && (
                    <p style={{ color: 'var(--text)' }}>
                      <span style={{ color: 'var(--muted)' }}>Tomorrow: </span>
                      {checkin.tomorrow_intention}
                    </p>
                  )}
                  {!checkin.training_quality && !checkin.recovery_note && !checkin.rest_type && (
                    <p style={{ color: 'var(--muted)' }}>Checked in</p>
                  )}
                </>
              )}

              <div className="flex items-center justify-between pt-1">
                <p className="text-xs" style={{ color: 'var(--muted)' }}>
                  {new Date(checkin.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
                {expanded === 'morning' ? (
                  <button
                    onClick={() => navigate('/readiness')}
                    className="text-xs font-medium px-2 py-1 rounded-md"
                    style={{ color: 'var(--accent)' }}
                  >
                    Update readiness
                  </button>
                ) : (
                  <button
                    onClick={startEdit}
                    className="text-xs font-medium px-2 py-1 rounded-md"
                    style={{ color: 'var(--accent)' }}
                  >
                    Edit
                  </button>
                )}
              </div>
            </>
          ) : (
            <>
              {expanded === 'midday' && (
                <div className="space-y-2">
                  <div>
                    <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                      Energy: <span style={{ color: 'var(--text)' }}>{editEnergy}/5 — {energyLabels[editEnergy]}</span>
                    </label>
                    <input
                      type="range" min={1} max={5} value={editEnergy}
                      onChange={(e) => setEditEnergy(Number(e.target.value))}
                      className="w-full mt-1 accent-[var(--accent)]"
                    />
                  </div>
                  <input
                    type="text"
                    placeholder="Quick note (optional)"
                    value={editMiddayNote}
                    onChange={(e) => setEditMiddayNote(e.target.value)}
                    className="w-full text-sm rounded-lg px-3 py-2"
                    style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  />
                </div>
              )}

              {expanded === 'evening' && (
                <div className="space-y-2">
                  <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                    <button
                      onClick={() => setEditDidNotTrain(false)}
                      className="flex-1 py-1.5 text-xs font-semibold transition-colors"
                      style={{
                        backgroundColor: !editDidNotTrain ? 'var(--accent)' : 'var(--surface)',
                        color: !editDidNotTrain ? '#fff' : 'var(--muted)',
                      }}
                    >
                      Trained
                    </button>
                    <button
                      onClick={() => setEditDidNotTrain(true)}
                      className="flex-1 py-1.5 text-xs font-semibold transition-colors"
                      style={{
                        backgroundColor: editDidNotTrain ? 'var(--surfaceElev)' : 'var(--surface)',
                        color: editDidNotTrain ? 'var(--text)' : 'var(--muted)',
                        borderLeft: '1px solid var(--border)',
                      }}
                    >
                      Rest day
                    </button>
                  </div>

                  {!editDidNotTrain ? (
                    <div>
                      <label className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                        Quality: <span style={{ color: 'var(--text)' }}>{editQuality}/5 — {qualityLabels[editQuality]}</span>
                      </label>
                      <input
                        type="range" min={1} max={5} value={editQuality}
                        onChange={(e) => setEditQuality(Number(e.target.value))}
                        className="w-full mt-1 accent-[var(--accent)]"
                      />
                    </div>
                  ) : (
                    <div className="grid grid-cols-4 gap-1.5">
                      {REST_TYPES.map((rt) => {
                        const Icon = rt.icon;
                        const selected = editRestType === rt.id;
                        return (
                          <button
                            key={rt.id}
                            onClick={() => setEditRestType(selected ? null : rt.id)}
                            className="flex flex-col items-center gap-0.5 py-1.5 rounded-lg text-[10px] font-medium transition-all"
                            style={{
                              backgroundColor: selected ? 'var(--surface)' : 'var(--surface)',
                              border: selected ? `1px solid ${rt.color}` : '1px solid var(--border)',
                              color: selected ? rt.color : 'var(--muted)',
                            }}
                          >
                            <Icon className="w-3.5 h-3.5" />
                            {rt.label}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  <textarea
                    placeholder={editDidNotTrain ? 'Rest note (optional)' : 'Recovery note (optional)'}
                    value={editDidNotTrain ? editRestNote : editRecoveryNote}
                    onChange={(e) => editDidNotTrain ? setEditRestNote(e.target.value) : setEditRecoveryNote(e.target.value)}
                    rows={2}
                    className="w-full text-sm rounded-lg px-3 py-2 resize-none"
                    style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  />
                  <input
                    type="text"
                    placeholder="Tomorrow's plan (optional)"
                    value={editTomorrow}
                    onChange={(e) => setEditTomorrow(e.target.value)}
                    className="w-full text-sm rounded-lg px-3 py-2"
                    style={{ backgroundColor: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' }}
                  />
                </div>
              )}

              {error && <p className="text-xs" style={{ color: 'var(--error)' }}>{error}</p>}

              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => setEditing(false)}
                  className="flex-1 py-1.5 rounded-lg text-xs font-semibold"
                  style={{ backgroundColor: 'var(--surface)', color: 'var(--muted)', border: '1px solid var(--border)' }}
                >
                  Cancel
                </button>
                <button
                  onClick={saveEdit}
                  disabled={saving}
                  className="flex-1 py-1.5 rounded-lg text-xs font-semibold"
                  style={{ backgroundColor: 'var(--accent)', color: '#fff', opacity: saving ? 0.6 : 1 }}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

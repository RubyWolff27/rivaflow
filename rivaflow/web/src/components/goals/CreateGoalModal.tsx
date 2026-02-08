import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { trainingGoalsApi, glossaryApi } from '../../api/client';
import type { Movement } from '../../types';
import { useToast } from '../../contexts/ToastContext';

interface CreateGoalModalProps {
  month: string;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateGoalModal({ month, onClose, onCreated }: CreateGoalModalProps) {
  const toast = useToast();
  const [goalType, setGoalType] = useState<'frequency' | 'technique'>('frequency');
  const [metric, setMetric] = useState('sessions');
  const [targetValue, setTargetValue] = useState(10);
  const [classTypeFilter, setClassTypeFilter] = useState('');
  const [movementSearch, setMovementSearch] = useState('');
  const [movementId, setMovementId] = useState<number | null>(null);
  const [movements, setMovements] = useState<Movement[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Search movements for technique goals
  useEffect(() => {
    if (goalType !== 'technique' || movementSearch.length < 2) {
      setMovements([]);
      return;
    }
    let cancelled = false;
    const search = async () => {
      try {
        const res = await glossaryApi.list({ search: movementSearch, limit: 10 });
        if (!cancelled) setMovements(res.data);
      } catch {
        if (!cancelled) setMovements([]);
      }
    };
    const timer = setTimeout(search, 300);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [goalType, movementSearch]);

  // Reset metric when switching goal type
  useEffect(() => {
    if (goalType === 'technique') {
      setMetric('technique_count');
    } else if (metric === 'technique_count') {
      setMetric('sessions');
    }
  }, [goalType, metric]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (goalType === 'technique' && !movementId) {
      toast.showToast('error', 'Please select a movement');
      return;
    }
    setSubmitting(true);
    try {
      await trainingGoalsApi.create({
        goal_type: goalType,
        metric,
        target_value: targetValue,
        month,
        movement_id: goalType === 'technique' ? movementId : null,
        class_type_filter: classTypeFilter || null,
      });
      toast.showToast('success', 'Goal created');
      onCreated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create goal';
      toast.showToast('error', msg);
    } finally {
      setSubmitting(false);
    }
  };

  const selectMovement = (m: Movement) => {
    setMovementId(m.id);
    setMovementSearch(m.name);
    setMovements([]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-[14px] p-6 max-h-[90vh] overflow-y-auto"
        style={{ backgroundColor: 'var(--surface)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
            New Monthly Goal
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
            style={{ color: 'var(--muted)' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Goal type toggle */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Goal Type
            </label>
            <div className="flex gap-2">
              {(['frequency', 'technique'] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setGoalType(type)}
                  className="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
                  style={{
                    backgroundColor: goalType === type ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: goalType === type ? '#FFFFFF' : 'var(--text)',
                  }}
                >
                  {type === 'frequency' ? 'Frequency' : 'Technique'}
                </button>
              ))}
            </div>
          </div>

          {/* Frequency: metric selection */}
          {goalType === 'frequency' && (
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                Metric
              </label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{
                  backgroundColor: 'var(--surfaceElev)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                }}
              >
                <option value="sessions">Sessions</option>
                <option value="hours">Hours</option>
                <option value="rolls">Rolls</option>
                <option value="submissions">Submissions</option>
              </select>
            </div>
          )}

          {/* Technique: movement search */}
          {goalType === 'technique' && (
            <div className="relative">
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                Movement
              </label>
              <input
                type="text"
                value={movementSearch}
                onChange={(e) => { setMovementSearch(e.target.value); setMovementId(null); }}
                placeholder="Search movements..."
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{
                  backgroundColor: 'var(--surfaceElev)',
                  color: 'var(--text)',
                  border: '1px solid var(--border)',
                }}
              />
              {movements.length > 0 && (
                <div
                  className="absolute z-10 left-0 right-0 mt-1 rounded-lg shadow-lg max-h-48 overflow-y-auto"
                  style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
                >
                  {movements.map((m) => (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => selectMovement(m)}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-[var(--surfaceElev)] transition-colors"
                      style={{ color: 'var(--text)' }}
                    >
                      {m.name}
                      <span className="ml-2 text-xs" style={{ color: 'var(--muted)' }}>
                        {m.category}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Class type filter (optional) */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Class Type Filter
              <span className="ml-1 font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
            </label>
            <select
              value={classTypeFilter}
              onChange={(e) => setClassTypeFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
            >
              <option value="">All class types</option>
              <option value="gi">Gi</option>
              <option value="nogi">No-Gi</option>
              <option value="open_mat">Open Mat</option>
              <option value="private">Private</option>
              <option value="competition">Competition</option>
              <option value="drill">Drill</option>
              <option value="s_and_c">S&C</option>
              <option value="mobility">Mobility</option>
            </select>
          </div>

          {/* Target value */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Target
            </label>
            <input
              type="number"
              min={1}
              value={targetValue}
              onChange={(e) => setTargetValue(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            style={{
              backgroundColor: 'var(--accent)',
              color: '#FFFFFF',
            }}
          >
            {submitting ? 'Creating...' : 'Create Goal'}
          </button>
        </form>
      </div>
    </div>
  );
}

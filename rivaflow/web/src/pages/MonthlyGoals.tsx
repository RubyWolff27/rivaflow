import { useState, useEffect, useCallback } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { Plus, Crosshair } from 'lucide-react';
import { trainingGoalsApi } from '../api/client';
import { logger } from '../utils/logger';
import type { TrainingGoal } from '../types';
import { PageHeader, Card, EmptyState } from '../components/ui';
import MonthSelector from '../components/goals/MonthSelector';
import TrainingGoalCard from '../components/goals/TrainingGoalCard';
import CreateGoalModal from '../components/goals/CreateGoalModal';
import { useToast } from '../contexts/ToastContext';

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export default function MonthlyGoals() {
  usePageTitle('Monthly Goals');
  const toast = useToast();
  const [month, setMonth] = useState(currentMonth);
  const [goals, setGoals] = useState<TrainingGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [editingGoal, setEditingGoal] = useState<{id: number; value: string} | null>(null);

  const fetchGoals = useCallback(async (m: string, signal?: AbortSignal) => {
    setLoading(true);
    try {
      const res = await trainingGoalsApi.list(m);
      if (!signal?.aborted) setGoals(res.data);
    } catch (err) {
      if (!signal?.aborted) {
        logger.error('Failed to load goals:', err);
        setGoals([]);
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchGoals(month, ctrl.signal);
    return () => ctrl.abort();
  }, [month, fetchGoals]);

  const handleDelete = (goalId: number) => {
    setConfirmDeleteId(goalId);
  };

  const confirmDelete = async () => {
    if (!confirmDeleteId) return;
    try {
      await trainingGoalsApi.delete(confirmDeleteId);
      setGoals((prev) => prev.filter((g) => g.id !== confirmDeleteId));
      toast.success('Goal deleted');
    } catch {
      toast.error('Failed to delete goal');
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const handleEdit = (goal: TrainingGoal) => {
    setEditingGoal({ id: goal.id, value: String(goal.target_value) });
  };

  const submitEdit = async () => {
    if (!editingGoal) return;
    const parsed = parseInt(editingGoal.value);
    if (isNaN(parsed) || parsed < 1) {
      toast.error('Target must be a positive number');
      return;
    }
    try {
      const res = await trainingGoalsApi.update(editingGoal.id, { target_value: parsed });
      setGoals((prev) => prev.map((g) => (g.id === editingGoal.id ? res.data : g)));
      toast.success('Goal updated');
      setEditingGoal(null);
    } catch {
      toast.error('Failed to update goal');
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Monthly Goals"
        subtitle="Set and track your training goals"
        actions={
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            <Plus className="w-4 h-4" /> Add Goal
          </button>
        }
      />

      <MonthSelector month={month} onChange={setMonth} />

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-4">
              <div className="animate-pulse">
                <div className="h-4 bg-[var(--surfaceElev)] rounded w-1/3 mb-3" />
                <div className="h-2 bg-[var(--surfaceElev)] rounded w-full" />
              </div>
            </Card>
          ))}
        </div>
      ) : goals.length === 0 ? (
        <EmptyState
          icon={Crosshair}
          title="No goals for this month"
          description="Create monthly goals to track your training targets. Progress updates automatically from your logged sessions."
        />
      ) : (
        <div className="space-y-3">
          {goals.map((goal) => (
            <TrainingGoalCard
              key={goal.id}
              goal={goal}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateGoalModal
          month={month}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            fetchGoals(month);
          }}
        />
      )}

      {confirmDeleteId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-[14px] p-6 max-w-sm mx-4">
            <p className="text-sm font-medium mb-4" style={{ color: 'var(--text)' }}>Delete this goal?</p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="px-3 py-1.5 text-sm rounded-lg border border-[var(--border)]"
                style={{ color: 'var(--text)' }}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-3 py-1.5 text-sm rounded-lg text-white"
                style={{ backgroundColor: 'var(--error)' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {editingGoal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-[var(--surface)] border border-[var(--border)] rounded-[14px] p-6 max-w-sm mx-4">
            <p className="text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>New target value</p>
            <input
              type="number"
              min={1}
              value={editingGoal.value}
              onChange={(e) => setEditingGoal({ ...editingGoal, value: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && submitEdit()}
              autoFocus
              className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg bg-[var(--surface)] mb-4"
              style={{ color: 'var(--text)' }}
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setEditingGoal(null)}
                className="px-3 py-1.5 text-sm rounded-lg border border-[var(--border)]"
                style={{ color: 'var(--text)' }}
              >
                Cancel
              </button>
              <button
                onClick={submitEdit}
                className="px-3 py-1.5 text-sm rounded-lg text-white"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

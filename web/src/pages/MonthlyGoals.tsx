import { useState, useEffect, useCallback } from 'react';
import { Plus, Crosshair } from 'lucide-react';
import { trainingGoalsApi } from '../api/client';
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
  const toast = useToast();
  const [month, setMonth] = useState(currentMonth);
  const [goals, setGoals] = useState<TrainingGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editGoal, setEditGoal] = useState<TrainingGoal | null>(null);

  const fetchGoals = useCallback(async (m: string, signal?: AbortSignal) => {
    setLoading(true);
    try {
      const res = await trainingGoalsApi.list(m);
      if (!signal?.aborted) setGoals(res.data);
    } catch (err) {
      if (!signal?.aborted) {
        console.error('Failed to load goals:', err);
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

  const handleDelete = async (goalId: number) => {
    if (!confirm('Delete this goal?')) return;
    try {
      await trainingGoalsApi.delete(goalId);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
      toast.showToast('success', 'Goal deleted');
    } catch {
      toast.showToast('error', 'Failed to delete goal');
    }
  };

  const handleEdit = async (goal: TrainingGoal) => {
    const newTarget = prompt('New target value:', String(goal.target_value));
    if (!newTarget) return;
    const parsed = parseInt(newTarget);
    if (isNaN(parsed) || parsed < 1) {
      toast.showToast('error', 'Target must be a positive number');
      return;
    }
    try {
      const res = await trainingGoalsApi.update(goal.id, { target_value: parsed });
      setGoals((prev) => prev.map((g) => (g.id === goal.id ? res.data : g)));
      toast.showToast('success', 'Goal updated');
    } catch {
      toast.showToast('error', 'Failed to update goal');
    }
  };

  // Suppress unused var lint — editGoal reserved for future inline editing
  void editGoal;
  void setEditGoal;

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
    </div>
  );
}

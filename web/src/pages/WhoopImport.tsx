import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { useNavigate } from 'react-router-dom';
import { whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton, EmptyState } from '../components/ui';
import { formatClassType, ACTIVITY_COLORS } from '../constants/activity';
import { Activity, Clock, Zap, Heart, X, Check, RefreshCw } from 'lucide-react';
import type { WhoopWorkoutMatch } from '../types';

type ImportableWorkout = WhoopWorkoutMatch & { suggested_class_type: string };

export default function WhoopImport() {
  usePageTitle('Import Activities');
  const toast = useToast();
  const navigate = useNavigate();
  const [workouts, setWorkouts] = useState<ImportableWorkout[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [importing, setImporting] = useState<number | null>(null);

  const loadWorkouts = async () => {
    setLoading(true);
    try {
      const res = await whoopApi.getImportable();
      setWorkouts(res.data?.workouts ?? []);
    } catch (err) {
      logger.error('Failed to load importable workouts', err);
      toast.error('Failed to load workouts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadWorkouts(); }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await whoopApi.sync(14);
      toast.success('Synced with WHOOP');
      await loadWorkouts();
    } catch (err) {
      logger.error('Sync failed', err);
      toast.error('Failed to sync with WHOOP');
    } finally {
      setSyncing(false);
    }
  };

  const handleImport = async (workoutId: number) => {
    setImporting(workoutId);
    try {
      const res = await whoopApi.importWorkout(workoutId);
      toast.success('Session created');
      setWorkouts(prev => prev.filter(w => w.id !== workoutId));
      navigate(`/session/${res.data.session_id}`);
    } catch (err) {
      logger.error('Import failed', err);
      toast.error('Failed to import workout');
    } finally {
      setImporting(null);
    }
  };

  const handleDismiss = async (workoutId: number) => {
    try {
      await whoopApi.dismissWorkout(workoutId);
      setWorkouts(prev => prev.filter(w => w.id !== workoutId));
    } catch (err) {
      logger.error('Dismiss failed', err);
      toast.error('Failed to dismiss workout');
    }
  };

  const formatTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString('en-AU', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch { return isoStr; }
  };

  const durationMins = (start: string, end: string) => {
    try {
      return Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60000);
    } catch { return 0; }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <CardSkeleton lines={2} />
        <CardSkeleton lines={3} />
        <CardSkeleton lines={3} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)]">Import Activities</h1>
          <p className="text-sm text-[var(--muted)]">
            Import non-BJJ workouts from WHOOP into RivaFlow
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          Sync
        </button>
      </div>

      {workouts.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No activities to import"
          description="All recent WHOOP workouts are either already imported or are BJJ sessions (auto-created). Tap Sync to refresh."
        />
      ) : (
        <div className="space-y-3">
          {workouts.map((w) => {
            const mins = durationMins(w.start_time, w.end_time);
            const color = ACTIVITY_COLORS[w.suggested_class_type] || 'var(--accent)';
            return (
              <div key={w.id} className="card">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="px-2 py-0.5 rounded text-xs font-semibold uppercase"
                        style={{ backgroundColor: color + '1A', color }}
                      >
                        {formatClassType(w.suggested_class_type)}
                      </span>
                      {w.sport_name && (
                        <span className="text-xs text-[var(--muted)]">{w.sport_name}</span>
                      )}
                    </div>
                    <p className="text-sm text-[var(--text)]">{formatTime(w.start_time)}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm text-[var(--muted)] mb-3">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {mins} min
                  </span>
                  {w.strain != null && (
                    <span className="flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5" />
                      {Number(w.strain).toFixed(1)}
                    </span>
                  )}
                  {w.avg_heart_rate != null && (
                    <span className="flex items-center gap-1">
                      <Heart className="w-3.5 h-3.5" />
                      {w.avg_heart_rate} bpm
                    </span>
                  )}
                  {w.calories != null && (
                    <span className="text-xs">{w.calories} cal</span>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleImport(w.id)}
                    disabled={importing === w.id}
                    className="btn-primary flex-1 flex items-center justify-center gap-2 text-sm py-2"
                  >
                    <Check className="w-4 h-4" />
                    {importing === w.id ? 'Importing...' : 'Import'}
                  </button>
                  <button
                    onClick={() => handleDismiss(w.id)}
                    className="btn-secondary px-3 py-2"
                    title="Dismiss"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

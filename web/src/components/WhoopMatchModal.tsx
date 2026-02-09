import { useEffect } from 'react';
import type { WhoopWorkoutMatch } from '../types';
import { X, Heart, Flame, Zap } from 'lucide-react';

interface WhoopMatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  matches: WhoopWorkoutMatch[];
  onSelect: (workoutCacheId: number) => void;
  onManual: () => void;
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoStr;
  }
}

export default function WhoopMatchModal({ isOpen, onClose, matches, onSelect, onManual }: WhoopMatchModalProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-[var(--surface)] rounded-[14px] shadow-xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold">Select WHOOP Workout</h2>
          <button onClick={onClose} className="text-[var(--muted)] hover:opacity-80">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-y-auto flex-1 space-y-3">
          {matches.length === 0 ? (
            <p className="text-center text-[var(--muted)] py-6">No matching workouts found.</p>
          ) : (
            matches.map((workout, i) => {
              const isBest = i === 0;
              return (
                <div
                  key={workout.id}
                  className="rounded-[14px] p-4 transition-colors"
                  style={{
                    backgroundColor: isBest ? 'rgba(var(--accent-rgb), 0.08)' : 'var(--surfaceElev)',
                    border: isBest ? '2px solid var(--accent)' : '1px solid var(--border)',
                  }}
                >
                  {isBest && (
                    <span className="inline-block text-xs font-semibold px-2 py-0.5 rounded-full mb-2"
                      style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                      Best Match
                    </span>
                  )}

                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">
                      {formatTime(workout.start_time)} - {formatTime(workout.end_time)}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                      style={{
                        backgroundColor: workout.overlap_pct >= 80 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                        color: workout.overlap_pct >= 80 ? 'rgb(34, 197, 94)' : 'rgb(234, 179, 8)',
                      }}>
                      {workout.overlap_pct}% match
                    </span>
                  </div>

                  {workout.sport_name && (
                    <p className="text-xs text-[var(--muted)] mb-2">{workout.sport_name}</p>
                  )}

                  <div className="grid grid-cols-3 gap-3 mb-3">
                    {workout.strain != null && (
                      <div className="flex items-center gap-1 text-sm">
                        <Flame className="w-3.5 h-3.5 text-orange-500" />
                        <span className="font-semibold">{workout.strain.toFixed(1)}</span>
                      </div>
                    )}
                    {workout.avg_heart_rate != null && (
                      <div className="flex items-center gap-1 text-sm">
                        <Heart className="w-3.5 h-3.5 text-red-500" />
                        <span className="font-semibold">{workout.avg_heart_rate}</span>
                        <span className="text-xs text-[var(--muted)]">bpm</span>
                      </div>
                    )}
                    {workout.calories != null && (
                      <div className="flex items-center gap-1 text-sm">
                        <Zap className="w-3.5 h-3.5 text-yellow-500" />
                        <span className="font-semibold">{workout.calories}</span>
                        <span className="text-xs text-[var(--muted)]">cal</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => onSelect(workout.id)}
                    className="w-full py-2 rounded-lg text-sm font-medium transition-colors"
                    style={{
                      backgroundColor: isBest ? 'var(--accent)' : 'var(--surfaceElev)',
                      color: isBest ? '#fff' : 'var(--text)',
                      border: isBest ? 'none' : '1px solid var(--border)',
                    }}
                  >
                    Apply This Workout
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[var(--border)] text-center">
          <button
            onClick={onManual}
            className="text-sm text-[var(--accent)] hover:opacity-80"
          >
            Enter manually instead
          </button>
        </div>
      </div>
    </div>
  );
}

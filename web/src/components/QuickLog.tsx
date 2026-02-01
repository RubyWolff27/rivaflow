import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { sessionsApi, profileApi, restApi } from '../api/client';
import { PrimaryButton, SecondaryButton } from './ui';
import { useToast } from '../contexts/ToastContext';

interface QuickLogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function QuickLog({ isOpen, onClose, onSuccess }: QuickLogProps) {
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  // Activity type: 'training' or 'rest'
  const [activityType, setActivityType] = useState<'training' | 'rest'>('training');

  // Training session fields
  const [gym, setGym] = useState('');
  const [duration, setDuration] = useState(90);
  const [intensity, setIntensity] = useState(3);

  // Rest day fields
  const [restType, setRestType] = useState('active');
  const [restNote, setRestNote] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDefaultGym();
    }
  }, [isOpen]);

  const loadDefaultGym = async () => {
    try {
      // First try to get home gym from profile
      const profileRes = await profileApi.get();
      if (profileRes.data?.default_gym) {
        setGym(profileRes.data.default_gym);
        return;
      }

      // Fall back to last session's gym if no home gym set
      const res = await sessionsApi.list(1);
      if (res.data && res.data.length > 0) {
        const last = res.data[0].gym_name || '';
        setGym(last);
      }
    } catch (error) {
      console.error('Error loading gym:', error);
    }
  };

  const handleQuickLog = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];

      if (activityType === 'rest') {
        // Log rest day
        await restApi.logRestDay({
          rest_type: restType,
          note: restNote || undefined,
          rest_date: today,
        });
        toast.success('Rest day logged successfully');
        // Reset rest form
        setRestType('active');
        setRestNote('');
      } else {
        // Log training session
        if (!gym.trim()) {
          toast.error('Please enter a gym name');
          setLoading(false);
          return;
        }

        await sessionsApi.create({
          gym_name: gym,
          session_date: today,
          duration_mins: duration,
          intensity,
          class_type: 'Open Mat',
          rolls: 0,
        });
        toast.success('Session logged successfully');
        // Reset training form
        setDuration(90);
        setIntensity(3);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (error) {
      console.error('Error logging activity:', error);
      toast.error(`Failed to log ${activityType === 'rest' ? 'rest day' : 'session'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const durationOptions = [60, 75, 90, 120];
  const intensityOptions = [1, 2, 3, 4, 5];

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="quick-log-title"
    >
      <div
        className="w-full max-w-md rounded-t-[24px] sm:rounded-[24px] p-6 space-y-6"
        style={{ backgroundColor: 'var(--surface)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 id="quick-log-title" className="text-xl font-semibold" style={{ color: 'var(--text)' }}>
            Quick Log
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg"
            style={{ color: 'var(--muted)' }}
            aria-label="Close quick log dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Form */}
        <div className="space-y-4">
          {/* Activity Type Selector */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Activity Type
            </label>
            <div className="flex gap-2" role="group" aria-label="Activity type">
              <button
                onClick={() => setActivityType('training')}
                className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
                style={{
                  backgroundColor: activityType === 'training' ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: activityType === 'training' ? '#FFFFFF' : 'var(--text)',
                  border: activityType === 'training' ? 'none' : '1px solid var(--border)',
                }}
                aria-pressed={activityType === 'training'}
              >
                Training
              </button>
              <button
                onClick={() => setActivityType('rest')}
                className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
                style={{
                  backgroundColor: activityType === 'rest' ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: activityType === 'rest' ? '#FFFFFF' : 'var(--text)',
                  border: activityType === 'rest' ? 'none' : '1px solid var(--border)',
                }}
                aria-pressed={activityType === 'rest'}
              >
                Rest Day
              </button>
            </div>
          </div>

          {/* Training Session Fields */}
          {activityType === 'training' && (
            <>
              {/* Gym */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Gym
                </label>
                <input
                  type="text"
                  value={gym}
                  onChange={(e) => setGym(e.target.value)}
                  className="input w-full"
                  placeholder="Enter gym name"
                  autoFocus
                />
              </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Duration (minutes)
            </label>
            <div className="flex gap-2" role="group" aria-label="Duration options">
              {durationOptions.map((mins) => (
                <button
                  key={mins}
                  onClick={() => setDuration(mins)}
                  className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
                  style={{
                    backgroundColor: duration === mins ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: duration === mins ? '#FFFFFF' : 'var(--text)',
                    border: duration === mins ? 'none' : '1px solid var(--border)',
                  }}
                  aria-label={`${mins} minutes`}
                  aria-pressed={duration === mins}
                >
                  {mins}m
                </button>
              ))}
            </div>
          </div>

              {/* Intensity */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Intensity
                </label>
                <div className="flex gap-2" role="group" aria-label="Intensity options">
                  {intensityOptions.map((level) => (
                    <button
                      key={level}
                      onClick={() => setIntensity(level)}
                      className="flex-1 py-3 rounded-lg font-semibold transition-all"
                      style={{
                        backgroundColor: intensity === level ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: intensity === level ? '#FFFFFF' : 'var(--text)',
                        border: intensity === level ? 'none' : '1px solid var(--border)',
                      }}
                      aria-label={`Intensity level ${level} of 5`}
                      aria-pressed={intensity === level}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Rest Day Fields */}
          {activityType === 'rest' && (
            <>
              {/* Rest Type */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Rest Type
                </label>
                <div className="flex gap-2" role="group" aria-label="Rest type options">
                  {['active', 'passive', 'injury'].map((type) => (
                    <button
                      key={type}
                      onClick={() => setRestType(type)}
                      className="flex-1 py-3 rounded-lg font-medium text-sm transition-all capitalize"
                      style={{
                        backgroundColor: restType === type ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: restType === type ? '#FFFFFF' : 'var(--text)',
                        border: restType === type ? 'none' : '1px solid var(--border)',
                      }}
                      aria-pressed={restType === type}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              {/* Rest Note */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Note (optional)
                </label>
                <textarea
                  value={restNote}
                  onChange={(e) => setRestNote(e.target.value)}
                  className="input w-full"
                  rows={3}
                  placeholder="Any notes about your rest day..."
                />
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <SecondaryButton onClick={onClose} className="flex-1">
            Cancel
          </SecondaryButton>
          <PrimaryButton onClick={handleQuickLog} disabled={loading} className="flex-1">
            {loading ? 'Logging...' : activityType === 'rest' ? 'Log Rest Day' : 'Log Session'}
          </PrimaryButton>
        </div>

        {/* Full log link */}
        <p className="text-xs text-center" style={{ color: 'var(--muted)' }}>
          Need more details?{' '}
          <a href="/log" className="underline" style={{ color: 'var(--accent)' }}>
            Use full form
          </a>
        </p>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { X, Mic, MicOff } from 'lucide-react';
import { sessionsApi, profileApi, restApi, friendsApi } from '../api/client';
import { PrimaryButton, SecondaryButton, ClassTypeChips, IntensityChips } from './ui';
import { useToast } from '../contexts/ToastContext';
import { getLocalDateString } from '../utils/date';
import { triggerInsightRefresh } from '../hooks/useInsightRefresh';
import type { Friend } from '../types';

const TIME_OPTIONS = [
  { label: '6:30am', value: '06:30' },
  { label: '12pm', value: '12:00' },
  { label: '5:30pm', value: '17:30' },
  { label: '7pm', value: '19:00' },
] as const;

interface QuickLogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (sessionId?: number) => void;
}

export default function QuickLog({ isOpen, onClose, onSuccess }: QuickLogProps) {
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  // Activity type: 'training' or 'rest'
  const [activityType, setActivityType] = useState<'training' | 'rest'>('training');

  // Training session fields
  const [gym, setGym] = useState('');
  const [classType, setClassType] = useState('gi');
  const [classTime, setClassTime] = useState('');
  const [duration, setDuration] = useState(90);
  const [intensity, setIntensity] = useState(3);
  const [quickPartners, setQuickPartners] = useState('');
  const [quickRolls, setQuickRolls] = useState(0);
  const [notes, setNotes] = useState('');

  // Partner pills
  const [topPartners, setTopPartners] = useState<Friend[]>([]);
  const [selectedPartnerIds, setSelectedPartnerIds] = useState<Set<number>>(new Set());

  // Voice-to-text
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const hasSpeechApi = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  // Rest day fields
  const [restType, setRestType] = useState('active');
  const [restNote, setRestNote] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [profileRes, partnersRes] = await Promise.all([
          profileApi.get(),
          friendsApi.listPartners(),
        ]);
        if (cancelled) return;
        if (profileRes.data?.primary_training_type) {
          setClassType(profileRes.data.primary_training_type);
        }
        if (profileRes.data?.default_gym) {
          setGym(profileRes.data.default_gym);
        } else {
          const res = await sessionsApi.list(1);
          if (!cancelled && res.data && res.data.length > 0) {
            const last = res.data[0].gym_name || '';
            setGym(last);
          }
        }
        if (partnersRes.data) {
          setTopPartners(partnersRes.data.slice(0, 5));
        }
      } catch (error) {
        if (!cancelled) console.error('Error loading data:', error);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [isOpen]);

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  const togglePartner = (id: number) => {
    setSelectedPartnerIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleRecording = () => {
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setNotes(prev => prev ? `${prev} ${transcript}` : transcript);
    };
    recognition.onend = () => setIsRecording(false);
    recognition.onerror = () => setIsRecording(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  };

  const handleQuickLog = async () => {
    setLoading(true);
    try {
      const today = getLocalDateString();

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

        // Merge pill-selected partner names + typed names
        const pillNames = topPartners
          .filter(p => selectedPartnerIds.has(p.id))
          .map(p => p.name);
        const typedNames = quickPartners
          ? quickPartners.split(',').map(p => p.trim()).filter(p => p !== '')
          : [];
        const allPartners = [...pillNames, ...typedNames];

        const response = await sessionsApi.create({
          gym_name: gym,
          session_date: today,
          duration_mins: duration,
          intensity,
          class_type: classType,
          class_time: classTime || undefined,
          rolls: quickRolls,
          partners: allPartners.length > 0 ? allPartners : undefined,
          notes: notes || undefined,
        });
        toast.success('Session logged successfully');
        triggerInsightRefresh(response.data?.id);
        // Reset training form
        setDuration(90);
        setIntensity(3);
        setClassTime('');
        setQuickPartners('');
        setQuickRolls(0);
        setNotes('');
        setSelectedPartnerIds(new Set());

        if (onSuccess) onSuccess(response.data?.id);
        onClose();
        return;
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
        className="w-full max-w-md rounded-t-[24px] sm:rounded-[24px] p-6 space-y-6 max-h-[90vh] overflow-y-auto"
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
              {/* Class Type */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Class Type
                </label>
                <ClassTypeChips value={classType} onChange={setClassType} size="sm" />
              </div>

              {/* Class Time */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Class Time <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
                </label>
                <div className="flex gap-2" role="group" aria-label="Class time options">
                  {TIME_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setClassTime(classTime === opt.value ? '' : opt.value)}
                      className="flex-1 py-2 rounded-lg font-medium text-xs transition-all"
                      style={{
                        backgroundColor: classTime === opt.value ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: classTime === opt.value ? '#FFFFFF' : 'var(--text)',
                        border: classTime === opt.value ? 'none' : '1px solid var(--border)',
                      }}
                      aria-pressed={classTime === opt.value}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Gym */}
              <div>
                <label htmlFor="quick-log-gym" className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Gym
                </label>
                <input
                  id="quick-log-gym"
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
                <IntensityChips value={intensity} onChange={setIntensity} size="sm" />
              </div>

              {/* Rolls */}
              {['gi', 'no-gi', 'open-mat', 'competition'].includes(classType) && (
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                    Rolls
                  </label>
                  <input
                    type="number"
                    value={quickRolls}
                    onChange={(e) => setQuickRolls(parseInt(e.target.value) || 0)}
                    className="input w-full"
                    placeholder="0"
                    min="0"
                  />
                </div>
              )}

              {/* Partners */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Partners <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
                </label>
                {topPartners.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {topPartners.map((partner) => {
                      const selected = selectedPartnerIds.has(partner.id);
                      return (
                        <button
                          key={partner.id}
                          type="button"
                          onClick={() => togglePartner(partner.id)}
                          className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                          style={{
                            backgroundColor: selected ? 'var(--accent)' : 'var(--surfaceElev)',
                            color: selected ? '#FFFFFF' : 'var(--text)',
                            border: selected ? 'none' : '1px solid var(--border)',
                          }}
                        >
                          {partner.name}
                        </button>
                      );
                    })}
                  </div>
                )}
                <input
                  type="text"
                  value={quickPartners}
                  onChange={(e) => setQuickPartners(e.target.value)}
                  className="input w-full"
                  placeholder="e.g., Alex, Sarah"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Notes <span className="font-normal" style={{ color: 'var(--muted)' }}>(optional)</span>
                </label>
                <div className="relative">
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="input w-full"
                    rows={3}
                    placeholder="Session notes..."
                  />
                  {hasSpeechApi && (
                    <button
                      type="button"
                      onClick={toggleRecording}
                      className="absolute bottom-2 right-2 p-1.5 rounded-lg transition-all"
                      style={{
                        backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
                        color: isRecording ? '#FFFFFF' : 'var(--muted)',
                      }}
                      aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
                    >
                      {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    </button>
                  )}
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

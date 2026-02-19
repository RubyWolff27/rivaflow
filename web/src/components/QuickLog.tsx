import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { X, Mic, MicOff } from 'lucide-react';
import { sessionsApi, profileApi, restApi, friendsApi, socialApi } from '../api/client';
import { logger } from '../utils/logger';
import { PrimaryButton, SecondaryButton, ClassTypeChips, IntensityChips } from './ui';
import { useToast } from '../contexts/ToastContext';
import { getLocalDateString } from '../utils/date';
import { triggerInsightRefresh } from '../utils/insightRefresh';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { mapSocialFriends } from '../hooks/useSessionForm';
import type { Friend } from '../types';

const HH_MM_RE = /^([01]\d|2[0-3]):([0-5]\d)$/;

/** Extract gym name before comma (strips address suffix like ", City, State"). */
function extractGymName(fullName: string): string {
  const commaIdx = fullName.indexOf(',');
  return commaIdx > 0 ? fullName.substring(0, commaIdx).trim() : fullName;
}

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

  // Custom inputs
  const [customDuration, setCustomDuration] = useState(false);
  const [customTime, setCustomTime] = useState(false);

  // Voice-to-text
  const onTranscript = useCallback((transcript: string) => {
    setNotes(prev => prev ? `${prev} ${transcript}` : transcript);
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
  }, [toast]);
  const { isRecording, isTranscribing, hasSpeechApi, toggleRecording } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

  // Rest day fields
  const [restType, setRestType] = useState('active');
  const [restNote, setRestNote] = useState('');

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    const doLoad = async () => {
      try {
        const [profileRes, partnersRes, socialFriendsRes] = await Promise.all([
          profileApi.get(),
          friendsApi.listPartners(),
          socialApi.getFriends().catch(() => ({ data: { friends: [] } })),
        ]);
        if (cancelled) return;
        if (profileRes.data?.primary_training_type) {
          setClassType(profileRes.data.primary_training_type);
        }
        if (profileRes.data?.default_gym) {
          setGym(extractGymName(profileRes.data.default_gym));
        } else {
          const res = await sessionsApi.list(1);
          if (!cancelled && res.data && res.data.length > 0) {
            const last = res.data[0].gym_name || '';
            setGym(extractGymName(last));
          }
        }
        if (partnersRes.data) {
          const manualPartners: Friend[] = partnersRes.data;
          const socialFriends = mapSocialFriends(socialFriendsRes.data.friends || []);
          const manualNames = new Set(manualPartners.map(p => p.name.toLowerCase()));
          const merged = [
            ...manualPartners,
            ...socialFriends.filter(sf => !manualNames.has(sf.name.toLowerCase())),
          ];
          setTopPartners(merged.slice(0, 5));
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading data:', error);
          toast.error('Failed to load form data');
        }
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [isOpen]);

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

  const handleQuickLog = async () => {
    setLoading(true);
    try {
      const today = getLocalDateString();

      if (activityType === 'rest') {
        // Log rest day
        await restApi.logRestDay({
          rest_type: restType,
          rest_note: restNote || undefined,
          check_date: today,
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
          class_time: classTime && HH_MM_RE.test(classTime) ? classTime : undefined,
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
      logger.error('Error logging activity:', error);
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
                      onClick={() => { setClassTime(classTime === opt.value ? '' : opt.value); setCustomTime(false); }}
                      className="flex-1 py-2 rounded-lg font-medium text-xs transition-all"
                      style={{
                        backgroundColor: !customTime && classTime === opt.value ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: !customTime && classTime === opt.value ? '#FFFFFF' : 'var(--text)',
                        border: !customTime && classTime === opt.value ? 'none' : '1px solid var(--border)',
                      }}
                      aria-pressed={!customTime && classTime === opt.value}
                    >
                      {opt.label}
                    </button>
                  ))}
                  <button
                    onClick={() => setCustomTime(!customTime)}
                    className="flex-1 py-2 rounded-lg font-medium text-xs transition-all"
                    style={{
                      backgroundColor: customTime ? 'var(--accent)' : 'var(--surfaceElev)',
                      color: customTime ? '#FFFFFF' : 'var(--text)',
                      border: customTime ? 'none' : '1px solid var(--border)',
                    }}
                    aria-pressed={customTime}
                  >
                    Other
                  </button>
                </div>
                {customTime && (
                  <input
                    type="time"
                    value={classTime}
                    onChange={(e) => setClassTime(e.target.value)}
                    className="input w-full mt-2"
                    autoFocus
                  />
                )}
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
                      onClick={() => { setDuration(mins); setCustomDuration(false); }}
                      className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
                      style={{
                        backgroundColor: !customDuration && duration === mins ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: !customDuration && duration === mins ? '#FFFFFF' : 'var(--text)',
                        border: !customDuration && duration === mins ? 'none' : '1px solid var(--border)',
                      }}
                      aria-label={`${mins} minutes`}
                      aria-pressed={!customDuration && duration === mins}
                    >
                      {mins}m
                    </button>
                  ))}
                  <button
                    onClick={() => setCustomDuration(!customDuration)}
                    className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
                    style={{
                      backgroundColor: customDuration ? 'var(--accent)' : 'var(--surfaceElev)',
                      color: customDuration ? '#FFFFFF' : 'var(--text)',
                      border: customDuration ? 'none' : '1px solid var(--border)',
                    }}
                    aria-pressed={customDuration}
                  >
                    Custom
                  </button>
                </div>
                {customDuration && (
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value) || 0)}
                    className="input w-full mt-2"
                    placeholder="Minutes"
                    min="1"
                    max="600"
                    autoFocus
                  />
                )}
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
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setQuickRolls(Math.max(0, quickRolls - 1))}
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold transition-colors"
                      style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
                      aria-label="Decrease rolls"
                    >
                      &minus;
                    </button>
                    <input
                      type="number"
                      value={quickRolls}
                      onChange={(e) => setQuickRolls(parseInt(e.target.value) || 0)}
                      className="input w-20 text-center"
                      min="0"
                    />
                    <button
                      type="button"
                      onClick={() => setQuickRolls(quickRolls + 1)}
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold transition-colors"
                      style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
                      aria-label="Increase rolls"
                    >
                      +
                    </button>
                  </div>
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
                      disabled={isTranscribing}
                      className="absolute bottom-2 right-2 p-1.5 rounded-lg transition-all"
                      style={{
                        backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
                        color: isRecording ? '#FFFFFF' : 'var(--muted)',
                        opacity: isTranscribing ? 0.6 : 1,
                      }}
                      aria-label={isTranscribing ? 'Transcribing audio...' : isRecording ? 'Stop recording' : 'Start voice input'}
                    >
                      {isTranscribing ? (
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      ) : isRecording ? (
                        <MicOff className="w-4 h-4" />
                      ) : (
                        <Mic className="w-4 h-4" />
                      )}
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
                <div className="grid grid-cols-3 gap-2" role="group" aria-label="Rest type options">
                  {([
                    { value: 'active', label: '\u{1F3C3} Active Recovery' },
                    { value: 'full', label: '\u{1F6CC} Full Rest' },
                    { value: 'injury', label: '\u{1F915} Injury / Rehab' },
                    { value: 'sick', label: '\u{1F912} Sick Day' },
                    { value: 'travel', label: '\u{2708}\u{FE0F} Travelling' },
                    { value: 'life', label: '\u{1F937} Life Got in the Way' },
                  ] as const).map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setRestType(type.value)}
                      className="py-2.5 rounded-lg font-medium text-xs transition-all"
                      style={{
                        backgroundColor: restType === type.value ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: restType === type.value ? '#FFFFFF' : 'var(--text)',
                        border: restType === type.value ? 'none' : '1px solid var(--border)',
                      }}
                      aria-pressed={restType === type.value}
                    >
                      {type.label}
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
          <Link to="/log" className="underline" style={{ color: 'var(--accent)' }}>
            Add roll details, techniques &amp; photos &rarr;
          </Link>
        </p>
      </div>
    </div>
  );
}

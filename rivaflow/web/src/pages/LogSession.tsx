import { useState, useEffect, useMemo, useCallback } from 'react';
import { getLocalDateString } from '../utils/date';
import { useNavigate } from 'react-router-dom';
import { sessionsApi, readinessApi, profileApi, friendsApi, socialApi, glossaryApi, restApi, whoopApi, getErrorMessage } from '../api/client';
import { logger } from '../utils/logger';
import type { Friend, Movement, MediaUrl, Readiness, WhoopWorkoutMatch } from '../types';
import { CheckCircle, ArrowLeft, Camera, Mic, MicOff } from 'lucide-react';
import WhoopMatchModal from '../components/WhoopMatchModal';
import GymSelector from '../components/GymSelector';
import { ClassTypeChips, IntensityChips } from '../components/ui';
import { useToast } from '../contexts/ToastContext';
import { triggerInsightRefresh } from '../utils/insightRefresh';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import ReadinessStep from '../components/sessions/ReadinessStep';
import TechniqueTracker from '../components/sessions/TechniqueTracker';
import RollTracker from '../components/sessions/RollTracker';
import WhoopIntegrationPanel from '../components/sessions/WhoopIntegrationPanel';
import FightDynamicsPanel from '../components/sessions/FightDynamicsPanel';
import type { RollEntry, TechniqueEntry } from '../components/sessions/sessionTypes';
import { SPARRING_TYPES } from '../components/sessions/sessionTypes';

const TIME_QUICK_SELECT = [
  { label: '6:30am', value: '06:30' },
  { label: '12pm', value: '12:00' },
  { label: '5:30pm', value: '17:30' },
  { label: '7pm', value: '19:00' },
] as const;

const DURATION_QUICK_SELECT = [60, 75, 90, 120] as const;

export default function LogSession() {
  const navigate = useNavigate();
  const toast = useToast();
  const [activityType, setActivityType] = useState<'training' | 'rest'>('training');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [skippedReadiness, setSkippedReadiness] = useState(false);
  const [autocomplete, setAutocomplete] = useState<{ gyms?: string[]; locations?: string[]; partners?: string[]; techniques?: string[] }>({});

  const [instructors, setInstructors] = useState<Friend[]>([]);
  const [partners, setPartners] = useState<Friend[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);

  const [detailedMode, setDetailedMode] = useState(false);
  const [rolls, setRolls] = useState<RollEntry[]>([]);

  // WHOOP integration state
  const [whoopConnected, setWhoopConnected] = useState(false);
  const [whoopSyncing, setWhoopSyncing] = useState(false);
  const [whoopSynced, setWhoopSynced] = useState(false);
  const [whoopMatches, setWhoopMatches] = useState<WhoopWorkoutMatch[]>([]);
  const [showWhoopModal, setShowWhoopModal] = useState(false);
  const [whoopManualMode, setWhoopManualMode] = useState(false);

  const [showWhoop, setShowWhoop] = useState(false);
  const [showFightDynamics, setShowFightDynamics] = useState(false);
  const [fightDynamics, setFightDynamics] = useState({
    attacks_attempted: 0,
    attacks_successful: 0,
    defenses_attempted: 0,
    defenses_successful: 0,
  });

  const [submissionSearchFor, setSubmissionSearchFor] = useState<{[rollIndex: number]: string}>({});
  const [submissionSearchAgainst, setSubmissionSearchAgainst] = useState<{[rollIndex: number]: string}>({});

  const [techniques, setTechniques] = useState<TechniqueEntry[]>([]);
  const [techniqueSearch, setTechniqueSearch] = useState<{[techIndex: number]: string}>({});

  const [readinessData, setReadinessData] = useState({
    check_date: getLocalDateString(),
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '',
  });

  const [sessionData, setSessionData] = useState({
    session_date: getLocalDateString(),
    class_time: '',
    class_type: 'gi',
    gym_name: '',
    location: '',
    duration_mins: 60,
    intensity: 4,
    instructor_id: null as number | null,
    instructor_name: '',
    rolls: 0,
    submissions_for: 0,
    submissions_against: 0,
    partners: '',
    techniques: '',
    notes: '',
    whoop_strain: '',
    whoop_calories: '',
    whoop_avg_hr: '',
    whoop_max_hr: '',
  });

  const [restData, setRestData] = useState({
    rest_date: getLocalDateString(),
    rest_type: 'active',
    rest_note: '',
  });

  // Voice-to-text for notes
  const onTranscript = useCallback((transcript: string) => {
    setSessionData(prev => ({
      ...prev,
      notes: prev.notes ? `${prev.notes} ${transcript}` : transcript,
    }));
  }, []);
  const onSpeechError = useCallback((message: string) => {
    toast.showToast('error', message);
  }, [toast]);
  const { isRecording, isTranscribing, hasSpeechApi, toggleRecording } = useSpeechRecognition({ onTranscript, onError: onSpeechError });

  useEffect(() => {
    const controller = new AbortController();
    const doLoad = async () => {
      try {
        const [autocompleteRes, profileRes, instructorsRes, partnersRes, movementsRes, socialFriendsRes] = await Promise.all([
          sessionsApi.getAutocomplete(),
          profileApi.get(),
          friendsApi.listInstructors(),
          friendsApi.listPartners(),
          glossaryApi.list(),
          socialApi.getFriends().catch(() => ({ data: { friends: [] } })),
        ]);
        if (controller.signal.aborted) return;

        setAutocomplete(autocompleteRes.data ?? {});
        const loadedInstructors: Friend[] = instructorsRes.data ?? [];
        setInstructors(loadedInstructors);
        const manualPartners: Friend[] = partnersRes.data ?? [];
        const socialFriends: Friend[] = (socialFriendsRes.data.friends || []).map((sf: any) => ({
          id: sf.id + 1000000,
          name: `${sf.first_name || ''} ${sf.last_name || ''}`.trim(),
          friend_type: 'training-partner' as const,
        }));
        const seenNames = new Set<string>();
        const merged: Friend[] = [];
        for (const p of [...manualPartners, ...loadedInstructors]) {
          const key = p.name.toLowerCase();
          if (!seenNames.has(key)) {
            seenNames.add(key);
            merged.push(p);
          }
        }
        for (const sf of socialFriends) {
          if (!seenNames.has(sf.name.toLowerCase())) {
            seenNames.add(sf.name.toLowerCase());
            merged.push(sf);
          }
        }
        setPartners(merged);
        const movementsData = movementsRes.data as Movement[] | { movements: Movement[] };
        setMovements(Array.isArray(movementsData) ? movementsData : movementsData?.movements || []);

        const updates: Partial<typeof sessionData> = {};
        if (profileRes.data?.default_gym) {
          updates.gym_name = profileRes.data.default_gym;
        }
        if (profileRes.data?.default_location) {
          updates.location = profileRes.data.default_location;
        }
        if (profileRes.data?.current_instructor_id) {
          updates.instructor_id = profileRes.data.current_instructor_id;
          updates.instructor_name = profileRes.data?.current_professor ?? '';
        }
        if (profileRes.data?.primary_training_type) {
          updates.class_type = profileRes.data.primary_training_type;
        }
        if (Object.keys(updates).length > 0) {
          setSessionData(prev => ({ ...prev, ...updates }));
        }

        try {
          const whoopRes = await whoopApi.getStatus();
          if (!controller.signal.aborted && whoopRes.data?.connected) {
            setWhoopConnected(true);
          }
        } catch {
          // Feature flag off or not available
        }
      } catch (error) {
        if (!controller.signal.aborted) logger.error('Error loading data:', error);
      }
    };
    doLoad();
    return () => { controller.abort(); };
  }, []);

  const handleNextStep = useCallback(() => {
    if (step === 1) setStep(2);
  }, [step]);

  const handleSkipReadiness = useCallback(() => {
    setSkippedReadiness(true);
    setStep(2);
  }, []);

  const handleBackStep = useCallback(() => {
    setStep(1);
  }, []);

  // Roll handlers
  const handleAddRoll = useCallback(() => {
    setRolls(prev => [...prev, {
      roll_number: prev.length + 1, partner_id: null, partner_name: '',
      duration_mins: 5, submissions_for: [], submissions_against: [], notes: '',
    }]);
  }, []);

  const handleRemoveRoll = useCallback((index: number) => {
    setRolls(prev => {
      const updated = prev.filter((_, i) => i !== index);
      updated.forEach((roll, i) => { roll.roll_number = i + 1; });
      return updated;
    });
    setSubmissionSearchFor(prev => {
      const result: {[key: number]: string} = {};
      Object.keys(prev).forEach(key => {
        const idx = parseInt(key);
        if (idx < index) result[idx] = prev[idx];
        else if (idx > index) result[idx - 1] = prev[idx];
      });
      return result;
    });
    setSubmissionSearchAgainst(prev => {
      const result: {[key: number]: string} = {};
      Object.keys(prev).forEach(key => {
        const idx = parseInt(key);
        if (idx < index) result[idx] = prev[idx];
        else if (idx > index) result[idx - 1] = prev[idx];
      });
      return result;
    });
  }, []);

  const handleRollChange = useCallback((index: number, field: keyof RollEntry, value: RollEntry[keyof RollEntry]) => {
    setRolls(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  }, []);

  const handleToggleSubmission = useCallback((rollIndex: number, movementId: number, type: 'for' | 'against') => {
    setRolls(prev => {
      const updated = [...prev];
      const field = type === 'for' ? 'submissions_for' : 'submissions_against';
      const current = updated[rollIndex][field];
      if (current.includes(movementId)) {
        updated[rollIndex][field] = current.filter(id => id !== movementId);
      } else {
        updated[rollIndex][field] = [...current, movementId];
      }
      return updated;
    });
  }, []);

  // Technique handlers
  const handleAddTechnique = useCallback(() => {
    setTechniques(prev => [...prev, {
      technique_number: prev.length + 1, movement_id: null, movement_name: '', notes: '', media_urls: [],
    }]);
  }, []);

  const handleRemoveTechnique = useCallback((index: number) => {
    setTechniques(prev => {
      const updated = prev.filter((_, i) => i !== index);
      updated.forEach((tech, i) => { tech.technique_number = i + 1; });
      return updated;
    });
    setTechniqueSearch(prev => {
      const result: {[key: number]: string} = {};
      Object.keys(prev).forEach(key => {
        const idx = parseInt(key);
        if (idx < index) result[idx] = prev[idx];
        else if (idx > index) result[idx - 1] = prev[idx];
      });
      return result;
    });
  }, []);

  const handleTechniqueChange = useCallback((index: number, field: keyof TechniqueEntry, value: TechniqueEntry[keyof TechniqueEntry]) => {
    setTechniques(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  }, []);

  const handleSelectMovement = useCallback((index: number, movementId: number, movementName: string) => {
    setTechniques(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], movement_id: movementId, movement_name: movementName };
      return updated;
    });
  }, []);

  const handleAddMediaUrl = useCallback((techIndex: number) => {
    setTechniques(prev => {
      const updated = [...prev];
      updated[techIndex] = {
        ...updated[techIndex],
        media_urls: [...updated[techIndex].media_urls, { type: 'video', url: '', title: '' }],
      };
      return updated;
    });
  }, []);

  const handleRemoveMediaUrl = useCallback((techIndex: number, mediaIndex: number) => {
    setTechniques(prev => {
      const updated = [...prev];
      updated[techIndex] = {
        ...updated[techIndex],
        media_urls: updated[techIndex].media_urls.filter((_, i) => i !== mediaIndex),
      };
      return updated;
    });
  }, []);

  const handleMediaUrlChange = useCallback((techIndex: number, mediaIndex: number, field: keyof MediaUrl, value: string) => {
    setTechniques(prev => {
      const updated = [...prev];
      const mediaUrls = [...updated[techIndex].media_urls];
      mediaUrls[mediaIndex] = { ...mediaUrls[mediaIndex], [field]: value };
      updated[techIndex] = { ...updated[techIndex], media_urls: mediaUrls };
      return updated;
    });
  }, []);

  // Fight dynamics handlers
  const handleFightDynamicsIncrement = useCallback((field: keyof typeof fightDynamics) => {
    setFightDynamics(fd => {
      if (field === 'attacks_successful') return { ...fd, [field]: Math.min(fd.attacks_attempted, fd[field] + 1) };
      if (field === 'defenses_successful') return { ...fd, [field]: Math.min(fd.defenses_attempted, fd[field] + 1) };
      return { ...fd, [field]: fd[field] + 1 };
    });
  }, []);

  const handleFightDynamicsDecrement = useCallback((field: keyof typeof fightDynamics) => {
    setFightDynamics(fd => ({ ...fd, [field]: Math.max(0, fd[field] - 1) }));
  }, []);

  const handleFightDynamicsChange = useCallback((field: keyof typeof fightDynamics, value: number) => {
    setFightDynamics(fd => {
      const clamped = Math.max(0, value);
      if (field === 'attacks_successful') return { ...fd, [field]: Math.min(fd.attacks_attempted, clamped) };
      if (field === 'defenses_successful') return { ...fd, [field]: Math.min(fd.defenses_attempted, clamped) };
      return { ...fd, [field]: clamped };
    });
  }, []);

  // WHOOP handlers
  const handleWhoopSync = useCallback(async () => {
    if (!sessionData.session_date || !sessionData.class_time) return;
    setWhoopSyncing(true);
    try {
      const res = await whoopApi.getWorkouts({
        session_date: sessionData.session_date,
        class_time: sessionData.class_time,
        duration_mins: sessionData.duration_mins,
      });
      const matches = res.data.workouts || [];
      if (matches.length === 0) {
        toast.showToast('warning', 'No matching WHOOP workouts found');
      } else if (matches.length === 1 && matches[0].overlap_pct >= 90) {
        const w = matches[0];
        setSessionData(prev => ({
          ...prev,
          whoop_strain: w.strain?.toString() || '',
          whoop_calories: w.calories?.toString() || '',
          whoop_avg_hr: w.avg_heart_rate?.toString() || '',
          whoop_max_hr: w.max_heart_rate?.toString() || '',
        }));
        setWhoopSynced(true);
        toast.showToast('success', 'WHOOP data synced automatically');
      } else {
        setWhoopMatches(matches);
        setShowWhoopModal(true);
      }
    } catch (error: unknown) {
      toast.showToast('error', getErrorMessage(error));
    } finally {
      setWhoopSyncing(false);
    }
  }, [sessionData.session_date, sessionData.class_time, sessionData.duration_mins, toast]);

  const handleWhoopMatchSelect = useCallback((workoutCacheId: number) => {
    const workout = whoopMatches.find(w => w.id === workoutCacheId);
    if (workout) {
      setSessionData(prev => ({
        ...prev,
        whoop_strain: workout.strain?.toString() || '',
        whoop_calories: workout.calories?.toString() || '',
        whoop_avg_hr: workout.avg_heart_rate?.toString() || '',
        whoop_max_hr: workout.max_heart_rate?.toString() || '',
      }));
      setWhoopSynced(true);
      setShowWhoopModal(false);
      toast.showToast('success', 'WHOOP data applied');
    }
  }, [whoopMatches, toast]);

  const handleWhoopClear = useCallback(() => {
    setSessionData(prev => ({ ...prev, whoop_strain: '', whoop_calories: '', whoop_avg_hr: '', whoop_max_hr: '' }));
    setWhoopSynced(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (activityType === 'rest') {
        await restApi.logRestDay({
          rest_type: restData.rest_type,
          note: restData.rest_note || undefined,
          rest_date: restData.rest_date,
        });
        setSuccess(true);
        setTimeout(() => navigate('/'), 1500);
        return;
      }

      if (!skippedReadiness) {
        const readinessPayload: Partial<Readiness> & Record<string, unknown> = {
          ...readinessData,
          weight_kg: readinessData.weight_kg ? parseFloat(readinessData.weight_kg as string) : undefined,
        };
        await readinessApi.create(readinessPayload);
      }

      const payload: Record<string, unknown> = {
        ...sessionData,
        class_time: sessionData.class_time || undefined,
        location: sessionData.location || undefined,
        notes: sessionData.notes || undefined,
        partners: sessionData.partners ? sessionData.partners.split(',').map(p => p.trim()) : undefined,
        techniques: sessionData.techniques ? sessionData.techniques.split(',').map(t => t.trim()) : undefined,
        visibility_level: 'private',
        whoop_strain: sessionData.whoop_strain ? parseFloat(sessionData.whoop_strain as string) : undefined,
        whoop_calories: sessionData.whoop_calories ? parseInt(sessionData.whoop_calories as string) : undefined,
        whoop_avg_hr: sessionData.whoop_avg_hr ? parseInt(sessionData.whoop_avg_hr as string) : undefined,
        whoop_max_hr: sessionData.whoop_max_hr ? parseInt(sessionData.whoop_max_hr as string) : undefined,
      };

      if (fightDynamics.attacks_attempted > 0 || fightDynamics.defenses_attempted > 0) {
        payload.attacks_attempted = fightDynamics.attacks_attempted;
        payload.attacks_successful = Math.min(fightDynamics.attacks_successful, fightDynamics.attacks_attempted);
        payload.defenses_attempted = fightDynamics.defenses_attempted;
        payload.defenses_successful = Math.min(fightDynamics.defenses_successful, fightDynamics.defenses_attempted);
      }

      if (sessionData.instructor_id) {
        payload.instructor_id = sessionData.instructor_id;
        const instructor = instructors.find(i => i.id === sessionData.instructor_id);
        if (instructor) payload.instructor_name = instructor.name ?? undefined;
      } else if (sessionData.instructor_name) {
        payload.instructor_name = sessionData.instructor_name;
      } else {
        payload.instructor_id = undefined;
        payload.instructor_name = undefined;
      }

      if (detailedMode && rolls.length > 0) {
        payload.session_rolls = rolls.map(roll => ({
          roll_number: roll.roll_number,
          partner_id: roll.partner_id || undefined,
          partner_name: roll.partner_name || undefined,
          duration_mins: roll.duration_mins || undefined,
          submissions_for: roll.submissions_for.length > 0 ? roll.submissions_for : undefined,
          submissions_against: roll.submissions_against.length > 0 ? roll.submissions_against : undefined,
          notes: roll.notes || undefined,
        }));
        payload.rolls = rolls.length;
        payload.submissions_for = rolls.reduce((sum, roll) => sum + roll.submissions_for.length, 0);
        payload.submissions_against = rolls.reduce((sum, roll) => sum + roll.submissions_against.length, 0);
      }

      if (techniques.length > 0) {
        payload.session_techniques = techniques
          .filter(tech => tech.movement_id !== null)
          .map(tech => ({
            movement_id: tech.movement_id!,
            technique_number: tech.technique_number,
            notes: tech.notes || undefined,
            media_urls: tech.media_urls.length > 0 ? tech.media_urls.filter(m => m.url) : undefined,
          }));
      }

      const response = await sessionsApi.create(payload);
      setSuccess(true);
      if (response.data?.id) {
        triggerInsightRefresh(response.data.id);
        setTimeout(() => navigate(`/session/${response.data.id}`), 1500);
      } else {
        triggerInsightRefresh();
        setTimeout(() => navigate('/'), 1500);
      }
    } catch (error) {
      logger.error('Error creating session:', error);
      toast.showToast('error', 'Failed to log session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const compositeScore = useMemo(
    () => readinessData.sleep + (6 - readinessData.stress) + (6 - readinessData.soreness) + readinessData.energy,
    [readinessData.sleep, readinessData.stress, readinessData.soreness, readinessData.energy]
  );
  const isSparringType = useMemo(
    () => SPARRING_TYPES.includes(sessionData.class_type),
    [sessionData.class_type]
  );

  const submissionMovements = useMemo(
    () => movements.filter(m => m.category === 'submission'),
    [movements]
  );

  const filterMovements = useCallback((search: string) => {
    const s = search.toLowerCase();
    return movements.filter(m =>
      m.name?.toLowerCase().includes(s) ||
      m.category?.toLowerCase().includes(s) ||
      m.subcategory?.toLowerCase().includes(s) ||
      (m.aliases ?? []).some(alias => alias.toLowerCase().includes(s))
    );
  }, [movements]);

  const filterSubmissions = useCallback((search: string) => {
    const s = search.toLowerCase();
    return submissionMovements.filter(m =>
      m.name?.toLowerCase().includes(s) ||
      m.subcategory?.toLowerCase().includes(s) ||
      (m.aliases ?? []).some(alias => alias.toLowerCase().includes(s))
    );
  }, [submissionMovements]);

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <style>{`
          @keyframes celebrationBounce {
            0% { transform: scale(0); opacity: 0; }
            50% { transform: scale(1.2); opacity: 1; }
            70% { transform: scale(0.9); }
            100% { transform: scale(1); opacity: 1; }
          }
          .celebrate-bounce {
            animation: celebrationBounce 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
          }
          .celebrate-bounce-delay {
            animation: celebrationBounce 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.15s forwards;
            opacity: 0;
          }
        `}</style>
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4 celebrate-bounce" />
        <div className="celebrate-bounce-delay">
          <h2 className="text-2xl font-bold mb-2">{activityType === 'rest' ? 'Rest Day Logged!' : 'Session Logged!'}</h2>
          <p className="text-[var(--muted)]">{activityType === 'rest' ? 'Redirecting to home...' : 'Redirecting to session details...'}</p>
          {activityType === 'training' && <p className="text-sm text-[var(--muted)] mt-2">You can add photos on the next page</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Activity Type Selector */}
      <div className="card mb-6">
        <label className="label">What would you like to log?</label>
        <div className="flex gap-3" role="group" aria-label="Activity type">
          <button
            type="button"
            onClick={() => { setActivityType('training'); setStep(1); }}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
            style={{
              backgroundColor: activityType === 'training' ? 'var(--accent)' : 'var(--surfaceElev)',
              color: activityType === 'training' ? '#FFFFFF' : 'var(--text)',
              border: activityType === 'training' ? 'none' : '1px solid var(--border)',
            }}
            aria-pressed={activityType === 'training'}
          >
            Training Session
          </button>
          <button
            type="button"
            onClick={() => { setActivityType('rest'); setStep(2); }}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
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

      {/* Progress Indicator (only for training) */}
      {activityType === 'training' && (
        <div className="mb-6">
        <div className="flex items-center justify-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
            step === 1
              ? 'bg-[var(--accent)] text-white'
              : skippedReadiness
                ? 'bg-[var(--surfaceElev)] text-[var(--muted)] line-through'
                : 'bg-green-500 text-white'
          }`}>
            1
          </div>
          <div className="w-16 h-1 bg-[var(--surfaceElev)]"></div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 2 ? 'bg-[var(--accent)] text-white' : 'bg-[var(--surfaceElev)] text-[var(--muted)]'}`}>
            2
          </div>
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={`${step === 1 ? 'font-semibold' : skippedReadiness ? 'text-[var(--muted)] line-through' : 'text-[var(--muted)]'}`}>
            Readiness Check {skippedReadiness && '(skipped)'}
          </span>
          <span className={step === 2 ? 'font-semibold' : 'text-[var(--muted)]'}>Session Details</span>
        </div>
      </div>
      )}

      <h1 className="text-3xl font-bold mb-6">
        {activityType === 'rest'
          ? 'Log Rest Day'
          : step === 1
            ? 'How Are You Feeling?'
            : 'Log Training Session'
        }
      </h1>

      {/* Step 1: Readiness */}
      {activityType === 'training' && step === 1 && (
        <ReadinessStep
          data={readinessData}
          onChange={setReadinessData}
          compositeScore={compositeScore}
          onNext={handleNextStep}
          onSkip={handleSkipReadiness}
        />
      )}

      {/* Step 2: Training Session */}
      {activityType === 'training' && step === 2 && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          {/* Date */}
          <div>
            <label className="label">Date</label>
            <input type="date" className="input" value={sessionData.session_date}
              onChange={(e) => setSessionData({ ...sessionData, session_date: e.target.value })} required />
          </div>

          {/* Class Time */}
          <div>
            <label className="label">Class Time (optional)</label>
            <div className="flex gap-2 mb-2" role="group" aria-label="Common class times">
              {TIME_QUICK_SELECT.map((time) => (
                <button key={time.value} type="button"
                  onClick={() => setSessionData({ ...sessionData, class_time: time.value })}
                  className="flex-1 min-h-[44px] py-2 rounded-lg font-medium text-sm transition-all"
                  style={{
                    backgroundColor: sessionData.class_time === time.value ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: sessionData.class_time === time.value ? '#FFFFFF' : 'var(--text)',
                    border: sessionData.class_time === time.value ? 'none' : '1px solid var(--border)',
                  }}
                  aria-pressed={sessionData.class_time === time.value}
                >
                  {time.label}
                </button>
              ))}
            </div>
            <input type="text" className="input text-sm" value={sessionData.class_time}
              onChange={(e) => setSessionData({ ...sessionData, class_time: e.target.value })}
              placeholder="Or type custom time (e.g., 18:30, morning)" />
          </div>

          {/* Class Type */}
          <div>
            <label className="label">Class Type</label>
            <ClassTypeChips value={sessionData.class_type}
              onChange={(val) => setSessionData({ ...sessionData, class_type: val })} />
          </div>

          {/* Gym Name */}
          <div>
            <label className="label">Gym Name</label>
            <GymSelector
              value={sessionData.gym_name}
              onChange={(gymName, _isCustom) => { setSessionData({ ...sessionData, gym_name: gymName }); }}
              onGymSelected={(gym) => {
                if (gym.head_coach) {
                  setSessionData(prev => ({
                    ...prev,
                    gym_name: [gym.name, gym.city, gym.state, gym.country].filter(Boolean).join(', '),
                    instructor_name: gym.head_coach ?? '',
                    instructor_id: null,
                  }));
                }
              }}
            />
            <p className="text-xs text-[var(--muted)] mt-1">
              Select from verified gyms or add a new one. Head coach will auto-populate if available.
            </p>
          </div>

          {/* Instructor */}
          <div>
            <label className="label">Instructor (optional)</label>
            <select className="input" value={sessionData.instructor_id || ''}
              onChange={(e) => {
                const instructorId = e.target.value ? parseInt(e.target.value) : null;
                const instructor = instructors.find(i => i.id === instructorId);
                setSessionData({ ...sessionData, instructor_id: instructorId, instructor_name: instructor?.name || '' });
              }}>
              <option value="">Select instructor...</option>
              {instructors.map(instructor => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name ?? 'Unknown'}
                  {instructor.belt_rank && ` (${instructor.belt_rank} belt)`}
                  {instructor.instructor_certification && ` - ${instructor.instructor_certification}`}
                </option>
              ))}
            </select>
            <p className="text-xs text-[var(--muted)] mt-1">
              Select from your list. <a href="/friends" className="text-[var(--accent)] hover:underline">Manage instructors in Friends</a>
            </p>
          </div>

          {/* Location */}
          <div>
            <label className="label">Location (optional)</label>
            <input type="text" className="input" value={sessionData.location}
              onChange={(e) => setSessionData({ ...sessionData, location: e.target.value })}
              placeholder="e.g., Sydney, NSW" list="locations" />
            {autocomplete.locations && (
              <datalist id="locations">
                {autocomplete.locations.map((loc: string) => <option key={loc} value={loc} />)}
              </datalist>
            )}
          </div>

          {/* Duration */}
          <div>
            <label className="label">Duration (minutes)</label>
            <div className="flex gap-2 mb-2" role="group" aria-label="Duration options">
              {DURATION_QUICK_SELECT.map((mins) => (
                <button key={mins} type="button"
                  onClick={() => setSessionData({ ...sessionData, duration_mins: mins })}
                  className="flex-1 min-h-[44px] py-3 rounded-lg font-medium text-sm transition-all"
                  style={{
                    backgroundColor: sessionData.duration_mins === mins ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: sessionData.duration_mins === mins ? '#FFFFFF' : 'var(--text)',
                    border: sessionData.duration_mins === mins ? 'none' : '1px solid var(--border)',
                  }}
                  aria-label={`${mins} minutes`} aria-pressed={sessionData.duration_mins === mins}
                >
                  {mins}m
                </button>
              ))}
            </div>
            <input type="number" className="input text-sm" value={sessionData.duration_mins}
              onChange={(e) => setSessionData({ ...sessionData, duration_mins: parseInt(e.target.value) || 0 })}
              placeholder="Or enter custom duration" min="1" required />
          </div>

          {/* Intensity */}
          <div>
            <label className="label">Intensity</label>
            <IntensityChips value={sessionData.intensity}
              onChange={(val) => setSessionData({ ...sessionData, intensity: val })} />
          </div>

          {/* Technique Tracker */}
          <TechniqueTracker
            techniques={techniques}
            techniqueSearch={techniqueSearch}
            onSearchChange={(index, value) => setTechniqueSearch({ ...techniqueSearch, [index]: value })}
            filterMovements={filterMovements}
            onAdd={handleAddTechnique}
            onRemove={handleRemoveTechnique}
            onChange={handleTechniqueChange}
            onSelectMovement={handleSelectMovement}
            onAddMediaUrl={handleAddMediaUrl}
            onRemoveMediaUrl={handleRemoveMediaUrl}
            onMediaUrlChange={handleMediaUrlChange}
          />

          {/* Roll Tracking */}
          {isSparringType && (
            <RollTracker
              detailedMode={detailedMode}
              onToggleMode={() => setDetailedMode(!detailedMode)}
              rolls={rolls}
              partners={partners}
              simpleData={{
                rolls: sessionData.rolls,
                submissions_for: sessionData.submissions_for,
                submissions_against: sessionData.submissions_against,
                partners: sessionData.partners,
              }}
              onSimpleChange={(field, value) => setSessionData({ ...sessionData, [field]: value })}
              submissionSearchFor={submissionSearchFor}
              submissionSearchAgainst={submissionSearchAgainst}
              onSubmissionSearchForChange={(index, value) => setSubmissionSearchFor({ ...submissionSearchFor, [index]: value })}
              onSubmissionSearchAgainstChange={(index, value) => setSubmissionSearchAgainst({ ...submissionSearchAgainst, [index]: value })}
              filterSubmissions={filterSubmissions}
              onAddRoll={handleAddRoll}
              onRemoveRoll={handleRemoveRoll}
              onRollChange={handleRollChange}
              onToggleSubmission={handleToggleSubmission}
            />
          )}

          {/* WHOOP Integration */}
          <WhoopIntegrationPanel
            whoopConnected={whoopConnected}
            whoopSyncing={whoopSyncing}
            whoopSynced={whoopSynced}
            whoopManualMode={whoopManualMode}
            showWhoop={showWhoop}
            classTime={sessionData.class_time}
            whoopData={{
              whoop_strain: sessionData.whoop_strain,
              whoop_calories: sessionData.whoop_calories,
              whoop_avg_hr: sessionData.whoop_avg_hr,
              whoop_max_hr: sessionData.whoop_max_hr,
            }}
            onWhoopDataChange={(field, value) => setSessionData({ ...sessionData, [field]: value })}
            onSync={handleWhoopSync}
            onClear={handleWhoopClear}
            onToggleManualMode={(manual) => { setWhoopManualMode(manual); if (manual) setShowWhoop(true); }}
            onToggleShow={() => setShowWhoop(!showWhoop)}
          />

          {/* Fight Dynamics */}
          {isSparringType && (
            <FightDynamicsPanel
              data={fightDynamics}
              expanded={showFightDynamics}
              onToggle={() => setShowFightDynamics(!showFightDynamics)}
              onIncrement={handleFightDynamicsIncrement}
              onDecrement={handleFightDynamicsDecrement}
              onChange={handleFightDynamicsChange}
            />
          )}

          {/* Notes */}
          <div className={!isSparringType ? 'border-t border-[var(--border)] pt-4' : ''}>
            <label className="label">
              {!isSparringType ? 'Session Details' : 'Notes'}
              {!isSparringType && <span className="text-sm font-normal text-[var(--muted)] ml-2">(Workout details, exercises, distances, times, etc.)</span>}
            </label>
            <div className="relative">
              <textarea className="input" value={sessionData.notes}
                onChange={(e) => setSessionData({ ...sessionData, notes: e.target.value })}
                rows={!isSparringType ? 5 : 3}
                placeholder={!isSparringType
                  ? "e.g., 5km run in 30 mins, Deadlifts 3x8 @ 100kg, Squats 3x10 @ 80kg, or Yoga flow focusing on hip mobility..."
                  : "Any notes about today's training..."} />
              {hasSpeechApi && (
                <button type="button" onClick={toggleRecording} disabled={isTranscribing}
                  className="absolute bottom-2 right-2 p-1.5 rounded-lg transition-all"
                  style={{
                    backgroundColor: isRecording ? 'var(--error)' : 'var(--surfaceElev)',
                    color: isRecording ? '#FFFFFF' : 'var(--muted)',
                    opacity: isTranscribing ? 0.6 : 1,
                  }}
                  aria-label={isTranscribing ? 'Transcribing audio...' : isRecording ? 'Stop recording' : 'Start voice input'}>
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

          {/* Photo Upload Info */}
          <div className="rounded-lg p-3 flex items-start gap-2" style={{ backgroundColor: 'rgba(59,130,246,0.1)', border: '1px solid var(--accent)' }}>
            <Camera className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--accent)' }} />
            <div className="text-sm" style={{ color: 'var(--accent)' }}>
              <span className="font-semibold">Want to add photos?</span> Save the session first, then you can upload up to 3 photos on the next page.
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-2">
            <button type="button" onClick={handleBackStep} className="btn-secondary flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Logging Session...' : 'Log Session'}
            </button>
          </div>
        </form>
      )}

      {/* WHOOP Match Modal */}
      <WhoopMatchModal
        isOpen={showWhoopModal}
        onClose={() => setShowWhoopModal(false)}
        matches={whoopMatches}
        onSelect={handleWhoopMatchSelect}
        onManual={() => { setShowWhoopModal(false); setWhoopManualMode(true); setShowWhoop(true); }}
      />

      {/* Rest Day Form */}
      {activityType === 'rest' && step === 2 && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="label">Date</label>
            <input type="date" className="input" value={restData.rest_date}
              onChange={(e) => setRestData({ ...restData, rest_date: e.target.value })} required />
          </div>
          <div>
            <label className="label">Rest Type</label>
            <div className="flex gap-2" role="group" aria-label="Rest type options">
              {['active', 'passive', 'injury'].map((type) => (
                <button key={type} type="button"
                  onClick={() => setRestData({ ...restData, rest_type: type })}
                  className="flex-1 py-3 rounded-lg font-medium text-sm transition-all capitalize focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
                  style={{
                    backgroundColor: restData.rest_type === type ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: restData.rest_type === type ? '#FFFFFF' : 'var(--text)',
                    border: restData.rest_type === type ? 'none' : '1px solid var(--border)',
                  }}
                  aria-pressed={restData.rest_type === type}
                >
                  {type}
                </button>
              ))}
            </div>
            <p className="text-xs text-[var(--muted)] mt-2">
              <span className="font-semibold">Active:</span> Light activity, stretching, mobility work.
              <span className="font-semibold ml-3">Passive:</span> Complete rest, no training.
              <span className="font-semibold ml-3">Injury:</span> Recovering from injury.
            </p>
          </div>
          <div>
            <label className="label">Note (optional)</label>
            <textarea className="input" rows={4} value={restData.rest_note}
              onChange={(e) => setRestData({ ...restData, rest_note: e.target.value })}
              placeholder="Any notes about your rest day, recovery activities, or how you're feeling..." />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Logging Rest Day...' : 'Log Rest Day'}
          </button>
        </form>
      )}
    </div>
  );
}

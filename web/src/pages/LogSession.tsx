import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi, readinessApi, profileApi, friendsApi, glossaryApi, restApi } from '../api/client';
import type { Friend, Movement, MediaUrl } from '../types';
import { CheckCircle, ArrowRight, ArrowLeft, Plus, X, ToggleLeft, ToggleRight, Search, Camera, ChevronDown, ChevronUp, Swords, Shield, Minus } from 'lucide-react';
import GymSelector from '../components/GymSelector';
import { useToast } from '../contexts/ToastContext';

const CLASS_TYPES = ['gi', 'no-gi', 'open-mat', 'competition', 's&c', 'cardio', 'mobility'];
const CLASS_TYPE_LABELS: Record<string, string> = {
  'gi': 'Gi',
  'no-gi': 'No-Gi',
  'open-mat': 'Open Mat',
  'competition': 'Competition',
  's&c': 'S&C',
  'cardio': 'Cardio',
  'mobility': 'Mobility',
};
const SPARRING_TYPES = ['gi', 'no-gi', 'open-mat', 'competition'];

interface RollEntry {
  roll_number: number;
  partner_id: number | null;
  partner_name: string;
  duration_mins: number;
  submissions_for: number[];
  submissions_against: number[];
  notes: string;
}

interface TechniqueEntry {
  technique_number: number;
  movement_id: number | null;
  movement_name: string;
  notes: string;
  media_urls: MediaUrl[];
}

export default function LogSession() {
  const navigate = useNavigate();
  const toast = useToast();
  const [activityType, setActivityType] = useState<'training' | 'rest'>('training');
  const [step, setStep] = useState(1); // 1 = Readiness, 2 = Session (or Rest form if rest selected)
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [skippedReadiness, setSkippedReadiness] = useState(false);
  const [autocomplete, setAutocomplete] = useState<any>({});

  // New: Contacts and glossary data
  const [instructors, setInstructors] = useState<Friend[]>([]);
  const [partners, setPartners] = useState<Friend[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);

  // New: Roll tracking mode
  const [detailedMode, setDetailedMode] = useState(false);
  const [rolls, setRolls] = useState<RollEntry[]>([]);

  // Fight dynamics state
  const [showFightDynamics, setShowFightDynamics] = useState(false);
  const [fightDynamics, setFightDynamics] = useState({
    attacks_attempted: 0,
    attacks_successful: 0,
    defenses_attempted: 0,
    defenses_successful: 0,
  });

  // Search state for submissions
  const [submissionSearchFor, setSubmissionSearchFor] = useState<{[rollIndex: number]: string}>({});
  const [submissionSearchAgainst, setSubmissionSearchAgainst] = useState<{[rollIndex: number]: string}>({});

  // Technique tracking
  const [techniques, setTechniques] = useState<TechniqueEntry[]>([]);
  const [techniqueSearch, setTechniqueSearch] = useState<{[techIndex: number]: string}>({});

  // Readiness data (Step 1)
  const [readinessData, setReadinessData] = useState({
    check_date: new Date().toISOString().split('T')[0],
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '',
  });

  // Session data (Step 2)
  const [sessionData, setSessionData] = useState({
    session_date: new Date().toISOString().split('T')[0],
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

  // Rest day data
  const [restData, setRestData] = useState({
    rest_date: new Date().toISOString().split('T')[0],
    rest_type: 'active',
    rest_note: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [autocompleteRes, profileRes, instructorsRes, partnersRes, movementsRes] = await Promise.all([
        sessionsApi.getAutocomplete(),
        profileApi.get(),
        friendsApi.listInstructors(),
        friendsApi.listPartners(),
        glossaryApi.list(),
      ]);

      setAutocomplete(autocompleteRes.data ?? {});
      setInstructors(instructorsRes.data ?? []);
      setPartners(partnersRes.data ?? []);
      // API returns {movements: [...], total: N} — extract the array
      const movementsData = movementsRes.data as any;
      setMovements(Array.isArray(movementsData) ? movementsData : movementsData?.movements || []);

      // Auto-populate default gym, location, coach, and class type from profile
      const updates: any = {};
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
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleNextStep = () => {
    if (step === 1) {
      setStep(2);
    }
  };

  const handleSkipReadiness = () => {
    setSkippedReadiness(true);
    setStep(2);
  };

  const handleBackStep = () => {
    setStep(1);
  };

  const handleAddRoll = () => {
    setRolls([
      ...rolls,
      {
        roll_number: rolls.length + 1,
        partner_id: null,
        partner_name: '',
        duration_mins: 5,
        submissions_for: [],
        submissions_against: [],
        notes: '',
      },
    ]);
  };

  const handleRemoveRoll = (index: number) => {
    const updated = rolls.filter((_, i) => i !== index);
    // Renumber rolls
    updated.forEach((roll, i) => {
      roll.roll_number = i + 1;
    });
    setRolls(updated);

    // Clean up search state for removed roll and reindex remaining
    const newSearchFor: {[key: number]: string} = {};
    const newSearchAgainst: {[key: number]: string} = {};

    Object.keys(submissionSearchFor).forEach(key => {
      const idx = parseInt(key);
      if (idx < index) {
        newSearchFor[idx] = submissionSearchFor[idx];
      } else if (idx > index) {
        newSearchFor[idx - 1] = submissionSearchFor[idx];
      }
    });

    Object.keys(submissionSearchAgainst).forEach(key => {
      const idx = parseInt(key);
      if (idx < index) {
        newSearchAgainst[idx] = submissionSearchAgainst[idx];
      } else if (idx > index) {
        newSearchAgainst[idx - 1] = submissionSearchAgainst[idx];
      }
    });

    setSubmissionSearchFor(newSearchFor);
    setSubmissionSearchAgainst(newSearchAgainst);
  };

  const handleRollChange = (index: number, field: keyof RollEntry, value: any) => {
    const updated = [...rolls];
    updated[index] = { ...updated[index], [field]: value };
    setRolls(updated);
  };

  const handleToggleSubmission = (rollIndex: number, movementId: number, type: 'for' | 'against') => {
    const updated = [...rolls];
    const field = type === 'for' ? 'submissions_for' : 'submissions_against';
    const current = updated[rollIndex][field];

    if (current.includes(movementId)) {
      updated[rollIndex][field] = current.filter(id => id !== movementId);
    } else {
      updated[rollIndex][field] = [...current, movementId];
    }

    setRolls(updated);
  };

  // Technique handlers
  const handleAddTechnique = () => {
    setTechniques([
      ...techniques,
      {
        technique_number: techniques.length + 1,
        movement_id: null,
        movement_name: '',
        notes: '',
        media_urls: [],
      },
    ]);
  };

  const handleRemoveTechnique = (index: number) => {
    const updated = techniques.filter((_, i) => i !== index);
    // Renumber techniques
    updated.forEach((tech, i) => {
      tech.technique_number = i + 1;
    });
    setTechniques(updated);

    // Clean up search state for removed technique and reindex remaining
    const newSearch: {[key: number]: string} = {};
    Object.keys(techniqueSearch).forEach(key => {
      const idx = parseInt(key);
      if (idx < index) {
        newSearch[idx] = techniqueSearch[idx];
      } else if (idx > index) {
        newSearch[idx - 1] = techniqueSearch[idx];
      }
    });
    setTechniqueSearch(newSearch);
  };

  const handleTechniqueChange = (index: number, field: keyof TechniqueEntry, value: any) => {
    const updated = [...techniques];
    updated[index] = { ...updated[index], [field]: value };
    setTechniques(updated);
  };

  const handleAddMediaUrl = (techIndex: number) => {
    const updated = [...techniques];
    updated[techIndex].media_urls = [
      ...updated[techIndex].media_urls,
      { type: 'video', url: '', title: '' },
    ];
    setTechniques(updated);
  };

  const handleRemoveMediaUrl = (techIndex: number, mediaIndex: number) => {
    const updated = [...techniques];
    updated[techIndex].media_urls = updated[techIndex].media_urls.filter((_, i) => i !== mediaIndex);
    setTechniques(updated);
  };

  const handleMediaUrlChange = (techIndex: number, mediaIndex: number, field: keyof MediaUrl, value: any) => {
    const updated = [...techniques];
    updated[techIndex].media_urls[mediaIndex] = {
      ...updated[techIndex].media_urls[mediaIndex],
      [field]: value,
    };
    setTechniques(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Handle rest day submission
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

      // Handle training session submission
      // Save readiness first (only if not skipped)
      if (!skippedReadiness) {
        const readinessPayload: any = {
          ...readinessData,
          weight_kg: readinessData.weight_kg ? parseFloat(readinessData.weight_kg as string) : undefined,
        };
        await readinessApi.create(readinessPayload);
      }

      // Build session payload
      const payload: any = {
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

      // Add fight dynamics if any data was entered
      if (fightDynamics.attacks_attempted > 0 || fightDynamics.defenses_attempted > 0) {
        payload.attacks_attempted = fightDynamics.attacks_attempted;
        payload.attacks_successful = Math.min(fightDynamics.attacks_successful, fightDynamics.attacks_attempted);
        payload.defenses_attempted = fightDynamics.defenses_attempted;
        payload.defenses_successful = Math.min(fightDynamics.defenses_successful, fightDynamics.defenses_attempted);
      }

      // Add instructor
      if (sessionData.instructor_id) {
        payload.instructor_id = sessionData.instructor_id;
        const instructor = instructors.find(i => i.id === sessionData.instructor_id);
        if (instructor) {
          payload.instructor_name = instructor.name ?? undefined;
        }
      } else if (sessionData.instructor_name) {
        payload.instructor_name = sessionData.instructor_name;
      } else {
        payload.instructor_id = undefined;
        payload.instructor_name = undefined;
      }

      // Add detailed rolls if in detailed mode
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

        // Calculate aggregates from detailed rolls
        payload.rolls = rolls.length;
        payload.submissions_for = rolls.reduce((sum, roll) => sum + roll.submissions_for.length, 0);
        payload.submissions_against = rolls.reduce((sum, roll) => sum + roll.submissions_against.length, 0);
      }

      // Add detailed techniques if present
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
      // Redirect to session detail page after creation so user can add photos
      if (response.data?.id) {
        setTimeout(() => navigate(`/session/${response.data.id}`), 1500);
      } else {
        setTimeout(() => navigate('/'), 1500);
      }
    } catch (error) {
      console.error('Error creating session:', error);
      toast.showToast('error', 'Failed to log session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const compositeScore = readinessData.sleep + (6 - readinessData.stress) + (6 - readinessData.soreness) + readinessData.energy;
  const isSparringType = SPARRING_TYPES.includes(sessionData.class_type);

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">{activityType === 'rest' ? 'Rest Day Logged!' : 'Session Logged!'}</h2>
        <p className="text-gray-600 dark:text-gray-400">{activityType === 'rest' ? 'Redirecting to home...' : 'Redirecting to session details...'}</p>
        {activityType === 'training' && <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">You can add photos on the next page</p>}
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
            onClick={() => {
              setActivityType('training');
              setStep(1);
            }}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all"
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
            onClick={() => {
              setActivityType('rest');
              setStep(2); // Skip readiness for rest days
            }}
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

      {/* Progress Indicator (only for training) */}
      {activityType === 'training' && (
        <div className="mb-6">
        <div className="flex items-center justify-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
            step === 1
              ? 'bg-primary-600 text-white'
              : skippedReadiness
                ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 line-through'
                : 'bg-green-500 text-white'
          }`}>
            1
          </div>
          <div className="w-16 h-1 bg-gray-300 dark:bg-gray-600"></div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 2 ? 'bg-primary-600 text-white' : 'bg-gray-300 dark:bg-gray-600 text-gray-600'}`}>
            2
          </div>
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={`${step === 1 ? 'font-semibold' : skippedReadiness ? 'text-gray-400 line-through' : 'text-gray-500'}`}>
            Readiness Check {skippedReadiness && '(skipped)'}
          </span>
          <span className={step === 2 ? 'font-semibold' : 'text-gray-500'}>Session Details</span>
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

      {/* Step 1: Readiness (only for training) */}
      {activityType === 'training' && step === 1 && (
        <div className="card space-y-6">
          <p className="text-gray-600 dark:text-gray-400">
            Let's check your readiness before logging today's session.
          </p>

          {/* Sliders */}
          {(['sleep', 'stress', 'soreness', 'energy'] as const).map((metric) => (
            <div key={metric}>
              <label className="label capitalize flex justify-between">
                <span>{metric}</span>
                <span className="font-bold">{readinessData[metric]}/5</span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={readinessData[metric]}
                onChange={(e) => setReadinessData({ ...readinessData, [metric]: parseInt(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Low</span>
                <span>High</span>
              </div>
            </div>
          ))}

          {/* Composite Score */}
          <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Readiness Score</p>
            <p className="text-3xl font-bold text-primary-600">{compositeScore}/20</p>
          </div>

          {/* Hotspot */}
          <div>
            <label className="label">Any Injuries or Hotspots? (optional)</label>
            <input
              type="text"
              className="input"
              value={readinessData.hotspot_note}
              onChange={(e) => setReadinessData({ ...readinessData, hotspot_note: e.target.value })}
              placeholder="e.g., left shoulder, right knee"
            />
          </div>

          {/* Weight */}
          <div>
            <label className="label">Weight (kg) (optional)</label>
            <input
              type="number"
              className="input"
              value={readinessData.weight_kg}
              onChange={(e) => setReadinessData({ ...readinessData, weight_kg: e.target.value })}
              placeholder="e.g., 75.5"
              step="0.1"
              min="30"
              max="300"
            />
          </div>

          <button onClick={handleNextStep} className="btn-primary w-full flex items-center justify-center gap-2">
            Continue to Session Details
            <ArrowRight className="w-4 h-4" />
          </button>

          {/* Discreet skip option */}
          <div className="text-center mt-3">
            <button
              type="button"
              onClick={handleSkipReadiness}
              className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 underline"
            >
              Skip readiness check
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Training Session */}
      {activityType === 'training' && step === 2 && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          {/* Date */}
          <div>
            <label className="label">Date</label>
            <input
              type="date"
              className="input"
              value={sessionData.session_date}
              onChange={(e) => setSessionData({ ...sessionData, session_date: e.target.value })}
              required
            />
          </div>

          {/* Class Time */}
          <div>
            <label className="label">Class Time (optional)</label>
            <div className="flex gap-2 mb-2" role="group" aria-label="Common class times">
              {[
                { label: '6:30am', value: '06:30' },
                { label: '12pm', value: '12:00' },
                { label: '5:30pm', value: '17:30' },
                { label: '7pm', value: '19:00' },
              ].map((time) => (
                <button
                  key={time.value}
                  type="button"
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
            <input
              type="text"
              className="input text-sm"
              value={sessionData.class_time}
              onChange={(e) => setSessionData({ ...sessionData, class_time: e.target.value })}
              placeholder="Or type custom time (e.g., 18:30, morning)"
            />
          </div>

          {/* Class Type */}
          <div>
            <label className="label">Class Type</label>
            <select
              className="input"
              value={sessionData.class_type}
              onChange={(e) => setSessionData({ ...sessionData, class_type: e.target.value })}
              required
            >
              {CLASS_TYPES.map((type) => (
                <option key={type} value={type}>{CLASS_TYPE_LABELS[type] || type}</option>
              ))}
            </select>
          </div>

          {/* Gym Name */}
          <div>
            <label className="label">Gym Name</label>
            <GymSelector
              value={sessionData.gym_name}
              onChange={(gymName, _isCustom) => {
                setSessionData({ ...sessionData, gym_name: gymName });
              }}
              onGymSelected={(gym) => {
                // Auto-populate instructor with gym's head coach if available
                if (gym.head_coach) {
                  setSessionData(prev => ({
                    ...prev,
                    gym_name: [gym.name, gym.city, gym.state, gym.country].filter(Boolean).join(', '),
                    instructor_name: gym.head_coach ?? '',
                    instructor_id: null, // Clear instructor_id since head coach is free text
                  }));
                }
              }}
            />
            <p className="text-xs text-gray-500 mt-1">
              Select from verified gyms or add a new one. Head coach will auto-populate if available.
            </p>
          </div>

          {/* Instructor */}
          <div>
            <label className="label">Instructor (optional)</label>
            <select
              className="input"
              value={sessionData.instructor_id || ''}
              onChange={(e) => {
                const instructorId = e.target.value ? parseInt(e.target.value) : null;
                const instructor = instructors.find(i => i.id === instructorId);
                setSessionData({
                  ...sessionData,
                  instructor_id: instructorId,
                  instructor_name: instructor?.name || '',
                });
              }}
            >
              <option value="">Select instructor...</option>
              {instructors.map(instructor => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name ?? 'Unknown'}
                  {instructor.belt_rank && ` (${instructor.belt_rank} belt)`}
                  {instructor.instructor_certification && ` - ${instructor.instructor_certification}`}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Select from your list. <a href="/friends" className="text-primary-600 hover:underline">Manage instructors in Friends</a>
            </p>
          </div>

          {/* Location */}
          <div>
            <label className="label">Location (optional)</label>
            <input
              type="text"
              className="input"
              value={sessionData.location}
              onChange={(e) => setSessionData({ ...sessionData, location: e.target.value })}
              placeholder="e.g., Sydney, NSW"
              list="locations"
            />
            {autocomplete.locations && (
              <datalist id="locations">
                {autocomplete.locations.map((loc: string) => (
                  <option key={loc} value={loc} />
                ))}
              </datalist>
            )}
          </div>

          {/* Duration */}
          <div>
            <label className="label">Duration (minutes)</label>
            <div className="flex gap-2 mb-2" role="group" aria-label="Duration options">
              {[60, 75, 90, 120].map((mins) => (
                <button
                  key={mins}
                  type="button"
                  onClick={() => setSessionData({ ...sessionData, duration_mins: mins })}
                  className="flex-1 min-h-[44px] py-3 rounded-lg font-medium text-sm transition-all"
                  style={{
                    backgroundColor: sessionData.duration_mins === mins ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: sessionData.duration_mins === mins ? '#FFFFFF' : 'var(--text)',
                    border: sessionData.duration_mins === mins ? 'none' : '1px solid var(--border)',
                  }}
                  aria-label={`${mins} minutes`}
                  aria-pressed={sessionData.duration_mins === mins}
                >
                  {mins}m
                </button>
              ))}
            </div>
            <input
              type="number"
              className="input text-sm"
              value={sessionData.duration_mins}
              onChange={(e) => setSessionData({ ...sessionData, duration_mins: parseInt(e.target.value) || 0 })}
              placeholder="Or enter custom duration"
              min="1"
              required
            />
          </div>

          {/* Intensity */}
          <div>
            <label className="label">Intensity</label>
            <div className="flex gap-2" role="group" aria-label="Intensity options">
              {[1, 2, 3, 4, 5].map((level) => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setSessionData({ ...sessionData, intensity: level })}
                  className="flex-1 min-h-[44px] py-3 rounded-lg font-semibold transition-all"
                  style={{
                    backgroundColor: sessionData.intensity === level ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: sessionData.intensity === level ? '#FFFFFF' : 'var(--text)',
                    border: sessionData.intensity === level ? 'none' : '1px solid var(--border)',
                  }}
                  aria-label={`Intensity level ${level} of 5`}
                  aria-pressed={sessionData.intensity === level}
                >
                  {level}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              1 = Light, 3 = Moderate, 5 = Maximum effort
            </p>
          </div>

          {/* Technique Focus */}
          <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Technique of the Day</h3>
              <button
                type="button"
                onClick={handleAddTechnique}
                className="flex items-center gap-2 px-3 py-1 min-h-[44px] bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
              >
                <Plus className="w-4 h-4" />
                Add Technique
              </button>
            </div>

            {techniques.length === 0 ? (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Click "Add Technique" to track techniques you focused on today
              </p>
            ) : (
              <div className="space-y-4">
                {techniques.map((tech, index) => (
                  <div key={index} className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">Technique #{tech.technique_number}</h4>
                      <button
                        type="button"
                        onClick={() => handleRemoveTechnique(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Movement Selection */}
                    <div>
                      <label className="label text-sm">Movement</label>
                      <div className="relative mb-2">
                        <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="text"
                          className="input pl-8 text-sm"
                          placeholder="Search movements..."
                          value={techniqueSearch[index] || ''}
                          onChange={(e) => setTechniqueSearch({ ...techniqueSearch, [index]: e.target.value })}
                        />
                      </div>
                      <div className="max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2 space-y-1">
                        {movements
                          .filter(m => {
                            const search = techniqueSearch[index]?.toLowerCase() ?? '';
                            return m.name?.toLowerCase().includes(search) ||
                                   m.category?.toLowerCase().includes(search) ||
                                   m.subcategory?.toLowerCase().includes(search) ||
                                   (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                          })
                          .map(movement => (
                            <button
                              key={movement.id}
                              type="button"
                              onClick={() => {
                                const updated = [...techniques];
                                updated[index] = {
                                  ...updated[index],
                                  movement_id: movement.id,
                                  movement_name: movement.name ?? ''
                                };
                                setTechniques(updated);
                              }}
                              className={`w-full text-left px-2 py-2 min-h-[44px] rounded text-sm ${
                                tech.movement_id === movement.id
                                  ? 'bg-primary-600 text-white'
                                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                              }`}
                            >
                              <span className="font-medium">{movement.name ?? 'Unknown'}</span>
                              <span className="text-xs ml-2 opacity-75">
                                {movement.category ?? 'N/A'}
                                {movement.subcategory && ` - ${movement.subcategory}`}
                              </span>
                            </button>
                          ))}
                        {movements.filter(m => {
                          const search = techniqueSearch[index]?.toLowerCase() ?? '';
                          return m.name?.toLowerCase().includes(search) ||
                                 m.category?.toLowerCase().includes(search) ||
                                 m.subcategory?.toLowerCase().includes(search) ||
                                 (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                        }).length === 0 && (
                          <p className="text-xs text-gray-500 text-center py-2">No movements found</p>
                        )}
                      </div>
                      {tech.movement_id && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Selected: <span className="font-medium">{tech.movement_name}</span>
                        </p>
                      )}
                    </div>

                    {/* Notes */}
                    <div>
                      <label className="label text-sm">Notes / Key Points</label>
                      <textarea
                        className="input resize-none"
                        rows={3}
                        value={tech.notes}
                        onChange={(e) => handleTechniqueChange(index, 'notes', e.target.value)}
                        placeholder="What did you learn? Key details, insights, or observations..."
                      />
                    </div>

                    {/* Media URLs */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="label text-sm mb-0">Reference Media</label>
                        <button
                          type="button"
                          onClick={() => handleAddMediaUrl(index)}
                          className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                        >
                          <Plus className="w-3 h-3" />
                          Add Link
                        </button>
                      </div>
                      {tech.media_urls.length === 0 ? (
                        <p className="text-xs text-gray-500">No media links added</p>
                      ) : (
                        <div className="space-y-2">
                          {tech.media_urls.map((media, mediaIndex) => (
                            <div key={mediaIndex} className="border border-gray-200 dark:border-gray-700 rounded p-2 space-y-2">
                              <div className="flex items-center justify-between">
                                <select
                                  className="input-sm text-xs"
                                  value={media.type}
                                  onChange={(e) => handleMediaUrlChange(index, mediaIndex, 'type', e.target.value as 'video' | 'image')}
                                >
                                  <option value="video">Video</option>
                                  <option value="image">Image</option>
                                </select>
                                <button
                                  type="button"
                                  onClick={() => handleRemoveMediaUrl(index, mediaIndex)}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </div>
                              <input
                                type="text"
                                className="input text-xs"
                                placeholder="URL (YouTube, Instagram, etc.)"
                                value={media.url}
                                onChange={(e) => handleMediaUrlChange(index, mediaIndex, 'url', e.target.value)}
                              />
                              <input
                                type="text"
                                className="input text-xs"
                                placeholder="Title (optional)"
                                value={media.title ?? ''}
                                onChange={(e) => handleMediaUrlChange(index, mediaIndex, 'title', e.target.value)}
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sparring Details */}
          {isSparringType && (
            <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">Roll Tracking</h3>
                <button
                  type="button"
                  onClick={() => setDetailedMode(!detailedMode)}
                  className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700"
                >
                  {detailedMode ? (
                    <>
                      <ToggleRight className="w-5 h-5" />
                      Detailed Mode
                    </>
                  ) : (
                    <>
                      <ToggleLeft className="w-5 h-5" />
                      Simple Mode
                    </>
                  )}
                </button>
              </div>

              {!detailedMode ? (
                // Simple Mode: Aggregate counts
                <>
                  <div>
                    <label className="label">Rolls</label>
                    <input
                      type="number"
                      className="input"
                      value={sessionData.rolls}
                      onChange={(e) => setSessionData({ ...sessionData, rolls: parseInt(e.target.value) })}
                      min="0"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="label">Submissions For</label>
                      <input
                        type="number"
                        className="input"
                        value={sessionData.submissions_for}
                        onChange={(e) => setSessionData({ ...sessionData, submissions_for: parseInt(e.target.value) })}
                        min="0"
                      />
                    </div>
                    <div>
                      <label className="label">Submissions Against</label>
                      <input
                        type="number"
                        className="input"
                        value={sessionData.submissions_against}
                        onChange={(e) => setSessionData({ ...sessionData, submissions_against: parseInt(e.target.value) })}
                        min="0"
                      />
                    </div>
                  </div>
                </>
              ) : (
                // Detailed Mode: Individual rolls
                <div className="space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Track each roll with partner and submissions from glossary
                  </p>

                  {rolls.map((roll, index) => (
                    <div key={index} className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold">Roll #{roll.roll_number}</h4>
                        <button
                          type="button"
                          onClick={() => handleRemoveRoll(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Partner Selection */}
                      <div>
                        <label className="label text-sm">Partner</label>
                        <select
                          className="input"
                          value={roll.partner_id || ''}
                          onChange={(e) => {
                            const partnerId = e.target.value ? parseInt(e.target.value) : null;
                            const partner = partners.find(p => p.id === partnerId);
                            handleRollChange(index, 'partner_id', partnerId);
                            handleRollChange(index, 'partner_name', partner ? partner.name : '');
                          }}
                        >
                          <option value="">Select partner...</option>
                          {partners.map(partner => (
                            <option key={partner.id} value={partner.id}>
                              {partner.name ?? 'Unknown'}
                              {partner.belt_rank && ` (${partner.belt_rank} belt)`}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Duration */}
                      <div>
                        <label className="label text-sm">Duration (mins)</label>
                        <input
                          type="number"
                          className="input"
                          value={roll.duration_mins}
                          onChange={(e) => handleRollChange(index, 'duration_mins', parseInt(e.target.value))}
                          min="1"
                        />
                      </div>

                      {/* Submissions For */}
                      <div>
                        <label className="label text-sm">Submissions You Got</label>
                        <div className="relative mb-2">
                          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="text"
                            className="input pl-8 text-sm"
                            placeholder="Search submissions..."
                            value={submissionSearchFor[index] || ''}
                            onChange={(e) => setSubmissionSearchFor({ ...submissionSearchFor, [index]: e.target.value })}
                          />
                        </div>
                        <div className="max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2 space-y-1">
                          {movements
                            .filter(m => m.category === 'submission')
                            .filter(m => {
                              const search = submissionSearchFor[index]?.toLowerCase() ?? '';
                              return m.name?.toLowerCase().includes(search) ||
                                     m.subcategory?.toLowerCase().includes(search) ||
                                     (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                            })
                            .map(movement => (
                              <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-1 rounded">
                                <input
                                  type="checkbox"
                                  checked={roll.submissions_for.includes(movement.id)}
                                  onChange={() => handleToggleSubmission(index, movement.id, 'for')}
                                  className="w-4 h-4"
                                />
                                <span>{movement.name ?? 'Unknown'}</span>
                              </label>
                            ))}
                          {movements.filter(m => m.category === 'submission').filter(m => {
                            const search = submissionSearchFor[index]?.toLowerCase() ?? '';
                            return m.name?.toLowerCase().includes(search) ||
                                   m.subcategory?.toLowerCase().includes(search) ||
                                   (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                          }).length === 0 && (
                            <p className="text-xs text-gray-500 text-center py-2">No submissions found</p>
                          )}
                        </div>
                      </div>

                      {/* Submissions Against */}
                      <div>
                        <label className="label text-sm">Submissions They Got</label>
                        <div className="relative mb-2">
                          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="text"
                            className="input pl-8 text-sm"
                            placeholder="Search submissions..."
                            value={submissionSearchAgainst[index] || ''}
                            onChange={(e) => setSubmissionSearchAgainst({ ...submissionSearchAgainst, [index]: e.target.value })}
                          />
                        </div>
                        <div className="max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2 space-y-1">
                          {movements
                            .filter(m => m.category === 'submission')
                            .filter(m => {
                              const search = submissionSearchAgainst[index]?.toLowerCase() ?? '';
                              return m.name?.toLowerCase().includes(search) ||
                                     m.subcategory?.toLowerCase().includes(search) ||
                                     (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                            })
                            .map(movement => (
                              <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-1 rounded">
                                <input
                                  type="checkbox"
                                  checked={roll.submissions_against.includes(movement.id)}
                                  onChange={() => handleToggleSubmission(index, movement.id, 'against')}
                                  className="w-4 h-4"
                                />
                                <span>{movement.name ?? 'Unknown'}</span>
                              </label>
                            ))}
                          {movements.filter(m => m.category === 'submission').filter(m => {
                            const search = submissionSearchAgainst[index]?.toLowerCase() ?? '';
                            return m.name?.toLowerCase().includes(search) ||
                                   m.subcategory?.toLowerCase().includes(search) ||
                                   (m.aliases ?? []).some(alias => alias.toLowerCase().includes(search));
                          }).length === 0 && (
                            <p className="text-xs text-gray-500 text-center py-2">No submissions found</p>
                          )}
                        </div>
                      </div>

                      {/* Roll Notes */}
                      <div>
                        <label className="label text-sm">Notes (optional)</label>
                        <input
                          type="text"
                          className="input"
                          value={roll.notes}
                          onChange={(e) => handleRollChange(index, 'notes', e.target.value)}
                          placeholder="How did this roll go?"
                        />
                      </div>
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={handleAddRoll}
                    className="btn-secondary w-full flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add Roll
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Partners (Simple mode sparring only) */}
          {!detailedMode && isSparringType && (
            <div>
              <label className="label">Partners (comma-separated)</label>
              <input
                type="text"
                className="input"
                value={sessionData.partners}
                onChange={(e) => setSessionData({ ...sessionData, partners: e.target.value })}
                placeholder="e.g., John, Sarah"
              />
            </div>
          )}

          {/* Whoop Stats (Optional) */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-semibold mb-3">Whoop Stats (optional)</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Activity Strain</label>
                <input
                  type="number"
                  className="input"
                  value={sessionData.whoop_strain}
                  onChange={(e) => setSessionData({ ...sessionData, whoop_strain: e.target.value })}
                  placeholder="0-21"
                  min="0"
                  max="21"
                  step="0.1"
                />
              </div>
              <div>
                <label className="label">Calories</label>
                <input
                  type="number"
                  className="input"
                  value={sessionData.whoop_calories}
                  onChange={(e) => setSessionData({ ...sessionData, whoop_calories: e.target.value })}
                  placeholder="e.g., 500"
                  min="0"
                />
              </div>
              <div>
                <label className="label">Avg HR (bpm)</label>
                <input
                  type="number"
                  className="input"
                  value={sessionData.whoop_avg_hr}
                  onChange={(e) => setSessionData({ ...sessionData, whoop_avg_hr: e.target.value })}
                  placeholder="e.g., 140"
                  min="0"
                  max="250"
                />
              </div>
              <div>
                <label className="label">Max HR (bpm)</label>
                <input
                  type="number"
                  className="input"
                  value={sessionData.whoop_max_hr}
                  onChange={(e) => setSessionData({ ...sessionData, whoop_max_hr: e.target.value })}
                  placeholder="e.g., 185"
                  min="0"
                  max="250"
                />
              </div>
            </div>
          </div>

          {/* Fight Dynamics (BJJ sessions only) */}
          {isSparringType && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <button
                type="button"
                onClick={() => setShowFightDynamics(!showFightDynamics)}
                className="flex items-center justify-between w-full text-left"
              >
                <div>
                  <h3 className="font-semibold text-lg flex items-center gap-2">
                    <Swords className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                    Fight Dynamics
                    <span className="text-xs font-normal px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}>
                      optional
                    </span>
                  </h3>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>For comp prep — track attacks and defences</p>
                </div>
                {showFightDynamics ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>

              {showFightDynamics && (
                <div className="mt-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Attack Column */}
                    <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(255, 77, 45, 0.08)', border: '1px solid rgba(255, 77, 45, 0.2)' }}>
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                        <Swords className="w-4 h-4" />
                        ATTACK
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Attempted</label>
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, attacks_attempted: Math.max(0, fd.attacks_attempted - 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                              <Minus className="w-4 h-4" />
                            </button>
                            <input
                              type="number"
                              className="input text-center font-bold text-lg flex-1"
                              value={fightDynamics.attacks_attempted}
                              onChange={(e) => setFightDynamics({ ...fightDynamics, attacks_attempted: Math.max(0, parseInt(e.target.value) || 0) })}
                              min="0"
                            />
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, attacks_attempted: fd.attacks_attempted + 1 }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                              <Plus className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <div>
                          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Successful</label>
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, attacks_successful: Math.max(0, fd.attacks_successful - 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                              <Minus className="w-4 h-4" />
                            </button>
                            <input
                              type="number"
                              className="input text-center font-bold text-lg flex-1"
                              value={fightDynamics.attacks_successful}
                              onChange={(e) => setFightDynamics({ ...fightDynamics, attacks_successful: Math.min(fightDynamics.attacks_attempted, Math.max(0, parseInt(e.target.value) || 0)) })}
                              min="0"
                              max={fightDynamics.attacks_attempted}
                            />
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, attacks_successful: Math.min(fd.attacks_attempted, fd.attacks_successful + 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                              <Plus className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                      {fightDynamics.attacks_attempted > 0 && (
                        <p className="text-xs font-semibold mt-2 text-center" style={{ color: 'var(--accent)' }}>
                          {Math.round((fightDynamics.attacks_successful / fightDynamics.attacks_attempted) * 100)}% success
                        </p>
                      )}
                    </div>

                    {/* Defence Column */}
                    <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(0, 149, 255, 0.08)', border: '1px solid rgba(0, 149, 255, 0.2)' }}>
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-1" style={{ color: '#0095FF' }}>
                        <Shield className="w-4 h-4" />
                        DEFENCE
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Attempted</label>
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, defenses_attempted: Math.max(0, fd.defenses_attempted - 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                              <Minus className="w-4 h-4" />
                            </button>
                            <input
                              type="number"
                              className="input text-center font-bold text-lg flex-1"
                              value={fightDynamics.defenses_attempted}
                              onChange={(e) => setFightDynamics({ ...fightDynamics, defenses_attempted: Math.max(0, parseInt(e.target.value) || 0) })}
                              min="0"
                            />
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, defenses_attempted: fd.defenses_attempted + 1 }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: '#0095FF', color: '#fff' }}>
                              <Plus className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <div>
                          <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--muted)' }}>Successful</label>
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, defenses_successful: Math.max(0, fd.defenses_successful - 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
                              <Minus className="w-4 h-4" />
                            </button>
                            <input
                              type="number"
                              className="input text-center font-bold text-lg flex-1"
                              value={fightDynamics.defenses_successful}
                              onChange={(e) => setFightDynamics({ ...fightDynamics, defenses_successful: Math.min(fightDynamics.defenses_attempted, Math.max(0, parseInt(e.target.value) || 0)) })}
                              min="0"
                              max={fightDynamics.defenses_attempted}
                            />
                            <button type="button" onClick={() => setFightDynamics(fd => ({ ...fd, defenses_successful: Math.min(fd.defenses_attempted, fd.defenses_successful + 1) }))} className="w-9 h-9 rounded-lg flex items-center justify-center font-bold" style={{ backgroundColor: '#0095FF', color: '#fff' }}>
                              <Plus className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                      {fightDynamics.defenses_attempted > 0 && (
                        <p className="text-xs font-semibold mt-2 text-center" style={{ color: '#0095FF' }}>
                          {Math.round((fightDynamics.defenses_successful / fightDynamics.defenses_attempted) * 100)}% success
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Session Details / Notes */}
          <div className={!isSparringType ? 'border-t border-gray-200 dark:border-gray-700 pt-4' : ''}>
            <label className="label">
              {!isSparringType ? 'Session Details' : 'Notes'}
              {!isSparringType && <span className="text-sm font-normal text-gray-500 ml-2">(Workout details, exercises, distances, times, etc.)</span>}
            </label>
            <textarea
              className="input"
              value={sessionData.notes}
              onChange={(e) => setSessionData({ ...sessionData, notes: e.target.value })}
              rows={!isSparringType ? 5 : 3}
              placeholder={
                !isSparringType
                  ? "e.g., 5km run in 30 mins, Deadlifts 3x8 @ 100kg, Squats 3x10 @ 80kg, or Yoga flow focusing on hip mobility..."
                  : "Any notes about today's training..."
              }
            />
          </div>

          {/* Photo Upload Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-start gap-2">
            <Camera className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <span className="font-semibold">Want to add photos?</span> Save the session first, then you can upload up to 3 photos on the next page.
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleBackStep}
              className="btn-secondary flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1"
            >
              {loading ? 'Logging Session...' : 'Log Session'}
            </button>
          </div>
        </form>
      )}

      {/* Rest Day Form */}
      {activityType === 'rest' && step === 2 && (
        <form onSubmit={handleSubmit} className="card space-y-4">
          {/* Date */}
          <div>
            <label className="label">Date</label>
            <input
              type="date"
              className="input"
              value={restData.rest_date}
              onChange={(e) => setRestData({ ...restData, rest_date: e.target.value })}
              required
            />
          </div>

          {/* Rest Type */}
          <div>
            <label className="label">Rest Type</label>
            <div className="flex gap-2" role="group" aria-label="Rest type options">
              {['active', 'passive', 'injury'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setRestData({ ...restData, rest_type: type })}
                  className="flex-1 py-3 rounded-lg font-medium text-sm transition-all capitalize"
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
            <p className="text-xs text-gray-500 mt-2">
              <span className="font-semibold">Active:</span> Light activity, stretching, mobility work.
              <span className="font-semibold ml-3">Passive:</span> Complete rest, no training.
              <span className="font-semibold ml-3">Injury:</span> Recovering from injury.
            </p>
          </div>

          {/* Note */}
          <div>
            <label className="label">Note (optional)</label>
            <textarea
              className="input"
              rows={4}
              value={restData.rest_note}
              onChange={(e) => setRestData({ ...restData, rest_note: e.target.value })}
              placeholder="Any notes about your rest day, recovery activities, or how you're feeling..."
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Logging Rest Day...' : 'Log Rest Day'}
          </button>
        </form>
      )}
    </div>
  );
}

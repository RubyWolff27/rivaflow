import { useState, useEffect, useMemo, useCallback } from 'react';
import { getLocalDateString } from '../utils/date';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { sessionsApi, readinessApi, profileApi, friendsApi, socialApi, glossaryApi, restApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Readiness, Movement } from '../types';
import { CheckCircle, ArrowLeft, Mic, MicOff, ChevronDown, ChevronUp } from 'lucide-react';
import WhoopMatchModal from '../components/WhoopMatchModal';
import GymSelector from '../components/GymSelector';
import { ClassTypeChips, IntensityChips } from '../components/ui';
import { useToast } from '../contexts/ToastContext';
import { triggerInsightRefresh } from '../utils/insightRefresh';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import ReadinessStep from '../components/sessions/ReadinessStep';
import TechniqueTracker from '../components/sessions/TechniqueTracker';
import RollTracker from '../components/sessions/RollTracker';
import ClassTimePicker from '../components/sessions/ClassTimePicker';
import WhoopIntegrationPanel from '../components/sessions/WhoopIntegrationPanel';
import FightDynamicsPanel from '../components/sessions/FightDynamicsPanel';
import { useSessionForm, mergePartners, mapSocialFriends } from '../hooks/useSessionForm';

const DURATION_QUICK_SELECT = [60, 75, 90, 120] as const;

export default function LogSession() {
  usePageTitle('Log Session');
  const navigate = useNavigate();
  const toast = useToast();
  const [activityType, setActivityType] = useState<'training' | 'rest'>('training');
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [skippedReadiness, setSkippedReadiness] = useState(false);
  const [readinessAutoSkipped, setReadinessAutoSkipped] = useState(false);

  const form = useSessionForm({
    initialData: { session_date: getLocalDateString() },
  });

  const [readinessData, setReadinessData] = useState({
    check_date: getLocalDateString(),
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
    weight_kg: '',
  });

  const [restData, setRestData] = useState({
    rest_date: getLocalDateString(),
    rest_type: 'active',
    rest_note: '',
  });

  // Voice-to-text for notes
  const onTranscript = useCallback((transcript: string) => {
    form.setSessionData(prev => ({
      ...prev,
      notes: prev.notes ? `${prev.notes} ${transcript}` : transcript,
    }));
  }, [form]);
  const onSpeechError = useCallback((message: string) => {
    toast.error(message);
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

        form.setAutocomplete(autocompleteRes.data ?? {});
        const loadedInstructors = instructorsRes.data ?? [];
        form.setInstructors(loadedInstructors);
        const manualPartners = partnersRes.data ?? [];
        const socialFriends = mapSocialFriends(socialFriendsRes.data.friends || []);
        form.setPartners(mergePartners(manualPartners, loadedInstructors, socialFriends));
        const movementsData = movementsRes.data as Movement[] | { movements: Movement[] };
        form.setMovements(Array.isArray(movementsData) ? movementsData : movementsData?.movements || []);

        const updates: Record<string, string | number | null> = {};
        if (profileRes.data?.default_gym) {
          updates.gym_name = profileRes.data.default_gym;
        }
        if (profileRes.data?.primary_gym_id) {
          updates.gym_id = profileRes.data.primary_gym_id;
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
          form.setSessionData(prev => ({ ...prev, ...updates }));
        }

        // Check if readiness already logged today — auto-skip step 1
        try {
          const today = getLocalDateString();
          const readinessRes = await readinessApi.getByDate(today);
          if (!controller.signal.aborted && readinessRes.data) {
            setReadinessData(prev => ({
              ...prev,
              sleep: readinessRes.data.sleep ?? prev.sleep,
              stress: readinessRes.data.stress ?? prev.stress,
              soreness: readinessRes.data.soreness ?? prev.soreness,
              energy: readinessRes.data.energy ?? prev.energy,
              hotspot_note: readinessRes.data.hotspot_note ?? prev.hotspot_note,
              weight_kg: readinessRes.data.weight_kg?.toString() ?? prev.weight_kg,
            }));
            setSkippedReadiness(true);
            setReadinessAutoSkipped(true);
            setStep(2);
          }
        } catch {
          // No readiness logged today — show step 1 as normal
        }

        try {
          const whoopRes = await whoopApi.getStatus();
          if (!controller.signal.aborted && whoopRes.data?.connected) {
            form.setWhoopConnected(true);
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

      const { gym_id: _gymId, ...sessionPayloadData } = form.sessionData;
      const payload: Record<string, unknown> = {
        ...sessionPayloadData,
        class_time: form.sessionData.class_time || undefined,
        location: form.sessionData.location || undefined,
        notes: form.sessionData.notes || undefined,
        partners: (() => {
          const pillNames = form.topPartners.filter(p => form.selectedPartnerIds.has(p.id)).map(p => p.name);
          const typedNames = form.sessionData.partners ? form.sessionData.partners.split(',').map(p => p.trim()).filter(Boolean) : [];
          const all = [...pillNames, ...typedNames];
          return all.length > 0 ? all : undefined;
        })(),
        techniques: form.sessionData.techniques ? form.sessionData.techniques.split(',').map(t => t.trim()) : undefined,
        visibility_level: 'private',
        ...form.buildWhoopPayload(),
        ...form.buildFightDynamicsPayload(),
      };

      if (form.sessionData.instructor_id) {
        payload.instructor_id = form.sessionData.instructor_id;
        const instructor = form.instructors.find(i => i.id === form.sessionData.instructor_id);
        if (instructor) payload.instructor_name = instructor.name ?? undefined;
      } else if (form.sessionData.instructor_name) {
        payload.instructor_name = form.sessionData.instructor_name;
      } else {
        payload.instructor_id = undefined;
        payload.instructor_name = undefined;
      }

      const rollsPayload = form.buildRollsPayload();
      if (rollsPayload.session_rolls) {
        payload.session_rolls = rollsPayload.session_rolls;
        payload.rolls = rollsPayload.rolls;
        payload.submissions_for = rollsPayload.submissions_for;
        payload.submissions_against = rollsPayload.submissions_against;
      }

      const techniquesPayload = form.buildTechniquesPayload();
      if (techniquesPayload.session_techniques) {
        payload.session_techniques = techniquesPayload.session_techniques;
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
      toast.error('Failed to log session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const compositeScore = useMemo(
    () => readinessData.sleep + (6 - readinessData.stress) + (6 - readinessData.soreness) + readinessData.energy,
    [readinessData.sleep, readinessData.stress, readinessData.soreness, readinessData.energy]
  );

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
          {/* Readiness auto-skip note */}
          {readinessAutoSkipped && (
            <div className="flex items-center justify-between text-sm rounded-lg px-3 py-2" style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: '#16a34a' }}>
              <span>Readiness already logged today</span>
              <button type="button" onClick={() => { setReadinessAutoSkipped(false); setSkippedReadiness(false); setStep(1); }}
                className="font-medium underline" style={{ color: 'var(--accent)' }}>
                Edit
              </button>
            </div>
          )}
          {/* Date */}
          <div>
            <label className="label">Date</label>
            <input type="date" className="input" value={form.sessionData.session_date}
              onChange={(e) => form.setSessionData(prev => ({ ...prev, session_date: e.target.value }))} required />
          </div>

          {/* Class Time */}
          <ClassTimePicker
            gymId={form.sessionData.gym_id}
            classTime={form.sessionData.class_time}
            onSelect={(classTime, classType, durationMins) => {
              form.setSessionData(prev => ({
                ...prev,
                class_time: classTime,
                ...(classType ? { class_type: classType } : {}),
                ...(durationMins ? { duration_mins: durationMins } : {}),
              }));
            }}
          />

          {/* Class Type */}
          <div>
            <label className="label">Class Type</label>
            <ClassTypeChips value={form.sessionData.class_type}
              onChange={(val) => form.setSessionData(prev => ({ ...prev, class_type: val }))} />
          </div>

          {/* Gym Name */}
          <div>
            <label className="label">Gym Name</label>
            <GymSelector
              value={form.sessionData.gym_name}
              onChange={(gymName, isCustom) => {
                form.setSessionData(prev => ({
                  ...prev,
                  gym_name: gymName,
                  gym_id: isCustom ? null : prev.gym_id,
                }));
              }}
              onGymSelected={(gym) => {
                form.setSessionData(prev => ({
                  ...prev,
                  gym_name: [gym.name, gym.city, gym.state, gym.country].filter(Boolean).join(', '),
                  gym_id: gym.id,
                  instructor_name: gym.head_coach ?? prev.instructor_name,
                  instructor_id: gym.head_coach ? null : prev.instructor_id,
                }));
              }}
            />
            <p className="text-xs text-[var(--muted)] mt-1">
              Select from verified gyms or add a new one. Head coach will auto-populate if available.
            </p>
          </div>

          {/* Duration */}
          <div>
            <label className="label">Duration (minutes)</label>
            {(() => {
              const isStandard = (DURATION_QUICK_SELECT as readonly number[]).includes(form.sessionData.duration_mins);
              const isCustomActive = !isStandard || form.showCustomDuration;
              return (
                <>
                  <div className="flex flex-wrap gap-2" role="group" aria-label="Duration options">
                    {DURATION_QUICK_SELECT.map((mins) => (
                      <button key={mins} type="button"
                        onClick={() => { form.setSessionData(prev => ({ ...prev, duration_mins: mins })); form.setShowCustomDuration(false); }}
                        className="flex-1 min-h-[44px] py-3 rounded-lg font-medium text-sm transition-all"
                        style={{
                          backgroundColor: form.sessionData.duration_mins === mins && !form.showCustomDuration ? 'var(--accent)' : 'var(--surfaceElev)',
                          color: form.sessionData.duration_mins === mins && !form.showCustomDuration ? '#FFFFFF' : 'var(--text)',
                          border: form.sessionData.duration_mins === mins && !form.showCustomDuration ? 'none' : '1px solid var(--border)',
                        }}
                        aria-label={`${mins} minutes`} aria-pressed={form.sessionData.duration_mins === mins && !form.showCustomDuration}
                      >
                        {mins}m
                      </button>
                    ))}
                    <button type="button"
                      onClick={() => form.setShowCustomDuration(true)}
                      className="flex-1 min-h-[44px] py-3 rounded-lg font-medium text-sm transition-all"
                      style={{
                        backgroundColor: isCustomActive ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: isCustomActive ? '#FFFFFF' : 'var(--text)',
                        border: isCustomActive ? 'none' : '1px solid var(--border)',
                      }}
                      aria-pressed={isCustomActive}
                    >
                      {isCustomActive && !isStandard ? `${form.sessionData.duration_mins}m` : 'Custom'}
                    </button>
                  </div>
                  {isCustomActive && (
                    <input type="number" className="input text-sm mt-2" value={form.sessionData.duration_mins}
                      onChange={(e) => form.setSessionData(prev => ({ ...prev, duration_mins: parseInt(e.target.value) || 0 }))}
                      placeholder="Enter duration in minutes" min="1" autoFocus />
                  )}
                </>
              );
            })()}
          </div>

          {/* Intensity */}
          <div>
            <label className="label">Intensity</label>
            <IntensityChips value={form.sessionData.intensity}
              onChange={(val) => form.setSessionData(prev => ({ ...prev, intensity: val }))} />
          </div>

          {/* Notes */}
          <div className="border-t border-[var(--border)] pt-4">
            <label className="label">
              {form.isSparringType ? 'Notes' : 'Session Details'}
              {!form.isSparringType && (
                <span className="text-sm font-normal text-[var(--muted)] ml-2">(Workout details, exercises, distances, times, etc.)</span>
              )}
            </label>
            <div className="relative">
              <textarea className="input" value={form.sessionData.notes}
                onChange={(e) => form.setSessionData(prev => ({ ...prev, notes: e.target.value }))}
                rows={form.isSparringType ? 3 : 5}
                placeholder={form.isSparringType
                  ? "Any notes about today's training..."
                  : "e.g., 5km run in 30 mins, Deadlifts 3x8 @ 100kg, Squats 3x10 @ 80kg, or Yoga flow focusing on hip mobility..."} />
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

          {/* Collapsible More Details — Instructor, Location */}
          <div className="border-t border-[var(--border)] pt-3">
            <button type="button" onClick={() => form.setShowMoreDetails(!form.showMoreDetails)}
              className="flex items-center justify-between w-full text-sm text-[var(--muted)] hover:text-[var(--text)] transition-colors">
              <span className="font-medium">
                More Details
                {!form.showMoreDetails && (form.sessionData.instructor_name || form.sessionData.location) && (
                  <span className="ml-2 text-xs font-normal">
                    {[
                      form.sessionData.instructor_name && `Instructor: ${form.sessionData.instructor_name}`,
                      form.sessionData.location && `Location: ${form.sessionData.location}`,
                    ].filter(Boolean).join(' | ')}
                  </span>
                )}
              </span>
              {form.showMoreDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {form.showMoreDetails && (
              <div className="space-y-4 mt-3">
                {/* Instructor */}
                <div>
                  <label className="label">Instructor (optional)</label>
                  <select className="input" value={form.sessionData.instructor_id || ''}
                    onChange={(e) => {
                      const instructorId = e.target.value ? parseInt(e.target.value) : null;
                      const instructor = form.instructors.find(i => i.id === instructorId);
                      form.setSessionData(prev => ({ ...prev, instructor_id: instructorId, instructor_name: instructor?.name || '' }));
                    }}>
                    <option value="">Select instructor...</option>
                    {form.instructors.map(instructor => (
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
                  <input type="text" className="input" value={form.sessionData.location}
                    onChange={(e) => form.setSessionData(prev => ({ ...prev, location: e.target.value }))}
                    placeholder="e.g., Sydney, NSW" list="locations" />
                  {form.autocomplete.locations && (
                    <datalist id="locations">
                      {form.autocomplete.locations.map((loc: string) => <option key={loc} value={loc} />)}
                    </datalist>
                  )}
                </div>

              </div>
            )}
          </div>

          {/* Technique Tracker */}
          <TechniqueTracker
            techniques={form.techniques}
            techniqueSearch={form.techniqueSearch}
            onSearchChange={(index, value) => form.setTechniqueSearch(prev => ({ ...prev, [index]: value }))}
            filterMovements={form.filterMovements}
            onAdd={form.handleAddTechnique}
            onRemove={form.handleRemoveTechnique}
            onChange={form.handleTechniqueChange}
            onSelectMovement={form.handleSelectMovement}
            onAddMediaUrl={form.handleAddMediaUrl}
            onRemoveMediaUrl={form.handleRemoveMediaUrl}
            onMediaUrlChange={form.handleMediaUrlChange}
          />

          {/* Roll Tracking */}
          {form.isSparringType && (
            <RollTracker
              detailedMode={form.detailedMode}
              onToggleMode={() => form.setDetailedMode(prev => !prev)}
              rolls={form.rolls}
              partners={form.partners}
              simpleData={{
                rolls: form.sessionData.rolls,
                submissions_for: form.sessionData.submissions_for,
                submissions_against: form.sessionData.submissions_against,
                partners: form.sessionData.partners,
              }}
              onSimpleChange={(field, value) => form.setSessionData(prev => ({ ...prev, [field]: value }))}
              submissionSearchFor={form.submissionSearchFor}
              submissionSearchAgainst={form.submissionSearchAgainst}
              onSubmissionSearchForChange={(index, value) => form.setSubmissionSearchFor(prev => ({ ...prev, [index]: value }))}
              onSubmissionSearchAgainstChange={(index, value) => form.setSubmissionSearchAgainst(prev => ({ ...prev, [index]: value }))}
              filterSubmissions={form.filterSubmissions}
              onAddRoll={form.handleAddRoll}
              onRemoveRoll={form.handleRemoveRoll}
              onRollChange={form.handleRollChange}
              onToggleSubmission={form.handleToggleSubmission}
              topPartners={form.topPartners}
              selectedPartnerIds={form.selectedPartnerIds}
              onTogglePartner={form.handleTogglePartner}
            />
          )}

          {/* WHOOP Integration */}
          <WhoopIntegrationPanel
            whoopConnected={form.whoopConnected}
            whoopSyncing={form.whoopSyncing}
            whoopSynced={form.whoopSynced}
            whoopManualMode={form.whoopManualMode}
            showWhoop={form.showWhoop}
            classTime={form.sessionData.class_time}
            whoopData={{
              whoop_strain: form.sessionData.whoop_strain,
              whoop_calories: form.sessionData.whoop_calories,
              whoop_avg_hr: form.sessionData.whoop_avg_hr,
              whoop_max_hr: form.sessionData.whoop_max_hr,
            }}
            onWhoopDataChange={(field, value) => form.setSessionData(prev => ({ ...prev, [field]: value }))}
            onSync={form.handleWhoopSync}
            onClear={form.handleWhoopClear}
            onToggleManualMode={(manual) => { form.setWhoopManualMode(manual); if (manual) form.setShowWhoop(true); }}
            onToggleShow={() => form.setShowWhoop(prev => !prev)}
          />

          {/* Fight Dynamics */}
          {form.isSparringType && (
            <FightDynamicsPanel
              data={form.fightDynamics}
              expanded={form.showFightDynamics}
              onToggle={() => form.setShowFightDynamics(prev => !prev)}
              onIncrement={form.handleFightDynamicsIncrement}
              onDecrement={form.handleFightDynamicsDecrement}
              onChange={form.handleFightDynamicsChange}
            />
          )}

          {/* Photo Upload Info */}
          <p className="text-xs text-[var(--muted)]">You can add up to 3 photos after saving.</p>

          {/* Spacer so sticky bar doesn't obscure content on mobile */}
          <div className="pb-16 sm:pb-0" />

          {/* Submit — sticky on mobile */}
          <div className="sticky bottom-0 -mx-4 px-4 py-3 border-t border-[var(--border)] bg-[var(--surface)] sm:static sm:mx-0 sm:px-0 sm:py-0 sm:border-t-0">
            <div className="flex gap-2">
              <button type="button" onClick={handleBackStep} className="btn-secondary flex items-center gap-2">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button type="submit" disabled={loading} className="btn-primary flex-1">
                {loading ? 'Logging Session...' : 'Log Session'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* WHOOP Match Modal */}
      <WhoopMatchModal
        isOpen={form.showWhoopModal}
        onClose={() => form.setShowWhoopModal(false)}
        matches={form.whoopMatches}
        onSelect={form.handleWhoopMatchSelect}
        onManual={() => { form.setShowWhoopModal(false); form.setWhoopManualMode(true); form.setShowWhoop(true); }}
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
            <div className="grid grid-cols-3 gap-2" role="group" aria-label="Rest type options">
              {([
                { value: 'active', label: 'Active Recovery' },
                { value: 'full', label: 'Full Rest' },
                { value: 'injury', label: 'Injury / Rehab' },
                { value: 'sick', label: 'Sick Day' },
                { value: 'travel', label: 'Travelling' },
                { value: 'life', label: 'Life Got in the Way' },
              ] as const).map((type) => (
                <button key={type.value} type="button"
                  onClick={() => setRestData({ ...restData, rest_type: type.value })}
                  className="py-3 rounded-lg font-medium text-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2"
                  style={{
                    backgroundColor: restData.rest_type === type.value ? 'var(--accent)' : 'var(--surfaceElev)',
                    color: restData.rest_type === type.value ? '#FFFFFF' : 'var(--text)',
                    border: restData.rest_type === type.value ? 'none' : '1px solid var(--border)',
                  }}
                  aria-pressed={restData.rest_type === type.value}
                >
                  {type.label}
                </button>
              ))}
            </div>
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

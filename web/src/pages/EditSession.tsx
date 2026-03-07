import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { sessionsApi, friendsApi, socialApi, glossaryApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import { HH_MM_RE } from '../utils/validation';
import type { Friend, Movement, Session, SessionRoll, SessionTechnique } from '../types';
import { CheckCircle, ArrowLeft, Save, Loader, Trash2, Camera, Users2, X } from 'lucide-react';
import WhoopMatchModal from '../components/WhoopMatchModal';
import WhoopIntegrationPanel from '../components/sessions/WhoopIntegrationPanel';
import TechniqueTracker from '../components/sessions/TechniqueTracker';
import RollTracker from '../components/sessions/RollTracker';
import ClassTimePicker from '../components/sessions/ClassTimePicker';
import GymSelector from '../components/GymSelector';
import { ClassTypeChips, IntensityChips } from '../components/ui';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { useSessionForm, mergePartners, mapSocialFriends } from '../hooks/useSessionForm';
import { useDraftSaving } from '../hooks/useDraftSaving';

export default function EditSession() {
  usePageTitle('Edit Session');
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sessionId = Number(id);

  useEffect(() => {
    if (!id || isNaN(sessionId)) {
      navigate('/', { replace: true });
    }
  }, [id, sessionId, navigate]);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const toast = useToast();

  // Photo tracking
  const [photoCount, setPhotoCount] = useState(0);

  // Attendees / classmates
  const [attendees, setAttendees] = useState<string[]>([]);
  const [attendeeInput, setAttendeeInput] = useState('');

  // Multi-select intensity tags
  const [intensityTags, setIntensityTags] = useState<number[]>([]);

  const form = useSessionForm({
    whoopSyncParams: useCallback(() => ({
      session_id: parseInt(id!),
    }), [id]),
  });

  const { clearDraft } = useDraftSaving(`edit-session-${id}`, form.sessionData, form.setSessionData);

  useEffect(() => {
    const controller = new AbortController();
    const doLoad = async () => {
      setLoading(true);
      try {
        // Session data is critical; supporting data can fail gracefully
        const sessionRes = await sessionsApi.getWithRolls(parseInt(id!));
        const [instructorsRes, partnersRes, autocompleteRes, movementsRes, socialFriendsRes] = await Promise.all([
          friendsApi.listInstructors().catch(() => ({ data: [] })),
          friendsApi.listPartners().catch(() => ({ data: [] })),
          sessionsApi.getAutocomplete().catch(() => ({ data: {} })),
          glossaryApi.list().catch(() => ({ data: [] })),
          socialApi.getFriends().catch(() => ({ data: { friends: [] } })),
        ]);
        if (controller.signal.aborted) return;

        const sessionData = sessionRes.data;
        const iData = instructorsRes.data as Friend[] | { friends: Friend[] };
        const loadedInstructors: Friend[] = Array.isArray(iData) ? iData : iData?.friends || [];
        form.setInstructors(loadedInstructors);
        const pData = partnersRes.data as Friend[] | { friends: Friend[] };
        const manualPartners: Friend[] = Array.isArray(pData) ? pData : pData?.friends || [];
        const socialFriends = mapSocialFriends(socialFriendsRes.data?.friends || []);
        form.setPartners(mergePartners(manualPartners, loadedInstructors, socialFriends));
        form.setAutocomplete(autocompleteRes.data || {});
        const mData = movementsRes.data as Movement[] | { movements: Movement[] };
        form.setMovements(Array.isArray(mData) ? mData : mData?.movements || []);

        // Safely convert partners/techniques to comma string (may be array or string)
        const partnersStr = Array.isArray(sessionData.partners)
          ? sessionData.partners.join(', ')
          : (typeof sessionData.partners === 'string' ? sessionData.partners : '');
        const techniquesStr = Array.isArray(sessionData.techniques)
          ? sessionData.techniques.join(', ')
          : (typeof sessionData.techniques === 'string' ? sessionData.techniques : '');

        // Find instructor name for free text display
        const instructor = loadedInstructors.find(i => i.id === sessionData.instructor_id);
        const instructorName = instructor?.name || sessionData.instructor_name || '';

        // Populate form
        form.setSessionData({
          session_date: sessionData.session_date,
          class_time: sessionData.class_time || '',
          class_type: sessionData.class_type,
          gym_name: sessionData.gym_name,
          gym_id: null,
          location: sessionData.location || '',
          duration_mins: sessionData.duration_mins,
          intensity: sessionData.intensity,
          instructor_id: sessionData.instructor_id || null,
          instructor_name: instructorName,
          rolls: sessionData.rolls,
          submissions_for: sessionData.submissions_for,
          submissions_against: sessionData.submissions_against,
          partners: partnersStr,
          techniques: techniquesStr,
          notes: sessionData.notes || '',
          whoop_strain: sessionData.whoop_strain?.toString() || '',
          whoop_calories: sessionData.whoop_calories?.toString() || '',
          whoop_avg_hr: sessionData.whoop_avg_hr?.toString() || '',
          whoop_max_hr: sessionData.whoop_max_hr?.toString() || '',
        });

        // Load intensity tags if stored, otherwise initialize from single intensity value
        if (sessionData.intensity_tags && Array.isArray(sessionData.intensity_tags)) {
          setIntensityTags(sessionData.intensity_tags);
        } else if (sessionData.intensity) {
          setIntensityTags([sessionData.intensity]);
        }

        // Load attendees
        if (sessionData.attendees && Array.isArray(sessionData.attendees)) {
          setAttendees(sessionData.attendees);
        }

        // Check WHOOP connection status
        try {
          const whoopRes = await whoopApi.getStatus();
          if (!controller.signal.aborted) {
            form.setWhoopConnected(whoopRes.data.connected);
            if (sessionData.whoop_strain || sessionData.whoop_calories || sessionData.whoop_avg_hr || sessionData.whoop_max_hr) {
              form.setWhoopSynced(true);
            }
          }
        } catch (err) {
          logger.debug('WHOOP not available, keep manual mode', err);
        }

        // Load detailed_rolls if present
        if (sessionData.detailed_rolls && sessionData.detailed_rolls.length > 0) {
          form.setDetailedMode(true);
          form.setRolls(
            sessionData.detailed_rolls.map((roll: SessionRoll) => ({
              roll_number: roll.roll_number,
              partner_id: roll.partner_id || null,
              partner_name: roll.partner_name || '',
              duration_mins: roll.duration_mins || 5,
              intensity: Array.isArray(roll.intensity) ? roll.intensity : [],
              submissions_for: Array.isArray(roll.submissions_for) ? roll.submissions_for : [],
              submissions_against: Array.isArray(roll.submissions_against) ? roll.submissions_against : [],
              notes: roll.notes || '',
            }))
          );
        }

        // Load session_techniques if present
        if (sessionData.session_techniques && sessionData.session_techniques.length > 0) {
          form.setTechniques(
            sessionData.session_techniques.map((tech: SessionTechnique) => ({
              technique_number: tech.technique_number,
              movement_id: tech.movement_id,
              movement_name: tech.movement_name || '',
              notes: tech.notes || '',
              media_urls: Array.isArray(tech.media_urls) ? tech.media_urls : [],
            }))
          );
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          logger.error('Error loading session:', error);
          const msg = error instanceof Error ? error.message : 'Unknown error';
          setLoadError(`Failed to load session: ${msg}`);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    doLoad();
    return () => { controller.abort(); };
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const payload: Partial<Session> & Record<string, unknown> = {
        session_date: form.sessionData.session_date,
        class_time: form.sessionData.class_time && HH_MM_RE.test(form.sessionData.class_time) ? form.sessionData.class_time : undefined,
        class_type: form.sessionData.class_type,
        gym_name: form.sessionData.gym_name,
        location: form.sessionData.location || undefined,
        duration_mins: form.sessionData.duration_mins,
        intensity: intensityTags.length > 0 ? Math.max(...intensityTags) : form.sessionData.intensity,
        instructor_id: form.sessionData.instructor_id || undefined,
        instructor_name: form.sessionData.instructor_name || undefined,
        rolls: form.sessionData.rolls,
        submissions_for: form.sessionData.submissions_for,
        submissions_against: form.sessionData.submissions_against,
        partners: form.sessionData.partners ? form.sessionData.partners.split(',').map(p => p.trim()).filter(p => p !== '') : [],
        techniques: form.sessionData.techniques ? form.sessionData.techniques.split(',').map(t => t.trim()).filter(t => t !== '') : [],
        notes: form.sessionData.notes || undefined,
        attendees: attendees.length > 0 ? attendees : undefined,
        intensity_tags: intensityTags.length > 0 ? intensityTags : undefined,
        ...form.buildWhoopPayload(),
        needs_review: false,
      };

      // Add detailed rolls (send even if empty to clear old rolls)
      if (form.detailedMode) {
        const rollsPayload = form.buildRollsPayload();
        payload.session_rolls = rollsPayload.session_rolls || [];
        payload.rolls = rollsPayload.rolls ?? form.rolls.length;
        payload.submissions_for = rollsPayload.submissions_for ?? 0;
        payload.submissions_against = rollsPayload.submissions_against ?? 0;
      }

      // Add detailed techniques
      if (form.techniques.length > 0) {
        const techniquesPayload = form.buildTechniquesPayload();
        payload.session_techniques = techniquesPayload.session_techniques || [];
      } else {
        payload.session_techniques = [];
      }

      await sessionsApi.update(parseInt(id!), payload);
      clearDraft();
      setSuccess(true);
      setTimeout(() => navigate(`/session/${id}`), 1500);
    } catch (error) {
      logger.error('Error updating session:', error);
      toast.error('Failed to update session. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    setSaving(true);
    try {
      await sessionsApi.delete(parseInt(id!));
      toast.success('Session deleted successfully');
      navigate('/');
    } catch (error) {
      logger.error('Error deleting session:', error);
      toast.error('Failed to delete session. Please try again.');
      setSaving(false);
    }
  };

  // Build instructor name datalist
  const instructorNames = form.instructors.map(i => {
    const name = i.name ?? 'Unknown';
    return i.belt_rank
      ? `${name} (${i.belt_rank.charAt(0).toUpperCase() + i.belt_rank.slice(1)} belt)`
      : name;
  });

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <Loader className="w-8 h-8 text-[var(--accent)] animate-spin mx-auto mb-4" />
        <p className="text-[var(--muted)]">Loading session...</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <p className="text-red-500 mb-4">{loadError}</p>
        <div className="flex gap-2 justify-center">
          <button onClick={() => navigate(-1)} className="btn-secondary">
            Go Back
          </button>
          <button onClick={() => window.location.reload()} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Session Updated!</h2>
        <p className="text-[var(--muted)]">Redirecting to session...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate(`/session/${id}`)}
          className="text-[var(--muted)] hover:text-[var(--text)]"
          aria-label="Back to session"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-3xl font-bold" id="page-title">Edit Session</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        {/* Date */}
        <div>
          <label className="label" htmlFor="edit-session-date">Date</label>
          <input
            type="date"
            id="edit-session-date"
            className="input"
            value={form.sessionData.session_date}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, session_date: e.target.value }))}
            required
          />
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
          <ClassTypeChips
            value={form.sessionData.class_type}
            size="sm"
            onChange={(val) => form.setSessionData(prev => ({ ...prev, class_type: val }))}
          />
        </div>

        {/* WHOOP Stats — positioned high for visibility */}
        <WhoopIntegrationPanel
          whoopConnected={form.whoopConnected}
          whoopSyncing={form.whoopSyncing}
          whoopSynced={form.whoopSynced}
          whoopManualMode={form.whoopManualMode}
          showWhoop={true}
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
          onToggleManualMode={(manual) => form.setWhoopManualMode(manual)}
          onToggleShow={() => {}}
        />

        {/* Instructor — free text with suggestions */}
        <div>
          <label className="label" htmlFor="edit-session-instructor">Instructor (optional)</label>
          <input
            type="text"
            id="edit-session-instructor"
            className="input"
            value={form.sessionData.instructor_name}
            onChange={(e) => {
              const name = e.target.value;
              // Try to match to a known instructor for the ID
              const match = form.instructors.find(
                i => i.name?.toLowerCase() === name.toLowerCase()
              );
              form.setSessionData(prev => ({
                ...prev,
                instructor_name: name,
                instructor_id: match ? match.id : null,
              }));
            }}
            placeholder="Type instructor name..."
            list="instructor-suggestions"
          />
          <datalist id="instructor-suggestions">
            {instructorNames.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </div>

        {/* Gym Name */}
        <div>
          <label className="label">Gym</label>
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
              }));
            }}
          />
        </div>

        {/* Location */}
        <div>
          <label className="label" htmlFor="edit-session-location">Location (optional)</label>
          <input
            type="text"
            id="edit-session-location"
            className="input"
            value={form.sessionData.location}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, location: e.target.value }))}
            placeholder="e.g., Sydney, NSW"
            list="locations"
          />
          {form.autocomplete.locations && (
            <datalist id="locations">
              {form.autocomplete.locations.map((loc: string) => (
                <option key={loc} value={loc} />
              ))}
            </datalist>
          )}
        </div>

        {/* Duration & Intensity */}
        <div className="space-y-4">
          <div>
            <label className="label" htmlFor="edit-session-duration">Duration (mins)</label>
            <input
              type="number"
              id="edit-session-duration"
              className="input"
              value={form.sessionData.duration_mins}
              onChange={(e) => form.setSessionData(prev => ({ ...prev, duration_mins: parseInt(e.target.value) }))}
              min="1"
              required
            />
          </div>
          <div>
            <label className="label">Intensity (select all that apply)</label>
            <IntensityChips
              value={0}
              onChange={() => {}}
              multi
              selectedValues={intensityTags}
              onToggle={(val) => {
                setIntensityTags(prev =>
                  prev.includes(val)
                    ? prev.filter(v => v !== val)
                    : [...prev, val]
                );
              }}
              size="sm"
              showDescription
            />
          </div>
        </div>

        {/* Classmates / Who was in class? */}
        <div className="relative">
          <label className="label flex items-center gap-1.5">
            <Users2 className="w-4 h-4" />
            Who was in class?
          </label>
          {attendees.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {attendees.map((name, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
                  style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: '#3B82F6' }}
                >
                  {name}
                  <button
                    type="button"
                    onClick={() => setAttendees(prev => prev.filter((_, idx) => idx !== i))}
                    className="ml-0.5 hover:opacity-70"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          <input
            type="text"
            className="input text-sm"
            value={attendeeInput}
            onChange={(e) => setAttendeeInput(e.target.value)}
            onKeyDown={(e) => {
              if ((e.key === 'Enter' || e.key === ',') && attendeeInput.trim()) {
                e.preventDefault();
                const name = attendeeInput.trim().replace(/,+$/, '');
                if (name && !attendees.includes(name)) {
                  setAttendees(prev => [...prev, name]);
                }
                setAttendeeInput('');
              }
            }}
            onBlur={() => {
              // Delay to allow click on suggestion
              setTimeout(() => {
                const name = attendeeInput.trim().replace(/,+$/, '');
                if (name && !attendees.includes(name)) {
                  setAttendees(prev => [...prev, name]);
                }
                setAttendeeInput('');
              }, 200);
            }}
            placeholder="Type a name or pick from friends..."
          />
          {/* Friend suggestions dropdown */}
          {attendeeInput.trim().length >= 1 && (() => {
            const query = attendeeInput.trim().toLowerCase();
            const suggestions = form.partners
              .filter(p => p.name && p.name.toLowerCase().includes(query) && !attendees.includes(p.name))
              .slice(0, 6);
            if (suggestions.length === 0) return null;
            return (
              <div
                className="absolute left-0 right-0 mt-1 rounded-lg overflow-hidden shadow-lg z-10"
                style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
              >
                {suggestions.map((friend) => (
                  <button
                    key={friend.id}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--surfaceElev)] transition-colors"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      if (!attendees.includes(friend.name)) {
                        setAttendees(prev => [...prev, friend.name]);
                      }
                      setAttendeeInput('');
                    }}
                  >
                    <span className="font-medium text-[var(--text)]">{friend.name}</span>
                    {friend.belt_rank && (
                      <span className="text-xs text-[var(--muted)] ml-1.5">
                        ({friend.belt_rank} belt)
                      </span>
                    )}
                  </button>
                ))}
              </div>
            );
          })()}
          <p className="text-xs text-[var(--muted)] mt-1">Type to search friends, or enter any name and press Enter</p>
        </div>

        {/* Technique Focus — promoted above rolls */}
        <div className="border-t border-[var(--border)] pt-4">
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
        </div>

        {/* Session Details / Notes — promoted above rolls */}
        <div className={!form.isSparringType ? 'border-t border-[var(--border)] pt-4' : ''}>
          <label className="label" htmlFor="edit-session-notes">
            {!form.isSparringType ? 'Session Details' : 'Notes'}
            {!form.isSparringType && <span className="text-sm font-normal text-[var(--muted)] ml-2">(Workout details, exercises, distances, times, etc.)</span>}
          </label>
          <textarea
            id="edit-session-notes"
            className="input"
            value={form.sessionData.notes}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, notes: e.target.value }))}
            rows={!form.isSparringType ? 5 : 3}
            placeholder={
              !form.isSparringType
                ? "e.g., 5km run in 30 mins, Deadlifts 3x8 @ 100kg, Squats 3x10 @ 80kg, or Yoga flow focusing on hip mobility..."
                : "Any notes about this session..."
            }
          />
        </div>

        {/* Roll Tracking (Sparring only) — moved to bottom */}
        {form.isSparringType && (
          <div className="border-t border-[var(--border)] pt-4">
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
              onSimpleChange={(field, value) =>
                form.setSessionData(prev => ({ ...prev, [field]: value }))
              }
              submissionSearchFor={form.submissionSearchFor}
              submissionSearchAgainst={form.submissionSearchAgainst}
              onSubmissionSearchForChange={(index, value) => form.setSubmissionSearchFor(prev => ({ ...prev, [index]: value }))}
              onSubmissionSearchAgainstChange={(index, value) => form.setSubmissionSearchAgainst(prev => ({ ...prev, [index]: value }))}
              filterSubmissions={form.filterSubmissions}
              onAddRoll={form.handleAddRoll}
              onRemoveRoll={form.handleRemoveRoll}
              onRollChange={form.handleRollChange}
              onToggleSubmission={form.handleToggleSubmission}
            />
          </div>
        )}

        {/* Photos */}
        <div className="border-t border-[var(--border)] pt-6">
          <div className="flex items-center gap-2 mb-4">
            <Camera className="w-5 h-5 text-[var(--muted)]" />
            <h3 className="font-semibold text-lg">Photos</h3>
            <span className="text-sm text-[var(--muted)]">({photoCount}/3)</span>
          </div>

          <div className="space-y-4">
            <PhotoGallery
              activityType="session"
              activityId={parseInt(id!)}
              onPhotoCountChange={setPhotoCount}
            />

            <PhotoUpload
              activityType="session"
              activityId={parseInt(id!)}
              activityDate={form.sessionData.session_date}
              currentPhotoCount={photoCount}
              onUploadSuccess={() => {
                setPhotoCount(prev => prev + 1);
              }}
            />
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => navigate(`/session/${id}`)}
            className="btn-secondary flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Cancel
          </button>
          <button
            type="button"
            onClick={() => setShowDeleteConfirm(true)}
            disabled={saving}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            aria-label="Delete session"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
          <button
            type="submit"
            disabled={saving}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>

      <WhoopMatchModal
        isOpen={form.showWhoopModal}
        onClose={() => form.setShowWhoopModal(false)}
        matches={form.whoopMatches}
        onSelect={form.handleWhoopMatchSelect}
        onManual={() => { form.setShowWhoopModal(false); form.setWhoopManualMode(true); }}
      />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Session"
        message="Are you sure you want to delete this session? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { sessionsApi, friendsApi, socialApi, glossaryApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import { HH_MM_RE } from '../utils/validation';
import type { Friend, Movement, Session, SessionRoll, SessionTechnique } from '../types';
import { CheckCircle, ArrowLeft, Save, Loader, Trash2, Camera } from 'lucide-react';
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const toast = useToast();

  // Photo tracking
  const [photoCount, setPhotoCount] = useState(0);

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
        const [sessionRes, instructorsRes, partnersRes, autocompleteRes, movementsRes, socialFriendsRes] = await Promise.all([
          sessionsApi.getWithRolls(parseInt(id!)),
          friendsApi.listInstructors(),
          friendsApi.listPartners(),
          sessionsApi.getAutocomplete(),
          glossaryApi.list(),
          socialApi.getFriends().catch(() => ({ data: { friends: [] } })),
        ]);
        if (controller.signal.aborted) return;

        const sessionData = sessionRes.data;
        const iData = instructorsRes.data as Friend[] | { friends: Friend[] };
        const loadedInstructors: Friend[] = Array.isArray(iData) ? iData : iData?.friends || [];
        form.setInstructors(loadedInstructors);
        const pData = partnersRes.data as Friend[] | { friends: Friend[] };
        const manualPartners: Friend[] = Array.isArray(pData) ? pData : pData?.friends || [];
        const socialFriends = mapSocialFriends(socialFriendsRes.data.friends || []);
        form.setPartners(mergePartners(manualPartners, loadedInstructors, socialFriends));
        form.setAutocomplete(autocompleteRes.data);
        const mData = movementsRes.data as Movement[] | { movements: Movement[] };
        form.setMovements(Array.isArray(mData) ? mData : mData?.movements || []);

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
          instructor_name: '',
          rolls: sessionData.rolls,
          submissions_for: sessionData.submissions_for,
          submissions_against: sessionData.submissions_against,
          partners: sessionData.partners?.join(', ') || '',
          techniques: sessionData.techniques?.join(', ') || '',
          notes: sessionData.notes || '',
          whoop_strain: sessionData.whoop_strain?.toString() || '',
          whoop_calories: sessionData.whoop_calories?.toString() || '',
          whoop_avg_hr: sessionData.whoop_avg_hr?.toString() || '',
          whoop_max_hr: sessionData.whoop_max_hr?.toString() || '',
        });

        // Check WHOOP connection status
        try {
          const whoopRes = await whoopApi.getStatus();
          if (!controller.signal.aborted) {
            form.setWhoopConnected(whoopRes.data.connected);
            if (sessionData.whoop_strain || sessionData.whoop_calories || sessionData.whoop_avg_hr || sessionData.whoop_max_hr) {
              form.setWhoopSynced(true);
            }
          }
        } catch {
          // WHOOP not available, keep manual mode
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
          toast.error('Failed to load session. Redirecting to dashboard.');
          navigate('/');
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
        intensity: form.sessionData.intensity,
        instructor_id: form.sessionData.instructor_id || undefined,
        rolls: form.sessionData.rolls,
        submissions_for: form.sessionData.submissions_for,
        submissions_against: form.sessionData.submissions_against,
        partners: form.sessionData.partners ? form.sessionData.partners.split(',').map(p => p.trim()).filter(p => p !== '') : [],
        techniques: form.sessionData.techniques ? form.sessionData.techniques.split(',').map(t => t.trim()).filter(t => t !== '') : [],
        notes: form.sessionData.notes || undefined,
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
        // Explicitly set empty array to clear techniques if all removed
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

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <Loader className="w-8 h-8 text-[var(--accent)] animate-spin mx-auto mb-4" />
        <p className="text-[var(--muted)]">Loading session...</p>
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
          <label className="label">Date</label>
          <input
            type="date"
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

        {/* Instructor */}
        <div>
          <label className="label">Instructor (optional)</label>
          <select
            className="input"
            value={form.sessionData.instructor_id || ''}
            onChange={(e) => form.setSessionData(prev => ({
              ...prev,
              instructor_id: e.target.value ? parseInt(e.target.value) : null
            }))}
          >
            <option value="">Select instructor...</option>
            {form.instructors.map(instructor => (
              <option key={instructor.id} value={instructor.id}>
                {instructor.name}
                {instructor.belt_rank && ` (${instructor.belt_rank.charAt(0).toUpperCase() + instructor.belt_rank.slice(1)} belt)`}
              </option>
            ))}
          </select>
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
          <label className="label">Location (optional)</label>
          <input
            type="text"
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
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Duration (mins)</label>
            <input
              type="number"
              className="input"
              value={form.sessionData.duration_mins}
              onChange={(e) => form.setSessionData(prev => ({ ...prev, duration_mins: parseInt(e.target.value) }))}
              min="1"
              required
            />
          </div>
          <div>
            <label className="label">Intensity</label>
            <IntensityChips
              value={form.sessionData.intensity}
              size="sm"
              showDescription={false}
              onChange={(val) => form.setSessionData(prev => ({ ...prev, intensity: val }))}
            />
          </div>
        </div>

        {/* Roll Tracking (Sparring only) */}
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
          </div>
        )}

        {/* Technique Focus */}
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

        {/* Whoop Stats */}
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

        {/* Session Details / Notes */}
        <div className={!form.isSparringType ? 'border-t border-[var(--border)] pt-4' : ''}>
          <label className="label">
            {!form.isSparringType ? 'Session Details' : 'Notes'}
            {!form.isSparringType && <span className="text-sm font-normal text-[var(--muted)] ml-2">(Workout details, exercises, distances, times, etc.)</span>}
          </label>
          <textarea
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

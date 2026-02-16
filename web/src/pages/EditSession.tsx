import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { sessionsApi, friendsApi, socialApi, glossaryApi, whoopApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Friend, Movement, Session, SessionRoll, SessionTechnique } from '../types';
import { CheckCircle, ArrowLeft, Save, Loader, Plus, X, Search, Trash2, ToggleLeft, ToggleRight, Camera } from 'lucide-react';
import WhoopMatchModal from '../components/WhoopMatchModal';
import WhoopIntegrationPanel from '../components/sessions/WhoopIntegrationPanel';
import PhotoGallery from '../components/PhotoGallery';
import PhotoUpload from '../components/PhotoUpload';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { useSessionForm, mergePartners, mapSocialFriends } from '../hooks/useSessionForm';

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
        class_time: form.sessionData.class_time || undefined,
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
                onClick={() => form.setSessionData(prev => ({ ...prev, class_time: time.value }))}
                className="flex-1 min-h-[44px] py-2 rounded-lg font-medium text-sm transition-all"
                style={{
                  backgroundColor: form.sessionData.class_time === time.value ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: form.sessionData.class_time === time.value ? '#FFFFFF' : 'var(--text)',
                  border: form.sessionData.class_time === time.value ? 'none' : '1px solid var(--border)',
                }}
                aria-pressed={form.sessionData.class_time === time.value}
              >
                {time.label}
              </button>
            ))}
          </div>
          <input
            type="text"
            className="input text-sm"
            value={form.sessionData.class_time}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, class_time: e.target.value }))}
            placeholder="Or type custom time (e.g., 18:30, morning)"
          />
        </div>

        {/* Class Type */}
        <div>
          <label className="label">Class Type</label>
          <select
            className="input"
            value={form.sessionData.class_type}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, class_type: e.target.value }))}
            required
          >
            {CLASS_TYPES.map((type) => (
              <option key={type} value={type}>{CLASS_TYPE_LABELS[type] || type}</option>
            ))}
          </select>
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
                {instructor.belt_rank && ` (${instructor.belt_rank} belt)`}
              </option>
            ))}
          </select>
        </div>

        {/* Gym Name */}
        <div>
          <label className="label">Gym Name</label>
          <input
            type="text"
            className="input"
            value={form.sessionData.gym_name}
            onChange={(e) => form.setSessionData(prev => ({ ...prev, gym_name: e.target.value }))}
            list="gyms"
            required
          />
          {form.autocomplete.gyms && (
            <datalist id="gyms">
              {form.autocomplete.gyms.map((gym: string) => (
                <option key={gym} value={gym} />
              ))}
            </datalist>
          )}
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
            <label className="label">Intensity (1-5)</label>
            <input
              type="number"
              className="input"
              value={form.sessionData.intensity}
              onChange={(e) => form.setSessionData(prev => ({ ...prev, intensity: parseInt(e.target.value) }))}
              min="1"
              max="5"
              required
            />
          </div>
        </div>

        {/* Roll Tracking (Sparring only) */}
        {form.isSparringType && (
          <div className="border-t border-[var(--border)] pt-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">Roll Tracking</h3>
              <button
                type="button"
                onClick={() => form.setDetailedMode(prev => !prev)}
                className="flex items-center gap-2 text-sm text-[var(--accent)] hover:opacity-80"
              >
                {form.detailedMode ? (
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

            {!form.detailedMode ? (
              /* Simple Mode: Aggregate counts */
              <>
                <div>
                  <label className="label">Rolls</label>
                  <input
                    type="number"
                    className="input"
                    value={form.sessionData.rolls}
                    onChange={(e) => form.setSessionData(prev => ({ ...prev, rolls: parseInt(e.target.value) }))}
                    min="0"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Submissions For</label>
                    <input
                      type="number"
                      className="input"
                      value={form.sessionData.submissions_for}
                      onChange={(e) => form.setSessionData(prev => ({ ...prev, submissions_for: parseInt(e.target.value) }))}
                      min="0"
                    />
                  </div>
                  <div>
                    <label className="label">Submissions Against</label>
                    <input
                      type="number"
                      className="input"
                      value={form.sessionData.submissions_against}
                      onChange={(e) => form.setSessionData(prev => ({ ...prev, submissions_against: parseInt(e.target.value) }))}
                      min="0"
                    />
                  </div>
                </div>
              </>
            ) : (
              /* Detailed Mode: Individual roll records */
              <div className="space-y-3">
                {form.rolls.length === 0 ? (
                  <p className="text-sm text-[var(--muted)]">
                    Click "Add Roll" to track individual rolls with partners and submissions
                  </p>
                ) : (
                  form.rolls.map((roll, index) => (
                    <div key={index} className="border border-[var(--border)] rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold">Roll #{roll.roll_number}</h4>
                        <button
                          type="button"
                          onClick={() => form.handleRemoveRoll(index)}
                          className="text-red-600 hover:text-red-700"
                          aria-label={`Remove roll ${roll.roll_number}`}
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
                            const partner = form.partners.find(p => p.id === partnerId);
                            form.handleRollChange(index, 'partner_id', partnerId);
                            form.handleRollChange(index, 'partner_name', partner ? partner.name : '');
                          }}
                        >
                          <option value="">Select partner...</option>
                          {form.partners.map(partner => (
                            <option key={partner.id} value={partner.id}>
                              {partner.name}
                              {partner.belt_rank && ` (${partner.belt_rank} belt)`}
                            </option>
                          ))}
                        </select>
                        {!roll.partner_id && (
                          <input
                            type="text"
                            className="input mt-2 text-sm"
                            placeholder="Or enter partner name"
                            value={roll.partner_name}
                            onChange={(e) => form.handleRollChange(index, 'partner_name', e.target.value)}
                          />
                        )}
                      </div>

                      {/* Duration */}
                      <div>
                        <label className="label text-sm">Duration (mins)</label>
                        <input
                          type="number"
                          className="input"
                          value={roll.duration_mins}
                          onChange={(e) => form.handleRollChange(index, 'duration_mins', parseInt(e.target.value) || 0)}
                          min="0"
                        />
                      </div>

                      {/* Submissions For */}
                      <div>
                        <label className="label text-sm">Submissions For ({roll.submissions_for.length})</label>
                        <div className="relative mb-2">
                          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                          <input
                            type="text"
                            className="input pl-8 text-sm"
                            placeholder="Search submissions..."
                            value={form.submissionSearchFor[index] || ''}
                            onChange={(e) => form.setSubmissionSearchFor(prev => ({ ...prev, [index]: e.target.value }))}
                          />
                        </div>
                        <div className="max-h-32 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1 mb-2">
                          {form.movements
                            .filter(m => {
                              const search = form.submissionSearchFor[index]?.toLowerCase() || '';
                              return (m.name.toLowerCase().includes(search) ||
                                     m.category?.toLowerCase().includes(search)) &&
                                     m.category === 'submission';
                            })
                            .slice(0, 10)
                            .map(movement => (
                              <button
                                key={movement.id}
                                type="button"
                                onClick={() => form.handleToggleSubmission(index, movement.id, 'for')}
                                className="w-full text-left px-2 py-1 rounded text-sm hover:bg-[var(--surfaceElev)]"
                                disabled={roll.submissions_for.includes(movement.id)}
                              >
                                {movement.name} {roll.submissions_for.includes(movement.id) && '\u2713'}
                              </button>
                            ))}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {roll.submissions_for.map(movementId => {
                            const movement = form.movements.find(m => m.id === movementId);
                            return movement ? (
                              <span
                                key={movementId}
                                className="text-xs px-2 py-1 rounded flex items-center gap-1"
                                style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: 'var(--success)' }}
                              >
                                {movement.name}
                                <button
                                  type="button"
                                  onClick={() => form.handleToggleSubmission(index, movementId, 'for')}
                                  className="hover:text-red-600"
                                  aria-label={`Remove ${movement.name} submission`}
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </span>
                            ) : null;
                          })}
                        </div>
                      </div>

                      {/* Submissions Against */}
                      <div>
                        <label className="label text-sm">Submissions Against ({roll.submissions_against.length})</label>
                        <div className="relative mb-2">
                          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                          <input
                            type="text"
                            className="input pl-8 text-sm"
                            placeholder="Search submissions..."
                            value={form.submissionSearchAgainst[index] || ''}
                            onChange={(e) => form.setSubmissionSearchAgainst(prev => ({ ...prev, [index]: e.target.value }))}
                          />
                        </div>
                        <div className="max-h-32 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1 mb-2">
                          {form.movements
                            .filter(m => {
                              const search = form.submissionSearchAgainst[index]?.toLowerCase() || '';
                              return (m.name.toLowerCase().includes(search) ||
                                     m.category?.toLowerCase().includes(search)) &&
                                     m.category === 'submission';
                            })
                            .slice(0, 10)
                            .map(movement => (
                              <button
                                key={movement.id}
                                type="button"
                                onClick={() => form.handleToggleSubmission(index, movement.id, 'against')}
                                className="w-full text-left px-2 py-1 rounded text-sm hover:bg-[var(--surfaceElev)]"
                                disabled={roll.submissions_against.includes(movement.id)}
                              >
                                {movement.name} {roll.submissions_against.includes(movement.id) && '\u2713'}
                              </button>
                            ))}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {roll.submissions_against.map(movementId => {
                            const movement = form.movements.find(m => m.id === movementId);
                            return movement ? (
                              <span
                                key={movementId}
                                className="text-xs px-2 py-1 rounded flex items-center gap-1"
                                style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)' }}
                              >
                                {movement.name}
                                <button
                                  type="button"
                                  onClick={() => form.handleToggleSubmission(index, movementId, 'against')}
                                  className="hover:text-red-600"
                                  aria-label={`Remove ${movement.name} submission against`}
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </span>
                            ) : null;
                          })}
                        </div>
                      </div>

                      {/* Notes */}
                      <div>
                        <label className="label text-sm">Notes</label>
                        <textarea
                          className="input resize-none text-sm"
                          rows={2}
                          value={roll.notes}
                          onChange={(e) => form.handleRollChange(index, 'notes', e.target.value)}
                          placeholder="Key moments, positions, what worked/didn't work..."
                        />
                      </div>
                    </div>
                  ))
                )}
                <button
                  type="button"
                  onClick={form.handleAddRoll}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Roll
                </button>
              </div>
            )}
          </div>
        )}

        {/* Technique Focus */}
        <div className="space-y-4 border-t border-[var(--border)] pt-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">Technique of the Day</h3>
            <button
              type="button"
              onClick={form.handleAddTechnique}
              className="flex items-center gap-2 px-3 py-1 bg-[var(--accent)] text-white rounded-md hover:opacity-90 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Technique
            </button>
          </div>

          {form.techniques.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              Click "Add Technique" to track techniques you focused on
            </p>
          ) : (
            <div className="space-y-4">
              {form.techniques.map((tech, index) => (
                <div key={index} className="border border-[var(--border)] rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Technique #{tech.technique_number}</h4>
                    <button
                      type="button"
                      onClick={() => form.handleRemoveTechnique(index)}
                      className="text-red-600 hover:text-red-700"
                      aria-label={`Remove technique ${tech.technique_number}`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Movement Selection */}
                  <div>
                    <label className="label text-sm">Movement</label>
                    <div className="relative mb-2">
                      <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                      <input
                        type="text"
                        className="input pl-8 text-sm"
                        placeholder="Search movements..."
                        value={form.techniqueSearch[index] || ''}
                        onChange={(e) => form.setTechniqueSearch(prev => ({ ...prev, [index]: e.target.value }))}
                      />
                    </div>
                    <div className="max-h-48 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1">
                      {form.filterMovements(form.techniqueSearch[index] || '')
                        .map(movement => (
                          <button
                            key={movement.id}
                            type="button"
                            onClick={() => form.handleSelectMovement(index, movement.id, movement.name)}
                            className={`w-full text-left px-2 py-1 rounded text-sm ${
                              tech.movement_id === movement.id
                                ? 'bg-[var(--accent)] text-white'
                                : 'hover:bg-[var(--surfaceElev)]'
                            }`}
                          >
                            <span className="font-medium">{movement.name}</span>
                            <span className="text-xs ml-2 opacity-75">
                              {movement.category}
                              {movement.subcategory && ` - ${movement.subcategory}`}
                            </span>
                          </button>
                        ))}
                      {form.filterMovements(form.techniqueSearch[index] || '').length === 0 && (
                        <p className="text-xs text-[var(--muted)] text-center py-2">No movements found</p>
                      )}
                    </div>
                    {tech.movement_id && (
                      <p className="text-sm text-[var(--muted)] mt-1">
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
                      onChange={(e) => form.handleTechniqueChange(index, 'notes', e.target.value)}
                      placeholder="What did you learn? Key details, insights, or observations..."
                    />
                  </div>

                  {/* Media URLs */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="label text-sm mb-0">Reference Media</label>
                      <button
                        type="button"
                        onClick={() => form.handleAddMediaUrl(index)}
                        className="text-xs text-[var(--accent)] hover:opacity-80 flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" />
                        Add Link
                      </button>
                    </div>
                    {tech.media_urls.length === 0 ? (
                      <p className="text-xs text-[var(--muted)]">No media links added</p>
                    ) : (
                      <div className="space-y-2">
                        {tech.media_urls.map((media, mediaIndex) => (
                          <div key={mediaIndex} className="border border-[var(--border)] rounded p-2 space-y-2">
                            <div className="flex items-center justify-between">
                              <select
                                className="input-sm text-xs"
                                value={media.type}
                                onChange={(e) => form.handleMediaUrlChange(index, mediaIndex, 'type', e.target.value as 'video' | 'image')}
                              >
                                <option value="video">Video</option>
                                <option value="image">Image</option>
                              </select>
                              <button
                                type="button"
                                onClick={() => form.handleRemoveMediaUrl(index, mediaIndex)}
                                className="text-red-600 hover:text-red-700"
                                aria-label="Remove media URL"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                            <input
                              type="text"
                              className="input text-xs"
                              placeholder="URL (YouTube, Instagram, etc.)"
                              value={media.url}
                              onChange={(e) => form.handleMediaUrlChange(index, mediaIndex, 'url', e.target.value)}
                            />
                            <input
                              type="text"
                              className="input text-xs"
                              placeholder="Title (optional)"
                              value={media.title || ''}
                              onChange={(e) => form.handleMediaUrlChange(index, mediaIndex, 'title', e.target.value)}
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

        {/* Partners (Simple mode sparring only) */}
        {!form.detailedMode && form.isSparringType && (
          <div>
            <label className="label">Partners (comma-separated)</label>
            <input
              type="text"
              className="input"
              value={form.sessionData.partners}
              onChange={(e) => form.setSessionData(prev => ({ ...prev, partners: e.target.value }))}
              placeholder="e.g., John, Sarah"
            />
          </div>
        )}

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

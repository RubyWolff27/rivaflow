import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { sessionsApi, contactsApi, glossaryApi } from '../api/client';
import type { Contact, Movement, Session } from '../types';
import { CheckCircle, ArrowLeft, Save, Loader } from 'lucide-react';

const CLASS_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat', 's&c', 'mobility', 'yoga', 'rehab', 'physio', 'drilling'];
const SPARRING_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat'];

export default function EditSession() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [session, setSession] = useState<Session | null>(null);

  const [instructors, setInstructors] = useState<Contact[]>([]);
  const [autocomplete, setAutocomplete] = useState<any>({});

  // Form data
  const [formData, setFormData] = useState({
    session_date: '',
    class_type: 'gi',
    gym_name: '',
    location: '',
    duration_mins: 60,
    intensity: 4,
    instructor_id: null as number | null,
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

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessionRes, instructorsRes, autocompleteRes] = await Promise.all([
        sessionsApi.getById(parseInt(id!)),
        contactsApi.listInstructors(),
        sessionsApi.getAutocomplete(),
      ]);

      const sessionData = sessionRes.data;
      setSession(sessionData);
      setInstructors(instructorsRes.data);
      setAutocomplete(autocompleteRes.data);

      // Populate form
      setFormData({
        session_date: sessionData.session_date,
        class_type: sessionData.class_type,
        gym_name: sessionData.gym_name,
        location: sessionData.location || '',
        duration_mins: sessionData.duration_mins,
        intensity: sessionData.intensity,
        instructor_id: sessionData.instructor_id || null,
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
    } catch (error) {
      console.error('Error loading session:', error);
      alert('Failed to load session. Redirecting to dashboard.');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const payload: any = {
        session_date: formData.session_date,
        class_type: formData.class_type,
        gym_name: formData.gym_name,
        location: formData.location || undefined,
        duration_mins: formData.duration_mins,
        intensity: formData.intensity,
        instructor_id: formData.instructor_id || undefined,
        rolls: formData.rolls,
        submissions_for: formData.submissions_for,
        submissions_against: formData.submissions_against,
        partners: formData.partners ? formData.partners.split(',').map(p => p.trim()) : undefined,
        techniques: formData.techniques ? formData.techniques.split(',').map(t => t.trim()) : undefined,
        notes: formData.notes || undefined,
        whoop_strain: formData.whoop_strain ? parseFloat(formData.whoop_strain) : undefined,
        whoop_calories: formData.whoop_calories ? parseInt(formData.whoop_calories) : undefined,
        whoop_avg_hr: formData.whoop_avg_hr ? parseInt(formData.whoop_avg_hr) : undefined,
        whoop_max_hr: formData.whoop_max_hr ? parseInt(formData.whoop_max_hr) : undefined,
      };

      await sessionsApi.update(parseInt(id!), payload);
      setSuccess(true);
      setTimeout(() => navigate('/'), 1500);
    } catch (error) {
      console.error('Error updating session:', error);
      alert('Failed to update session. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const isSparringType = SPARRING_TYPES.includes(formData.class_type);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <Loader className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">Loading session...</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Session Updated!</h2>
        <p className="text-gray-600 dark:text-gray-400">Redirecting to dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => navigate('/')}
          className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-3xl font-bold">Edit Session</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        {/* Date */}
        <div>
          <label className="label">Date</label>
          <input
            type="date"
            className="input"
            value={formData.session_date}
            onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
            required
          />
        </div>

        {/* Class Type */}
        <div>
          <label className="label">Class Type</label>
          <select
            className="input"
            value={formData.class_type}
            onChange={(e) => setFormData({ ...formData, class_type: e.target.value })}
            required
          >
            {CLASS_TYPES.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        {/* Instructor */}
        <div>
          <label className="label">Instructor (optional)</label>
          <select
            className="input"
            value={formData.instructor_id || ''}
            onChange={(e) => setFormData({
              ...formData,
              instructor_id: e.target.value ? parseInt(e.target.value) : null
            })}
          >
            <option value="">Select instructor...</option>
            {instructors.map(instructor => (
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
            value={formData.gym_name}
            onChange={(e) => setFormData({ ...formData, gym_name: e.target.value })}
            list="gyms"
            required
          />
          {autocomplete.gyms && (
            <datalist id="gyms">
              {autocomplete.gyms.map((gym: string) => (
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
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
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

        {/* Duration & Intensity */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Duration (mins)</label>
            <input
              type="number"
              className="input"
              value={formData.duration_mins}
              onChange={(e) => setFormData({ ...formData, duration_mins: parseInt(e.target.value) })}
              min="1"
              required
            />
          </div>
          <div>
            <label className="label">Intensity (1-5)</label>
            <input
              type="number"
              className="input"
              value={formData.intensity}
              onChange={(e) => setFormData({ ...formData, intensity: parseInt(e.target.value) })}
              min="1"
              max="5"
              required
            />
          </div>
        </div>

        {/* Sparring Details */}
        {isSparringType && (
          <>
            <div>
              <label className="label">Rolls</label>
              <input
                type="number"
                className="input"
                value={formData.rolls}
                onChange={(e) => setFormData({ ...formData, rolls: parseInt(e.target.value) })}
                min="0"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Submissions For</label>
                <input
                  type="number"
                  className="input"
                  value={formData.submissions_for}
                  onChange={(e) => setFormData({ ...formData, submissions_for: parseInt(e.target.value) })}
                  min="0"
                />
              </div>
              <div>
                <label className="label">Submissions Against</label>
                <input
                  type="number"
                  className="input"
                  value={formData.submissions_against}
                  onChange={(e) => setFormData({ ...formData, submissions_against: parseInt(e.target.value) })}
                  min="0"
                />
              </div>
            </div>
          </>
        )}

        {/* Techniques */}
        <div>
          <label className="label">Techniques (comma-separated)</label>
          <input
            type="text"
            className="input"
            value={formData.techniques}
            onChange={(e) => setFormData({ ...formData, techniques: e.target.value })}
            placeholder="e.g., armbar, triangle, guard pass"
          />
        </div>

        {/* Partners */}
        <div>
          <label className="label">Partners (comma-separated)</label>
          <input
            type="text"
            className="input"
            value={formData.partners}
            onChange={(e) => setFormData({ ...formData, partners: e.target.value })}
            placeholder="e.g., John, Sarah"
          />
        </div>

        {/* Whoop Stats (Optional) */}
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-3">Whoop Stats (optional)</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Activity Strain</label>
              <input
                type="number"
                className="input"
                value={formData.whoop_strain}
                onChange={(e) => setFormData({ ...formData, whoop_strain: e.target.value })}
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
                value={formData.whoop_calories}
                onChange={(e) => setFormData({ ...formData, whoop_calories: e.target.value })}
                placeholder="e.g., 500"
                min="0"
              />
            </div>
            <div>
              <label className="label">Avg HR (bpm)</label>
              <input
                type="number"
                className="input"
                value={formData.whoop_avg_hr}
                onChange={(e) => setFormData({ ...formData, whoop_avg_hr: e.target.value })}
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
                value={formData.whoop_max_hr}
                onChange={(e) => setFormData({ ...formData, whoop_max_hr: e.target.value })}
                placeholder="e.g., 185"
                min="0"
                max="250"
              />
            </div>
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="label">Notes</label>
          <textarea
            className="input"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            placeholder="Any notes about this session..."
          />
        </div>

        {/* Submit */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Cancel
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
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi } from '../api/client';
import { CheckCircle } from 'lucide-react';

const CLASS_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat', 's&c', 'mobility', 'yoga', 'rehab', 'physio', 'drilling'];
const SPARRING_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat'];

export default function LogSession() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [autocomplete, setAutocomplete] = useState<any>({});

  const [formData, setFormData] = useState({
    session_date: new Date().toISOString().split('T')[0],
    class_type: 'gi',
    gym_name: '',
    location: '',
    duration_mins: 60,
    intensity: 4,
    rolls: 0,
    submissions_for: 0,
    submissions_against: 0,
    partners: '',
    techniques: '',
    notes: '',
  });

  useEffect(() => {
    loadAutocomplete();
  }, []);

  const loadAutocomplete = async () => {
    try {
      const res = await sessionsApi.getAutocomplete();
      setAutocomplete(res.data);
    } catch (error) {
      console.error('Error loading autocomplete:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        partners: formData.partners ? formData.partners.split(',').map(p => p.trim()) : undefined,
        techniques: formData.techniques ? formData.techniques.split(',').map(t => t.trim()) : undefined,
        visibility_level: 'private',
      };

      await sessionsApi.create(payload);
      setSuccess(true);
      setTimeout(() => navigate('/'), 1500);
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Failed to log session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const isSparringType = SPARRING_TYPES.includes(formData.class_type);

  if (success) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Session Logged!</h2>
        <p className="text-gray-600 dark:text-gray-400">Redirecting to dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Log Training Session</h1>

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

        {/* Gym Name */}
        <div>
          <label className="label">Gym Name</label>
          <input
            type="text"
            className="input"
            value={formData.gym_name}
            onChange={(e) => setFormData({ ...formData, gym_name: e.target.value })}
            placeholder="e.g., Gracie Barra Sydney"
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

        {/* Notes */}
        <div>
          <label className="label">Notes</label>
          <textarea
            className="input"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            placeholder="Any notes about today's training..."
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full"
        >
          {loading ? 'Logging Session...' : 'Log Session'}
        </button>
      </form>
    </div>
  );
}

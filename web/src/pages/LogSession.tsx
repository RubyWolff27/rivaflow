import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi, readinessApi, profileApi } from '../api/client';
import { CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';

const CLASS_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat', 's&c', 'mobility', 'yoga', 'rehab', 'physio', 'drilling'];
const SPARRING_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat'];

export default function LogSession() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1 = Readiness, 2 = Session
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [autocomplete, setAutocomplete] = useState<any>({});
  const [defaultGym, setDefaultGym] = useState('');

  // Readiness data (Step 1)
  const [readinessData, setReadinessData] = useState({
    check_date: new Date().toISOString().split('T')[0],
    sleep: 3,
    stress: 3,
    soreness: 2,
    energy: 3,
    hotspot_note: '',
  });

  // Session data (Step 2)
  const [sessionData, setSessionData] = useState({
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
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [autocompleteRes, profileRes] = await Promise.all([
        sessionsApi.getAutocomplete(),
        profileApi.get(),
      ]);
      setAutocomplete(autocompleteRes.data);

      if (profileRes.data.default_gym) {
        setDefaultGym(profileRes.data.default_gym);
        setSessionData(prev => ({ ...prev, gym_name: profileRes.data.default_gym || '' }));
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleNextStep = () => {
    // Validate step 1
    if (step === 1) {
      setStep(2);
    }
  };

  const handleBackStep = () => {
    setStep(1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Save readiness first
      await readinessApi.create(readinessData);

      // Then save session
      const payload = {
        ...sessionData,
        partners: sessionData.partners ? sessionData.partners.split(',').map(p => p.trim()) : undefined,
        techniques: sessionData.techniques ? sessionData.techniques.split(',').map(t => t.trim()) : undefined,
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

  const compositeScore = readinessData.sleep + (6 - readinessData.stress) + (6 - readinessData.soreness) + readinessData.energy;
  const isSparringType = SPARRING_TYPES.includes(sessionData.class_type);

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
      {/* Progress Indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 1 ? 'bg-primary-600 text-white' : 'bg-green-500 text-white'}`}>
            1
          </div>
          <div className="w-16 h-1 bg-gray-300 dark:bg-gray-600"></div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 2 ? 'bg-primary-600 text-white' : 'bg-gray-300 dark:bg-gray-600 text-gray-600'}`}>
            2
          </div>
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={step === 1 ? 'font-semibold' : 'text-gray-500'}>Readiness Check</span>
          <span className={step === 2 ? 'font-semibold' : 'text-gray-500'}>Session Details</span>
        </div>
      </div>

      <h1 className="text-3xl font-bold mb-6">
        {step === 1 ? 'How Are You Feeling?' : 'Log Training Session'}
      </h1>

      {/* Step 1: Readiness */}
      {step === 1 && (
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

          <button onClick={handleNextStep} className="btn-primary w-full flex items-center justify-center gap-2">
            Continue to Session Details
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Step 2: Session */}
      {step === 2 && (
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
              value={sessionData.gym_name}
              onChange={(e) => setSessionData({ ...sessionData, gym_name: e.target.value })}
              placeholder={defaultGym || "e.g., Gracie Barra Sydney"}
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

          {/* Duration & Intensity */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Duration (mins)</label>
              <input
                type="number"
                className="input"
                value={sessionData.duration_mins}
                onChange={(e) => setSessionData({ ...sessionData, duration_mins: parseInt(e.target.value) })}
                min="1"
                required
              />
            </div>
            <div>
              <label className="label">Intensity (1-5)</label>
              <input
                type="number"
                className="input"
                value={sessionData.intensity}
                onChange={(e) => setSessionData({ ...sessionData, intensity: parseInt(e.target.value) })}
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
          )}

          {/* Techniques */}
          <div>
            <label className="label">Techniques (comma-separated)</label>
            <input
              type="text"
              className="input"
              value={sessionData.techniques}
              onChange={(e) => setSessionData({ ...sessionData, techniques: e.target.value })}
              placeholder="e.g., armbar, triangle, guard pass"
            />
          </div>

          {/* Partners */}
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

          {/* Notes */}
          <div>
            <label className="label">Notes</label>
            <textarea
              className="input"
              value={sessionData.notes}
              onChange={(e) => setSessionData({ ...sessionData, notes: e.target.value })}
              rows={3}
              placeholder="Any notes about today's training..."
            />
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
    </div>
  );
}

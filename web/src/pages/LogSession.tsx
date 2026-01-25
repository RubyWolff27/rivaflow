import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi, readinessApi, profileApi, contactsApi, glossaryApi } from '../api/client';
import type { Contact, Movement } from '../types';
import { CheckCircle, ArrowRight, ArrowLeft, Plus, X, ToggleLeft, ToggleRight } from 'lucide-react';

const CLASS_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat', 's&c', 'mobility', 'yoga', 'rehab', 'physio', 'drilling'];
const SPARRING_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat'];

interface RollEntry {
  roll_number: number;
  partner_id: number | null;
  partner_name: string;
  duration_mins: number;
  submissions_for: number[];
  submissions_against: number[];
  notes: string;
}

export default function LogSession() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1 = Readiness, 2 = Session
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [autocomplete, setAutocomplete] = useState<any>({});
  const [defaultGym, setDefaultGym] = useState('');

  // New: Contacts and glossary data
  const [instructors, setInstructors] = useState<Contact[]>([]);
  const [partners, setPartners] = useState<Contact[]>([]);
  const [movements, setMovements] = useState<Movement[]>([]);

  // New: Roll tracking mode
  const [detailedMode, setDetailedMode] = useState(false);
  const [rolls, setRolls] = useState<RollEntry[]>([]);

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
    instructor_id: null as number | null,
    instructor_name: '',
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
      const [autocompleteRes, profileRes, instructorsRes, partnersRes, movementsRes] = await Promise.all([
        sessionsApi.getAutocomplete(),
        profileApi.get(),
        contactsApi.listInstructors(),
        contactsApi.listPartners(),
        glossaryApi.list(),
      ]);

      setAutocomplete(autocompleteRes.data);
      setInstructors(instructorsRes.data);
      setPartners(partnersRes.data);
      setMovements(movementsRes.data);

      if (profileRes.data.default_gym) {
        setDefaultGym(profileRes.data.default_gym);
        setSessionData(prev => ({ ...prev, gym_name: profileRes.data.default_gym || '' }));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Save readiness first
      await readinessApi.create(readinessData);

      // Build session payload
      const payload: any = {
        ...sessionData,
        partners: sessionData.partners ? sessionData.partners.split(',').map(p => p.trim()) : undefined,
        techniques: sessionData.techniques ? sessionData.techniques.split(',').map(t => t.trim()) : undefined,
        visibility_level: 'private',
      };

      // Add instructor
      if (sessionData.instructor_id) {
        payload.instructor_id = sessionData.instructor_id;
        const instructor = instructors.find(i => i.id === sessionData.instructor_id);
        if (instructor) {
          payload.instructor_name = instructor.name;
        }
      } else if (sessionData.instructor_name) {
        payload.instructor_name = sessionData.instructor_name;
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

          {/* Instructor */}
          <div>
            <label className="label">Instructor (optional)</label>
            <select
              className="input"
              value={sessionData.instructor_id || ''}
              onChange={(e) => setSessionData({
                ...sessionData,
                instructor_id: e.target.value ? parseInt(e.target.value) : null
              })}
            >
              <option value="">Select instructor...</option>
              {instructors.map(instructor => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name}
                  {instructor.belt_rank && ` (${instructor.belt_rank} belt)`}
                  {instructor.instructor_certification && ` - ${instructor.instructor_certification}`}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Don't see your instructor? <a href="/contacts" className="text-primary-600 hover:underline">Add them in Contacts</a>
            </p>
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
                              {partner.name}
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
                        <div className="max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2 space-y-1">
                          {movements.filter(m => m.category === 'submission').map(movement => (
                            <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-1 rounded">
                              <input
                                type="checkbox"
                                checked={roll.submissions_for.includes(movement.id)}
                                onChange={() => handleToggleSubmission(index, movement.id, 'for')}
                                className="w-4 h-4"
                              />
                              <span>{movement.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Submissions Against */}
                      <div>
                        <label className="label text-sm">Submissions They Got</label>
                        <div className="max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2 space-y-1">
                          {movements.filter(m => m.category === 'submission').map(movement => (
                            <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-1 rounded">
                              <input
                                type="checkbox"
                                checked={roll.submissions_against.includes(movement.id)}
                                onChange={() => handleToggleSubmission(index, movement.id, 'against')}
                                className="w-4 h-4"
                              />
                              <span>{movement.name}</span>
                            </label>
                          ))}
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

          {/* Partners (Simple mode or non-sparring) */}
          {!detailedMode && (
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

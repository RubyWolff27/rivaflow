import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { sessionsApi, contactsApi, glossaryApi } from '../api/client';
import type { Contact, Movement, MediaUrl } from '../types';
import { CheckCircle, ArrowLeft, Save, Loader, Plus, X, Search } from 'lucide-react';

const CLASS_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat', 's&c', 'mobility', 'yoga', 'rehab', 'physio', 'drilling', 'cardio'];
const SPARRING_TYPES = ['gi', 'no-gi', 'wrestling', 'judo', 'open-mat'];

interface TechniqueEntry {
  technique_number: number;
  movement_id: number | null;
  movement_name: string;
  notes: string;
  media_urls: MediaUrl[];
}

export default function EditSession() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const [instructors, setInstructors] = useState<Contact[]>([]);
  const [autocomplete, setAutocomplete] = useState<any>({});
  const [movements, setMovements] = useState<Movement[]>([]);

  // Technique tracking
  const [techniques, setTechniques] = useState<TechniqueEntry[]>([]);
  const [techniqueSearch, setTechniqueSearch] = useState<{[techIndex: number]: string}>({});

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
      const [sessionRes, instructorsRes, autocompleteRes, movementsRes] = await Promise.all([
        sessionsApi.getById(parseInt(id!)),
        contactsApi.listInstructors(),
        sessionsApi.getAutocomplete(),
        glossaryApi.list(),
      ]);

      const sessionData = sessionRes.data;
      setInstructors(instructorsRes.data);
      setAutocomplete(autocompleteRes.data);
      setMovements(movementsRes.data);

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

      // Load session_techniques if present
      if (sessionData.session_techniques && sessionData.session_techniques.length > 0) {
        setTechniques(
          sessionData.session_techniques.map((tech: any) => ({
            technique_number: tech.technique_number,
            movement_id: tech.movement_id,
            movement_name: tech.movement_name || '',
            notes: tech.notes || '',
            media_urls: tech.media_urls || [],
          }))
        );
      }
    } catch (error) {
      console.error('Error loading session:', error);
      alert('Failed to load session. Redirecting to dashboard.');
      navigate('/');
    } finally {
      setLoading(false);
    }
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
    updated.forEach((tech, i) => {
      tech.technique_number = i + 1;
    });
    setTechniques(updated);

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

      // Add detailed techniques
      if (techniques.length > 0) {
        payload.session_techniques = techniques
          .filter(tech => tech.movement_id !== null)
          .map(tech => ({
            movement_id: tech.movement_id!,
            technique_number: tech.technique_number,
            notes: tech.notes || undefined,
            media_urls: tech.media_urls.length > 0 ? tech.media_urls.filter(m => m.url) : undefined,
          }));
      } else {
        // Explicitly set empty array to clear techniques if all removed
        payload.session_techniques = [];
      }

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

        {/* Technique Focus */}
        <div className="space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-lg">Technique of the Day</h3>
            <button
              type="button"
              onClick={handleAddTechnique}
              className="flex items-center gap-2 px-3 py-1 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Technique
            </button>
          </div>

          {techniques.length === 0 ? (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Click "Add Technique" to track techniques you focused on
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
                          const search = techniqueSearch[index]?.toLowerCase() || '';
                          return m.name.toLowerCase().includes(search) ||
                                 m.category?.toLowerCase().includes(search) ||
                                 m.subcategory?.toLowerCase().includes(search) ||
                                 m.aliases.some(alias => alias.toLowerCase().includes(search));
                        })
                        .map(movement => (
                          <button
                            key={movement.id}
                            type="button"
                            onClick={() => {
                              handleTechniqueChange(index, 'movement_id', movement.id);
                              handleTechniqueChange(index, 'movement_name', movement.name);
                            }}
                            className={`w-full text-left px-2 py-1 rounded text-sm ${
                              tech.movement_id === movement.id
                                ? 'bg-primary-600 text-white'
                                : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                            }`}
                          >
                            <span className="font-medium">{movement.name}</span>
                            <span className="text-xs ml-2 opacity-75">
                              {movement.category}
                              {movement.subcategory && ` - ${movement.subcategory}`}
                            </span>
                          </button>
                        ))}
                      {movements.filter(m => {
                        const search = techniqueSearch[index]?.toLowerCase() || '';
                        return m.name.toLowerCase().includes(search) ||
                               m.category?.toLowerCase().includes(search) ||
                               m.subcategory?.toLowerCase().includes(search) ||
                               m.aliases.some(alias => alias.toLowerCase().includes(search));
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
                              value={media.title || ''}
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

        {/* Partners (Sparring only) */}
        {isSparringType && (
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

        {/* Session Details / Notes */}
        <div className={!isSparringType ? 'border-t border-gray-200 dark:border-gray-700 pt-4' : ''}>
          <label className="label">
            {!isSparringType ? 'Session Details' : 'Notes'}
            {!isSparringType && <span className="text-sm font-normal text-gray-500 ml-2">(Workout details, exercises, distances, times, etc.)</span>}
          </label>
          <textarea
            className="input"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={!isSparringType ? 5 : 3}
            placeholder={
              !isSparringType
                ? "e.g., 5km run in 30 mins, Deadlifts 3x8 @ 100kg, Squats 3x10 @ 80kg, or Yoga flow focusing on hip mobility..."
                : "Any notes about this session..."
            }
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

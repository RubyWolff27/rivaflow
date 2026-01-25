import { useState, useEffect } from 'react';
import { profileApi, gradingsApi } from '../api/client';
import type { Profile as ProfileType, Grading } from '../types';
import { User, CheckCircle, Award, Plus, Trash2, Edit2 } from 'lucide-react';

const BELT_GRADES = [
  'White',
  'Blue',
  'Purple',
  'Brown',
  'Black',
  'White (1 stripe)',
  'White (2 stripes)',
  'White (3 stripes)',
  'White (4 stripes)',
  'Blue (1 stripe)',
  'Blue (2 stripes)',
  'Blue (3 stripes)',
  'Blue (4 stripes)',
  'Purple (1 stripe)',
  'Purple (2 stripes)',
  'Purple (3 stripes)',
  'Purple (4 stripes)',
  'Brown (1 stripe)',
  'Brown (2 stripes)',
  'Brown (3 stripes)',
  'Brown (4 stripes)',
  'Black (1st degree)',
  'Black (2nd degree)',
  'Black (3rd degree)',
  'Black (4th degree)',
  'Black (5th degree)',
];

export default function Profile() {
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [gradings, setGradings] = useState<Grading[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showAddGrading, setShowAddGrading] = useState(false);
  const [editingGrading, setEditingGrading] = useState<Grading | null>(null);

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    sex: '',
    city: '',
    state: '',
    default_gym: '',
    current_professor: '',
  });

  const [gradingForm, setGradingForm] = useState({
    grade: '',
    date_graded: new Date().toISOString().split('T')[0],
    professor: '',
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileRes, gradingsRes] = await Promise.all([
        profileApi.get(),
        gradingsApi.list(),
      ]);
      setProfile(profileRes.data);
      setGradings(gradingsRes.data);
      setFormData({
        first_name: profileRes.data.first_name || '',
        last_name: profileRes.data.last_name || '',
        date_of_birth: profileRes.data.date_of_birth || '',
        sex: profileRes.data.sex || '',
        city: profileRes.data.city || '',
        state: profileRes.data.state || '',
        default_gym: profileRes.data.default_gym || '',
        current_professor: profileRes.data.current_professor || '',
      });
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      await profileApi.update({
        first_name: formData.first_name || undefined,
        last_name: formData.last_name || undefined,
        date_of_birth: formData.date_of_birth || undefined,
        sex: (formData.sex || undefined) as 'male' | 'female' | 'other' | 'prefer_not_to_say' | undefined,
        city: formData.city || undefined,
        state: formData.state || undefined,
        default_gym: formData.default_gym || undefined,
        current_professor: formData.current_professor || undefined,
      });
      setSuccess(true);
      await loadData();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleOpenAddGrading = () => {
    setGradingForm({
      grade: '',
      date_graded: new Date().toISOString().split('T')[0],
      professor: profile?.current_professor || '',
      notes: '',
    });
    setShowAddGrading(true);
    setEditingGrading(null);
  };

  const handleAddGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gradingForm.grade || !gradingForm.date_graded) {
      alert('Please select a grade and date.');
      return;
    }

    try {
      await gradingsApi.create({
        grade: gradingForm.grade,
        date_graded: gradingForm.date_graded,
        professor: gradingForm.professor || undefined,
        notes: gradingForm.notes || undefined,
      });
      setGradingForm({
        grade: '',
        date_graded: new Date().toISOString().split('T')[0],
        professor: '',
        notes: '',
      });
      setShowAddGrading(false);
      await loadData();
    } catch (error) {
      console.error('Error adding grading:', error);
      alert('Failed to add grading. Please try again.');
    }
  };

  const handleEditGrading = (grading: Grading) => {
    setEditingGrading(grading);
    setGradingForm({
      grade: grading.grade,
      date_graded: grading.date_graded,
      professor: grading.professor || '',
      notes: grading.notes || '',
    });
    setShowAddGrading(false);
  };

  const handleUpdateGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGrading) return;

    if (!gradingForm.grade || !gradingForm.date_graded) {
      alert('Please select a grade and date.');
      return;
    }

    try {
      await gradingsApi.update(editingGrading.id, {
        grade: gradingForm.grade,
        date_graded: gradingForm.date_graded,
        professor: gradingForm.professor || undefined,
        notes: gradingForm.notes || undefined,
      });
      setGradingForm({
        grade: '',
        date_graded: new Date().toISOString().split('T')[0],
        professor: '',
        notes: '',
      });
      setEditingGrading(null);
      await loadData();
    } catch (error) {
      console.error('Error updating grading:', error);
      alert('Failed to update grading. Please try again.');
    }
  };

  const handleCancelEdit = () => {
    setEditingGrading(null);
    setGradingForm({
      grade: '',
      date_graded: new Date().toISOString().split('T')[0],
      professor: '',
      notes: '',
    });
  };

  const handleDeleteGrading = async (gradingId: number) => {
    if (!confirm('Are you sure you want to delete this grading?')) {
      return;
    }

    try {
      await gradingsApi.delete(gradingId);
      await loadData();
    } catch (error) {
      console.error('Error deleting grading:', error);
      alert('Failed to delete grading.');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <User className="w-8 h-8 text-primary-600" />
        <h1 className="text-3xl font-bold">Profile</h1>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
        {success && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-700 dark:text-green-400">
            <CheckCircle className="w-5 h-5" />
            Profile updated successfully!
          </div>
        )}

        <div className="space-y-6">
          {/* Name */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">First Name</label>
              <input
                type="text"
                className="input"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="Your first name"
                required
              />
            </div>
            <div>
              <label className="label">Last Name</label>
              <input
                type="text"
                className="input"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="Your last name"
                required
              />
            </div>
          </div>

          {/* Date of Birth */}
          <div>
            <label className="label">Date of Birth</label>
            <input
              type="date"
              className="input"
              value={formData.date_of_birth}
              onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
              max={new Date().toISOString().split('T')[0]}
            />
            {profile?.age && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Age: {profile.age} years old
              </p>
            )}
          </div>

          {/* Sex */}
          <div>
            <label className="label">Sex</label>
            <select
              className="input"
              value={formData.sex}
              onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
            >
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>

          {/* Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">City</label>
              <input
                type="text"
                className="input"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                placeholder="e.g., Sydney"
                required
              />
            </div>
            <div>
              <label className="label">State</label>
              <input
                type="text"
                className="input"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                placeholder="e.g., NSW"
                required
              />
            </div>
          </div>

          {/* Default Gym */}
          <div>
            <label className="label">Default Gym</label>
            <input
              type="text"
              className="input"
              value={formData.default_gym}
              onChange={(e) => setFormData({ ...formData, default_gym: e.target.value })}
              placeholder="Your main training gym"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              This will be pre-filled when logging sessions
            </p>
          </div>

          {/* Current Professor */}
          <div>
            <label className="label">Current Professor / Instructor</label>
            <input
              type="text"
              className="input"
              value={formData.current_professor}
              onChange={(e) => setFormData({ ...formData, current_professor: e.target.value })}
              placeholder="e.g., Professor John Smith"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              This will auto-populate when adding gradings
            </p>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="btn-primary w-full"
          >
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </form>

      {/* Belt Progression Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Award className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-semibold">Belt Progression</h2>
          </div>
          <button
            onClick={handleOpenAddGrading}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Grading
          </button>
        </div>

        {/* Current Grade Display */}
        {profile?.current_grade && (
          <div className="mb-6 p-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Current Grade</p>
            <p className="text-2xl font-bold text-primary-600">{profile.current_grade}</p>
          </div>
        )}

        {/* Add/Edit Grading Form */}
        {(showAddGrading || editingGrading) && (
          <form onSubmit={editingGrading ? handleUpdateGrading : handleAddGrading} className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-4">
            <h3 className="font-semibold text-lg">{editingGrading ? 'Edit Grading' : 'Add New Grading'}</h3>

            <div>
              <label className="label">Belt / Grade</label>
              <select
                className="input"
                value={gradingForm.grade}
                onChange={(e) => setGradingForm({ ...gradingForm, grade: e.target.value })}
                required
              >
                <option value="">Select your grade</option>
                {BELT_GRADES.map((grade) => (
                  <option key={grade} value={grade}>
                    {grade}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Date Graded</label>
              <input
                type="date"
                className="input"
                value={gradingForm.date_graded}
                onChange={(e) => setGradingForm({ ...gradingForm, date_graded: e.target.value })}
                max={new Date().toISOString().split('T')[0]}
                required
              />
            </div>

            <div>
              <label className="label">Professor / Instructor (optional)</label>
              <input
                type="text"
                className="input"
                value={gradingForm.professor}
                onChange={(e) => setGradingForm({ ...gradingForm, professor: e.target.value })}
                placeholder="e.g., Professor John Smith"
              />
            </div>

            <div>
              <label className="label">Notes (optional)</label>
              <textarea
                className="input"
                value={gradingForm.notes}
                onChange={(e) => setGradingForm({ ...gradingForm, notes: e.target.value })}
                rows={2}
                placeholder="e.g., Focused on passing game, competition preparation"
              />
            </div>

            <div className="flex gap-2">
              <button type="submit" className="btn-primary">
                {editingGrading ? 'Update Grading' : 'Save Grading'}
              </button>
              <button
                type="button"
                onClick={editingGrading ? handleCancelEdit : () => setShowAddGrading(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Grading History */}
        {gradings.length > 0 ? (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase">History</h3>
            {gradings.map((grading) => (
              <div
                key={grading.id}
                className="flex items-start justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 dark:text-white">{grading.grade}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {formatDate(grading.date_graded)}
                  </p>
                  {grading.professor && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Professor: {grading.professor}
                    </p>
                  )}
                  {grading.notes && (
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-1 italic">
                      {grading.notes}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditGrading(grading)}
                    className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    title="Edit grading"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteGrading(grading.id)}
                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    title="Delete grading"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-center py-6">
            No gradings recorded yet. Click "Add Grading" to track your belt progression.
          </p>
        )}
      </div>

      {/* Info Card */}
      <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold mb-2">About Your Profile</h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>• Your profile data is stored locally on your device</li>
          <li>• Default gym will pre-fill session logging forms</li>
          <li>• Belt progression tracks your BJJ journey over time</li>
          <li>• All fields are optional</li>
        </ul>
      </div>
    </div>
  );
}

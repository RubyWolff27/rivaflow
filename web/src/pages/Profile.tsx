import { useState, useEffect } from 'react';
import { profileApi, gradingsApi, friendsApi, adminApi } from '../api/client';
import type { Profile as ProfileType, Grading, Friend } from '../types';
import { User, CheckCircle, Award, Plus, Trash2, Edit2, Target, AlertCircle } from 'lucide-react';
import GymSelector from '../components/GymSelector';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';

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
  const [instructors, setInstructors] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showAddGrading, setShowAddGrading] = useState(false);
  const [editingGrading, setEditingGrading] = useState<Grading | null>(null);
  const [isCustomGym, setIsCustomGym] = useState(false);
  const [gymVerificationPending, setGymVerificationPending] = useState(false);
  const [gradingToDelete, setGradingToDelete] = useState<number | null>(null);
  const toast = useToast();

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    sex: '',
    city: '',
    state: '',
    default_gym: '',
    default_location: '',
    current_professor: '',
    current_instructor_id: null as number | null,
    height_cm: '',
    target_weight_kg: '',
    weekly_sessions_target: 3,
    weekly_hours_target: 4.5,
    weekly_rolls_target: 15,
    show_streak_on_dashboard: true,
    show_weekly_goals: true,
    avatar_url: '',
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
      const [profileRes, gradingsRes, instructorsRes] = await Promise.all([
        profileApi.get(),
        gradingsApi.list(),
        friendsApi.listInstructors(),
      ]);
      setProfile(profileRes.data ?? null);
      setGradings(gradingsRes.data ?? []);
      setInstructors(instructorsRes.data ?? []);
      setFormData({
        first_name: profileRes.data?.first_name ?? '',
        last_name: profileRes.data?.last_name ?? '',
        date_of_birth: profileRes.data?.date_of_birth ?? '',
        sex: profileRes.data?.sex ?? '',
        city: profileRes.data?.city ?? '',
        state: profileRes.data?.state ?? '',
        default_gym: profileRes.data?.default_gym ?? '',
        default_location: profileRes.data?.default_location ?? '',
        current_professor: profileRes.data?.current_professor ?? '',
        current_instructor_id: profileRes.data?.current_instructor_id ?? null,
        height_cm: profileRes.data?.height_cm?.toString() ?? '',
        target_weight_kg: profileRes.data?.target_weight_kg?.toString() ?? '',
        weekly_sessions_target: profileRes.data?.weekly_sessions_target ?? 3,
        weekly_hours_target: profileRes.data?.weekly_hours_target ?? 4.5,
        weekly_rolls_target: profileRes.data?.weekly_rolls_target ?? 15,
        show_streak_on_dashboard: profileRes.data?.show_streak_on_dashboard ?? true,
        show_weekly_goals: profileRes.data?.show_weekly_goals ?? true,
        avatar_url: profileRes.data?.avatar_url ?? '',
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
        default_location: formData.default_location || undefined,
        current_professor: formData.current_professor || undefined,
        current_instructor_id: formData.current_instructor_id || undefined,
        height_cm: formData.height_cm ? parseInt(formData.height_cm) : undefined,
        target_weight_kg: formData.target_weight_kg ? parseFloat(formData.target_weight_kg) : undefined,
        avatar_url: formData.avatar_url || undefined,
      });
      setSuccess(true);
      await loadData();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleGoalsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      await profileApi.update({
        weekly_sessions_target: formData.weekly_sessions_target,
        weekly_hours_target: formData.weekly_hours_target,
        weekly_rolls_target: formData.weekly_rolls_target,
        show_streak_on_dashboard: formData.show_streak_on_dashboard,
        show_weekly_goals: formData.show_weekly_goals,
      });
      setSuccess(true);
      await loadData();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating goals:', error);
      toast.error('Failed to update goals. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleOpenAddGrading = () => {
    setGradingForm({
      grade: '',
      date_graded: new Date().toISOString().split('T')[0],
      professor: profile?.current_professor ?? '',
      notes: '',
    });
    setShowAddGrading(true);
    setEditingGrading(null);
  };

  const handleAddGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gradingForm.grade || !gradingForm.date_graded) {
      toast.error('Please select a grade and date.');
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
      toast.success('Grading added successfully');
    } catch (error) {
      console.error('Error adding grading:', error);
      toast.error('Failed to add grading. Please try again.');
    }
  };

  const handleEditGrading = (grading: Grading) => {
    setEditingGrading(grading);
    setGradingForm({
      grade: grading.grade ?? '',
      date_graded: grading.date_graded ?? new Date().toISOString().split('T')[0],
      professor: grading.professor ?? '',
      notes: grading.notes ?? '',
    });
    setShowAddGrading(false);
  };

  const handleUpdateGrading = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGrading) return;

    if (!gradingForm.grade || !gradingForm.date_graded) {
      toast.error('Please select a grade and date.');
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
      toast.success('Grading updated successfully');
    } catch (error) {
      console.error('Error updating grading:', error);
      toast.error('Failed to update grading. Please try again.');
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

  const handleDeleteGrading = async () => {
    if (!gradingToDelete) return;

    try {
      await gradingsApi.delete(gradingToDelete);
      await loadData();
      toast.success('Grading deleted successfully');
    } catch (error) {
      console.error('Error deleting grading:', error);
      toast.error('Failed to delete grading.');
    } finally {
      setGradingToDelete(null);
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
          {/* Profile Photo */}
          <div className="flex items-center gap-6 pb-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex-shrink-0">
              {formData.avatar_url ? (
                <img
                  src={formData.avatar_url}
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover border-4 border-gray-200 dark:border-gray-700"
                  onError={(e) => {
                    e.currentTarget.src = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(formData.first_name + '+' + formData.last_name) + '&size=200&background=random';
                  }}
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                  <User className="w-12 h-12 text-gray-400 dark:text-gray-500" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <label className="label">Profile Photo URL</label>
              <input
                type="url"
                className="input"
                value={formData.avatar_url}
                onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                placeholder="https://example.com/photo.jpg or leave blank for initials"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Paste an image URL or leave blank to use your initials
              </p>
            </div>
          </div>

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
            {profile?.age != null && (
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

          {/* Height and Target Weight */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Height (cm)</label>
              <input
                type="number"
                className="input"
                value={formData.height_cm}
                onChange={(e) => setFormData({ ...formData, height_cm: e.target.value })}
                placeholder="e.g., 175"
                min="100"
                max="250"
              />
            </div>
            <div>
              <label className="label">Target Weight (kg)</label>
              <input
                type="number"
                className="input"
                value={formData.target_weight_kg}
                onChange={(e) => setFormData({ ...formData, target_weight_kg: e.target.value })}
                placeholder="e.g., 75.5"
                min="30"
                max="300"
                step="0.1"
              />
            </div>
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
            <GymSelector
              value={formData.default_gym}
              onChange={(value, custom) => {
                setFormData({ ...formData, default_gym: value });
                setIsCustomGym(custom);
              }}
              onCreateGym={async (gymName) => {
                try {
                  // Submit custom gym for verification
                  await adminApi.createGym({
                    name: gymName,
                    country: formData.state === 'NSW' || formData.state === 'VIC' || formData.state === 'QLD'
                      ? 'Australia'
                      : 'Unknown',
                    city: formData.city || undefined,
                    state: formData.state || undefined,
                    verified: false, // Pending verification
                  });
                  setGymVerificationPending(true);
                  setTimeout(() => setGymVerificationPending(false), 5000);
                } catch (error) {
                  console.error('Error submitting gym:', error);
                }
              }}
            />
            {isCustomGym && gymVerificationPending && (
              <div className="flex items-start gap-2 mt-2 p-3 rounded-lg" style={{ backgroundColor: 'var(--warning-bg)' }}>
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: 'var(--warning)' }} />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--warning)' }}>
                    Gym Submitted for Verification
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                    Your gym has been added to our database and will be verified by our team soon.
                  </p>
                </div>
              </div>
            )}
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Select from existing gyms or add a new one for verification
            </p>
          </div>

          {/* Default Location */}
          <div>
            <label className="label">Default Location</label>
            <input
              type="text"
              className="input"
              value={formData.default_location}
              onChange={(e) => setFormData({ ...formData, default_location: e.target.value })}
              placeholder="e.g., Sydney, NSW"
            />
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              This will auto-populate when logging sessions
            </p>
          </div>

          {/* Current Coach/Instructor */}
          <div>
            <label className="label">Current Coach / Instructor</label>
            <select
              className="input"
              value={formData.current_instructor_id ?? ''}
              onChange={(e) => {
                const instructorId = e.target.value ? parseInt(e.target.value) : null;
                const instructor = instructors.find(i => i.id === instructorId);
                setFormData({
                  ...formData,
                  current_instructor_id: instructorId,
                  current_professor: instructor?.name ?? '',
                });
              }}
            >
              <option value="">Select a coach...</option>
              {instructors.map((instructor) => (
                <option key={instructor.id} value={instructor.id}>
                  {instructor.name ?? 'Unknown'}
                  {instructor.belt_rank && ` - ${instructor.belt_rank}`}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              This will auto-populate when logging sessions. Add instructors in Contacts first.
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

      {/* Weekly Goals Section */}
      <form onSubmit={handleGoalsSubmit} className="card">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-6 h-6 text-green-600" />
          <h2 className="text-xl font-semibold">Weekly Goals</h2>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Set your weekly training targets. These will be tracked on your dashboard.
        </p>

        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Sessions / Week</label>
              <input
                type="number"
                className="input"
                value={formData.weekly_sessions_target}
                onChange={(e) => setFormData({ ...formData, weekly_sessions_target: parseInt(e.target.value) || 0 })}
                min="0"
                max="20"
              />
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Recommended: 3-5</p>
            </div>

            <div>
              <label className="label">Hours / Week</label>
              <input
                type="number"
                className="input"
                value={formData.weekly_hours_target}
                onChange={(e) => setFormData({ ...formData, weekly_hours_target: parseFloat(e.target.value) || 0 })}
                min="0"
                max="40"
                step="0.5"
              />
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Recommended: 4-6</p>
            </div>

            <div>
              <label className="label">Rolls / Week</label>
              <input
                type="number"
                className="input"
                value={formData.weekly_rolls_target}
                onChange={(e) => setFormData({ ...formData, weekly_rolls_target: parseInt(e.target.value) || 0 })}
                min="0"
                max="100"
              />
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Recommended: 15-25</p>
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.show_weekly_goals}
                onChange={(e) => setFormData({ ...formData, show_weekly_goals: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm">Show weekly goals on dashboard</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.show_streak_on_dashboard}
                onChange={(e) => setFormData({ ...formData, show_streak_on_dashboard: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm">Show training streaks on dashboard</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="btn-primary w-full"
          >
            {saving ? 'Saving...' : 'Save Goals'}
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
                    onClick={() => setGradingToDelete(grading.id)}
                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    title="Delete grading"
                    aria-label="Delete grading"
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

      <ConfirmDialog
        isOpen={gradingToDelete !== null}
        onClose={() => setGradingToDelete(null)}
        onConfirm={handleDeleteGrading}
        title="Delete Grading"
        message="Are you sure you want to delete this grading? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

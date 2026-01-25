import { useState, useEffect } from 'react';
import { profileApi } from '../api/client';
import type { Profile as ProfileType } from '../types';
import { User, CheckCircle } from 'lucide-react';

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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    age: '',
    sex: '',
    default_gym: '',
    current_grade: '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const res = await profileApi.get();
      setProfile(res.data);
      setFormData({
        age: res.data.age?.toString() || '',
        sex: res.data.sex || '',
        default_gym: res.data.default_gym || '',
        current_grade: res.data.current_grade || '',
      });
    } catch (error) {
      console.error('Error loading profile:', error);
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
        age: formData.age ? parseInt(formData.age) : undefined,
        sex: formData.sex || undefined,
        default_gym: formData.default_gym || undefined,
        current_grade: formData.current_grade || undefined,
      });
      setSuccess(true);
      await loadProfile();
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
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

      <form onSubmit={handleSubmit} className="card">
        {success && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-700 dark:text-green-400">
            <CheckCircle className="w-5 h-5" />
            Profile updated successfully!
          </div>
        )}

        <div className="space-y-6">
          {/* Age */}
          <div>
            <label className="label">Age</label>
            <input
              type="number"
              className="input"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: e.target.value })}
              min="1"
              max="120"
              placeholder="Optional"
            />
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

          {/* Current Grade/Belt */}
          <div>
            <label className="label">Current Grade / Belt Rank</label>
            <select
              className="input"
              value={formData.current_grade}
              onChange={(e) => setFormData({ ...formData, current_grade: e.target.value })}
            >
              <option value="">Select your grade</option>
              {BELT_GRADES.map((grade) => (
                <option key={grade} value={grade}>
                  {grade}
                </option>
              ))}
            </select>
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

      {/* Info Card */}
      <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold mb-2">About Your Profile</h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>• Your profile data is stored locally on your device</li>
          <li>• Default gym will pre-fill session logging forms</li>
          <li>• Grade tracking helps you remember your progression</li>
          <li>• All fields are optional</li>
        </ul>
      </div>
    </div>
  );
}

import { User, CheckCircle, AlertCircle } from 'lucide-react';
import { getLocalDateString } from '../../utils/date';
import GymSelector from '../GymSelector';
import type { Profile, Friend } from '../../types';

export interface PersonalInformationFormProps {
  formData: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    sex: string;
    city: string;
    state: string;
    default_gym: string;
    default_location: string;
    current_professor: string;
    current_instructor_id: number | null;
    primary_training_type: string;
    height_cm: string;
    target_weight_kg: string;
    target_weight_date: string;
    avatar_url: string;
    timezone: string;
    primary_gym_id: number | null;
  };
  onChange: (data: PersonalInformationFormProps['formData']) => void;
  profile: Profile | null;
  instructors: Friend[];
  saving: boolean;
  success: boolean;
  onSubmit: (e: React.FormEvent) => void;
  // Photo props
  photoPreview: string | null;
  uploadingPhoto: boolean;
  onPhotoUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDeletePhoto: () => void;
  // Gym props
  isCustomGym: boolean;
  onCustomGymChange: (isCustom: boolean) => void;
  gymVerificationPending: boolean;
  onGymVerificationPending: (pending: boolean) => void;
  gymHeadCoach: string | null;
  onCreateGym: (gymName: string) => Promise<void>;
  onGymSelected: (gym: { id: number }) => void;
}

export default function PersonalInformationForm({
  formData,
  onChange,
  profile,
  instructors,
  saving,
  success,
  onSubmit,
  photoPreview,
  uploadingPhoto,
  onPhotoUpload,
  onDeletePhoto,
  isCustomGym,
  onCustomGymChange,
  gymVerificationPending,
  gymHeadCoach,
  onCreateGym,
  onGymSelected,
}: PersonalInformationFormProps) {
  return (
    <form onSubmit={onSubmit} className="card">
      <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
      {success && (
        <div className="mb-4 p-3 rounded-lg flex items-center gap-2" style={{ backgroundColor: 'rgba(34,197,94,0.1)', color: 'var(--success)', border: '1px solid var(--success)' }}>
          <CheckCircle className="w-5 h-5" />
          Profile updated successfully!
        </div>
      )}

      <div className="space-y-6">
        {/* Profile Photo */}
        <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-[var(--border)]">
          <div className="flex-shrink-0">
            {photoPreview || formData.avatar_url ? (
              <img
                src={photoPreview || formData.avatar_url}
                alt="Profile"
                className="w-24 h-24 rounded-full object-cover border-4 border-[var(--border)]"
                onError={(e) => {
                  e.currentTarget.src = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(formData.first_name + '+' + formData.last_name) + '&size=200&background=random';
                }}
              />
            ) : (
              <div className="w-24 h-24 rounded-full bg-[var(--surfaceElev)] flex items-center justify-center">
                <User className="w-12 h-12 text-[var(--muted)]" />
              </div>
            )}
          </div>
          <div className="flex-1">
            <label className="label">Profile Photo</label>
            <div className="flex gap-2">
              <label className="btn-primary cursor-pointer flex items-center gap-2">
                <input
                  type="file"
                  className="hidden"
                  accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                  onChange={onPhotoUpload}
                  disabled={uploadingPhoto}
                />
                {uploadingPhoto ? 'Uploading...' : 'Choose Photo'}
              </label>
              {formData.avatar_url && (
                <button
                  type="button"
                  onClick={onDeletePhoto}
                  className="btn-secondary"
                >
                  Remove Photo
                </button>
              )}
            </div>
            <p className="text-xs text-[var(--muted)] mt-1">
              Upload a JPG, PNG, WebP, or GIF image (max 5MB)
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
              onChange={(e) => onChange({ ...formData, first_name: e.target.value })}
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
              onChange={(e) => onChange({ ...formData, last_name: e.target.value })}
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
            onChange={(e) => onChange({ ...formData, date_of_birth: e.target.value })}
            max={getLocalDateString()}
          />
          {profile?.age != null && (
            <p className="text-sm text-[var(--muted)] mt-1">
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
            onChange={(e) => onChange({ ...formData, sex: e.target.value })}
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
              onChange={(e) => onChange({ ...formData, height_cm: e.target.value })}
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
              onChange={(e) => onChange({ ...formData, target_weight_kg: e.target.value })}
              placeholder="e.g., 75.5"
              min="30"
              max="300"
              step="0.1"
            />
          </div>
        </div>
        {formData.target_weight_kg && (
          <div>
            <label className="label">Target Date (optional)</label>
            <input
              type="date"
              className="input"
              value={formData.target_weight_date}
              onChange={(e) => onChange({ ...formData, target_weight_date: e.target.value })}
            />
          </div>
        )}

        {/* Location */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">City</label>
            <input
              type="text"
              className="input"
              value={formData.city}
              onChange={(e) => onChange({ ...formData, city: e.target.value })}
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
              onChange={(e) => onChange({ ...formData, state: e.target.value })}
              placeholder="e.g., NSW"
              required
            />
          </div>
        </div>

        {/* Timezone */}
        <div>
          <label className="label">Timezone</label>
          <div className="flex gap-2">
            <input
              type="text"
              className="input flex-1"
              value={formData.timezone}
              onChange={(e) => onChange({ ...formData, timezone: e.target.value })}
              placeholder="e.g., Australia/Sydney"
            />
            <button
              type="button"
              onClick={() => {
                const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                if (tz) onChange({ ...formData, timezone: tz });
              }}
              className="btn-secondary text-sm whitespace-nowrap"
            >
              Detect
            </button>
          </div>
          <p className="text-sm text-[var(--muted)] mt-1">
            {formData.timezone
              ? `Timezone set to ${formData.timezone}`
              : 'Used for daily check-in timing. Click Detect to use your browser timezone.'}
          </p>
        </div>

        {/* Default Gym */}
        <div>
          <label className="label">Default Gym</label>
          <GymSelector
            value={formData.default_gym}
            onChange={(value, custom) => {
              onChange({ ...formData, default_gym: value, primary_gym_id: custom ? null : formData.primary_gym_id });
              onCustomGymChange(custom);
            }}
            onGymSelected={(gym) => {
              onGymSelected(gym);
            }}
            onCreateGym={async (gymName) => {
              await onCreateGym(gymName);
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
          <p className="text-sm text-[var(--muted)] mt-1">
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
            onChange={(e) => onChange({ ...formData, default_location: e.target.value })}
            placeholder="e.g., Sydney, NSW"
          />
          <p className="text-sm text-[var(--muted)] mt-1">
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
              const value = e.target.value;
              if (value === 'gym_head_coach') {
                // Using gym head coach (no ID, just name)
                onChange({
                  ...formData,
                  current_instructor_id: null,
                  current_professor: gymHeadCoach ?? '',
                });
              } else {
                const instructorId = value ? parseInt(value) : null;
                const instructor = instructors.find(i => i.id === instructorId);
                onChange({
                  ...formData,
                  current_instructor_id: instructorId,
                  current_professor: instructor?.name ?? '',
                });
              }
            }}
          >
            <option value="">Select a coach...</option>
            {gymHeadCoach && (
              <option value="gym_head_coach">
                {gymHeadCoach} (Head Coach at {formData.default_gym})
              </option>
            )}
            {instructors.map((instructor) => (
              <option key={instructor.id} value={instructor.id}>
                {instructor.name ?? 'Unknown'}
                {instructor.belt_rank && ` - ${instructor.belt_rank.charAt(0).toUpperCase() + instructor.belt_rank.slice(1)}`}
              </option>
            ))}
          </select>
          <p className="text-sm text-[var(--muted)] mt-1">
            {gymHeadCoach
              ? `Head coach from your selected gym is available, or add other instructors in Friends.`
              : 'This will auto-populate when logging sessions. Add instructors in Friends first.'}
          </p>
        </div>

        {/* Primary Training Type */}
        <div>
          <label className="label">Primary Training Type</label>
          <select
            className="input"
            value={formData.primary_training_type}
            onChange={(e) => onChange({ ...formData, primary_training_type: e.target.value })}
          >
            <option value="gi">Gi</option>
            <option value="no-gi">No-Gi</option>
            <option value="s&c">S&C</option>
            <option value="mobility">Mobility</option>
            <option value="drilling">Drilling</option>
            <option value="cardio">Cardio</option>
            <option value="physio">Physio</option>
            <option value="recovery">Recovery</option>
            <option value="mma">MMA</option>
            <option value="judo">Judo</option>
            <option value="wrestling">Wrestling</option>
            <option value="other">Other</option>
          </select>
          <p className="text-sm text-[var(--muted)] mt-1">
            This will be the default class type when logging sessions
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
  );
}

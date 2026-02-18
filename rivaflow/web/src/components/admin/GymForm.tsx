import { PrimaryButton, SecondaryButton } from '../ui';
import { Card } from '../ui';

interface GymFormData {
  name: string;
  city: string;
  state: string;
  country: string;
  address: string;
  website: string;
  email: string;
  phone: string;
  head_coach: string;
  head_coach_belt: string;
  google_maps_url: string;
  verified: boolean;
}

interface GymFormProps {
  formData: GymFormData;
  onFormDataChange: (data: GymFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  isEditing: boolean;
}

export default function GymForm({ formData, onFormDataChange, onSubmit, onCancel, isEditing }: GymFormProps) {
  return (
    <Card>
      <form onSubmit={onSubmit} className="space-y-4">
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
          {isEditing ? 'Edit Gym' : 'Add New Gym'}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => onFormDataChange({ ...formData, name: e.target.value })}
              className="input w-full"
              placeholder="Gym name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              City
            </label>
            <input
              type="text"
              value={formData.city}
              onChange={(e) => onFormDataChange({ ...formData, city: e.target.value })}
              className="input w-full"
              placeholder="City"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              State
            </label>
            <input
              type="text"
              value={formData.state}
              onChange={(e) => onFormDataChange({ ...formData, state: e.target.value })}
              className="input w-full"
              placeholder="State"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Country
            </label>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => onFormDataChange({ ...formData, country: e.target.value })}
              className="input w-full"
              placeholder="Country"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Address
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => onFormDataChange({ ...formData, address: e.target.value })}
              className="input w-full"
              placeholder="Full address"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Website
            </label>
            <input
              type="url"
              value={formData.website}
              onChange={(e) => onFormDataChange({ ...formData, website: e.target.value })}
              className="input w-full"
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => onFormDataChange({ ...formData, email: e.target.value })}
              className="input w-full"
              placeholder="contact@gym.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Phone
            </label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => onFormDataChange({ ...formData, phone: e.target.value })}
              className="input w-full"
              placeholder="+1 (555) 123-4567"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Head Coach
            </label>
            <input
              type="text"
              value={formData.head_coach}
              onChange={(e) => onFormDataChange({ ...formData, head_coach: e.target.value })}
              className="input w-full"
              placeholder="Coach name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Head Coach Belt
            </label>
            <select
              value={formData.head_coach_belt}
              onChange={(e) => onFormDataChange({ ...formData, head_coach_belt: e.target.value })}
              className="input w-full"
            >
              <option value="">Select belt...</option>
              <option value="white">White Belt</option>
              <option value="blue">Blue Belt</option>
              <option value="purple">Purple Belt</option>
              <option value="brown">Brown Belt</option>
              <option value="black">Black Belt</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Google Maps URL
            </label>
            <input
              type="url"
              value={formData.google_maps_url}
              onChange={(e) => onFormDataChange({ ...formData, google_maps_url: e.target.value })}
              className="input w-full"
              placeholder="https://maps.google.com/..."
            />
          </div>

          <div className="md:col-span-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.verified}
                onChange={(e) => onFormDataChange({ ...formData, verified: e.target.checked })}
                className="rounded"
              />
              <span className="text-sm" style={{ color: 'var(--text)' }}>
                Verified gym
              </span>
            </label>
          </div>
        </div>

        <div className="flex gap-2">
          <PrimaryButton type="submit">
            {isEditing ? 'Update' : 'Create'}
          </PrimaryButton>
          <SecondaryButton type="button" onClick={onCancel}>
            Cancel
          </SecondaryButton>
        </div>
      </form>
    </Card>
  );
}

export type { GymFormData };

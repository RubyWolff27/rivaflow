interface FriendFormData {
  name: string;
  friend_type: 'instructor' | 'training-partner' | 'both';
  belt_rank: '' | 'white' | 'blue' | 'purple' | 'brown' | 'black';
  belt_stripes: number;
  instructor_certification: string;
  phone: string;
  email: string;
  notes: string;
}

interface FriendFormProps {
  formData: FriendFormData;
  onFormDataChange: (data: FriendFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  isEditing: boolean;
}

export default function FriendForm({ formData, onFormDataChange, onSubmit, onCancel, isEditing }: FriendFormProps) {
  return (
    <form onSubmit={onSubmit} className="card bg-[var(--surfaceElev)] space-y-4">
      <h3 className="text-lg font-semibold">
        {isEditing ? 'Edit Friend' : 'Add New Friend'}
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Name *</label>
          <input
            type="text"
            className="input"
            value={formData.name}
            onChange={(e) => onFormDataChange({ ...formData, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="label">Type</label>
          <select
            className="input"
            value={formData.friend_type}
            onChange={(e) => onFormDataChange({ ...formData, friend_type: e.target.value as any })}
          >
            <option value="training-partner">Training Partner</option>
            <option value="instructor">Instructor</option>
            <option value="both">Both</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="label">Belt Rank</label>
          <select
            className="input"
            value={formData.belt_rank}
            onChange={(e) => onFormDataChange({ ...formData, belt_rank: e.target.value as any })}
          >
            <option value="">None</option>
            <option value="white">White</option>
            <option value="blue">Blue</option>
            <option value="purple">Purple</option>
            <option value="brown">Brown</option>
            <option value="black">Black</option>
          </select>
        </div>
        <div>
          <label className="label">Stripes</label>
          <input
            type="number"
            className="input"
            value={formData.belt_stripes}
            onChange={(e) => onFormDataChange({ ...formData, belt_stripes: parseInt(e.target.value) || 0 })}
            min="0"
            max="4"
          />
        </div>
        <div>
          <label className="label">Instructor Cert</label>
          <input
            type="text"
            className="input"
            value={formData.instructor_certification}
            onChange={(e) => onFormDataChange({ ...formData, instructor_certification: e.target.value })}
            placeholder="e.g., 1st degree"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Phone</label>
          <input
            type="tel"
            className="input"
            value={formData.phone}
            onChange={(e) => onFormDataChange({ ...formData, phone: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Email</label>
          <input
            type="email"
            className="input"
            value={formData.email}
            onChange={(e) => onFormDataChange({ ...formData, email: e.target.value })}
          />
        </div>
      </div>

      <div>
        <label className="label">Notes</label>
        <textarea
          className="input"
          value={formData.notes}
          onChange={(e) => onFormDataChange({ ...formData, notes: e.target.value })}
          rows={2}
        />
      </div>

      <div className="flex gap-2">
        <button type="submit" className="btn-primary">
          {isEditing ? 'Update Friend' : 'Add Friend'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
      </div>
    </form>
  );
}

export type { FriendFormData };

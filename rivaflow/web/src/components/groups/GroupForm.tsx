import { X } from 'lucide-react';

interface GroupFormData {
  name: string;
  description: string;
  group_type: string;
  privacy: string;
}

interface GroupFormProps {
  formData: GroupFormData;
  onFormDataChange: (data: GroupFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
}

export default function GroupForm({ formData, onFormDataChange, onSubmit, onClose }: GroupFormProps) {
  return (
    <div className="rounded-[14px] p-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Create Group</h2>
        <button onClick={onClose} style={{ color: 'var(--muted)' }}>
          <X className="w-5 h-5" />
        </button>
      </div>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Group Name *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => onFormDataChange({ ...formData, name: e.target.value })}
            placeholder="e.g. Tuesday Night Crew"
            className="w-full px-3 py-2 rounded-lg text-sm"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => onFormDataChange({ ...formData, description: e.target.value })}
            placeholder="What's this group about?"
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-sm resize-none"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Type
            </label>
            <select
              value={formData.group_type}
              onChange={(e) => onFormDataChange({ ...formData, group_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
            >
              <option value="training_crew">Training Crew</option>
              <option value="comp_team">Comp Team</option>
              <option value="study_group">Study Group</option>
              <option value="gym_class">Gym Class</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
              Privacy
            </label>
            <select
              value={formData.privacy}
              onChange={(e) => onFormDataChange({ ...formData, privacy: e.target.value })}
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
            >
              <option value="invite_only">Invite Only</option>
              <option value="open">Open</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            Create Group
          </button>
        </div>
      </form>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { groupsApi } from '../api/client';
import type { Group, GroupMember } from '../types';
import { Users, Plus, X, LogOut, Trash2, ChevronRight, Shield } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';

const GROUP_TYPE_LABELS: Record<string, string> = {
  training_crew: 'Training Crew',
  comp_team: 'Comp Team',
  study_group: 'Study Group',
  gym_class: 'Gym Class',
};

const GROUP_TYPE_COLORS: Record<string, string> = {
  training_crew: 'var(--accent)',
  comp_team: '#3B82F6',
  study_group: '#8B5CF6',
  gym_class: '#10B981',
};

export default function Groups() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<(Group & { members: GroupMember[]; member_count: number; user_role: string | null }) | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const toast = useToast();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    group_type: 'training_crew',
    privacy: 'invite_only',
  });

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const response = await groupsApi.list();
      setGroups(response.data.groups || []);
    } catch {
      toast.showToast('error', 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const loadGroupDetail = async (groupId: number) => {
    setDetailLoading(true);
    try {
      const response = await groupsApi.get(groupId);
      setSelectedGroup(response.data);
    } catch {
      toast.showToast('error', 'Failed to load group details');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    try {
      await groupsApi.create(formData);
      toast.showToast('success', 'Group created!');
      setShowCreateForm(false);
      setFormData({ name: '', description: '', group_type: 'training_crew', privacy: 'invite_only' });
      loadGroups();
    } catch {
      toast.showToast('error', 'Failed to create group');
    }
  };

  const handleLeave = async (groupId: number) => {
    try {
      await groupsApi.leave(groupId);
      toast.showToast('success', 'Left group');
      setSelectedGroup(null);
      loadGroups();
    } catch {
      toast.showToast('error', 'Failed to leave group');
    }
  };

  const handleDelete = async (groupId: number) => {
    try {
      await groupsApi.delete(groupId);
      toast.showToast('success', 'Group deleted');
      setSelectedGroup(null);
      loadGroups();
    } catch {
      toast.showToast('error', 'Failed to delete group');
    }
  };

  // Group Detail View
  if (selectedGroup) {
    const isAdmin = selectedGroup.user_role === 'admin';

    return (
      <div className="space-y-6">
        {/* Back + Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedGroup(null)}
            className="flex items-center gap-2 text-sm font-medium"
            style={{ color: 'var(--muted)' }}
          >
            <ChevronRight className="w-4 h-4 rotate-180" />
            Back to Groups
          </button>
          <div className="flex gap-2">
            {!isAdmin && (
              <button
                onClick={() => handleLeave(selectedGroup.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium"
                style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
              >
                <LogOut className="w-3.5 h-3.5" />
                Leave
              </button>
            )}
            {isAdmin && (
              <button
                onClick={() => handleDelete(selectedGroup.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium"
                style={{ color: 'var(--error)', border: '1px solid var(--error)' }}
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete
              </button>
            )}
          </div>
        </div>

        {/* Group Info Card */}
        <div className="rounded-[14px] p-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                {selectedGroup.name}
              </h1>
              {selectedGroup.description && (
                <p className="mt-1 text-sm" style={{ color: 'var(--muted)' }}>
                  {selectedGroup.description}
                </p>
              )}
            </div>
            <span
              className="px-3 py-1 rounded-full text-xs font-semibold"
              style={{
                backgroundColor: `${GROUP_TYPE_COLORS[selectedGroup.group_type] || 'var(--accent)'}20`,
                color: GROUP_TYPE_COLORS[selectedGroup.group_type] || 'var(--accent)',
              }}
            >
              {GROUP_TYPE_LABELS[selectedGroup.group_type] || selectedGroup.group_type}
            </span>
          </div>
          <div className="flex gap-4 text-sm" style={{ color: 'var(--muted)' }}>
            <span className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              {selectedGroup.member_count} member{selectedGroup.member_count !== 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1">
              {selectedGroup.privacy === 'open' ? 'Open' : 'Invite Only'}
            </span>
            {isAdmin && (
              <span className="flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                <Shield className="w-3.5 h-3.5" />
                Admin
              </span>
            )}
          </div>
        </div>

        {/* Members List */}
        <div>
          <h2 className="text-lg font-semibold mb-3" style={{ color: 'var(--text)' }}>
            Members ({selectedGroup.members?.length || 0})
          </h2>
          <div className="space-y-2">
            {detailLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-[14px] p-4 animate-pulse" style={{ backgroundColor: 'var(--surface)' }}>
                  <div className="h-5 rounded w-1/3" style={{ backgroundColor: 'var(--border)' }} />
                </div>
              ))
            ) : (
              (selectedGroup.members || []).map((member) => (
                <div
                  key={member.id}
                  className="rounded-[14px] p-4 flex items-center justify-between"
                  style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold"
                      style={{
                        backgroundColor: member.role === 'admin' ? 'var(--accent)' : 'var(--surfaceElev)',
                        color: member.role === 'admin' ? '#fff' : 'var(--text)',
                      }}
                    >
                      {(member.first_name?.[0] || '?').toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {member.first_name} {member.last_name}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--muted)' }}>
                        {member.role === 'admin' ? 'Admin' : 'Member'}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // Groups List View
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Groups</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Training crews, comp teams & study groups
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
          style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
        >
          <Plus className="w-4 h-4" />
          New Group
        </button>
      </div>

      {/* Create Group Form */}
      {showCreateForm && (
        <div className="rounded-[14px] p-6" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Create Group</h2>
            <button onClick={() => setShowCreateForm(false)} style={{ color: 'var(--muted)' }}>
              <X className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Group Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value })}
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
                  onChange={(e) => setFormData({ ...formData, privacy: e.target.value })}
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
                onClick={() => setShowCreateForm(false)}
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
      )}

      {/* Groups List */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-[14px] p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)' }}>
              <div className="h-5 rounded w-1/3 mb-2" style={{ backgroundColor: 'var(--border)' }} />
              <div className="h-4 rounded w-1/2" style={{ backgroundColor: 'var(--border)' }} />
            </div>
          ))}
        </div>
      ) : groups.length === 0 ? (
        <div className="text-center py-16">
          <Users className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
          <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
            No groups yet
          </h3>
          <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
            Create a group to train and track progress together.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            <Plus className="w-4 h-4" />
            Create Your First Group
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {groups.map((group) => (
            <button
              key={group.id}
              onClick={() => loadGroupDetail(group.id)}
              className="w-full text-left rounded-[14px] p-5 transition-colors"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-sm truncate" style={{ color: 'var(--text)' }}>
                      {group.name}
                    </h3>
                    <span
                      className="px-2 py-0.5 rounded-full text-[10px] font-semibold shrink-0"
                      style={{
                        backgroundColor: `${GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)'}20`,
                        color: GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)',
                      }}
                    >
                      {GROUP_TYPE_LABELS[group.group_type] || group.group_type}
                    </span>
                  </div>
                  {group.description && (
                    <p className="text-xs mb-2 line-clamp-1" style={{ color: 'var(--muted)' }}>
                      {group.description}
                    </p>
                  )}
                  <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--muted)' }}>
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5" />
                      {group.member_count || 0} member{(group.member_count || 0) !== 1 ? 's' : ''}
                    </span>
                    {group.member_role === 'admin' && (
                      <span className="flex items-center gap-1" style={{ color: 'var(--accent)' }}>
                        <Shield className="w-3 h-3" />
                        Admin
                      </span>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 shrink-0 mt-1" style={{ color: 'var(--muted)' }} />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

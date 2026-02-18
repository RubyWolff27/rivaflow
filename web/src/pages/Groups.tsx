import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { groupsApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Group, GroupMember } from '../types';
import { Users, Plus, Globe } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import EmptyState from '../components/ui/EmptyState';
import GroupCard, { DiscoverGroupCard } from '../components/groups/GroupCard';
import GroupForm from '../components/groups/GroupForm';
import GroupDetailView from '../components/groups/GroupDetailView';

export default function Groups() {
  usePageTitle('Groups');
  const [groups, setGroups] = useState<Group[]>([]);
  const [discoverGroups, setDiscoverGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<(Group & { members: GroupMember[]; member_count: number; user_role: string | null }) | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [tab, setTab] = useState<'my' | 'discover'>('my');
  const toast = useToast();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    group_type: 'training_crew',
    privacy: 'invite_only',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await groupsApi.list();
        if (!cancelled) setGroups(response.data.groups || []);
      } catch {
        if (!cancelled) {
          logger.error('Error loading groups');
          toast.error('Failed to load groups');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const response = await groupsApi.list();
      setGroups(response.data.groups || []);
    } catch {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const loadDiscover = async () => {
    setLoading(true);
    try {
      const response = await groupsApi.discover();
      setDiscoverGroups(response.data.groups || []);
    } catch {
      toast.error('Failed to load discoverable groups');
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
      toast.error('Failed to load group details');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    try {
      await groupsApi.create(formData);
      toast.success('Group created!');
      setShowCreateForm(false);
      setFormData({ name: '', description: '', group_type: 'training_crew', privacy: 'invite_only' });
      loadGroups();
    } catch {
      toast.error('Failed to create group');
    }
  };

  const handleLeave = async (groupId: number) => {
    try {
      await groupsApi.leave(groupId);
      toast.success('Left group');
      setSelectedGroup(null);
      loadGroups();
    } catch {
      toast.error('Failed to leave group');
    }
  };

  const handleDelete = async (groupId: number) => {
    try {
      await groupsApi.delete(groupId);
      toast.success('Group deleted');
      setSelectedGroup(null);
      loadGroups();
    } catch {
      toast.error('Failed to delete group');
    }
  };

  const handleJoin = async (groupId: number) => {
    try {
      await groupsApi.join(groupId);
      toast.success('Joined group!');
      loadGroups();
      loadDiscover();
    } catch {
      toast.error('Failed to join group');
    }
  };

  const handleAddMember = async (userId: number) => {
    if (!selectedGroup) return;
    try {
      await groupsApi.addMember(selectedGroup.id, userId);
      toast.success('Member added!');
      loadGroupDetail(selectedGroup.id);
    } catch {
      toast.error('Failed to add member');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!selectedGroup) return;
    try {
      await groupsApi.removeMember(selectedGroup.id, userId);
      toast.success('Member removed');
      loadGroupDetail(selectedGroup.id);
    } catch {
      toast.error('Failed to remove member');
    }
  };

  const handleTabChange = (newTab: 'my' | 'discover') => {
    setTab(newTab);
    if (newTab === 'discover') {
      loadDiscover();
    }
  };

  // Group Detail View
  if (selectedGroup) {
    return (
      <GroupDetailView
        group={selectedGroup}
        detailLoading={detailLoading}
        onBack={() => setSelectedGroup(null)}
        onLeave={handleLeave}
        onDelete={handleDelete}
        onAddMember={handleAddMember}
        onRemoveMember={handleRemoveMember}
      />
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

      {/* Tabs: My Groups | Discover */}
      <div className="flex gap-1 p-1 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
        <button
          onClick={() => handleTabChange('my')}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors"
          style={{
            backgroundColor: tab === 'my' ? 'var(--surface)' : 'transparent',
            color: tab === 'my' ? 'var(--text)' : 'var(--muted)',
            boxShadow: tab === 'my' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
          }}
        >
          <Users className="w-3.5 h-3.5" />
          My Groups
        </button>
        <button
          onClick={() => handleTabChange('discover')}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors"
          style={{
            backgroundColor: tab === 'discover' ? 'var(--surface)' : 'transparent',
            color: tab === 'discover' ? 'var(--text)' : 'var(--muted)',
            boxShadow: tab === 'discover' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
          }}
        >
          <Globe className="w-3.5 h-3.5" />
          Discover
        </button>
      </div>

      {/* Create Group Form */}
      {showCreateForm && (
        <GroupForm
          formData={formData}
          onFormDataChange={setFormData}
          onSubmit={handleCreate}
          onClose={() => setShowCreateForm(false)}
        />
      )}

      {/* Groups List / Discover */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-[14px] p-5 animate-pulse" style={{ backgroundColor: 'var(--surface)' }}>
              <div className="h-5 rounded w-1/3 mb-2" style={{ backgroundColor: 'var(--border)' }} />
              <div className="h-4 rounded w-1/2" style={{ backgroundColor: 'var(--border)' }} />
            </div>
          ))}
        </div>
      ) : tab === 'my' ? (
        groups.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No groups yet"
            description="Create a group or discover open groups to join."
            action={
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
                >
                  <Plus className="w-4 h-4" />
                  Create Group
                </button>
                <button
                  onClick={() => handleTabChange('discover')}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium"
                  style={{ color: 'var(--text)', border: '1px solid var(--border)' }}
                >
                  <Globe className="w-4 h-4" />
                  Discover
                </button>
              </div>
            }
          />
        ) : (
          <div className="space-y-3">
            {groups.map((group) => (
              <GroupCard
                key={group.id}
                group={group}
                onClick={() => loadGroupDetail(group.id)}
              />
            ))}
          </div>
        )
      ) : (
        /* Discover Tab */
        discoverGroups.length === 0 ? (
          <EmptyState
            icon={Globe}
            title="No open groups to discover"
            description="All open groups have been joined, or none exist yet."
          />
        ) : (
          <div className="space-y-3">
            {discoverGroups.map((group) => (
              <DiscoverGroupCard
                key={group.id}
                group={group}
                onJoin={() => handleJoin(group.id)}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}

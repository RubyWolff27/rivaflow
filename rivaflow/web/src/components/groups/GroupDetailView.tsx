import { useState } from 'react';
import type { Group, GroupMember, UserBasic } from '../../types';
import { Users, X, LogOut, Trash2, ChevronRight, Shield, UserPlus, Search } from 'lucide-react';
import { socialApi } from '../../api/client';
import { GROUP_TYPE_LABELS, GROUP_TYPE_COLORS } from './GroupCard';

type GroupDetail = Group & { members: GroupMember[]; member_count: number; user_role: string | null };

interface GroupDetailViewProps {
  group: GroupDetail;
  detailLoading: boolean;
  onBack: () => void;
  onLeave: (groupId: number) => void;
  onDelete: (groupId: number) => void;
  onAddMember: (userId: number) => void;
  onRemoveMember: (userId: number) => void;
}

export default function GroupDetailView({
  group,
  detailLoading,
  onBack,
  onLeave,
  onDelete,
  onAddMember,
  onRemoveMember,
}: GroupDetailViewProps) {
  const isAdmin = group.user_role === 'admin';
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberSearch, setMemberSearch] = useState('');
  const [searchResults, setSearchResults] = useState<UserBasic[]>([]);
  const [searching, setSearching] = useState(false);

  const handleMemberSearch = async (query: string) => {
    setMemberSearch(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const response = await socialApi.searchUsers(query);
      const results = response.data?.users || response.data || [];
      const memberIds = new Set((group.members || []).map(m => m.user_id));
      setSearchResults(results.filter((u: UserBasic) => !memberIds.has(u.id)));
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddMemberClick = (userId: number) => {
    onAddMember(userId);
    setShowAddMember(false);
    setMemberSearch('');
    setSearchResults([]);
  };

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm font-medium"
          style={{ color: 'var(--muted)' }}
        >
          <ChevronRight className="w-4 h-4 rotate-180" />
          Back to Groups
        </button>
        <div className="flex gap-2">
          {!isAdmin && (
            <button
              onClick={() => onLeave(group.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium"
              style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
            >
              <LogOut className="w-3.5 h-3.5" />
              Leave
            </button>
          )}
          {isAdmin && (
            <button
              onClick={() => onDelete(group.id)}
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
              {group.name}
            </h1>
            {group.description && (
              <p className="mt-1 text-sm" style={{ color: 'var(--muted)' }}>
                {group.description}
              </p>
            )}
          </div>
          <span
            className="px-3 py-1 rounded-full text-xs font-semibold"
            style={{
              backgroundColor: `${GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)'}20`,
              color: GROUP_TYPE_COLORS[group.group_type] || 'var(--accent)',
            }}
          >
            {GROUP_TYPE_LABELS[group.group_type] || group.group_type}
          </span>
        </div>
        <div className="flex gap-4 text-sm" style={{ color: 'var(--muted)' }}>
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {group.member_count} member{group.member_count !== 1 ? 's' : ''}
          </span>
          <span className="flex items-center gap-1">
            {group.privacy === 'open' ? 'Open' : 'Invite Only'}
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
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
            Members ({group.members?.length || 0})
          </h2>
          {isAdmin && (
            <button
              onClick={() => setShowAddMember(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium"
              style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
            >
              <UserPlus className="w-3.5 h-3.5" />
              Add Member
            </button>
          )}
        </div>

        {/* Add Member Modal */}
        {showAddMember && (
          <div className="rounded-[14px] p-4 mb-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Search Users</h3>
              <button onClick={() => { setShowAddMember(false); setMemberSearch(''); setSearchResults([]); }} style={{ color: 'var(--muted)' }}>
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="relative mb-3">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted)' }} />
              <input
                type="text"
                value={memberSearch}
                onChange={(e) => handleMemberSearch(e.target.value)}
                placeholder="Search by name or email..."
                className="w-full pl-9 pr-3 py-2 rounded-lg text-sm"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
                autoFocus
              />
            </div>
            {searching && (
              <p className="text-xs py-2" style={{ color: 'var(--muted)' }}>Searching...</p>
            )}
            {searchResults.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {searchResults.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-2 rounded-lg"
                    style={{ backgroundColor: 'var(--surfaceElev)' }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                        style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
                      >
                        {(user.first_name?.[0] || '?').toUpperCase()}
                      </div>
                      <span className="text-sm" style={{ color: 'var(--text)' }}>
                        {user.first_name} {user.last_name}
                      </span>
                    </div>
                    <button
                      onClick={() => handleAddMemberClick(user.id)}
                      className="px-2.5 py-1 rounded text-xs font-medium"
                      style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
                    >
                      Add
                    </button>
                  </div>
                ))}
              </div>
            )}
            {memberSearch.length >= 2 && !searching && searchResults.length === 0 && (
              <p className="text-xs py-2" style={{ color: 'var(--muted)' }}>No users found</p>
            )}
          </div>
        )}

        <div className="space-y-2">
          {detailLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="rounded-[14px] p-4 animate-pulse" style={{ backgroundColor: 'var(--surface)' }}>
                <div className="h-5 rounded w-1/3" style={{ backgroundColor: 'var(--border)' }} />
              </div>
            ))
          ) : (
            (group.members || []).map((member) => (
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
                {isAdmin && member.role !== 'admin' && (
                  <button
                    onClick={() => onRemoveMember(member.user_id)}
                    className="p-1.5 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors"
                    aria-label="Remove member"
                    title="Remove member"
                  >
                    <X className="w-4 h-4" style={{ color: 'var(--error)' }} />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

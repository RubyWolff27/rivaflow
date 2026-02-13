import { useState, useEffect } from 'react';
import { friendsApi, socialApi } from '../api/client';
import type { Friend } from '../types';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Edit2, Trash2, Award, Filter, Search, UserCheck, X } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';

interface PendingRequest {
  id: number;
  requester_id: number;
  requester_first_name: string;
  requester_last_name: string;
  requester_email: string;
  requester_avatar_url?: string;
  requested_at: string;
}

const BELT_STYLES: Record<string, React.CSSProperties> = {
  white: { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', borderColor: 'var(--border)' },
  blue: { backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'rgb(96, 165, 250)', borderColor: 'rgba(59, 130, 246, 0.3)' },
  purple: { backgroundColor: 'rgba(168, 85, 247, 0.15)', color: 'rgb(192, 132, 252)', borderColor: 'rgba(168, 85, 247, 0.3)' },
  brown: { backgroundColor: 'rgba(180, 120, 60, 0.15)', color: 'rgb(200, 150, 80)', borderColor: 'rgba(180, 120, 60, 0.3)' },
  black: { backgroundColor: 'rgba(0, 0, 0, 0.6)', color: '#fff', borderColor: 'rgba(100, 100, 100, 0.5)' },
};

export default function Friends() {
  const navigate = useNavigate();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [filteredFriends, setFilteredFriends] = useState<Friend[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingFriend, setEditingFriend] = useState<Friend | null>(null);
  const [friendToDelete, setFriendToDelete] = useState<number | null>(null);
  const [pendingRequests, setPendingRequests] = useState<PendingRequest[]>([]);
  const [requestActionLoading, setRequestActionLoading] = useState<number | null>(null);
  const toast = useToast();

  const [formData, setFormData] = useState({
    name: '',
    friend_type: 'training-partner' as 'instructor' | 'training-partner' | 'both',
    belt_rank: '' as '' | 'white' | 'blue' | 'purple' | 'brown' | 'black',
    belt_stripes: 0,
    instructor_certification: '',
    phone: '',
    email: '',
    notes: '',
  });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await friendsApi.list();
        if (!cancelled) {
          const data = response.data as any;
          setFriends(data.friends || data || []);
        }
      } catch (error) {
        if (!cancelled) console.error('Error loading contacts:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  // Load pending friend requests
  useEffect(() => {
    let cancelled = false;
    const loadRequests = async () => {
      try {
        const res = await socialApi.getReceivedRequests();
        if (!cancelled) setPendingRequests(res.data.requests || []);
      } catch {
        // Best-effort
      }
    };
    loadRequests();
    return () => { cancelled = true; };
  }, []);

  const handleAcceptRequest = async (request: PendingRequest) => {
    try {
      setRequestActionLoading(request.id);
      await socialApi.acceptFriendRequest(request.id);
      setPendingRequests((prev) => prev.filter((r) => r.id !== request.id));
      toast.success(`You and ${request.requester_first_name} are now friends!`);
    } catch {
      toast.error('Failed to accept friend request');
    } finally {
      setRequestActionLoading(null);
    }
  };

  const handleDeclineRequest = async (request: PendingRequest) => {
    try {
      setRequestActionLoading(request.id);
      await socialApi.declineFriendRequest(request.id);
      setPendingRequests((prev) => prev.filter((r) => r.id !== request.id));
      toast.success('Friend request declined');
    } catch {
      toast.error('Failed to decline friend request');
    } finally {
      setRequestActionLoading(null);
    }
  };

  useEffect(() => {
    filterFriends();
  }, [friends, selectedFilter]);

  const loadFriends = async () => {
    setLoading(true);
    try {
      const response = await friendsApi.list();
      // API returns {friends: [], total: 0}, extract the friends array
      const data = response.data as any;
      setFriends(data.friends || data || []);
    } catch (error) {
      console.error('Error loading contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterFriends = () => {
    let filtered = [...friends];

    if (selectedFilter === 'instructors') {
      filtered = filtered.filter(c => c.friend_type === 'instructor' || c.friend_type === 'both');
    } else if (selectedFilter === 'partners') {
      filtered = filtered.filter(c => c.friend_type === 'training-partner' || c.friend_type === 'both');
    }

    setFilteredFriends(filtered);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingFriend) {
        await friendsApi.update(editingFriend.id, {
          name: formData.name,
          friend_type: formData.friend_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      } else {
        await friendsApi.create({
          name: formData.name,
          friend_type: formData.friend_type,
          belt_rank: formData.belt_rank || undefined,
          belt_stripes: formData.belt_stripes,
          instructor_certification: formData.instructor_certification || undefined,
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          notes: formData.notes || undefined,
        });
      }

      resetForm();
      await loadFriends();
      toast.success(editingFriend ? 'Friend updated successfully' : 'Friend added successfully');
    } catch (error) {
      console.error('Error saving contact:', error);
      toast.error('Failed to save friend.');
    }
  };

  const handleEdit = (friend: Friend) => {
    setEditingFriend(friend);
    setFormData({
      name: friend.name,
      friend_type: friend.friend_type,
      belt_rank: friend.belt_rank || '',
      belt_stripes: friend.belt_stripes || 0,
      instructor_certification: friend.instructor_certification || '',
      phone: friend.phone || '',
      email: friend.email || '',
      notes: friend.notes || '',
    });
    setShowAddForm(true);
  };

  const handleDelete = async () => {
    if (!friendToDelete) return;

    try {
      await friendsApi.delete(friendToDelete);
      await loadFriends();
      toast.success('Friend deleted successfully');
    } catch (error) {
      console.error('Error deleting friend:', error);
      toast.error('Failed to delete friend.');
    } finally {
      setFriendToDelete(null);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      friend_type: 'training-partner',
      belt_rank: '',
      belt_stripes: 0,
      instructor_certification: '',
      phone: '',
      email: '',
      notes: '',
    });
    setEditingFriend(null);
    setShowAddForm(false);
  };

  const renderBeltBadge = (friend: Friend) => {
    if (!friend.belt_rank) return null;

    const style = BELT_STYLES[friend.belt_rank];
    const stripes = friend.belt_stripes || 0;

    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border" style={style}>
        {friend.belt_rank.charAt(0).toUpperCase() + friend.belt_rank.slice(1)} Belt
        {stripes > 0 && (
          <span className="flex gap-0.5 ml-1">
            {Array.from({ length: stripes }).map((_, i) => (
              <div key={i} className="w-1 h-3 bg-current opacity-70" />
            ))}
          </span>
        )}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <CardSkeleton key={i} lines={2} />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="w-8 h-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-3xl font-bold">Friends</h1>
            <p className="text-[var(--muted)]">
              {filteredFriends.length} of {friends.length} friends
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/find-friends')}
            className="btn-secondary flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Discover
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            {showAddForm ? 'Cancel' : 'Add Friend'}
          </button>
        </div>
      </div>

      {/* Pending Friend Requests */}
      {pendingRequests.length > 0 && (
        <div className="card bg-[var(--surface)] border border-[var(--accent)]/20">
          <h3 className="text-lg font-semibold text-[var(--text)] mb-3">
            Friend Requests ({pendingRequests.length})
          </h3>
          <div className="space-y-3">
            {pendingRequests.map((request) => (
              <div
                key={request.id}
                className="flex items-center justify-between p-3 rounded-[14px] bg-[var(--surfaceElev)]"
              >
                <div
                  className="flex items-center gap-3 cursor-pointer flex-1"
                  onClick={() => navigate(`/users/${request.requester_id}`)}
                >
                  {request.requester_avatar_url ? (
                    <img
                      src={request.requester_avatar_url}
                      alt={request.requester_first_name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                      style={{ background: 'linear-gradient(135deg, var(--accent), #FF8C42)' }}
                    >
                      {request.requester_first_name?.charAt(0) || '?'}
                    </div>
                  )}
                  <div>
                    <p className="font-medium text-[var(--text)]">
                      {request.requester_first_name} {request.requester_last_name}
                    </p>
                    <p className="text-xs text-[var(--muted)]">
                      Sent {new Date(request.requested_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAcceptRequest(request)}
                    disabled={requestActionLoading === request.id}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
                    style={{ backgroundColor: 'var(--accent)' }}
                  >
                    <UserCheck className="w-4 h-4" />
                    Accept
                  </button>
                  <button
                    onClick={() => handleDeclineRequest(request)}
                    disabled={requestActionLoading === request.id}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--muted)] bg-[var(--surface)] hover:opacity-80 disabled:opacity-50 border border-[var(--border)]"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add/Edit Form */}
      {showAddForm && (
        <form onSubmit={handleSubmit} className="card bg-[var(--surfaceElev)] space-y-4">
          <h3 className="text-lg font-semibold">
            {editingFriend ? 'Edit Friend' : 'Add New Friend'}
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Name *</label>
              <input
                type="text"
                className="input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Type</label>
              <select
                className="input"
                value={formData.friend_type}
                onChange={(e) => setFormData({ ...formData, friend_type: e.target.value as any })}
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
                onChange={(e) => setFormData({ ...formData, belt_rank: e.target.value as any })}
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
                onChange={(e) => setFormData({ ...formData, belt_stripes: parseInt(e.target.value) || 0 })}
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
                onChange={(e) => setFormData({ ...formData, instructor_certification: e.target.value })}
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
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="label">Notes</label>
            <textarea
              className="input"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={2}
            />
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">
              {editingFriend ? 'Update Friend' : 'Add Friend'}
            </button>
            <button type="button" onClick={resetForm} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-[var(--muted)]" />
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'all'
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--surfaceElev)] text-[var(--text)] hover:opacity-80'
              }`}
            >
              All ({friends.length})
            </button>
            <button
              onClick={() => setSelectedFilter('instructors')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'instructors'
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--surfaceElev)] text-[var(--text)] hover:opacity-80'
              }`}
            >
              Instructors ({friends.filter(c => c.friend_type === 'instructor' || c.friend_type === 'both').length})
            </button>
            <button
              onClick={() => setSelectedFilter('partners')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilter === 'partners'
                  ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--surfaceElev)] text-[var(--text)] hover:opacity-80'
              }`}
            >
              Training Partners ({friends.filter(c => c.friend_type === 'training-partner' || c.friend_type === 'both').length})
            </button>
          </div>
        </div>
      </div>

      {/* Contacts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredFriends.map(friend => (
          <div key={friend.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-[var(--text)]">
                  {friend.name}
                </h3>
                <p className="text-sm text-[var(--muted)] capitalize">
                  {friend.friend_type.replace('-', ' ')}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(friend)}
                  className="text-[var(--accent)] hover:opacity-80"
                  title="Edit friend"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setFriendToDelete(friend.id)}
                  className="text-[var(--error)] hover:opacity-80"
                  title="Delete friend"
                  aria-label="Delete friend"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2">
              {renderBeltBadge(friend)}

              {friend.instructor_certification && (
                <div className="flex items-center gap-1 text-sm text-[var(--muted)]">
                  <Award className="w-4 h-4" />
                  <span>{friend.instructor_certification}</span>
                </div>
              )}

              {friend.phone && (
                <p className="text-sm text-[var(--muted)]">
                  📱 {friend.phone}
                </p>
              )}

              {friend.email && (
                <p className="text-sm text-[var(--muted)]">
                  📧 {friend.email}
                </p>
              )}

              {friend.notes && (
                <p className="text-sm text-[var(--muted)] italic">
                  {friend.notes}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredFriends.length === 0 && (
        <div className="text-center py-12 text-[var(--muted)]">
          No friends found. Add your first friend to get started!
        </div>
      )}

      <ConfirmDialog
        isOpen={friendToDelete !== null}
        onClose={() => setFriendToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Friend"
        message="Are you sure you want to delete this friend? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

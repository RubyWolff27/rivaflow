import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { friendsApi, socialApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Friend } from '../types';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Search, Filter } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton, EmptyState } from '../components/ui';
import FriendCard from '../components/friends/FriendCard';
import FriendRequestCard, { SocialFriendsList } from '../components/friends/FriendRequestCard';
import type { PendingRequest, SocialFriend } from '../components/friends/FriendRequestCard';
import FriendForm from '../components/friends/FriendForm';
import type { FriendFormData } from '../components/friends/FriendForm';

export default function Friends() {
  usePageTitle('Friends');
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
  const [socialFriends, setSocialFriends] = useState<SocialFriend[]>([]);
  const toast = useToast();

  const [formData, setFormData] = useState<FriendFormData>({
    name: '',
    friend_type: 'training-partner',
    belt_rank: '',
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
        if (!cancelled) {
          logger.error('Error loading contacts:', error);
          toast.error('Failed to load friends');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  // Load pending friend requests and social friends
  useEffect(() => {
    let cancelled = false;
    const loadSocial = async () => {
      try {
        const [requestsRes, friendsRes] = await Promise.allSettled([
          socialApi.getReceivedRequests(),
          socialApi.getFriends(),
        ]);
        if (cancelled) return;
        if (requestsRes.status === 'fulfilled') {
          setPendingRequests(requestsRes.value.data.requests || []);
        }
        if (friendsRes.status === 'fulfilled') {
          setSocialFriends(friendsRes.value.data.friends || []);
        }
      } catch {
        // Best-effort
      }
    };
    loadSocial();
    return () => { cancelled = true; };
  }, []);

  const handleAcceptRequest = async (request: PendingRequest) => {
    try {
      setRequestActionLoading(request.id);
      await socialApi.acceptFriendRequest(request.id);
      setPendingRequests((prev) => prev.filter((r) => r.id !== request.id));
      setSocialFriends((prev) => [...prev, {
        id: request.requester_id,
        first_name: request.requester_first_name,
        last_name: request.requester_last_name,
        avatar_url: request.requester_avatar_url,
        friends_since: new Date().toISOString(),
      }]);
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
      const data = response.data as any;
      setFriends(data.friends || data || []);
    } catch (error) {
      logger.error('Error loading contacts:', error);
      toast.error('Failed to load friends');
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
      logger.error('Error saving contact:', error);
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
      logger.error('Error deleting friend:', error);
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
      <FriendRequestCard
        pendingRequests={pendingRequests}
        requestActionLoading={requestActionLoading}
        onAccept={handleAcceptRequest}
        onDecline={handleDeclineRequest}
      />

      {/* Social Friends (RivaFlow users) */}
      <SocialFriendsList socialFriends={socialFriends} />

      {/* Add/Edit Form */}
      {showAddForm && (
        <FriendForm
          formData={formData}
          onFormDataChange={setFormData}
          onSubmit={handleSubmit}
          onCancel={resetForm}
          isEditing={!!editingFriend}
        />
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
          <FriendCard
            key={friend.id}
            friend={friend}
            onEdit={handleEdit}
            onDelete={setFriendToDelete}
          />
        ))}
      </div>

      {filteredFriends.length === 0 && (
        <EmptyState
          icon={Users}
          title="No friends found"
          description="Add your first friend to get started!"
        />
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

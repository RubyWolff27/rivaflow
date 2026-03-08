import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { friendsApi, socialApi, analyticsApi } from '../api/client';
import { logger } from '../utils/logger';
import type { Friend } from '../types';
import type { PartnersData } from '../components/analytics/reportTypes';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Search, Filter, Activity, Target, Calendar } from 'lucide-react';
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
  const [partnersData, setPartnersData] = useState<PartnersData | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
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
          const data = response.data as Friend[] | { friends: Friend[] };
          setFriends(Array.isArray(data) ? data : data.friends || []);
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
      } catch (err) {
        logger.debug('Social data load best-effort', err);
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
    } catch (err) {
      logger.warn('Failed to accept friend request', err);
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
    } catch (err) {
      logger.warn('Failed to decline friend request', err);
      toast.error('Failed to decline friend request');
    } finally {
      setRequestActionLoading(null);
    }
  };

  // Load partner stats for the stats banner
  useEffect(() => {
    let cancelled = false;
    const loadStats = async () => {
      try {
        const res = await analyticsApi.partnerStats();
        if (!cancelled) setPartnersData(res.data ?? null);
      } catch (err) {
        logger.debug('Partner stats not available', err);
      } finally {
        if (!cancelled) setStatsLoading(false);
      }
    };
    loadStats();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    filterFriends();
  }, [friends, selectedFilter]);

  const loadFriends = async () => {
    setLoading(true);
    try {
      const response = await friendsApi.list();
      const data = response.data as Friend[] | { friends: Friend[] };
      setFriends(Array.isArray(data) ? data : data.friends || []);
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
              {filteredFriends.length === friends.length
                ? `${friends.length} Friends`
                : `${filteredFriends.length} of ${friends.length} Friends`}
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

      {/* Training Stats Banner */}
      {statsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} lines={1} />)}
        </div>
      ) : partnersData && (partnersData.summary?.total_rolls ?? 0) > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Active Partners</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
              {partnersData.diversity_metrics?.active_partners ?? 0}
            </p>
          </div>
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Total Rolls</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
              {partnersData.summary?.total_rolls ?? 0}
            </p>
          </div>
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs For</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
              {partnersData.summary?.total_submissions_for ?? 0}
            </p>
          </div>
          <div className="p-4 rounded-[14px]" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4" style={{ color: 'var(--muted)' }} />
              <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Subs Against</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
              {partnersData.summary?.total_submissions_against ?? 0}
            </p>
          </div>
        </div>
      ) : null}

      {/* Top Training Partners */}
      {partnersData?.top_partners && partnersData.top_partners.length > 0 && (
        <div className="rounded-[14px] p-5" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
          <div className="mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Top Training Partners</h2>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>Most frequent partners (last 30 days)</p>
          </div>
          <div className="space-y-3">
            {partnersData.top_partners.slice(0, 5).map((partner, index) => (
              <div
                key={partner.id ?? index}
                className="p-4 rounded-[14px]"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold"
                      style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
                    >
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium" style={{ color: 'var(--text)' }}>{partner.name ?? 'Unknown'}</p>
                      {partner.belt_rank && (
                        <p className="text-xs capitalize" style={{ color: 'var(--muted)' }}>{partner.belt_rank}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                      {partner.total_rolls ?? 0} {(partner.total_rolls ?? 0) === 1 ? 'roll' : 'rolls'}
                    </p>
                    {partner.last_rolled_date && (
                      <p className="text-xs flex items-center justify-end gap-1 mt-0.5" style={{ color: 'var(--muted)' }}>
                        <Calendar className="w-3 h-3" />
                        {new Date(partner.last_rolled_date + 'T00:00:00').toLocaleDateString('en-AU', { day: 'numeric', month: 'short' })}
                      </p>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                  <div>
                    <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs For</p>
                    <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{partner.submissions_for ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs" style={{ color: 'var(--muted)' }}>Subs Against</p>
                    <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{partner.submissions_against ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs" style={{ color: 'var(--muted)' }}>Ratio</p>
                    <p className="text-sm font-medium" style={{ color: (partner.sub_ratio ?? 0) >= 1 ? 'var(--accent)' : 'var(--text)' }}>
                      {partner.sub_ratio != null ? partner.sub_ratio.toFixed(2) : '0.00'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
          <div className="flex gap-2" role="tablist" aria-label="Friend type filter">
            <button
              onClick={() => setSelectedFilter('all')}
              role="tab"
              aria-selected={selectedFilter === 'all'}
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
              role="tab"
              aria-selected={selectedFilter === 'instructors'}
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
              role="tab"
              aria-selected={selectedFilter === 'partners'}
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
          description={friends.length > 0
            ? `No ${selectedFilter} found. Try a different filter.`
            : 'Add your first friend to get started!'}
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

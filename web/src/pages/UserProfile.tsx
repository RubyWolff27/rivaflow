import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { usersApi, socialApi } from '../api/client';
import { logger } from '../utils/logger';
import { Users, MapPin, Calendar, TrendingUp, Activity, UserCheck, UserPlus, Clock } from 'lucide-react';
import { useToast } from '../contexts/ToastContext';
import { useAuth } from '../contexts/AuthContext';
import { CardSkeleton } from '../components/ui';

interface UserProfileData {
  id: number;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  current_grade?: string;
  default_gym?: string;
  location?: string;
  state?: string;
  follower_count?: number;
  following_count?: number;
  is_following?: boolean;
  is_followed_by?: boolean;
  [key: string]: unknown;
}

interface UserStats {
  total_sessions?: number;
  total_hours?: number;
  total_rolls?: number;
  sessions_this_week?: number;
  [key: string]: unknown;
}

interface ActivityItem {
  id?: number;
  type?: string;
  date?: string;
  summary?: string;
  [key: string]: unknown;
}

// 'none' | 'pending_sent' | 'pending_received' | 'friends'
type FriendshipStatus = 'none' | 'pending_sent' | 'pending_received' | 'friends';

export default function UserProfile() {
  usePageTitle('User Profile');
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();

  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [friendshipStatus, setFriendshipStatus] = useState<FriendshipStatus>('none');
  const toast = useToast();

  useEffect(() => {
    if (!userId) {
      navigate('/feed');
      return;
    }

    let cancelled = false;
    const doLoad = async () => {
      try {
        setLoading(true);
        setError('');

        // Load profile (required)
        const profileRes = await usersApi.getProfile(parseInt(userId!));
        if (cancelled) return;
        setProfile(profileRes.data);

        // Load stats and activity in parallel (best-effort)
        const [statsRes, activityRes] = await Promise.allSettled([
          usersApi.getStats(parseInt(userId!)),
          usersApi.getActivity(parseInt(userId!)),
        ]);
        if (!cancelled) {
          if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
          if (activityRes.status === 'fulfilled') setActivity(activityRes.value.data?.items || []);
        }

        // Load friendship status (best-effort, not needed for own profile)
        try {
          const statusRes = await socialApi.getFriendshipStatus(parseInt(userId!));
          if (!cancelled) {
            setFriendshipStatus(statusRes.data.status as FriendshipStatus);
          }
        } catch {
          // Ignore — defaults to 'none'
        }
      } catch (err: unknown) {
        if (!cancelled) {
          logger.error('Error loading user profile:', err);
          const e = err as { response?: { data?: { detail?: string } } };
          setError(e.response?.data?.detail || 'Failed to load user profile');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [userId]);

  const handleAddFriend = async () => {
    if (!profile) return;

    try {
      setActionLoading(true);
      // Send friend request + follow
      await socialApi.sendFriendRequest(profile.id, { connection_source: 'profile' });
      // Also follow them so their activity shows in feed
      if (!profile.is_following) {
        try {
          await socialApi.follow(profile.id);
          setProfile({ ...profile, is_following: true, follower_count: (profile.follower_count ?? 0) + 1 });
        } catch {
          // Follow is best-effort
        }
      }
      setFriendshipStatus('pending_sent');
      toast.success('Friend request sent!');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      const msg = e.response?.data?.detail || 'Failed to send friend request';
      logger.error('Failed to send friend request:', err);
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAcceptRequest = async () => {
    if (!profile) return;

    try {
      setActionLoading(true);
      // We need the connection ID — get it from received requests
      const receivedRes = await socialApi.getReceivedRequests();
      const pending = receivedRes.data.requests?.find(
        (r: { requester_id: number; id: number }) => r.requester_id === profile.id
      );
      if (pending) {
        await socialApi.acceptFriendRequest(pending.id);
        setFriendshipStatus('friends');
        toast.success('Friend request accepted!');
      }
    } catch (err: unknown) {
      logger.error('Failed to accept friend request:', err);
      toast.error('Failed to accept friend request');
    } finally {
      setActionLoading(false);
    }
  };

  const getBeltStyle = (grade: string): React.CSSProperties => {
    const beltStyles: Record<string, React.CSSProperties> = {
      white: { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', borderColor: 'var(--border)' },
      blue: { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)', borderColor: 'var(--accent)' },
      purple: { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7', borderColor: '#a855f7' },
      brown: { backgroundColor: 'rgba(245,158,11,0.1)', color: '#d97706', borderColor: '#d97706' },
      black: { backgroundColor: '#111827', color: '#fff', borderColor: '#374151' },
    };

    for (const [belt, style] of Object.entries(beltStyles)) {
      if (grade?.toLowerCase().includes(belt)) {
        return style;
      }
    }

    return { backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)', borderColor: 'var(--border)' };
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderActionButton = () => {
    // Don't show action button on your own profile
    const isOwnProfile = currentUser && profile && currentUser.id === profile.id;
    if (isOwnProfile) return null;

    if (actionLoading) {
      return (
        <button
          disabled
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-[var(--surfaceElev)] text-[var(--muted)] opacity-50"
        >
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-[var(--muted)] border-t-transparent"></div>
          <span>...</span>
        </button>
      );
    }

    switch (friendshipStatus) {
      case 'friends':
        return (
          <span className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-green-500/10 text-green-400 border border-green-500/20">
            <UserCheck className="w-4 h-4" />
            Friends
          </span>
        );

      case 'pending_sent':
        return (
          <span className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-[var(--surfaceElev)] text-[var(--muted)]">
            <Clock className="w-4 h-4" />
            Request Sent
          </span>
        );

      case 'pending_received':
        return (
          <button
            onClick={handleAcceptRequest}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-[var(--accent)] text-white hover:opacity-90"
          >
            <UserCheck className="w-4 h-4" />
            Accept Request
          </button>
        );

      default:
        return (
          <button
            onClick={handleAddFriend}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-[var(--accent)] text-white hover:opacity-90"
          >
            <UserPlus className="w-4 h-4" />
            Add Friend
          </button>
        );
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <CardSkeleton />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <CardSkeleton />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          <p className="font-semibold">Error</p>
          <p>{error || 'User not found'}</p>
          <button
            onClick={() => navigate('/feed')}
            className="mt-4 text-sm underline"
          >
            Back to Feed
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Profile Header */}
      <div className="bg-[var(--surface)] rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt={`${profile.first_name} ${profile.last_name}`}
                className="w-20 h-20 rounded-full object-cover border-2 border-[var(--border)]"
              />
            ) : (
              <div className="w-20 h-20 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                {profile.first_name?.[0] ?? 'U'}{profile.last_name?.[0] ?? '?'}
              </div>
            )}
            <div>
              <h1 className="text-3xl font-bold text-[var(--text)]">
                {profile.first_name ?? 'Unknown'} {profile.last_name ?? 'User'}
              </h1>
              <div className="flex items-center gap-4 mt-2 text-sm text-[var(--muted)]">
                {profile.current_grade && (
                  <span className="px-3 py-1 rounded-full border" style={getBeltStyle(profile.current_grade)}>
                    {profile.current_grade}
                  </span>
                )}
                {profile.default_gym && (
                  <span className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {profile.default_gym}
                  </span>
                )}
                {(profile.location ?? profile.state) && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {[profile.location, profile.state].filter(Boolean).join(', ')}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4 mt-3 text-sm">
                <span className="text-[var(--text)]">
                  <strong>{profile.follower_count ?? 0}</strong> followers
                </span>
                <span className="text-[var(--text)]">
                  <strong>{profile.following_count ?? 0}</strong> following
                </span>
                {profile.is_followed_by && (
                  <span className="text-xs bg-[var(--surfaceElev)] text-[var(--muted)] px-2 py-1 rounded">
                    Follows you
                  </span>
                )}
              </div>
            </div>
          </div>

          {renderActionButton()}
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-[var(--surface)] rounded-lg shadow-sm p-4">
            <div className="flex items-center gap-2 text-[var(--muted)] mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-sm">Total Sessions</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text)]">{stats.total_sessions ?? 0}</p>
          </div>

          <div className="bg-[var(--surface)] rounded-lg shadow-sm p-4">
            <div className="flex items-center gap-2 text-[var(--muted)] mb-1">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">Total Hours</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text)]">{stats.total_hours ?? 0}</p>
          </div>

          <div className="bg-[var(--surface)] rounded-lg shadow-sm p-4">
            <div className="flex items-center gap-2 text-[var(--muted)] mb-1">
              <Users className="w-4 h-4" />
              <span className="text-sm">Total Rolls</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text)]">{stats.total_rolls ?? 0}</p>
          </div>

          <div className="bg-[var(--surface)] rounded-lg shadow-sm p-4">
            <div className="flex items-center gap-2 text-[var(--muted)] mb-1">
              <Calendar className="w-4 h-4" />
              <span className="text-sm">This Week</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text)]">{stats.sessions_this_week ?? 0}</p>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-[var(--surface)] rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-bold text-[var(--text)] mb-4">Recent Activity</h2>

        {activity.length === 0 ? (
          <p className="text-[var(--muted)] text-center py-8">
            No public activity to display
          </p>
        ) : (
          <div className="space-y-4">
            {activity.map((item) => (
              <div
                key={`${item.type}-${item.id}`}
                className="border-l-4 border-primary-500 pl-4 py-2"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[var(--muted)]">
                      {formatDate(item.date!)}
                    </p>
                    <p className="text-[var(--text)]">{item.summary}</p>
                  </div>
                  <span className="text-xs bg-[var(--surfaceElev)] text-[var(--muted)] px-2 py-1 rounded">
                    {item.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

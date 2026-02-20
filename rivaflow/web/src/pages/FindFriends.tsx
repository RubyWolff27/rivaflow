import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { socialApi } from '../api/client';
import { logger } from '../utils/logger';
import { UserPlus, UserMinus, Search, X, Users, MapPin, Dumbbell } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';
import { FriendSuggestions } from '../components/FriendSuggestions';
import { useToast } from '../contexts/ToastContext';

interface SearchUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  is_following?: boolean;
  friendship_status?: 'none' | 'friends' | 'pending_sent' | 'pending_received';
  connection_id?: number;
}

interface RecommendedUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  reason: string;
  score: number;
  friendship_status?: 'none' | 'friends' | 'pending_sent' | 'pending_received';
}

type DiscoveryTab = 'search' | 'gym' | 'suggestions';

export default function FindFriends() {
  usePageTitle('Find Friends');
  const navigate = useNavigate();
  const [searchResults, setSearchResults] = useState<SearchUser[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<DiscoveryTab>('suggestions');
  const [recommended, setRecommended] = useState<RecommendedUser[]>([]);
  const [loadingRecommended, setLoadingRecommended] = useState(false);
  const toast = useToast();

  useEffect(() => {
    let cancelled = false;
    if (searchQuery.length >= 2) {
      setActiveTab('search');
      const doSearch = async () => {
        try {
          const response = await socialApi.searchUsers(searchQuery);
          if (cancelled) return;
          const users = response.data.users || [];
          const usersWithStatus = await Promise.all(
            users.map(async (user: SearchUser) => {
              try {
                const statusResponse = await socialApi.getFriendshipStatus(user.id);
                return { ...user, friendship_status: statusResponse.data.status };
              } catch (err) {
                logger.debug('Friendship status unavailable for user', err);
                return { ...user, friendship_status: 'none' };
              }
            })
          );
          if (!cancelled) setSearchResults(usersWithStatus);
        } catch (error) {
          if (!cancelled) {
            logger.error('Error searching users:', error);
            toast.error('Failed to search users');
          }
        }
      };
      doSearch();
    } else {
      setSearchResults([]);
      if (activeTab === 'search') {
        setActiveTab('suggestions');
      }
    }
    return () => { cancelled = true; };
  }, [searchQuery]);

  useEffect(() => {
    let cancelled = false;
    if (activeTab === 'gym' && recommended.length === 0) {
      const doLoad = async () => {
        setLoadingRecommended(true);
        try {
          const response = await socialApi.getRecommended();
          if (cancelled) return;
          const recs = response.data.recommendations || [];
          const recsWithStatus = await Promise.all(
            recs.map(async (user: RecommendedUser) => {
              try {
                const statusResponse = await socialApi.getFriendshipStatus(user.id);
                return { ...user, friendship_status: statusResponse.data.status };
              } catch (err) {
                logger.debug('Friendship status unavailable for recommended user', err);
                return { ...user, friendship_status: 'none' };
              }
            })
          );
          if (!cancelled) setRecommended(recsWithStatus);
        } catch (error) {
          if (!cancelled) {
            logger.error('Error loading recommendations:', error);
            toast.error('Failed to load recommendations');
          }
        } finally {
          if (!cancelled) setLoadingRecommended(false);
        }
      };
      doLoad();
    }
    return () => { cancelled = true; };
  }, [activeTab]);

  const handleSendRequest = async (userId: number, source: 'search' | 'recommendation' = 'search') => {
    try {
      await socialApi.sendFriendRequest(userId, { connection_source: source });
      toast.success('Friend request sent');
      updateUserStatus(userId, 'pending_sent');
    } catch (error: unknown) {
      logger.error('Error sending friend request:', error);
      const e = error as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Failed to send friend request');
    }
  };

  const handleAcceptRequest = async (userId: number) => {
    try {
      const receivedResponse = await socialApi.getReceivedRequests();
      const request = receivedResponse.data.requests.find((r: { requester_id: number; id: number }) => r.requester_id === userId);

      if (request) {
        await socialApi.acceptFriendRequest(request.id);
        toast.success('Friend request accepted');
        updateUserStatus(userId, 'friends');
      }
    } catch (error) {
      logger.error('Error accepting friend request:', error);
      toast.error('Failed to accept friend request');
    }
  };

  const handleDeclineRequest = async (userId: number) => {
    try {
      const receivedResponse = await socialApi.getReceivedRequests();
      const request = receivedResponse.data.requests.find((r: { requester_id: number; id: number }) => r.requester_id === userId);

      if (request) {
        await socialApi.declineFriendRequest(request.id);
        toast.success('Friend request declined');
        updateUserStatus(userId, 'none');
      }
    } catch (error) {
      logger.error('Error declining friend request:', error);
      toast.error('Failed to decline friend request');
    }
  };

  const handleUnfriend = async (userId: number) => {
    try {
      await socialApi.unfriend(userId);
      toast.success('Friend removed');
      updateUserStatus(userId, 'none');
    } catch (error) {
      logger.error('Error removing friend:', error);
      toast.error('Failed to remove friend');
    }
  };

  const updateUserStatus = (userId: number, status: SearchUser['friendship_status']) => {
    setSearchResults((prev) =>
      prev.map((user) =>
        user.id === userId ? { ...user, friendship_status: status } : user
      )
    );
    setRecommended((prev) =>
      prev.map((user) =>
        user.id === userId ? { ...user, friendship_status: status } : user
      )
    );
  };

  const renderFriendshipActions = (user: { id: number; friendship_status?: string }, source: 'search' | 'recommendation' = 'search') => {
    if (user.friendship_status === 'friends') {
      return (
        <SecondaryButton onClick={() => handleUnfriend(user.id)} className="flex items-center gap-2">
          <UserMinus className="w-4 h-4" />
          Unfriend
        </SecondaryButton>
      );
    }
    if (user.friendship_status === 'pending_sent') {
      return (
        <SecondaryButton disabled className="flex items-center gap-2 opacity-60 cursor-not-allowed">
          <UserPlus className="w-4 h-4" />
          Request Sent
        </SecondaryButton>
      );
    }
    if (user.friendship_status === 'pending_received') {
      return (
        <div className="flex items-center gap-2">
          <PrimaryButton onClick={() => handleAcceptRequest(user.id)} className="text-sm px-3 py-1">
            Accept
          </PrimaryButton>
          <SecondaryButton onClick={() => handleDeclineRequest(user.id)} className="text-sm px-3 py-1">
            <X className="w-4 h-4" />
          </SecondaryButton>
        </div>
      );
    }
    return (
      <PrimaryButton onClick={() => handleSendRequest(user.id, source)} className="flex items-center gap-2">
        <UserPlus className="w-4 h-4" />
        Add Friend
      </PrimaryButton>
    );
  };

  const tabs: { key: DiscoveryTab; label: string; icon: React.ReactNode }[] = [
    { key: 'suggestions', label: 'For You', icon: <Users className="w-4 h-4" /> },
    { key: 'gym', label: 'At Your Gym', icon: <Dumbbell className="w-4 h-4" /> },
    { key: 'search', label: 'Search', icon: <Search className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
          Find Friends
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Connect with athletes at your gym
        </p>
      </div>

      {/* Search */}
      <Card>
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5" style={{ color: 'var(--muted)' }} />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input flex-1"
          />
        </div>
      </Card>

      {/* Discovery Tabs */}
      {!searchQuery && (
        <div className="flex gap-2">
          {tabs.filter(t => t.key !== 'search').map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-white'
                  : 'text-[var(--text)] hover:bg-[var(--surfaceElev)]'
              }`}
              style={activeTab === tab.key ? { backgroundColor: 'var(--accent)' } : { backgroundColor: 'var(--surfaceElev)' }}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Search Results */}
      {activeTab === 'search' && searchResults.length > 0 && (
        <Card>
          <div className="mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Search Results
            </h2>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
            </p>
          </div>
          <div className="space-y-3">
            {searchResults.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 rounded-[14px]"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <div
                  className="flex items-center gap-3 cursor-pointer flex-1"
                  onClick={() => navigate(`/users/${user.id}`)}
                >
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                    style={{ background: 'linear-gradient(135deg, var(--accent), #FF8C42)' }}
                  >
                    {user.first_name?.charAt(0) || '?'}
                  </div>
                  <div>
                    <p className="font-medium" style={{ color: 'var(--text)' }}>
                      {user.first_name} {user.last_name}
                    </p>
                    <p className="text-sm" style={{ color: 'var(--muted)' }}>
                      {user.email}
                    </p>
                  </div>
                </div>
                {renderFriendshipActions(user)}
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'search' && searchQuery && searchResults.length === 0 && (
        <Card className="p-8 text-center">
          <p style={{ color: 'var(--muted)' }}>No users found matching "{searchQuery}"</p>
        </Card>
      )}

      {/* At Your Gym */}
      {activeTab === 'gym' && (
        <div className="space-y-4">
          {loadingRecommended ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="p-4">
                  <div className="animate-pulse flex items-center space-x-4">
                    <div className="w-12 h-12 rounded-full" style={{ backgroundColor: 'var(--border)' }} />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 rounded w-1/3" style={{ backgroundColor: 'var(--border)' }} />
                      <div className="h-3 rounded w-1/2" style={{ backgroundColor: 'var(--border)' }} />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : recommended.length > 0 ? (
            <div className="space-y-3">
              {recommended.map((user) => (
                <Card key={user.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div
                      className="flex items-center gap-3 cursor-pointer flex-1"
                      onClick={() => navigate(`/users/${user.id}`)}
                    >
                      <div className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg"
                        style={{ background: 'linear-gradient(135deg, var(--accent), #FF8C42)' }}
                      >
                        {user.first_name?.charAt(0) || '?'}
                      </div>
                      <div>
                        <p className="font-semibold" style={{ color: 'var(--text)' }}>
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="text-sm flex items-center gap-1" style={{ color: 'var(--muted)' }}>
                          <MapPin className="w-3 h-3" />
                          {user.reason}
                        </p>
                      </div>
                    </div>
                    {renderFriendshipActions(user, 'recommendation')}
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <Dumbbell className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--muted)' }} />
              <p className="font-medium mb-1" style={{ color: 'var(--text)' }}>No gym recommendations yet</p>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>
                Log more sessions to get gym-based friend recommendations
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Friend Suggestions */}
      {activeTab === 'suggestions' && (
        <FriendSuggestions />
      )}
    </div>
  );
}

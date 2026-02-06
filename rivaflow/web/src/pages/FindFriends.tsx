import { useState, useEffect } from 'react';
import { socialApi } from '../api/client';
import { UserPlus, UserMinus, Search, X } from 'lucide-react';
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

export default function FindFriends() {
  const [searchResults, setSearchResults] = useState<SearchUser[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const toast = useToast();

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchUsers();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const searchUsers = async () => {
    try {
      const response = await socialApi.searchUsers(searchQuery);
      const users = response.data.users || [];

      // Fetch friendship status for each user
      const usersWithStatus = await Promise.all(
        users.map(async (user: any) => {
          try {
            const statusResponse = await socialApi.getFriendshipStatus(user.id);
            return {
              ...user,
              friendship_status: statusResponse.data.status,
            };
          } catch {
            return {
              ...user,
              friendship_status: 'none',
            };
          }
        })
      );

      setSearchResults(usersWithStatus);
    } catch (error) {
      console.error('Error searching users:', error);
    }
  };

  const handleSendRequest = async (userId: number) => {
    try {
      await socialApi.sendFriendRequest(userId, { connection_source: 'search' });
      toast.success('Friend request sent');
      // Update search results
      setSearchResults((prev) =>
        prev.map((user) =>
          user.id === userId ? { ...user, friendship_status: 'pending_sent' } : user
        )
      );
    } catch (error: any) {
      console.error('Error sending friend request:', error);
      toast.error(error.response?.data?.detail || 'Failed to send friend request');
    }
  };

  const handleAcceptRequest = async (userId: number) => {
    try {
      // We need to get the connection ID from received requests
      const receivedResponse = await socialApi.getReceivedRequests();
      const request = receivedResponse.data.requests.find((r: any) => r.requester_id === userId);

      if (request) {
        await socialApi.acceptFriendRequest(request.id);
        toast.success('Friend request accepted');
        setSearchResults((prev) =>
          prev.map((user) =>
            user.id === userId ? { ...user, friendship_status: 'friends' } : user
          )
        );
      }
    } catch (error) {
      console.error('Error accepting friend request:', error);
      toast.error('Failed to accept friend request');
    }
  };

  const handleDeclineRequest = async (userId: number) => {
    try {
      const receivedResponse = await socialApi.getReceivedRequests();
      const request = receivedResponse.data.requests.find((r: any) => r.requester_id === userId);

      if (request) {
        await socialApi.declineFriendRequest(request.id);
        toast.success('Friend request declined');
        setSearchResults((prev) =>
          prev.map((user) =>
            user.id === userId ? { ...user, friendship_status: 'none' } : user
          )
        );
      }
    } catch (error) {
      console.error('Error declining friend request:', error);
      toast.error('Failed to decline friend request');
    }
  };

  const handleUnfriend = async (userId: number) => {
    try {
      await socialApi.unfriend(userId);
      toast.success('Friend removed');
      setSearchResults((prev) =>
        prev.map((user) =>
          user.id === userId ? { ...user, friendship_status: 'none' } : user
        )
      );
    } catch (error) {
      console.error('Error removing friend:', error);
      toast.error('Failed to remove friend');
    }
  };

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

      {/* Search Results */}
      {searchResults.length > 0 && (
        <Card>
          <div className="mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Search Results
            </h2>
          </div>
          <div className="space-y-3">
            {searchResults.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 rounded-[14px]"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <div>
                  <p className="font-medium" style={{ color: 'var(--text)' }}>
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-sm" style={{ color: 'var(--muted)' }}>
                    {user.email}
                  </p>
                </div>
                {user.friendship_status === 'friends' ? (
                  <SecondaryButton onClick={() => handleUnfriend(user.id)} className="flex items-center gap-2">
                    <UserMinus className="w-4 h-4" />
                    Unfriend
                  </SecondaryButton>
                ) : user.friendship_status === 'pending_sent' ? (
                  <SecondaryButton disabled className="flex items-center gap-2 opacity-60 cursor-not-allowed">
                    <UserPlus className="w-4 h-4" />
                    Request Sent
                  </SecondaryButton>
                ) : user.friendship_status === 'pending_received' ? (
                  <div className="flex items-center gap-2">
                    <PrimaryButton onClick={() => handleAcceptRequest(user.id)} className="text-sm px-3 py-1">
                      Accept
                    </PrimaryButton>
                    <SecondaryButton onClick={() => handleDeclineRequest(user.id)} className="text-sm px-3 py-1">
                      <X className="w-4 h-4" />
                    </SecondaryButton>
                  </div>
                ) : (
                  <PrimaryButton onClick={() => handleSendRequest(user.id)} className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4" />
                    Add Friend
                  </PrimaryButton>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Friend Suggestions */}
      {!searchQuery && (
        <FriendSuggestions />
      )}
    </div>
  );
}

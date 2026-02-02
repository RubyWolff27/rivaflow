import { useState, useEffect } from 'react';
import { socialApi } from '../api/client';
import { UserPlus, UserMinus, Search } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';
import { FriendSuggestions } from '../components/FriendSuggestions';

interface SearchUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  is_following: boolean;
}

export default function FindFriends() {
  const [searchResults, setSearchResults] = useState<SearchUser[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

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
      setSearchResults(response.data.users || []);
    } catch (error) {
      console.error('Error searching users:', error);
    }
  };

  const handleFollow = async (userId: number) => {
    try {
      await socialApi.follow(userId);
      // Update search results
      setSearchResults((prev) =>
        prev.map((user) =>
          user.id === userId ? { ...user, is_following: true } : user
        )
      );
    } catch (error) {
      console.error('Error following user:', error);
    }
  };

  const handleUnfollow = async (userId: number) => {
    try {
      await socialApi.unfollow(userId);
      // Update search results
      setSearchResults((prev) =>
        prev.map((user) =>
          user.id === userId ? { ...user, is_following: false } : user
        )
      );
    } catch (error) {
      console.error('Error unfollowing user:', error);
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
                {user.is_following ? (
                  <SecondaryButton onClick={() => handleUnfollow(user.id)} className="flex items-center gap-2">
                    <UserMinus className="w-4 h-4" />
                    Unfollow
                  </SecondaryButton>
                ) : (
                  <PrimaryButton onClick={() => handleFollow(user.id)} className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4" />
                    Follow
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

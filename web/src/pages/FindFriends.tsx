import { useState, useEffect } from 'react';
import { socialApi } from '../api/client';
import { Users, UserPlus, UserMinus, Search } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';

interface RecommendedUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  reason: string;
  score: number;
}

interface SearchUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  is_following: boolean;
}

export default function FindFriends() {
  const [recommendations, setRecommendations] = useState<RecommendedUser[]>([]);
  const [searchResults, setSearchResults] = useState<SearchUser[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadRecommendations();
  }, []);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchUsers();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const response = await socialApi.getRecommended();
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error loading recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

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
      setFollowing((prev) => new Set(prev).add(userId));
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
      setFollowing((prev) => {
        const newSet = new Set(prev);
        newSet.delete(userId);
        return newSet;
      });
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

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

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

      {/* Recommended Athletes */}
      {!searchQuery && recommendations.length > 0 && (
        <Card>
          <div className="mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              Suggested Athletes
            </h2>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              Based on your training locations
            </p>
          </div>

          <div className="space-y-3">
            {recommendations.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 rounded-[14px]"
                style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
              >
                <div className="flex-1">
                  <p className="font-medium" style={{ color: 'var(--text)' }}>
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-sm" style={{ color: 'var(--muted)' }}>
                    {user.reason}
                  </p>
                </div>
                {following.has(user.id) ? (
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

      {/* Empty State */}
      {!searchQuery && recommendations.length === 0 && (
        <Card>
          <div className="text-center py-12">
            <Users className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
              No Recommendations Yet
            </h3>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Log more sessions to find athletes at your gym
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}

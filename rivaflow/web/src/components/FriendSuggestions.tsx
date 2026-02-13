import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { socialApi } from '../api/client';
import { useToast } from '../contexts/ToastContext';
import { Card, PrimaryButton, SecondaryButton } from './ui';
import { useFeatureAccess } from '../hooks/useTier';
import { UpgradePrompt } from './UpgradePrompt';

interface FriendSuggestion {
  id: number;
  suggested_user_id: number;
  score: number;
  reasons: string[];
  mutual_friends_count: number;
  username: string;
  display_name: string;
  belt_rank: string;
  belt_stripes: number;
  location_city: string;
  location_state: string;
  primary_gym_name: string;
  profile_photo_url: string;
}

interface BrowseUser {
  id: number;
  username: string;
  display_name: string;
  belt_rank: string;
  location_city: string;
  location_state: string;
  default_gym: string;
  profile_photo_url: string;
}

export function FriendSuggestions() {
  const navigate = useNavigate();
  const { hasAccess } = useFeatureAccess('friend_suggestions');
  const [suggestions, setSuggestions] = useState<FriendSuggestion[]>([]);
  const [browseUsers, setBrowseUsers] = useState<BrowseUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const toast = useToast();

  // Show upgrade prompt for free users
  if (!hasAccess) {
    return <UpgradePrompt feature="friend_suggestions" inline />;
  }

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const response = await socialApi.getFriendSuggestions(10);
      const s = response.data.suggestions;
      setSuggestions(s);

      // If no scored suggestions, load browse fallback
      if (s.length === 0) {
        try {
          const browseRes = await socialApi.browseFriends(20);
          setBrowseUsers(browseRes.data.users);
        } catch {
          // Browse is best-effort
        }
      } else {
        setBrowseUsers([]);
      }
    } catch (error) {
      console.error('Failed to load friend suggestions:', error);
      toast.error('Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      try {
        setLoading(true);
        const response = await socialApi.getFriendSuggestions(10);
        if (cancelled) return;
        const s = response.data.suggestions;
        setSuggestions(s);

        if (s.length === 0) {
          try {
            const browseRes = await socialApi.browseFriends(20);
            if (!cancelled) setBrowseUsers(browseRes.data.users);
          } catch {
            // Browse is best-effort
          }
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load friend suggestions:', error);
          toast.error('Failed to load suggestions');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const handleDismiss = async (suggestedUserId: number) => {
    try {
      await socialApi.dismissSuggestion(suggestedUserId);
      setSuggestions(suggestions.filter(s => s.suggested_user_id !== suggestedUserId));
      toast.success('Suggestion dismissed');
    } catch (error) {
      console.error('Failed to dismiss suggestion:', error);
      toast.error('Failed to dismiss suggestion');
    }
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      await socialApi.regenerateSuggestions();
      toast.success('Generating new suggestions...');
      setTimeout(() => loadSuggestions(), 2000);
    } catch (error) {
      console.error('Failed to regenerate suggestions:', error);
      toast.error('Failed to regenerate suggestions');
    } finally {
      setRegenerating(false);
    }
  };

  const formatReasons = (reasons: string[]) => {
    return reasons.map(reason => {
      if (reason === 'same_gym') return 'Trains at the same gym';
      if (reason.startsWith('mutual_friends:')) {
        const count = reason.split(':')[1];
        return `${count} mutual friend${parseInt(count) > 1 ? 's' : ''}`;
      }
      if (reason === 'same_city') return 'Same city';
      if (reason === 'partner_match') return 'Training partner match';
      if (reason === 'similar_belt') return 'Similar belt rank';
      return reason;
    }).join(' • ');
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="animate-pulse">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-[var(--surfaceElev)] rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-[var(--surfaceElev)] rounded w-1/4"></div>
                  <div className="h-3 bg-[var(--surfaceElev)] rounded w-1/2"></div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // No scored suggestions — show browse fallback
  if (suggestions.length === 0) {
    return (
      <div className="space-y-4">
        {browseUsers.length > 0 ? (
          <>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">People on RivaFlow</h3>
              <SecondaryButton onClick={handleRegenerate} disabled={regenerating} className="text-sm px-3 py-1.5">
                {regenerating ? 'Generating...' : 'Refresh'}
              </SecondaryButton>
            </div>
            {browseUsers.map((user) => (
              <Card key={user.id} className="p-4 hover:bg-[var(--surfaceElev)] transition-colors">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    {user.profile_photo_url ? (
                      <img
                        src={user.profile_photo_url}
                        alt={user.display_name}
                        className="w-14 h-14 rounded-full object-cover"
                      />
                    ) : (
                      <div
                        className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-lg font-bold"
                        role="img"
                        aria-label={`${user.display_name || user.username} avatar`}
                      >
                        {user.display_name?.charAt(0) || user.username?.charAt(0) || '?'}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-white font-semibold truncate">
                      {user.display_name || user.username}
                    </h4>
                    {user.belt_rank && (
                      <p className="text-sm text-[var(--text)] mb-1">
                        {user.belt_rank.charAt(0).toUpperCase() + user.belt_rank.slice(1)} Belt
                      </p>
                    )}
                    {(user.location_city || user.default_gym) && (
                      <p className="text-sm text-[var(--muted)] mb-2">
                        {user.default_gym && <span>{user.default_gym}</span>}
                        {user.default_gym && user.location_city && ' • '}
                        {user.location_city && <span>{user.location_city}{user.location_state ? `, ${user.location_state}` : ''}</span>}
                      </p>
                    )}
                    <PrimaryButton
                      className="text-sm px-3 py-1.5"
                      onClick={() => navigate(`/users/${user.id}`)}
                    >
                      View Profile
                    </PrimaryButton>
                  </div>
                </div>
              </Card>
            ))}
          </>
        ) : (
          <Card className="p-8 text-center">
            <p className="text-[var(--muted)] mb-4">No friend suggestions available</p>
            <PrimaryButton onClick={handleRegenerate} disabled={regenerating}>
              {regenerating ? 'Generating...' : 'Generate Suggestions'}
            </PrimaryButton>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-white">Suggested Friends</h3>
        <SecondaryButton onClick={handleRegenerate} disabled={regenerating} className="text-sm px-3 py-1.5">
          {regenerating ? 'Generating...' : 'Refresh'}
        </SecondaryButton>
      </div>

      {suggestions.map((suggestion) => (
        <Card key={suggestion.id} className="p-4 hover:bg-[var(--surfaceElev)] transition-colors">
          <div className="flex items-start space-x-4">
            {/* Profile Photo */}
            <div className="flex-shrink-0">
              {suggestion.profile_photo_url ? (
                <img
                  src={suggestion.profile_photo_url}
                  alt={suggestion.display_name}
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <div
                  className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold"
                  role="img"
                  aria-label={`${suggestion.display_name || suggestion.username} avatar`}
                >
                  {suggestion.display_name?.charAt(0) || suggestion.username?.charAt(0) || '?'}
                </div>
              )}
            </div>

            {/* User Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-white font-semibold truncate">
                  {suggestion.display_name || suggestion.username}
                </h4>
                <span className="text-xs text-[var(--muted)] ml-2">
                  {suggestion.score.toFixed(0)} match score
                </span>
              </div>

              {suggestion.belt_rank && (
                <p className="text-sm text-[var(--text)] mb-1">
                  {suggestion.belt_rank.charAt(0).toUpperCase() + suggestion.belt_rank.slice(1)} Belt
                  {suggestion.belt_stripes > 0 && ` • ${suggestion.belt_stripes} stripe${suggestion.belt_stripes > 1 ? 's' : ''}`}
                </p>
              )}

              {(suggestion.location_city || suggestion.primary_gym_name) && (
                <p className="text-sm text-[var(--muted)] mb-2">
                  {suggestion.primary_gym_name && (
                    <span>{suggestion.primary_gym_name}</span>
                  )}
                  {suggestion.primary_gym_name && suggestion.location_city && ' • '}
                  {suggestion.location_city && (
                    <span>{suggestion.location_city}, {suggestion.location_state}</span>
                  )}
                </p>
              )}

              <p className="text-xs text-blue-400 mb-3">
                {formatReasons(suggestion.reasons)}
              </p>

              <div className="flex space-x-2">
                <PrimaryButton
                  className="text-sm px-3 py-1.5"
                  onClick={() => navigate(`/users/${suggestion.suggested_user_id}`)}
                >
                  View Profile
                </PrimaryButton>
                <SecondaryButton
                  className="text-sm px-3 py-1.5"
                  onClick={() => handleDismiss(suggestion.suggested_user_id)}
                >
                  Dismiss
                </SecondaryButton>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

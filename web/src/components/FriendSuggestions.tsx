import { useState, useEffect } from 'react';
import { socialApi } from '../api/client';
import { useToast } from '../contexts/ToastContext';
import { Card, PrimaryButton, SecondaryButton } from './ui';

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

export function FriendSuggestions() {
  const [suggestions, setSuggestions] = useState<FriendSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const toast = useToast();

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const response = await socialApi.getFriendSuggestions(10);
      setSuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Failed to load friend suggestions:', error);
      toast.error('Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestions();
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
                <div className="w-16 h-16 bg-gray-700 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-700 rounded w-1/4"></div>
                  <div className="h-3 bg-gray-700 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-400 mb-4">No friend suggestions available</p>
        <PrimaryButton onClick={handleRegenerate} disabled={regenerating}>
          {regenerating ? 'Generating...' : 'Generate Suggestions'}
        </PrimaryButton>
      </Card>
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
        <Card key={suggestion.id} className="p-4 hover:bg-gray-800/50 transition-colors">
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
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold">
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
                <span className="text-xs text-gray-400 ml-2">
                  {suggestion.score.toFixed(0)} match score
                </span>
              </div>

              {suggestion.belt_rank && (
                <p className="text-sm text-gray-300 mb-1">
                  {suggestion.belt_rank.charAt(0).toUpperCase() + suggestion.belt_rank.slice(1)} Belt
                  {suggestion.belt_stripes > 0 && ` • ${suggestion.belt_stripes} stripe${suggestion.belt_stripes > 1 ? 's' : ''}`}
                </p>
              )}

              {(suggestion.location_city || suggestion.primary_gym_name) && (
                <p className="text-sm text-gray-400 mb-2">
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
                  onClick={() => window.location.href = `/users/${suggestion.suggested_user_id}`}
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

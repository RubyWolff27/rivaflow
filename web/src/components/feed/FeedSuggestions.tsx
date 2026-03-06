import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { socialApi } from '../../api/client';
import { UserPlus } from 'lucide-react';
import { logger } from '../../utils/logger';

interface SuggestedUser {
  suggested_user_id: number;
  username: string;
  display_name: string;
  belt_rank: string;
  primary_gym_name: string;
  profile_photo_url: string;
  reasons: string[];
}

export default function FeedSuggestions() {
  const navigate = useNavigate();
  const [suggestions, setSuggestions] = useState<SuggestedUser[]>([]);

  useEffect(() => {
    let cancelled = false;
    socialApi
      .getFriendSuggestions(3)
      .then((res) => {
        if (!cancelled) setSuggestions(res.data.suggestions ?? []);
      })
      .catch((err) => logger.debug('Friend suggestions unavailable', err));
    return () => { cancelled = true; };
  }, []);

  if (suggestions.length === 0) return null;

  return (
    <div
      className="rounded-[14px] p-4 space-y-3"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          People You May Know
        </h3>
        <button
          onClick={() => navigate('/friends/find')}
          className="text-xs font-medium hover:underline"
          style={{ color: 'var(--accent)' }}
        >
          See All
        </button>
      </div>

      {suggestions.map((user) => (
        <button
          key={user.suggested_user_id}
          onClick={() => navigate(`/users/${user.suggested_user_id}`)}
          className="flex items-center gap-3 w-full text-left p-2 rounded-xl transition-colors hover:bg-[var(--surfaceElev)]"
        >
          {user.profile_photo_url ? (
            <img
              src={user.profile_photo_url}
              alt={user.display_name}
              className="w-10 h-10 rounded-full object-cover shrink-0"
            />
          ) : (
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              {(user.display_name || user.username || '?')[0].toUpperCase()}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
              {user.display_name || user.username}
            </p>
            <p className="text-xs truncate" style={{ color: 'var(--muted)' }}>
              {user.belt_rank
                ? `${user.belt_rank.charAt(0).toUpperCase() + user.belt_rank.slice(1)} Belt`
                : user.primary_gym_name || 'RivaFlow user'}
            </p>
          </div>
          <UserPlus className="w-4 h-4 text-[var(--accent)] shrink-0" />
        </button>
      ))}
    </div>
  );
}

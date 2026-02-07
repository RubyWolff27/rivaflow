import { memo } from 'react';
import { Heart, MessageCircle } from 'lucide-react';

interface ActivitySocialActionsProps {
  activityType: 'session' | 'readiness' | 'rest';
  activityId: number;
  likeCount: number;
  commentCount: number;
  hasLiked: boolean;
  onLike: () => void;
  onUnlike: () => void;
  onToggleComments: () => void;
  disabled?: boolean;
}

const ActivitySocialActions = memo(function ActivitySocialActions({
  activityType: _activityType,
  activityId: _activityId,
  likeCount,
  commentCount,
  hasLiked,
  onLike,
  onUnlike,
  onToggleComments,
  disabled = false,
}: ActivitySocialActionsProps) {
  const handleLikeClick = () => {
    if (disabled) return;
    if (hasLiked) {
      onUnlike();
    } else {
      onLike();
    }
  };

  return (
    <div className="flex items-center gap-4 pt-3 border-t border-[var(--border)]" role="group" aria-label="Activity actions">
      <button
        onClick={handleLikeClick}
        disabled={disabled}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
          hasLiked
            ? 'bg-red-50 text-red-600'
            : 'bg-[var(--surfaceElev)] text-[var(--muted)] hover:opacity-80'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={hasLiked ? `Unlike (${likeCount} likes)` : `Like (${likeCount} likes)`}
        aria-pressed={hasLiked}
      >
        <Heart className={`w-4 h-4 ${hasLiked ? 'fill-current' : ''}`} />
        <span>{likeCount > 0 ? likeCount : 'Like'}</span>
      </button>

      <button
        onClick={onToggleComments}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--surfaceElev)] text-[var(--muted)] hover:opacity-80 transition-all"
        aria-label={`View comments (${commentCount} comments)`}
      >
        <MessageCircle className="w-4 h-4" />
        <span>{commentCount > 0 ? commentCount : 'Comment'}</span>
      </button>
    </div>
  );
});

export default ActivitySocialActions;

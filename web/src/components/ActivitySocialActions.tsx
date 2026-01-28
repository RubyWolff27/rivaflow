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

export default function ActivitySocialActions({
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
    <div className="flex items-center gap-4 pt-3 border-t border-gray-200 dark:border-gray-700">
      <button
        onClick={handleLikeClick}
        disabled={disabled}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
          hasLiked
            ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <Heart className={`w-4 h-4 ${hasLiked ? 'fill-current' : ''}`} />
        <span>{likeCount > 0 ? likeCount : 'Like'}</span>
      </button>

      <button
        onClick={onToggleComments}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
      >
        <MessageCircle className="w-4 h-4" />
        <span>{commentCount > 0 ? commentCount : 'Comment'}</span>
      </button>
    </div>
  );
}

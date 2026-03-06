import { memo } from 'react';
import { MessageCircle } from 'lucide-react';

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

/** OSS fist-bump icon (BJJ respect gesture) */
function OssIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 11V6a2 2 0 0 0-2-2 2 2 0 0 0-2 2" />
      <path d="M14 10V4a2 2 0 0 0-2-2 2 2 0 0 0-2 2v2" />
      <path d="M10 10.5V6a2 2 0 0 0-2-2 2 2 0 0 0-2 2v8" />
      <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 16" />
    </svg>
  );
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
            ? 'bg-[rgba(59,130,246,0.12)] text-[var(--accent)]'
            : 'bg-[var(--surfaceElev)] text-[var(--muted)] hover:opacity-80'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-label={hasLiked ? `Un-OSS (${likeCount})` : `OSS (${likeCount})`}
        aria-pressed={hasLiked}
      >
        <OssIcon className={`w-4 h-4 ${hasLiked ? 'stroke-[2.5]' : ''}`} />
        <span>{likeCount > 0 ? likeCount : 'OSS'}</span>
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

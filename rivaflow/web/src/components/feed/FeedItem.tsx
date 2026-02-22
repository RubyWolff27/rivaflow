import { memo } from 'react';
import { Calendar, Edit2, Eye, Lock, Moon, Trash2, Users2, Globe } from 'lucide-react';
import ActivitySocialActions from '../ActivitySocialActions';
import CommentSection from '../CommentSection';
import type { FeedItem } from '../../types';
import { ACTIVITY_COLORS } from '../../constants/activity';

/** Capitalize class type names in feed summary text */
function formatSummary(summary: string): string {
  return summary
    .replace(/\bno-gi\b/gi, 'No-Gi')
    .replace(/\bgi\b/g, 'Gi')
    .replace(/\bs&c\b/gi, 'S&C')
    .replace(/\bmma\b/gi, 'MMA');
}

export interface FeedItemComponentProps {
  item: FeedItem;
  prevItem: FeedItem | null;
  view: 'my' | 'friends';
  currentUserId: number | null;
  navigate: (path: string) => void;
  expandedComments: Set<string>;
  handleLike: (type: string, id: number) => void;
  handleUnlike: (type: string, id: number) => void;
  toggleComments: (type: string, id: number) => void;
  formatDate: (date: string) => string;
  shouldShowSocialActions: (item: FeedItem) => boolean;
  isActivityEditable: (item: FeedItem) => boolean;
  handleVisibilityChange: (type: string, id: number, visibility: string) => void;
  handleDeleteRest: (id: number) => void;
}

const FeedItemComponent = memo(function FeedItemComponent({
  item,
  prevItem,
  view,
  currentUserId,
  navigate,
  expandedComments,
  handleLike,
  handleUnlike,
  toggleComments,
  formatDate,
  shouldShowSocialActions,
  isActivityEditable,
  handleVisibilityChange,
  handleDeleteRest,
}: FeedItemComponentProps) {
  const showDateHeader = !prevItem || prevItem.date !== item.date;
  const commentKey = `${item.type}-${item.id}`;
  const isCommentsOpen = expandedComments.has(commentKey);

  const isFriend = !!(item.owner_user_id && currentUserId && item.owner_user_id !== currentUserId);
  const ownerName = item.owner
    ? `${item.owner.first_name || ''} ${item.owner.last_name || ''}`.trim()
    : '';
  const ownerInitial = ownerName ? ownerName[0].toUpperCase() : '?';

  const isRest = item.type === 'rest';

  const getRestTypeStyle = (type: string): React.CSSProperties => {
    const styles: Record<string, React.CSSProperties> = {
      'active': { backgroundColor: 'rgba(59,130,246,0.1)', color: 'var(--accent)' },
      'passive': { backgroundColor: 'rgba(107,114,128,0.1)', color: '#6b7280' },
      'full': { backgroundColor: 'rgba(168,85,247,0.1)', color: '#a855f7' },
      'injury': { backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)' },
      'sick': { backgroundColor: 'rgba(234,179,8,0.1)', color: '#ca8a04' },
      'travel': { backgroundColor: 'rgba(34,197,94,0.1)', color: '#16a34a' },
      'life': { backgroundColor: 'rgba(156,163,175,0.1)', color: '#6b7280' },
    };
    return styles[type] || { backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' };
  };

  const getRestTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'active': '\u{1F3C3} Active Recovery',
      'passive': '\u{1F6B6} Passive Recovery',
      'full': '\u{1F6CC} Full Rest',
      'injury': '\u{1F915} Injury / Rehab',
      'sick': '\u{1F912} Sick Day',
      'travel': '\u{2708}\u{FE0F} Travelling',
      'life': '\u{1F937} Life Got in the Way',
    };
    return labels[type] || type || 'Rest';
  };

  return (
    <div>
      {showDateHeader && (
        <div className="flex items-center gap-3 mb-3 mt-6 first:mt-0">
          <Calendar className="w-4 h-4 text-[var(--muted)]" />
          <h3 className="text-sm font-semibold text-[var(--text)] uppercase tracking-wide">
            {formatDate(item.date)}
          </h3>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>
      )}

      <div
        className="rounded-[14px] overflow-hidden"
        role="article"
        aria-label={item.summary}
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderLeft: `3px solid ${isRest ? '#A855F7' : ACTIVITY_COLORS[item.data?.class_type ?? ''] || 'var(--accent)'}`,
        }}
      >
        {/* Friend name header */}
        {isFriend && ownerName && (
          <div className="px-4 pt-3 pb-0">
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => navigate(`/users/${item.owner_user_id}`)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
              >
                {ownerInitial}
              </button>
              <div className="flex items-center gap-1.5 min-w-0">
                <button
                  onClick={() => navigate(`/users/${item.owner_user_id}`)}
                  className="text-sm font-semibold truncate hover:underline"
                  style={{ color: 'var(--text)' }}
                >
                  {ownerName}
                </button>
                <span className="text-xs shrink-0" style={{ color: 'var(--muted)' }}>
                  · {formatDate(item.date)}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="p-4">
          {isRest ? (
            /* Rest day card */
            <>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <Moon className="w-5 h-5 text-purple-500" />
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                    {formatSummary(item.summary)}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {view === 'my' && (
                    <>
                      <button
                        onClick={() => navigate(`/rest/${item.date}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="View rest day"
                      >
                        <Eye className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => navigate(`/rest/edit/${item.date}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Edit rest day"
                      >
                        <Edit2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => handleDeleteRest(item.id)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Delete rest day"
                      >
                        <Trash2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {item.data?.rest_type && (
                <span
                  className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold mb-2"
                  style={getRestTypeStyle(item.data.rest_type)}
                >
                  {getRestTypeLabel(item.data.rest_type)}
                </span>
              )}

              {item.data?.rest_note && (
                <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
                  {item.data.rest_note}
                </p>
              )}

              {item.data?.tomorrow_intention && (
                <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  Tomorrow: {item.data.tomorrow_intention}
                </div>
              )}
            </>
          ) : (
            /* Session card */
            <>
              {/* Summary + actions row */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                  {formatSummary(item.summary)}
                </p>
                <div className="flex items-center gap-2 shrink-0">
                  {isActivityEditable(item) && (
                    <>
                      <button
                        onClick={() => navigate(`/session/${item.id}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="View session details"
                      >
                        <Eye className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                      <button
                        onClick={() => navigate(`/session/edit/${item.id}`)}
                        className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                        aria-label="Edit session"
                      >
                        <Edit2 className="w-4 h-4 text-[var(--muted)]" />
                      </button>
                    </>
                  )}
                  {isActivityEditable(item) && (() => {
                    const vis = item.data?.visibility_level || item.data?.visibility || 'summary';
                    const options = [
                      { value: 'private', icon: Lock, label: 'Private' },
                      { value: 'summary', icon: Users2, label: 'Friends' },
                      { value: 'full', icon: Globe, label: 'Public' },
                    ] as const;
                    return (
                      <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }} role="group" aria-label="Visibility">
                        {options.map(opt => {
                          const Icon = opt.icon;
                          const active = vis === opt.value;
                          return (
                            <button
                              key={opt.value}
                              onClick={() => handleVisibilityChange(item.type, item.id, opt.value)}
                              className="p-1.5 transition-colors"
                              style={{
                                backgroundColor: active ? 'var(--accent)' : 'transparent',
                                color: active ? '#FFFFFF' : 'var(--muted)',
                                opacity: active ? 1 : 0.5,
                              }}
                              title={opt.label}
                              aria-label={opt.label}
                              aria-pressed={active}
                            >
                              <Icon className="w-3.5 h-3.5" />
                            </button>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              </div>

              {/* Session details */}
              <div className="mt-2 text-sm space-y-1" style={{ color: 'var(--muted)' }}>
                {item.data?.class_time && <div>🕐 {item.data.class_time}</div>}
                {item.data?.location && <div>📍 {item.data.location}</div>}
                {item.data?.instructor_name && <div>👨‍🏫 {item.data.instructor_name}</div>}
                {item.data?.partners && Array.isArray(item.data.partners) && item.data.partners.length > 0 && (
                  <div>🤝 Partners: {item.data.partners.join(', ')}</div>
                )}
                {item.data?.techniques && Array.isArray(item.data.techniques) && item.data.techniques.length > 0 && (
                  <div>🎯 Techniques: {item.data.techniques.join(', ')}</div>
                )}
                {item.data?.notes && (
                  <div className="mt-2 italic" style={{ color: 'var(--text)' }}>
                    &ldquo;{item.data.notes}&rdquo;
                  </div>
                )}
              </div>

              {/* Photo — full-width for social feel */}
              {item.thumbnail && (
                <div
                  className="mt-3 cursor-pointer"
                  onClick={() => navigate(`/session/${item.id}`)}
                >
                  <div className="relative">
                    <img
                      src={item.thumbnail}
                      alt="Session photo"
                      className="w-full max-h-48 rounded-lg object-cover border border-[var(--border)]"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />
                    {(item.photo_count ?? 0) > 1 && (
                      <span className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded-full font-medium">
                        +{(item.photo_count ?? 1) - 1}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {item.data?.tomorrow_intention && (
                <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  Tomorrow: {item.data.tomorrow_intention}
                </div>
              )}
            </>
          )}

          {/* Social actions bar */}
          {shouldShowSocialActions(item) && currentUserId && (
            <>
              <ActivitySocialActions
                activityType={item.type}
                activityId={item.id}
                likeCount={item.like_count || 0}
                commentCount={item.comment_count || 0}
                hasLiked={item.has_liked || false}
                onLike={() => handleLike(item.type, item.id)}
                onUnlike={() => handleUnlike(item.type, item.id)}
                onToggleComments={() => toggleComments(item.type, item.id)}
              />

              <CommentSection
                activityType={item.type}
                activityId={item.id}
                currentUserId={currentUserId}
                isOpen={isCommentsOpen}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
});

export default FeedItemComponent;

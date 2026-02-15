import { useEffect, useState, memo, useCallback, useMemo } from 'react';
import { getLocalDateString } from '../utils/date';
import { useNavigate } from 'react-router-dom';
import { feedApi, socialApi, sessionsApi } from '../api/client';
import { logger } from '../utils/logger';
import { Activity, Calendar, Edit2, Eye, Moon } from 'lucide-react';
import FeedToggle from '../components/FeedToggle';
import ActivitySocialActions from '../components/ActivitySocialActions';
import CommentSection from '../components/CommentSection';
import { CardSkeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import type { FeedItem } from '../types';

interface FeedResponse {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Memoized feed item component to prevent unnecessary re-renders
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
}: {
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
}) {
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
      'active': 'Active Recovery',
      'full': 'Full Rest',
      'injury': 'Injury / Rehab',
      'sick': 'Sick Day',
      'travel': 'Travelling',
      'life': 'Life Got in the Way',
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

      <div className="rounded-[14px] overflow-hidden" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
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
                    {item.summary}
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
                  {item.summary}
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
                  {isActivityEditable(item) && (
                    <select
                      value={item.data?.visibility_level || item.data?.visibility || 'friends'}
                      onChange={(e) => handleVisibilityChange(item.type, item.id, e.target.value)}
                      className="text-xs px-2 py-1 bg-white/50 dark:bg-black/20 rounded cursor-pointer border-none outline-none"
                      aria-label="Change visibility"
                      title="Who can see this"
                    >
                      <option value="private">Private</option>
                      <option value="friends">Friends</option>
                      <option value="public">Public</option>
                    </select>
                  )}
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

export default function Feed() {
  useEffect(() => { document.title = 'Feed | RivaFlow'; }, []);
  const navigate = useNavigate();
  const { user } = useAuth();
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [daysBack, setDaysBack] = useState(30);
  const [view, setView] = useState<'my' | 'friends'>('my');
  const [sessionFilter, setSessionFilter] = useState<string>('all');
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());
  const [loadingMore, setLoadingMore] = useState(false);

  const currentUserId = user?.id ?? null;

  useEffect(() => {
    const controller = new AbortController();
    const doLoad = async () => {
      setLoading(true);
      try {
        if (view === 'my') {
          const response = await feedApi.getActivity({
            limit: 100,
            days_back: daysBack,
            enrich_social: true,
          });
          if (!controller.signal.aborted) setFeed(response.data ?? null);
        } else {
          const response = await feedApi.getFriends({
            limit: 100,
            days_back: daysBack,
          });
          if (!controller.signal.aborted) setFeed(response.data ?? null);
        }
      } catch (error) {
        if (!controller.signal.aborted) logger.error('Error loading feed:', error);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    doLoad();
    return () => { controller.abort(); };
  }, [daysBack, view]);

  const loadFeed = async () => {
    setLoading(true);
    try {
      if (view === 'my') {
        const response = await feedApi.getActivity({
          limit: 100,
          days_back: daysBack,
          enrich_social: true,
        });
        setFeed(response.data ?? null);
      } else {
        const response = await feedApi.getFriends({
          limit: 100,
          days_back: daysBack,
        });
        setFeed(response.data ?? null);
      }
    } catch (error) {
      logger.error('Error loading feed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = useCallback(async (activityType: string, activityId: number) => {
    if (!feed) return;

    // Optimistic update
    setFeed({
      ...feed,
      items: feed.items.map((item) =>
        item.type === activityType && item.id === activityId
          ? { ...item, has_liked: true, like_count: (item.like_count || 0) + 1 }
          : item
      ),
    });

    try {
      await socialApi.like(activityType, activityId);
    } catch (error) {
      logger.error('Error liking activity:', error);
      // Revert optimistic update on error
      loadFeed();
    }
  }, [feed]);

  const handleUnlike = useCallback(async (activityType: string, activityId: number) => {
    if (!feed) return;

    // Optimistic update
    setFeed({
      ...feed,
      items: feed.items.map((item) =>
        item.type === activityType && item.id === activityId
          ? { ...item, has_liked: false, like_count: Math.max((item.like_count || 0) - 1, 0) }
          : item
      ),
    });

    try {
      await socialApi.unlike(activityType, activityId);
    } catch (error) {
      logger.error('Error unliking activity:', error);
      // Revert optimistic update on error
      loadFeed();
    }
  }, [feed]);

  const toggleComments = useCallback((activityType: string, activityId: number) => {
    const key = `${activityType}-${activityId}`;
    setExpandedComments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  }, []);

  const handleVisibilityChange = useCallback(async (activityType: string, activityId: number, visibility: string) => {
    if (!feed) return;

    // Only sessions support visibility updates
    if (activityType !== 'session') {
      return;
    }

    // Optimistic update
    setFeed({
      ...feed,
      items: feed.items.map((item) =>
        item.type === activityType && item.id === activityId
          ? { ...item, data: { ...item.data, visibility_level: visibility, visibility } }
          : item
      ),
    });

    try {
      // Get current session data and update only visibility
      const session = feed.items.find(item => item.type === 'session' && item.id === activityId);
      if (session?.data) {
        await sessionsApi.update(activityId, {
          ...session.data,
          visibility_level: visibility,
        });
      }
    } catch (error) {
      logger.error('Error updating visibility:', error);
      // Revert optimistic update on error
      loadFeed();
    }
  }, [feed]);

  const formatDate = useCallback((dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const dateOnly = getLocalDateString(date);
    const todayOnly = getLocalDateString(today);
    const yesterdayOnly = getLocalDateString(yesterday);

    if (dateOnly === todayOnly) return 'Today';
    if (dateOnly === yesterdayOnly) return 'Yesterday';

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
    });
  }, []);

  const shouldShowSocialActions = useCallback((item: FeedItem) => {
    // Show social actions in contacts feed, or in my feed if enriched with social data
    return view === 'friends' || (item.like_count !== undefined && item.comment_count !== undefined);
  }, [view]);

  const isActivityEditable = useCallback((_item: FeedItem) => {
    // Only show edit/view buttons for own activities
    return view === 'my';
  }, [view]);

  const sessionFilters = [
    { key: 'all', label: 'All' },
    { key: 'rest', label: 'Rest Days' },
    { key: 'comp', label: '\u{1F94B} Comp Prep' },
    { key: 'hard', label: '\u{1F525} Hard' },
    { key: 'technical', label: '\u{1F9E0} Technical' },
    { key: 'smashed', label: '\u{1F480} Smashed' },
  ];

  const matchesSessionFilter = useCallback((item: FeedItem): boolean => {
    if (sessionFilter === 'all') return true;
    if (sessionFilter === 'rest') return item.type === 'rest';
    // Non-rest filters only match sessions
    if (item.type !== 'session') return false;
    const d = item.data ?? {};
    switch (sessionFilter) {
      case 'comp':
        return d.class_type === 'competition';
      case 'hard':
        return (d.intensity ?? 0) >= 4;
      case 'technical':
        return (d.intensity ?? 5) <= 2;
      case 'smashed':
        return (d.submissions_against ?? 0) > (d.submissions_for ?? 0) && (d.submissions_against ?? 0) > 0;
      default:
        return true;
    }
  }, [sessionFilter]);

  const getFilterCount = useCallback((filterKey: string): number => {
    if (!feed) return 0;
    if (filterKey === 'all') return feed.items.length;
    if (filterKey === 'rest') return feed.items.filter(i => i.type === 'rest').length;
    return feed.items.filter(i => {
      if (i.type !== 'session') return false;
      const d = i.data ?? {};
      switch (filterKey) {
        case 'comp': return d.class_type === 'competition';
        case 'hard': return (d.intensity ?? 0) >= 4;
        case 'technical': return (d.intensity ?? 5) <= 2;
        case 'smashed': return (d.submissions_against ?? 0) > (d.submissions_for ?? 0) && (d.submissions_against ?? 0) > 0;
        default: return false;
      }
    }).length;
  }, [feed]);

  const filteredItems = useMemo(
    () => feed?.items.filter(matchesSessionFilter) ?? [],
    [feed, matchesSessionFilter]
  );

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <CardSkeleton key={i} lines={4} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-[var(--text)] flex items-center gap-3">
          <Activity className="w-8 h-8" />
          Activity Feed
        </h1>
        <select
          className="input w-auto"
          value={daysBack}
          onChange={(e) => setDaysBack(parseInt(e.target.value))}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 2 weeks</option>
          <option value={30}>Last month</option>
          <option value={60}>Last 2 months</option>
          <option value={90}>Last 3 months</option>
          <option value={180}>Last 6 months</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      {/* Feed toggle */}
      <FeedToggle view={view} onChange={setView} />

      {/* Session filters */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {sessionFilters.map((f) => {
          const count = getFilterCount(f.key);
          const isActive = sessionFilter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setSessionFilter(f.key)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all"
              style={{
                backgroundColor: isActive ? 'var(--accent)' : 'var(--surfaceElev)',
                color: isActive ? '#FFFFFF' : 'var(--text)',
                border: isActive ? 'none' : '1px solid var(--border)',
              }}
            >
              {f.label}
              {f.key !== 'all' && count > 0 && (
                <span
                  className="text-xs px-1.5 py-0.5 rounded-full font-semibold"
                  style={{
                    backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : 'var(--border)',
                    color: isActive ? '#FFFFFF' : 'var(--muted)',
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {feed && feed.items.length === 0 ? (
        <div className="card text-center py-12">
          <Activity className="w-16 h-16 text-[var(--muted)] mx-auto mb-4" />
          <p className="text-[var(--muted)] text-lg">
            {view === 'friends'
              ? "No activity from friends in the last " + daysBack + " days"
              : "No activity in the last " + daysBack + " days"}
          </p>
          <p className="text-[var(--muted)] text-sm mt-2">
            {view === 'friends'
              ? "Follow other users to see their activity here!"
              : "Log a session or rest day to see it here!"}
          </p>
        </div>
      ) : filteredItems.length === 0 && sessionFilter !== 'all' ? (
        <div className="card text-center py-12">
          <p className="text-[var(--muted)] text-lg">No sessions match this filter</p>
          <button
            onClick={() => setSessionFilter('all')}
            className="text-sm mt-2 underline"
            style={{ color: 'var(--accent)' }}
          >
            Clear filter
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item, index) => (
            <FeedItemComponent
              key={`${item.type}-${item.id}`}
              item={item}
              prevItem={index > 0 ? filteredItems[index - 1] : null}
              view={view}
              currentUserId={currentUserId}
              navigate={navigate}
              expandedComments={expandedComments}
              handleLike={handleLike}
              handleUnlike={handleUnlike}
              toggleComments={toggleComments}
              formatDate={formatDate}
              shouldShowSocialActions={shouldShowSocialActions}
              isActivityEditable={isActivityEditable}
              handleVisibilityChange={handleVisibilityChange}
            />
          ))}
        </div>
      )}

      {feed && feed.total > 0 && (
        <div className="text-center py-4 space-y-2">
          <p className="text-sm text-[var(--muted)]">
            Showing {feed.items.length} of {feed.total} activities
          </p>
          {feed.has_more && (
            <button
              onClick={async () => {
                if (!feed || loadingMore) return;
                setLoadingMore(true);
                try {
                  const fetchFn = view === 'my' ? feedApi.getActivity : feedApi.getFriends;
                  const params = view === 'my'
                    ? { limit: 50, offset: feed.items.length, days_back: daysBack, enrich_social: true }
                    : { limit: 50, offset: feed.items.length, days_back: daysBack };
                  const res = await fetchFn(params);
                  if (res.data?.items) {
                    setFeed({
                      ...res.data,
                      items: [...feed.items, ...res.data.items],
                    });
                  }
                } catch (err) {
                  logger.error('Error loading more:', err);
                } finally {
                  setLoadingMore(false);
                }
              }}
              disabled={loadingMore}
              className="px-6 py-2 rounded-[14px] text-sm font-medium transition-colors"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
                border: '1px solid var(--border)',
              }}
            >
              {loadingMore ? 'Loading...' : 'Load More'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

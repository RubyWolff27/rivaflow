import { useState, useCallback, useMemo, useEffect } from 'react';
import { getLocalDateString } from '../utils/date';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { Activity } from 'lucide-react';
import FeedToggle from '../components/FeedToggle';
import { CardSkeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import type { FeedItem, Grading } from '../types';
import FeedItemComponent from '../components/feed/FeedItem';
import FeedFilters, { matchesSessionFilter } from '../components/feed/FeedFilters';
import { useFeedData } from '../hooks/useFeedData';
import ConfirmDialog from '../components/ConfirmDialog';
import WeeklySummaryCard from '../components/analytics/WeeklySummaryCard';
import FeedSuggestions from '../components/feed/FeedSuggestions';
import { gradingsApi, notificationsApi, profileApi } from '../api/client';
import { logger } from '../utils/logger';

export default function Feed() {
  usePageTitle('Feed');
  const navigate = useNavigate();
  const { user } = useAuth();
  const [daysBack, setDaysBack] = useState(30);
  const [view, setView] = useState<'my' | 'friends'>('my');
  const [sessionFilter, setSessionFilter] = useState<string>('all');
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());
  const [restToDelete, setRestToDelete] = useState<number | null>(null);

  const currentUserId = user?.id ?? null;
  const [promotionItems, setPromotionItems] = useState<FeedItem[]>([]);
  const [milestoneItems, setMilestoneItems] = useState<FeedItem[]>([]);

  // Fetch gradings and milestones for feed integration
  useEffect(() => {
    let cancelled = false;
    const loadExtra = async () => {
      try {
        // Fetch gradings
        const [gradingsRes, profileRes] = await Promise.all([
          gradingsApi.list().catch(() => ({ data: [] as Grading[] })),
          profileApi.get().catch(() => ({ data: null })),
        ]);
        if (cancelled) return;

        const gradings = Array.isArray(gradingsRes.data) ? gradingsRes.data : [];
        const profile = profileRes.data;

        const promoItems: FeedItem[] = gradings.map((g: Grading, idx: number) => ({
          type: 'promotion' as const,
          date: g.date_graded,
          id: g.id || 10000 + idx,
          data: {} as FeedItem['data'],
          summary: `Promoted to ${g.grade}`,
          grade: g.grade,
          professor: g.professor,
          sessions_since_last: profile?.sessions_since_promotion,
          hours_since_last: profile?.hours_since_promotion,
          rolls_since_last: undefined,
        }));
        setPromotionItems(promoItems);
      } catch (err) {
        logger.debug('Failed to load gradings for feed', err);
      }

      try {
        // Fetch milestone notifications
        const notifRes = await notificationsApi.getAll({ limit: 50 });
        if (cancelled) return;

        const notifications = notifRes.data?.notifications ?? [];
        const milestones: FeedItem[] = notifications
          .filter((n: Record<string, unknown>) => n.notification_type === 'milestone' || (typeof n.title === 'string' && (n.title as string).toLowerCase().includes('milestone')))
          .map((n: Record<string, unknown>, idx: number) => ({
            type: 'milestone' as const,
            date: (n.created_at as string) || new Date().toISOString(),
            id: (n.id as number) || 20000 + idx,
            data: {} as FeedItem['data'],
            summary: (n.title as string) || 'Milestone achieved!',
            milestone_label: (n.title as string) || 'Milestone',
            milestone_type: (n.data as Record<string, unknown>)?.milestone_type as string | undefined,
            milestone_value: (n.data as Record<string, unknown>)?.milestone_value as number | undefined,
          }));
        setMilestoneItems(milestones);
      } catch (err) {
        logger.debug('Failed to load milestones for feed', err);
      }
    };
    loadExtra();
    return () => { cancelled = true; };
  }, []);

  const {
    feed,
    loading,
    loadingMore,
    error,
    retry,
    handleLike,
    handleUnlike,
    handleDeleteRest,
    handleVisibilityChange,
    handleLoadMore,
  } = useFeedData(daysBack, view);

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
    return view === 'friends' || (item.like_count !== undefined && item.comment_count !== undefined);
  }, [view]);

  const isActivityEditable = useCallback((_item: FeedItem) => {
    return view === 'my';
  }, [view]);

  const confirmDeleteRest = useCallback((id: number) => {
    setRestToDelete(id);
  }, []);

  const filteredItems = useMemo(
    () => {
      let items = feed?.items ?? [];
      if (view === 'friends' && currentUserId) {
        items = items.filter(
          (item) => item.owner_user_id && item.owner_user_id !== currentUserId
        );
      }
      const filtered = items.filter((item) => matchesSessionFilter(item, sessionFilter));

      // Merge promotion and milestone items into the feed (only on "my" view)
      if (view === 'my') {
        const merged = [...filtered, ...promotionItems, ...milestoneItems];
        // Sort by date descending
        merged.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        return merged;
      }
      return filtered;
    },
    [feed, sessionFilter, view, currentUserId, promotionItems, milestoneItems]
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

      <FeedToggle view={view} onChange={setView} />

      {/* Weekly summary + partner suggestions */}
      {view === 'my' && (
        <div className="space-y-4">
          <WeeklySummaryCard />
          <FeedSuggestions />
        </div>
      )}

      <FeedFilters
        feed={feed}
        sessionFilter={sessionFilter}
        onFilterChange={setSessionFilter}
      />

      {!loading && error && !feed ? (
        <div className="card text-center py-12">
          <Activity className="w-16 h-16 text-[var(--muted)] mx-auto mb-4" />
          <p className="text-[var(--muted)] text-lg">Couldn't load activity feed</p>
          <button
            onClick={retry}
            className="text-sm mt-2 underline"
            style={{ color: 'var(--accent)' }}
          >
            Try again
          </button>
        </div>
      ) : feed && feed.items.length === 0 ? (
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
              handleDeleteRest={confirmDeleteRest}
            />
          ))}
        </div>
      )}

      {/* Delete rest day confirmation */}
      <ConfirmDialog
        isOpen={restToDelete !== null}
        onClose={() => setRestToDelete(null)}
        onConfirm={() => {
          if (restToDelete !== null) handleDeleteRest(restToDelete);
          setRestToDelete(null);
        }}
        title="Delete Rest Day"
        message="Delete this rest day? This cannot be undone."
        confirmText="Delete"
        variant="danger"
      />

      {feed && feed.total > 0 && filteredItems.length > 0 && (
        <div className="text-center py-4 space-y-2">
          <p className="text-sm text-[var(--muted)]">
            Showing {feed.items.length} of {feed.total} activities
          </p>
          {feed.has_more && (
            <button
              onClick={handleLoadMore}
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

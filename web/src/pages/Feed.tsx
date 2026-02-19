import { useState, useCallback, useMemo } from 'react';
import { getLocalDateString } from '../utils/date';
import { useNavigate } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';
import { Activity } from 'lucide-react';
import FeedToggle from '../components/FeedToggle';
import { CardSkeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import type { FeedItem } from '../types';
import FeedItemComponent from '../components/feed/FeedItem';
import FeedFilters, { matchesSessionFilter } from '../components/feed/FeedFilters';
import { useFeedData } from '../hooks/useFeedData';
import ConfirmDialog from '../components/ConfirmDialog';

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

  const {
    feed,
    loading,
    loadingMore,
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
      return items.filter((item) => matchesSessionFilter(item, sessionFilter));
    },
    [feed, sessionFilter, view, currentUserId]
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

      <FeedFilters
        feed={feed}
        sessionFilter={sessionFilter}
        onFilterChange={setSessionFilter}
      />

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

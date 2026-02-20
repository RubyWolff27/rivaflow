import { useEffect, useState, useCallback } from 'react';
import { feedApi, socialApi, sessionsApi, restApi } from '../api/client';
import { logger } from '../utils/logger';
import { useToast } from '../contexts/ToastContext';
import type { FeedItem } from '../types';

export interface FeedResponse {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export function useFeedData(daysBack: number, view: 'my' | 'friends') {
  const toast = useToast();
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const doLoad = async () => {
      setLoading(true);
      setError(false);
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
        if (!controller.signal.aborted) {
          logger.error('Error loading feed:', error);
          toast.error('Failed to load feed');
          setError(true);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    doLoad();
    return () => { controller.abort(); };
  }, [daysBack, view, toast]);

  const loadFeed = useCallback(async () => {
    setLoading(true);
    setError(false);
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
      toast.error('Failed to load feed');
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [daysBack, view, toast]);

  const handleLike = useCallback(async (activityType: string, activityId: number) => {
    if (!feed) return;

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
      toast.error('Failed to like activity');
      loadFeed();
    }
  }, [feed, loadFeed, toast]);

  const handleUnlike = useCallback(async (activityType: string, activityId: number) => {
    if (!feed) return;

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
      toast.error('Failed to update like');
      loadFeed();
    }
  }, [feed, loadFeed, toast]);

  const handleDeleteRest = useCallback(async (checkinId: number) => {
    if (!feed) return;

    setFeed({
      ...feed,
      items: feed.items.filter(item => !(item.type === 'rest' && item.id === checkinId)),
      total: feed.total - 1,
    });

    try {
      await restApi.delete(checkinId);
    } catch (error) {
      logger.error('Error deleting rest day:', error);
      toast.error('Failed to delete rest day');
      loadFeed();
    }
  }, [feed, loadFeed, toast]);

  const handleVisibilityChange = useCallback(async (activityType: string, activityId: number, visibility: string) => {
    if (!feed) return;
    if (activityType !== 'session') return;

    setFeed({
      ...feed,
      items: feed.items.map((item) =>
        item.type === activityType && item.id === activityId
          ? { ...item, data: { ...item.data, visibility_level: visibility, visibility } }
          : item
      ),
    });

    try {
      const session = feed.items.find(item => item.type === 'session' && item.id === activityId);
      if (session?.data) {
        await sessionsApi.update(activityId, {
          ...session.data,
          visibility_level: visibility,
        });
      }
    } catch (error) {
      logger.error('Error updating visibility:', error);
      toast.error('Failed to update visibility');
      loadFeed();
    }
  }, [feed, loadFeed, toast]);

  const handleLoadMore = useCallback(async () => {
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
      toast.error('Failed to load more activities');
    } finally {
      setLoadingMore(false);
    }
  }, [feed, loadingMore, view, daysBack, toast]);

  return {
    feed,
    loading,
    loadingMore,
    error,
    retry: loadFeed,
    handleLike,
    handleUnlike,
    handleDeleteRest,
    handleVisibilityChange,
    handleLoadMore,
  };
}

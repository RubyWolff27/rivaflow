import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { feedApi, socialApi } from '../api/client';
import { Activity, Calendar, Heart, Moon, Zap, Edit2, Eye } from 'lucide-react';
import FeedToggle from '../components/FeedToggle';
import ActivitySocialActions from '../components/ActivitySocialActions';
import CommentSection from '../components/CommentSection';
import { useAuth } from '../contexts/AuthContext';
import type { FeedItem } from '../types';

interface FeedResponse {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export default function Feed() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [daysBack, setDaysBack] = useState(30);
  const [view, setView] = useState<'my' | 'friends'>('my');
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());

  const currentUserId = user?.id || null;

  useEffect(() => {
    loadFeed();
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
        setFeed(response.data);
      } else {
        const response = await feedApi.getFriends({
          limit: 100,
          days_back: daysBack,
        });
        setFeed(response.data);
      }
    } catch (error) {
      console.error('Error loading feed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (activityType: string, activityId: number) => {
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
      console.error('Error liking activity:', error);
      // Revert optimistic update on error
      loadFeed();
    }
  };

  const handleUnlike = async (activityType: string, activityId: number) => {
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
      console.error('Error unliking activity:', error);
      // Revert optimistic update on error
      loadFeed();
    }
  };

  const toggleComments = (activityType: string, activityId: number) => {
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
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'session':
        return <Zap className="w-5 h-5 text-primary-600" />;
      case 'readiness':
        return <Heart className="w-5 h-5 text-green-600" />;
      case 'rest':
        return <Moon className="w-5 h-5 text-purple-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getBackgroundColor = (type: string) => {
    switch (type) {
      case 'session':
        return 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800';
      case 'readiness':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'rest':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      default:
        return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const dateOnly = date.toISOString().split('T')[0];
    const todayOnly = today.toISOString().split('T')[0];
    const yesterdayOnly = yesterday.toISOString().split('T')[0];

    if (dateOnly === todayOnly) return 'Today';
    if (dateOnly === yesterdayOnly) return 'Yesterday';

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
    });
  };

  const shouldShowSocialActions = (item: FeedItem) => {
    // Show social actions in contacts feed, or in my feed if enriched with social data
    return view === 'friends' || (item.like_count !== undefined && item.comment_count !== undefined);
  };

  const isActivityEditable = (_item: FeedItem) => {
    // Only show edit/view buttons for own activities
    return view === 'my';
  };

  if (loading) {
    return <div className="text-center py-12">Loading activity...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
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

      {feed && feed.items.length === 0 ? (
        <div className="card text-center py-12">
          <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-lg">
            {view === 'friends'
              ? "No activity from friends in the last " + daysBack + " days"
              : "No activity in the last " + daysBack + " days"}
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
            {view === 'friends'
              ? "Follow other users to see their activity here!"
              : "Log a session, readiness check-in, or rest day to see it here!"}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {feed?.items.map((item, index) => {
            const prevItem = index > 0 ? feed.items[index - 1] : null;
            const showDateHeader = !prevItem || prevItem.date !== item.date;
            const commentKey = `${item.type}-${item.id}`;
            const isCommentsOpen = expandedComments.has(commentKey);

            return (
              <div key={`${item.type}-${item.id}`}>
                {showDateHeader && (
                  <div className="flex items-center gap-3 mb-3 mt-6 first:mt-0">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                      {formatDate(item.date)}
                    </h3>
                    <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                  </div>
                )}

                <div className={`card border-2 ${getBackgroundColor(item.type)}`}>
                  <div className="flex items-start gap-4">
                    <div className="mt-1">{getIcon(item.type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {item.summary}
                        </p>
                        <div className="flex items-center gap-2">
                          {isActivityEditable(item) && (
                            <>
                              {item.type === 'session' && (
                                <>
                                  <button
                                    onClick={() => navigate(`/session/${item.id}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="View session details"
                                  >
                                    <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                  <button
                                    onClick={() => navigate(`/session/edit/${item.id}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="Edit session"
                                  >
                                    <Edit2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                </>
                              )}
                              {item.type === 'readiness' && (
                                <>
                                  <button
                                    onClick={() => navigate(`/readiness/${item.data.check_date}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="View readiness details"
                                  >
                                    <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                  <button
                                    onClick={() => navigate(`/readiness/edit/${item.data.check_date}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="Edit readiness"
                                  >
                                    <Edit2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                </>
                              )}
                              {item.type === 'rest' && (
                                <>
                                  <button
                                    onClick={() => navigate(`/rest/${item.data.rest_date}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="View rest day details"
                                  >
                                    <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                  <button
                                    onClick={() => navigate(`/rest/edit/${item.data.rest_date}`)}
                                    className="p-1 hover:bg-white/50 dark:hover:bg-black/20 rounded transition-colors"
                                    aria-label="Edit rest day"
                                  >
                                    <Edit2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </button>
                                </>
                              )}
                            </>
                          )}
                          <span className="text-xs px-2 py-1 bg-white/50 dark:bg-black/20 rounded capitalize whitespace-nowrap">
                            {item.type}
                          </span>
                        </div>
                      </div>

                      {/* Session details */}
                      {item.type === 'session' && (
                        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                          {item.data.class_time && <div>🕐 {item.data.class_time}</div>}
                          {item.data.location && <div>📍 {item.data.location}</div>}
                          {item.data.instructor_name && <div>👨‍🏫 {item.data.instructor_name}</div>}
                          {item.data.partners && item.data.partners.length > 0 && (
                            <div>🤝 Partners: {item.data.partners.join(', ')}</div>
                          )}
                          {item.data.techniques && item.data.techniques.length > 0 && (
                            <div>🎯 Techniques: {item.data.techniques.join(', ')}</div>
                          )}
                          {item.data.notes && (
                            <div className="mt-2 text-gray-700 dark:text-gray-300 italic">
                              "{item.data.notes}"
                            </div>
                          )}
                        </div>
                      )}

                      {/* Readiness details */}
                      {item.type === 'readiness' && (
                        <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">😴 Sleep:</span>
                            <span className="font-semibold">{item.data.sleep}/5</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">😰 Stress:</span>
                            <span className="font-semibold">{item.data.stress}/5</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">💪 Soreness:</span>
                            <span className="font-semibold">{item.data.soreness}/5</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-gray-500">⚡ Energy:</span>
                            <span className="font-semibold">{item.data.energy}/5</span>
                          </div>
                          {item.data.hotspot_note && (
                            <div className="col-span-2 md:col-span-4 text-gray-700 dark:text-gray-300 mt-1">
                              🔥 Hotspot: {item.data.hotspot_note}
                            </div>
                          )}
                          {item.data.weight_kg && (
                            <div className="col-span-2 md:col-span-4 text-gray-700 dark:text-gray-300">
                              ⚖️ Weight: {item.data.weight_kg} kg
                            </div>
                          )}
                        </div>
                      )}

                      {/* Rest day details */}
                      {item.type === 'rest' && item.data.rest_note && (
                        <div className="mt-2 text-sm text-gray-700 dark:text-gray-300 italic">
                          "{item.data.rest_note}"
                        </div>
                      )}

                      {item.data.tomorrow_intention && (
                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          → Tomorrow: {item.data.tomorrow_intention}
                        </div>
                      )}

                      {/* Social actions */}
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
              </div>
            );
          })}
        </div>
      )}

      {feed && feed.total > 0 && (
        <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-4">
          Showing {feed.items.length} of {feed.total} activities
        </div>
      )}
    </div>
  );
}

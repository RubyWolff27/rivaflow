import { api } from './_client';
import type { DayCheckins, DailyCheckin, StreakStatus, Streak, UserBasic } from '../types';

export const checkinsApi = {
  getToday: () => api.get<DayCheckins>('/checkins/today'),
  getYesterday: () => api.get<{ date: string; morning: DailyCheckin | null; midday: DailyCheckin | null; evening: DailyCheckin | null }>('/checkins/yesterday'),
  getWeek: () => api.get<{ week_start: string; checkins: { date: string; checked_in: boolean; checkin_type: string | null; slots: { morning: unknown; midday: unknown; evening: unknown }; slots_filled: number }[] }>('/checkins/week'),
  updateTomorrow: (data: { tomorrow_intention: string }) => api.put('/checkins/today/tomorrow', data),
  createMidday: (data: { energy_level: number; midday_note?: string }) => api.post<{ success: boolean; id: number }>('/checkins/midday', data),
  createEvening: (data: { did_not_train?: boolean; rest_type?: string; rest_note?: string; training_quality?: number; recovery_note?: string; tomorrow_intention?: string }) => api.post<{ success: boolean; id: number }>('/checkins/evening', data),
};

export const streaksApi = {
  getStatus: () => api.get<StreakStatus>('/streaks/status'),
  getByType: (type: 'checkin' | 'training' | 'readiness') => api.get<Streak>(`/streaks/${type}`),
};

export const feedApi = {
  getActivity: (params?: { limit?: number; offset?: number; days_back?: number; enrich_social?: boolean }) =>
    api.get('/feed/activity', { params }),
  getFriends: (params?: { limit?: number; offset?: number; days_back?: number }) =>
    api.get('/feed/friends', { params }),
};

export const socialApi = {
  // User search
  searchUsers: (query: string) => api.get('/social/users/search', { params: { q: query } }),
  getRecommended: () => api.get('/social/users/recommended'),

  // Friend suggestions (v0.2.0)
  getFriendSuggestions: (limit = 10) =>
    api.get('/social/friend-suggestions', { params: { limit } }),
  dismissSuggestion: (suggestedUserId: number) =>
    api.post(`/social/friend-suggestions/${suggestedUserId}/dismiss`),
  regenerateSuggestions: () =>
    api.post<{ success: boolean; suggestions_created: number }>('/social/friend-suggestions/regenerate'),
  browseFriends: (limit = 20) =>
    api.get('/social/friend-suggestions/browse', { params: { limit } }),

  // Friend Requests (v0.2.0)
  sendFriendRequest: (userId: number, data?: { connection_source?: string; request_message?: string }) =>
    api.post(`/social/friend-requests/${userId}`, data || {}),
  acceptFriendRequest: (connectionId: number) =>
    api.post(`/social/friend-requests/${connectionId}/accept`),
  declineFriendRequest: (connectionId: number) =>
    api.post(`/social/friend-requests/${connectionId}/decline`),
  cancelFriendRequest: (connectionId: number) =>
    api.delete(`/social/friend-requests/${connectionId}`),
  getReceivedRequests: () =>
    api.get<{ requests: { id: number; requester_id: number; requester_first_name: string; requester_last_name: string; requester_email: string; requester_avatar_url?: string; status: string; requested_at: string }[]; count: number }>('/social/friend-requests/received'),
  getSentRequests: () =>
    api.get<{ requests: (UserBasic & { status: string; requested_at: string })[]; count: number }>('/social/friend-requests/sent'),
  getFriends: (params?: { limit?: number; offset?: number }) =>
    api.get<{ friends: UserBasic[]; count: number }>('/social/friends', { params }),
  unfriend: (userId: number) =>
    api.delete(`/social/friends/${userId}`),
  getFriendshipStatus: (userId: number) =>
    api.get<{ status: string; are_friends: boolean }>(`/social/friends/${userId}/status`),

  // Relationships (legacy follow/unfollow)
  follow: (userId: number) => api.post(`/social/follow/${userId}`),
  unfollow: (userId: number) => api.delete(`/social/follow/${userId}`),
  getFollowers: () => api.get('/social/followers'),
  getFollowing: () => api.get('/social/following'),
  isFollowing: (userId: number) => api.get(`/social/following/${userId}`),

  // Likes
  like: (activityType: string, activityId: number) =>
    api.post('/social/like', { activity_type: activityType, activity_id: activityId }),
  unlike: (activityType: string, activityId: number) =>
    api.delete('/social/like', { data: { activity_type: activityType, activity_id: activityId } }),
  getLikes: (activityType: string, activityId: number) =>
    api.get(`/social/likes/${activityType}/${activityId}`),

  // Comments
  addComment: (activityType: string, activityId: number, commentText: string, parentCommentId?: number) =>
    api.post('/social/comment', {
      activity_type: activityType,
      activity_id: activityId,
      comment_text: commentText,
      parent_comment_id: parentCommentId,
    }),
  updateComment: (commentId: number, commentText: string) =>
    api.put(`/social/comment/${commentId}`, { comment_text: commentText }),
  deleteComment: (commentId: number) => api.delete(`/social/comment/${commentId}`),
  getComments: (activityType: string, activityId: number) =>
    api.get(`/social/comments/${activityType}/${activityId}`),
};

import axios from 'axios';
import type { Session, Readiness, Report, Suggestion, Technique, TrainedMovement, Video, Profile, Grading, Movement, Friend, CustomVideo, WeeklyGoalProgress, GoalsSummary, TrainingStreaks, GoalCompletionStreak, DailyCheckin, StreakStatus, Streak, Milestone, MilestoneProgress, CompEvent, WeightLog, WeightAverage, Group, GroupMember } from '../types';

// Paginated response type
interface PaginatedResponse<T> {
  techniques: T[];
  total: number;
  limit: number;
  offset: number;
}

// API base URL - use environment variable if set, otherwise default to relative path for production
// In development, Vite proxy will forward /api requests to localhost:8000
// In production, API and frontend are served from the same domain
// Using /api/v1 for versioned endpoints with backward compatibility via redirect middleware
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Extract a human-readable error message from an API error response.
 * Handles both structured format: { error: { message: "..." } }
 * and FastAPI format: { detail: "..." }
 */
export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: unknown } }).response;
    const data = resp?.data;
    if (data && typeof data === 'object') {
      // Structured error format: { error: { message: "..." } }
      if ('error' in data) {
        const errObj = (data as { error: { message?: string } }).error;
        if (errObj?.message) return errObj.message;
      }
      // FastAPI HTTPException format: { detail: "..." }
      if ('detail' in data) {
        const detail = (data as { detail: unknown }).detail;
        if (typeof detail === 'string') return detail;
      }
    }
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred. Please try again.';
}

// Response interceptor - handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          // Import auth API dynamically to avoid circular dependency
          const { authApi } = await import('./auth');
          const response = await authApi.refresh(refreshToken);

          localStorage.setItem('access_token', response.data.access_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api.request(originalRequest);
        } catch (refreshError) {
          // Refresh failed - logout user
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token - redirect to login
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const sessionsApi = {
  create: (data: any) => api.post<Session>('/sessions/', data),
  list: (limit = 10) => api.get<Session[]>(`/sessions/?limit=${limit}`),
  getById: (id: number) => api.get<Session>(`/sessions/${id}`),
  update: (id: number, data: any) => api.put<Session>(`/sessions/${id}`, data),
  delete: (id: number) => api.delete(`/sessions/${id}`),
  getByRange: (startDate: string, endDate: string) =>
    api.get<Session[]>(`/sessions/range/${startDate}/${endDate}`),
  getAutocomplete: () => api.get<{ gyms: string[]; locations: string[]; partners: string[]; techniques: string[] }>('/sessions/autocomplete/data'),
};

export const readinessApi = {
  create: (data: any) => api.post<Readiness>('/readiness/', data),
  getLatest: () => api.get<Readiness | null>('/readiness/latest'),
  getByDate: (date: string) => api.get<Readiness>(`/readiness/${date}`),
  getByRange: (startDate: string, endDate: string) =>
    api.get<Readiness[]>(`/readiness/range/${startDate}/${endDate}`),
  logWeightOnly: (data: { check_date: string; weight_kg: number }) =>
    api.post<Readiness>('/readiness/weight', data),
};

export const reportsApi = {
  getWeek: (targetDate?: string) => api.get<Report>('/reports/week', { params: { target_date: targetDate } }),
  getMonth: (targetDate?: string) => api.get<Report>('/reports/month', { params: { target_date: targetDate } }),
  getRange: (startDate: string, endDate: string) =>
    api.get<Report>(`/reports/range/${startDate}/${endDate}`),
  exportWeekCSV: (targetDate?: string) =>
    api.get('/reports/week/csv', {
      params: { target_date: targetDate },
      responseType: 'blob',
    }),
};

export const suggestionsApi = {
  getToday: (targetDate?: string) =>
    api.get<Suggestion>('/suggestions/today', { params: { target_date: targetDate } }),
};

export const techniquesApi = {
  create: (data: { name: string; category: string }) => api.post<TrainedMovement>('/techniques/', data),
  list: () => api.get<PaginatedResponse<TrainedMovement>>('/techniques/'),
  getStale: (days = 7) => api.get<TrainedMovement[]>(`/techniques/stale?days=${days}`),
  search: (query: string) => api.get<TrainedMovement[]>(`/techniques/search?q=${query}`),
  getById: (id: number) => api.get<TrainedMovement>(`/techniques/${id}`),
};

export const videosApi = {
  create: (data: { url: string; title?: string; movement_id?: number; video_type?: string }) => api.post<Video>('/videos/', data),
  list: () => api.get<{ videos: Video[]; total: number }>('/videos/'),
  delete: (id: number) => api.delete(`/videos/${id}`),
  getById: (id: number) => api.get<Video>(`/videos/${id}`),
};

export const profileApi = {
  get: () => api.get<Profile>('/profile/'),
  update: (data: Partial<Profile>) => api.put<Profile>('/profile/', data),
  uploadPhoto: (formData: FormData) => {
    return api.post<{ avatar_url: string; filename: string; message: string }>('/profile/photo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  deletePhoto: () => api.delete<{ message: string }>('/profile/photo'),
};

export const gradingsApi = {
  create: (data: { grade: string; date_graded: string; professor?: string; instructor_id?: number; notes?: string; photo_url?: string }) =>
    api.post<Grading>('/gradings/', data),
  list: () => api.get<Grading[]>('/gradings/'),
  getLatest: () => api.get<Grading | null>('/gradings/latest'),
  update: (id: number, data: Partial<Grading>) => api.put<Grading>(`/gradings/${id}`, data),
  delete: (id: number) => api.delete(`/gradings/${id}`),
  uploadPhoto: (formData: FormData) => {
    return api.post<{ photo_url: string; filename: string; message: string }>('/gradings/photo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export const glossaryApi = {
  list: (params?: { category?: string; search?: string; gi_only?: boolean; nogi_only?: boolean }) =>
    api.get<Movement[]>('/glossary/', { params }),
  getCategories: () => api.get<{ categories: string[] }>('/glossary/categories'),
  getById: (id: number, includeVideos = true) => api.get<Movement>(`/glossary/${id}?include_videos=${includeVideos}`),
  create: (data: { name: string; category: string; subcategory?: string; points?: number; description?: string; aliases?: string[]; gi_applicable?: boolean; nogi_applicable?: boolean }) =>
    api.post<Movement>('/glossary/', data),
  delete: (id: number) => api.delete(`/glossary/${id}`),
  addCustomVideo: (movementId: number, data: { url: string; title?: string; video_type?: string }) =>
    api.post<CustomVideo>(`/glossary/${movementId}/videos`, data),
  deleteCustomVideo: (movementId: number, videoId: number) =>
    api.delete(`/glossary/${movementId}/videos/${videoId}`),
};

export const friendsApi = {
  list: (params?: { search?: string; friend_type?: string }) =>
    api.get<Friend[]>('/friends/', { params }),
  listInstructors: () => api.get<Friend[]>('/friends/instructors'),
  listPartners: () => api.get<Friend[]>('/friends/partners'),
  getById: (id: number) => api.get<Friend>(`/friends/${id}`),
  create: (data: { name: string; friend_type?: string; belt_rank?: string; belt_stripes?: number; instructor_certification?: string; phone?: string; email?: string; notes?: string }) =>
    api.post<Friend>('/friends/', data),
  update: (id: number, data: Partial<Friend>) => api.put<Friend>(`/friends/${id}`, data),
  delete: (id: number) => api.delete(`/friends/${id}`),
};

export const usersApi = {
  search: (q: string, limit = 20) =>
    api.get('/users/search', { params: { q, limit } }),
  getProfile: (userId: number) =>
    api.get(`/users/${userId}`),
  getStats: (userId: number) =>
    api.get(`/users/${userId}/stats`),
  getActivity: (userId: number, params?: { limit?: number; offset?: number }) =>
    api.get(`/users/${userId}/activity`, { params }),
};

export const analyticsApi = {
  performanceOverview: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/performance-overview', { params }),
  partnerStats: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/partners/stats', { params }),
  headToHead: (partner1_id: number, partner2_id: number) =>
    api.get('/analytics/partners/head-to-head', { params: { partner1_id, partner2_id } }),
  readinessTrends: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/readiness/trends', { params }),
  whoopAnalytics: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/whoop/analytics', { params }),
  techniqueBreakdown: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/techniques/breakdown', { params }),
  consistencyMetrics: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/consistency/metrics', { params }),
  milestones: () => api.get('/analytics/milestones'),
  instructorInsights: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/instructors/insights', { params }),
  fightDynamicsHeatmap: (params?: { view?: string; weeks?: number; months?: number }) =>
    api.get('/analytics/fight-dynamics/heatmap', { params }),
  fightDynamicsInsights: () =>
    api.get('/analytics/fight-dynamics/insights'),
};

export const goalsApi = {
  getCurrentWeek: () => api.get<WeeklyGoalProgress>('/goals/current-week'),
  getSummary: () => api.get<GoalsSummary>('/goals/summary'),
  getTrainingStreaks: () => api.get<TrainingStreaks>('/goals/streaks/training'),
  getGoalStreaks: () => api.get<GoalCompletionStreak>('/goals/streaks/goals'),
  getTrend: (weeks = 12) => api.get('/goals/trend', { params: { weeks } }),
  updateTargets: (data: {
    weekly_sessions_target?: number;
    weekly_hours_target?: number;
    weekly_rolls_target?: number;
  }) => api.put<Profile>('/goals/targets', data),
};

// Engagement features (v0.2)
export const checkinsApi = {
  getToday: () => api.get<DailyCheckin & { checked_in: boolean }>('/checkins/today'),
  getWeek: () => api.get<{ week_start: string; checkins: any[] }>('/checkins/week'),
  updateTomorrow: (data: { tomorrow_intention: string }) => api.put('/checkins/today/tomorrow', data),
};

export const streaksApi = {
  getStatus: () => api.get<StreakStatus>('/streaks/status'),
  getByType: (type: 'checkin' | 'training' | 'readiness') => api.get<Streak>(`/streaks/${type}`),
};

export const milestonesApi = {
  getAchieved: () => api.get<{ milestones: Milestone[]; count: number }>('/milestones/achieved'),
  getProgress: () => api.get<{ progress: MilestoneProgress[] }>('/milestones/progress'),
  getClosest: () => api.get<{ has_milestone: boolean } & MilestoneProgress>('/milestones/closest'),
  getTotals: () => api.get<{ hours: number; sessions: number; rolls: number; partners: number; techniques: number; streak: number }>('/milestones/totals'),
};

export const restApi = {
  logRestDay: (data: { rest_type: string; note?: string; tomorrow_intention?: string; rest_date?: string }) =>
    api.post('/rest/', data),
  getRecent: (days = 30) => api.get('/rest/recent', { params: { days } }),
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
    api.get<{ suggestions: any[]; count: number }>('/social/friend-suggestions', { params: { limit } }),
  dismissSuggestion: (suggestedUserId: number) =>
    api.post(`/social/friend-suggestions/${suggestedUserId}/dismiss`),
  regenerateSuggestions: () =>
    api.post<{ success: boolean; suggestions_created: number }>('/social/friend-suggestions/regenerate'),

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
    api.get<{ requests: any[]; count: number }>('/social/friend-requests/received'),
  getSentRequests: () =>
    api.get<{ requests: any[]; count: number }>('/social/friend-requests/sent'),
  getFriends: (params?: { limit?: number; offset?: number }) =>
    api.get<{ friends: any[]; count: number }>('/social/friends', { params }),
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

export const photosApi = {
  upload: (formData: FormData) => {
    return api.post('/photos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getByActivity: (activityType: string, activityId: number) =>
    api.get(`/photos/activity/${activityType}/${activityId}`),
  getById: (photoId: number) => api.get(`/photos/${photoId}`),
  delete: (photoId: number) => api.delete(`/photos/${photoId}`),
  updateCaption: (photoId: number, caption: string) => {
    const formData = new FormData();
    formData.append('caption', caption);
    return api.put(`/photos/${photoId}/caption`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export const notificationsApi = {
  getCounts: () => api.get<{ feed_unread: number; friend_requests: number; total: number }>('/notifications/counts'),
  getAll: (params?: { limit?: number; offset?: number; unread_only?: boolean }) =>
    api.get<{ notifications: any[]; count: number }>('/notifications/', { params }),
  markAsRead: (notificationId: number) => api.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/notifications/read-all'),
  markFeedAsRead: () => api.post('/notifications/feed/read'),
  markFollowsAsRead: () => api.post('/notifications/follows/read'),
  deleteNotification: (notificationId: number) => api.delete(`/notifications/${notificationId}`),
};

export const gymsApi = {
  list: (verifiedOnly = true) =>
    api.get('/gyms', { params: { verified_only: verifiedOnly } }),
  search: (query: string, verifiedOnly = true) =>
    api.get('/gyms/search', { params: { q: query, verified_only: verifiedOnly } }),
};

export const adminApi = {
  // Dashboard
  getDashboardStats: () =>
    api.get('/admin/dashboard/stats'),

  // Gyms
  listGyms: (verifiedOnly = false) =>
    api.get('/admin/gyms', { params: { verified_only: verifiedOnly } }),
  getPendingGyms: () =>
    api.get('/admin/gyms/pending'),
  searchGyms: (query: string, verifiedOnly = false) =>
    api.get('/admin/gyms/search', { params: { q: query, verified_only: verifiedOnly } }),
  createGym: (data: { name: string; city?: string; state?: string; country?: string; address?: string; website?: string; email?: string; phone?: string; head_coach?: string; head_coach_belt?: string; google_maps_url?: string; verified?: boolean }) =>
    api.post('/admin/gyms', data),
  updateGym: (gymId: number, data: { name?: string; city?: string; state?: string; country?: string; address?: string; website?: string; email?: string; phone?: string; head_coach?: string; head_coach_belt?: string; google_maps_url?: string; verified?: boolean }) =>
    api.put(`/admin/gyms/${gymId}`, data),
  deleteGym: (gymId: number) =>
    api.delete(`/admin/gyms/${gymId}`),
  mergeGyms: (sourceGymId: number, targetGymId: number) =>
    api.post('/admin/gyms/merge', { source_gym_id: sourceGymId, target_gym_id: targetGymId }),
  verifyGym: (gymId: number) =>
    api.post(`/admin/gyms/${gymId}/verify`),
  rejectGym: (gymId: number, reason?: string) =>
    api.post(`/admin/gyms/${gymId}/reject`, { reason }),

  // Users
  listUsers: (params?: { search?: string; is_active?: boolean; is_admin?: boolean; limit?: number; offset?: number }) =>
    api.get('/admin/users', { params }),
  getUserDetails: (userId: number) =>
    api.get(`/admin/users/${userId}`),
  updateUser: (userId: number, data: { is_active?: boolean; is_admin?: boolean; subscription_tier?: string; is_beta_user?: boolean }) =>
    api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId: number) =>
    api.delete(`/admin/users/${userId}`),

  // Content Moderation
  listComments: (params?: { limit?: number; offset?: number }) =>
    api.get('/admin/comments', { params }),
  deleteComment: (commentId: number) =>
    api.delete(`/admin/comments/${commentId}`),

  // Techniques
  listTechniques: (params?: { search?: string; category?: string; custom_only?: boolean }) =>
    api.get('/admin/techniques', { params }),
  deleteTechnique: (techniqueId: number) =>
    api.delete(`/admin/techniques/${techniqueId}`),

  // Waitlist (v0.2.0)
  listWaitlist: (params?: { status?: string; search?: string; limit?: number; offset?: number }) =>
    api.get<{ entries: any[]; total: number; limit: number; offset: number }>('/admin/waitlist', { params }),
  getWaitlistStats: () =>
    api.get<{ total: number; waiting: number; invited: number; registered: number; declined: number }>('/admin/waitlist/stats'),
  inviteWaitlistEntry: (waitlistId: number, tier = 'free') =>
    api.post(`/admin/waitlist/${waitlistId}/invite`, { tier }),
  bulkInviteWaitlist: (ids: number[], tier = 'free') =>
    api.post('/admin/waitlist/bulk-invite', { ids, tier }),
  declineWaitlistEntry: (waitlistId: number) =>
    api.post(`/admin/waitlist/${waitlistId}/decline`),
  updateWaitlistNotes: (waitlistId: number, notes: string) =>
    api.put(`/admin/waitlist/${waitlistId}/notes`, { notes }),

  // Feedback (v0.2.0)
  listFeedback: (params?: { status?: string; category?: string; limit?: number; offset?: number }) =>
    api.get<{ feedback: any[]; count: number; stats: any }>('/admin/feedback', { params }),
  updateFeedbackStatus: (feedbackId: number, status: string, adminNotes?: string) =>
    api.put(`/admin/feedback/${feedbackId}/status`, { status, admin_notes: adminNotes }),
  getFeedbackStats: () =>
    api.get<{ total: number; by_status: any; by_category: any }>('/admin/feedback/stats'),
};

// Feedback API (v0.2.0)
export const feedbackApi = {
  submit: (data: {
    category: 'bug' | 'feature' | 'improvement' | 'question' | 'other';
    subject?: string;
    message: string;
    platform?: 'web' | 'cli' | 'api';
    url?: string;
  }) => api.post<{ success: boolean; feedback: any }>('/feedback/', data),
  getMy: (limit = 50) =>
    api.get<{ feedback: any[]; count: number }>('/feedback/my', { params: { limit } }),
  getById: (feedbackId: number) =>
    api.get('/feedback/' + feedbackId),
};

// Waitlist API (v0.2.0)
export const waitlistApi = {
  join: (data: { email: string; first_name?: string; gym_name?: string; belt_rank?: string; referral_source?: string }) =>
    api.post<{ position: number; message: string }>('/waitlist/join', data),
  getCount: () =>
    api.get<{ count: number }>('/waitlist/count'),
};


// Groups API (v0.3)
export const groupsApi = {
  create: (data: { name: string; description?: string; group_type?: string; privacy?: string; gym_id?: number; avatar_url?: string }) =>
    api.post<Group>('/groups/', data),
  list: () =>
    api.get<{ groups: Group[]; count: number }>('/groups/'),
  get: (groupId: number) =>
    api.get<Group & { members: GroupMember[]; member_count: number; user_role: string | null }>(`/groups/${groupId}`),
  update: (groupId: number, data: { name?: string; description?: string; group_type?: string; privacy?: string; gym_id?: number; avatar_url?: string }) =>
    api.put<Group>(`/groups/${groupId}`, data),
  delete: (groupId: number) =>
    api.delete(`/groups/${groupId}`),
  addMember: (groupId: number, userId: number, role = 'member') =>
    api.post(`/groups/${groupId}/members`, { user_id: userId, role }),
  removeMember: (groupId: number, userId: number) =>
    api.delete(`/groups/${groupId}/members/${userId}`),
  join: (groupId: number) =>
    api.post(`/groups/${groupId}/join`),
  leave: (groupId: number) =>
    api.post(`/groups/${groupId}/leave`),
};

// Dashboard API (v0.2.0)
export const dashboardApi = {
  getSummary: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/dashboard/summary', { params }),
  getQuickStats: () =>
    api.get<{ total_sessions: number; total_hours: number; current_streak: number; next_milestone: any }>('/dashboard/quick-stats'),
  getWeekSummary: (weekOffset = 0) =>
    api.get('/dashboard/week-summary', { params: { week_offset: weekOffset } }),
};

// Events & Competition Prep API (v0.3)
export const eventsApi = {
  create: (data: Partial<CompEvent>) => api.post<CompEvent>('/events/', data),
  list: (status?: string) => api.get<{ events: CompEvent[]; total: number }>('/events/', { params: { status } }),
  get: (id: number) => api.get<CompEvent>(`/events/${id}`),
  update: (id: number, data: Partial<CompEvent>) => api.put<CompEvent>(`/events/${id}`, data),
  delete: (id: number) => api.delete(`/events/${id}`),
  getNext: () => api.get<{ event: CompEvent | null; days_until: number | null; current_weight: number | null }>('/events/next'),
};

export const weightLogsApi = {
  create: (data: { weight: number; logged_date?: string; time_of_day?: string; notes?: string }) =>
    api.post<{ id: number; message: string }>('/events/weight-logs/', data),
  list: (params?: { start_date?: string; end_date?: string }) =>
    api.get<{ logs: WeightLog[]; total: number }>('/events/weight-logs/', { params }),
  getLatest: () => api.get<WeightLog | { weight: null; logged_date: null }>('/events/weight-logs/latest'),
  getAverages: (period?: string) =>
    api.get<{ averages: WeightAverage[]; period: string }>('/events/weight-logs/averages', { params: { period } }),
};

// Game Plans API (My Game)
export const gamePlansApi = {
  generate: (data: { belt_level: string; archetype: string; style?: string }) =>
    api.post('/game-plans/generate', data),
  getCurrent: () => api.get('/game-plans/'),
  getById: (id: number) => api.get(`/game-plans/${id}`),
  update: (id: number, data: Record<string, unknown>) =>
    api.patch(`/game-plans/${id}`, data),
  delete: (id: number) => api.delete(`/game-plans/${id}`),
  addNode: (planId: number, data: { name: string; node_type?: string; parent_id?: number; glossary_id?: number }) =>
    api.post(`/game-plans/${planId}/nodes`, data),
  updateNode: (planId: number, nodeId: number, data: Record<string, unknown>) =>
    api.patch(`/game-plans/${planId}/nodes/${nodeId}`, data),
  deleteNode: (planId: number, nodeId: number) =>
    api.delete(`/game-plans/${planId}/nodes/${nodeId}`),
  addEdge: (planId: number, data: { from_node_id: number; to_node_id: number; edge_type?: string; label?: string }) =>
    api.post(`/game-plans/${planId}/edges`, data),
  deleteEdge: (planId: number, edgeId: number) =>
    api.delete(`/game-plans/${planId}/edges/${edgeId}`),
  setFocus: (planId: number, nodeIds: number[]) =>
    api.post(`/game-plans/${planId}/focus`, { node_ids: nodeIds }),
};

// Enhanced Grapple API
export const grappleApi = {
  getInfo: () => api.get('/grapple/info'),
  getSessions: () => api.get('/grapple/sessions'),
  getSession: (sessionId: string) => api.get(`/grapple/sessions/${sessionId}`),
  deleteSession: (sessionId: string) => api.delete(`/grapple/sessions/${sessionId}`),
  chat: (data: { message: string; session_id: string | null }) =>
    api.post('/grapple/chat', data),
  submitFeedback: (data: { message_id: string; rating: string }) =>
    api.post('/admin/grapple/feedback', data),
  extractSession: (text: string) =>
    api.post('/grapple/extract-session', { text }),
  saveExtractedSession: (data: Record<string, unknown>) =>
    api.post('/grapple/save-extracted-session', data),
  getInsights: (params?: { limit?: number; insight_type?: string }) =>
    api.get('/grapple/insights', { params }),
  generateInsight: (data: { insight_type: string; session_id?: number }) =>
    api.post('/grapple/insights/generate', data),
  techniqueQA: (question: string) =>
    api.post('/grapple/technique-qa', { question }),
};

import { api, userTz } from './_client';
import type { MilestoneProgress } from '../types';

// Dashboard API (v0.2.0)
export const dashboardApi = {
  getSummary: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/dashboard/summary', { params: { ...params, tz: userTz } }),
  getQuickStats: () =>
    api.get<{ total_sessions: number; total_hours: number; current_streak: number; next_milestone: MilestoneProgress | null }>('/dashboard/quick-stats'),
  getWeekSummary: (weekOffset = 0) =>
    api.get('/dashboard/week-summary', { params: { week_offset: weekOffset, tz: userTz } }),
};

export const notificationsApi = {
  getCounts: () => api.get<{ feed_unread: number; friend_requests: number; total: number }>('/notifications/counts'),
  getAll: (params?: { limit?: number; offset?: number; unread_only?: boolean }) =>
    api.get<{ notifications: Record<string, unknown>[]; count: number }>('/notifications/', { params }),
  markAsRead: (notificationId: number) => api.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/notifications/read-all'),
  markFeedAsRead: () => api.post('/notifications/feed/read'),
  markFollowsAsRead: () => api.post('/notifications/follows/read'),
  deleteNotification: (notificationId: number) => api.delete(`/notifications/${notificationId}`),
};

export const restApi = {
  logRestDay: (data: { rest_type: string; rest_note?: string; tomorrow_intention?: string; check_date?: string }) =>
    api.post('/rest/', data),
  getRecent: (days = 30) => api.get('/rest/recent', { params: { days } }),
  getByDate: (date: string) => api.get(`/rest/by-date/${date}`),
  delete: (checkinId: number) => api.delete(`/rest/${checkinId}`),
};

import axios from 'axios';
import type { Session, Readiness, Report, Suggestion, Technique, Video, Profile, Grading, Movement, Contact, CustomVideo, WeeklyGoalProgress, GoalsSummary, TrainingStreaks, GoalCompletionStreak } from '../types';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sessionsApi = {
  create: (data: any) => api.post<Session>('/sessions/', data),
  list: (limit = 10) => api.get<Session[]>(`/sessions/?limit=${limit}`),
  getById: (id: number) => api.get<Session>(`/sessions/${id}`),
  update: (id: number, data: any) => api.put<Session>(`/sessions/${id}`, data),
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
  create: (data: { name: string; category?: string }) => api.post<Technique>('/techniques/', data),
  list: () => api.get<Technique[]>('/techniques/'),
  getStale: (days = 7) => api.get<Technique[]>(`/techniques/stale?days=${days}`),
  search: (query: string) => api.get<Technique[]>(`/techniques/search?q=${query}`),
  getById: (id: number) => api.get<Technique>(`/techniques/${id}`),
};

export const videosApi = {
  create: (data: any) => api.post<Video>('/videos/', data),
  list: () => api.get<Video[]>('/videos/'),
  getByTechnique: (name: string) => api.get<Video[]>(`/videos/technique/${name}`),
  search: (query: string) => api.get<Video[]>(`/videos/search?q=${query}`),
  delete: (id: number) => api.delete(`/videos/${id}`),
  getById: (id: number) => api.get<Video>(`/videos/${id}`),
};

export const profileApi = {
  get: () => api.get<Profile>('/profile/'),
  update: (data: Partial<Profile>) => api.put<Profile>('/profile/', data),
};

export const gradingsApi = {
  create: (data: { grade: string; date_graded: string; professor?: string; notes?: string }) =>
    api.post<Grading>('/gradings/', data),
  list: () => api.get<Grading[]>('/gradings/'),
  getLatest: () => api.get<Grading | null>('/gradings/latest'),
  update: (id: number, data: Partial<Grading>) => api.put<Grading>(`/gradings/${id}`, data),
  delete: (id: number) => api.delete(`/gradings/${id}`),
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

export const contactsApi = {
  list: (params?: { search?: string; contact_type?: string }) =>
    api.get<Contact[]>('/contacts/', { params }),
  listInstructors: () => api.get<Contact[]>('/contacts/instructors'),
  listPartners: () => api.get<Contact[]>('/contacts/partners'),
  getById: (id: number) => api.get<Contact>(`/contacts/${id}`),
  create: (data: { name: string; contact_type?: string; belt_rank?: string; belt_stripes?: number; instructor_certification?: string; phone?: string; email?: string; notes?: string }) =>
    api.post<Contact>('/contacts/', data),
  update: (id: number, data: Partial<Contact>) => api.put<Contact>(`/contacts/${id}`, data),
  delete: (id: number) => api.delete(`/contacts/${id}`),
};

export const analyticsApi = {
  performanceOverview: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/performance-overview', { params }),
  partnerStats: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/partners/stats', { params }),
  headToHead: (partner1_id: number, partner2_id: number) =>
    api.get('/analytics/partners/head-to-head', { params: { partner1_id, partner2_id } }),
  readinessTrends: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/readiness/trends', { params }),
  whoopAnalytics: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/whoop/analytics', { params }),
  techniqueBreakdown: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/techniques/breakdown', { params }),
  consistencyMetrics: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/consistency/metrics', { params }),
  milestones: () => api.get('/analytics/milestones'),
  instructorInsights: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/instructors/insights', { params }),
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

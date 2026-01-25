import axios from 'axios';
import type { Session, Readiness, Report, Suggestion, Technique, Video, Profile, Grading } from '../types';

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
  create: (data: { grade: string; date_graded: string; notes?: string }) =>
    api.post<Grading>('/gradings/', data),
  list: () => api.get<Grading[]>('/gradings/'),
  getLatest: () => api.get<Grading | null>('/gradings/latest'),
  delete: (id: number) => api.delete(`/gradings/${id}`),
};

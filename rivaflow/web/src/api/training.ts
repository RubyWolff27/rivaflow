import { api } from './_client';
import type { Session, SessionScoreBreakdown, SessionRoll, SessionTechnique, Readiness, Report, Suggestion, TrainedMovement } from '../types';

interface PaginatedResponse<T> {
  techniques: T[];
  total: number;
  limit: number;
  offset: number;
}

/** Payload for creating or updating a session — all Session fields optional plus roll/technique arrays */
interface SessionPayload extends Partial<Session> {
  session_rolls?: SessionRoll[];
  session_techniques?: SessionTechnique[];
  visibility_level?: string;
}

export const sessionsApi = {
  create: (data: SessionPayload) => api.post<Session>('/sessions/', data),
  list: (limit = 10) => api.get<Session[]>(`/sessions/?limit=${limit}`),
  getById: (id: number) => api.get<Session>(`/sessions/${id}`),
  getWithRolls: (id: number) => api.get<Session>(`/sessions/${id}/with-rolls`),
  getInsights: (id: number) => api.get<{ insights: { type: string; title: string; description: string; icon: string }[] }>(`/sessions/${id}/insights`),
  update: (id: number, data: SessionPayload) => api.put<Session>(`/sessions/${id}`, data),
  delete: (id: number) => api.delete(`/sessions/${id}`),
  getByRange: (startDate: string, endDate: string) =>
    api.get<Session[]>(`/sessions/range/${startDate}/${endDate}`),
  getAutocomplete: () => api.get<{ gyms: string[]; locations: string[]; partners: string[]; techniques: string[] }>('/sessions/autocomplete/data'),
  getScore: (id: number) => api.get<{ session_id: number; session_score: number | null; score_breakdown: SessionScoreBreakdown | null }>(`/sessions/${id}/score`),
  recalculateScore: (id: number) => api.post<{ session_id: number; session_score: number; score_breakdown: SessionScoreBreakdown }>(`/sessions/${id}/score/recalculate`),
  backfillScores: () => api.post<{ scored: number; skipped: number; total: number }>('/sessions/scores/backfill'),
};

export const readinessApi = {
  create: (data: Partial<Readiness>) => api.post<Readiness>('/readiness/', data),
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

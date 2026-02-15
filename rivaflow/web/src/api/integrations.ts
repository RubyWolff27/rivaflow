import { api } from './_client';
import type { WhoopConnectionStatus, WhoopWorkoutMatch, WhoopRecovery, WhoopScopeCheck, WhoopReadinessAutoFill, WhoopSessionContext } from '../types';

// Transcription API (Whisper)
export const transcribeApi = {
  transcribe: (formData: FormData) =>
    api.post<{ transcript: string }>('/transcribe/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }),
};

// WHOOP Integration API
export const whoopApi = {
  getStatus: () =>
    api.get<WhoopConnectionStatus>('/integrations/whoop/status'),
  getAuthorizeUrl: () =>
    api.get<{ authorization_url: string }>('/integrations/whoop/authorize'),
  sync: () =>
    api.post<{ total_fetched: number; created: number; updated: number; auto_sessions_created: number }>('/integrations/whoop/sync'),
  getWorkouts: (params?: { session_id?: number; session_date?: string; class_time?: string; duration_mins?: number }) =>
    api.get<{ workouts: WhoopWorkoutMatch[]; count: number }>('/integrations/whoop/workouts', { params }),
  matchWorkout: (data: { session_id: number; workout_cache_id: number }) =>
    api.post('/integrations/whoop/match', data),
  disconnect: () =>
    api.delete<{ disconnected: boolean }>('/integrations/whoop'),
  syncRecovery: () =>
    api.post<{ total_fetched: number; created: number; updated: number }>('/integrations/whoop/sync-recovery'),
  getLatestRecovery: () =>
    api.get<WhoopRecovery>('/integrations/whoop/recovery/latest'),
  checkScopes: () =>
    api.get<WhoopScopeCheck>('/integrations/whoop/scope-check'),
  getReadinessAutoFill: (date: string) =>
    api.get<{ auto_fill: WhoopReadinessAutoFill | null }>('/integrations/whoop/readiness/auto-fill', { params: { date } }),
  sessionContext: (sessionId: number) =>
    api.get<WhoopSessionContext>(`/integrations/whoop/session/${sessionId}/context`),
  setAutoCreate: (enabled: boolean) =>
    api.post('/integrations/whoop/auto-create-sessions', { enabled }),
  setAutoFillReadiness: (enabled: boolean) =>
    api.post('/integrations/whoop/auto-fill-readiness', { enabled }),
  getZonesBatch: (sessionIds: number[]) =>
    api.get<{ zones: Record<string, { zone_durations: Record<string, number> | null; strain: number | null; calories: number | null; score_state: string | null } | null> }>('/integrations/whoop/zones/batch', { params: { session_ids: sessionIds.join(',') } }),
  getZonesWeekly: (weekOffset = 0, tz?: string) =>
    api.get<{ totals: Record<string, number>; session_count: number; week_start: string; week_end: string }>('/integrations/whoop/zones/weekly', { params: { week_offset: weekOffset, tz } }),
};

// Chat API (general chat, separate from Grapple)
export const chatApi = {
  send: (messages: { role: string; content: string }[]) =>
    api.post<{ reply: string }>('/chat/', { messages }),
};

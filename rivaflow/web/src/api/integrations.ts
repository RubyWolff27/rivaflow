import { api } from './_client';
import type { GarminDailyMetric } from '../types';

// Garmin metrics API — daily key metrics power the Health tab; per-session
// Garmin biometrics ride on the session object (no dedicated endpoint).
export const garminApi = {
  dailyMetrics: (days = 30) =>
    api.get<GarminDailyMetric[]>(`/garmin/daily?days=${days}`),
  summary: () =>
    api.get<{ latest: GarminDailyMetric | null }>('/garmin/summary'),
};

// Transcription API (Whisper)
export const transcribeApi = {
  transcribe: (formData: FormData) =>
    api.post<{ transcript: string }>('/transcribe/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }),
};

// Chat API (general chat, separate from Grapple)
export const chatApi = {
  send: (messages: { role: string; content: string }[]) =>
    api.post<{ reply: string }>('/chat/', { messages }),
};

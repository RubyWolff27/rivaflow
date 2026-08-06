import { api } from './_client';

// Feedback API (v0.2.0)
export const feedbackApi = {
  submit: (data: {
    category: 'bug' | 'feature' | 'improvement' | 'question' | 'other';
    subject?: string;
    message: string;
    platform?: 'web' | 'cli' | 'api';
    url?: string;
  }) => api.post('/feedback/', data),
  getMy: (limit = 50) =>
    api.get('/feedback/my', { params: { limit } }),
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


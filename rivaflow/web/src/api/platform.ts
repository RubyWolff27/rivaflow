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

import { api } from './_client';
import type { Movement, Video, CustomVideo } from '../types';

export const videosApi = {
  create: (data: { url: string; title?: string; movement_id?: number; video_type?: string }) => api.post<Video>('/videos/', data),
  list: () => api.get<{ videos: Video[]; total: number }>('/videos/'),
  delete: (id: number) => api.delete(`/videos/${id}`),
  getById: (id: number) => api.get<Video>(`/videos/${id}`),
};

export const glossaryApi = {
  list: (params?: { category?: string; search?: string; gi_only?: boolean; nogi_only?: boolean; limit?: number }) =>
    api.get<Movement[]>('/glossary/', { params: { limit: 1000, ...params } }),
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

export const coachPreferencesApi = {
  get: () => api.get('/coach-preferences/'),
  update: (data: Record<string, unknown>) =>
    api.put('/coach-preferences/', data),
};

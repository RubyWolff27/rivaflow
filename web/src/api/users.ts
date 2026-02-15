import { api } from './_client';
import type { Profile, Grading, Friend } from '../types';

interface OnboardingStep {
  key: string;
  label: string;
  done: boolean;
}

interface OnboardingStatus {
  steps: OnboardingStep[];
  completed: number;
  total: number;
  all_done: boolean;
  profile_completion: {
    filled: number;
    total: number;
    percentage: number;
    missing: string[];
  };
}

export const profileApi = {
  get: () => api.get<Profile>('/profile/'),
  update: (data: Partial<Profile>) => api.put<Profile>('/profile/', data),
  getOnboardingStatus: () => api.get<OnboardingStatus>('/profile/onboarding-status'),
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

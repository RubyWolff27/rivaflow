import { api } from './_client';
import type { Group, GroupMember, GymClass } from '../types';

export const photosApi = {
  upload: (formData: FormData) => {
    return api.post('/photos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getByActivity: (activityType: string, activityId: number) =>
    api.get(`/photos/activity/${activityType}/${activityId}`),
  getById: (photoId: number) => api.get(`/photos/${photoId}`),
  delete: (photoId: number) => api.delete(`/photos/${photoId}`),
  updateCaption: (photoId: number, caption: string) => {
    const formData = new FormData();
    formData.append('caption', caption);
    return api.put(`/photos/${photoId}/caption`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export const gymsApi = {
  list: (verifiedOnly = true) =>
    api.get('/gyms', { params: { verified_only: verifiedOnly } }),
  search: (query: string, verifiedOnly = true) =>
    api.get('/gyms/search', { params: { q: query, verified_only: verifiedOnly } }),
  getTimetable: (gymId: number) =>
    api.get<{ gym_id: number; gym_name: string; timetable: Record<string, GymClass[]> }>(`/gyms/${gymId}/timetable`),
  getTodaysClasses: (gymId: number) =>
    api.get<{ gym_id: number; gym_name: string; classes: GymClass[] }>(`/gyms/${gymId}/timetable/today`),
};

// Groups API (v0.3)
export const groupsApi = {
  create: (data: { name: string; description?: string; group_type?: string; privacy?: string; gym_id?: number; avatar_url?: string }) =>
    api.post<Group>('/groups/', data),
  list: () =>
    api.get<{ groups: Group[]; count: number }>('/groups/'),
  discover: () =>
    api.get<{ groups: Group[]; count: number }>('/groups/discover'),
  get: (groupId: number) =>
    api.get<Group & { members: GroupMember[]; member_count: number; user_role: string | null }>(`/groups/${groupId}`),
  update: (groupId: number, data: { name?: string; description?: string; group_type?: string; privacy?: string; gym_id?: number; avatar_url?: string }) =>
    api.put<Group>(`/groups/${groupId}`, data),
  delete: (groupId: number) =>
    api.delete(`/groups/${groupId}`),
  addMember: (groupId: number, userId: number, role = 'member') =>
    api.post(`/groups/${groupId}/members`, { user_id: userId, role }),
  removeMember: (groupId: number, userId: number) =>
    api.delete(`/groups/${groupId}/members/${userId}`),
  join: (groupId: number) =>
    api.post(`/groups/${groupId}/join`),
  leave: (groupId: number) =>
    api.post(`/groups/${groupId}/leave`),
};

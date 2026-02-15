import { api } from './_client';

export const adminApi = {
  // Dashboard
  getDashboardStats: () =>
    api.get('/admin/dashboard/stats'),

  // Gyms
  listGyms: (verifiedOnly = false) =>
    api.get('/admin/gyms', { params: { verified_only: verifiedOnly } }),
  getPendingGyms: () =>
    api.get('/admin/gyms/pending'),
  searchGyms: (query: string, verifiedOnly = false) =>
    api.get('/admin/gyms/search', { params: { q: query, verified_only: verifiedOnly } }),
  createGym: (data: { name: string; city?: string; state?: string; country?: string; address?: string; website?: string; email?: string; phone?: string; head_coach?: string; head_coach_belt?: string; google_maps_url?: string; verified?: boolean }) =>
    api.post('/admin/gyms', data),
  updateGym: (gymId: number, data: { name?: string; city?: string; state?: string; country?: string; address?: string; website?: string; email?: string; phone?: string; head_coach?: string; head_coach_belt?: string; google_maps_url?: string; verified?: boolean }) =>
    api.put(`/admin/gyms/${gymId}`, data),
  deleteGym: (gymId: number) =>
    api.delete(`/admin/gyms/${gymId}`),
  mergeGyms: (sourceGymId: number, targetGymId: number) =>
    api.post('/admin/gyms/merge', { source_gym_id: sourceGymId, target_gym_id: targetGymId }),
  verifyGym: (gymId: number) =>
    api.post(`/admin/gyms/${gymId}/verify`),
  rejectGym: (gymId: number, reason?: string) =>
    api.post(`/admin/gyms/${gymId}/reject`, { reason }),

  // Users
  listUsers: (params?: { search?: string; is_active?: boolean; is_admin?: boolean; limit?: number; offset?: number }) =>
    api.get('/admin/users', { params }),
  getUserDetails: (userId: number) =>
    api.get(`/admin/users/${userId}`),
  updateUser: (userId: number, data: { is_active?: boolean; is_admin?: boolean; subscription_tier?: string; is_beta_user?: boolean }) =>
    api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId: number) =>
    api.delete(`/admin/users/${userId}`),

  // Content Moderation
  listComments: (params?: { limit?: number; offset?: number }) =>
    api.get('/admin/comments', { params }),
  deleteComment: (commentId: number) =>
    api.delete(`/admin/comments/${commentId}`),

  // Techniques
  listTechniques: (params?: { search?: string; category?: string; custom_only?: boolean }) =>
    api.get('/admin/techniques', { params }),
  deleteTechnique: (techniqueId: number) =>
    api.delete(`/admin/techniques/${techniqueId}`),

  // Waitlist (v0.2.0)
  listWaitlist: (params?: { status?: string; search?: string; limit?: number; offset?: number }) =>
    api.get('/admin/waitlist', { params }),
  getWaitlistStats: () =>
    api.get<{ total: number; waiting: number; invited: number; registered: number; declined: number }>('/admin/waitlist/stats'),
  inviteWaitlistEntry: (waitlistId: number, tier = 'free') =>
    api.post(`/admin/waitlist/${waitlistId}/invite`, { tier }),
  bulkInviteWaitlist: (ids: number[], tier = 'free') =>
    api.post('/admin/waitlist/bulk-invite', { ids, tier }),
  declineWaitlistEntry: (waitlistId: number) =>
    api.post(`/admin/waitlist/${waitlistId}/decline`),
  updateWaitlistNotes: (waitlistId: number, notes: string) =>
    api.put(`/admin/waitlist/${waitlistId}/notes`, { notes }),

  // Feedback (v0.2.0)
  listFeedback: (params?: { status?: string; category?: string; limit?: number; offset?: number }) =>
    api.get('/admin/feedback', { params }),
  updateFeedbackStatus: (feedbackId: number, status: string, adminNotes?: string) =>
    api.put(`/admin/feedback/${feedbackId}/status`, { status, admin_notes: adminNotes }),
  getFeedbackStats: () =>
    api.get('/admin/feedback/stats'),

  // Broadcast email
  broadcastEmail: (data: { subject: string; html_body: string; text_body?: string }) =>
    api.post('/admin/email/broadcast', data),

  // Grapple AI admin
  getGrappleGlobalStats: (days = 30) =>
    api.get('/admin/grapple/stats/global', { params: { days } }),
  getGrappleProjections: () =>
    api.get('/admin/grapple/stats/projections'),
  getGrappleProviderStats: (days = 7) =>
    api.get('/admin/grapple/stats/providers', { params: { days } }),
  getGrappleTopUsers: (limit = 10) =>
    api.get('/admin/grapple/stats/users', { params: { limit } }),
  getGrappleFeedback: (limit = 20) =>
    api.get('/admin/grapple/feedback', { params: { limit } }),
  getGrappleFeedbackSummary: (data: { session_ids: string[] }) =>
    api.post('/admin/grapple/feedback/summary', data),
};

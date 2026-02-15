import { api } from './_client';

export const analyticsApi = {
  performanceOverview: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/performance-overview', { params }),
  partnerStats: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/partners/stats', { params }),
  headToHead: (partner1_id: number, partner2_id: number) =>
    api.get('/analytics/partners/head-to-head', { params: { partner1_id, partner2_id } }),
  readinessTrends: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/readiness/trends', { params }),
  whoopAnalytics: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/whoop/analytics', { params }),
  techniqueBreakdown: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/techniques/breakdown', { params }),
  consistencyMetrics: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/consistency/metrics', { params }),
  milestones: () => api.get('/analytics/milestones'),
  instructorInsights: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/instructors/insights', { params }),
  fightDynamicsHeatmap: (params?: { view?: string; weeks?: number; months?: number }) =>
    api.get('/analytics/fight-dynamics/heatmap', { params }),
  fightDynamicsInsights: () =>
    api.get('/analytics/fight-dynamics/insights'),

  // Phase 1: Enhanced analytics
  durationTrends: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/duration/trends', { params }),
  timeOfDayPatterns: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/time-of-day/patterns', { params }),
  gymComparison: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/gyms/comparison', { params }),
  classTypeEffectiveness: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/class-types/effectiveness', { params }),
  weightTrend: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/weight/trend', { params }),
  trainingCalendar: (params?: { start_date?: string; end_date?: string; types?: string[] }) =>
    api.get('/analytics/training-calendar', { params }),
  partnerBeltDistribution: () =>
    api.get('/analytics/partners/belt-distribution'),

  // Phase 2: Insights engine
  insightsSummary: () =>
    api.get('/analytics/insights/summary'),
  readinessCorrelation: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/insights/readiness-correlation', { params }),
  trainingLoad: (params?: { days?: number }) =>
    api.get('/analytics/insights/training-load', { params }),
  techniqueEffectiveness: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/insights/technique-effectiveness', { params }),
  partnerProgression: (partnerId: number) =>
    api.get(`/analytics/insights/partner-progression/${partnerId}`),
  sessionQuality: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/analytics/insights/session-quality', { params }),
  overtTrainingRisk: () =>
    api.get('/analytics/insights/overtraining-risk'),
  recoveryInsights: (params?: { days?: number }) =>
    api.get('/analytics/insights/recovery', { params }),
  checkinTrends: (params?: { days?: number }) =>
    api.get('/analytics/insights/checkin-trends', { params }),

  // Phase 3: WHOOP Performance Science
  whoopPerformanceCorrelation: (params?: { days?: number }) =>
    api.get('/analytics/whoop/performance-correlation', { params }),
  whoopEfficiency: (params?: { days?: number }) =>
    api.get('/analytics/whoop/efficiency', { params }),
  whoopCardiovascular: (params?: { days?: number }) =>
    api.get('/analytics/whoop/cardiovascular', { params }),
  whoopSleepDebt: (params?: { days?: number }) =>
    api.get('/analytics/whoop/sleep-debt', { params }),
  whoopReadinessModel: (params?: { days?: number }) =>
    api.get('/analytics/whoop/readiness-model', { params }),
};

// Enhanced Grapple API
export const grappleApi = {
  getInfo: () => api.get('/grapple/info'),
  getSessions: () => api.get('/grapple/sessions'),
  getSession: (sessionId: string) => api.get(`/grapple/sessions/${sessionId}`),
  deleteSession: (sessionId: string) => api.delete(`/grapple/sessions/${sessionId}`),
  chat: (data: { message: string; session_id: string | null }) =>
    api.post('/grapple/chat', data),
  submitFeedback: (data: { message_id: string; rating: string }) =>
    api.post('/admin/grapple/feedback', data),
  extractSession: (text: string) =>
    api.post('/grapple/extract-session', { text }),
  saveExtractedSession: (data: Record<string, unknown>) =>
    api.post('/grapple/save-extracted-session', data),
  getInsights: (params?: { limit?: number; insight_type?: string }) =>
    api.get('/grapple/insights', { params }),
  generateInsight: (data: { insight_type: string; session_id?: number }) =>
    api.post('/grapple/insights/generate', data),
  createInsightChat: (insightId: number) =>
    api.post<{ chat_session_id: string }>(`/grapple/insights/${insightId}/chat`),
  techniqueQA: (question: string) =>
    api.post('/grapple/technique-qa', { question }),
};

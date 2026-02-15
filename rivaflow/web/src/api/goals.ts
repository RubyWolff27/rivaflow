import { api, userTz } from './_client';
import type { WeeklyGoalProgress, GoalsSummary, TrainingStreaks, GoalCompletionStreak, Profile, TrainingGoal, CompEvent, WeightLog, WeightAverage, MilestoneProgress, Milestone } from '../types';

export const goalsApi = {
  getCurrentWeek: () => api.get<WeeklyGoalProgress>('/goals/current-week', { params: { tz: userTz } }),
  getSummary: () => api.get<GoalsSummary>('/goals/summary', { params: { tz: userTz } }),
  getTrainingStreaks: () => api.get<TrainingStreaks>('/goals/streaks/training'),
  getGoalStreaks: () => api.get<GoalCompletionStreak>('/goals/streaks/goals'),
  getTrend: (weeks = 12) => api.get('/goals/trend', { params: { weeks } }),
  updateTargets: (data: {
    weekly_sessions_target?: number;
    weekly_hours_target?: number;
    weekly_rolls_target?: number;
  }) => api.put<Profile>('/goals/targets', data),
};

export const trainingGoalsApi = {
  list: (month?: string) => api.get<TrainingGoal[]>('/training-goals/', { params: month ? { month } : {} }),
  get: (id: number) => api.get<TrainingGoal>(`/training-goals/${id}`),
  create: (data: {
    goal_type: string;
    metric: string;
    target_value: number;
    month: string;
    movement_id?: number | null;
    class_type_filter?: string | null;
  }) => api.post<TrainingGoal>('/training-goals/', data),
  update: (id: number, data: { target_value?: number; is_active?: boolean }) =>
    api.put<TrainingGoal>(`/training-goals/${id}`, data),
  delete: (id: number) => api.delete(`/training-goals/${id}`),
};

// Events & Competition Prep API (v0.3)
export const eventsApi = {
  create: (data: Partial<CompEvent>) => api.post<CompEvent>('/events/', data),
  list: (status?: string) => api.get<{ events: CompEvent[]; total: number }>('/events/', { params: { status } }),
  get: (id: number) => api.get<CompEvent>(`/events/${id}`),
  update: (id: number, data: Partial<CompEvent>) => api.put<CompEvent>(`/events/${id}`, data),
  delete: (id: number) => api.delete(`/events/${id}`),
  getNext: () => api.get<{ event: CompEvent | null; days_until: number | null; current_weight: number | null }>('/events/next'),
};

export const weightLogsApi = {
  create: (data: { weight: number; logged_date?: string; time_of_day?: string; notes?: string }) =>
    api.post<{ id: number; message: string }>('/events/weight-logs/', data),
  list: (params?: { start_date?: string; end_date?: string }) =>
    api.get<{ logs: WeightLog[]; total: number }>('/events/weight-logs/', { params }),
  getLatest: () => api.get<WeightLog | { weight: null; logged_date: null }>('/events/weight-logs/latest'),
  getAverages: (period?: string) =>
    api.get<{ averages: WeightAverage[]; period: string }>('/events/weight-logs/averages', { params: { period } }),
};

export const milestonesApi = {
  getAchieved: () => api.get<{ milestones: Milestone[]; count: number }>('/milestones/achieved'),
  getProgress: () => api.get<{ progress: MilestoneProgress[] }>('/milestones/progress'),
  getClosest: () => api.get<{ has_milestone: boolean } & MilestoneProgress>('/milestones/closest'),
  getTotals: () => api.get<{ hours: number; sessions: number; rolls: number; partners: number; techniques: number; streak: number }>('/milestones/totals'),
};

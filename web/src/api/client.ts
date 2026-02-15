// Barrel re-export — all existing import sites continue working unchanged
export { api, getErrorMessage } from './_client';
export { sessionsApi, readinessApi, reportsApi, suggestionsApi, techniquesApi } from './training';
export { analyticsApi, grappleApi } from './analytics';
export { socialApi, feedApi, checkinsApi, streaksApi } from './social';
export { profileApi, gradingsApi, friendsApi, usersApi } from './users';
export { adminApi } from './admin';
export { whoopApi, transcribeApi, chatApi } from './integrations';
export { goalsApi, trainingGoalsApi, eventsApi, weightLogsApi, milestonesApi } from './goals';
export { glossaryApi, videosApi, coachPreferencesApi } from './content';
export { groupsApi, gymsApi, photosApi } from './community';
export { dashboardApi, notificationsApi, restApi } from './dashboard';
export { feedbackApi, waitlistApi, gamePlansApi } from './platform';

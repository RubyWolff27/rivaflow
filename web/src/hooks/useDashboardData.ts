import { useEffect, useState, useCallback } from 'react';
import { getLocalDateString } from '../utils/date';
import {
  suggestionsApi,
  readinessApi,
  whoopApi,
  checkinsApi,
  sessionsApi,
  goalsApi,
  gymsApi,
  profileApi,
  streaksApi,
} from '../api/client';
import type { DayCheckins, Session, WeeklyGoalProgress, GymClass, StreakStatus } from '../types';

interface TriggeredRule {
  name: string;
  recommendation: string;
  explanation: string;
  priority: number;
}

interface SuggestionData {
  suggestion: string;
  triggered_rules: TriggeredRule[];
  readiness?: { composite_score?: number };
}

interface WhoopRecovery {
  recovery_score: number | null;
  hrv_ms: number | null;
  resting_hr: number | null;
}

export interface DashboardData {
  loading: boolean;
  streaks: StreakStatus | null;
  readinessScore: number | null;
  whoopRecovery: WhoopRecovery | null;
  hasCheckedIn: boolean;
  suggestion: SuggestionData | null;
  dayCheckins: DayCheckins | null;
  todayPlan: string | undefined;
  todaySessions: Session[];
  weeklyGoals: WeeklyGoalProgress | null;
  todaysClasses: GymClass[];
  gymName: string | null;
  refetchCheckins: () => Promise<void>;
  syncWhoop: () => Promise<void>;
  whoopSyncing: boolean;
}

export function useDashboardData(): DashboardData {
  const [loading, setLoading] = useState(true);
  const [streaks, setStreaks] = useState<StreakStatus | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [whoopRecovery, setWhoopRecovery] = useState<WhoopRecovery | null>(null);
  const [hasCheckedIn, setHasCheckedIn] = useState(false);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [dayCheckins, setDayCheckins] = useState<DayCheckins | null>(null);
  const [todayPlan, setTodayPlan] = useState<string | undefined>(undefined);
  const [todaySessions, setTodaySessions] = useState<Session[]>([]);
  const [weeklyGoals, setWeeklyGoals] = useState<WeeklyGoalProgress | null>(null);
  const [todaysClasses, setTodaysClasses] = useState<GymClass[]>([]);
  const [gymName, setGymName] = useState<string | null>(null);
  const [whoopSyncing, setWhoopSyncing] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      const today = getLocalDateString();
      const results = await Promise.allSettled([
        suggestionsApi.getToday(),         // 0
        readinessApi.getByDate(today),     // 1
        whoopApi.getLatestRecovery(),       // 2
        checkinsApi.getToday(),            // 3
        checkinsApi.getYesterday(),        // 4
        sessionsApi.getByRange(today, today), // 5
        goalsApi.getCurrentWeek(),         // 6
        streaksApi.getStatus(),            // 7
        profileApi.get().then(res => {
          const gymId = res.data.primary_gym_id;
          return gymId
            ? gymsApi.getTodaysClasses(gymId).then(classRes => ({
                classes: classRes.data.classes,
                gymName: classRes.data.gym_name || null,
              }))
            : { classes: [] as GymClass[], gymName: null };
        }),                                // 8
      ]);

      if (controller.signal.aborted) return;

      // Suggestion + embedded readiness
      if (results[0].status === 'fulfilled' && results[0].value.data) {
        setSuggestion(results[0].value.data);
        if (results[0].value.data.readiness?.composite_score != null) {
          setReadinessScore(results[0].value.data.readiness.composite_score);
          setHasCheckedIn(true);
        }
      }

      // Explicit readiness
      if (results[1].status === 'fulfilled' && results[1].value.data) {
        setReadinessScore(results[1].value.data.composite_score);
        setHasCheckedIn(true);
      }

      // WHOOP recovery
      if (results[2].status === 'fulfilled' && results[2].value.data?.recovery_score != null) {
        setWhoopRecovery(results[2].value.data);
      }

      // Today check-ins
      if (results[3].status === 'fulfilled' && results[3].value.data) {
        setDayCheckins(results[3].value.data);
        if (results[3].value.data.checked_in) {
          setHasCheckedIn(true);
        }
      }

      // Yesterday intention → today plan
      if (results[4].status === 'fulfilled' && results[4].value.data) {
        const y = results[4].value.data;
        const intention = y.evening?.tomorrow_intention
          || y.midday?.tomorrow_intention
          || y.morning?.tomorrow_intention;
        if (intention) setTodayPlan(intention);
      }

      // Today sessions
      if (results[5].status === 'fulfilled' && results[5].value.data) {
        const sessions = results[5].value.data;
        if (Array.isArray(sessions)) setTodaySessions(sessions);
      }

      // Weekly goals
      if (results[6].status === 'fulfilled' && results[6].value.data) {
        setWeeklyGoals(results[6].value.data);
      }

      // Streaks
      if (results[7].status === 'fulfilled' && results[7].value.data) {
        setStreaks(results[7].value.data);
      }

      // Gym classes + name
      if (results[8].status === 'fulfilled' && results[8].value) {
        const gymData = results[8].value;
        if ('classes' in gymData) {
          const data = gymData as { classes: GymClass[]; gymName: string | null };
          if (Array.isArray(data.classes)) setTodaysClasses(data.classes);
          if (data.gymName) setGymName(data.gymName);
        }
      }

      setLoading(false);
    };
    load();
    return () => { controller.abort(); };
  }, []);

  const refetchCheckins = useCallback(async () => {
    try {
      const res = await checkinsApi.getToday();
      setDayCheckins(res.data);
      setHasCheckedIn(res.data.checked_in);
    } catch { /* best-effort */ }
  }, []);

  const syncWhoop = useCallback(async () => {
    setWhoopSyncing(true);
    try {
      await whoopApi.sync();
      const res = await whoopApi.getLatestRecovery();
      if (res.data?.recovery_score != null) setWhoopRecovery(res.data);
    } catch { /* best-effort */ }
    setWhoopSyncing(false);
  }, []);

  return {
    loading,
    streaks,
    readinessScore,
    whoopRecovery,
    hasCheckedIn,
    suggestion,
    dayCheckins,
    todayPlan,
    todaySessions,
    weeklyGoals,
    todaysClasses,
    gymName,
    refetchCheckins,
    syncWhoop,
    whoopSyncing,
  };
}

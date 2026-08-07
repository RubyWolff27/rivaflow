import { useEffect, useState, useCallback } from 'react';
import { getLocalDateString } from '../utils/date';
import { logger } from '../utils/logger';
import {
  suggestionsApi,
  readinessApi,
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

export interface DashboardData {
  loading: boolean;
  streaks: StreakStatus | null;
  readinessScore: number | null;
  hasCheckedIn: boolean;
  suggestion: SuggestionData | null;
  dayCheckins: DayCheckins | null;
  todayPlan: string | undefined;
  todaySessions: Session[];
  weeklyGoals: WeeklyGoalProgress | null;
  todaysClasses: GymClass[];
  gymName: string | null;
  refetchCheckins: () => Promise<void>;
}

export function useDashboardData(): DashboardData {
  const [loading, setLoading] = useState(true);
  const [streaks, setStreaks] = useState<StreakStatus | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [hasCheckedIn, setHasCheckedIn] = useState(false);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [dayCheckins, setDayCheckins] = useState<DayCheckins | null>(null);
  const [todayPlan, setTodayPlan] = useState<string | undefined>(undefined);
  const [todaySessions, setTodaySessions] = useState<Session[]>([]);
  const [weeklyGoals, setWeeklyGoals] = useState<WeeklyGoalProgress | null>(null);
  const [todaysClasses, setTodaysClasses] = useState<GymClass[]>([]);
  const [gymName, setGymName] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      const today = getLocalDateString();
      const results = await Promise.allSettled([
        suggestionsApi.getToday(),         // 0
        readinessApi.getByDate(today),     // 1
        checkinsApi.getToday(),            // 2
        checkinsApi.getYesterday(),        // 3
        sessionsApi.getByRange(today, today), // 4
        goalsApi.getCurrentWeek(),         // 5
        streaksApi.getStatus(),            // 6
        profileApi.get().then(res => {
          const gymId = res.data.primary_gym_id;
          return gymId
            ? gymsApi.getTodaysClasses(gymId).then(classRes => ({
                classes: classRes.data.classes,
                gymName: classRes.data.gym_name || null,
              }))
            : { classes: [] as GymClass[], gymName: null };
        }),                                // 7
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

      // Today check-ins
      if (results[2].status === 'fulfilled' && results[2].value.data) {
        setDayCheckins(results[2].value.data);
        if (results[2].value.data.checked_in) {
          setHasCheckedIn(true);
        }
      }

      // Yesterday intention → today plan
      if (results[3].status === 'fulfilled' && results[3].value.data) {
        const y = results[3].value.data;
        const intention = y.evening?.tomorrow_intention
          || y.midday?.tomorrow_intention
          || y.morning?.tomorrow_intention;
        if (intention) setTodayPlan(intention);
      }

      // Today sessions
      if (results[4].status === 'fulfilled' && results[4].value.data) {
        const sessions = results[4].value.data;
        if (Array.isArray(sessions)) setTodaySessions(sessions);
      }

      // Weekly goals
      if (results[5].status === 'fulfilled' && results[5].value.data) {
        setWeeklyGoals(results[5].value.data);
      }

      // Streaks
      if (results[6].status === 'fulfilled' && results[6].value.data) {
        setStreaks(results[6].value.data);
      }

      // Gym classes + name
      if (results[7].status === 'fulfilled' && results[7].value) {
        const gymData = results[7].value;
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
    } catch (err) { logger.debug('Refetch checkins best-effort failed', err); }
  }, []);

  return {
    loading,
    streaks,
    readinessScore,
    hasCheckedIn,
    suggestion,
    dayCheckins,
    todayPlan,
    todaySessions,
    weeklyGoals,
    todaysClasses,
    gymName,
    refetchCheckins,
  };
}

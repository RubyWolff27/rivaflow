import { useEffect, useState } from 'react';
import { sessionsApi, dashboardApi, profileApi } from '../api/client';
import type { Session } from '../types';

export interface WeekDay {
  label: string;
  date: string;
  sessions: { class_type: string; duration_mins: number }[];
}

export interface ClassTypeVolume {
  type: string;
  count: number;
  hours: number;
}

interface ProfileSummary {
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  current_grade: string | null;
}

interface LastSessionSummary {
  class_type: string;
  gym_name: string;
  duration_mins: number;
  session_date: string;
  rolls: number;
}

export interface TrainingSnapshotData {
  loading: boolean;
  weekDays: WeekDay[];
  volumes: ClassTypeVolume[];
  totalSessions: number;
  totalHours: number;
  totalRolls: number;
  lastSession: LastSessionSummary | null;
  profile: ProfileSummary | null;
}

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(d);
  monday.setDate(diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

const DAY_LABELS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

export function useTrainingSnapshot(): TrainingSnapshotData {
  const [loading, setLoading] = useState(true);
  const [weekDays, setWeekDays] = useState<WeekDay[]>([]);
  const [volumes, setVolumes] = useState<ClassTypeVolume[]>([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [totalHours, setTotalHours] = useState(0);
  const [totalRolls, setTotalRolls] = useState(0);
  const [lastSession, setLastSession] = useState<LastSessionSummary | null>(null);
  const [profile, setProfile] = useState<ProfileSummary | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const now = new Date();
      const monday = getMonday(now);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      const results = await Promise.allSettled([
        sessionsApi.getByRange(formatDate(monday), formatDate(sunday)),
        dashboardApi.getWeekSummary(0),
        profileApi.get(),
        sessionsApi.list(1),
      ]);

      if (cancelled) return;

      // Build week days grid + compute per-type hours
      const days: WeekDay[] = DAY_LABELS.map((label, i) => {
        const date = new Date(monday);
        date.setDate(monday.getDate() + i);
        return { label, date: formatDate(date), sessions: [] };
      });

      const typeHours: Record<string, number> = {};
      let weekRolls = 0;

      if (results[0].status === 'fulfilled') {
        const sessions: Session[] = Array.isArray(results[0].value.data)
          ? results[0].value.data
          : [];
        for (const s of sessions) {
          const day = days.find(d => d.date === s.session_date);
          if (day) {
            day.sessions.push({ class_type: s.class_type, duration_mins: s.duration_mins });
          }
          typeHours[s.class_type] = (typeHours[s.class_type] || 0) + (s.duration_mins || 0) / 60;
          weekRolls += s.rolls || 0;
        }
      }
      setWeekDays(days);
      setTotalRolls(weekRolls);

      // Build volume breakdown from week stats
      if (results[1].status === 'fulfilled') {
        const stats = results[1].value.data?.stats;
        if (stats?.class_types) {
          const vols: ClassTypeVolume[] = Object.entries(stats.class_types as Record<string, number>)
            .map(([type, count]) => ({
              type,
              count,
              hours: typeHours[type] || 0,
            }))
            .sort((a, b) => b.count - a.count);
          setVolumes(vols);
          setTotalSessions(stats.total_sessions || 0);
          setTotalHours(stats.total_hours || 0);
        }
      }

      // Profile
      if (results[2].status === 'fulfilled') {
        const p = results[2].value.data;
        setProfile({
          first_name: p.first_name || '',
          last_name: p.last_name || '',
          avatar_url: p.avatar_url || null,
          current_grade: p.current_grade || null,
        });
      }

      // Last session
      if (results[3].status === 'fulfilled') {
        const list = results[3].value.data;
        const sessions: Session[] = Array.isArray(list) ? list : [];
        if (sessions.length > 0) {
          const s = sessions[0];
          setLastSession({
            class_type: s.class_type,
            gym_name: s.gym_name,
            duration_mins: s.duration_mins,
            session_date: s.session_date,
            rolls: s.rolls || 0,
          });
        }
      }

      setLoading(false);
    };

    load();
    return () => { cancelled = true; };
  }, []);

  return { loading, weekDays, volumes, totalSessions, totalHours, totalRolls, lastSession, profile };
}

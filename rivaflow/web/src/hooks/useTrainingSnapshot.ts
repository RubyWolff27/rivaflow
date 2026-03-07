import { useEffect, useState } from 'react';
import { sessionsApi, dashboardApi, profileApi } from '../api/client';
import type { Session } from '../types';

interface WeekDay {
  label: string;
  date: string;
  sessions: { class_type: string }[];
}

interface ClassTypeVolume {
  type: string;
  count: number;
}

interface ProfileSummary {
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  current_grade: string | null;
}

export interface TrainingSnapshotData {
  loading: boolean;
  weekDays: WeekDay[];
  volumes: ClassTypeVolume[];
  totalSessions: number;
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
      ]);

      if (cancelled) return;

      // Build week days grid
      const days: WeekDay[] = DAY_LABELS.map((label, i) => {
        const date = new Date(monday);
        date.setDate(monday.getDate() + i);
        return { label, date: formatDate(date), sessions: [] };
      });

      if (results[0].status === 'fulfilled') {
        const sessions: Session[] = Array.isArray(results[0].value.data)
          ? results[0].value.data
          : [];
        for (const s of sessions) {
          const day = days.find(d => d.date === s.session_date);
          if (day) {
            day.sessions.push({ class_type: s.class_type });
          }
        }
      }
      setWeekDays(days);

      // Build volume breakdown from week stats
      if (results[1].status === 'fulfilled') {
        const stats = results[1].value.data?.stats;
        if (stats?.class_types) {
          const vols: ClassTypeVolume[] = Object.entries(stats.class_types as Record<string, number>)
            .map(([type, count]) => ({ type, count }))
            .sort((a, b) => b.count - a.count);
          setVolumes(vols);
          setTotalSessions(stats.total_sessions || 0);
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

      setLoading(false);
    };

    load();
    return () => { cancelled = true; };
  }, []);

  return { loading, weekDays, volumes, totalSessions, profile };
}

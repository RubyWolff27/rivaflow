import { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';
import { Card } from '../ui';
import { profileApi, gymsApi } from '../../api/client';
import type { GymClass } from '../../api/client';

function classBadge(classType: string | null) {
  switch (classType) {
    case 'gi':
      return { bg: '#0D9488', label: 'Gi' };
    case 'no-gi':
      return { bg: '#F97316', label: 'No-Gi' };
    case 'open-mat':
      return { bg: '#3B82F6', label: 'Open Mat' };
    default:
      return { bg: 'var(--muted)', label: classType || '' };
  }
}

function isPast(startTime: string): boolean {
  const now = new Date();
  const [h, m] = startTime.split(':').map(Number);
  return now.getHours() > h || (now.getHours() === h && now.getMinutes() >= m);
}

export default function TodayClassesWidget() {
  const [classes, setClasses] = useState<GymClass[]>([]);
  const [gymName, setGymName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data: profile } = await profileApi.get();
        const gymId = profile.primary_gym_id;
        if (!gymId) {
          setLoading(false);
          return;
        }
        const { data } = await gymsApi.getTodaysClasses(gymId);
        setClasses(data.classes || []);
        setGymName(data.gym_name || '');
      } catch {
        /* best-effort */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading || classes.length === 0) return null;

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-4 h-4" style={{ color: 'var(--accent)' }} />
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
          Classes at {gymName} today
        </h3>
      </div>
      <div className="space-y-2">
        {classes.map((cls) => {
          const past = isPast(cls.start_time);
          const badge = classBadge(cls.class_type);
          return (
            <div
              key={cls.id}
              className="flex items-center gap-3 py-1.5"
              style={{ opacity: past ? 0.45 : 1 }}
            >
              <span
                className="text-sm font-mono font-medium w-[100px] shrink-0"
                style={{ color: past ? 'var(--muted)' : 'var(--text)' }}
              >
                {cls.start_time}–{cls.end_time}
              </span>
              <span
                className="text-sm flex-1 truncate"
                style={{ color: past ? 'var(--muted)' : 'var(--text)' }}
              >
                {cls.class_name}
              </span>
              {cls.class_type && (
                <span
                  className="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0"
                  style={{ backgroundColor: badge.bg, color: '#fff' }}
                >
                  {badge.label}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

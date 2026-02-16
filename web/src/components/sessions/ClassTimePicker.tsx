import { useState, useEffect } from 'react';
import { gymsApi } from '../../api/client';
import type { GymClass } from '../../types';

const TIME_QUICK_SELECT = [
  { label: '6:30am', value: '06:30' },
  { label: '12pm', value: '12:00' },
  { label: '5:30pm', value: '17:30' },
  { label: '7pm', value: '19:00' },
] as const;

const CLASS_TYPE_DOT: Record<string, string> = {
  gi: '#3B82F6',
  'no-gi': '#F59E0B',
  'open-mat': '#10B981',
};

function formatTime12(time24: string): string {
  const [h, m] = time24.split(':').map(Number);
  const suffix = h >= 12 ? 'pm' : 'am';
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return m === 0 ? `${h12}${suffix}` : `${h12}:${m.toString().padStart(2, '0')}${suffix}`;
}

function durationFromTimes(start: string, end: string): number {
  const [sh, sm] = start.split(':').map(Number);
  const [eh, em] = end.split(':').map(Number);
  return (eh * 60 + em) - (sh * 60 + sm);
}

interface ClassTimePickerProps {
  gymId: number | null;
  classTime: string;
  onSelect: (classTime: string, classType?: string, durationMins?: number) => void;
}

export default function ClassTimePicker({ gymId, classTime, onSelect }: ClassTimePickerProps) {
  const [gymClasses, setGymClasses] = useState<GymClass[]>([]);

  useEffect(() => {
    if (!gymId) { setGymClasses([]); return; }
    let cancelled = false;
    gymsApi.getTodaysClasses(gymId).then(res => {
      if (!cancelled) setGymClasses((res.data.classes || []).filter(c => c.is_active));
    }).catch(() => { if (!cancelled) setGymClasses([]); });
    return () => { cancelled = true; };
  }, [gymId]);

  const chips = gymClasses.length > 0 ? gymClasses : null;

  return (
    <div>
      <label className="label">Class Time (optional)</label>
      <div className="flex flex-wrap gap-2 mb-2" role="group" aria-label="Class times">
        {chips ? chips.map(gc => {
          const active = classTime === gc.start_time;
          return (
            <button key={gc.id} type="button"
              onClick={() => {
                const dur = durationFromTimes(gc.start_time, gc.end_time);
                onSelect(gc.start_time, gc.class_type || undefined, dur > 0 ? dur : undefined);
              }}
              className="px-3 min-h-[44px] py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-1.5"
              style={{
                backgroundColor: active ? 'var(--accent)' : 'var(--surfaceElev)',
                color: active ? '#FFFFFF' : 'var(--text)',
                border: active ? 'none' : '1px solid var(--border)',
              }}
              aria-pressed={active}
            >
              {gc.class_type && (
                <span className="w-2 h-2 rounded-full inline-block flex-shrink-0"
                  style={{ backgroundColor: active ? '#FFFFFF' : (CLASS_TYPE_DOT[gc.class_type] || 'var(--muted)') }} />
              )}
              {formatTime12(gc.start_time)}
              <span className="text-xs opacity-75">{gc.class_name}</span>
            </button>
          );
        }) : TIME_QUICK_SELECT.map(time => (
          <button key={time.value} type="button"
            onClick={() => onSelect(time.value)}
            className="flex-1 min-h-[44px] py-2 rounded-lg font-medium text-sm transition-all"
            style={{
              backgroundColor: classTime === time.value ? 'var(--accent)' : 'var(--surfaceElev)',
              color: classTime === time.value ? '#FFFFFF' : 'var(--text)',
              border: classTime === time.value ? 'none' : '1px solid var(--border)',
            }}
            aria-pressed={classTime === time.value}
          >
            {time.label}
          </button>
        ))}
      </div>
      <input type="text" className="input text-sm" value={classTime}
        onChange={(e) => onSelect(e.target.value)}
        placeholder="Or type custom time (e.g., 18:30)" />
    </div>
  );
}

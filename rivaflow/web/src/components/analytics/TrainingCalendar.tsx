import { useMemo } from 'react';
import { Card } from '../ui';
import { formatCount } from '../../utils/text';

interface CalendarDay {
  date: string;
  count: number;
  intensity: number;
}

interface TrainingCalendarProps {
  calendar: CalendarDay[];
  totalActiveDays: number;
  activityRate: number;
}

export default function TrainingCalendar({ calendar, totalActiveDays, activityRate }: TrainingCalendarProps) {
  const { weeks, months } = useMemo(() => {
    if (!calendar || calendar.length === 0) return { weeks: [], months: [] };

    // Group by week (columns)
    const weekGroups: CalendarDay[][] = [];
    let currentWeek: CalendarDay[] = [];

    // Pad first week to align to start on Sunday
    const firstDate = new Date(calendar[0].date);
    const dayOfWeek = firstDate.getDay();
    for (let i = 0; i < dayOfWeek; i++) {
      currentWeek.push({ date: '', count: 0, intensity: 0 });
    }

    for (const day of calendar) {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        weekGroups.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      // Pad remaining
      while (currentWeek.length < 7) {
        currentWeek.push({ date: '', count: 0, intensity: 0 });
      }
      weekGroups.push(currentWeek);
    }

    // Extract month labels
    const monthLabels: { label: string; col: number }[] = [];
    let lastMonth = '';
    weekGroups.forEach((week, weekIdx) => {
      for (const day of week) {
        if (!day.date) continue;
        const d = new Date(day.date);
        const monthKey = d.toLocaleDateString('en-US', { month: 'short' });
        if (monthKey !== lastMonth) {
          monthLabels.push({ label: monthKey, col: weekIdx });
          lastMonth = monthKey;
        }
        break;
      }
    });

    return { weeks: weekGroups, months: monthLabels };
  }, [calendar]);

  if (!calendar || calendar.length === 0) return null;

  const getColor = (count: number, intensity: number) => {
    if (count === 0) return 'var(--border)';
    // Intensity-based green scale (mapped 1-5 to opacity levels)
    const level = Math.min(Math.ceil(intensity), 5);
    const opacities: Record<number, number> = { 1: 0.25, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0 };
    const opacity = opacities[level] || 0.25;
    return `rgba(var(--accent-rgb), ${opacity})`;
  };

  const dayLabels = ['', 'Mon', '', 'Wed', '', 'Fri', ''];

  return (
    <Card>
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Training Calendar</h3>
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {totalActiveDays} active days ({activityRate}% activity rate)
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-flex flex-col gap-0.5" style={{ minWidth: 'max-content' }}>
          {/* Month labels */}
          <div className="flex gap-0.5 ml-8 mb-1">
            {months.map((m, i) => (
              <span
                key={i}
                className="text-[10px]"
                style={{
                  color: 'var(--muted)',
                  position: 'relative',
                  left: `${m.col * 14}px`,
                }}
              >
                {m.label}
              </span>
            ))}
          </div>

          {/* Grid */}
          <div className="flex gap-0">
            {/* Day labels */}
            <div className="flex flex-col gap-0.5 mr-1" style={{ width: '28px' }}>
              {dayLabels.map((label, i) => (
                <div key={i} className="flex items-center justify-end" style={{ height: '12px' }}>
                  <span className="text-[10px]" style={{ color: 'var(--muted)' }}>{label}</span>
                </div>
              ))}
            </div>

            {/* Weeks */}
            <div className="flex gap-0.5">
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col gap-0.5">
                  {week.map((day, dayIdx) => (
                    <div
                      key={dayIdx}
                      className="rounded-sm"
                      style={{
                        width: '12px',
                        height: '12px',
                        backgroundColor: day.date ? getColor(day.count, day.intensity) : 'transparent',
                      }}
                      title={day.date ? `${day.date}: ${formatCount(day.count, 'session')}, intensity ${day.intensity}` : ''}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-1 mt-2 ml-8">
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>Less</span>
            {[0, 0.25, 0.5, 0.75, 1.0].map((opacity, i) => (
              <div
                key={i}
                className="rounded-sm"
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: i === 0 ? 'var(--border)' : `rgba(var(--accent-rgb), ${opacity})`,
                }}
              />
            ))}
            <span className="text-[10px]" style={{ color: 'var(--muted)' }}>More</span>
          </div>
        </div>
      </div>
    </Card>
  );
}

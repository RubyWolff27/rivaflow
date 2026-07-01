import { memo } from 'react';

// Garmin 5 HR zones (seconds) → a labelled stacked bar with a minutes legend.
const ZONES = [
  { key: 0, label: 'Z1', color: '#93C5FD' },
  { key: 1, label: 'Z2', color: '#34D399' },
  { key: 2, label: 'Z3', color: '#FBBF24' },
  { key: 3, label: 'Z4', color: '#F97316' },
  { key: 4, label: 'Z5', color: '#EF4444' },
];

interface GarminZoneBarProps {
  /** seconds in each HR zone, [z1..z5] */
  seconds: (number | null | undefined)[];
}

const GarminZoneBar = memo(function GarminZoneBar({ seconds }: GarminZoneBarProps) {
  const secs = ZONES.map((z) => Number(seconds[z.key] ?? 0));
  const total = secs.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;

  return (
    <div>
      <div className="flex rounded-full overflow-hidden h-3">
        {ZONES.map((z) => {
          const pct = (secs[z.key] / total) * 100;
          if (pct < 0.5) return null;
          return <div key={z.key} style={{ width: `${pct}%`, backgroundColor: z.color }} title={`${z.label}: ${Math.round(secs[z.key] / 60)}m`} />;
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
        {ZONES.map((z) => {
          const min = Math.round(secs[z.key] / 60);
          if (min <= 0) return null;
          return (
            <span key={z.key} className="inline-flex items-center gap-1 text-xs" style={{ color: 'var(--muted)' }}>
              <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: z.color }} />
              {z.label} {min}m
            </span>
          );
        })}
      </div>
    </div>
  );
});

export default GarminZoneBar;

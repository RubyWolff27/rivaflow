import { memo } from 'react';

const ZONE_CONFIG = [
  { key: 'zone_one_milli', color: '#93C5FD' },
  { key: 'zone_two_milli', color: '#34D399' },
  { key: 'zone_three_milli', color: '#FBBF24' },
  { key: 'zone_four_milli', color: '#F97316' },
  { key: 'zone_five_milli', color: '#EF4444' },
];

interface MiniZoneBarProps {
  zones: Record<string, number>;
  height?: string;
}

const MiniZoneBar = memo(function MiniZoneBar({ zones, height = 'h-2' }: MiniZoneBarProps) {
  const totalMs = ZONE_CONFIG.reduce((sum, z) => sum + (zones[z.key] || 0), 0);
  if (totalMs <= 0) return null;

  return (
    <div className={`flex rounded-full overflow-hidden ${height}`}>
      {ZONE_CONFIG.map(z => {
        const ms = zones[z.key] || 0;
        const pct = (ms / totalMs) * 100;
        if (pct < 1) return null;
        return (
          <div
            key={z.key}
            style={{ width: `${pct}%`, backgroundColor: z.color }}
          />
        );
      })}
    </div>
  );
});

export default MiniZoneBar;

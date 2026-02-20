import { useState, useEffect } from 'react';
import { analyticsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { CardSkeleton } from '../ui';

interface ProgressionPoint {
  roll_number: number;
  date: string;
  rolling_sub_rate: number;
  window_size: number;
}

interface PartnerProgressionChartProps {
  partnerId: number;
}

interface PartnerProgressionData {
  progression?: ProgressionPoint[];
  partner?: { name?: string; belt_rank?: string; [key: string]: unknown };
  trend?: string;
  insight?: string;
  [key: string]: unknown;
}

export default function PartnerProgressionChart({ partnerId }: PartnerProgressionChartProps) {
  const [data, setData] = useState<PartnerProgressionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    analyticsApi.partnerProgression(partnerId)
      .then(res => { if (!cancelled) setData(res.data); })
      .catch((err) => { logger.debug('Partner progression not available', err); if (!cancelled) setData(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [partnerId]);

  if (loading) return <CardSkeleton lines={3} />;
  if (!data || !data.progression || data.progression.length < 3) {
    return (
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        {data?.insight || 'Not enough data for progression chart.'}
      </p>
    );
  }

  const progression: ProgressionPoint[] = data.progression;
  const width = 400;
  const height = 150;
  const padding = { top: 15, right: 15, bottom: 25, left: 35 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxRate = Math.max(2, ...progression.map(p => p.rolling_sub_rate));
  const xScale = (i: number) => padding.left + (i / (progression.length - 1)) * chartW;
  const yScale = (v: number) => padding.top + chartH - (v / maxRate) * chartH;

  const linePath = progression
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${xScale(i)},${yScale(p.rolling_sub_rate)}`)
    .join(' ');

  const trendColors: Record<string, string> = {
    improving: '#22C55E',
    declining: '#EF4444',
    stable: '#EAB308',
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
          vs {data.partner?.name ?? 'Unknown'}
        </span>
        {data.partner?.belt_rank && (
          <span className="text-xs" style={{ color: 'var(--muted)' }}>({data.partner.belt_rank})</span>
        )}
        <span
          className="text-xs px-2 py-0.5 rounded-full capitalize"
          style={{ backgroundColor: (data.trend && trendColors[data.trend]) || 'var(--muted)', color: '#FFFFFF' }}
        >
          {data.trend}
        </span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '160px' }}>
        {/* Reference line at 1.0 (even) */}
        <line x1={padding.left} y1={yScale(1)} x2={padding.left + chartW} y2={yScale(1)} stroke="var(--border)" strokeWidth={0.5} strokeDasharray="3,3" />
        <text x={padding.left - 5} y={yScale(1) + 4} textAnchor="end" fontSize={9} fill="var(--muted)">1.0</text>

        {/* Line */}
        <path d={linePath} fill="none" stroke={(data.trend && trendColors[data.trend]) || 'var(--accent)'} strokeWidth={2} strokeLinejoin="round" />

        {/* Points */}
        {progression.map((p, i) => (
          <circle key={i} cx={xScale(i)} cy={yScale(p.rolling_sub_rate)} r={3} fill={(data.trend && trendColors[data.trend]) || 'var(--accent)'}>
            <title>{`Roll ${p.roll_number}: ${p.rolling_sub_rate} sub rate`}</title>
          </circle>
        ))}

        {/* X labels */}
        <text x={xScale(0)} y={height - 5} textAnchor="start" fontSize={9} fill="var(--muted)">Roll 1</text>
        <text x={xScale(progression.length - 1)} y={height - 5} textAnchor="end" fontSize={9} fill="var(--muted)">Roll {progression.length}</text>
      </svg>

      <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>{data.insight}</p>
    </div>
  );
}

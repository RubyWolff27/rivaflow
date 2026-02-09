interface WeeklyRHR {
  week: string;
  avg_rhr: number;
  data_points: number;
}

interface CardiovascularDriftChartProps {
  weeklyRhr: WeeklyRHR[];
  slope: number;
  trend: string;
  currentRhr: number | null;
  baselineRhr: number | null;
}

export default function CardiovascularDriftChart({ weeklyRhr, slope, trend, currentRhr, baselineRhr }: CardiovascularDriftChartProps) {
  if (weeklyRhr.length < 2) return null;

  const width = 600;
  const height = 180;
  const pad = { top: 15, right: 20, bottom: 30, left: 45 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const values = weeklyRhr.map(w => w.avg_rhr);
  const minV = Math.floor(Math.min(...values) * 0.95);
  const maxV = Math.ceil(Math.max(...values) * 1.05);
  const range = maxV - minV || 1;

  const xScale = (i: number) => pad.left + (i / Math.max(weeklyRhr.length - 1, 1)) * plotW;
  const yScale = (v: number) => pad.top + plotH - ((v - minV) / range) * plotH;

  // Build line path
  const linePath = weeklyRhr.map((w, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(w.avg_rhr)}`).join(' ');

  // Trend line
  const trendY0 = yScale(values[0]);
  const trendY1 = yScale(values[0] + slope * (weeklyRhr.length - 1));

  const trendColor = trend === 'improving' ? '#10B981' : trend === 'rising' ? '#EF4444' : '#6B7280';
  const trendLabel = trend === 'improving' ? 'Improving' : trend === 'rising' ? 'Fatigued' : 'Stable';

  const labelIndices = weeklyRhr.length <= 4
    ? weeklyRhr.map((_, i) => i)
    : [0, Math.floor(weeklyRhr.length / 2), weeklyRhr.length - 1];

  const gridValues = (() => {
    const step = Math.max(Math.round(range / 4), 1);
    const vals: number[] = [];
    for (let v = minV; v <= maxV; v += step) vals.push(v);
    return vals;
  })();

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 180 }}>
        {/* Grid */}
        {gridValues.map(v => (
          <g key={v}>
            <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
            <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}</text>
          </g>
        ))}

        {/* Trend line */}
        <line
          x1={xScale(0)}
          y1={trendY0}
          x2={xScale(weeklyRhr.length - 1)}
          y2={trendY1}
          stroke={trendColor}
          strokeWidth={2}
          strokeDasharray="6 3"
          opacity={0.6}
        />

        {/* Main line */}
        <path d={linePath} fill="none" stroke="#EF4444" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

        {/* Points */}
        {weeklyRhr.map((w, i) => (
          <circle key={i} cx={xScale(i)} cy={yScale(w.avg_rhr)} r={3} fill="#EF4444">
            <title>{w.week}: {w.avg_rhr} bpm ({w.data_points} days)</title>
          </circle>
        ))}

        {/* X labels */}
        {labelIndices.map(i => (
          <text key={i} x={xScale(i)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
            {weeklyRhr[i].week.replace(/^\d{4}-/, '')}
          </text>
        ))}
      </svg>

      <div className="flex items-center gap-3 mt-2 flex-wrap">
        <span className="text-xs px-2 py-1 rounded font-medium" style={{ backgroundColor: trendColor, color: '#fff' }}>
          {trendLabel}
        </span>
        <span className="text-xs" style={{ color: 'var(--muted)' }}>
          Slope: {slope > 0 ? '+' : ''}{slope.toFixed(2)} bpm/week
        </span>
        {currentRhr != null && (
          <span className="text-xs" style={{ color: 'var(--text)' }}>
            Current: {currentRhr} bpm
          </span>
        )}
        {baselineRhr != null && (
          <span className="text-xs" style={{ color: 'var(--muted)' }}>
            Baseline: {baselineRhr} bpm
          </span>
        )}
      </div>
    </div>
  );
}

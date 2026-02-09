interface ScatterPoint {
  date: string;
  recovery_score: number;
  sub_rate: number;
}

interface Zone {
  avg_sub_rate: number;
  sessions: number;
}

interface RecoveryPerformanceChartProps {
  scatter: ScatterPoint[];
  zones: Record<string, Zone>;
  rValue: number;
}

export default function RecoveryPerformanceChart({ scatter, zones, rValue }: RecoveryPerformanceChartProps) {
  if (scatter.length === 0) return null;

  const width = 600;
  const height = 220;
  const pad = { top: 20, right: 20, bottom: 35, left: 50 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const maxSR = Math.max(...scatter.map(p => p.sub_rate), 1);
  const xScale = (v: number) => pad.left + (v / 100) * plotW;
  const yScale = (v: number) => pad.top + plotH - (v / (maxSR * 1.1)) * plotH;

  // Zone bands
  const zoneBands = [
    { x1: 0, x2: 33, color: 'rgba(239, 68, 68, 0.06)' },
    { x1: 34, x2: 66, color: 'rgba(245, 158, 11, 0.06)' },
    { x1: 67, x2: 100, color: 'rgba(16, 185, 129, 0.06)' },
  ];

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 220 }}>
        {/* Zone bands */}
        {zoneBands.map(band => (
          <rect
            key={band.x1}
            x={xScale(band.x1)}
            y={pad.top}
            width={xScale(band.x2) - xScale(band.x1)}
            height={plotH}
            fill={band.color}
          />
        ))}

        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(v => (
          <g key={v}>
            <line x1={xScale(v)} y1={pad.top} x2={xScale(v)} y2={pad.top + plotH} stroke="var(--border)" strokeWidth={1} />
            <text x={xScale(v)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">{v}%</text>
          </g>
        ))}

        {/* Y grid */}
        {[0, 0.5, 1, 1.5, 2].filter(v => v <= maxSR * 1.1).map(v => (
          <g key={v}>
            <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
            <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}</text>
          </g>
        ))}

        {/* Scatter points */}
        {scatter.map((p, i) => {
          const color = p.recovery_score >= 67 ? '#10B981' : p.recovery_score >= 34 ? '#F59E0B' : '#EF4444';
          return (
            <circle
              key={i}
              cx={xScale(p.recovery_score)}
              cy={yScale(p.sub_rate)}
              r={4}
              fill={color}
              opacity={0.7}
            >
              <title>{p.date}: Recovery {p.recovery_score}%, Sub Rate {p.sub_rate}</title>
            </circle>
          );
        })}

        {/* Axis labels */}
        <text x={width / 2} y={height - 2} textAnchor="middle" fontSize={10} fill="var(--muted)">Recovery Score %</text>
        <text x={12} y={height / 2} textAnchor="middle" fontSize={10} fill="var(--muted)" transform={`rotate(-90, 12, ${height / 2})`}>Sub Rate</text>
      </svg>

      {/* Correlation badge */}
      <div className="flex items-center gap-3 mt-2">
        <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}>
          r = {rValue}
        </span>
        {Object.entries(zones).map(([zone, data]) => (
          <span key={zone} className="text-xs" style={{ color: 'var(--muted)' }}>
            {zone}: {data.avg_sub_rate} avg ({data.sessions} sessions)
          </span>
        ))}
      </div>
    </div>
  );
}

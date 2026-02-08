interface ScatterPoint {
  date: string;
  readiness: number;
  sub_rate: number;
  intensity: number;
}

interface CorrelationScatterProps {
  scatter: ScatterPoint[];
  rValue: number;
  optimalZone: string;
  insight: string;
}

export default function CorrelationScatter({ scatter, rValue, optimalZone, insight }: CorrelationScatterProps) {
  if (!scatter || scatter.length < 3) {
    return (
      <p className="text-sm py-4" style={{ color: 'var(--muted)' }}>
        Need 3+ sessions with readiness data to show correlation.
      </p>
    );
  }

  const width = 400;
  const height = 300;
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxReadiness = 20;
  const maxSubRate = Math.max(3, ...scatter.map(s => s.sub_rate));

  const xScale = (v: number) => padding.left + (v / maxReadiness) * chartW;
  const yScale = (v: number) => padding.top + chartH - (v / maxSubRate) * chartH;

  // Optimal zone highlight
  let zoneX1 = 0;
  let zoneX2 = 0;
  if (optimalZone) {
    const parts = optimalZone.split('-').map(Number);
    if (parts.length === 2) {
      zoneX1 = xScale(parts[0]);
      zoneX2 = xScale(parts[1]);
    }
  }

  const rColor = Math.abs(rValue) >= 0.4 ? 'var(--accent)' : Math.abs(rValue) >= 0.2 ? '#EAB308' : 'var(--muted)';

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>r = {rValue}</span>
        <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: rColor, color: '#FFFFFF' }}>
          {Math.abs(rValue) >= 0.4 ? 'Strong' : Math.abs(rValue) >= 0.2 ? 'Moderate' : 'Weak'}
        </span>
        {optimalZone && (
          <span className="text-xs" style={{ color: 'var(--muted)' }}>Optimal: {optimalZone}</span>
        )}
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '320px' }}>
        {/* Optimal zone band */}
        {zoneX1 > 0 && zoneX2 > 0 && (
          <rect x={zoneX1} y={padding.top} width={zoneX2 - zoneX1} height={chartH} fill="rgba(var(--accent-rgb), 0.08)" />
        )}

        {/* Grid */}
        {[0, 5, 10, 15, 20].map(v => (
          <g key={`x-${v}`}>
            <line x1={xScale(v)} y1={padding.top} x2={xScale(v)} y2={padding.top + chartH} stroke="var(--border)" strokeWidth={0.5} />
            <text x={xScale(v)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">{v}</text>
          </g>
        ))}
        {[0, 1, 2, 3].filter(v => v <= maxSubRate).map(v => (
          <g key={`y-${v}`}>
            <line x1={padding.left} y1={yScale(v)} x2={padding.left + chartW} y2={yScale(v)} stroke="var(--border)" strokeWidth={0.5} />
            <text x={padding.left - 5} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}</text>
          </g>
        ))}

        {/* Axis labels */}
        <text x={width / 2} y={height - 20} textAnchor="middle" fontSize={11} fill="var(--muted)">Readiness Score</text>
        <text x={12} y={height / 2} textAnchor="middle" fontSize={11} fill="var(--muted)" transform={`rotate(-90, 12, ${height / 2})`}>Sub Rate</text>

        {/* Data points */}
        {scatter.map((point, i) => (
          <circle
            key={i}
            cx={xScale(point.readiness)}
            cy={yScale(point.sub_rate)}
            r={4}
            fill="var(--accent)"
            opacity={0.6}
          >
            <title>{`${point.date}: Readiness ${point.readiness}, Sub Rate ${point.sub_rate}`}</title>
          </circle>
        ))}
      </svg>

      <p className="text-sm mt-2" style={{ color: 'var(--muted)' }}>{insight}</p>
    </div>
  );
}

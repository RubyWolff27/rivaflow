interface Factor {
  score: number;
  max: number;
}

interface RiskGaugeProps {
  riskScore: number;
  level: string;
  factors: {
    acwr_spike: Factor;
    readiness_decline: Factor;
    hotspot_mentions: Factor;
    intensity_creep: Factor;
  };
  recommendations: string[];
}

export default function RiskGauge({ riskScore, level, factors, recommendations }: RiskGaugeProps) {
  const levelColors: Record<string, string> = {
    green: '#22C55E',
    yellow: '#EAB308',
    red: '#EF4444',
  };

  const color = levelColors[level] || 'var(--muted)';

  // Semi-circular gauge
  const radius = 80;
  const cx = 100;
  const cy = 95;
  const startAngle = Math.PI;
  const angle = startAngle - (riskScore / 100) * Math.PI;

  const arcX = cx + radius * Math.cos(angle);
  const arcY = cy - radius * Math.sin(angle);

  // Arc path from left (score 0) to current score
  const largeArc = riskScore > 50 ? 1 : 0;
  const arcPath = `M ${cx - radius} ${cy} A ${radius} ${radius} 0 ${largeArc} 1 ${arcX} ${arcY}`;
  const fullArcPath = `M ${cx - radius} ${cy} A ${radius} ${radius} 0 1 1 ${cx + radius} ${cy}`;

  const factorList = [
    { key: 'acwr_spike', label: 'ACWR Spike', ...factors.acwr_spike },
    { key: 'readiness_decline', label: 'Readiness Decline', ...factors.readiness_decline },
    { key: 'hotspot_mentions', label: 'Injury Hotspots', ...factors.hotspot_mentions },
    { key: 'intensity_creep', label: 'Intensity Creep', ...factors.intensity_creep },
  ];

  return (
    <div>
      {/* Gauge */}
      <div className="flex justify-center mb-4">
        <svg viewBox="0 0 200 110" className="w-48">
          {/* Background arc */}
          <path d={fullArcPath} fill="none" stroke="var(--border)" strokeWidth={12} strokeLinecap="round" />
          {/* Score arc */}
          {riskScore > 0 && (
            <path d={arcPath} fill="none" stroke={color} strokeWidth={12} strokeLinecap="round" />
          )}
          {/* Score text */}
          <text x={cx} y={cy - 10} textAnchor="middle" fontSize={28} fontWeight="bold" fill={color}>
            {riskScore}
          </text>
          <text x={cx} y={cy + 10} textAnchor="middle" fontSize={12} fill="var(--muted)">
            / 100
          </text>
        </svg>
      </div>

      {/* Level Badge */}
      <div className="flex justify-center mb-4">
        <span
          className="px-3 py-1 rounded-full text-sm font-semibold uppercase"
          style={{ backgroundColor: color, color: '#FFFFFF' }}
        >
          {level}
        </span>
      </div>

      {/* Factor Breakdown */}
      <div className="space-y-2 mb-4">
        {factorList.map(f => (
          <div key={f.key}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs" style={{ color: 'var(--text)' }}>{f.label}</span>
              <span className="text-xs font-medium" style={{ color: f.score >= 15 ? '#EF4444' : 'var(--muted)' }}>
                {f.score}/{f.max}
              </span>
            </div>
            <div className="w-full rounded-full h-1.5" style={{ backgroundColor: 'var(--border)' }}>
              <div
                className="h-1.5 rounded-full"
                style={{
                  width: `${(f.score / f.max) * 100}%`,
                  backgroundColor: f.score >= 15 ? '#EF4444' : f.score >= 5 ? '#EAB308' : '#22C55E',
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
          <p className="text-xs font-medium uppercase tracking-wide mb-2" style={{ color: 'var(--muted)' }}>Recommendations</p>
          <ul className="space-y-1">
            {recommendations.map((r, i) => (
              <li key={i} className="text-xs flex items-start gap-1" style={{ color: 'var(--text)' }}>
                <span style={{ color }}>{'>'}</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

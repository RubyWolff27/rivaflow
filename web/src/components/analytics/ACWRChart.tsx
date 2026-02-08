interface ACWRPoint {
  date: string;
  acwr: number;
  zone: string;
  acute: number;
  chronic: number;
  daily_load: number;
}

interface ACWRChartProps {
  data: ACWRPoint[];
  currentAcwr: number;
  currentZone: string;
  insight: string;
}

export default function ACWRChart({ data, currentAcwr, currentZone, insight }: ACWRChartProps) {
  if (!data || data.length === 0) return null;

  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Last 60 data points max for readability
  const displayData = data.slice(-60);

  const maxAcwr = Math.max(2.0, ...displayData.map(d => d.acwr));
  const xScale = (i: number) => padding.left + (i / (displayData.length - 1)) * chartW;
  const yScale = (v: number) => padding.top + chartH - (v / maxAcwr) * chartH;

  // Zone bands
  const zones = [
    { min: 0, max: 0.8, color: 'rgba(59, 130, 246, 0.1)', label: 'Undertrained' },
    { min: 0.8, max: 1.3, color: 'rgba(34, 197, 94, 0.1)', label: 'Sweet Spot' },
    { min: 1.3, max: 1.5, color: 'rgba(234, 179, 8, 0.1)', label: 'Caution' },
    { min: 1.5, max: maxAcwr, color: 'rgba(239, 68, 68, 0.1)', label: 'Danger' },
  ];

  // Build ACWR line path
  const linePath = displayData
    .map((d, i) => `${i === 0 ? 'M' : 'L'}${xScale(i)},${yScale(d.acwr)}`)
    .join(' ');

  const zoneColors: Record<string, string> = {
    sweet_spot: 'var(--accent)',
    caution: '#EAB308',
    danger: '#EF4444',
    undertrained: '#3B82F6',
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <div
          className="px-3 py-1 rounded-full text-sm font-semibold"
          style={{
            backgroundColor: zoneColors[currentZone] || 'var(--muted)',
            color: '#FFFFFF',
          }}
        >
          ACWR: {currentAcwr}
        </div>
        <span className="text-xs capitalize" style={{ color: 'var(--muted)' }}>
          {currentZone.replace('_', ' ')}
        </span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '220px' }}>
        {/* Zone backgrounds */}
        {zones.map((zone, i) => {
          const y1 = yScale(Math.min(zone.max, maxAcwr));
          const y2 = yScale(zone.min);
          if (y2 <= y1) return null;
          return (
            <rect
              key={i}
              x={padding.left}
              y={y1}
              width={chartW}
              height={y2 - y1}
              fill={zone.color}
            />
          );
        })}

        {/* Reference lines at 0.8, 1.0, 1.3, 1.5 */}
        {[0.8, 1.0, 1.3, 1.5].map(v => (
          <line
            key={v}
            x1={padding.left}
            y1={yScale(v)}
            x2={padding.left + chartW}
            y2={yScale(v)}
            stroke="var(--border)"
            strokeWidth={0.5}
            strokeDasharray={v === 1.0 ? '0' : '3,3'}
          />
        ))}

        {/* Y-axis labels */}
        {[0, 0.5, 1.0, 1.5, 2.0].filter(v => v <= maxAcwr).map(v => (
          <text key={v} x={padding.left - 5} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">
            {v.toFixed(1)}
          </text>
        ))}

        {/* ACWR line */}
        <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" />

        {/* X-axis labels */}
        {[0, Math.floor(displayData.length / 2), displayData.length - 1].map(i => {
          const d = displayData[i];
          if (!d) return null;
          const label = d.date.slice(5);
          return (
            <text key={i} x={xScale(i)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">
              {label}
            </text>
          );
        })}
      </svg>

      <p className="text-sm mt-2" style={{ color: 'var(--muted)' }}>{insight}</p>
    </div>
  );
}

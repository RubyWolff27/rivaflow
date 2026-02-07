interface DataPoint {
  date: string;
  score: number;
}

interface ReadinessTrendChartProps {
  data: DataPoint[];
}

export default function ReadinessTrendChart({ data }: ReadinessTrendChartProps) {
  if (data.length === 0) return null;

  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const maxScore = 20;
  const minScore = 0;

  const xScale = (i: number) => padding.left + (i / Math.max(data.length - 1, 1)) * plotW;
  const yScale = (v: number) => padding.top + plotH - ((v - minScore) / (maxScore - minScore)) * plotH;

  // Build line path
  const linePath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.score)}`).join(' ');

  // Zone bands (horizontal colored zones)
  const zones = [
    { min: 0, max: 12, color: 'rgba(239, 68, 68, 0.08)' },    // red zone
    { min: 12, max: 16, color: 'rgba(245, 158, 11, 0.08)' },   // yellow zone
    { min: 16, max: 20, color: 'rgba(16, 185, 129, 0.08)' },   // green zone
  ];

  // X-axis labels (show first, middle, last)
  const labelIndices = data.length <= 3
    ? data.map((_, i) => i)
    : [0, Math.floor(data.length / 2), data.length - 1];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ maxHeight: 200 }}
      role="img"
      aria-label="Readiness trend chart"
    >
      {/* Zone bands */}
      {zones.map((zone) => (
        <rect
          key={zone.min}
          x={padding.left}
          y={yScale(zone.max)}
          width={plotW}
          height={yScale(zone.min) - yScale(zone.max)}
          fill={zone.color}
        />
      ))}

      {/* Grid lines */}
      {[0, 5, 10, 15, 20].map((v) => (
        <g key={v}>
          <line
            x1={padding.left}
            y1={yScale(v)}
            x2={width - padding.right}
            y2={yScale(v)}
            stroke="var(--border)"
            strokeWidth={1}
          />
          <text
            x={padding.left - 8}
            y={yScale(v) + 4}
            textAnchor="end"
            fontSize={10}
            fill="var(--muted)"
          >
            {v}
          </text>
        </g>
      ))}

      {/* Trend line */}
      <path
        d={linePath}
        fill="none"
        stroke="var(--accent)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {data.map((d, i) => (
        <circle
          key={i}
          cx={xScale(i)}
          cy={yScale(d.score)}
          r={3}
          fill="var(--accent)"
        >
          <title>{d.date}: {d.score}/20</title>
        </circle>
      ))}

      {/* X-axis labels */}
      {labelIndices.map((i) => (
        <text
          key={i}
          x={xScale(i)}
          y={height - 5}
          textAnchor="middle"
          fontSize={10}
          fill="var(--muted)"
        >
          {new Date(data[i].date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </text>
      ))}
    </svg>
  );
}

// Small hand-rolled SVG line chart for a single daily Garmin metric over time.
// Mirrors the ACWRChart pattern (no charting lib). Gaps (null values) split the
// line into segments so missing days don't draw a false straight line.

interface TrendPoint {
  date: string;
  value: number | null;
}

interface GarminTrendChartProps {
  title: string;
  data: TrendPoint[];
  color?: string;
  unit?: string;
  /** number of decimal places for the current-value badge */
  decimals?: number;
}

export default function GarminTrendChart({ title, data, color = 'var(--accent)', unit = '', decimals = 0 }: GarminTrendChartProps) {
  const points = (data ?? []).filter((d) => d.value != null) as { date: string; value: number }[];
  if (points.length < 2) {
    return (
      <div>
        <div className="text-sm font-medium mb-1">{title}</div>
        <div className="text-xs" style={{ color: 'var(--muted)' }}>Not enough data yet</div>
      </div>
    );
  }

  const width = 600;
  const height = 160;
  const padding = { top: 16, right: 16, bottom: 22, left: 34 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const display = data.slice(-90); // align x across the full window incl. gaps
  const n = display.length;
  const vals = points.map((p) => p.value);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const pad = span * 0.15;
  const yMin = min - pad;
  const yMax = max + pad;

  const xScale = (i: number) => padding.left + (n <= 1 ? 0 : (i / (n - 1)) * chartW);
  const yScale = (v: number) => padding.top + chartH - ((v - yMin) / (yMax - yMin)) * chartH;

  // Build path with gaps
  let path = '';
  display.forEach((d, i) => {
    if (d.value == null) {
      path += ' ';
      return;
    }
    const cmd = i === 0 || display[i - 1]?.value == null ? 'M' : 'L';
    path += `${cmd}${xScale(i).toFixed(1)},${yScale(d.value).toFixed(1)} `;
  });

  const last = points[points.length - 1];
  const first = display.find((d) => d.value != null);
  let lastIdx = n - 1;
  for (let i = display.length - 1; i >= 0; i--) {
    if (display[i].value != null) { lastIdx = i; break; }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium">{title}</span>
        <span className="text-sm font-semibold" style={{ color }}>
          {last.value.toFixed(decimals)}
          {unit ? ` ${unit}` : ''}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: '170px' }}>
        {[yMax, (yMax + yMin) / 2, yMin].map((v, i) => (
          <g key={i}>
            <line x1={padding.left} y1={yScale(v)} x2={padding.left + chartW} y2={yScale(v)} stroke="var(--border)" strokeWidth={0.5} strokeDasharray="3,3" />
            <text x={padding.left - 4} y={yScale(v) + 3} textAnchor="end" fontSize={9} fill="var(--muted)">
              {v.toFixed(decimals)}
            </text>
          </g>
        ))}
        <path d={path.trim()} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {last.value != null && (
          <circle cx={xScale(lastIdx)} cy={yScale(last.value)} r={3} fill={color} />
        )}
        {[first, display[Math.floor(n / 2)], last].map((d, i) =>
          d ? (
            <text key={i} x={xScale(i === 0 ? 0 : i === 2 ? n - 1 : Math.floor(n / 2))} y={height - 5} textAnchor="middle" fontSize={9} fill="var(--muted)">
              {d.date.slice(5)}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  );
}

interface ScatterPoint {
  date: string;
  hrv_ms: number;
  quality: number;
}

interface HRVPredictorChartProps {
  scatter: ScatterPoint[];
  rValue: number;
  hrvThreshold: number;
  qualityAbove: number;
  qualityBelow: number;
}

export default function HRVPredictorChart({ scatter, rValue, hrvThreshold, qualityAbove, qualityBelow }: HRVPredictorChartProps) {
  if (scatter.length === 0) return null;

  const width = 600;
  const height = 220;
  const pad = { top: 20, right: 20, bottom: 35, left: 50 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const hrvs = scatter.map(p => p.hrv_ms);
  const minHRV = Math.floor(Math.min(...hrvs) * 0.9);
  const maxHRV = Math.ceil(Math.max(...hrvs) * 1.1);
  const hrvRange = maxHRV - minHRV || 1;

  const xScale = (v: number) => pad.left + ((v - minHRV) / hrvRange) * plotW;
  const yScale = (v: number) => pad.top + plotH - (v / 100) * plotH;

  // Threshold line
  const thresholdX = xScale(hrvThreshold);

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 220 }}>
        {/* Grid */}
        {[0, 25, 50, 75, 100].map(v => (
          <g key={v}>
            <line x1={pad.left} y1={yScale(v)} x2={width - pad.right} y2={yScale(v)} stroke="var(--border)" strokeWidth={1} />
            <text x={pad.left - 6} y={yScale(v) + 4} textAnchor="end" fontSize={10} fill="var(--muted)">{v}</text>
          </g>
        ))}

        {/* Threshold line */}
        {hrvThreshold > 0 && (
          <>
            <line x1={thresholdX} y1={pad.top} x2={thresholdX} y2={pad.top + plotH} stroke="#8B5CF6" strokeWidth={2} strokeDasharray="5 3" />
            <text x={thresholdX + 4} y={pad.top + 12} fontSize={9} fill="#8B5CF6">Threshold: {hrvThreshold}ms</text>
            {/* Below zone */}
            <rect x={pad.left} y={pad.top} width={thresholdX - pad.left} height={plotH} fill="rgba(239, 68, 68, 0.04)" />
            {/* Above zone */}
            <rect x={thresholdX} y={pad.top} width={width - pad.right - thresholdX} height={plotH} fill="rgba(16, 185, 129, 0.04)" />
          </>
        )}

        {/* Scatter */}
        {scatter.map((p, i) => (
          <circle
            key={i}
            cx={xScale(p.hrv_ms)}
            cy={yScale(p.quality)}
            r={4}
            fill={p.hrv_ms >= hrvThreshold ? '#10B981' : '#EF4444'}
            opacity={0.7}
          >
            <title>{p.date}: HRV {p.hrv_ms}ms, Quality {p.quality}/100</title>
          </circle>
        ))}

        {/* X labels */}
        {[minHRV, Math.round((minHRV + maxHRV) / 2), maxHRV].map(v => (
          <text key={v} x={xScale(v)} y={height - 5} textAnchor="middle" fontSize={10} fill="var(--muted)">{v}ms</text>
        ))}

        {/* Axis labels */}
        <text x={width / 2} y={height - 2} textAnchor="middle" fontSize={10} fill="var(--muted)">HRV (ms)</text>
        <text x={12} y={height / 2} textAnchor="middle" fontSize={10} fill="var(--muted)" transform={`rotate(-90, 12, ${height / 2})`}>Quality</text>
      </svg>

      <div className="flex items-center gap-3 mt-2 flex-wrap">
        <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}>
          r = {rValue}
        </span>
        <span className="text-xs" style={{ color: '#10B981' }}>
          Above threshold: {qualityAbove}/100 avg
        </span>
        <span className="text-xs" style={{ color: '#EF4444' }}>
          Below threshold: {qualityBelow}/100 avg
        </span>
      </div>
    </div>
  );
}

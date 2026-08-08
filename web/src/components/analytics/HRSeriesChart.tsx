import { useMemo, useRef, useState } from 'react';

/** Wahoo/Air personal zone edges (bpm) — same boundaries the zone bars use
 *  (z1 ≤118, z2 ≤147, z3 ≤160, z4 ≤174, z5 above; HRmax 177). */
const ZONE_EDGES = [118, 147, 160, 174];
/** GarminZoneBar's established zone hues, recessive here as background bands. */
const ZONE_COLORS = ['#93C5FD', '#34D399', '#FBBF24', '#F97316', '#EF4444'];
const BAND_OPACITY = 0.09;

const VB_W = 640;
const VB_H = 200;
const PAD = { top: 10, right: 10, bottom: 22, left: 34 };

function fmtTime(sec: number): string {
  const m = Math.floor(sec / 60);
  if (m < 60) return `${m}m`;
  return `${Math.floor(m / 60)}h${String(m % 60).padStart(2, '0')}`;
}

interface Props {
  /** [offset_sec, bpm] pairs, 60s buckets from the Air forward link. */
  series: number[][];
  avgHr?: number | null;
}

/**
 * Heart rate across the whole session — single-series SVG line over recessive
 * zone bands, crosshair + tooltip on hover/touch. Renders nothing for a series
 * under 2 points (a line needs a line).
 */
export default function HRSeriesChart({ series, avgHr }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const model = useMemo(() => {
    const pts = (series ?? []).filter(
      (p): p is [number, number] =>
        Array.isArray(p) && p.length === 2 && Number.isFinite(p[0]) && Number.isFinite(p[1])
    );
    if (pts.length < 2) return null;
    const xMax = pts[pts.length - 1][0];
    const bpms = pts.map((p) => p[1]);
    // Y domain: pad around observed range, snapped to 10s for calm gridlines.
    const yMin = Math.max(40, Math.floor((Math.min(...bpms) - 8) / 10) * 10);
    const yMax = Math.ceil((Math.max(...bpms) + 8) / 10) * 10;
    const plotW = VB_W - PAD.left - PAD.right;
    const plotH = VB_H - PAD.top - PAD.bottom;
    const x = (sec: number) => PAD.left + (xMax === 0 ? 0 : (sec / xMax) * plotW);
    const y = (bpm: number) => PAD.top + plotH - ((bpm - yMin) / (yMax - yMin)) * plotH;
    const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(' ');
    // ~4 recessive horizontal gridlines on multiples of 20 bpm.
    const gridStep = yMax - yMin > 80 ? 40 : 20;
    const gridLines: number[] = [];
    for (let v = Math.ceil(yMin / gridStep) * gridStep; v <= yMax; v += gridStep) gridLines.push(v);
    // X ticks: start / mid / end.
    const xTicks = [0, Math.round(xMax / 2), xMax];
    return { pts, xMax, yMin, yMax, x, y, path, gridLines, xTicks };
  }, [series]);

  if (!model) return null;
  const { pts, xMax, yMin, yMax, x, y, path, gridLines, xTicks } = model;

  const handleMove = (clientX: number) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const sec = ((clientX - rect.left) / rect.width) * VB_W;
    // nearest point by projected x
    let best = 0;
    let bestDist = Infinity;
    pts.forEach((p, i) => {
      const d = Math.abs(x(p[0]) - sec);
      if (d < bestDist) { bestDist = d; best = i; }
    });
    setHoverIdx(best);
  };

  const hover = hoverIdx != null ? pts[hoverIdx] : null;
  const peak = pts.reduce((a, b) => (b[1] > a[1] ? b : a));

  return (
    <div>
      <div className="text-xs mb-1.5" style={{ color: 'var(--muted)' }}>Heart rate over the session</div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        className="w-full"
        role="img"
        aria-label={`Heart rate across the session: ${pts[0][1]} bpm at the start, peaking at ${peak[1]} bpm, over ${fmtTime(xMax)}.`}
        onPointerMove={(e) => handleMove(e.clientX)}
        onPointerLeave={() => setHoverIdx(null)}
      >
        {/* Recessive zone bands (clipped to plot + observed range) */}
        {ZONE_COLORS.map((color, zi) => {
          const lo = zi === 0 ? yMin : ZONE_EDGES[zi - 1];
          const hi = zi === ZONE_COLORS.length - 1 ? yMax : ZONE_EDGES[zi];
          const top = Math.max(lo, yMin);
          const bottom = Math.min(hi, yMax);
          if (bottom <= top) return null;
          return (
            <rect
              key={color}
              x={PAD.left}
              y={y(bottom)}
              width={VB_W - PAD.left - PAD.right}
              height={y(top) - y(bottom)}
              fill={color}
              opacity={BAND_OPACITY}
            />
          );
        })}

        {/* Recessive grid + y labels (text tokens, never series color) */}
        {gridLines.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={VB_W - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--border)" strokeWidth={1} />
            <text x={PAD.left - 6} y={y(v)} textAnchor="end" dominantBaseline="middle" fontSize={9} fill="var(--muted)">
              {v}
            </text>
          </g>
        ))}

        {/* Avg HR reference (dashed, muted) */}
        {avgHr != null && avgHr >= yMin && avgHr <= yMax && (
          <g>
            <line x1={PAD.left} x2={VB_W - PAD.right} y1={y(avgHr)} y2={y(avgHr)} stroke="var(--muted)" strokeWidth={1} strokeDasharray="4 4" opacity={0.7} />
            <text x={VB_W - PAD.right} y={y(avgHr) - 4} textAnchor="end" fontSize={9} fill="var(--muted)">
              avg {avgHr}
            </text>
          </g>
        )}

        {/* The line */}
        <path d={path} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

        {/* Peak label (selective direct label) */}
        <text x={Math.min(x(peak[0]), VB_W - PAD.right - 4)} y={Math.max(y(peak[1]) - 6, 10)} textAnchor="middle" fontSize={9} fontWeight={600} fill="var(--text)">
          {peak[1]}
        </text>

        {/* X ticks */}
        {xTicks.map((t, i) => (
          <text
            key={t}
            x={x(t)}
            y={VB_H - 6}
            textAnchor={i === 0 ? 'start' : i === xTicks.length - 1 ? 'end' : 'middle'}
            fontSize={9}
            fill="var(--muted)"
          >
            {fmtTime(t)}
          </text>
        ))}

        {/* Crosshair + tooltip */}
        {hover && (
          <g>
            <line x1={x(hover[0])} x2={x(hover[0])} y1={PAD.top} y2={VB_H - PAD.bottom} stroke="var(--muted)" strokeWidth={1} opacity={0.5} />
            <circle cx={x(hover[0])} cy={y(hover[1])} r={4} fill="var(--accent)" stroke="var(--surface)" strokeWidth={2} />
            {(() => {
              const boxW = 76;
              const bx = Math.min(Math.max(x(hover[0]) - boxW / 2, PAD.left), VB_W - PAD.right - boxW);
              const by = y(hover[1]) - 30 < PAD.top ? y(hover[1]) + 10 : y(hover[1]) - 30;
              return (
                <g>
                  <rect x={bx} y={by} width={boxW} height={20} rx={4} fill="var(--surfaceElev)" stroke="var(--border)" />
                  <text x={bx + boxW / 2} y={by + 13} textAnchor="middle" fontSize={10} fill="var(--text)">
                    {hover[1]} bpm · {fmtTime(hover[0])}
                  </text>
                </g>
              );
            })()}
          </g>
        )}
      </svg>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsApi } from '../../api/client';
import { logger } from '../../utils/logger';
import { Card } from '../ui';

export type MetricKey = 'coverage' | 'frequency' | 'load';
export type WindowKey = 'all' | '12w' | '8w';

interface AxisMetric {
  value?: number;
  prev?: number | null;
  axis_max?: number;
  per_10h?: number;
}

interface GameAxis {
  key?: string;
  label?: string;
  coverage?: AxisMetric;
  frequency?: AxisMetric;
  load?: AxisMetric;
}

export interface GameDistribution {
  window?: { mode?: string; start?: string | null; end?: string | null };
  axes?: GameAxis[];
  gaps?: {
    sessions_in_window?: number;
    sessions_with_techniques?: number;
    load_sessions_with_hr?: number;
    load_unattributed_pct?: number;
    other_category_touches?: number;
  };
  totals?: { mat_hours?: number; touches?: number; distinct_movements?: number };
}

const METRICS: { key: MetricKey; label: string }[] = [
  { key: 'coverage', label: 'Coverage' },
  { key: 'frequency', label: 'Frequency' },
  { key: 'load', label: 'Load' },
];

const WINDOWS: { key: WindowKey; label: string }[] = [
  { key: 'all', label: 'All time' },
  { key: '12w', label: '12 weeks' },
  { key: '8w', label: '8 weeks' },
];

// Geometry — a fixed viewBox keeps the wheel and its outer labels in frame at any width.
const VB_W = 420;
const VB_H = 350;
const CX = 210;
const CY = 160;
const MAX_R = 95;
const LABEL_R = 134;
const RINGS = [0.25, 0.5, 0.75, 1];

const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0);

/** Fraction of this axis' all-time max. axis_max === 0 means the axis has never had data. */
function ratio(value: number, axisMax: number): number {
  if (axisMax <= 0) return 0;
  return Math.max(0, Math.min(1, value / axisMax));
}

function formatValue(v: number, metric: MetricKey): string {
  if (metric === 'load') return v.toFixed(1);
  return Number.isInteger(v) ? String(v) : v.toFixed(1);
}

function pointAt(index: number, r: number): { x: number; y: number } {
  const rad = ((-90 + index * 60) * Math.PI) / 180;
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) };
}

function anchorFor(x: number): 'start' | 'middle' | 'end' {
  const dx = x - CX;
  if (Math.abs(dx) < 1) return 'middle';
  return dx > 0 ? 'start' : 'end';
}

function ringPoints(scale: number): string {
  return [0, 1, 2, 3, 4, 5]
    .map((i) => {
      const p = pointAt(i, MAX_R * scale);
      return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
    })
    .join(' ');
}

export default function GameRadar() {
  const [metric, setMetric] = useState<MetricKey>('coverage');
  const [windowMode, setWindowMode] = useState<WindowKey>('all');
  const [data, setData] = useState<GameDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await analyticsApi.gameDistribution({ window: windowMode });
        if (!cancelled) setData(res.data ?? null);
      } catch (err) {
        if (!cancelled) {
          logger.error('Failed to load game distribution:', err);
          setError('Could not load your game distribution.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [windowMode]);

  const controls = (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid var(--border)' }} role="group" aria-label="Metric">
        {METRICS.map((m) => (
          <button
            key={m.key}
            type="button"
            onClick={() => setMetric(m.key)}
            aria-pressed={metric === m.key}
            className="px-3 py-1.5 text-xs font-medium transition-colors"
            style={{
              backgroundColor: metric === m.key ? 'var(--accent)' : 'var(--surface)',
              color: metric === m.key ? '#FFFFFF' : 'var(--muted)',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>
      <select
        value={windowMode}
        onChange={(e) => setWindowMode(e.target.value as WindowKey)}
        aria-label="Time window"
        className="input text-xs"
        style={{ maxWidth: '130px', padding: '0.375rem 0.5rem' }}
      >
        {WINDOWS.map((w) => (
          <option key={w.key} value={w.key}>{w.label}</option>
        ))}
      </select>
    </div>
  );

  const header = (
    <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
      <div>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>Game Distribution</h2>
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Where your logged technique work actually lands
        </p>
      </div>
      {!loading && !error && controls}
    </div>
  );

  if (loading) {
    return (
      <Card>
        {header}
        <div className="animate-pulse">
          <div className="h-64 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }} />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        {header}
        <p className="text-sm" style={{ color: 'var(--muted)' }}>{error}</p>
      </Card>
    );
  }

  const axes = data?.axes ?? [];
  const gaps = data?.gaps ?? {};
  const sessionsWithTechniques = num(gaps.sessions_with_techniques);
  const sessionsInWindow = num(gaps.sessions_in_window);

  // Too little logged technique data for a wheel to say anything honest.
  if (axes.length === 0 || sessionsWithTechniques < 3) {
    return (
      <Card>
        {header}
        <div className="rounded-lg p-5 text-center" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
          <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
            Your wheel is still filling in
          </p>
          <p className="text-sm mb-4" style={{ color: 'var(--muted)' }}>
            The radar needs a few sessions with techniques attached before it can show
            you anything worth trusting. Add the two or three things you actually drilled
            next time you log — that&apos;s enough to get it moving.
          </p>
          <Link
            to="/log"
            className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          >
            Log a session
          </Link>
        </div>
      </Card>
    );
  }

  const rows = axes.map((axis, i) => {
    const m = (axis?.[metric] ?? {}) as AxisMetric;
    const value = num(m.value);
    const axisMax = num(m.axis_max);
    const prev = typeof m.prev === 'number' && Number.isFinite(m.prev) ? m.prev : null;
    const r = MAX_R * ratio(value, axisMax);
    return {
      index: i,
      key: axis?.key ?? String(i),
      label: axis?.label ?? '',
      value,
      axisMax,
      prev,
      per10h: typeof m.per_10h === 'number' && Number.isFinite(m.per_10h) ? m.per_10h : null,
      point: pointAt(i, r),
      labelPoint: pointAt(i, LABEL_R),
      valuePoint: pointAt(i, Math.min(r + 16, MAX_R + 16)),
      hasData: axisMax > 0,
    };
  });

  // Previous-window polygon only when every axis carries a comparison — a partial
  // shape would read as a real drop on the axes that are simply absent.
  const showPrev = rows.length > 0 && rows.every((row) => row.prev !== null);

  const currentPoints = rows.map((row) => `${row.point.x.toFixed(1)},${row.point.y.toFixed(1)}`).join(' ');
  const prevPoints = showPrev
    ? rows
        .map((row) => {
          const p = pointAt(row.index, MAX_R * ratio(row.prev as number, row.axisMax));
          return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
        })
        .join(' ')
    : '';

  const tooltipFor = (row: (typeof rows)[number]): string => {
    if (!row.hasData) return `${row.label}: no data yet`;
    const base = `${row.label}: ${formatValue(row.value, metric)}`;
    if (metric === 'frequency' && row.per10h !== null) return `${base} · ×${row.per10h} per 10 mat-hrs`;
    if (metric === 'load') return `${base} TRIMP-share`;
    return base;
  };

  const gapNote = (() => {
    const base = `Computed from ${sessionsWithTechniques} sessions with logged techniques (of ${sessionsInWindow} in window)`;
    if (metric !== 'load') return base;
    const pct = num(gaps.load_unattributed_pct);
    return `${base} · ${pct}% of training load unattributed — log techniques on HR-tracked sessions`;
  })();

  return (
    <Card>
      {header}

      {showPrev && (
        <div className="flex items-center gap-4 mb-2">
          <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
            <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: 'var(--accent)' }} />
            This window
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
            <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: 'var(--muted)' }} />
            Previous
          </span>
        </div>
      )}

      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="w-full" style={{ maxHeight: '360px' }} role="img" aria-label="Game distribution radar">
        {/* Recessive hex grid */}
        {RINGS.map((scale) => (
          <polygon
            key={scale}
            points={ringPoints(scale)}
            fill="none"
            stroke="var(--border)"
            strokeWidth={1}
          />
        ))}
        {rows.map((row) => (
          <line
            key={`spoke-${row.key}`}
            x1={CX}
            y1={CY}
            x2={pointAt(row.index, MAX_R).x}
            y2={pointAt(row.index, MAX_R).y}
            stroke="var(--border)"
            strokeWidth={1}
          />
        ))}

        {/* Previous window sits under the current one, stroke only */}
        {showPrev && (
          <polygon points={prevPoints} fill="none" stroke="var(--muted)" strokeWidth={2} strokeLinejoin="round" />
        )}

        <polygon
          points={currentPoints}
          fill="rgba(var(--accent-rgb), 0.08)"
          stroke="var(--accent)"
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {rows.map((row) => (
          <g key={`vertex-${row.key}`}>
            <circle cx={row.point.x} cy={row.point.y} r={4} fill="var(--accent)" />
            {/* Oversized transparent hit target */}
            <circle cx={row.point.x} cy={row.point.y} r={10} fill="transparent" style={{ cursor: 'pointer' }}>
              <title>{tooltipFor(row)}</title>
            </circle>
          </g>
        ))}

        {/* Raw values in text tokens, never the series color */}
        {rows.filter((row) => row.hasData).map((row) => (
          <text
            key={`value-${row.key}`}
            x={row.valuePoint.x}
            y={row.valuePoint.y}
            textAnchor={anchorFor(row.valuePoint.x)}
            dominantBaseline="middle"
            fontSize={10}
            fontWeight={600}
            fill="var(--text)"
          >
            {formatValue(row.value, metric)}
          </text>
        ))}

        {rows.map((row) => (
          <g key={`label-${row.key}`}>
            <text
              x={row.labelPoint.x}
              y={row.labelPoint.y}
              textAnchor={anchorFor(row.labelPoint.x)}
              dominantBaseline="middle"
              fontSize={11}
              fill="var(--muted)"
            >
              {row.label}
            </text>
            {!row.hasData && (
              <>
                <circle
                  cx={row.labelPoint.x + (anchorFor(row.labelPoint.x) === 'end' ? 8 : anchorFor(row.labelPoint.x) === 'start' ? -8 : 0)}
                  cy={row.labelPoint.y + (anchorFor(row.labelPoint.x) === 'middle' ? -12 : 0)}
                  r={4}
                  fill="none"
                  stroke="var(--muted)"
                  strokeWidth={1.5}
                />
                <text
                  x={row.labelPoint.x}
                  y={row.labelPoint.y + 13}
                  textAnchor={anchorFor(row.labelPoint.x)}
                  dominantBaseline="middle"
                  fontSize={9}
                  fill="var(--muted)"
                >
                  no data yet
                </text>
              </>
            )}
          </g>
        ))}
      </svg>

      <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>{gapNote}</p>
    </Card>
  );
}

import { useEffect, useState } from 'react';
import type { BlockSummary, SlotStatus } from '../../types/curriculum';
import { STATUS_ORDER, statusRank } from './constants';

interface CurriculumRadarProps {
  blocks: BlockSummary[];
}

// Geometry — fixed viewBox so the wheel and its outer labels stay in frame.
const VB_W = 420;
const VB_H = 360;
const CX = 210;
const CY = 170;
const MAX_R = 100;
const LABEL_R = 138;
const RINGS = [0.25, 0.5, 0.75, 1];

const HORIZON_KEY = 'rivaflow.curriculum.gradingHorizon';

/** Stand-up is the injury-risk block: paced ahead so it is never crammed late. */
const EARLY_PACE_MULTIPLIER = 1.5;

interface Horizon {
  /** Target grading date, ISO. */
  date: string;
  /** The day the target was set — the pace line's origin. */
  setOn: string;
}

function readHorizon(): Horizon | null {
  try {
    const raw = localStorage.getItem(HORIZON_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Horizon>;
    if (!parsed?.date || !parsed?.setOn) return null;
    return { date: parsed.date, setOn: parsed.setOn };
  } catch {
    return null;
  }
}

function writeHorizon(horizon: Horizon | null): void {
  try {
    if (horizon) localStorage.setItem(HORIZON_KEY, JSON.stringify(horizon));
    else localStorage.removeItem(HORIZON_KEY);
  } catch {
    /* private browsing — the radar still renders, just without a pace line */
  }
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function daysBetween(from: string, to: string): number {
  const a = Date.parse(`${from}T00:00:00Z`);
  const b = Date.parse(`${to}T00:00:00Z`);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return 0;
  return Math.round((b - a) / 86_400_000);
}

function pointAt(index: number, r: number, count: number): { x: number; y: number } {
  const rad = ((-90 + (index * 360) / count) * Math.PI) / 180;
  return { x: CX + r * Math.cos(rad), y: CY + r * Math.sin(rad) };
}

function anchorFor(x: number): 'start' | 'middle' | 'end' {
  const dx = x - CX;
  if (Math.abs(dx) < 1) return 'middle';
  return dx > 0 ? 'start' : 'end';
}

function ratio(value: number, axisMax: number): number {
  if (axisMax <= 0) return 0;
  return Math.max(0, Math.min(1, value / axisMax));
}

/** Slots at or above a rung, summed from the block's status counts. */
function countAtLeast(block: BlockSummary, floor: SlotStatus): number {
  const min = statusRank(floor);
  return STATUS_ORDER.reduce(
    (n, status, i) => (i >= min ? n + (block.status_counts?.[status] ?? 0) : n),
    0,
  );
}

/**
 * Curriculum coverage per syllabus block, with an optional pace line against a
 * self-set grading date. The pace line is a target, not a forecast — the
 * caption says so, because the council's standing worry is exactly that a
 * radar invites chasing fill.
 */
export default function CurriculumRadar({ blocks }: CurriculumRadarProps) {
  const [horizon, setHorizon] = useState<Horizon | null>(null);

  useEffect(() => {
    setHorizon(readHorizon());
  }, []);

  const onHorizonChange = (value: string) => {
    const next = value ? { date: value, setOn: todayIso() } : null;
    setHorizon(next);
    writeHorizon(next);
  };

  const count = blocks.length;

  const picker = (
    <label className="text-xs flex items-center gap-2" style={{ color: 'var(--muted)' }}>
      Target grading date
      <input
        type="date"
        aria-label="Target grading date"
        className="input text-xs"
        style={{ padding: '0.25rem 0.5rem', maxWidth: '160px' }}
        value={horizon?.date ?? ''}
        onChange={(e) => onHorizonChange(e.target.value)}
      />
    </label>
  );

  if (count === 0) {
    return (
      <p className="text-sm" style={{ color: 'var(--muted)' }}>
        No blocks to draw yet.
      </p>
    );
  }

  const rows = blocks.map((block, i) => {
    const axisMax = block.slot_count ?? 0;
    const grooved = countAtLeast(block, 'grooved');
    const live = countAtLeast(block, 'live');
    return {
      index: i,
      key: block.block,
      label: block.label ?? block.block,
      early: block.pace_weight === 'early',
      axisMax,
      grooved,
      live,
      hasData: axisMax > 0,
      groovedPoint: pointAt(i, MAX_R * ratio(grooved, axisMax), count),
      livePoint: pointAt(i, MAX_R * ratio(live, axisMax), count),
      labelPoint: pointAt(i, LABEL_R, count),
      valuePoint: pointAt(i, Math.min(MAX_R * ratio(grooved, axisMax) + 16, MAX_R + 16), count),
    };
  });

  // Elapsed share of the run-up to the target date. Origin is the day the date
  // was set, because nothing in the API records when the campaign started.
  let paceFraction: number | null = null;
  if (horizon) {
    const total = daysBetween(horizon.setOn, horizon.date);
    const elapsed = daysBetween(horizon.setOn, todayIso());
    paceFraction = total <= 0 ? 1 : Math.max(0, Math.min(1, elapsed / total));
  }

  const pacePoints =
    paceFraction === null
      ? ''
      : rows
          .map((row) => {
            const expected = row.early
              ? Math.min(1, (paceFraction as number) * EARLY_PACE_MULTIPLIER)
              : (paceFraction as number);
            const p = pointAt(row.index, MAX_R * expected, count);
            return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
          })
          .join(' ');

  const groovedPoints = rows
    .map((r) => `${r.groovedPoint.x.toFixed(1)},${r.groovedPoint.y.toFixed(1)}`)
    .join(' ');
  const livePoints = rows
    .map((r) => `${r.livePoint.x.toFixed(1)},${r.livePoint.y.toFixed(1)}`)
    .join(' ');

  const ringPoints = (scale: number): string =>
    rows
      .map((row) => {
        const p = pointAt(row.index, MAX_R * scale, count);
        return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
      })
      .join(' ');

  return (
    <div className="space-y-3" data-testid="curriculum-radar">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-base font-semibold" style={{ color: 'var(--text)' }}>
            Curriculum coverage
          </h2>
          <p className="text-xs" style={{ color: 'var(--muted)' }}>
            Raw slot counts per syllabus block — grooved or better, and live or better.
          </p>
        </div>
        {picker}
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: 'var(--accent)' }} />
          Grooved or better
        </span>
        <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: 'var(--text)' }} />
          Live or better
        </span>
        {pacePoints && (
          <span className="inline-flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted)' }}>
            <span className="inline-block w-4 h-0 border-t-2 border-dashed" style={{ borderColor: 'var(--muted)' }} />
            Pace line
          </span>
        )}
      </div>

      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        className="w-full"
        style={{ maxHeight: '360px' }}
        role="img"
        aria-label="Curriculum coverage radar"
      >
        {RINGS.map((scale) => (
          <polygon key={scale} points={ringPoints(scale)} fill="none" stroke="var(--border)" strokeWidth={1} />
        ))}
        {rows.map((row) => {
          const spoke = pointAt(row.index, MAX_R, count);
          return (
            <line
              key={`spoke-${row.key}`}
              x1={CX}
              y1={CY}
              x2={spoke.x}
              y2={spoke.y}
              stroke="var(--border)"
              strokeWidth={1}
            />
          );
        })}

        {pacePoints && (
          <polygon
            data-testid="pace-line"
            points={pacePoints}
            fill="none"
            stroke="var(--muted)"
            strokeWidth={1.5}
            strokeDasharray="4 3"
            strokeLinejoin="round"
          />
        )}

        <polygon
          points={groovedPoints}
          fill="rgba(var(--accent-rgb), 0.08)"
          stroke="var(--accent)"
          strokeWidth={2}
          strokeLinejoin="round"
        />
        <polygon points={livePoints} fill="none" stroke="var(--text)" strokeWidth={2} strokeLinejoin="round" />

        {rows.map((row) => (
          <g key={`vertex-${row.key}`}>
            <circle cx={row.groovedPoint.x} cy={row.groovedPoint.y} r={4} fill="var(--accent)" />
            <circle cx={row.groovedPoint.x} cy={row.groovedPoint.y} r={10} fill="transparent" style={{ cursor: 'pointer' }}>
              <title>
                {row.hasData
                  ? `${row.label}: ${row.grooved} grooved+ · ${row.live} live+ of ${row.axisMax} slots`
                  : `${row.label}: no slots yet`}
              </title>
            </circle>
          </g>
        ))}

        {rows.filter((r) => r.hasData).map((row) => (
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
            {row.grooved}
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
            )}
          </g>
        ))}
      </svg>

      <p className="text-xs" style={{ color: 'var(--muted)' }}>
        Vertex numbers are slot counts, not scores. Axis reach is the number of slots that
        block asks for.
      </p>
      {pacePoints ? (
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Pace line: where even coverage would sit today on the way to{' '}
          {horizon?.date}, measured from the day you set that date. Stand up is paced{' '}
          {EARLY_PACE_MULTIPLIER}× ahead — it is the injury-risk block and should never be
          crammed late. This is pace against your own target, not a promise about grading.
        </p>
      ) : (
        <p className="text-xs" style={{ color: 'var(--muted)' }}>
          Set a target grading date to draw a pace line. It is stored on this device only.
        </p>
      )}
    </div>
  );
}

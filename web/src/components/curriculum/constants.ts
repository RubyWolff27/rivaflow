import type { CurriculumSlot, SlotStatus } from '../../types/curriculum';

/** Ladder order — index comparisons are how "status ≥ grooved" is expressed. */
export const STATUS_ORDER: SlotStatus[] = [
  'not-started',
  'drilled',
  'grooved',
  'live',
  'coach-verified',
];

export function statusRank(status: SlotStatus | null | undefined): number {
  const i = STATUS_ORDER.indexOf((status ?? 'not-started') as SlotStatus);
  return i < 0 ? 0 : i;
}

export function atLeast(status: SlotStatus | null | undefined, floor: SlotStatus): boolean {
  return statusRank(status) >= statusRank(floor);
}

interface StatusMeta {
  label: string;
  /** Short plain-language rule, shown in tooltips and the detail sheet. */
  rule: string;
  color: string;
  background: string;
  border: string;
}

/** Five visually distinct treatments — never reused between rungs. */
export const STATUS_META: Record<SlotStatus, StatusMeta> = {
  'not-started': {
    label: 'Not started',
    rule: 'No logged evidence yet.',
    color: 'var(--muted)',
    background: 'transparent',
    border: '1px dashed var(--border)',
  },
  drilled: {
    label: 'Drilled',
    rule: 'Appears in at least 1 logged session (cooperative).',
    color: 'var(--muted)',
    background: 'var(--surfaceElev)',
    border: '1px solid var(--border)',
  },
  grooved: {
    label: 'Grooved',
    rule: 'Drilled across 3+ distinct sessions spanning 3+ weeks.',
    color: 'var(--text)',
    background: 'var(--surfaceElev)',
    border: '1px solid var(--text)',
  },
  live: {
    label: 'Live',
    rule: 'Landed under resistance on 2+ occasions vs 2+ different partners.',
    color: '#FFFFFF',
    background: 'var(--accent)',
    border: '1px solid var(--accent)',
  },
  'coach-verified': {
    label: 'Coach-verified',
    rule: 'A coach signed it off. Never inferred from your logs.',
    color: 'var(--accent)',
    background: 'rgba(var(--accent-rgb), 0.12)',
    border: '2px solid var(--accent)',
  },
};

/**
 * Staleness is VISUAL ONLY (council ruling — a stale slot keeps its rung).
 * These thresholds drive opacity on the chip and nothing else.
 */
export const STALE_DAYS = 42;
export const VERY_STALE_DAYS = 90;

export function stalenessOpacity(days: number | null | undefined): number {
  if (days == null) return 1;
  if (days >= VERY_STALE_DAYS) return 0.45;
  if (days >= STALE_DAYS) return 0.7;
  return 1;
}

// ---------------------------------------------------------------------------
// System view: requirement_key -> (position, component)
// ---------------------------------------------------------------------------

export const POSITIONS = [
  'Half guard bottom',
  'Pressure pass',
  'Pin',
  'Back',
] as const;

export const COMPONENTS = [
  'Entries',
  'Offense',
  'Defensive awareness',
  'Troubleshooting',
] as const;

export type PositionName = (typeof POSITIONS)[number];
export type ComponentName = (typeof COMPONENTS)[number];

/**
 * Every AJJ purple requirement lands in exactly ONE cell, so the grid's counts
 * sum to the slate and nothing is double-counted. Two rules settle the cases
 * the requirement labels leave open:
 *
 *  1. An escape is always Troubleshooting, and it belongs to the position you
 *     are escaping TO, not the one you are under. Bottom side-control and
 *     bottom-mount escapes therefore sit under Half guard bottom — recovering
 *     guard is the bottom game's failure recovery, not the pin's.
 *  2. A takedown is an Entry to the top game, so the whole stand-up block sits
 *     under Pressure pass / Entries.
 *
 * This keeps the brief's steer (guard→Half guard bottom, side→Pressure
 * pass/Pin, back→Back) with one documented departure: `side-escapes` follows
 * rule 1 to Half guard bottom rather than staying with the side block.
 *
 * Cells with no requirement mapped to them are a real finding, not a bug: the
 * syllabus tests almost no top-game defence and almost no troubleshooting. The
 * grid renders those as "no requirement" rather than as a zero.
 */
export const REQUIREMENT_CELL: Record<string, { position: PositionName; component: ComponentName }> = {
  // Half guard bottom — the B-game wrestle-up.
  'guard-sweeps': { position: 'Half guard bottom', component: 'Entries' },
  'guard-subs': { position: 'Half guard bottom', component: 'Offense' },
  'guard-defences': { position: 'Half guard bottom', component: 'Defensive awareness' },
  'side-escapes': { position: 'Half guard bottom', component: 'Troubleshooting' },
  'mount-escapes': { position: 'Half guard bottom', component: 'Troubleshooting' },

  // Pressure pass — the A-game.
  'td-strikes': { position: 'Pressure pass', component: 'Entries' },
  'td-defend-strikes': { position: 'Pressure pass', component: 'Entries' },
  'td-grappling': { position: 'Pressure pass', component: 'Entries' },
  'side-passes': { position: 'Pressure pass', component: 'Offense' },

  // Pin — side control and mount, held.
  'mount-transitions': { position: 'Pin', component: 'Entries' },
  'side-subs': { position: 'Pin', component: 'Offense' },
  'mount-subs': { position: 'Pin', component: 'Offense' },
  'mount-defences': { position: 'Pin', component: 'Defensive awareness' },

  // Back — both sides of it, since there is only one back row.
  'back-transitions': { position: 'Back', component: 'Entries' },
  'back-subs': { position: 'Back', component: 'Offense' },
  'back-defences': { position: 'Back', component: 'Defensive awareness' },
  'back-escapes': { position: 'Back', component: 'Troubleshooting' },
};

/** Which (position, component) pairs the syllabus actually populates. */
export function mappedCells(): Set<string> {
  const cells = new Set<string>();
  for (const cell of Object.values(REQUIREMENT_CELL)) {
    cells.add(`${cell.position}|${cell.component}`);
  }
  return cells;
}

/**
 * The system-view count for one cell: declared slots tagged a-game or b-game
 * that have reached grooved or better. Syllabus-only slots are excluded on
 * purpose — this grid answers "do I own a game?", not "have I covered the
 * syllabus?", and the radar tab is where coverage lives.
 */
export function systemCount(
  slots: CurriculumSlot[],
  position: PositionName,
  component: ComponentName,
): number {
  return slots.filter((slot) => {
    const cell = REQUIREMENT_CELL[slot.requirement_key];
    if (!cell || cell.position !== position || cell.component !== component) return false;
    if (!slot.declared) return false;
    if (slot.game_tag !== 'a-game' && slot.game_tag !== 'b-game') return false;
    return atLeast(slot.status, 'grooved');
  }).length;
}

/**
 * "entry → position → finish", skipping the parts that were never declared.
 * Takes either a slot row or the export's nested `sequence` object, because the
 * two endpoints spell the same three fields differently.
 */
export function sequenceText(slot: {
  seq_entry?: string | null;
  seq_position?: string | null;
  seq_finish?: string | null;
  entry?: string | null;
  position?: string | null;
  finish?: string | null;
}): string {
  return [
    slot.seq_entry ?? slot.entry,
    slot.seq_position ?? slot.position,
    slot.seq_finish ?? slot.finish,
  ]
    .map((part) => (part ?? '').trim())
    .filter(Boolean)
    .join(' → ');
}

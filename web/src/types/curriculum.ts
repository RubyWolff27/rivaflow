/**
 * Shapes for the belt-curriculum tracker.
 *
 * Derived from the committed backend (`rivaflow/core/services/curriculum_service.py`),
 * not guessed. Two things the service deliberately does NOT return are worth
 * knowing before you reach for them:
 *
 *  - there is no per-row evidence history anywhere — `compute_slot_state` hands
 *    back counters only, so a slot's "history" is those counters;
 *  - the export carries `signoff_verdict` but no coach name or sign-off date.
 *    The optional `signoff_coach_name` / `signoff_at` fields below are declared
 *    so the coach view lights up if the backend starts sending them.
 */

export type SlotStatus =
  | 'not-started'
  | 'drilled'
  | 'grooved'
  | 'live'
  | 'coach-verified';

export type GameTag = 'a-game' | 'b-game' | 'syllabus-only';

export type SignoffVerdict = 'verified' | 'not-yet' | 'show-me';

export type PartnerRankBand = 'lower' | 'same' | 'higher';

export type PartnerSize = 'smaller' | 'similar' | 'bigger';

/** The counters `compute_slot_state` derives from evidence + sign-offs. */
export interface SlotState {
  status: SlotStatus;
  sessions: number;
  drilled_entries: number;
  live_occasions: number;
  live_partners: number;
  span_days: number;
  last_evidence_at: string | null;
  staleness_days: number | null;
  weak_evidence: boolean;
  signoff_verdict: SignoffVerdict | null;
  signoff_count: number;
}

/** A `curriculum_slot` row joined with its derived state. */
export interface CurriculumSlot extends SlotState {
  id: number;
  belt: string;
  block: string;
  requirement_key: string;
  requirement_label: string | null;
  slot_index: number;
  of_choice: boolean;
  seq_entry: string | null;
  seq_position: string | null;
  seq_finish: string | null;
  game_tag: GameTag | null;
  movement_ids: string | null;
  is_draft: boolean;
  tension_note: string | null;
  blocker_note: string | null;
  declared_at: string | null;
  declared: boolean;
}

export interface SlotsResponse {
  belt: string;
  slot_count: number;
  status_ladder: SlotStatus[];
  slots: CurriculumSlot[];
}

export interface HardGate {
  key: string;
  label: string;
  type: 'date' | 'count';
  value: string | number | null;
  met: boolean | null;
  note: string | null;
}

export interface BlockSummary {
  block: string;
  label: string | null;
  /** "early" on the stand-up block; null elsewhere. Not a number. */
  pace_weight: string | null;
  slot_count: number;
  declared: number;
  draft: number;
  weak_evidence: number;
  status_counts: Record<SlotStatus, number>;
  game_tag_counts: Record<GameTag, number>;
  untagged: number;
}

export interface SummaryResponse {
  belt: string;
  hard_gates: HardGate[];
  blocks: BlockSummary[];
  totals: {
    slot_count: number;
    declared: number;
    draft: number;
    weak_evidence: number;
    status_counts: Record<SlotStatus, number>;
    game_tag_counts: Record<GameTag, number>;
    untagged: number;
  };
}

/** The trimmed slot the coach export renders. No scores, no percentages. */
export interface ExportSlot {
  id: number;
  requirement_key: string;
  requirement_label: string | null;
  slot_index: number;
  sequence: { entry: string | null; position: string | null; finish: string | null };
  status: SlotStatus;
  declared: boolean;
  is_draft: boolean;
  sessions: number;
  live_occasions: number;
  live_partners: number;
  staleness_days: number | null;
  weak_evidence: boolean;
  signoff_verdict: SignoffVerdict | null;
  blocker_note: string | null;
  tension_note: string | null;
  /** Not currently sent by the backend — see the module note above. */
  signoff_coach_name?: string | null;
  signoff_at?: string | null;
}

export interface ExportBlock {
  block: string;
  label: string | null;
  not_yet: ExportSlot[];
  in_progress: ExportSlot[];
  verified: ExportSlot[];
}

export interface ExportResponse {
  belt: string;
  generated_on: string;
  disclaimer: string;
  hard_gates: HardGate[];
  blocks: ExportBlock[];
}

export interface SlotDeclaration {
  seq_entry?: string | null;
  seq_position?: string | null;
  seq_finish?: string | null;
  game_tag?: GameTag | null;
  movement_ids?: string | null;
  is_draft?: boolean;
  tension_note?: string | null;
  blocker_note?: string | null;
}

export interface EvidencePayload {
  kind: 'drilled' | 'live';
  session_id?: number | null;
  partner_ref?: string | null;
  partner_rank_band?: PartnerRankBand | null;
  partner_size?: PartnerSize | null;
  note?: string | null;
  logged_at?: string | null;
}

export interface SignoffPayload {
  verdict: SignoffVerdict;
  coach_name: string;
  coach_rank?: string | null;
  note?: string | null;
}

export interface MetaPayload {
  competition_date?: string | null;
  competition_note?: string | null;
  classes_logged?: number | null;
  stripes?: number | null;
  notes?: string | null;
}

export interface SeedResponse {
  seeded: number;
  existing: number;
  skipped: boolean;
}

/** POST evidence / POST signoff both echo the slot's recomputed state. */
export interface SlotStateResponse extends SlotState {
  id: number;
  slot_id: number;
}

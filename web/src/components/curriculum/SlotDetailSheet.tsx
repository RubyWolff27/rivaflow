import { useState } from 'react';
import { X } from 'lucide-react';
import type {
  CurriculumSlot,
  EvidencePayload,
  GameTag,
  PartnerRankBand,
  PartnerSize,
  SlotDeclaration,
} from '../../types/curriculum';
import StatusChip from './StatusChip';
import { STATUS_META, sequenceText } from './constants';

interface SlotDetailSheetProps {
  slot: CurriculumSlot;
  onClose: () => void;
  onLogEvidence: (slotId: number, payload: EvidencePayload) => Promise<void>;
  onUpdateSlot: (slotId: number, payload: SlotDeclaration) => Promise<void>;
}

const RANK_BANDS: PartnerRankBand[] = ['lower', 'same', 'higher'];
const SIZES: PartnerSize[] = ['smaller', 'similar', 'bigger'];
const GAME_TAGS: GameTag[] = ['a-game', 'b-game', 'syllabus-only'];

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span className="text-xs" style={{ color: 'var(--muted)' }}>{label}</span>
      <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{value}</span>
    </div>
  );
}

/**
 * The evidence section shows counters, not rows: the API derives a slot's state
 * and returns no per-evidence history, so a list would have to be invented.
 */
export default function SlotDetailSheet({
  slot,
  onClose,
  onLogEvidence,
  onUpdateSlot,
}: SlotDetailSheetProps) {
  const [busy, setBusy] = useState(false);
  const [livePanel, setLivePanel] = useState(false);
  const [rankBand, setRankBand] = useState<PartnerRankBand>('same');
  const [size, setSize] = useState<PartnerSize>('similar');
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<SlotDeclaration>({
    seq_entry: slot.seq_entry ?? '',
    seq_position: slot.seq_position ?? '',
    seq_finish: slot.seq_finish ?? '',
    game_tag: slot.game_tag ?? 'syllabus-only',
  });

  const logDrilled = async () => {
    setBusy(true);
    try {
      await onLogEvidence(slot.id, { kind: 'drilled' });
    } finally {
      setBusy(false);
    }
  };

  const logLive = async () => {
    setBusy(true);
    try {
      await onLogEvidence(slot.id, {
        kind: 'live',
        partner_rank_band: rankBand,
        partner_size: size,
      });
      setLivePanel(false);
    } finally {
      setBusy(false);
    }
  };

  const saveEdit = async () => {
    setBusy(true);
    try {
      await onUpdateSlot(slot.id, draft);
      setEditing(false);
    } finally {
      setBusy(false);
    }
  };

  const sequence = sequenceText(slot);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
      role="dialog"
      aria-modal="true"
      aria-label="Slot detail"
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-lg max-h-[85vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl p-4"
        style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              {slot.requirement_label ?? slot.requirement_key} · #{slot.slot_index}
            </p>
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
              {sequence || 'Not declared yet'}
            </h3>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" style={{ color: 'var(--muted)' }}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <StatusChip status={slot.status} stalenessDays={slot.staleness_days} />
          {slot.game_tag && (
            <span className="text-[11px] px-2 py-0.5 rounded-full" style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}>
              {slot.game_tag}
            </span>
          )}
          {slot.is_draft && (
            <span className="text-[11px] px-2 py-0.5 rounded-full" style={{ color: 'var(--muted)', border: '1px dashed var(--border)' }}>
              draft — review me
            </span>
          )}
        </div>

        <p className="text-[11px] mb-3" style={{ color: 'var(--muted)' }}>
          {STATUS_META[slot.status]?.rule}
        </p>

        {slot.tension_note && (
          <p className="text-xs mb-3 p-2 rounded-lg" style={{ color: 'var(--muted)', backgroundColor: 'var(--surfaceElev)' }}>
            Tension: {slot.tension_note}
          </p>
        )}
        {slot.blocker_note && (
          <p className="text-xs mb-3 p-2 rounded-lg" style={{ color: 'var(--muted)', backgroundColor: 'var(--surfaceElev)' }}>
            Blocker: {slot.blocker_note}
          </p>
        )}

        <div className="rounded-xl p-3 mb-3" style={{ backgroundColor: 'var(--surfaceElev)' }}>
          <p className="text-xs font-semibold mb-1" style={{ color: 'var(--text)' }}>Evidence</p>
          <Row label="Distinct sessions" value={String(slot.sessions)} />
          <Row label="Drilled entries" value={String(slot.drilled_entries)} />
          <Row label="Live occasions" value={String(slot.live_occasions)} />
          <Row label="Distinct live partners" value={String(slot.live_partners)} />
          <Row label="Span" value={slot.span_days ? `${slot.span_days} days` : '—'} />
          <Row label="Last evidence" value={slot.last_evidence_at ?? 'none yet'} />
          {slot.weak_evidence && (
            <p className="text-[11px] mt-2" style={{ color: 'var(--muted)' }}>
              Live evidence only vs smaller and lower-ranked partners — strength may be
              doing the work.
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          <button type="button" className="btn-secondary text-sm" onClick={logDrilled} disabled={busy}>
            Log drilled
          </button>
          <button
            type="button"
            className="btn-secondary text-sm"
            onClick={() => setLivePanel((v) => !v)}
            disabled={busy}
          >
            Log live
          </button>
          <button
            type="button"
            className="btn-secondary text-sm"
            onClick={() => setEditing((v) => !v)}
            disabled={busy}
          >
            Edit sequence
          </button>
        </div>

        {livePanel && (
          <div className="rounded-xl p-3 mb-3 space-y-2" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              Who did it land on? Rank and size are what keep the live rung honest.
            </p>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Partner rank
              <select
                className="input mt-1 w-full text-sm"
                aria-label="Partner rank band"
                value={rankBand}
                onChange={(e) => setRankBand(e.target.value as PartnerRankBand)}
              >
                {RANK_BANDS.map((b) => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Partner size
              <select
                className="input mt-1 w-full text-sm"
                aria-label="Partner size"
                value={size}
                onChange={(e) => setSize(e.target.value as PartnerSize)}
              >
                {SIZES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>
            <button type="button" className="btn-primary text-sm" onClick={logLive} disabled={busy}>
              Save live evidence
            </button>
          </div>
        )}

        {editing && (
          <div className="rounded-xl p-3 space-y-2" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Entry / grip
              <input
                className="input mt-1 w-full text-sm"
                aria-label="Sequence entry"
                value={draft.seq_entry ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, seq_entry: e.target.value }))}
              />
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Position / action
              <input
                className="input mt-1 w-full text-sm"
                aria-label="Sequence position"
                value={draft.seq_position ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, seq_position: e.target.value }))}
              />
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Terminal finish
              <input
                className="input mt-1 w-full text-sm"
                aria-label="Sequence finish"
                value={draft.seq_finish ?? ''}
                onChange={(e) => setDraft((d) => ({ ...d, seq_finish: e.target.value }))}
              />
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Game tag
              <select
                className="input mt-1 w-full text-sm"
                aria-label="Game tag"
                value={draft.game_tag ?? 'syllabus-only'}
                onChange={(e) => setDraft((d) => ({ ...d, game_tag: e.target.value as GameTag }))}
              >
                {GAME_TAGS.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <button type="button" className="btn-primary text-sm" onClick={saveEdit} disabled={busy}>
              Save sequence
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

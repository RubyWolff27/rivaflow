import { useState } from 'react';
import type {
  ExportResponse,
  ExportSlot,
  MetaPayload,
  SignoffPayload,
  SignoffVerdict,
} from '../../types/curriculum';
import HardGatesStrip from './HardGatesStrip';
import { sequenceText } from './constants';

interface CoachViewProps {
  data: ExportResponse;
  onSaveGates: (payload: MetaPayload) => Promise<void>;
  onSignoff: (slotId: number, payload: SignoffPayload) => Promise<void>;
}

const VERDICTS: { key: SignoffVerdict; label: string }[] = [
  { key: 'verified', label: 'Verified' },
  { key: 'not-yet', label: 'Not yet' },
  { key: 'show-me', label: 'Show me on the mat' },
];

const BUCKETS: { key: 'not_yet' | 'in_progress' | 'verified'; heading: string; blurb: string }[] = [
  { key: 'not_yet', heading: 'Not there yet', blurb: 'Nothing logged, or a coach has already said not yet.' },
  { key: 'in_progress', heading: 'Working on it', blurb: 'Logged, unverified.' },
  { key: 'verified', heading: 'Signed off', blurb: 'A coach put their name to it.' },
];

/**
 * The coach-facing export, rendered in the order the API sends it: gaps first.
 * Deliberately carries no percentage, ratio, or completion count — the council
 * ruled a score invites exactly the reading this page must not invite. Plain
 * lists only.
 */
export default function CoachView({ data, onSaveGates, onSignoff }: CoachViewProps) {
  const [openSlot, setOpenSlot] = useState<number | null>(null);
  const [verdict, setVerdict] = useState<SignoffVerdict>('verified');
  const [coachName, setCoachName] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (slotId: number) => {
    if (!coachName.trim()) return;
    setBusy(true);
    try {
      await onSignoff(slotId, { verdict, coach_name: coachName.trim(), note: note.trim() || null });
      setOpenSlot(null);
      setNote('');
    } finally {
      setBusy(false);
    }
  };

  const renderSlot = (slot: ExportSlot, bucket: string) => {
    const sequence = sequenceText(slot.sequence);
    const isOpen = openSlot === slot.id;
    return (
      <li key={slot.id} className="py-2" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs" style={{ color: sequence ? 'var(--text)' : 'var(--muted)' }}>
              {sequence || `${slot.requirement_label ?? slot.requirement_key} — not declared`}
            </p>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
              {slot.requirement_label ?? slot.requirement_key}
              {bucket === 'verified' && (
                <>
                  {' · '}
                  {slot.signoff_coach_name
                    ? `signed by ${slot.signoff_coach_name}${slot.signoff_at ? ` on ${slot.signoff_at}` : ''}`
                    : 'signed off — the export does not carry the coach name or date'}
                </>
              )}
              {slot.signoff_verdict === 'show-me' && ' · coach asked to see it on the mat'}
              {slot.signoff_verdict === 'not-yet' && ' · coach said not yet'}
              {slot.weak_evidence && ' · live work only vs smaller, lower-ranked partners'}
            </p>
            {slot.blocker_note && (
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--muted)' }}>
                Blocker: {slot.blocker_note}
              </p>
            )}
          </div>
          <button
            type="button"
            className="text-[11px] px-2 py-1 rounded-lg whitespace-nowrap"
            style={{ color: 'var(--muted)', border: '1px solid var(--border)' }}
            onClick={() => setOpenSlot(isOpen ? null : slot.id)}
          >
            Record coach verdict
          </button>
        </div>

        {isOpen && (
          <div className="mt-2 rounded-xl p-3 space-y-2" style={{ backgroundColor: 'var(--surfaceElev)' }}>
            <p className="text-[11px]" style={{ color: 'var(--muted)' }}>
              Recorded once, attributed, and never editable. A changed mind is a new record.
            </p>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Verdict
              <select
                className="input mt-1 w-full text-sm"
                aria-label="Verdict"
                value={verdict}
                onChange={(e) => setVerdict(e.target.value as SignoffVerdict)}
              >
                {VERDICTS.map((v) => (
                  <option key={v.key} value={v.key}>{v.label}</option>
                ))}
              </select>
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Coach name
              <input
                className="input mt-1 w-full text-sm"
                aria-label="Coach name"
                value={coachName}
                onChange={(e) => setCoachName(e.target.value)}
              />
            </label>
            <label className="block text-xs" style={{ color: 'var(--muted)' }}>
              Note (optional)
              <input
                className="input mt-1 w-full text-sm"
                aria-label="Sign-off note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </label>
            <button
              type="button"
              className="btn-primary text-sm"
              onClick={() => submit(slot.id)}
              disabled={busy || !coachName.trim()}
            >
              Record verdict
            </button>
          </div>
        )}
      </li>
    );
  };

  return (
    <div className="space-y-4" data-testid="coach-view">
      <HardGatesStrip gates={data.hard_gates} onSave={onSaveGates} />

      <p className="text-xs p-3 rounded-xl" style={{ color: 'var(--muted)', backgroundColor: 'var(--surfaceElev)' }}>
        {data.disclaimer || 'Promotions are at the instructor’s discretion — this log has no authority over grading.'}
      </p>

      <p className="text-xs" style={{ color: 'var(--muted)' }}>
        Summary for {data.generated_on}. It opens with what is missing, on purpose.
      </p>

      {data.blocks.map((block) => (
        <div
          key={block.block}
          className="rounded-2xl p-3"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>
            {block.label ?? block.block}
          </h3>
          {BUCKETS.map(({ key, heading, blurb }) => {
            const slots = block[key];
            if (!slots || slots.length === 0) return null;
            return (
              <div key={key} className="mb-3 last:mb-0">
                <p className="text-[11px] font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                  {heading}
                </p>
                <p className="text-[11px] mb-1" style={{ color: 'var(--muted)' }}>{blurb}</p>
                <ul>{slots.map((slot) => renderSlot(slot, key))}</ul>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

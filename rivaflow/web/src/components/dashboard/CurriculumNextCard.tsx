import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Award, ChevronRight } from 'lucide-react';
import { curriculumApi } from '../../api/client';
import { logger } from '../../utils/logger';
import type { CurriculumSlot } from '../../types/curriculum';

/** Status ladder order — the "next slot to work" is the least-progressed declared one. */
const STATUS_ORDER = ['not-started', 'drilled', 'grooved', 'live'];

/**
 * One-liner Home card (Wave 4 Home item 4): the next purple-belt slot worth
 * working, with the honest status word. Hidden entirely when the slate is
 * empty or the fetch fails — never a fabricated prompt.
 */
export default function CurriculumNextCard() {
  const [slot, setSlot] = useState<CurriculumSlot | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await curriculumApi.slots();
        const slots = (res.data?.slots ?? []) as CurriculumSlot[];
        if (!alive || slots.length === 0) return;
        setTotal(slots.length);
        const declared = slots.filter((s) => s.declared && !s.is_draft);
        const pool = declared.length > 0 ? declared : slots;
        const next = [...pool].sort(
          (a, b) =>
            STATUS_ORDER.indexOf(a.status ?? 'not-started') -
            STATUS_ORDER.indexOf(b.status ?? 'not-started')
        )[0];
        setSlot(next ?? null);
      } catch (err) {
        logger.debug('Curriculum next-slot card unavailable', err);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (!slot) return null;

  const sequence = [slot.seq_entry, slot.seq_position, slot.seq_finish]
    .filter(Boolean)
    .join(' → ');

  return (
    <Link
      to="/curriculum"
      className="flex items-center justify-between gap-3 rounded-[14px] p-4 transition-opacity hover:opacity-90"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-3 min-w-0">
        <Award className="w-5 h-5 shrink-0" style={{ color: 'var(--accent)' }} />
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
            Purple Belt — next up ({total} slots)
          </p>
          <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>
            {sequence || slot.requirement_label || 'Open your slate'}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span
          className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase"
          style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}
        >
          {slot.status ?? 'not-started'}
        </span>
        <ChevronRight className="w-4 h-4" style={{ color: 'var(--muted)' }} />
      </div>
    </Link>
  );
}

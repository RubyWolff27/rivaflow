import type { SlotStatus } from '../../types/curriculum';
import { STALE_DAYS, STATUS_META, stalenessOpacity } from './constants';

interface StatusChipProps {
  status: SlotStatus;
  /** Days since the last evidence of any kind. Dims the chip; never changes it. */
  stalenessDays?: number | null;
}

/**
 * The status chip and the staleness treatment are deliberately separate: age
 * only ever fades the chip, so a slot that went quiet still reads as the rung
 * it earned.
 */
export default function StatusChip({ status, stalenessDays }: StatusChipProps) {
  const meta = STATUS_META[status] ?? STATUS_META['not-started'];
  const opacity = stalenessOpacity(stalenessDays);
  const stale = opacity < 1;

  const title = stale
    ? `${meta.label} — ${meta.rule} Last touched ${stalenessDays} days ago; the rung stands, the chip is just dimmed.`
    : `${meta.label} — ${meta.rule}`;

  return (
    <span
      data-testid={`status-chip-${status}`}
      data-status={status}
      data-stale={stale ? 'true' : 'false'}
      title={title}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium whitespace-nowrap"
      style={{
        color: meta.color,
        backgroundColor: meta.background,
        border: meta.border,
        opacity,
      }}
    >
      {meta.label}
      {stale && (
        <span aria-hidden="true" title={`Last touched ${stalenessDays} days ago`}>
          ·
        </span>
      )}
      {stale && (
        <span className="sr-only">
          {` last touched ${stalenessDays} days ago (over ${STALE_DAYS})`}
        </span>
      )}
    </span>
  );
}

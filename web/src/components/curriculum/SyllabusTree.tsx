import { useMemo, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, Scale } from 'lucide-react';
import type { BlockSummary, CurriculumSlot } from '../../types/curriculum';
import StatusChip from './StatusChip';
import { sequenceText } from './constants';

interface SyllabusTreeProps {
  slots: CurriculumSlot[];
  blocks: BlockSummary[];
  onOpenSlot: (slot: CurriculumSlot) => void;
}

interface RequirementGroup {
  key: string;
  label: string;
  slots: CurriculumSlot[];
}

interface BlockGroup {
  key: string;
  label: string;
  slotCount: number;
  requirements: RequirementGroup[];
}

/** block → requirement → slots, in the order the summary lists the blocks. */
function groupSlots(slots: CurriculumSlot[], blocks: BlockSummary[]): BlockGroup[] {
  const order = blocks.map((b) => b.block);
  const labels = new Map(blocks.map((b) => [b.block, b.label ?? b.block]));
  const byBlock = new Map<string, Map<string, RequirementGroup>>();

  for (const slot of slots) {
    if (!byBlock.has(slot.block)) byBlock.set(slot.block, new Map());
    const reqs = byBlock.get(slot.block)!;
    if (!reqs.has(slot.requirement_key)) {
      reqs.set(slot.requirement_key, {
        key: slot.requirement_key,
        label: slot.requirement_label ?? slot.requirement_key,
        slots: [],
      });
    }
    reqs.get(slot.requirement_key)!.slots.push(slot);
  }

  const keys = [...byBlock.keys()].sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });

  return keys.map((key) => {
    const reqs = [...byBlock.get(key)!.values()];
    return {
      key,
      label: labels.get(key) ?? key,
      slotCount: reqs.reduce((n, r) => n + r.slots.length, 0),
      requirements: reqs,
    };
  });
}

export default function SyllabusTree({ slots, blocks, onOpenSlot }: SyllabusTreeProps) {
  const groups = useMemo(() => groupSlots(slots, blocks), [slots, blocks]);
  const [openBlocks, setOpenBlocks] = useState<Record<string, boolean>>(() =>
    groups.length ? { [groups[0].key]: true } : {},
  );
  const [openReqs, setOpenReqs] = useState<Record<string, boolean>>({});

  const toggleBlock = (key: string) =>
    setOpenBlocks((s) => ({ ...s, [key]: !s[key] }));
  const toggleReq = (key: string) => setOpenReqs((s) => ({ ...s, [key]: !s[key] }));

  return (
    <div className="space-y-2" data-testid="syllabus-tree">
      <p className="text-xs" style={{ color: 'var(--muted)' }}>
        Block → requirement → declared sequence. Counts are raw: declared slots out of the
        slots the syllabus asks for.
      </p>

      {groups.map((group) => {
        const declared = group.requirements.reduce(
          (n, r) => n + r.slots.filter((s) => s.declared).length,
          0,
        );
        const blockOpen = !!openBlocks[group.key];
        return (
          <div
            key={group.key}
            className="rounded-2xl overflow-hidden"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
          >
            <button
              type="button"
              onClick={() => toggleBlock(group.key)}
              aria-expanded={blockOpen}
              className="w-full flex items-center justify-between gap-2 px-3 py-3 text-left"
            >
              <span className="flex items-center gap-2 min-w-0">
                {blockOpen ? (
                  <ChevronDown className="w-4 h-4 shrink-0" style={{ color: 'var(--muted)' }} />
                ) : (
                  <ChevronRight className="w-4 h-4 shrink-0" style={{ color: 'var(--muted)' }} />
                )}
                <span className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
                  {group.label}
                </span>
              </span>
              <span className="text-[11px] whitespace-nowrap" style={{ color: 'var(--muted)' }}>
                {declared} of {group.slotCount} declared
              </span>
            </button>

            {blockOpen && (
              <div style={{ borderTop: '1px solid var(--border)' }}>
                {group.requirements.map((req) => {
                  const reqOpen = !!openReqs[req.key];
                  const reqDeclared = req.slots.filter((s) => s.declared).length;
                  return (
                    <div key={req.key} style={{ borderBottom: '1px solid var(--border)' }}>
                      <button
                        type="button"
                        onClick={() => toggleReq(req.key)}
                        aria-expanded={reqOpen}
                        className="w-full flex items-center justify-between gap-2 pl-8 pr-3 py-2.5 text-left"
                      >
                        <span className="flex items-center gap-2 min-w-0">
                          {reqOpen ? (
                            <ChevronDown className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--muted)' }} />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--muted)' }} />
                          )}
                          <span className="text-xs truncate" style={{ color: 'var(--text)' }}>
                            {req.label}
                          </span>
                        </span>
                        <span className="text-[11px] whitespace-nowrap" style={{ color: 'var(--muted)' }}>
                          {reqDeclared} of {req.slots.length}
                        </span>
                      </button>

                      {reqOpen && (
                        <ul>
                          {req.slots.map((slot) => {
                            const sequence = sequenceText(slot);
                            return (
                              <li key={slot.id} style={{ borderTop: '1px solid var(--border)' }}>
                                <button
                                  type="button"
                                  data-testid={`slot-row-${slot.id}`}
                                  onClick={() => onOpenSlot(slot)}
                                  className="w-full flex items-start justify-between gap-2 pl-12 pr-3 py-2.5 text-left"
                                  style={{
                                    backgroundColor: slot.is_draft ? 'var(--surfaceElev)' : 'transparent',
                                  }}
                                >
                                  <span className="min-w-0">
                                    <span
                                      className="block text-xs"
                                      style={{ color: sequence ? 'var(--text)' : 'var(--muted)' }}
                                    >
                                      {sequence || `Slot ${slot.slot_index} — not declared yet`}
                                    </span>
                                    <span className="flex items-center gap-2 mt-1">
                                      {slot.is_draft && (
                                        <span
                                          className="text-[10px] px-1.5 py-0.5 rounded"
                                          style={{ color: 'var(--muted)', border: '1px dashed var(--border)' }}
                                        >
                                          draft — review me
                                        </span>
                                      )}
                                      {slot.weak_evidence && (
                                        <span
                                          title="Live evidence only vs smaller/lower-ranked partners"
                                          aria-label="Live evidence only vs smaller/lower-ranked partners"
                                          data-testid={`weak-evidence-${slot.id}`}
                                        >
                                          <Scale className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                                        </span>
                                      )}
                                      {slot.tension_note && (
                                        <span
                                          title={slot.tension_note}
                                          aria-label={`Tension: ${slot.tension_note}`}
                                          data-testid={`tension-note-${slot.id}`}
                                        >
                                          <AlertTriangle className="w-3.5 h-3.5" style={{ color: 'var(--muted)' }} />
                                        </span>
                                      )}
                                    </span>
                                  </span>
                                  <StatusChip status={slot.status} stalenessDays={slot.staleness_days} />
                                </button>
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

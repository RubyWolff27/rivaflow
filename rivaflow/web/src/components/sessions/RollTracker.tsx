import { useState } from 'react';
import { Plus, X, Search, ToggleLeft, ToggleRight } from 'lucide-react';
import type { Friend, Movement } from '../../types';
import type { RollEntry } from './sessionTypes';
import IntensityChips from '../ui/IntensityChips';

interface RollTrackerProps {
  detailedMode: boolean;
  onToggleMode: () => void;
  rolls: RollEntry[];
  partners: Friend[];
  simpleData: {
    rolls: number;
    submissions_for: number;
    submissions_against: number;
    partners: string;
  };
  onSimpleChange: (field: string, value: number | string) => void;
  submissionSearchFor: Record<number, string>;
  submissionSearchAgainst: Record<number, string>;
  onSubmissionSearchForChange: (index: number, value: string) => void;
  onSubmissionSearchAgainstChange: (index: number, value: string) => void;
  filterSubmissions: (search: string) => Movement[];
  onAddRoll: () => void;
  onRemoveRoll: (index: number) => void;
  onRollChange: (index: number, field: keyof RollEntry, value: RollEntry[keyof RollEntry]) => void;
  onToggleSubmission: (rollIndex: number, movementId: number, type: 'for' | 'against') => void;
  showPartners?: boolean;
  topPartners?: Friend[];
  selectedPartnerIds?: Set<number>;
  onTogglePartner?: (partnerId: number) => void;
}

/** Autocomplete partner input with pills — replaces dumb text field in simple mode */
function PartnerAutocomplete({
  partners,
  topPartners,
  selectedPartnerIds,
  onTogglePartner,
  value,
  onChange,
}: {
  partners: Friend[];
  topPartners: Friend[];
  selectedPartnerIds?: Set<number>;
  onTogglePartner?: (id: number) => void;
  value: string;
  onChange: (val: string) => void;
}) {
  const [input, setInput] = useState('');

  // Parse existing comma-separated value into pill array
  const pills = value ? value.split(',').map(p => p.trim()).filter(Boolean) : [];

  const addPill = (name: string) => {
    const trimmed = name.trim();
    if (!trimmed || pills.includes(trimmed)) return;
    const next = [...pills, trimmed].join(', ');
    onChange(next);
    setInput('');
  };

  const removePill = (name: string) => {
    const next = pills.filter(p => p !== name).join(', ');
    onChange(next);
  };

  // Filter suggestions from all partners
  const query = input.trim().toLowerCase();
  const suggestions = query.length >= 1
    ? partners
        .filter(p => p.name && p.name.toLowerCase().includes(query) && !pills.includes(p.name))
        .slice(0, 6)
    : [];

  return (
    <div className="relative">
      <label className="label">Partners</label>
      {/* Quick-select pills for top partners */}
      {topPartners.length > 0 && selectedPartnerIds && onTogglePartner && (
        <div className="flex flex-wrap gap-2 mb-2">
          {topPartners.map((partner) => {
            const selected = selectedPartnerIds.has(partner.id);
            return (
              <button
                key={partner.id}
                type="button"
                onClick={() => onTogglePartner(partner.id)}
                className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                style={{
                  backgroundColor: selected ? 'var(--accent)' : 'var(--surfaceElev)',
                  color: selected ? '#FFFFFF' : 'var(--text)',
                  border: selected ? 'none' : '1px solid var(--border)',
                }}
              >
                {partner.name}
              </button>
            );
          })}
        </div>
      )}
      {/* Typed partner pills */}
      {pills.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {pills.map((name) => (
            <span
              key={name}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
              style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: '#3B82F6' }}
            >
              {name}
              <button
                type="button"
                onClick={() => removePill(name)}
                className="ml-0.5 hover:opacity-70"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
      {/* Autocomplete input */}
      <input
        type="text"
        className="input text-sm"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
            e.preventDefault();
            addPill(input.replace(/,+$/, ''));
          }
        }}
        onBlur={() => {
          setTimeout(() => {
            if (input.trim()) {
              addPill(input.replace(/,+$/, ''));
            }
          }, 200);
        }}
        placeholder="Type to search partners..."
      />
      {/* Suggestions dropdown */}
      {suggestions.length > 0 && (
        <div
          className="absolute left-0 right-0 mt-1 rounded-lg overflow-hidden shadow-lg z-10"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          {suggestions.map((friend) => (
            <button
              key={friend.id}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--surfaceElev)] transition-colors"
              onMouseDown={(e) => {
                e.preventDefault();
                addPill(friend.name);
              }}
            >
              <span className="font-medium text-[var(--text)]">{friend.name}</span>
              {friend.belt_rank && (
                <span className="text-xs text-[var(--muted)] ml-1.5">
                  ({friend.belt_rank} belt)
                </span>
              )}
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-[var(--muted)] mt-1">Type to search friends, or enter any name and press Enter</p>
    </div>
  );
}

export default function RollTracker({
  detailedMode,
  onToggleMode,
  rolls,
  partners,
  simpleData,
  onSimpleChange,
  submissionSearchFor,
  submissionSearchAgainst,
  onSubmissionSearchForChange,
  onSubmissionSearchAgainstChange,
  filterSubmissions,
  onAddRoll,
  onRemoveRoll,
  onRollChange,
  onToggleSubmission,
  showPartners = true,
  topPartners = [],
  selectedPartnerIds,
  onTogglePartner,
}: RollTrackerProps) {
  // Build datalist options from partner names
  const partnerNames = partners.map(p => p.name).filter(Boolean);

  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-base">Rolls & Submissions</h3>
          <button
            type="button"
            onClick={onToggleMode}
            className="flex items-center gap-2 text-sm text-[var(--accent)] hover:opacity-80"
          >
            {detailedMode ? (
              <>
                <ToggleRight className="w-5 h-5" />
                Detailed Mode
              </>
            ) : (
              <>
                <ToggleLeft className="w-5 h-5" />
                Simple Mode
              </>
            )}
          </button>
        </div>

        {!detailedMode ? (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label text-xs">Rolls</label>
              <input
                type="number"
                className="input"
                value={simpleData.rolls}
                onChange={(e) => onSimpleChange('rolls', parseInt(e.target.value))}
                min="0"
              />
            </div>
            <div>
              <label className="label text-xs">Subs+</label>
              <input
                type="number"
                className="input"
                value={simpleData.submissions_for}
                onChange={(e) => onSimpleChange('submissions_for', parseInt(e.target.value))}
                min="0"
              />
            </div>
            <div>
              <label className="label text-xs">Subs-</label>
              <input
                type="number"
                className="input"
                value={simpleData.submissions_against}
                onChange={(e) => onSimpleChange('submissions_against', parseInt(e.target.value))}
                min="0"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-[var(--muted)]">
              Track each roll with partner and submissions from glossary
            </p>

            {rolls.map((roll, index) => (
              <div key={index} className="border border-[var(--border)] rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold">Roll #{roll.roll_number}</h4>
                  <button
                    type="button"
                    onClick={() => onRemoveRoll(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <label className="label text-sm">Partner</label>
                  <input
                    type="text"
                    className="input"
                    value={roll.partner_name}
                    onChange={(e) => {
                      onRollChange(index, 'partner_name', e.target.value);
                      // Try to match to a known partner for the ID
                      const match = partners.find(
                        p => p.name.toLowerCase() === e.target.value.toLowerCase()
                      );
                      onRollChange(index, 'partner_id', match ? match.id : null);
                    }}
                    placeholder="Type partner name..."
                    list={`roll-partners-${index}`}
                  />
                  <datalist id={`roll-partners-${index}`}>
                    {partnerNames.map((name) => (
                      <option key={name} value={name} />
                    ))}
                  </datalist>
                </div>

                {/* Per-roll intensity */}
                <div>
                  <label className="label text-sm">Intensity</label>
                  <IntensityChips
                    value={0}
                    onChange={() => {}}
                    multi
                    selectedValues={roll.intensity || []}
                    onToggle={(val) => {
                      const current = roll.intensity || [];
                      const next = current.includes(val)
                        ? current.filter(v => v !== val)
                        : [...current, val];
                      onRollChange(index, 'intensity', next);
                    }}
                    size="sm"
                    showDescription={false}
                  />
                </div>

                <div>
                  <label className="label text-sm">Duration (mins)</label>
                  <input
                    type="number"
                    className="input"
                    value={roll.duration_mins}
                    onChange={(e) => onRollChange(index, 'duration_mins', parseInt(e.target.value))}
                    min="1"
                  />
                </div>

                <div>
                  <label className="label text-sm">Submissions You Got</label>
                  <div className="relative mb-2">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                    <input
                      type="text"
                      className="input pl-8 text-sm"
                      placeholder="Search submissions..."
                      value={submissionSearchFor[index] || ''}
                      onChange={(e) => onSubmissionSearchForChange(index, e.target.value)}
                    />
                  </div>
                  <div className="max-h-32 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1">
                    {(() => {
                      const filtered = filterSubmissions(submissionSearchFor[index] ?? '');
                      return filtered.length === 0
                        ? <p className="text-xs text-[var(--muted)] text-center py-2">No submissions found</p>
                        : filtered.map(movement => (
                          <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-[var(--surfaceElev)] p-1 rounded">
                            <input
                              type="checkbox"
                              checked={roll.submissions_for.includes(movement.id)}
                              onChange={() => onToggleSubmission(index, movement.id, 'for')}
                              className="w-4 h-4"
                            />
                            <span>{movement.name ?? 'Unknown'}</span>
                          </label>
                        ));
                    })()}
                  </div>
                </div>

                <div>
                  <label className="label text-sm">Submissions They Got</label>
                  <div className="relative mb-2">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                    <input
                      type="text"
                      className="input pl-8 text-sm"
                      placeholder="Search submissions..."
                      value={submissionSearchAgainst[index] || ''}
                      onChange={(e) => onSubmissionSearchAgainstChange(index, e.target.value)}
                    />
                  </div>
                  <div className="max-h-32 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1">
                    {(() => {
                      const filtered = filterSubmissions(submissionSearchAgainst[index] ?? '');
                      return filtered.length === 0
                        ? <p className="text-xs text-[var(--muted)] text-center py-2">No submissions found</p>
                        : filtered.map(movement => (
                          <label key={movement.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-[var(--surfaceElev)] p-1 rounded">
                            <input
                              type="checkbox"
                              checked={roll.submissions_against.includes(movement.id)}
                              onChange={() => onToggleSubmission(index, movement.id, 'against')}
                              className="w-4 h-4"
                            />
                            <span>{movement.name ?? 'Unknown'}</span>
                          </label>
                        ));
                    })()}
                  </div>
                </div>

                <div>
                  <label className="label text-sm">Notes (optional)</label>
                  <input
                    type="text"
                    className="input"
                    value={roll.notes}
                    onChange={(e) => onRollChange(index, 'notes', e.target.value)}
                    placeholder="How did this roll go?"
                  />
                </div>
              </div>
            ))}

            <button
              type="button"
              onClick={onAddRoll}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Roll
            </button>
          </div>
        )}
      </div>

      {!detailedMode && showPartners && (
        <PartnerAutocomplete
          partners={partners}
          topPartners={topPartners}
          selectedPartnerIds={selectedPartnerIds}
          onTogglePartner={onTogglePartner}
          value={simpleData.partners}
          onChange={(val) => onSimpleChange('partners', val)}
        />
      )}
    </>
  );
}

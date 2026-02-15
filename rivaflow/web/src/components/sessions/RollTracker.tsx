import { Plus, X, Search, ToggleLeft, ToggleRight } from 'lucide-react';
import type { Friend, Movement } from '../../types';
import type { RollEntry } from './sessionTypes';

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
  return (
    <>
      <div className="space-y-4 border-t border-[var(--border)] pt-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-lg">Roll Tracking</h3>
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
          <>
            <div>
              <label className="label">Rolls</label>
              <input
                type="number"
                className="input"
                value={simpleData.rolls}
                onChange={(e) => onSimpleChange('rolls', parseInt(e.target.value))}
                min="0"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Submissions For</label>
                <input
                  type="number"
                  className="input"
                  value={simpleData.submissions_for}
                  onChange={(e) => onSimpleChange('submissions_for', parseInt(e.target.value))}
                  min="0"
                />
              </div>
              <div>
                <label className="label">Submissions Against</label>
                <input
                  type="number"
                  className="input"
                  value={simpleData.submissions_against}
                  onChange={(e) => onSimpleChange('submissions_against', parseInt(e.target.value))}
                  min="0"
                />
              </div>
            </div>
          </>
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
                  <select
                    className="input"
                    value={roll.partner_id || ''}
                    onChange={(e) => {
                      const partnerId = e.target.value ? parseInt(e.target.value) : null;
                      const partner = partners.find(p => p.id === partnerId);
                      onRollChange(index, 'partner_id', partnerId);
                      onRollChange(index, 'partner_name', partner ? partner.name : '');
                    }}
                  >
                    <option value="">Select partner...</option>
                    {partners.map(partner => (
                      <option key={partner.id} value={partner.id}>
                        {partner.name ?? 'Unknown'}
                        {partner.belt_rank && ` (${partner.belt_rank} belt)`}
                      </option>
                    ))}
                  </select>
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
        <div>
          <label className="label">Partners</label>
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
          <input
            type="text"
            className="input"
            value={simpleData.partners}
            onChange={(e) => onSimpleChange('partners', e.target.value)}
            placeholder={topPartners.length > 0 ? "Additional partners..." : "e.g., John, Sarah"}
          />
        </div>
      )}
    </>
  );
}

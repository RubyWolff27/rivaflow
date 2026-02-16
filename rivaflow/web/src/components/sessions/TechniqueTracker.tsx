import { Plus, X, Search } from 'lucide-react';
import type { Movement, MediaUrl } from '../../types';
import type { TechniqueEntry } from './sessionTypes';

interface TechniqueTrackerProps {
  techniques: TechniqueEntry[];
  techniqueSearch: Record<number, string>;
  onSearchChange: (index: number, value: string) => void;
  filterMovements: (search: string) => Movement[];
  onAdd: () => void;
  onRemove: (index: number) => void;
  onChange: (
    index: number,
    field: keyof TechniqueEntry,
    value: TechniqueEntry[keyof TechniqueEntry]
  ) => void;
  onSelectMovement: (
    index: number,
    movementId: number,
    movementName: string
  ) => void;
  onAddMediaUrl: (techIndex: number) => void;
  onRemoveMediaUrl: (techIndex: number, mediaIndex: number) => void;
  onMediaUrlChange: (
    techIndex: number,
    mediaIndex: number,
    field: keyof MediaUrl,
    value: string
  ) => void;
}

export default function TechniqueTracker({
  techniques,
  techniqueSearch,
  onSearchChange,
  filterMovements,
  onAdd,
  onRemove,
  onChange,
  onSelectMovement,
  onAddMediaUrl,
  onRemoveMediaUrl,
  onMediaUrlChange,
}: TechniqueTrackerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Technique of the Day</h3>
        <button
          type="button"
          onClick={onAdd}
          className="flex items-center gap-2 px-3 py-1 min-h-[44px] bg-[var(--accent)] text-white rounded-md hover:opacity-90 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Technique
        </button>
      </div>

      {techniques.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">
          Click "Add Technique" to track techniques you focused on today
        </p>
      ) : (
        <div className="space-y-4">
          {techniques.map((tech, index) => (
            <div
              key={index}
              className="border border-[var(--border)] rounded-lg p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">
                  Technique #{tech.technique_number}
                </h4>
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Movement Selection */}
              <div>
                <label className="label text-sm">Movement</label>
                <div className="relative mb-2">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
                  <input
                    type="text"
                    className="input pl-8 text-sm"
                    placeholder="Search movements..."
                    value={techniqueSearch[index] || ''}
                    onChange={(e) => onSearchChange(index, e.target.value)}
                  />
                </div>
                <div className="max-h-48 overflow-y-auto border border-[var(--border)] rounded p-2 space-y-1">
                  {(() => {
                    const filtered = filterMovements(
                      techniqueSearch[index] ?? ''
                    );
                    return filtered.length === 0 ? (
                      <p className="text-xs text-[var(--muted)] text-center py-2">
                        No movements found
                      </p>
                    ) : (
                      filtered.map((movement) => (
                        <button
                          key={movement.id}
                          type="button"
                          onClick={() =>
                            onSelectMovement(
                              index,
                              movement.id,
                              movement.name ?? ''
                            )
                          }
                          className={`w-full text-left px-2 py-2 min-h-[44px] rounded text-sm ${
                            tech.movement_id === movement.id
                              ? 'bg-[var(--accent)] text-white'
                              : 'hover:bg-[var(--surfaceElev)]'
                          }`}
                        >
                          <span className="font-medium">
                            {movement.name ?? 'Unknown'}
                          </span>
                          <span className="text-xs ml-2 opacity-75">
                            {movement.category ?? 'N/A'}
                            {movement.subcategory &&
                              ` - ${movement.subcategory}`}
                          </span>
                        </button>
                      ))
                    );
                  })()}
                </div>
                {tech.movement_id && (
                  <p className="text-sm text-[var(--muted)] mt-1">
                    Selected:{' '}
                    <span className="font-medium">{tech.movement_name}</span>
                  </p>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="label text-sm">Notes / Key Points</label>
                <textarea
                  className="input resize-none"
                  rows={3}
                  value={tech.notes}
                  onChange={(e) => onChange(index, 'notes', e.target.value)}
                  placeholder="What did you learn? Key details, insights, or observations..."
                />
              </div>

              {/* Media URLs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="label text-sm mb-0">Reference Media</label>
                  <button
                    type="button"
                    onClick={() => onAddMediaUrl(index)}
                    className="text-xs text-[var(--accent)] hover:opacity-80 flex items-center gap-1"
                  >
                    <Plus className="w-3 h-3" />
                    Add Link
                  </button>
                </div>
                {tech.media_urls.length === 0 ? (
                  <p className="text-xs text-[var(--muted)]">
                    No media links added
                  </p>
                ) : (
                  <div className="space-y-2">
                    {tech.media_urls.map((media, mediaIndex) => (
                      <div
                        key={mediaIndex}
                        className="border border-[var(--border)] rounded p-2 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <select
                            className="input-sm text-xs"
                            value={media.type}
                            onChange={(e) =>
                              onMediaUrlChange(
                                index,
                                mediaIndex,
                                'type',
                                e.target.value as 'video' | 'image'
                              )
                            }
                          >
                            <option value="video">Video</option>
                            <option value="image">Image</option>
                          </select>
                          <button
                            type="button"
                            onClick={() => onRemoveMediaUrl(index, mediaIndex)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                        <input
                          type="text"
                          className="input text-xs"
                          placeholder="URL (YouTube, Instagram, etc.)"
                          value={media.url}
                          onChange={(e) =>
                            onMediaUrlChange(
                              index,
                              mediaIndex,
                              'url',
                              e.target.value
                            )
                          }
                        />
                        <input
                          type="text"
                          className="input text-xs"
                          placeholder="Title (optional)"
                          value={media.title ?? ''}
                          onChange={(e) =>
                            onMediaUrlChange(
                              index,
                              mediaIndex,
                              'title',
                              e.target.value
                            )
                          }
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

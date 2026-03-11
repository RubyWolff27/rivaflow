export const CLASS_TYPES = [
  { value: 'gi', label: 'Gi', color: '#3B82F6', primary: true, bjj: true },
  { value: 'no-gi', label: 'No-Gi', color: '#8B5CF6', primary: true, bjj: true },
  { value: 'open-mat', label: 'Open Mat', color: '#F59E0B', primary: false, bjj: true },
  { value: 'competition', label: 'Competition', color: '#EF4444', primary: false, bjj: true },
  { value: 's&c', label: 'S&C', color: '#10B981', primary: false, bjj: false },
  { value: 'cardio', label: 'Cardio', color: '#06B6D4', primary: false, bjj: false },
  { value: 'mobility', label: 'Mobility', color: '#EC4899', primary: false, bjj: false },
  { value: 'drilling', label: 'Drilling', color: '#F97316', primary: false, bjj: true },
];

/** All types available as primary selection in multi mode */
const ALL_PRIMARY_TYPES = CLASS_TYPES;
/** BJJ-only secondary tags (shown when a BJJ type is selected) */
const BJJ_SECONDARY_TYPES = CLASS_TYPES.filter(t => !t.primary && t.bjj);

interface ClassTypeChipsProps {
  /** Single-select mode: primary class type value */
  value: string;
  /** Single-select mode: callback when primary changes */
  onChange: (value: string) => void;
  /** Filter to specific type values */
  types?: string[];
  size?: 'sm' | 'md';
  /** Enable multi-select mode with primary + secondary tags */
  multi?: boolean;
  /** Multi-select mode: selected secondary tags */
  selectedTags?: string[];
  /** Multi-select mode: toggle a secondary tag */
  onToggleTag?: (tag: string) => void;
}

export default function ClassTypeChips({
  value,
  onChange,
  types,
  size = 'md',
  multi = false,
  selectedTags = [],
  onToggleTag,
}: ClassTypeChipsProps) {
  if (!multi) {
    // Original single-select behavior
    const filtered = types
      ? CLASS_TYPES.filter(t => types.includes(t.value))
      : CLASS_TYPES;

    return (
      <div className="flex flex-wrap gap-2" role="group" aria-label="Class type">
        {filtered.map((type) => {
          const selected = value === type.value;
          return (
            <button
              key={type.value}
              type="button"
              onClick={() => onChange(type.value)}
              className={`rounded-full font-medium transition-all min-h-[44px] ${
                size === 'sm' ? 'px-3 py-2 text-xs' : 'px-4 py-2.5 text-sm'
              }`}
              style={{
                backgroundColor: selected ? type.color : 'var(--surfaceElev)',
                color: selected ? '#FFFFFF' : 'var(--text)',
                border: selected ? 'none' : '1px solid var(--border)',
              }}
              aria-pressed={selected}
            >
              {type.label}
            </button>
          );
        })}
      </div>
    );
  }

  // Multi-select mode: primary (single-select from all types) + secondary BJJ tags
  const selectedIsBjj = CLASS_TYPES.find(t => t.value === value)?.bjj ?? true;

  return (
    <div className="space-y-2">
      {/* Primary: all class types (required, single-select) */}
      <div className="flex flex-wrap gap-2" role="group" aria-label="Class type">
        {ALL_PRIMARY_TYPES.map((type) => {
          const selected = value === type.value;
          return (
            <button
              key={type.value}
              type="button"
              onClick={() => onChange(type.value)}
              className={`rounded-full font-medium transition-all min-h-[44px] ${
                size === 'sm' ? 'px-3 py-2 text-xs' : 'px-4 py-2.5 text-sm'
              }`}
              style={{
                backgroundColor: selected ? type.color : 'var(--surfaceElev)',
                color: selected ? '#FFFFFF' : 'var(--text)',
                border: selected ? 'none' : '1px solid var(--border)',
              }}
              aria-pressed={selected}
            >
              {type.label}
            </button>
          );
        })}
      </div>
      {/* Secondary BJJ tags: only shown when a BJJ type is selected */}
      {selectedIsBjj && (
        <div className="flex flex-wrap gap-2" role="group" aria-label="Additional class tags">
          {BJJ_SECONDARY_TYPES.filter(t => t.value !== value).map((type) => {
            const selected = selectedTags.includes(type.value);
            return (
              <button
                key={type.value}
                type="button"
                onClick={() => onToggleTag?.(type.value)}
                className={`rounded-full font-medium transition-all ${
                  size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
                }`}
                style={{
                  backgroundColor: selected ? type.color : 'var(--surfaceElev)',
                  color: selected ? '#FFFFFF' : 'var(--text)',
                  border: selected ? 'none' : '1px solid var(--border)',
                }}
                aria-pressed={selected}
              >
                {type.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

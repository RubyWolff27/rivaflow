const LEVELS = [
  { value: 1, label: 'Technical', color: '#10B981' },
  { value: 2, label: 'Flow', color: '#34D399' },
  { value: 3, label: 'Moderate', color: '#F59E0B' },
  { value: 4, label: 'Hard', color: '#F97316' },
  { value: 5, label: 'War', color: '#EF4444' },
];

const DESCRIPTIONS: Record<number, string> = {
  1: 'Drilling, positional work, or technique-focused',
  2: 'Flow rolling or light controlled sparring',
  3: 'Standard class with normal rolling',
  4: 'Tough rounds, competition-pace sparring',
  5: 'Comp simulation, shark tank, or max effort',
};

/** Map numeric intensity to its label name */
export function intensityLabel(value: number): string {
  return LEVELS.find(l => l.value === value)?.label ?? `${value}`;
}

/** Get all available intensity levels */
export { LEVELS as INTENSITY_LEVELS };

interface IntensityChipsProps {
  value: number;
  onChange: (value: number) => void;
  size?: 'sm' | 'md';
  showDescription?: boolean;
  /** Multi-select mode: value is ignored, use selectedValues/onToggle instead */
  multi?: boolean;
  selectedValues?: number[];
  onToggle?: (value: number) => void;
}

export default function IntensityChips({
  value,
  onChange,
  size = 'md',
  showDescription = true,
  multi = false,
  selectedValues = [],
  onToggle,
}: IntensityChipsProps) {
  return (
    <div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Intensity level">
        {LEVELS.map((level) => {
          const selected = multi
            ? selectedValues.includes(level.value)
            : value === level.value;
          return (
            <button
              key={level.value}
              type="button"
              onClick={() => {
                if (multi && onToggle) {
                  onToggle(level.value);
                } else {
                  onChange(level.value);
                }
              }}
              className={`rounded-full font-medium transition-all ${
                size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
              }`}
              style={{
                backgroundColor: selected ? level.color : 'var(--surfaceElev)',
                color: selected ? '#FFFFFF' : 'var(--text)',
                border: selected ? 'none' : '1px solid var(--border)',
              }}
              aria-label={`Intensity: ${level.label}`}
              aria-pressed={selected}
            >
              {level.label}
            </button>
          );
        })}
      </div>
      {showDescription && !multi && DESCRIPTIONS[value] && (
        <p className="text-xs mt-1.5" style={{ color: 'var(--muted)' }}>
          {DESCRIPTIONS[value]}
        </p>
      )}
      {showDescription && multi && selectedValues.length > 0 && (
        <p className="text-xs mt-1.5" style={{ color: 'var(--muted)' }}>
          {selectedValues.sort((a, b) => a - b).map(v => DESCRIPTIONS[v]).filter(Boolean).join(' · ')}
        </p>
      )}
    </div>
  );
}

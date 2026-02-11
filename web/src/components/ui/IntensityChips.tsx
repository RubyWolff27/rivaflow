const LEVELS = [
  { value: 1, label: 'Light', color: '#10B981' },
  { value: 2, label: 'Easy', color: '#34D399' },
  { value: 3, label: 'Moderate', color: '#F59E0B' },
  { value: 4, label: 'Hard', color: '#F97316' },
  { value: 5, label: 'War', color: '#EF4444' },
];

const DESCRIPTIONS: Record<number, string> = {
  1: 'Drilling, flow rolling, or active recovery',
  2: 'Technique-focused class with light sparring',
  3: 'Standard class with normal rolling',
  4: 'Tough rounds, competition-pace sparring',
  5: 'Comp simulation, shark tank, or max effort',
};

interface IntensityChipsProps {
  value: number;
  onChange: (value: number) => void;
  size?: 'sm' | 'md';
  showDescription?: boolean;
}

export default function IntensityChips({ value, onChange, size = 'md', showDescription = true }: IntensityChipsProps) {
  return (
    <div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Intensity level">
        {LEVELS.map((level) => {
          const selected = value === level.value;
          return (
            <button
              key={level.value}
              type="button"
              onClick={() => onChange(level.value)}
              className={`rounded-full font-medium transition-all ${
                size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
              }`}
              style={{
                backgroundColor: selected ? level.color : 'var(--surfaceElev)',
                color: selected ? '#FFFFFF' : 'var(--text)',
                border: selected ? 'none' : '1px solid var(--border)',
              }}
              aria-label={`Intensity level ${level.value} of 5: ${level.label}`}
              aria-pressed={selected}
            >
              {level.value} {level.label}
            </button>
          );
        })}
      </div>
      {showDescription && DESCRIPTIONS[value] && (
        <p className="text-xs mt-1.5" style={{ color: 'var(--muted)' }}>
          {DESCRIPTIONS[value]}
        </p>
      )}
    </div>
  );
}

const LEVELS = [
  { value: 1, label: '1 Light', color: '#10B981' },
  { value: 2, label: '2 Easy', color: '#34D399' },
  { value: 3, label: '3 Moderate', color: '#F59E0B' },
  { value: 4, label: '4 Hard', color: '#F97316' },
  { value: 5, label: '5 War', color: '#EF4444' },
];

interface IntensityChipsProps {
  value: number;
  onChange: (value: number) => void;
  size?: 'sm' | 'md';
}

export default function IntensityChips({ value, onChange, size = 'md' }: IntensityChipsProps) {
  return (
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
            {level.label}
          </button>
        );
      })}
    </div>
  );
}

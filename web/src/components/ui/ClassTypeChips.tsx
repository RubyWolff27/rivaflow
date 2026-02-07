const CLASS_TYPES = [
  { value: 'gi', label: 'Gi', color: '#3B82F6' },
  { value: 'no-gi', label: 'No-Gi', color: '#8B5CF6' },
  { value: 'open-mat', label: 'Open Mat', color: '#F59E0B' },
  { value: 'competition', label: 'Competition', color: '#EF4444' },
  { value: 's&c', label: 'S&C', color: '#10B981' },
  { value: 'cardio', label: 'Cardio', color: '#06B6D4' },
  { value: 'mobility', label: 'Mobility', color: '#EC4899' },
  { value: 'drilling', label: 'Drilling', color: '#F97316' },
];

interface ClassTypeChipsProps {
  value: string;
  onChange: (value: string) => void;
  types?: string[];
  size?: 'sm' | 'md';
}

export default function ClassTypeChips({ value, onChange, types, size = 'md' }: ClassTypeChipsProps) {
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
  );
}

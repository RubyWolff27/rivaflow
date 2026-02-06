import { useState } from 'react';
import { Filter } from 'lucide-react';

interface ActivityTypeFilterProps {
  selectedTypes: string[];
  onChange: (types: string[]) => void;
}

const ACTIVITY_TYPES = [
  { value: 'gi', label: 'Gi', color: '#3B82F6' },
  { value: 'no-gi', label: 'No-Gi', color: '#8B5CF6' },
  { value: 's&c', label: 'S&C', color: '#EF4444' },
  { value: 'drilling', label: 'Drilling', color: '#F59E0B' },
  { value: 'open-mat', label: 'Open Mat', color: '#10B981' },
  { value: 'competition', label: 'Competition', color: '#EC4899' },
];

export function ActivityTypeFilter({ selectedTypes, onChange }: ActivityTypeFilterProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleType = (type: string) => {
    if (selectedTypes.includes(type)) {
      onChange(selectedTypes.filter(t => t !== type));
    } else {
      onChange([...selectedTypes, type]);
    }
  };

  const clearAll = () => {
    onChange([]);
    setIsOpen(false);
  };

  const hasFilters = selectedTypes.length > 0;

  return (
    <div className="relative">
      {/* Filter Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        style={{
          backgroundColor: hasFilters ? 'var(--accent)' : 'var(--surfaceElev)',
          color: hasFilters ? '#FFFFFF' : 'var(--text)',
          border: hasFilters ? 'none' : '1px solid var(--border)',
        }}
      >
        <Filter className="w-4 h-4" />
        <span>Filter by Type</span>
        {hasFilters && (
          <span
            className="px-2 py-0.5 rounded-full text-xs font-semibold"
            style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}
          >
            {selectedTypes.length}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Menu */}
          <div
            className="absolute right-0 mt-2 w-64 rounded-[14px] shadow-lg z-50 p-3"
            style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
            }}
          >
            <div className="flex items-center justify-between mb-3 pb-2" style={{ borderBottom: '1px solid var(--border)' }}>
              <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
                Filter by Class Type
              </span>
              {hasFilters && (
                <button
                  onClick={clearAll}
                  className="text-xs font-medium transition-colors"
                  style={{ color: 'var(--accent)' }}
                >
                  Clear All
                </button>
              )}
            </div>

            <div className="space-y-2">
              {ACTIVITY_TYPES.map((type) => {
                const isSelected = selectedTypes.includes(type.value);
                return (
                  <button
                    key={type.value}
                    onClick={() => toggleType(type.value)}
                    className="w-full flex items-center justify-between p-2 rounded-lg transition-all text-left"
                    style={{
                      backgroundColor: isSelected ? 'var(--surfaceElev)' : 'transparent',
                      border: isSelected ? `1px solid ${type.color}` : '1px solid transparent',
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: type.color }}
                      />
                      <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                        {type.label}
                      </span>
                    </div>
                    {isSelected && (
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: type.color }}
                      >
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

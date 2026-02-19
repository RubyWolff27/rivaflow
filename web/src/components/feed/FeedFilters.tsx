import { useCallback, useMemo } from 'react';
import type { FeedItem } from '../../types';

interface FeedResponse {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

const SESSION_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'rest', label: 'Rest Days' },
  { key: 'comp', label: '\u{1F94B} Comp Prep' },
  { key: 'hard', label: '\u{1F525} Hard' },
  { key: 'technical', label: '\u{1F9E0} Technical' },
  { key: 'smashed', label: '\u{1F480} Smashed' },
];

export interface FeedFiltersProps {
  feed: FeedResponse | null;
  sessionFilter: string;
  onFilterChange: (filter: string) => void;
}

export default function FeedFilters({
  feed,
  sessionFilter,
  onFilterChange,
}: FeedFiltersProps) {
  const getFilterCount = useCallback((filterKey: string): number => {
    if (!feed) return 0;
    if (filterKey === 'all') return feed.items.length;
    if (filterKey === 'rest') return feed.items.filter(i => i.type === 'rest').length;
    return feed.items.filter(i => {
      if (i.type !== 'session') return false;
      const d = i.data ?? {};
      switch (filterKey) {
        case 'comp': return d.class_type === 'competition';
        case 'hard': return (d.intensity ?? 0) >= 4;
        case 'technical': return (d.intensity ?? 5) <= 2;
        case 'smashed': return (d.submissions_against ?? 0) > (d.submissions_for ?? 0) && (d.submissions_against ?? 0) > 0;
        default: return false;
      }
    }).length;
  }, [feed]);

  const filterButtons = useMemo(() => SESSION_FILTERS.map((f) => {
    const count = getFilterCount(f.key);
    const isActive = sessionFilter === f.key;
    const isDisabled = f.key !== 'all' && count === 0;
    return (
      <button
        key={f.key}
        onClick={() => !isDisabled && onFilterChange(f.key)}
        disabled={isDisabled}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        style={{
          backgroundColor: isActive ? 'var(--accent)' : 'var(--surfaceElev)',
          color: isActive ? '#FFFFFF' : 'var(--text)',
          border: isActive ? 'none' : '1px solid var(--border)',
        }}
      >
        {f.label}
        {f.key !== 'all' && (
          <span
            className="text-xs px-1.5 py-0.5 rounded-full font-semibold"
            style={{
              backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : 'var(--border)',
              color: isActive ? '#FFFFFF' : 'var(--muted)',
            }}
          >
            {count}
          </span>
        )}
      </button>
    );
  }), [sessionFilter, getFilterCount, onFilterChange]);

  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {filterButtons}
    </div>
  );
}

/** Check if a feed item matches the active session filter */
export function matchesSessionFilter(item: FeedItem, sessionFilter: string): boolean {
  if (sessionFilter === 'all') return true;
  if (sessionFilter === 'rest') return item.type === 'rest';
  // Non-rest filters only match sessions
  if (item.type !== 'session') return false;
  const d = item.data ?? {};
  switch (sessionFilter) {
    case 'comp':
      return d.class_type === 'competition';
    case 'hard':
      return (d.intensity ?? 0) >= 4;
    case 'technical':
      return (d.intensity ?? 5) <= 2;
    case 'smashed':
      return (d.submissions_against ?? 0) > (d.submissions_for ?? 0) && (d.submissions_against ?? 0) > 0;
    default:
      return true;
  }
}

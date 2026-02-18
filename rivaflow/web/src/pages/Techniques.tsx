import { useState, useEffect, useMemo, memo } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { techniquesApi } from '../api/client';
import { logger } from '../utils/logger';
import type { TrainedMovement } from '../types';
import { Book, AlertCircle, ArrowUp, ArrowDown } from 'lucide-react';
import { CardSkeleton } from '../components/ui';
import { useToast } from '../contexts/ToastContext';

type SortKey = 'name' | 'category' | 'last_trained_date' | 'train_count';
type SortDir = 'asc' | 'desc';

// Memoized technique row component
const TechniqueRow = memo(function TechniqueRow({ tech }: { tech: TrainedMovement }) {
  return (
    <tr className="border-b border-[var(--border)]">
      <td className="py-3 px-4 font-medium">{tech.name}</td>
      <td className="py-3 px-4 text-[var(--muted)]">
        {tech.category || '—'}
      </td>
      <td className="py-3 px-4 text-[var(--muted)]">
        {tech.last_trained_date
          ? new Date(tech.last_trained_date).toLocaleDateString()
          : 'Never'}
      </td>
      <td className="py-3 px-4 text-[var(--muted)]">
        {tech.train_count ?? 0}
      </td>
    </tr>
  );
});

function SortHeader({
  label,
  sortKey,
  currentSort,
  currentDir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentSort: SortKey;
  currentDir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const active = currentSort === sortKey;
  return (
    <th
      className="text-left py-3 px-4 cursor-pointer select-none hover:opacity-70"
      onClick={() => onSort(sortKey)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {active && (currentDir === 'asc' ? (
          <ArrowUp className="w-3 h-3" />
        ) : (
          <ArrowDown className="w-3 h-3" />
        ))}
      </span>
    </th>
  );
}

export default function Techniques() {
  usePageTitle('Techniques');
  const toast = useToast();
  const [techniques, setTechniques] = useState<TrainedMovement[]>([]);
  const [staleTechniques, setStaleTechniques] = useState<TrainedMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const [techRes, staleRes] = await Promise.all([
          techniquesApi.list(),
          techniquesApi.getStale(7),
        ]);
        if (!cancelled) {
          setTechniques(techRes.data.techniques || []);
          setStaleTechniques(staleRes.data || []);
        }
      } catch (error) {
        if (!cancelled) {
          logger.error('Error loading techniques:', error);
          toast.error('Failed to load techniques');
          setTechniques([]);
          setStaleTechniques([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const handleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(key);
      setSortDir(key === 'train_count' || key === 'last_trained_date' ? 'desc' : 'asc');
    }
  };

  const sorted = useMemo(() => {
    const list = [...techniques];
    list.sort((a, b) => {
      let cmp = 0;
      switch (sortBy) {
        case 'name':
          cmp = (a.name || '').localeCompare(b.name || '');
          break;
        case 'category':
          cmp = (a.category || '').localeCompare(b.category || '');
          break;
        case 'last_trained_date': {
          const da = a.last_trained_date || '';
          const db = b.last_trained_date || '';
          cmp = da.localeCompare(db);
          break;
        }
        case 'train_count':
          cmp = (a.train_count ?? 0) - (b.train_count ?? 0);
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [techniques, sortBy, sortDir]);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <CardSkeleton key={i} lines={2} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Book className="w-8 h-8 text-[var(--accent)]" />
        <h1 className="text-3xl font-bold">Techniques</h1>
      </div>

      {/* Stale Techniques Alert */}
      {staleTechniques.length > 0 && (
        <div className="card" style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}>
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h2 className="font-semibold mb-2">Stale Techniques (7+ days)</h2>
              <div className="flex flex-wrap gap-2">
                {staleTechniques.map((tech) => (
                  <span
                    key={tech.id}
                    className="px-2 py-1 rounded text-sm"
                    style={{ backgroundColor: 'rgba(234,179,8,0.1)', color: '#ca8a04' }}
                  >
                    {tech.name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Techniques List */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Trained Techniques ({techniques.length})</h2>
        {techniques.length === 0 ? (
          <p className="text-center text-[var(--muted)] py-8">
            No techniques tracked yet. Log a session with techniques to see them here,
            or add custom movements in the Glossary.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-[var(--border)]">
                <tr>
                  <SortHeader label="Name" sortKey="name" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                  <SortHeader label="Category" sortKey="category" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                  <SortHeader label="Last Trained" sortKey="last_trained_date" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                  <SortHeader label="Train Count" sortKey="train_count" currentSort={sortBy} currentDir={sortDir} onSort={handleSort} />
                </tr>
              </thead>
              <tbody>
                {sorted.map((tech) => (
                  <TechniqueRow key={tech.id} tech={tech} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

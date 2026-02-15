import { useState, useEffect, memo } from 'react';
import { techniquesApi } from '../api/client';
import { logger } from '../utils/logger';
import type { TrainedMovement } from '../types';
import { Book, AlertCircle } from 'lucide-react';
import { CardSkeleton } from '../components/ui';

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

export default function Techniques() {
  const [techniques, setTechniques] = useState<TrainedMovement[]>([]);
  const [staleTechniques, setStaleTechniques] = useState<TrainedMovement[]>([]);
  const [loading, setLoading] = useState(true);

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
              <h3 className="font-semibold mb-2">Stale Techniques (7+ days)</h3>
              <div className="flex flex-wrap gap-2">
                {staleTechniques.map((tech) => (
                  <span
                    key={tech.id}
                    className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm"
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
                  <th className="text-left py-3 px-4">Name</th>
                  <th className="text-left py-3 px-4">Category</th>
                  <th className="text-left py-3 px-4">Last Trained</th>
                  <th className="text-left py-3 px-4">Train Count</th>
                </tr>
              </thead>
              <tbody>
                {techniques.map((tech) => (
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

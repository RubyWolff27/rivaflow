import { useState, useEffect, memo, useCallback } from 'react';
import { techniquesApi } from '../api/client';
import type { Technique } from '../types';
import { Book, AlertCircle } from 'lucide-react';
import { CardSkeleton } from '../components/ui';

// Memoized technique row component
const TechniqueRow = memo(function TechniqueRow({ tech }: { tech: Technique }) {
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
    </tr>
  );
});

export default function Techniques() {
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [staleTechniques, setStaleTechniques] = useState<Technique[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTechnique, setNewTechnique] = useState({ name: '', category: '' });

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
          console.error('Error loading techniques:', error);
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

  const loadTechniques = async () => {
    setLoading(true);
    try {
      const [techRes, staleRes] = await Promise.all([
        techniquesApi.list(),
        techniquesApi.getStale(7),
      ]);
      // API returns {techniques: [], total: number} for list endpoint
      setTechniques(techRes.data.techniques || []);
      // API returns array directly for stale endpoint
      setStaleTechniques(staleRes.data || []);
    } catch (error) {
      console.error('Error loading techniques:', error);
      // Set empty arrays on error to prevent .map crashes
      setTechniques([]);
      setStaleTechniques([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await techniquesApi.create(newTechnique);
      setNewTechnique({ name: '', category: '' });
      setShowAddForm(false);
      await loadTechniques();
    } catch (error) {
      console.error('Error adding technique:', error);
    }
  }, [newTechnique]);

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
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Book className="w-8 h-8 text-[var(--accent)]" />
          <h1 className="text-3xl font-bold">Techniques</h1>
        </div>
        <button onClick={() => setShowAddForm(!showAddForm)} className="btn-primary">
          Add Technique
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <form onSubmit={handleAdd} className="card">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Technique Name</label>
              <input
                type="text"
                className="input"
                value={newTechnique.name}
                onChange={(e) => setNewTechnique({ ...newTechnique, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Category (optional)</label>
              <select
                className="input"
                value={newTechnique.category}
                onChange={(e) => setNewTechnique({ ...newTechnique, category: e.target.value })}
              >
                <option value="">Select category</option>
                <option value="guard">Guard</option>
                <option value="pass">Pass</option>
                <option value="submission">Submission</option>
                <option value="sweep">Sweep</option>
                <option value="takedown">Takedown</option>
                <option value="escape">Escape</option>
                <option value="position">Position</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button type="submit" className="btn-primary">Add</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Stale Techniques Alert */}
      {staleTechniques.length > 0 && (
        <div className="card bg-yellow-50 border-yellow-200">
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
        <h2 className="text-xl font-semibold mb-4">All Techniques ({techniques.length})</h2>
        {techniques.length === 0 ? (
          <p className="text-center text-[var(--muted)] py-8">
            No techniques tracked yet. Add your first technique above!
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-[var(--border)]">
                <tr>
                  <th className="text-left py-3 px-4">Name</th>
                  <th className="text-left py-3 px-4">Category</th>
                  <th className="text-left py-3 px-4">Last Trained</th>
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

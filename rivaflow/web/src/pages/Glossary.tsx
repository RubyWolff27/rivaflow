import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { glossaryApi } from '../api/client';
import type { Movement } from '../types';
import { Book, Search, Plus, Trash2, Award } from 'lucide-react';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import { CardSkeleton } from '../components/ui';

const CATEGORY_LABELS: Record<string, string> = {
  position: 'Positions',
  submission: 'Submissions',
  sweep: 'Sweeps',
  pass: 'Guard Passes',
  takedown: 'Takedowns',
  escape: 'Escapes',
  movement: 'Movements',
  concept: 'Concepts',
  defense: 'Defense',
};

const CATEGORY_COLORS: Record<string, string> = {
  position: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  submission: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  sweep: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  pass: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  takedown: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  escape: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  movement: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
  concept: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  defense: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300',
};

export default function Glossary() {
  const navigate = useNavigate();
  const [movements, setMovements] = useState<Movement[]>([]);
  const [filteredMovements, setFilteredMovements] = useState<Movement[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showGiOnly, setShowGiOnly] = useState(false);
  const [showNoGiOnly, setShowNoGiOnly] = useState(false);
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [movementToDelete, setMovementToDelete] = useState<number | null>(null);
  const toast = useToast();

  const [customForm, setCustomForm] = useState({
    name: '',
    category: 'submission',
    subcategory: '',
    points: 0,
    description: '',
    gi_applicable: true,
    nogi_applicable: true,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterMovements();
  }, [movements, searchQuery, selectedCategory, showGiOnly, showNoGiOnly]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [movementsRes, categoriesRes] = await Promise.all([
        glossaryApi.list(),
        glossaryApi.getCategories(),
      ]);
      const movementsData = movementsRes.data as any;
      setMovements(Array.isArray(movementsData) ? movementsData : movementsData.movements || []);
      setCategories(categoriesRes.data.categories);
    } catch (error) {
      console.error('Error loading glossary:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterMovements = () => {
    let filtered = [...movements];

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(m => m.category === selectedCategory);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        m.name.toLowerCase().includes(query) ||
        m.description?.toLowerCase().includes(query) ||
        m.subcategory?.toLowerCase().includes(query) ||
        (m.aliases || []).some(alias => alias.toLowerCase().includes(query))
      );
    }

    // Gi/No-Gi filters
    if (showGiOnly) {
      filtered = filtered.filter(m => m.gi_applicable);
    }
    if (showNoGiOnly) {
      filtered = filtered.filter(m => m.nogi_applicable);
    }

    setFilteredMovements(filtered);
  };

  const handleAddCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await glossaryApi.create({
        name: customForm.name,
        category: customForm.category,
        subcategory: customForm.subcategory || undefined,
        points: customForm.points,
        description: customForm.description || undefined,
        gi_applicable: customForm.gi_applicable,
        nogi_applicable: customForm.nogi_applicable,
      });
      setShowAddCustom(false);
      setCustomForm({
        name: '',
        category: 'submission',
        subcategory: '',
        points: 0,
        description: '',
        gi_applicable: true,
        nogi_applicable: true,
      });
      await loadData();
      toast.success('Custom movement added successfully');
    } catch (error) {
      console.error('Error adding custom movement:', error);
      toast.error('Failed to add custom movement.');
    }
  };

  const handleDeleteCustom = async () => {
    if (!movementToDelete) return;

    try {
      await glossaryApi.delete(movementToDelete);
      await loadData();
      toast.success('Custom movement deleted successfully');
    } catch (error) {
      console.error('Error deleting movement:', error);
      toast.error('Failed to delete movement. Can only delete custom movements.');
    } finally {
      setMovementToDelete(null);
    }
  };

  const getCategoryStats = () => {
    const stats: Record<string, number> = {};
    movements.forEach(m => {
      stats[m.category] = (stats[m.category] || 0) + 1;
    });
    return stats;
  };

  const categoryStats = getCategoryStats();

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
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Book className="w-8 h-8 text-primary-600" />
          <div>
            <h1 className="text-3xl font-bold">BJJ Glossary</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Showing {filteredMovements.length} of {movements.length} techniques
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowAddCustom(!showAddCustom)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Custom
        </button>
      </div>

      {/* Add Custom Form */}
      {showAddCustom && (
        <form onSubmit={handleAddCustom} className="card bg-gray-50 dark:bg-gray-800 space-y-4">
          <h3 className="text-lg font-semibold">Add Custom Technique</h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Name</label>
              <input
                type="text"
                className="input"
                value={customForm.name}
                onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Category</label>
              <select
                className="input"
                value={customForm.category}
                onChange={(e) => setCustomForm({ ...customForm, category: e.target.value })}
                required
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{CATEGORY_LABELS[cat] || cat}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Subcategory (optional)</label>
              <input
                type="text"
                className="input"
                value={customForm.subcategory}
                onChange={(e) => setCustomForm({ ...customForm, subcategory: e.target.value })}
                placeholder="e.g., choke, armlock"
              />
            </div>
            <div>
              <label className="label">Points</label>
              <input
                type="number"
                className="input"
                value={customForm.points}
                onChange={(e) => setCustomForm({ ...customForm, points: parseInt(e.target.value) })}
                min="0"
              />
            </div>
          </div>

          <div>
            <label className="label">Description</label>
            <textarea
              className="input"
              value={customForm.description}
              onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
              rows={2}
              placeholder="Brief description of the technique"
            />
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={customForm.gi_applicable}
                onChange={(e) => setCustomForm({ ...customForm, gi_applicable: e.target.checked })}
              />
              <span>Gi Applicable</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={customForm.nogi_applicable}
                onChange={(e) => setCustomForm({ ...customForm, nogi_applicable: e.target.checked })}
              />
              <span>No-Gi Applicable</span>
            </label>
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Add Technique</button>
            <button
              type="button"
              onClick={() => setShowAddCustom(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Filters */}
      <div className="card space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            className="input pl-10"
            placeholder="Search techniques, descriptions, aliases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            All ({movements.length})
          </button>
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {CATEGORY_LABELS[category] || category} ({categoryStats[category] || 0})
            </button>
          ))}
        </div>

        {/* Gi/No-Gi Toggles */}
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showGiOnly}
              onChange={(e) => setShowGiOnly(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Gi Only</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showNoGiOnly}
              onChange={(e) => setShowNoGiOnly(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">No-Gi Only</span>
          </label>
        </div>
      </div>

      {/* Techniques List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMovements.map(movement => (
          <div
            key={movement.id}
            className="card hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/glossary/${movement.id}`)}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
                  {movement.name}
                </h3>
                {movement.subcategory && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {movement.subcategory}
                  </p>
                )}
              </div>
              {movement.custom && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setMovementToDelete(movement.id);
                  }}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                  title="Delete custom technique"
                  aria-label="Delete custom technique"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            {movement.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {movement.description}
              </p>
            )}

            <div className="flex flex-wrap gap-2 mb-3">
              <span className={`px-2 py-1 rounded text-xs font-medium ${CATEGORY_COLORS[movement.category]}`}>
                {CATEGORY_LABELS[movement.category] || movement.category}
              </span>
              {movement.points > 0 && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 flex items-center gap-1">
                  <Award className="w-3 h-3" />
                  {movement.points} pts
                </span>
              )}
              {!movement.gi_applicable && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                  No-Gi Only
                </span>
              )}
              {!movement.nogi_applicable && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                  Gi Only
                </span>
              )}
              {movement.custom && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                  Custom
                </span>
              )}
            </div>

            {(movement.aliases || []).length > 0 && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <span className="font-medium">Also known as:</span> {(movement.aliases || []).join(', ')}
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredMovements.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No techniques found matching your filters.
        </div>
      )}

      <ConfirmDialog
        isOpen={movementToDelete !== null}
        onClose={() => setMovementToDelete(null)}
        onConfirm={handleDeleteCustom}
        title="Delete Custom Movement"
        message="Are you sure you want to delete this custom movement? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

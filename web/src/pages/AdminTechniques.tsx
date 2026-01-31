import { useState, useEffect } from 'react';
import { adminApi, techniquesApi } from '../api/client';
import { Search, Trash2, Plus } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';
import AdminNav from '../components/AdminNav';

interface Technique {
  id: number;
  name: string;
  category?: string;
  is_custom: boolean;
  created_by_user_id?: number;
  created_at: string;
  usage_count?: number;
}

export default function AdminTechniques() {
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>(undefined);
  const [customOnlyFilter, setCustomOnlyFilter] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTechnique, setNewTechnique] = useState({ name: '', category: '' });

  useEffect(() => {
    loadTechniques();
  }, [searchQuery, categoryFilter, customOnlyFilter]);

  const loadTechniques = async () => {
    setLoading(true);
    try {
      const response = await adminApi.listTechniques({
        search: searchQuery || undefined,
        category: categoryFilter,
        custom_only: customOnlyFilter || undefined,
      });
      setTechniques(response.data.techniques || []);
    } catch (error) {
      console.error('Error loading techniques:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteTechnique = async (techniqueId: number, name: string) => {
    if (!confirm(`Delete technique "${name}"? This will remove it from all sessions that reference it.`)) return;
    try {
      await adminApi.deleteTechnique(techniqueId);
      loadTechniques();
    } catch (error) {
      console.error('Error deleting technique:', error);
    }
  };

  const createTechnique = async () => {
    if (!newTechnique.name.trim()) return;
    try {
      await techniquesApi.create({
        name: newTechnique.name.trim(),
        category: newTechnique.category.trim() || undefined,
      });
      setShowCreateModal(false);
      setNewTechnique({ name: '', category: '' });
      loadTechniques();
    } catch (error) {
      console.error('Error creating technique:', error);
    }
  };

  const categories = Array.from(new Set(techniques.map((t) => t.category).filter(Boolean)));

  return (
    <div className="space-y-6">
      <AdminNav />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
            Technique Management
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Manage techniques and glossary
          </p>
        </div>
        <PrimaryButton onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Technique
        </PrimaryButton>
      </div>

      {/* Search and Filters */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5" style={{ color: 'var(--muted)' }} />
            <input
              type="text"
              placeholder="Search techniques..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input flex-1"
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setCustomOnlyFilter(!customOnlyFilter)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                customOnlyFilter
                  ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              Custom Only
            </button>

            {categories.length > 0 && (
              <>
                <button
                  onClick={() => setCategoryFilter(undefined)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    !categoryFilter
                      ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  All Categories
                </button>
                {categories.slice(0, 5).map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategoryFilter(categoryFilter === cat ? undefined : cat)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      categoryFilter === cat
                        ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </>
            )}
          </div>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <div>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Total Techniques</p>
            <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
              {techniques.length}
            </p>
          </div>
        </Card>
        <Card>
          <div>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Custom Techniques</p>
            <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
              {techniques.filter((t) => t.is_custom).length}
            </p>
          </div>
        </Card>
        <Card>
          <div>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>Categories</p>
            <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
              {categories.length}
            </p>
          </div>
        </Card>
      </div>

      {/* Techniques List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : techniques.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p style={{ color: 'var(--muted)' }}>No techniques found</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {techniques.map((technique) => (
            <Card key={technique.id}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                      {technique.name}
                    </h3>
                    {technique.is_custom && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
                      >
                        Custom
                      </span>
                    )}
                    {technique.category && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}
                      >
                        {technique.category}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
                    <span>ID: {technique.id}</span>
                    {technique.usage_count !== undefined && (
                      <>
                        <span>•</span>
                        <span>Used {technique.usage_count} times</span>
                      </>
                    )}
                    <span>•</span>
                    <span>Created: {new Date(technique.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {technique.is_custom && (
                  <button
                    onClick={() => deleteTechnique(technique.id, technique.name)}
                    className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                    title="Delete technique"
                  >
                    <Trash2 className="w-4 h-4" style={{ color: 'var(--danger)' }} />
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Technique Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
          onClick={() => setShowCreateModal(false)}
        >
          <div onClick={(e: React.MouseEvent) => e.stopPropagation()}>
            <Card className="max-w-md w-full">
            <div className="space-y-4">
              <h2 className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                Add New Technique
              </h2>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Technique Name *
                </label>
                <input
                  type="text"
                  value={newTechnique.name}
                  onChange={(e) => setNewTechnique({ ...newTechnique, name: e.target.value })}
                  placeholder="e.g., Triangle Choke"
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Category (optional)
                </label>
                <input
                  type="text"
                  value={newTechnique.category}
                  onChange={(e) => setNewTechnique({ ...newTechnique, category: e.target.value })}
                  placeholder="e.g., Submissions, Guards"
                  className="input w-full"
                />
              </div>

              <div className="flex gap-2 pt-4">
                <PrimaryButton
                  onClick={createTechnique}
                  disabled={!newTechnique.name.trim()}
                  className="flex-1"
                >
                  Create Technique
                </PrimaryButton>
                <SecondaryButton onClick={() => setShowCreateModal(false)}>
                  Cancel
                </SecondaryButton>
              </div>
            </div>
          </Card>
          </div>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { adminApi } from '../api/client';
import { Search, Plus, Edit2, Trash2, Check, MapPin, Globe, Building2 } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';

interface Gym {
  id: number;
  name: string;
  city?: string;
  state?: string;
  country: string;
  address?: string;
  website?: string;
  email?: string;
  phone?: string;
  head_coach?: string;
  verified: boolean;
  added_by_user_id?: number;
  created_at: string;
  updated_at: string;
  // From pending gyms query (user info)
  first_name?: string;
  last_name?: string;
}

export default function AdminGyms() {
  const [gyms, setGyms] = useState<Gym[]>([]);
  const [pendingGyms, setPendingGyms] = useState<Gym[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingGym, setEditingGym] = useState<Gym | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'pending'>('all');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    city: '',
    state: '',
    country: 'Australia',
    address: '',
    website: '',
    email: '',
    phone: '',
    head_coach: '',
    verified: false,
  });

  useEffect(() => {
    loadGyms();
    loadPendingGyms();
  }, []);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchGyms();
    } else if (searchQuery.length === 0) {
      loadGyms();
    }
  }, [searchQuery]);

  const loadGyms = async () => {
    setLoading(true);
    try {
      const response = await adminApi.listGyms(false);
      setGyms(response.data.gyms || []);
    } catch (error) {
      console.error('Error loading gyms:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPendingGyms = async () => {
    try {
      const response = await adminApi.getPendingGyms();
      setPendingGyms(response.data.pending_gyms || []);
    } catch (error) {
      console.error('Error loading pending gyms:', error);
    }
  };

  const searchGyms = async () => {
    try {
      const response = await adminApi.searchGyms(searchQuery, false);
      setGyms(response.data.gyms || []);
    } catch (error) {
      console.error('Error searching gyms:', error);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createGym(formData);
      setShowAddForm(false);
      setFormData({ name: '', city: '', state: '', country: 'Australia', address: '', website: '', email: '', phone: '', head_coach: '', verified: false });
      loadGyms();
      loadPendingGyms();
    } catch (error) {
      console.error('Error creating gym:', error);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGym) return;
    try {
      await adminApi.updateGym(editingGym.id, formData);
      setEditingGym(null);
      setFormData({ name: '', city: '', state: '', country: 'Australia', address: '', website: '', email: '', phone: '', head_coach: '', verified: false });
      loadGyms();
      loadPendingGyms();
    } catch (error) {
      console.error('Error updating gym:', error);
    }
  };

  const handleDelete = async (gymId: number) => {
    if (!confirm('Are you sure you want to delete this gym?')) return;
    try {
      await adminApi.deleteGym(gymId);
      loadGyms();
      loadPendingGyms();
    } catch (error) {
      console.error('Error deleting gym:', error);
    }
  };

  const handleVerify = async (gym: Gym) => {
    try {
      await adminApi.updateGym(gym.id, { verified: true });
      loadGyms();
      loadPendingGyms();
    } catch (error) {
      console.error('Error verifying gym:', error);
    }
  };

  const startEdit = (gym: Gym) => {
    setEditingGym(gym);
    setFormData({
      name: gym.name,
      city: gym.city || '',
      state: gym.state || '',
      country: gym.country,
      address: gym.address || '',
      website: gym.website || '',
      email: gym.email || '',
      phone: gym.phone || '',
      head_coach: gym.head_coach || '',
      verified: gym.verified,
    });
    setShowAddForm(false);
  };

  const cancelEdit = () => {
    setEditingGym(null);
    setShowAddForm(false);
    setFormData({ name: '', city: '', state: '', country: 'Australia', address: '', website: '', email: '', phone: '', head_coach: '', verified: false });
  };

  const displayGyms = activeTab === 'pending' ? pendingGyms : gyms;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
            Gym Management
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Manage gym database and verify user-added gyms
          </p>
        </div>
        <PrimaryButton onClick={() => { setShowAddForm(true); setEditingGym(null); }} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Gym
        </PrimaryButton>
      </div>

      {/* Tabs */}
      <div className="flex gap-2" style={{ borderBottom: '1px solid var(--border)' }}>
        <button
          onClick={() => setActiveTab('all')}
          className="px-4 py-2 text-sm font-medium transition-colors"
          style={{
            color: activeTab === 'all' ? 'var(--primary)' : 'var(--muted)',
            borderBottom: activeTab === 'all' ? '2px solid var(--primary)' : '2px solid transparent',
          }}
        >
          All Gyms ({gyms.length})
        </button>
        <button
          onClick={() => setActiveTab('pending')}
          className="px-4 py-2 text-sm font-medium transition-colors"
          style={{
            color: activeTab === 'pending' ? 'var(--primary)' : 'var(--muted)',
            borderBottom: activeTab === 'pending' ? '2px solid var(--primary)' : '2px solid transparent',
          }}
        >
          Pending Verification ({pendingGyms.length})
        </button>
      </div>

      {/* Search */}
      {activeTab === 'all' && (
        <Card>
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5" style={{ color: 'var(--muted)' }} />
            <input
              type="text"
              placeholder="Search gyms by name or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input flex-1"
            />
          </div>
        </Card>
      )}

      {/* Add/Edit Form */}
      {(showAddForm || editingGym) && (
        <Card>
          <form onSubmit={editingGym ? handleUpdate : handleCreate} className="space-y-4">
            <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
              {editingGym ? 'Edit Gym' : 'Add New Gym'}
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="Gym name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  City
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="input w-full"
                  placeholder="City"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  State
                </label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="input w-full"
                  placeholder="State"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Country
                </label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  className="input w-full"
                  placeholder="Country"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Address
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input w-full"
                  placeholder="Full address"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Website
                </label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  className="input w-full"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input w-full"
                  placeholder="contact@gym.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input w-full"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                  Head Coach
                </label>
                <input
                  type="text"
                  value={formData.head_coach}
                  onChange={(e) => setFormData({ ...formData, head_coach: e.target.value })}
                  className="input w-full"
                  placeholder="Coach name"
                />
              </div>

              <div className="md:col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.verified}
                    onChange={(e) => setFormData({ ...formData, verified: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm" style={{ color: 'var(--text)' }}>
                    Verified gym
                  </span>
                </label>
              </div>
            </div>

            <div className="flex gap-2">
              <PrimaryButton type="submit">
                {editingGym ? 'Update' : 'Create'}
              </PrimaryButton>
              <SecondaryButton type="button" onClick={cancelEdit}>
                Cancel
              </SecondaryButton>
            </div>
          </form>
        </Card>
      )}

      {/* Gyms List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : displayGyms.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Building2 className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
              No Gyms Found
            </h3>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              {activeTab === 'pending' ? 'No pending gyms to verify' : 'Start by adding a gym'}
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {displayGyms.map((gym) => (
            <Card key={gym.id}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                      {gym.name}
                    </h3>
                    {gym.verified && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
                      >
                        Verified
                      </span>
                    )}
                    {!gym.verified && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--warning-bg)', color: 'var(--warning)' }}
                      >
                        Pending
                      </span>
                    )}
                  </div>

                  <div className="space-y-1">
                    {(gym.city || gym.state || gym.country) && (
                      <div className="flex items-center gap-1 text-sm" style={{ color: 'var(--muted)' }}>
                        <MapPin className="w-4 h-4" />
                        <span>
                          {[gym.city, gym.state, gym.country].filter(Boolean).join(', ')}
                        </span>
                      </div>
                    )}

                    {gym.website && (
                      <div className="flex items-center gap-1 text-sm" style={{ color: 'var(--muted)' }}>
                        <Globe className="w-4 h-4" />
                        <a
                          href={gym.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                          style={{ color: 'var(--primary)' }}
                        >
                          {gym.website}
                        </a>
                      </div>
                    )}

                    {gym.first_name && gym.last_name && (
                      <div className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
                        Added by: {gym.first_name} {gym.last_name} ({gym.email})
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {!gym.verified && (
                    <button
                      onClick={() => handleVerify(gym)}
                      className="p-2 rounded-lg hover:bg-green-500/10 transition-colors"
                      title="Verify gym"
                    >
                      <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                    </button>
                  )}
                  <button
                    onClick={() => startEdit(gym)}
                    className="p-2 rounded-lg hover:bg-blue-500/10 transition-colors"
                    title="Edit gym"
                  >
                    <Edit2 className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                  </button>
                  <button
                    onClick={() => handleDelete(gym.id)}
                    className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                    title="Delete gym"
                  >
                    <Trash2 className="w-4 h-4" style={{ color: 'var(--danger)' }} />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

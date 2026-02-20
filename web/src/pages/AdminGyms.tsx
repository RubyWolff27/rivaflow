import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { adminApi } from '../api/client';
import { logger } from '../utils/logger';
import { Search, Plus } from 'lucide-react';
import { Card, PrimaryButton } from '../components/ui';
import AdminNav from '../components/AdminNav';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';
import GymForm from '../components/admin/GymForm';
import type { GymFormData } from '../components/admin/GymForm';
import GymTable from '../components/admin/GymTable';
import type { Gym } from '../components/admin/GymTable';

const EMPTY_FORM: GymFormData = {
  name: '', city: '', state: '', country: 'Australia', address: '',
  website: '', email: '', phone: '', head_coach: '', head_coach_belt: '',
  google_maps_url: '', verified: false,
};

export default function AdminGyms() {
  usePageTitle('Gym Management');
  const toast = useToast();
  const [gyms, setGyms] = useState<Gym[]>([]);
  const [pendingGyms, setPendingGyms] = useState<Gym[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingGym, setEditingGym] = useState<Gym | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'pending'>('all');
  const [confirmDelete, setConfirmDelete] = useState<{ id: number; name: string } | null>(null);

  const [formData, setFormData] = useState<GymFormData>({ ...EMPTY_FORM });

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const [gymsRes, pendingRes] = await Promise.all([
          adminApi.listGyms(false),
          adminApi.getPendingGyms(),
        ]);
        if (!cancelled) {
          setGyms(gymsRes.data.gyms || []);
          setPendingGyms(pendingRes.data.pending_gyms || []);
        }
      } catch (err) {
        if (!cancelled) { logger.warn('Failed to load gyms', err); toast.error('Failed to load gyms. Please try again.'); }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const doSearch = async () => {
      if (searchQuery.length >= 2) {
        try {
          const response = await adminApi.searchGyms(searchQuery, false);
          if (!cancelled) setGyms(response.data.gyms || []);
        } catch (err) {
          if (!cancelled) { logger.warn('Failed to search gyms', err); toast.error('Failed to search gyms. Please try again.'); }
        }
      } else if (searchQuery.length === 0) {
        try {
          setLoading(true);
          const response = await adminApi.listGyms(false);
          if (!cancelled) setGyms(response.data.gyms || []);
        } catch {
          if (!cancelled) toast.error('Failed to load gyms. Please try again.');
        } finally {
          if (!cancelled) setLoading(false);
        }
      }
    };
    doSearch();
    return () => { cancelled = true; };
  }, [searchQuery]);

  const loadGyms = async () => {
    setLoading(true);
    try {
      const response = await adminApi.listGyms(false);
      setGyms(response.data.gyms || []);
    } catch (err) {
      logger.warn('Failed to load gyms', err);
      toast.error('Failed to load gyms. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadPendingGyms = async () => {
    try {
      const response = await adminApi.getPendingGyms();
      setPendingGyms(response.data.pending_gyms || []);
    } catch (err) {
      logger.warn('Failed to load pending gyms', err);
      toast.error('Failed to load pending gyms. Please try again.');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createGym(formData);
      setShowAddForm(false);
      setFormData({ ...EMPTY_FORM });
      toast.success(`Gym "${formData.name}" created successfully!`);
      loadGyms();
      loadPendingGyms();
    } catch (err) {
      logger.warn('Failed to create gym', err);
      toast.error('Failed to create gym. Please try again.');
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGym) return;
    try {
      await adminApi.updateGym(editingGym.id, formData);
      setEditingGym(null);
      setFormData({ ...EMPTY_FORM });
      toast.success(`Gym "${formData.name}" updated successfully!`);
      loadGyms();
      loadPendingGyms();
    } catch (err) {
      logger.warn('Failed to update gym', err);
      toast.error('Failed to update gym. Please try again.');
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      await adminApi.deleteGym(confirmDelete.id);
      toast.success(`Gym "${confirmDelete.name}" deleted successfully!`);
      setConfirmDelete(null);
      loadGyms();
      loadPendingGyms();
    } catch (err) {
      logger.warn('Failed to delete gym', err);
      toast.error('Failed to delete gym. Please try again.');
      setConfirmDelete(null);
    }
  };

  const handleVerify = async (gym: Gym) => {
    try {
      await adminApi.verifyGym(gym.id);
      toast.success(`Gym "${gym.name}" verified successfully!`);
      loadGyms();
      loadPendingGyms();
    } catch (err) {
      logger.warn('Failed to verify gym', err);
      toast.error('Failed to verify gym. Please try again.');
    }
  };

  const handleReject = async (gym: Gym) => {
    const reason = prompt(`Reason for rejecting "${gym.name}"?`);
    if (reason === null) return;

    try {
      await adminApi.rejectGym(gym.id, reason || undefined);
      toast.success(`Gym "${gym.name}" rejected`);
      loadGyms();
      loadPendingGyms();
    } catch (err) {
      logger.warn('Failed to reject gym', err);
      toast.error('Failed to reject gym. Please try again.');
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
      head_coach_belt: gym.head_coach_belt || '',
      google_maps_url: gym.google_maps_url || '',
      verified: gym.verified,
    });
    setShowAddForm(false);
  };

  const cancelEdit = () => {
    setEditingGym(null);
    setShowAddForm(false);
    setFormData({ ...EMPTY_FORM });
  };

  const displayGyms = activeTab === 'pending' ? pendingGyms : gyms;

  return (
    <div className="space-y-6">
      <AdminNav />

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
        <GymForm
          formData={formData}
          onFormDataChange={setFormData}
          onSubmit={editingGym ? handleUpdate : handleCreate}
          onCancel={cancelEdit}
          isEditing={!!editingGym}
        />
      )}

      {/* Gyms List */}
      <GymTable
        gyms={displayGyms}
        loading={loading}
        activeTab={activeTab}
        onEdit={startEdit}
        onDelete={(gym) => setConfirmDelete({ id: gym.id, name: gym.name })}
        onVerify={handleVerify}
        onReject={handleReject}
      />

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleDelete}
        title="Delete Gym"
        message={`Are you sure you want to delete "${confirmDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

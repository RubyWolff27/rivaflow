import { useState, useEffect } from 'react';
import { adminApi } from '../api/client';
import { Search, Shield, ShieldOff, UserX, Eye, CheckCircle, XCircle } from 'lucide-react';
import { Card, PrimaryButton, SecondaryButton } from '../components/ui';
import AdminNav from '../components/AdminNav';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface UserDetails extends User {
  stats: {
    sessions: number;
    comments: number;
    followers: number;
    following: number;
  };
}

export default function AdminUsers() {
  const toast = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<UserDetails | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [filterAdmin, setFilterAdmin] = useState<boolean | undefined>(undefined);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'toggleActive' | 'toggleAdmin' | 'delete';
    userId: number;
    email?: string;
    currentStatus?: boolean;
  } | null>(null);

  useEffect(() => {
    loadUsers();
  }, [searchQuery, filterActive, filterAdmin]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await adminApi.listUsers({
        search: searchQuery || undefined,
        is_active: filterActive,
        is_admin: filterAdmin,
        limit: 100,
      });
      setUsers(response.data.users || []);
    } catch (error) {
      toast.error('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const viewUserDetails = async (userId: number) => {
    try {
      const response = await adminApi.getUserDetails(userId);
      setSelectedUser(response.data);
      setShowDetailsModal(true);
    } catch (error) {
      toast.error('Failed to load user details. Please try again.');
    }
  };

  const toggleUserActive = async () => {
    if (!confirmAction || confirmAction.type !== 'toggleActive') return;
    try {
      await adminApi.updateUser(confirmAction.userId, { is_active: !confirmAction.currentStatus });
      toast.success(`User ${confirmAction.currentStatus ? 'deactivated' : 'activated'} successfully!`);
      setConfirmAction(null);
      loadUsers();
      if (selectedUser && selectedUser.id === confirmAction.userId) {
        setShowDetailsModal(false);
      }
    } catch (error) {
      toast.error('Failed to update user status. Please try again.');
      setConfirmAction(null);
    }
  };

  const toggleUserAdmin = async () => {
    if (!confirmAction || confirmAction.type !== 'toggleAdmin') return;
    try {
      await adminApi.updateUser(confirmAction.userId, { is_admin: !confirmAction.currentStatus });
      toast.success(`Admin privileges ${confirmAction.currentStatus ? 'revoked' : 'granted'} successfully!`);
      setConfirmAction(null);
      loadUsers();
      if (selectedUser && selectedUser.id === confirmAction.userId) {
        viewUserDetails(confirmAction.userId); // Refresh details
      }
    } catch (error) {
      toast.error('Failed to update admin privileges. Please try again.');
      setConfirmAction(null);
    }
  };

  const deleteUser = async () => {
    if (!confirmAction || confirmAction.type !== 'delete') return;
    try {
      await adminApi.deleteUser(confirmAction.userId);
      toast.success(`User "${confirmAction.email}" deleted successfully!`);
      setConfirmAction(null);
      loadUsers();
      setShowDetailsModal(false);
    } catch (error) {
      toast.error('Failed to delete user. Please try again.');
      setConfirmAction(null);
    }
  };

  return (
    <div className="space-y-6">
      <AdminNav />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
          User Management
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Manage user accounts and permissions
        </p>
      </div>

      {/* Search and Filters */}
      <Card>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5" style={{ color: 'var(--muted)' }} />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input flex-1"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setFilterActive(filterActive === true ? undefined : true)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                filterActive === true
                  ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              Active Only
            </button>
            <button
              onClick={() => setFilterActive(filterActive === false ? undefined : false)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                filterActive === false
                  ? 'bg-red-500/20 text-red-600 dark:text-red-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              Inactive Only
            </button>
            <button
              onClick={() => setFilterAdmin(filterAdmin === true ? undefined : true)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                filterAdmin === true
                  ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
              }`}
            >
              Admins Only
            </button>
          </div>
        </div>
      </Card>

      {/* Users List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : users.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p style={{ color: 'var(--muted)' }}>No users found</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {users.map((user) => (
            <Card key={user.id}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                      {user.first_name} {user.last_name}
                    </h3>
                    {user.is_admin && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
                      >
                        Admin
                      </span>
                    )}
                    {!user.is_active && (
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' }}
                      >
                        Inactive
                      </span>
                    )}
                  </div>
                  <p className="text-sm" style={{ color: 'var(--muted)' }}>
                    {user.email}
                  </p>
                  <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
                    Joined: {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => viewUserDetails(user.id)}
                    className="p-2 rounded-lg hover:bg-blue-500/10 transition-colors"
                    title="View details"
                  >
                    <Eye className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                  </button>
                  <button
                    onClick={() => setConfirmAction({ type: 'toggleActive', userId: user.id, currentStatus: user.is_active })}
                    className="p-2 rounded-lg hover:bg-yellow-500/10 transition-colors"
                    title={user.is_active ? 'Deactivate' : 'Activate'}
                    aria-label={`${user.is_active ? 'Deactivate' : 'Activate'} ${user.email}`}
                  >
                    {user.is_active ? (
                      <XCircle className="w-4 h-4" style={{ color: 'var(--warning)' }} />
                    ) : (
                      <CheckCircle className="w-4 h-4" style={{ color: 'var(--success)' }} />
                    )}
                  </button>
                  <button
                    onClick={() => setConfirmAction({ type: 'toggleAdmin', userId: user.id, currentStatus: user.is_admin })}
                    className="p-2 rounded-lg hover:bg-purple-500/10 transition-colors"
                    title={user.is_admin ? 'Revoke admin' : 'Grant admin'}
                    aria-label={`${user.is_admin ? 'Revoke admin from' : 'Grant admin to'} ${user.email}`}
                  >
                    {user.is_admin ? (
                      <ShieldOff className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                    ) : (
                      <Shield className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                    )}
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* User Details Modal */}
      {showDetailsModal && selectedUser && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
          onClick={() => setShowDetailsModal(false)}
        >
          <div onClick={(e: React.MouseEvent) => e.stopPropagation()}>
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                    {selectedUser.first_name} {selectedUser.last_name}
                  </h2>
                  <p className="text-sm" style={{ color: 'var(--muted)' }}>
                    {selectedUser.email}
                  </p>
                </div>
                <div className="flex gap-2">
                  {selectedUser.is_admin && (
                    <span
                      className="px-3 py-1 text-xs rounded-full"
                      style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
                    >
                      Admin
                    </span>
                  )}
                  <span
                    className="px-3 py-1 text-xs rounded-full"
                    style={{
                      backgroundColor: selectedUser.is_active ? 'var(--success-bg)' : 'var(--danger-bg)',
                      color: selectedUser.is_active ? 'var(--success)' : 'var(--danger)',
                    }}
                  >
                    {selectedUser.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>Sessions</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                    {selectedUser.stats.sessions}
                  </p>
                </div>
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>Comments</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                    {selectedUser.stats.comments}
                  </p>
                </div>
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>Followers</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                    {selectedUser.stats.followers}
                  </p>
                </div>
                <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                  <p className="text-xs" style={{ color: 'var(--muted)' }}>Following</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                    {selectedUser.stats.following}
                  </p>
                </div>
              </div>

              {/* Info */}
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium" style={{ color: 'var(--muted)' }}>User ID: </span>
                  <span className="text-sm" style={{ color: 'var(--text)' }}>{selectedUser.id}</span>
                </div>
                <div>
                  <span className="text-sm font-medium" style={{ color: 'var(--muted)' }}>Joined: </span>
                  <span className="text-sm" style={{ color: 'var(--text)' }}>
                    {new Date(selectedUser.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
                <PrimaryButton
                  onClick={() => setConfirmAction({ type: 'toggleAdmin', userId: selectedUser.id, currentStatus: selectedUser.is_admin, email: selectedUser.email })}
                  className="flex items-center gap-2"
                >
                  {selectedUser.is_admin ? <ShieldOff className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                  {selectedUser.is_admin ? 'Revoke Admin' : 'Grant Admin'}
                </PrimaryButton>

                <SecondaryButton
                  onClick={() => setConfirmAction({ type: 'toggleActive', userId: selectedUser.id, currentStatus: selectedUser.is_active, email: selectedUser.email })}
                  className="flex items-center gap-2"
                >
                  {selectedUser.is_active ? 'Deactivate' : 'Activate'}
                </SecondaryButton>

                <button
                  onClick={() => setConfirmAction({ type: 'delete', userId: selectedUser.id, email: selectedUser.email })}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors ml-auto"
                  style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' }}
                  aria-label={`Delete user ${selectedUser.email}`}
                >
                  <UserX className="w-4 h-4 inline mr-2" />
                  Delete User
                </button>
              </div>
            </div>
          </Card>
          </div>
        </div>
      )}

      {/* Confirm Action Dialog */}
      {confirmAction && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          onConfirm={() => {
            if (confirmAction.type === 'toggleActive') toggleUserActive();
            else if (confirmAction.type === 'toggleAdmin') toggleUserAdmin();
            else if (confirmAction.type === 'delete') deleteUser();
          }}
          title={
            confirmAction.type === 'toggleActive'
              ? confirmAction.currentStatus ? 'Deactivate User' : 'Activate User'
              : confirmAction.type === 'toggleAdmin'
              ? confirmAction.currentStatus ? 'Revoke Admin' : 'Grant Admin'
              : 'Delete User'
          }
          message={
            confirmAction.type === 'toggleActive'
              ? `Are you sure you want to ${confirmAction.currentStatus ? 'deactivate' : 'activate'} this user${confirmAction.email ? ` (${confirmAction.email})` : ''}?`
              : confirmAction.type === 'toggleAdmin'
              ? `Are you sure you want to ${confirmAction.currentStatus ? 'revoke admin from' : 'grant admin to'} this user${confirmAction.email ? ` (${confirmAction.email})` : ''}?`
              : `DANGER: Permanently delete user ${confirmAction.email}? This action cannot be undone!`
          }
          confirmText={
            confirmAction.type === 'delete' ? 'Delete Permanently' : 'Confirm'
          }
          cancelText="Cancel"
          variant={confirmAction.type === 'delete' ? 'danger' : 'warning'}
        />
      )}
    </div>
  );
}

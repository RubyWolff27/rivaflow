import { useState, useEffect } from 'react';
import { Search, Send, X, Users, Clock, CheckCircle, XCircle } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import AdminNav from '../components/AdminNav';
import { adminApi } from '../api/client';
import { logger } from '../utils/logger';
import { useToast } from '../contexts/ToastContext';
import ConfirmDialog from '../components/ConfirmDialog';

interface WaitlistEntry {
  id: number;
  email: string;
  first_name: string | null;
  gym_name: string | null;
  belt_rank: string | null;
  referral_source: string | null;
  status: string;
  position: number;
  invite_token: string | null;
  invite_expires_at: string | null;
  assigned_tier: string | null;
  admin_notes: string | null;
  created_at: string;
}

interface WaitlistStats {
  total: number;
  waiting: number;
  invited: number;
  registered: number;
  declined: number;
}

export default function AdminWaitlist() {
  usePageTitle('Waitlist Management');
  const toast = useToast();

  const [entries, setEntries] = useState<WaitlistEntry[]>([]);
  const [stats, setStats] = useState<WaitlistStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 25;

  // Selected entries for bulk actions
  const [selected, setSelected] = useState<Set<number>>(new Set());

  // Modal state
  const [showDetail, setShowDetail] = useState<WaitlistEntry | null>(null);
  const [notes, setNotes] = useState('');

  // Confirm dialog
  const [confirmAction, setConfirmAction] = useState<{ type: string; entry?: WaitlistEntry; ids?: number[] } | null>(null);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const res = await adminApi.listWaitlist({
        status: statusFilter || undefined,
        search: search || undefined,
        limit,
        offset: page * limit,
      });
      setEntries(res.data.entries);
      setTotal(res.data.total);
    } catch (err) {
      logger.warn('Failed to load waitlist', err);
      toast.error('Failed to load waitlist');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const res = await adminApi.getWaitlistStats();
      setStats(res.data);
    } catch (err) {
      logger.debug('Waitlist stats not available', err);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const [entriesRes, statsRes] = await Promise.all([
          adminApi.listWaitlist({
            status: statusFilter || undefined,
            search: search || undefined,
            limit,
            offset: page * limit,
          }),
          adminApi.getWaitlistStats(),
        ]);
        if (!cancelled) {
          setEntries(entriesRes.data.entries);
          setTotal(entriesRes.data.total);
          setStats(statsRes.data);
        }
      } catch (err) {
        if (!cancelled) { logger.warn('Failed to load waitlist', err); toast.error('Failed to load waitlist'); }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [statusFilter, page]);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      if (!cancelled) {
        setPage(0);
        loadEntries();
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [search]);

  const handleInvite = async (entry: WaitlistEntry) => {
    try {
      await adminApi.inviteWaitlistEntry(entry.id);
      toast.success(`Invite sent to ${entry.email}`);
      loadEntries();
      loadStats();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Failed to invite');
    }
    setConfirmAction(null);
  };

  const handleDecline = async (entry: WaitlistEntry) => {
    try {
      await adminApi.declineWaitlistEntry(entry.id);
      toast.success(`Declined ${entry.email}`);
      loadEntries();
      loadStats();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Failed to decline');
    }
    setConfirmAction(null);
  };

  const handleBulkInvite = async () => {
    const ids = Array.from(selected);
    try {
      const res = await adminApi.bulkInviteWaitlist(ids);
      toast.success(`Invited ${res.data.invited_count} entries`);
      setSelected(new Set());
      loadEntries();
      loadStats();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || 'Bulk invite failed');
    }
    setConfirmAction(null);
  };

  const handleSaveNotes = async () => {
    if (!showDetail) return;
    try {
      await adminApi.updateWaitlistNotes(showDetail.id, notes);
      toast.success('Notes saved');
      setShowDetail(null);
      loadEntries();
    } catch (err) {
      logger.warn('Failed to save notes', err);
      toast.error('Failed to save notes');
    }
  };

  const toggleSelect = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    const waitingIds = entries.filter(e => e.status === 'waiting').map(e => e.id);
    if (waitingIds.every(id => selected.has(id))) {
      setSelected(prev => {
        const next = new Set(prev);
        waitingIds.forEach(id => next.delete(id));
        return next;
      });
    } else {
      setSelected(prev => {
        const next = new Set(prev);
        waitingIds.forEach(id => next.add(id));
        return next;
      });
    }
  };

  const statusBadge = (s: string) => {
    const styles: Record<string, { bg: string; color: string }> = {
      waiting: { bg: 'var(--warning-bg)', color: 'var(--warning)' },
      invited: { bg: 'var(--primary-bg)', color: 'var(--primary)' },
      registered: { bg: 'var(--success-bg)', color: 'var(--success)' },
      declined: { bg: 'var(--danger-bg)', color: 'var(--danger)' },
    };
    const style = styles[s] || styles.waiting;
    return (
      <span
        className="px-2 py-0.5 rounded-full text-xs font-medium"
        style={{ backgroundColor: style.bg, color: style.color }}
      >
        {s}
      </span>
    );
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <AdminNav />

      <h1 className="text-2xl font-bold mb-4" style={{ color: 'var(--text)' }}>Waitlist Management</h1>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Waiting', value: stats.waiting, icon: Clock, color: 'var(--warning)' },
            { label: 'Invited', value: stats.invited, icon: Send, color: 'var(--primary)' },
            { label: 'Registered', value: stats.registered, icon: CheckCircle, color: 'var(--success)' },
            { label: 'Declined', value: stats.declined, icon: XCircle, color: 'var(--danger)' },
          ].map(stat => (
            <div
              key={stat.label}
              className="p-4 rounded-lg"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              <div className="flex items-center gap-2 mb-1">
                <stat.icon className="w-4 h-4" style={{ color: stat.color }} />
                <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>{stat.label}</span>
              </div>
              <div className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{stat.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--muted)' }} />
          <input
            type="text"
            placeholder="Search by email or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-2"
            style={{
              borderColor: 'var(--border)',
              backgroundColor: 'var(--surface)',
              color: 'var(--text)',
            }}
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
          className="px-3 py-2 rounded-lg text-sm border focus:outline-none"
          style={{
            borderColor: 'var(--border)',
            backgroundColor: 'var(--surface)',
            color: 'var(--text)',
          }}
        >
          <option value="">All statuses</option>
          <option value="waiting">Waiting</option>
          <option value="invited">Invited</option>
          <option value="registered">Registered</option>
          <option value="declined">Declined</option>
        </select>

        {selected.size > 0 && (
          <button
            onClick={() => setConfirmAction({ type: 'bulk_invite', ids: Array.from(selected) })}
            className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
            style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
          >
            <Send className="w-4 h-4" />
            Invite Selected ({selected.size})
          </button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg overflow-hidden" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
        {loading ? (
          <div className="p-8 text-center" style={{ color: 'var(--muted)' }}>Loading...</div>
        ) : entries.length === 0 ? (
          <div className="p-8 text-center" style={{ color: 'var(--muted)' }}>
            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
            No waitlist entries found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      onChange={toggleSelectAll}
                      checked={entries.filter(e => e.status === 'waiting').every(e => selected.has(e.id)) && entries.some(e => e.status === 'waiting')}
                    />
                  </th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>#</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Email</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Name</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Gym</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Belt</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Status</th>
                  <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--muted)' }}>Joined</th>
                  <th className="px-4 py-3 text-right font-medium" style={{ color: 'var(--muted)' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(entry => (
                  <tr
                    key={entry.id}
                    className="cursor-pointer hover:opacity-80"
                    style={{ borderBottom: '1px solid var(--border)' }}
                    onClick={() => { setShowDetail(entry); setNotes(entry.admin_notes || ''); }}
                  >
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      {entry.status === 'waiting' && (
                        <input
                          type="checkbox"
                          checked={selected.has(entry.id)}
                          onChange={() => toggleSelect(entry.id)}
                        />
                      )}
                    </td>
                    <td className="px-4 py-3" style={{ color: 'var(--muted)' }}>{entry.position}</td>
                    <td className="px-4 py-3 font-medium" style={{ color: 'var(--text)' }}>{entry.email}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--text)' }}>{entry.first_name || '-'}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--muted)' }}>{entry.gym_name || '-'}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--muted)' }}>{entry.belt_rank || '-'}</td>
                    <td className="px-4 py-3">{statusBadge(entry.status)}</td>
                    <td className="px-4 py-3" style={{ color: 'var(--muted)' }}>
                      {new Date(entry.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                      {entry.status === 'waiting' && (
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setConfirmAction({ type: 'invite', entry })}
                            className="px-3 py-1 rounded text-xs font-medium transition-colors"
                            style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
                          >
                            Invite
                          </button>
                          <button
                            onClick={() => setConfirmAction({ type: 'decline', entry })}
                            className="px-3 py-1 rounded text-xs font-medium transition-colors"
                            style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' }}
                          >
                            Decline
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3" style={{ borderTop: '1px solid var(--border)' }}>
            <span className="text-sm" style={{ color: 'var(--muted)' }}>
              Showing {page * limit + 1}-{Math.min((page + 1) * limit, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 rounded text-sm disabled:opacity-40"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 rounded text-sm disabled:opacity-40"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)', border: '1px solid var(--border)' }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div
            className="w-full max-w-lg rounded-lg p-6"
            style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
                Waitlist Entry #{showDetail.position}
              </h3>
              <button onClick={() => setShowDetail(null)}>
                <X className="w-5 h-5" style={{ color: 'var(--muted)' }} />
              </button>
            </div>

            <div className="space-y-3 text-sm mb-4">
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Email</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{showDetail.email}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Name</span>
                <span style={{ color: 'var(--text)' }}>{showDetail.first_name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Gym</span>
                <span style={{ color: 'var(--text)' }}>{showDetail.gym_name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Belt</span>
                <span style={{ color: 'var(--text)' }}>{showDetail.belt_rank || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Referral</span>
                <span style={{ color: 'var(--text)' }}>{showDetail.referral_source || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Status</span>
                {statusBadge(showDetail.status)}
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--muted)' }}>Joined</span>
                <span style={{ color: 'var(--text)' }}>{new Date(showDetail.created_at).toLocaleString()}</span>
              </div>
              {showDetail.assigned_tier && (
                <div className="flex justify-between">
                  <span style={{ color: 'var(--muted)' }}>Assigned Tier</span>
                  <span style={{ color: 'var(--text)' }}>{showDetail.assigned_tier}</span>
                </div>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>
                Admin Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 rounded-md border text-sm focus:outline-none focus:ring-2"
                style={{
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--surfaceElev)',
                  color: 'var(--text)',
                }}
                placeholder="Add notes about this entry..."
              />
            </div>

            <div className="flex justify-between">
              <div className="flex gap-2">
                {showDetail.status === 'waiting' && (
                  <>
                    <button
                      onClick={() => { setShowDetail(null); setConfirmAction({ type: 'invite', entry: showDetail }); }}
                      className="px-4 py-2 rounded-lg text-sm font-medium"
                      style={{ backgroundColor: 'var(--primary-bg)', color: 'var(--primary)' }}
                    >
                      Invite
                    </button>
                    <button
                      onClick={() => { setShowDetail(null); setConfirmAction({ type: 'decline', entry: showDetail }); }}
                      className="px-4 py-2 rounded-lg text-sm font-medium"
                      style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' }}
                    >
                      Decline
                    </button>
                  </>
                )}
              </div>
              <button
                onClick={handleSaveNotes}
                className="px-4 py-2 rounded-lg text-sm font-medium"
                style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
              >
                Save Notes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Dialog */}
      {confirmAction?.type === 'invite' && confirmAction.entry && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          onConfirm={() => handleInvite(confirmAction.entry!)}
          title="Send Invite?"
          message={`Send an invite email to ${confirmAction.entry.email}? They'll receive a unique registration link.`}
          confirmText="Send Invite"
          cancelText="Cancel"
        />
      )}

      {confirmAction?.type === 'decline' && confirmAction.entry && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          onConfirm={() => handleDecline(confirmAction.entry!)}
          title="Decline Entry?"
          message={`Decline ${confirmAction.entry.email}? They won't be notified.`}
          confirmText="Decline"
          cancelText="Cancel"
          variant="danger"
        />
      )}

      {confirmAction?.type === 'bulk_invite' && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          onConfirm={handleBulkInvite}
          title="Bulk Invite?"
          message={`Send invite emails to ${selected.size} selected entries?`}
          confirmText="Invite All"
          cancelText="Cancel"
        />
      )}
    </div>
  );
}

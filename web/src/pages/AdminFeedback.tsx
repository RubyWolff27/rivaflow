import { useState, useEffect } from 'react';
import { adminApi } from '../api/client';
import { MessageCircle, CheckCircle, Clock, BarChart3, User, Calendar } from 'lucide-react';
import { Card } from '../components/ui';
import AdminNav from '../components/AdminNav';
import { useToast } from '../contexts/ToastContext';

interface Feedback {
  id: number;
  user_id: number;
  category: 'bug' | 'feature' | 'improvement' | 'question' | 'other';
  subject: string;
  message: string;
  platform: string;
  url?: string;
  status: 'new' | 'reviewing' | 'resolved' | 'closed';
  admin_notes?: string;
  created_at: string;
  updated_at: string;
  // User info
  first_name?: string;
  last_name?: string;
  email?: string;
}

interface FeedbackStats {
  total: number;
  by_status: {
    new: number;
    reviewing: number;
    resolved: number;
    closed: number;
  };
  by_category: {
    bug: number;
    feature: number;
    improvement: number;
    question: number;
    other: number;
  };
}

export default function AdminFeedback() {
  const toast = useToast();
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const params: any = { limit: 100 };
        if (filterStatus !== 'all') params.status = filterStatus;
        if (filterCategory !== 'all') params.category = filterCategory;

        const [feedbackRes, statsRes] = await Promise.all([
          adminApi.listFeedback(params),
          adminApi.getFeedbackStats(),
        ]);
        if (!cancelled) {
          setFeedback(feedbackRes.data.feedback || []);
          setStats(statsRes.data);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load feedback:', error);
          toast.error('Failed to load feedback. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [filterStatus, filterCategory]);

  const loadFeedback = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 100 };
      if (filterStatus !== 'all') params.status = filterStatus;
      if (filterCategory !== 'all') params.category = filterCategory;

      const response = await adminApi.listFeedback(params);
      setFeedback(response.data.feedback || []);
    } catch (error) {
      console.error('Failed to load feedback:', error);
      toast.error('Failed to load feedback. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await adminApi.getFeedbackStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load feedback stats:', error);
    }
  };

  const handleUpdateStatus = async (feedbackId: number, newStatus: string) => {
    setUpdatingStatus(true);
    try {
      await adminApi.updateFeedbackStatus(feedbackId, newStatus, adminNotes || undefined);
      toast.success(`Feedback marked as ${newStatus}`);
      setSelectedFeedback(null);
      setAdminNotes('');
      loadFeedback();
      loadStats();
    } catch (error) {
      console.error('Failed to update feedback status:', error);
      toast.error('Failed to update feedback status. Please try again.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'bug': return '#EF4444';
      case 'feature': return '#3B82F6';
      case 'improvement': return '#10B981';
      case 'question': return '#F59E0B';
      case 'other': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return '#F59E0B';
      case 'reviewing': return '#3B82F6';
      case 'resolved': return '#10B981';
      case 'closed': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const filteredFeedback = feedback;

  return (
    <div className="space-y-6">
      <AdminNav />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
          Feedback Management
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Review and manage user feedback submissions
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: 'var(--surfaceElev)' }}
              >
                <MessageCircle className="w-5 h-5" style={{ color: 'var(--accent)' }} />
              </div>
              <div>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>Total</p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {stats.total}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}
              >
                <Clock className="w-5 h-5" style={{ color: '#F59E0B' }} />
              </div>
              <div>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>New</p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {stats.by_status.new}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}
              >
                <BarChart3 className="w-5 h-5" style={{ color: '#3B82F6' }} />
              </div>
              <div>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>Reviewing</p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {stats.by_status.reviewing}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}
              >
                <CheckCircle className="w-5 h-5" style={{ color: '#10B981' }} />
              </div>
              <div>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>Resolved</p>
                <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
                  {stats.by_status.resolved}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input w-full"
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="reviewing">Reviewing</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Category
            </label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="input w-full"
            >
              <option value="all">All Categories</option>
              <option value="bug">Bug</option>
              <option value="feature">Feature</option>
              <option value="improvement">Improvement</option>
              <option value="question">Question</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Feedback List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : filteredFeedback.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <MessageCircle className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
              No Feedback Found
            </h3>
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Try adjusting your filters or wait for users to submit feedback
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredFeedback.map((item) => (
            <Card key={item.id}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="px-2 py-1 text-xs font-medium rounded-full capitalize"
                      style={{
                        backgroundColor: `${getCategoryColor(item.category)}20`,
                        color: getCategoryColor(item.category),
                      }}
                    >
                      {item.category}
                    </span>
                    <span
                      className="px-2 py-1 text-xs font-medium rounded-full capitalize"
                      style={{
                        backgroundColor: `${getStatusColor(item.status)}20`,
                        color: getStatusColor(item.status),
                      }}
                    >
                      {item.status}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--muted)' }}>
                      #{item.id}
                    </span>
                  </div>

                  {/* Subject */}
                  <h3 className="font-semibold mb-2" style={{ color: 'var(--text)' }}>
                    {item.subject || 'No subject'}
                  </h3>

                  {/* Message */}
                  <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
                    {item.message.length > 150 ? `${item.message.substring(0, 150)}...` : item.message}
                  </p>

                  {/* Meta Info */}
                  <div className="flex flex-wrap gap-4 text-xs" style={{ color: 'var(--muted)' }}>
                    {item.first_name && item.last_name && (
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span>{item.first_name} {item.last_name}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                    {item.platform && (
                      <span className="px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--surfaceElev)' }}>
                        {item.platform}
                      </span>
                    )}
                    {item.url && (
                      <span className="truncate max-w-[200px]">{item.url}</span>
                    )}
                  </div>

                  {/* Admin Notes */}
                  {item.admin_notes && (
                    <div
                      className="mt-3 p-3 rounded-lg text-sm"
                      style={{ backgroundColor: 'var(--surfaceElev)', borderLeft: '3px solid var(--accent)' }}
                    >
                      <p className="font-medium mb-1" style={{ color: 'var(--text)' }}>Admin Notes:</p>
                      <p style={{ color: 'var(--muted)' }}>{item.admin_notes}</p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => {
                      setSelectedFeedback(item);
                      setAdminNotes(item.admin_notes || '');
                    }}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                    style={{
                      backgroundColor: 'var(--accent)',
                      color: '#FFFFFF',
                    }}
                  >
                    Manage
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Manage Modal */}
      {selectedFeedback && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
          onClick={() => setSelectedFeedback(null)}
        >
          <div
            className="w-full max-w-2xl rounded-[14px] shadow-xl p-6"
            style={{ backgroundColor: 'var(--surface)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold mb-4" style={{ color: 'var(--text)' }}>
              Manage Feedback #{selectedFeedback.id}
            </h2>

            <div className="space-y-4 mb-6">
              <div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>Subject</p>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>{selectedFeedback.subject || 'No subject'}</p>
              </div>

              <div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>Message</p>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>{selectedFeedback.message}</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
                  Admin Notes
                </label>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  placeholder="Add notes about this feedback..."
                  className="input w-full resize-none"
                  rows={4}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {selectedFeedback.status !== 'reviewing' && (
                <button
                  onClick={() => handleUpdateStatus(selectedFeedback.id, 'reviewing')}
                  disabled={updatingStatus}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  style={{ backgroundColor: '#3B82F6', color: '#FFFFFF' }}
                >
                  Mark as Reviewing
                </button>
              )}
              {selectedFeedback.status !== 'resolved' && (
                <button
                  onClick={() => handleUpdateStatus(selectedFeedback.id, 'resolved')}
                  disabled={updatingStatus}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  style={{ backgroundColor: '#10B981', color: '#FFFFFF' }}
                >
                  Mark as Resolved
                </button>
              )}
              {selectedFeedback.status !== 'closed' && (
                <button
                  onClick={() => handleUpdateStatus(selectedFeedback.id, 'closed')}
                  disabled={updatingStatus}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  style={{ backgroundColor: '#6B7280', color: '#FFFFFF' }}
                >
                  Close
                </button>
              )}
              <button
                onClick={() => setSelectedFeedback(null)}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-colors ml-auto"
                style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--text)' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

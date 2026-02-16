import { useState, useEffect } from 'react';
import { usePageTitle } from '../hooks/usePageTitle';
import { adminApi } from '../api/client';
import { Trash2, MessageSquare, User } from 'lucide-react';
import { Card, SecondaryButton } from '../components/ui';
import AdminNav from '../components/AdminNav';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../contexts/ToastContext';

interface Comment {
  id: number;
  user_id: number;
  activity_type: string;
  activity_id: number;
  comment_text: string;
  created_at: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export default function AdminContent() {
  usePageTitle('Content Moderation');
  const toast = useToast();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [confirmDelete, setConfirmDelete] = useState<{ id: number; text: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await adminApi.listComments({ limit: 100 });
        if (!cancelled) {
          setComments(response.data.comments || []);
          setTotal(response.data.total || 0);
        }
      } catch (error) {
        if (!cancelled) toast.error('Failed to load comments. Please try again.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, []);

  const loadComments = async () => {
    setLoading(true);
    try {
      const response = await adminApi.listComments({ limit: 100 });
      setComments(response.data.comments || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      toast.error('Failed to load comments. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const deleteComment = async () => {
    if (!confirmDelete) return;
    try {
      await adminApi.deleteComment(confirmDelete.id);
      toast.success('Comment deleted successfully!');
      setConfirmDelete(null);
      loadComments();
    } catch (error) {
      toast.error('Failed to delete comment. Please try again.');
      setConfirmDelete(null);
    }
  };

  const getActivityTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      session: 'Training Session',
      readiness: 'Readiness Check',
      rest: 'Rest Day',
    };
    return labels[type] || type;
  };

  return (
    <div className="space-y-6">
      <AdminNav />

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>
          Content Moderation
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
          Review and moderate user-generated content
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>Total Comments</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
                {total}
              </p>
            </div>
            <MessageSquare className="w-8 h-8" style={{ color: 'var(--primary)' }} />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>Showing</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
                {comments.length}
              </p>
            </div>
            <MessageSquare className="w-8 h-8" style={{ color: 'var(--muted)' }} />
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm" style={{ color: 'var(--muted)' }}>Active</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--text)' }}>
                {comments.length}
              </p>
            </div>
            <MessageSquare className="w-8 h-8" style={{ color: 'var(--success)' }} />
          </div>
        </Card>
      </div>

      {/* Comments List */}
      <Card>
        <div className="mb-4">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>
            Recent Comments
          </h2>
        </div>

        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : comments.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--muted)' }} />
            <p style={{ color: 'var(--muted)' }}>No comments found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className="p-4 rounded-lg border"
                style={{ borderColor: 'var(--border)', backgroundColor: 'var(--surfaceElev)' }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* User Info */}
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4" style={{ color: 'var(--muted)' }} />
                      <span className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {comment.first_name} {comment.last_name}
                      </span>
                      <span className="text-xs" style={{ color: 'var(--muted)' }}>
                        ({comment.email})
                      </span>
                    </div>

                    {/* Comment Text */}
                    <p className="text-sm mb-2" style={{ color: 'var(--text)' }}>
                      {comment.comment_text}
                    </p>

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
                      <span>
                        On: {getActivityTypeLabel(comment.activity_type)} #{comment.activity_id}
                      </span>
                      <span>•</span>
                      <span>{new Date(comment.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span>ID: {comment.id}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <SecondaryButton
                    onClick={() => setConfirmDelete({ id: comment.id, text: comment.comment_text })}
                    className="flex items-center gap-2"
                    aria-label={`Delete comment from ${comment.first_name} ${comment.last_name}`}
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </SecondaryButton>
                </div>
              </div>
            ))}
          </div>
        )}

        {comments.length > 0 && total > comments.length && (
          <div className="mt-4 text-center">
            <p className="text-sm" style={{ color: 'var(--muted)' }}>
              Showing {comments.length} of {total} comments
            </p>
          </div>
        )}
      </Card>

      {/* Future Features Placeholder */}
      <Card>
        <div className="text-center py-8">
          <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
            Coming Soon
          </h3>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            • Reported content queue<br />
            • Photo moderation<br />
            • Bulk actions<br />
            • Content filters
          </p>
        </div>
      </Card>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={deleteComment}
        title="Delete Comment"
        message={`Are you sure you want to delete this comment? "${confirmDelete?.text?.substring(0, 50)}${(confirmDelete?.text?.length || 0) > 50 ? '...' : ''}"`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}

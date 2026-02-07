import { useState, useEffect, memo } from 'react';
import { Edit2, Trash2, Send } from 'lucide-react';
import { socialApi } from '../api/client';
import type { ActivityComment } from '../types';
import ConfirmDialog from './ConfirmDialog';
import { useToast } from '../contexts/ToastContext';

interface CommentSectionProps {
  activityType: 'session' | 'readiness' | 'rest';
  activityId: number;
  currentUserId: number;
  isOpen: boolean;
}

const CommentSection = memo(function CommentSection({
  activityType,
  activityId,
  currentUserId,
  isOpen,
}: CommentSectionProps) {
  const [comments, setComments] = useState<ActivityComment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [commentToDelete, setCommentToDelete] = useState<number | null>(null);
  const toast = useToast();

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    const doLoad = async () => {
      setLoading(true);
      try {
        const response = await socialApi.getComments(activityType, activityId);
        if (!cancelled) setComments(response.data?.comments ?? []);
      } catch (error) {
        if (!cancelled) console.error('Error loading comments:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    doLoad();
    return () => { cancelled = true; };
  }, [isOpen, activityType, activityId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const response = await socialApi.getComments(activityType, activityId);
      setComments(response.data?.comments ?? []);
    } catch (error) {
      console.error('Error loading comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || submitting) return;

    setSubmitting(true);
    try {
      await socialApi.addComment(activityType, activityId, newComment.trim());
      setNewComment('');
      await loadComments();
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (comment: ActivityComment) => {
    setEditingCommentId(comment.id);
    setEditingText(comment.comment_text);
  };

  const handleUpdate = async (commentId: number) => {
    if (!editingText.trim() || submitting) return;

    setSubmitting(true);
    try {
      await socialApi.updateComment(commentId, editingText.trim());
      setEditingCommentId(null);
      setEditingText('');
      await loadComments();
    } catch (error) {
      console.error('Error updating comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!commentToDelete) return;

    try {
      await socialApi.deleteComment(commentToDelete);
      await loadComments();
      toast.success('Comment deleted successfully');
    } catch (error) {
      console.error('Error deleting comment:', error);
      toast.error('Failed to delete comment');
    } finally {
      setCommentToDelete(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (!isOpen) return null;

  return (
    <div className="mt-4 pt-4 border-t border-[var(--border)]">
      <h4 className="text-sm font-semibold text-[var(--text)] mb-3">
        Comments ({comments.length})
      </h4>

      {loading ? (
        <div className="text-sm text-[var(--muted)]">Loading comments...</div>
      ) : (
        <>
          {/* Comment list */}
          <div className="space-y-3 mb-4">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className="bg-[var(--surfaceElev)] rounded-lg p-3"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-[var(--text)]">
                      {comment.first_name ?? 'Unknown'} {comment.last_name ?? 'User'}
                    </span>
                    <span className="text-xs text-[var(--muted)] ml-2">
                      {formatDate(comment.created_at ?? new Date().toISOString())}
                      {comment.edited_at && ' (edited)'}
                    </span>
                  </div>

                  {comment.user_id === currentUserId && (
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleEdit(comment)}
                        className="p-1 text-[var(--muted)] hover:text-[var(--accent)]"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setCommentToDelete(comment.id)}
                        className="p-1 text-[var(--muted)] hover:text-[var(--error)]"
                        aria-label="Delete comment"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {editingCommentId === comment.id ? (
                  <div className="mt-2">
                    <textarea
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg bg-[var(--surface)] text-[var(--text)]"
                      rows={2}
                      maxLength={1000}
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleUpdate(comment.id)}
                        disabled={submitting}
                        className="px-3 py-1 text-sm bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingCommentId(null);
                          setEditingText('');
                        }}
                        className="px-3 py-1 text-sm bg-[var(--surfaceElev)] text-[var(--text)] rounded-lg hover:opacity-80"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-[var(--text)] whitespace-pre-wrap">
                    {comment.comment_text}
                  </p>
                )}
              </div>
            ))}

            {comments.length === 0 && (
              <p className="text-sm text-[var(--muted)] italic">
                No comments yet. Be the first to comment!
              </p>
            )}
          </div>

          {/* Add comment form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 px-3 py-2 text-sm border border-[var(--border)] rounded-lg bg-[var(--surface)] text-[var(--text)] placeholder-[var(--muted)]"
              maxLength={1000}
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-4 py-2 bg-[var(--accent)] text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </>
      )}

      <ConfirmDialog
        isOpen={commentToDelete !== null}
        onClose={() => setCommentToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Comment"
        message="Are you sure you want to delete this comment? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
});

export default CommentSection;

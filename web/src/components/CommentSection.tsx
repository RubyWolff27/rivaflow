import { useState, useEffect, memo } from 'react';
import { Edit2, Trash2, Send } from 'lucide-react';
import { socialApi } from '../api/client';
import type { ActivityComment } from '../types';

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

  useEffect(() => {
    if (isOpen) {
      loadComments();
    }
  }, [isOpen, activityType, activityId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const response = await socialApi.getComments(activityType, activityId);
      setComments(response.data.comments || []);
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

  const handleDelete = async (commentId: number) => {
    if (!confirm('Delete this comment?')) return;

    try {
      await socialApi.deleteComment(commentId);
      await loadComments();
    } catch (error) {
      console.error('Error deleting comment:', error);
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
    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
        Comments ({comments.length})
      </h4>

      {loading ? (
        <div className="text-sm text-gray-500 dark:text-gray-400">Loading comments...</div>
      ) : (
        <>
          {/* Comment list */}
          <div className="space-y-3 mb-4">
            {comments.map((comment) => (
              <div
                key={comment.id}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {comment.first_name} {comment.last_name}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                      {formatDate(comment.created_at)}
                      {comment.edited_at && ' (edited)'}
                    </span>
                  </div>

                  {comment.user_id === currentUserId && (
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleEdit(comment)}
                        className="p-1 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(comment.id)}
                        className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
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
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                      rows={2}
                      maxLength={1000}
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleUpdate(comment.id)}
                        disabled={submitting}
                        className="px-3 py-1 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingCommentId(null);
                          setEditingText('');
                        }}
                        className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {comment.comment_text}
                  </p>
                )}
              </div>
            ))}

            {comments.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 italic">
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
              className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              maxLength={1000}
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </>
      )}
    </div>
  );
});

export default CommentSection;

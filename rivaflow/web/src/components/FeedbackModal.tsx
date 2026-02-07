import { useState } from 'react';
import { X, Bug, Lightbulb, MessageCircle } from 'lucide-react';
import { feedbackApi } from '../api/client';
import { useToast } from '../contexts/ToastContext';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type FeedbackType = 'bug' | 'feature' | 'improvement' | 'question' | 'other';

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('improvement');
  const [summary, setSummary] = useState('');
  const [details, setDetails] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const toast = useToast();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSubmitting(true);
      await feedbackApi.submit({
        category: feedbackType,
        subject: summary,
        message: details || summary,
        platform: 'web',
        url: window.location.pathname,
      });

      toast.success('Thank you for your feedback!');

      // Reset form and close
      setSummary('');
      setDetails('');
      setFeedbackType('improvement');
      onClose();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      toast.error('Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const feedbackOptions = [
    { type: 'bug' as FeedbackType, icon: Bug, label: 'Bug', description: 'Something broke' },
    { type: 'feature' as FeedbackType, icon: Lightbulb, label: 'Feature', description: 'Something you want' },
    { type: 'general' as FeedbackType, icon: MessageCircle, label: 'Feedback', description: 'General thoughts' },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-[14px] shadow-xl"
        style={{ backgroundColor: 'var(--surface)' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="feedback-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: 'var(--border)' }}>
          <h2 id="feedback-title" className="text-xl font-bold" style={{ color: 'var(--text)' }}>
            📝 RivaFlow Feedback
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[var(--surfaceElev)] transition-colors"
            aria-label="Close feedback form"
          >
            <X className="w-5 h-5" style={{ color: 'var(--muted)' }} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Feedback Type */}
          <div>
            <label className="block text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>
              What type of feedback?
            </label>
            <div className="grid grid-cols-1 gap-2">
              {feedbackOptions.map((option) => {
                const Icon = option.icon;
                const isSelected = feedbackType === option.type;
                return (
                  <button
                    key={option.type}
                    type="button"
                    onClick={() => setFeedbackType(option.type)}
                    className="flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left"
                    style={{
                      borderColor: isSelected ? 'var(--accent)' : 'var(--border)',
                      backgroundColor: isSelected ? 'var(--surfaceElev)' : 'transparent',
                    }}
                  >
                    <Icon
                      className="w-5 h-5 flex-shrink-0"
                      style={{ color: isSelected ? 'var(--accent)' : 'var(--muted)' }}
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm" style={{ color: 'var(--text)' }}>
                        {option.label}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--muted)' }}>
                        {option.description}
                      </div>
                    </div>
                    {isSelected && (
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: 'var(--accent)' }}
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Summary */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Short summary (1 line) <span style={{ color: 'var(--error)' }}>*</span>
            </label>
            <input
              type="text"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="e.g., App crashes when logging yoga"
              className="input w-full"
              required
              maxLength={100}
            />
          </div>

          {/* Details */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text)' }}>
              Details (optional)
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Add any additional context, steps to reproduce, or suggestions..."
              className="input w-full resize-none"
              rows={4}
              maxLength={1000}
            />
            <p className="text-xs mt-1" style={{ color: 'var(--muted)' }}>
              {details.length}/1000 characters
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: 'var(--surfaceElev)',
                color: 'var(--text)',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!summary.trim() || submitting}
              className="flex-1 px-4 py-2.5 rounded-lg font-medium transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#FFFFFF',
              }}
            >
              {submitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

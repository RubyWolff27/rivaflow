import { useState } from 'react';
import { X, Bug, Lightbulb, MessageCircle, ExternalLink } from 'lucide-react';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type FeedbackType = 'bug' | 'feature' | 'general';

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('general');
  const [summary, setSummary] = useState('');
  const [details, setDetails] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Generate GitHub issue title and body
    const emoji = feedbackType === 'bug' ? '🐛' : feedbackType === 'feature' ? '💡' : '💬';
    const label = feedbackType === 'bug' ? 'bug' : feedbackType === 'feature' ? 'enhancement' : 'feedback';

    const title = `${emoji} ${summary}`;
    const body = `## Type
${feedbackType === 'bug' ? 'Bug Report' : feedbackType === 'feature' ? 'Feature Request' : 'General Feedback'}

## Summary
${summary}

${details ? `## Details\n${details}\n\n` : ''}---
**Version:** v0.1.0
**Submitted via:** Web Feedback Form
**Date:** ${new Date().toISOString().split('T')[0]}`;

    // Encode for URL
    const githubUrl = `https://github.com/RubyWolff27/rivaflow/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}&labels=${label}`;

    // Open GitHub in new tab
    window.open(githubUrl, '_blank', 'noopener,noreferrer');

    // Reset form and close
    setSummary('');
    setDetails('');
    setFeedbackType('general');
    onClose();
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
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
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

          {/* Info */}
          <div
            className="p-3 rounded-lg text-xs"
            style={{ backgroundColor: 'var(--surfaceElev)', color: 'var(--muted)' }}
          >
            <p className="flex items-center gap-2">
              <ExternalLink className="w-3.5 h-3.5" />
              This will open GitHub in a new tab. Just click "Submit new issue" to send.
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
              disabled={!summary.trim()}
              className="flex-1 px-4 py-2.5 rounded-lg font-medium transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: 'var(--accent)',
                color: '#FFFFFF',
              }}
            >
              Submit Feedback
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

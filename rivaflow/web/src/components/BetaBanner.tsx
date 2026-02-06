import { useState } from 'react';
import { MessageSquare, X } from 'lucide-react';
import FeedbackModal from './FeedbackModal';

export default function BetaBanner() {
  const [isVisible, setIsVisible] = useState(true);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  if (!isVisible) return null;

  return (
    <>
      <div
        className="w-full py-2 px-4 flex items-center justify-center gap-3 text-sm border-b"
        style={{
          backgroundColor: 'var(--accent)',
          color: '#FFFFFF',
          borderColor: 'var(--border)',
        }}
      >
        <span className="font-medium">
          Beta v0.2.0 — Testing in progress
        </span>
        <button
          onClick={() => setFeedbackOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1 rounded-md font-medium hover:opacity-90 transition-opacity"
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          }}
          aria-label="Give feedback"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Give Feedback
        </button>
        <button
          onClick={() => setIsVisible(false)}
          className="ml-2 p-1 rounded hover:opacity-80 transition-opacity"
          aria-label="Dismiss banner"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <FeedbackModal
        isOpen={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
      />
    </>
  );
}

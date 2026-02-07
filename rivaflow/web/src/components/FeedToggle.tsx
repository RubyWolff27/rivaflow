import { User, Users } from 'lucide-react';

interface FeedToggleProps {
  view: 'my' | 'friends';
  onChange: (view: 'my' | 'friends') => void;
}

export default function FeedToggle({ view, onChange }: FeedToggleProps) {
  return (
    <div className="flex gap-2 mb-6">
      <button
        onClick={() => onChange('my')}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
          view === 'my'
            ? 'bg-[var(--accent)] text-white shadow-sm'
            : 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--surfaceElev)]'
        }`}
      >
        <User className="w-4 h-4" />
        My Activities
      </button>

      <button
        onClick={() => onChange('friends')}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
          view === 'friends'
            ? 'bg-[var(--accent)] text-white shadow-sm'
            : 'bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--surfaceElev)]'
        }`}
      >
        <Users className="w-4 h-4" />
        Friends Activities
      </button>
    </div>
  );
}

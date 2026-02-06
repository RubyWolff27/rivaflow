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
            ? 'bg-primary-600 text-white shadow-sm'
            : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
        }`}
      >
        <User className="w-4 h-4" />
        My Activities
      </button>

      <button
        onClick={() => onChange('friends')}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
          view === 'friends'
            ? 'bg-primary-600 text-white shadow-sm'
            : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
        }`}
      >
        <Users className="w-4 h-4" />
        Friends Activities
      </button>
    </div>
  );
}

import { User, Users } from 'lucide-react';

interface FeedToggleProps {
  view: 'my' | 'contacts';
  onChange: (view: 'my' | 'contacts') => void;
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
        onClick={() => onChange('contacts')}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
          view === 'contacts'
            ? 'bg-primary-600 text-white shadow-sm'
            : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
        }`}
      >
        <Users className="w-4 h-4" />
        Contacts Activities
      </button>
    </div>
  );
}

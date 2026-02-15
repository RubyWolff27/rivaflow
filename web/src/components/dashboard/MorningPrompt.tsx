import { Sun } from 'lucide-react';

export default function MorningPrompt({ onNavigate }: { onNavigate: () => void }) {
  return (
    <div
      className="mt-3 rounded-xl overflow-hidden"
      style={{ backgroundColor: 'var(--surfaceElev)', border: '1px solid var(--border)' }}
    >
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-2">
          <Sun className="w-4 h-4" style={{ color: '#F59E0B' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Morning Check-in
          </span>
        </div>
        <button
          onClick={onNavigate}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
          style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
        >
          Check in
        </button>
      </div>
      <p className="px-3 pb-3 text-xs" style={{ color: 'var(--muted)' }}>
        Log how you're feeling to get personalized training guidance
      </p>
    </div>
  );
}

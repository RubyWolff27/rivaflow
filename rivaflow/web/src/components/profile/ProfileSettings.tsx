import { Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ProfileSettings() {
  return (
    <Link to="/coach-settings" className="card block hover:border-[var(--accent)] transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-[var(--accent)]" />
          <div>
            <h2 className="text-lg font-semibold">Grapple AI Coach Settings</h2>
            <p className="text-sm text-[var(--muted)]">
              Personalize how Grapple coaches you — training mode, style, injuries, and more
            </p>
          </div>
        </div>
        <span className="text-[var(--muted)]">&rarr;</span>
      </div>
    </Link>
  );
}

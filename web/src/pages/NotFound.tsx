import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

function NotFound() {
  usePageTitle('Page Not Found');
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <img src="/logo.webp" alt="RivaFlow" className="w-16 h-16 rounded-2xl mb-6 opacity-40" />
      <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--muted)' }}>404</h1>
      <p className="text-sm mb-6 max-w-sm" style={{ color: 'var(--muted)' }}>
        This page doesn't exist or has been moved.
      </p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-6 py-3 rounded-[14px] font-semibold text-sm"
        style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
      >
        <Home className="w-4 h-4" />
        Back to Dashboard
      </Link>
    </div>
  );
}

export default NotFound;

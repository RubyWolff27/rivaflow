import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <h1 className="text-6xl font-bold mb-4" style={{ color: 'var(--accent)' }}>404</h1>
      <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--text)' }}>Page Not Found</h2>
      <p className="mb-6 max-w-md" style={{ color: 'var(--muted)' }}>
        The page you're looking for doesn't exist or has been moved.
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

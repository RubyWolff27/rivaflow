import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from './Layout';

/**
 * PublicDocLayout — auth-aware wrapper for public-facing doc pages
 * (Privacy, Terms, etc.) that must be accessible WITHOUT an account.
 *
 * - Logged-in users get the full app Layout (bottom nav, header).
 * - Logged-out users get a thin marketing-style top bar.
 *
 * Added 2026-05-14 to fix:
 *   (a) App Store compliance — Privacy Policy must be publicly accessible.
 *   (b) Trust / conversion — visitors clicking footer "Privacy" / "Terms"
 *       previously bounced to /login, breaking the marketing flow.
 */
export default function PublicDocLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (user) {
    return <Layout>{children}</Layout>;
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--background)', color: 'var(--text)' }}>
      <header className="border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <img src="/logo.webp" alt="RivaFlow" className="w-9 h-9 rounded-lg" />
            <span className="text-xl font-black tracking-tight" style={{ color: 'var(--text)' }}>
              RIVAFLOW
            </span>
          </Link>
          <nav className="flex items-center gap-3">
            <Link
              to="/login"
              className="text-sm font-medium px-4 py-2 rounded-lg transition-opacity hover:opacity-70"
              style={{ color: 'var(--text)' }}
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="text-sm font-semibold px-4 py-2 rounded-lg text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: 'var(--accent)' }}
            >
              Start free
            </Link>
          </nav>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-10">
        {children}
      </main>
    </div>
  );
}

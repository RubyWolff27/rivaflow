import { useAuth } from '../contexts/AuthContext';
import { lazy, Suspense } from 'react';
import PageSkeleton from './PageSkeleton';
import Layout from './Layout';

/**
 * RootRoute — auth-aware handler for the "/" path.
 *
 * - If the user is logged in → show the Dashboard (wrapped in Layout so
 *   bottom nav + header are visible, matching the rest of the app).
 * - If the user is logged out → show the public Landing marketing page
 *   (no auth wrapper, no bottom nav — it's a marketing surface).
 * - While auth state is loading → show the page skeleton so we don't
 *   briefly flash the wrong page on every refresh.
 *
 * Added 2026-04-05 as part of the hobbyist-positioning marketing launch.
 * Before this, the "/" path was inside PrivateRoute which bounced
 * unauthenticated visitors to /login with zero context. Conversion
 * ceiling was literally zero.
 */

const Dashboard = lazy(() => import('../pages/Dashboard'));
const Landing = lazy(() => import('../pages/Landing'));

export default function RootRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <PageSkeleton />;
  }

  if (!user) {
    // Public landing page — no Layout wrapper, no bottom nav.
    return (
      <Suspense fallback={<PageSkeleton />}>
        <Landing />
      </Suspense>
    );
  }

  // Logged-in dashboard — matches what PrivateRoute + Layout used to render.
  return (
    <Layout>
      <Suspense fallback={<PageSkeleton />}>
        <Dashboard />
      </Suspense>
    </Layout>
  );
}

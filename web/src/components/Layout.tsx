import { useState, useRef, memo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Home, BarChart3, Activity, Shield, Sparkles, Target, Calendar, Download, Trophy } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuickLog from './QuickLog';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import PageTransition from './ui/PageTransition';
// Memoize Layout to prevent unnecessary re-renders
const Layout = memo(function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [quickLogOpen, setQuickLogOpen] = useState(false);
  const mainContentRef = useRef<HTMLElement>(null);

  const skipToContent = () => {
    mainContentRef.current?.focus();
  };

  // Primary navigation — clean core loop for users
  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Sessions', href: '/sessions', icon: Calendar },
    { name: 'Progress', href: '/reports', icon: BarChart3 },
  ];

  // Secondary sections — shown in sidebar collapsibles and "You" sheet on mobile
  const moreNavSections = [
    {
      label: 'Training',
      items: [
        { name: 'Goals', href: '/goals', icon: Trophy },
        { name: 'Grapple AI', href: '/grapple', icon: Sparkles },
        { name: 'Readiness', href: '/readiness', icon: Activity },
        { name: 'Glossary', href: '/glossary', icon: Target },
        { name: 'Import', href: '/import', icon: Download },
      ],
    },
    ...(user?.is_admin ? [{
      label: 'Admin',
      items: [
        { name: 'Admin Panel', href: '/admin', icon: Shield },
      ],
    }] : []),
  ];

  return (
    <div className="min-h-screen app-bg overflow-x-hidden">
      {/* Skip to content link for screen readers */}
      <a
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          skipToContent();
        }}
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg"
        style={{
          backgroundColor: 'var(--accent)',
          color: '#FFFFFF',
        }}
      >
        Skip to main content
      </a>

      {/* Layout: Sidebar + Main + BottomNav */}
      <div className="flex">
        <Sidebar
          navigation={navigation}
          moreNavSections={moreNavSections}
          onQuickLog={() => setQuickLogOpen(true)}
        />

        <div className="flex-1 min-w-0 flex flex-col">
          {/* Main Content */}
          <main
            id="main-content"
            ref={mainContentRef}
            className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 pb-24 md:pb-8"
            tabIndex={-1}
          >
            <PageTransition>{children}</PageTransition>
          </main>

          {/* Footer — hidden on dashboard */}
          {location.pathname !== '/' && (
            <footer className="mt-12 py-6 px-4 text-center hidden md:block" style={{ borderTop: '1px solid var(--border)' }}>
              <div className="flex items-center justify-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
                <span>RIVAFLOW</span>
                <span>&middot;</span>
                <a href="/terms" className="hover:underline" style={{ color: 'var(--muted)' }}>Terms</a>
                <span>&middot;</span>
                <a href="/privacy" className="hover:underline" style={{ color: 'var(--muted)' }}>Privacy</a>
                <span>&middot;</span>
                <a href="/contact" className="hover:underline" style={{ color: 'var(--muted)' }}>Contact</a>
                <span>&middot;</span>
                <a href="/faq" className="hover:underline" style={{ color: 'var(--muted)' }}>FAQ</a>
              </div>
            </footer>
          )}
        </div>
      </div>

      {/* Mobile Bottom Nav */}
      <BottomNav
        navigation={navigation}
        moreNavSections={moreNavSections}
        onQuickLog={() => setQuickLogOpen(true)}
      />

      {/* Quick Log Modal */}
      <QuickLog
        isOpen={quickLogOpen}
        onClose={() => setQuickLogOpen(false)}
        onSuccess={(sessionId?: number) => {
          if (sessionId) {
            navigate(`/session/${sessionId}`);
          } else if (location.pathname === '/') {
            navigate(0);
          }
        }}
      />
    </div>
  );
});

export default Layout;

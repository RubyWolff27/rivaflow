import { useState, useEffect, useRef, memo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Plus, BarChart3, Book, Users, BookOpen, Video, Activity, Shield, Calendar, Sparkles, Trophy, HelpCircle, MessageSquare, Target } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuickLog from './QuickLog';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import PageTransition from './ui/PageTransition';
import { notificationsApi } from '../api/client';
import BetaBanner from './BetaBanner';

// Memoize Layout to prevent unnecessary re-renders
const Layout = memo(function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [quickLogOpen, setQuickLogOpen] = useState(false);
  const [notificationCounts, setNotificationCounts] = useState({ feed_unread: 0, friend_requests: 0, total: 0 });
  const mainContentRef = useRef<HTMLElement>(null);

  const skipToContent = () => {
    mainContentRef.current?.focus();
  };

  // Fetch notification counts
  useEffect(() => {
    let cancelled = false;
    const fetchNotifications = async () => {
      try {
        const response = await notificationsApi.getCounts();
        if (!cancelled) setNotificationCounts(response.data);
      } catch (error) {
        if (!cancelled) console.error('Error fetching notifications:', error);
      }
    };

    fetchNotifications();

    // Refresh every 60 seconds
    const interval = setInterval(fetchNotifications, 60000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // Mark notifications as read when navigating to Feed or Friends
  useEffect(() => {
    let cancelled = false;
    const markNotificationsRead = async () => {
      try {
        if (location.pathname === '/feed') {
          await notificationsApi.markFeedAsRead();
          if (cancelled) return;
          const response = await notificationsApi.getCounts();
          if (!cancelled) setNotificationCounts(response.data);
        } else if (location.pathname === '/friends') {
          await notificationsApi.markFollowsAsRead();
          if (cancelled) return;
          const response = await notificationsApi.getCounts();
          if (!cancelled) setNotificationCounts(response.data);
        }
      } catch (error) {
        if (!cancelled) console.error('Error marking notifications as read:', error);
      }
    };

    markNotificationsRead();
    return () => { cancelled = true; };
  }, [location.pathname]);

  // Primary navigation - most important features only
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Feed', href: '/feed', icon: Activity, badge: notificationCounts.feed_unread },
    { name: 'Log', href: '/log', icon: Plus },
    { name: 'Progress', href: '/reports', icon: BarChart3 },
    { name: 'Friends', href: '/friends', icon: Users, badge: notificationCounts.friend_requests },
  ];

  // Secondary navigation - organized into sections
  const moreNavSections = [
    {
      label: 'Training',
      items: [
        { name: 'Sessions', href: '/sessions', icon: Calendar },
        { name: 'Readiness', href: '/readiness', icon: Activity },
        { name: 'Events', href: '/events', icon: Trophy },
        { name: 'Grapple AI', href: '/grapple', icon: Sparkles },
        { name: 'My Game', href: '/my-game', icon: Target },
      ],
    },
    {
      label: 'Library',
      items: [
        { name: 'Techniques', href: '/techniques', icon: Book },
        { name: 'Glossary', href: '/glossary', icon: BookOpen },
        { name: 'Videos', href: '/videos', icon: Video },
      ],
    },
    {
      label: 'Community',
      items: [
        { name: 'Groups', href: '/groups', icon: Users },
      ],
    },
    {
      label: 'Support',
      items: [
        { name: 'FAQ', href: '/faq', icon: HelpCircle },
        { name: 'Contact', href: '/contact', icon: MessageSquare },
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
    <div className="min-h-screen app-bg">
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

      {/* Beta Feedback Banner */}
      <BetaBanner />

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

          {/* Footer */}
          <footer className="mt-12 py-6 px-4 text-center hidden md:block" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="flex items-center justify-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
              <span>RIVAFLOW</span>
              <span>&middot;</span>
              <a href="/terms" className="hover:underline" style={{ color: 'var(--muted)' }}>Terms</a>
              <span>&middot;</span>
              <a href="/privacy" className="hover:underline" style={{ color: 'var(--muted)' }}>Privacy</a>
              <span>&middot;</span>
              <a href="/contact" className="hover:underline" style={{ color: 'var(--muted)' }}>Contact</a>
            </div>
          </footer>
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
            navigate(0); // Force re-render without full page reload
          }
        }}
      />
    </div>
  );
});

export default Layout;

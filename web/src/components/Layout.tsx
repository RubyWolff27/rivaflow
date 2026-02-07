import { useState, useEffect, useRef, memo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Plus, BarChart3, Book, User, Users, Menu, X, LogOut, Grid, BookOpen, Video, Activity, Shield, Calendar, Sparkles, Trophy, HelpCircle, MessageSquare } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuickLog from './QuickLog';
import { notificationsApi } from '../api/client';
import BetaBanner from './BetaBanner';

// Memoize Layout to prevent unnecessary re-renders
const Layout = memo(function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [quickLogOpen, setQuickLogOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [notificationCounts, setNotificationCounts] = useState({ feed_unread: 0, friend_requests: 0, total: 0 });
  const moreMenuRef = useRef<HTMLDivElement>(null);
  const mainContentRef = useRef<HTMLElement>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

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

  // Close more menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(event.target as Node)) {
        setMoreMenuOpen(false);
      }
    };
    if (moreMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [moreMenuOpen]);

  // Primary navigation - most important features only
  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Feed', href: '/feed', icon: Activity, badge: notificationCounts.feed_unread },
    { name: 'Log', href: '/log', icon: Plus },
    { name: 'Analytics', href: '/reports', icon: BarChart3 },
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

  // Flat list for mobile and active state detection
  const moreNavigation = moreNavSections.flatMap(s => s.items);

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

      {/* Header */}
      <header className="bg-[var(--surface)] shadow-sm border-b border-[var(--border)]" style={{ position: 'relative', zIndex: 10 }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link
                to="/"
                className="text-xl font-bold hover:opacity-80 transition-opacity"
                style={{ color: 'var(--text)' }}
              >
                RIVAFLOW
              </Link>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-2" role="navigation" aria-label="Main navigation">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                const Icon = item.icon;
                const hasBadge = item.badge && item.badge > 0;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors relative"
                    style={{
                      color: isActive ? 'var(--accent)' : 'var(--muted)',
                      backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                    }}
                  >
                    <Icon className="w-4 h-4" />
                    {item.name}
                    {hasBadge && (
                      <span
                        className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold rounded-full"
                        style={{
                          backgroundColor: 'var(--error)',
                          color: '#FFFFFF',
                        }}
                      >
                        {item.badge > 99 ? '99+' : item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}

              {/* More Menu */}
              <div className="relative" ref={moreMenuRef}>
                <button
                  onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                  className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                  style={{
                    color: moreNavigation.some(item => location.pathname === item.href) ? 'var(--accent)' : 'var(--muted)',
                    backgroundColor: moreMenuOpen ? 'var(--surfaceElev)' : 'transparent',
                  }}
                  aria-label="More menu"
                  aria-expanded={moreMenuOpen}
                  aria-haspopup="true"
                >
                  <Grid className="w-4 h-4" />
                  More
                </button>

                {/* Dropdown */}
                {moreMenuOpen && (
                  <div
                    className="absolute top-full mt-2 right-0 rounded-[14px] shadow-lg py-2 min-w-[200px]"
                    style={{
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border)',
                      zIndex: 50,
                    }}
                    role="menu"
                    aria-label="More options"
                  >
                    {moreNavSections.map((section, sectionIndex) => (
                      <div key={section.label}>
                        {sectionIndex > 0 && (
                          <div className="my-1 mx-3" style={{ borderTop: '1px solid var(--border)' }} />
                        )}
                        <div className="px-4 pt-2 pb-1">
                          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
                            {section.label}
                          </span>
                        </div>
                        {section.items.map((item) => {
                          const isActive = location.pathname === item.href;
                          const Icon = item.icon;
                          return (
                            <Link
                              key={item.name}
                              to={item.href}
                              onClick={() => setMoreMenuOpen(false)}
                              className="flex items-center gap-3 px-4 py-2 text-sm font-medium transition-colors"
                              style={{
                                color: isActive ? 'var(--accent)' : 'var(--text)',
                                backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                              }}
                            >
                              <Icon className="w-4 h-4" />
                              {item.name}
                            </Link>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="ml-4 pl-4 flex items-center gap-2" style={{ borderLeft: '1px solid var(--border)' }}>
                <button
                  onClick={() => setQuickLogOpen(true)}
                  className="px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: '#FFFFFF',
                  }}
                >
                  <Plus className="w-4 h-4" />
                  Quick Log
                </button>
              </div>

              {/* User menu */}
              <div className="ml-2 pl-4 flex items-center gap-2" style={{ borderLeft: '1px solid var(--border)' }}>
                <Link
                  to="/profile"
                  className="p-2 rounded-lg transition-colors"
                  style={{ color: 'var(--muted)' }}
                  aria-label={`Profile - ${user?.first_name} ${user?.last_name}`}
                >
                  <User className="w-5 h-5" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg transition-colors"
                  style={{ color: 'var(--muted)' }}
                  aria-label="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </nav>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg"
              style={{ color: 'var(--text)' }}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden" style={{ borderTop: '1px solid var(--border)' }} role="navigation" aria-label="Mobile navigation">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                const Icon = item.icon;
                const hasBadge = item.badge && item.badge > 0;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-base font-medium relative"
                    style={{
                      color: isActive ? 'var(--accent)' : 'var(--text)',
                      backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                    }}
                  >
                    <Icon className="w-5 h-5" />
                    {item.name}
                    {hasBadge && (
                      <span
                        className="ml-auto flex items-center justify-center min-w-[20px] h-[20px] px-1.5 text-[10px] font-bold rounded-full"
                        style={{
                          backgroundColor: 'var(--error)',
                          color: '#FFFFFF',
                        }}
                      >
                        {item.badge > 99 ? '99+' : item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}

              {/* More Navigation for mobile - organized by section */}
              {moreNavSections.map((section) => (
                <div key={section.label} className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
                  <div className="px-3 pb-2">
                    <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                      {section.label}
                    </span>
                  </div>
                  {section.items.map((item) => {
                    const isActive = location.pathname === item.href;
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-2 rounded-lg text-base font-medium"
                        style={{
                          color: isActive ? 'var(--accent)' : 'var(--text)',
                          backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                        }}
                      >
                        <Icon className="w-5 h-5" />
                        {item.name}
                      </Link>
                    );
                  })}
                </div>
              ))}

              {/* Quick Actions for mobile */}
              <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setQuickLogOpen(true);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: '#FFFFFF',
                  }}
                >
                  <Plus className="w-5 h-5" />
                  Quick Log
                </button>
              </div>

              {/* User section for mobile */}
              <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-base font-medium"
                  style={{ color: 'var(--text)' }}
                >
                  <User className="w-5 h-5" />
                  Profile
                </Link>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-base font-medium"
                  style={{ color: 'var(--text)' }}
                >
                  <LogOut className="w-5 h-5" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main
        id="main-content"
        ref={mainContentRef}
        className="max-w-4xl mx-auto px-4 sm:px-6 py-8"
        tabIndex={-1}
      >
        {children}
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 px-4 text-center" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex items-center justify-center gap-4 text-xs" style={{ color: 'var(--muted)' }}>
          <span>RIVAFLOW</span>
          <span>·</span>
          <Link to="/terms" className="hover:underline" style={{ color: 'var(--muted)' }}>Terms</Link>
          <span>·</span>
          <Link to="/privacy" className="hover:underline" style={{ color: 'var(--muted)' }}>Privacy</Link>
          <span>·</span>
          <Link to="/contact" className="hover:underline" style={{ color: 'var(--muted)' }}>Contact</Link>
        </div>
      </footer>

      {/* Quick Log Modal */}
      <QuickLog
        isOpen={quickLogOpen}
        onClose={() => setQuickLogOpen(false)}
        onSuccess={() => {
          // Refresh if on dashboard
          if (location.pathname === '/') {
            navigate(0); // Force re-render without full page reload
          }
        }}
      />
    </div>
  );
});

export default Layout;

import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Plus, BarChart3, Book, User, Users, Menu, X, LogOut, ListOrdered, Grid, BookOpen, Video, MessageCircle, Activity, Shield } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import QuickLog from './QuickLog';

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [quickLogOpen, setQuickLogOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const moreMenuRef = useRef<HTMLDivElement>(null);
  const mainContentRef = useRef<HTMLElement>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const skipToContent = () => {
    mainContentRef.current?.focus();
  };

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
    { name: 'Log', href: '/log', icon: Plus },
    { name: 'Analytics', href: '/reports', icon: BarChart3 },
    { name: 'Techniques', href: '/techniques', icon: Book },
    { name: 'Friends', href: '/friends', icon: Users },
  ];

  // Secondary navigation - accessible via More menu
  const moreNavigation = [
    { name: 'Glossary', href: '/glossary', icon: BookOpen },
    { name: 'Videos', href: '/videos', icon: Video },
    { name: 'Chat', href: '/chat', icon: MessageCircle },
    { name: 'Readiness', href: '/readiness', icon: Activity },
    ...(user?.is_admin ? [{ name: 'Admin', href: '/admin', icon: Shield }] : []),
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
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
                    style={{
                      color: isActive ? 'var(--accent)' : 'var(--muted)',
                      backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                    }}
                  >
                    <Icon className="w-4 h-4" />
                    {item.name}
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
                    className="absolute top-full mt-2 right-0 rounded-[14px] shadow-lg py-2 min-w-[180px]"
                    style={{
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border)',
                      zIndex: 50,
                    }}
                    role="menu"
                    aria-label="More options"
                  >
                    {moreNavigation.map((item) => {
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
                <Link
                  to="/feed"
                  className="p-2 rounded-lg transition-colors"
                  style={{ color: location.pathname === '/feed' ? 'var(--accent)' : 'var(--muted)' }}
                  aria-label="Activity Feed"
                >
                  <ListOrdered className="w-5 h-5" />
                </Link>
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

              {/* More Navigation for mobile */}
              <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
                <div className="px-3 pb-2">
                  <span className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                    More
                  </span>
                </div>
                {moreNavigation.map((item) => {
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

              {/* Quick Actions for mobile */}
              <div className="pt-3 mt-3" style={{ borderTop: '1px solid var(--border)' }}>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    setQuickLogOpen(true);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-base font-medium mb-2"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: '#FFFFFF',
                  }}
                >
                  <Plus className="w-5 h-5" />
                  Quick Log
                </button>
                <Link
                  to="/feed"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-base font-medium"
                  style={{
                    color: location.pathname === '/feed' ? 'var(--accent)' : 'var(--text)',
                    backgroundColor: location.pathname === '/feed' ? 'var(--surfaceElev)' : 'transparent',
                  }}
                >
                  <ListOrdered className="w-5 h-5" />
                  Feed
                </Link>
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

      {/* Quick Log Modal */}
      <QuickLog
        isOpen={quickLogOpen}
        onClose={() => setQuickLogOpen(false)}
        onSuccess={() => {
          // Refresh if on dashboard
          if (location.pathname === '/') {
            window.location.reload();
          }
        }}
      />
    </div>
  );
}

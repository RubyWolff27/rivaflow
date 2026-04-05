import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Users, Plus, BarChart3, User, LogOut, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavSectionItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  // badge: number = unread count (error-coloured pill)
  // badge: string = promo label like "NEW" (accent-coloured pill)
  badge?: number | string;
}

interface NavSection {
  label: string;
  items: NavSectionItem[];
}

interface BottomNavProps {
  navigation: { name: string; href: string; icon: React.ComponentType<{ className?: string }>; badge?: number }[];
  moreNavSections: NavSection[];
  onQuickLog: () => void;
}

export default function BottomNav({ moreNavSections, onQuickLog }: BottomNavProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [youOpen, setYouOpen] = useState(false);
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setYouOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (youOpen) {
      const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setYouOpen(false); };
      document.addEventListener('keydown', handleEsc);
      return () => document.removeEventListener('keydown', handleEsc);
    }
  }, [youOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // 5 bottom items: Home, Feed, Log(accent, centered), Progress, You.
  // 2026-04-05 — Feed un-hidden per CEO Q2 ratification ("un-hide feed").
  // Replaces the previous Sessions slot (sessions remain accessible via
  // Home dashboard widgets + /sessions URL + the You sheet).
  const bottomItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Feed', href: '/feed', icon: Users },
    { name: 'Log', href: '#quicklog', icon: Plus, isAccent: true },
    { name: 'Progress', href: '/reports', icon: BarChart3 },
    { name: 'You', href: '#you', icon: User },
  ];

  return (
    <>
      {/* "You" sheet overlay */}
      {youOpen && (
        <div
          className="md:hidden fixed inset-0 z-40"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={() => setYouOpen(false)}
        >
          <div
            ref={sheetRef}
            className="absolute bottom-0 left-0 right-0 rounded-t-[24px] max-h-[70vh] overflow-y-auto pb-20"
            style={{ backgroundColor: 'var(--surface)' }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="You menu"
          >
            <div className="flex items-center justify-between px-6 pt-5 pb-3">
              <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>You</h2>
              <button
                onClick={() => setYouOpen(false)}
                className="p-2 rounded-lg"
                style={{ color: 'var(--muted)' }}
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Profile link at top */}
            <Link
              to="/profile"
              className="flex items-center gap-3 px-6 py-3 text-sm font-medium"
              style={{ color: location.pathname === '/profile' ? 'var(--accent)' : 'var(--text)' }}
            >
              <User className="w-5 h-5" />
              Profile
            </Link>

            {moreNavSections.map((section) => (
              <div key={section.label}>
                <div className="my-1 mx-6" style={{ borderTop: '1px solid var(--border)' }} />
                <div className="px-6 pt-3 pb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
                    {section.label}
                  </span>
                </div>
                {section.items.map((item) => {
                  const isActive = location.pathname === item.href;
                  const Icon = item.icon;
                  // Badge can be a number (unread count) or a string ("NEW"
                  // promo badge, added 2026-04-05 for Grapple AI + Glossary).
                  const badge = (item as { badge?: number | string }).badge;
                  const numericBadge = typeof badge === 'number' && badge > 0;
                  const stringBadge = typeof badge === 'string' && badge.length > 0;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className="flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors"
                      style={{
                        color: isActive ? 'var(--accent)' : 'var(--text)',
                      }}
                    >
                      <Icon className="w-5 h-5" />
                      {item.name}
                      {numericBadge && (
                        <span
                          className="ml-auto flex items-center justify-center min-w-[20px] h-[20px] px-1.5 text-[10px] font-bold rounded-full"
                          style={{ backgroundColor: 'var(--error)', color: '#FFFFFF' }}
                        >
                          {(badge as number) > 99 ? '99+' : badge}
                        </span>
                      )}
                      {stringBadge && (
                        <span
                          className="ml-auto flex items-center justify-center px-2 h-[20px] text-[10px] font-bold rounded-full"
                          style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
                        >
                          {badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            ))}

            {/* Logout */}
            <div className="mx-6 my-1" style={{ borderTop: '1px solid var(--border)' }} />
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-6 py-3 text-sm font-medium"
              style={{ color: 'var(--text)' }}
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </div>
      )}

      {/* Bottom tab bar */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-30 border-t"
        style={{
          backgroundColor: 'var(--surface)',
          borderColor: 'var(--border)',
        }}
        role="navigation"
        aria-label="Mobile navigation"
      >
        <div className="flex items-center justify-around h-16 px-2 max-w-lg mx-auto">
          {bottomItems.map((item) => {
            const Icon = item.icon;
            const isLog = item.href === '#quicklog';
            const isYou = item.href === '#you';
            const isActive = !isLog && !isYou && (
              location.pathname === item.href ||
              (item.href === '/reports' && location.pathname === '/progress')
            );

            if (isLog) {
              return (
                <button
                  key={item.name}
                  onClick={onQuickLog}
                  className="flex flex-col items-center justify-center gap-0.5 py-1 px-2 relative"
                  aria-label="Quick Log"
                >
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'var(--accent)' }}
                  >
                    <Icon className="w-5 h-5" style={{ color: '#FFFFFF' }} />
                  </div>
                  <span className="text-[10px] font-medium" style={{ color: 'var(--accent)' }}>Log</span>
                </button>
              );
            }

            if (isYou) {
              const youActive = youOpen || location.pathname === '/profile';
              return (
                <button
                  key={item.name}
                  onClick={() => setYouOpen(true)}
                  className="flex flex-col items-center justify-center gap-0.5 py-1 px-2 relative"
                  style={{ color: youActive ? 'var(--accent)' : 'var(--muted)' }}
                  aria-label="You menu"
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-[10px] font-medium">{item.name}</span>
                </button>
              );
            }

            return (
              <Link
                key={item.name}
                to={item.href}
                className="flex flex-col items-center justify-center gap-0.5 py-1 px-2 relative"
                style={{ color: isActive ? 'var(--accent)' : 'var(--muted)' }}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-medium">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}

import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Calendar, Plus, BarChart3, User, LogOut, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavSectionItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
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

  // 5 bottom items: Home, Sessions, Log(accent, centered), Progress, You
  const bottomItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Sessions', href: '/sessions', icon: Calendar },
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
                  const hasBadge = item.badge != null && item.badge > 0;
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
                      {hasBadge && (
                        <span
                          className="ml-auto flex items-center justify-center min-w-[20px] h-[20px] px-1.5 text-[10px] font-bold rounded-full"
                          style={{ backgroundColor: 'var(--error)', color: '#FFFFFF' }}
                        >
                          {item.badge! > 99 ? '99+' : item.badge}
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

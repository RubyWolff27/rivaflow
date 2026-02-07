import { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Plus, Activity, BarChart3, Grid, User, LogOut, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavSection {
  label: string;
  items: { name: string; href: string; icon: React.ComponentType<{ className?: string }> }[];
}

interface BottomNavProps {
  navigation: { name: string; href: string; icon: React.ComponentType<{ className?: string }>; badge?: number }[];
  moreNavSections: NavSection[];
  onQuickLog: () => void;
}

export default function BottomNav({ navigation, moreNavSections, onQuickLog }: BottomNavProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);
  const sheetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (moreOpen) {
      const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMoreOpen(false); };
      document.addEventListener('keydown', handleEsc);
      return () => document.removeEventListener('keydown', handleEsc);
    }
  }, [moreOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // 5 bottom items: Dashboard, Feed, Log(accent), Progress, More
  const bottomItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Feed', href: '/feed', icon: Activity, badge: navigation.find(n => n.href === '/feed')?.badge },
    { name: 'Log', href: '#quicklog', icon: Plus, isAccent: true },
    { name: 'Progress', href: '/reports', icon: BarChart3 },
    { name: 'More', href: '#more', icon: Grid },
  ];

  return (
    <>
      {/* More sheet overlay */}
      {moreOpen && (
        <div
          className="md:hidden fixed inset-0 z-40"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          onClick={() => setMoreOpen(false)}
        >
          <div
            ref={sheetRef}
            className="absolute bottom-0 left-0 right-0 rounded-t-[24px] max-h-[70vh] overflow-y-auto pb-20"
            style={{ backgroundColor: 'var(--surface)' }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="More navigation options"
          >
            <div className="flex items-center justify-between px-6 pt-5 pb-3">
              <h2 className="text-lg font-semibold" style={{ color: 'var(--text)' }}>More</h2>
              <button
                onClick={() => setMoreOpen(false)}
                className="p-2 rounded-lg"
                style={{ color: 'var(--muted)' }}
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Friends link */}
            {navigation.filter(n => n.href === '/friends').map((item) => {
              const Icon = item.icon;
              const hasBadge = item.badge != null && item.badge > 0;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className="flex items-center gap-3 px-6 py-3 text-sm font-medium"
                  style={{ color: location.pathname === item.href ? 'var(--accent)' : 'var(--text)' }}
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

            {moreNavSections.map((section, sIdx) => (
              <div key={section.label}>
                {(sIdx > 0 || navigation.some(n => n.href === '/friends')) && (
                  <div className="my-1 mx-6" style={{ borderTop: '1px solid var(--border)' }} />
                )}
                <div className="px-6 pt-3 pb-1">
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
                      className="flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors"
                      style={{
                        color: isActive ? 'var(--accent)' : 'var(--text)',
                      }}
                    >
                      <Icon className="w-5 h-5" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            ))}

            {/* Profile + Logout */}
            <div className="mx-6 my-1" style={{ borderTop: '1px solid var(--border)' }} />
            <Link
              to="/profile"
              className="flex items-center gap-3 px-6 py-3 text-sm font-medium"
              style={{ color: 'var(--text)' }}
            >
              <User className="w-5 h-5" />
              Profile
            </Link>
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
            const isMore = item.href === '#more';
            const isLog = item.href === '#quicklog';
            const isActive = !isMore && !isLog && (
              location.pathname === item.href ||
              (item.href === '/reports' && location.pathname === '/progress')
            );
            const hasBadge = 'badge' in item && item.badge != null && item.badge > 0;

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

            if (isMore) {
              return (
                <button
                  key={item.name}
                  onClick={() => setMoreOpen(true)}
                  className="flex flex-col items-center justify-center gap-0.5 py-1 px-2 relative"
                  style={{ color: moreOpen ? 'var(--accent)' : 'var(--muted)' }}
                  aria-label="More options"
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
                {hasBadge && (
                  <span
                    className="absolute top-0 right-0 flex items-center justify-center min-w-[16px] h-[16px] px-1 text-[9px] font-bold rounded-full"
                    style={{ backgroundColor: 'var(--error)', color: '#FFFFFF' }}
                  >
                    {item.badge! > 99 ? '99+' : item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}

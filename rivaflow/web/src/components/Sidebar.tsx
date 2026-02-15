import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Plus, User, LogOut, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavSection {
  label: string;
  items: { name: string; href: string; icon: React.ComponentType<{ className?: string }> }[];
}

interface SidebarProps {
  navigation: { name: string; href: string; icon: React.ComponentType<{ className?: string }>; badge?: number }[];
  moreNavSections: NavSection[];
  onQuickLog: () => void;
}

const DEFAULT_EXPANDED = ['Training'];

export default function Sidebar({ navigation, moreNavSections, onQuickLog }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebar-collapsed') === 'true'; } catch { return false; }
  });
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() => {
    try {
      const stored = localStorage.getItem('sidebar-sections');
      if (stored) return JSON.parse(stored);
    } catch { /* noop */ }
    return Object.fromEntries(DEFAULT_EXPANDED.map(s => [s, true]));
  });

  useEffect(() => {
    try { localStorage.setItem('sidebar-collapsed', String(collapsed)); } catch { /* noop */ }
  }, [collapsed]);

  useEffect(() => {
    try { localStorage.setItem('sidebar-sections', JSON.stringify(expandedSections)); } catch { /* noop */ }
  }, [expandedSections]);

  const toggleSection = (label: string) => {
    setExpandedSections(prev => ({ ...prev, [label]: !prev[label] }));
  };

  // Auto-expand section if it contains the active route
  useEffect(() => {
    for (const section of moreNavSections) {
      if (section.items.some(item => location.pathname === item.href)) {
        setExpandedSections(prev => prev[section.label] ? prev : { ...prev, [section.label]: true });
        break;
      }
    }
  }, [location.pathname, moreNavSections]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside
      className="hidden md:flex flex-col shrink-0 sticky top-0 h-screen border-r overflow-y-auto"
      style={{
        width: collapsed ? 64 : 240,
        backgroundColor: 'var(--surface)',
        borderColor: 'var(--border)',
        transition: 'width 200ms ease',
      }}
    >
      {/* Logo + Collapse */}
      <div className="flex items-center justify-between px-4 h-16 shrink-0">
        {!collapsed && (
          <Link
            to="/"
            className="text-lg font-bold hover:opacity-80 transition-opacity"
            style={{ color: 'var(--text)' }}
          >
            RIVAFLOW
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg transition-colors"
          style={{ color: 'var(--muted)' }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Quick Log Button */}
      <div className="px-3 mb-2">
        <button
          onClick={onQuickLog}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-[14px] text-sm font-medium transition-colors"
          style={{ backgroundColor: 'var(--accent)', color: '#FFFFFF' }}
          title="Quick Log"
        >
          <Plus className="w-4 h-4" />
          {!collapsed && 'Quick Log'}
        </button>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 px-3 space-y-1" role="navigation" aria-label="Main navigation">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href ||
            (item.href === '/reports' && location.pathname === '/progress');
          const Icon = item.icon;
          const hasBadge = item.badge != null && item.badge > 0;
          return (
            <Link
              key={item.name}
              to={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors relative"
              style={{
                color: isActive ? 'var(--accent)' : 'var(--muted)',
                backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
              }}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && item.name}
              {hasBadge && (
                <span
                  className="flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold rounded-full"
                  style={{
                    backgroundColor: 'var(--error)',
                    color: '#FFFFFF',
                    position: collapsed ? 'absolute' : 'static',
                    top: collapsed ? 2 : undefined,
                    right: collapsed ? 2 : undefined,
                    marginLeft: collapsed ? 0 : 'auto',
                  }}
                >
                  {item.badge! > 99 ? '99+' : item.badge}
                </span>
              )}
            </Link>
          );
        })}

        {/* Collapsible sections */}
        {moreNavSections.map((section) => {
          const isExpanded = expandedSections[section.label] ?? false;
          const hasActiveItem = section.items.some(item => location.pathname === item.href);
          return (
            <div key={section.label} className="pt-4">
              {!collapsed ? (
                <button
                  onClick={() => toggleSection(section.label)}
                  className="w-full flex items-center justify-between px-3 pb-2 group"
                >
                  <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--muted)' }}>
                    {section.label}
                  </span>
                  <ChevronDown
                    className="w-3 h-3 transition-transform"
                    style={{
                      color: 'var(--muted)',
                      transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                    }}
                  />
                </button>
              ) : (
                <div className="my-2 mx-2" style={{ borderTop: '1px solid var(--border)' }} />
              )}
              {(collapsed || isExpanded || hasActiveItem) && section.items.map((item) => {
                const isActive = location.pathname === item.href;
                const Icon = item.icon;
                // When collapsed section has active item but section not expanded, only show active item
                if (!collapsed && !isExpanded && !isActive) return null;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                    style={{
                      color: isActive ? 'var(--accent)' : 'var(--muted)',
                      backgroundColor: isActive ? 'var(--surfaceElev)' : 'transparent',
                    }}
                    title={collapsed ? item.name : undefined}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    {!collapsed && item.name}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* User section at bottom */}
      <div className="px-3 py-3 mt-auto border-t" style={{ borderColor: 'var(--border)' }}>
        <Link
          to="/profile"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{ color: 'var(--muted)' }}
          title={collapsed ? `${user?.first_name} ${user?.last_name}` : undefined}
        >
          <User className="w-4 h-4 shrink-0" />
          {!collapsed && <span className="truncate">{user?.first_name} {user?.last_name}</span>}
        </Link>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{ color: 'var(--muted)' }}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && 'Logout'}
        </button>
      </div>
    </aside>
  );
}

import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Building2, MessageSquare, Book, Sparkles, MessageCircle, ListOrdered } from 'lucide-react';

export default function AdminNav() {
  const location = useLocation();

  const adminNavigation = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    { name: 'Grapple', href: '/admin/grapple', icon: Sparkles },
    { name: 'Users', href: '/admin/users', icon: Users },
    { name: 'Gyms', href: '/admin/gyms', icon: Building2 },
    { name: 'Content', href: '/admin/content', icon: MessageSquare },
    { name: 'Techniques', href: '/admin/techniques', icon: Book },
    { name: 'Feedback', href: '/admin/feedback', icon: MessageCircle },
    { name: 'Waitlist', href: '/admin/waitlist', icon: ListOrdered },
  ];

  return (
    <div className="mb-6">
      <nav className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {adminNavigation.map((item) => {
          const isActive = location.pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.href}
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors whitespace-nowrap"
              style={{
                color: isActive ? 'var(--accent)' : 'var(--muted)',
                backgroundColor: isActive ? 'var(--surfaceElev)' : 'var(--surface)',
                border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
              }}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

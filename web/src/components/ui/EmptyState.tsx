import { LucideIcon, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionPath?: string;
  action?: ReactNode;
}

export default function EmptyState({
  icon: Icon = TrendingUp,
  title,
  description,
  actionLabel,
  actionPath,
  action,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-[14px]"
      style={{ backgroundColor: 'var(--surface)' }}
    >
      <div
        className="flex items-center justify-center w-16 h-16 rounded-full mb-4"
        style={{ backgroundColor: 'var(--surfaceElev)' }}
      >
        <Icon className="w-8 h-8" style={{ color: 'var(--muted)' }} />
      </div>
      <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
        {title}
      </h3>
      <p className="text-sm mb-6 max-w-md" style={{ color: 'var(--muted)' }}>
        {description}
      </p>
      {actionLabel && actionPath && (
        <Link
          to={actionPath}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{
            backgroundColor: 'var(--accent)',
            color: '#FFFFFF',
          }}
        >
          {actionLabel}
        </Link>
      )}
      {action}
    </div>
  );
}

import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  backPath?: string;
}

export default function PageHeader({ title, subtitle, actions, backPath }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        {backPath && (
          <Link
            to={backPath}
            className="p-2 rounded-lg transition-colors shrink-0"
            style={{ color: 'var(--muted)' }}
            aria-label="Go back"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
        )}
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-[var(--text)] truncate" id="page-title">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-[var(--muted)] mt-0.5 truncate">{subtitle}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

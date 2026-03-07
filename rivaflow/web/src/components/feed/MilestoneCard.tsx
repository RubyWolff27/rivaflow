import { Star } from 'lucide-react';

interface MilestoneCardProps {
  label: string;
  type?: string;
  value?: number;
}

export default function MilestoneCard({ label, type, value }: MilestoneCardProps) {
  const supportText = type && value
    ? `${value.toLocaleString()} ${type}`
    : undefined;

  return (
    <div
      className="rounded-xl p-4"
      style={{
        background: 'linear-gradient(135deg, var(--surface), var(--surfaceElev))',
        border: '1px solid rgba(245, 158, 11, 0.3)',
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)' }}
        >
          <Star className="w-5 h-5" style={{ color: '#F59E0B' }} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-bold leading-tight" style={{ color: '#F59E0B' }}>
            {label}
          </p>
          {supportText && (
            <p className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
              {supportText}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

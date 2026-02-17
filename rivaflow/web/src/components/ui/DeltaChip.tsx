import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface DeltaChipProps {
  value: number;
  format?: 'number' | 'percent';
  className?: string;
}

const DeltaChip = memo(function DeltaChip({ value, format = 'number', className = '' }: DeltaChipProps) {
  const isPositive = value > 0;
  const isNeutral = value === 0;

  const Icon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;

  const colorClass = isNeutral
    ? 'text-[var(--muted)]'
    : isPositive
    ? 'text-[var(--accent)]'
    : 'text-[var(--muted)]';

  const formattedValue = format === 'percent' ? `${Math.abs(value)}%` : Math.abs(value);

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${colorClass} ${className}`}>
      <Icon className="w-3 h-3" />
      {formattedValue}
    </span>
  );
});

export default DeltaChip;

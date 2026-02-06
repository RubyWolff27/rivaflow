import { ReactNode } from 'react';

interface ChipProps {
  children: ReactNode;
  variant?: 'default' | 'accent';
  className?: string;
}

export default function Chip({ children, variant = 'default', className = '' }: ChipProps) {
  const baseStyles = 'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium';

  const variantStyles = {
    default: 'bg-[var(--surfaceElev)] text-[var(--muted)] border border-[var(--border)]',
    accent: 'bg-[var(--accent)] text-white',
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${className}`}>
      {children}
    </span>
  );
}

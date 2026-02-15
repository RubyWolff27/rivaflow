import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  variant?: 'default' | 'hero' | 'compact';
}

export default function Card({ children, className = '', interactive, variant = 'default' }: CardProps) {
  const baseClass = variant === 'hero' ? 'card-hero' : variant === 'compact' ? 'card-compact' : 'card';
  return (
    <div className={`${baseClass} ${interactive ? 'card-interactive' : ''} ${className}`}>
      {children}
    </div>
  );
}

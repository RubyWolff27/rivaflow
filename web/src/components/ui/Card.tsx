import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}

export default function Card({ children, className = '', interactive }: CardProps) {
  return (
    <div className={`card ${interactive ? 'card-interactive' : ''} ${className}`}>
      {children}
    </div>
  );
}

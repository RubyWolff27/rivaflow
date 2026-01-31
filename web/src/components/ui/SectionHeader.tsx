import { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  action?: ReactNode;
  className?: string;
}

export default function SectionHeader({ title, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <h2 className="text-lg font-semibold text-[var(--text)]">{title}</h2>
      {action && <div>{action}</div>}
    </div>
  );
}

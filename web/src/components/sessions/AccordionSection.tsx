import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface AccordionSectionProps {
  title: string;
  icon?: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}

export default function AccordionSection({
  title,
  icon,
  defaultOpen = false,
  children,
  className = '',
}: AccordionSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`border-t border-[var(--border)] pt-3 ${className}`}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-sm hover:text-[var(--text)] transition-colors mb-2"
      >
        <span className="font-semibold flex items-center gap-1.5" style={{ color: 'var(--text)' }}>
          {icon}
          {title}
        </span>
        {open ? (
          <ChevronUp className="w-4 h-4" style={{ color: 'var(--muted)' }} />
        ) : (
          <ChevronDown className="w-4 h-4" style={{ color: 'var(--muted)' }} />
        )}
      </button>
      {open && <div className="space-y-4">{children}</div>}
    </div>
  );
}

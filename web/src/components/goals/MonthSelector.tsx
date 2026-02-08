import { ChevronLeft, ChevronRight } from 'lucide-react';

interface MonthSelectorProps {
  month: string; // 'YYYY-MM'
  onChange: (month: string) => void;
}

function formatMonthLabel(month: string): string {
  const [year, m] = month.split('-');
  const date = new Date(parseInt(year), parseInt(m) - 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function shiftMonth(month: string, delta: number): string {
  const [year, m] = month.split('-').map(Number);
  const date = new Date(year, m - 1 + delta);
  const y = date.getFullYear();
  const mo = String(date.getMonth() + 1).padStart(2, '0');
  return `${y}-${mo}`;
}

export default function MonthSelector({ month, onChange }: MonthSelectorProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      <button
        onClick={() => onChange(shiftMonth(month, -1))}
        className="p-2 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
        style={{ color: 'var(--muted)' }}
        aria-label="Previous month"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <span
        className="text-lg font-semibold min-w-[200px] text-center"
        style={{ color: 'var(--text)' }}
      >
        {formatMonthLabel(month)}
      </span>
      <button
        onClick={() => onChange(shiftMonth(month, 1))}
        className="p-2 rounded-lg transition-colors hover:bg-[var(--surfaceElev)]"
        style={{ color: 'var(--muted)' }}
        aria-label="Next month"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
}

import Chip from './Chip';
import DeltaChip from './DeltaChip';
import Sparkline from './Sparkline';

interface MetricTileProps {
  label: string;
  chipLabel: string;
  value: string | number;
  delta?: number;
  sparklineData?: number[];
  className?: string;
}

export default function MetricTile({
  label,
  chipLabel,
  value,
  delta,
  sparklineData,
  className = '',
}: MetricTileProps) {
  return (
    <div className={`flex flex-col gap-3 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[14px] shadow-sm ${className}`}>
      {/* Header: Label + Chip */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-[var(--muted)] uppercase tracking-wide">{label}</span>
        <Chip>{chipLabel}</Chip>
      </div>

      {/* Value + Delta */}
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-[var(--text)]">{value}</span>
        {delta !== undefined && <DeltaChip value={delta} />}
      </div>

      {/* Sparkline */}
      {sparklineData && Array.isArray(sparklineData) && sparklineData.length > 0 && (
        <div className="mt-1">
          <Sparkline data={sparklineData} width={100} height={24} strokeWidth={1.5} />
        </div>
      )}
    </div>
  );
}

interface LoadingSkeletonProps {
  width?: string;
  height?: string;
  className?: string;
  rounded?: boolean;
}

export default function LoadingSkeleton({
  width = '100%',
  height = '20px',
  className = '',
  rounded = false,
}: LoadingSkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-[var(--border)] ${rounded ? 'rounded-full' : 'rounded'} ${className}`}
      style={{ width, height }}
    />
  );
}

export function MetricTileSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-[14px] shadow-sm">
      <div className="flex items-center justify-between">
        <LoadingSkeleton width="80px" height="12px" />
        <LoadingSkeleton width="50px" height="20px" rounded />
      </div>
      <div className="flex items-baseline gap-2">
        <LoadingSkeleton width="60px" height="28px" />
        <LoadingSkeleton width="40px" height="20px" rounded />
      </div>
      <div className="mt-1">
        <LoadingSkeleton width="100%" height="24px" />
      </div>
    </div>
  );
}

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-[14px] space-y-3">
      <LoadingSkeleton width="150px" height="20px" />
      {Array.from({ length: lines }).map((_, i) => (
        <LoadingSkeleton key={i} width={`${[95, 80, 70, 85, 75][i % 5]}%`} height="16px" />
      ))}
    </div>
  );
}

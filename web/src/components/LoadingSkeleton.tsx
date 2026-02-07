export default function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-10 w-32 bg-[var(--surfaceElev)] rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-3/4 bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-full bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-5/6 bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-4/6 bg-[var(--surfaceElev)] rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-2/3 bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-full bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-5/6 bg-[var(--surfaceElev)] rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-1/2 bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-full bg-[var(--surfaceElev)] rounded"></div>
        <div className="h-4 w-3/4 bg-[var(--surfaceElev)] rounded"></div>
      </div>
    </div>
  );
}

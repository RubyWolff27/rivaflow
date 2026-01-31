export default function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-3/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-4/6 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-2/3 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-5/6 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="card space-y-4">
        <div className="h-6 w-1/2 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>
  );
}

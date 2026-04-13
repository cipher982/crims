function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} />;
}

export default function PersonLoading() {
  return (
    <div>
      <SkeletonBlock className="mb-4 h-4 w-28" />
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <SkeletonBlock className="mb-3 h-6 w-48" />
        <SkeletonBlock className="mb-2 h-4 w-72" />
        <SkeletonBlock className="h-4 w-full max-w-2xl" />
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
      </div>
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5">
        <SkeletonBlock className="mb-4 h-4 w-64" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5">
        <SkeletonBlock className="mb-4 h-4 w-56" />
        <SkeletonBlock className="h-56 w-full" />
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <SkeletonBlock className="mb-3 h-4 w-40" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
    </div>
  );
}

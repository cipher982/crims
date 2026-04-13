function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded bg-gray-200 ${className}`} />;
}

export default function SearchLoading() {
  return (
    <div>
      <SkeletonBlock className="mb-4 h-8 w-56" />
      <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <SkeletonBlock className="h-4 w-64" />
          <SkeletonBlock className="h-3 w-14" />
        </div>
        <div className="flex flex-wrap gap-3">
          <SkeletonBlock className="h-9 w-36" />
          <SkeletonBlock className="h-9 w-36" />
          <SkeletonBlock className="h-9 w-28" />
          <SkeletonBlock className="h-9 w-24" />
          <SkeletonBlock className="h-9 w-32" />
        </div>
      </div>
      <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <SkeletonBlock className="h-20 w-full" />
        <SkeletonBlock className="h-20 w-full" />
        <SkeletonBlock className="h-20 w-full" />
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <SkeletonBlock className="mb-3 h-4 w-48" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
    </div>
  );
}

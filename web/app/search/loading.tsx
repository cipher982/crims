function SkeletonBlock({ className }: { className: string }) {
  return <div className={`drose-skeleton animate-pulse ${className}`} />;
}

export default function SearchLoading() {
  return (
    <div className="drose-page-stack">
      <SkeletonBlock className="mb-4 h-8 w-56" />
      <div className="drose-panel">
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
      <div className="drose-stat-grid">
        <SkeletonBlock className="h-20 w-full" />
        <SkeletonBlock className="h-20 w-full" />
        <SkeletonBlock className="h-20 w-full" />
      </div>
      <div className="drose-panel">
        <SkeletonBlock className="mb-3 h-4 w-48" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
    </div>
  );
}

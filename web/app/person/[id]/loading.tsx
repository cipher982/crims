function SkeletonBlock({ className }: { className: string }) {
  return <div className={`drose-skeleton animate-pulse ${className}`} />;
}

export default function PersonLoading() {
  return (
    <div className="drose-page-stack">
      <SkeletonBlock className="mb-4 h-4 w-28" />
      <div className="drose-panel">
        <SkeletonBlock className="mb-3 h-6 w-48" />
        <SkeletonBlock className="mb-2 h-4 w-72" />
        <SkeletonBlock className="h-4 w-full max-w-2xl" />
      </div>
      <div className="drose-stat-grid drose-person-stat-grid">
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
        <SkeletonBlock className="h-24 w-full" />
      </div>
      <div className="drose-panel">
        <SkeletonBlock className="mb-4 h-4 w-64" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
      <div className="drose-panel">
        <SkeletonBlock className="mb-4 h-4 w-56" />
        <SkeletonBlock className="h-56 w-full" />
      </div>
      <div className="drose-panel">
        <SkeletonBlock className="mb-3 h-4 w-40" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="mb-2 h-10 w-full" />
        <SkeletonBlock className="h-10 w-full" />
      </div>
    </div>
  );
}

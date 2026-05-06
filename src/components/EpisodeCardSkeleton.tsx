export function EpisodeCardSkeleton() {
  return (
    <div className="rounded-2xl glass cinematic-border overflow-hidden">
      <div className="w-full h-40 shimmer" />
      <div className="p-4 space-y-3">
        <div className="h-3 w-24 rounded-full shimmer" />
        <div className="h-5 w-3/4 rounded-lg shimmer" />
        <div className="space-y-1.5">
          <div className="h-3 w-full rounded shimmer" />
          <div className="h-3 w-full rounded shimmer" />
          <div className="h-3 w-2/3 rounded shimmer" />
        </div>
        <div className="h-px w-full bg-white/5 mt-2" />
        <div className="flex justify-between">
          <div className="h-3 w-16 rounded shimmer" />
          <div className="h-3 w-14 rounded shimmer" />
        </div>
      </div>
    </div>
  );
}

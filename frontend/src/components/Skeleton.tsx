export function SkeletonRows({ count = 6 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-3 p-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-row" />
      ))}
    </div>
  );
}

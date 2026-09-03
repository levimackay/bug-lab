export function ProgressBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="h-[6px] w-full bg-line">
      <div className="h-full bg-ink" style={{ width: `${pct}%` }} />
    </div>
  );
}

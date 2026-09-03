import { Link } from "react-router-dom";

export function PageHeader({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex h-9 items-center gap-4 border-b border-line px-3 font-mono text-2xs uppercase tracking-caps text-ink-dim">
      <Link to="/" className="focus-ring text-ink hover:text-ink">
        BUG LAB
      </Link>
      {children}
    </div>
  );
}

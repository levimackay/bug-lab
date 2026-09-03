import { useEffect, useMemo, useRef, useState } from "react";
import { fuzzyMatch } from "./fuzzyMatch";
import { useWorkspaceContext } from "./WorkspaceContext";

export function FileSwitcher() {
  const { files, openFile, setFileSwitcherOpen } = useWorkspaceContext();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const matches = useMemo(() => {
    const scored = files
      .map((f) => ({ path: f, score: fuzzyMatch(query, f) }))
      .filter((f): f is { path: string; score: number } => f.score !== null);
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, 30).map((f) => f.path);
  }, [files, query]);

  function choose(path: string) {
    openFile(path);
    setFileSwitcherOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      setFileSwitcherOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(matches.length - 1, s + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(0, s - 1));
    } else if (e.key === "Enter" && matches[selected]) {
      e.preventDefault();
      choose(matches[selected]);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-32" onKeyDown={onKeyDown}>
      <div role="dialog" aria-modal="true" aria-label="Open file" className="w-[480px] border border-line-strong bg-panel">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelected(0);
          }}
          placeholder="Go to file…"
          className="focus-ring w-full border-b border-line bg-panel px-3 py-2 font-mono text-sm text-ink outline-none"
        />
        <div className="max-h-80 overflow-auto">
          {matches.map((path, i) => (
            <button
              key={path}
              onClick={() => choose(path)}
              onMouseEnter={() => setSelected(i)}
              className={
                "focus-ring block w-full truncate px-3 py-1.5 text-left font-mono text-xs " +
                (i === selected ? "bg-raised text-ink" : "text-ink-dim")
              }
            >
              {path}
            </button>
          ))}
          {matches.length === 0 && <div className="px-3 py-2 font-mono text-xs text-ink-faint">No matches.</div>}
        </div>
      </div>
    </div>
  );
}

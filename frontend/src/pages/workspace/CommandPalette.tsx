import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fuzzyMatch } from "./fuzzyMatch";
import { useWorkspaceContext } from "./WorkspaceContext";

interface Command {
  id: string;
  label: string;
  shortcut?: string;
  run: () => void;
}

export function CommandPalette() {
  const ctx = useWorkspaceContext();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const close = () => ctx.setCommandPaletteOpen(false);

  const commands: Command[] = useMemo(() => {
    const list: Command[] = [
      { id: "run", label: "Run", shortcut: "", run: () => void ctx.doRun() },
      ...(ctx.run?.incident.commands.build ? [{ id: "build", label: "Build", run: () => void ctx.doBuild() }] : []),
      { id: "tests", label: "Run tests", shortcut: "⌘⇧R", run: () => void ctx.doTest() },
      { id: "reproduce", label: "Reproduce", run: () => ctx.setReproduceDialogOpen(true) },
      { id: "submit", label: "Submit", run: () => void ctx.doSubmit() },
      { id: "reset", label: "Reset run", run: () => ctx.setResetDialogOpen(true) },
      { id: "hint", label: "Request hint", run: () => void ctx.requestHint() },
      { id: "dashboard", label: "Go to dashboard", run: () => navigate("/") },
      { id: "toggle-terminal", label: "Toggle terminal", run: () => ctx.toggleTerminal() },
      { id: "focus-terminal", label: "Focus terminal", shortcut: "⌘`", run: () => ctx.focusTerminal() },
      { id: "open-file", label: "Open file…", shortcut: "⌘P", run: () => ctx.setFileSwitcherOpen(true) },
    ];
    return list;
  }, [ctx, navigate]);

  const matches = useMemo(() => {
    const scored = commands
      .map((c) => ({ c, score: fuzzyMatch(query, c.label) }))
      .filter((x): x is { c: Command; score: number } => x.score !== null);
    scored.sort((a, b) => b.score - a.score);
    return scored.map((x) => x.c);
  }, [commands, query]);

  function choose(cmd: Command) {
    close();
    cmd.run();
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
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
      <div role="dialog" aria-modal="true" aria-label="Command palette" className="w-[480px] border border-line-strong bg-panel">
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelected(0);
          }}
          placeholder="Type a command…"
          className="focus-ring w-full border-b border-line bg-panel px-3 py-2 font-mono text-sm text-ink outline-none"
        />
        <div className="max-h-80 overflow-auto">
          {matches.map((cmd, i) => (
            <button
              key={cmd.id}
              onClick={() => choose(cmd)}
              onMouseEnter={() => setSelected(i)}
              className={
                "focus-ring flex w-full items-center justify-between px-3 py-1.5 text-left font-mono text-xs " +
                (i === selected ? "bg-raised text-ink" : "text-ink-dim")
              }
            >
              <span>{cmd.label}</span>
              {cmd.shortcut && <span className="text-ink-faint">{cmd.shortcut}</span>}
            </button>
          ))}
          {matches.length === 0 && <div className="px-3 py-2 font-mono text-xs text-ink-faint">No matches.</div>}
        </div>
      </div>
    </div>
  );
}

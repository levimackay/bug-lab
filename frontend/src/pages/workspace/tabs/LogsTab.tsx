import { useEffect, useState } from "react";
import { useWorkspaceContext } from "../WorkspaceContext";

export function LogsTab() {
  const { logsInfo, refreshLogs } = useWorkspaceContext();
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!logsInfo) refreshLogs();
  }, []);

  if (!logsInfo) return <div className="p-3 font-mono text-xs text-ink-faint">Loading…</div>;

  function toggle(name: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  return (
    <div className="flex flex-col">
      {logsInfo.files.length === 0 && !logsInfo.last_run && (
        <div className="p-3 font-mono text-xs text-ink-faint">No log files.</div>
      )}
      {logsInfo.files.map((file) => (
        <div key={file.name} className="border-b border-line">
          <button
            className="focus-ring flex w-full items-center gap-2 px-2 py-1.5 text-left font-mono text-xs text-ink-dim hover:bg-raised"
            onClick={() => toggle(file.name)}
          >
            <span className="text-ink-faint">{collapsed.has(file.name) ? "▸" : "▾"}</span>
            {file.name}
          </button>
          {!collapsed.has(file.name) && (
            <pre className="whitespace-pre-wrap break-words bg-panel p-2 font-mono text-2xs text-ink-dim">{file.content}</pre>
          )}
        </div>
      ))}
      {logsInfo.last_run && (
        <div className="border-b border-line">
          <div className="panel-title">Last run output</div>
          <pre className="whitespace-pre-wrap break-words bg-panel p-2 font-mono text-2xs text-ink-dim">
            {logsInfo.last_run.stdout}
            {logsInfo.last_run.stderr}
          </pre>
          <div className="px-2 pb-2 font-mono text-2xs text-ink-faint">
            exit {logsInfo.last_run.exit_code} · {logsInfo.last_run.at}
          </div>
        </div>
      )}
    </div>
  );
}

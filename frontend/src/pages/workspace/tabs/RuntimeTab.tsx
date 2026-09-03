import { useEffect } from "react";
import type { ExecRecord } from "../../../api/types";
import { useWorkspaceContext } from "../WorkspaceContext";

function ExecRow({ record }: { record: ExecRecord }) {
  const color = record.exec.exit_code === 0 ? "text-success" : "text-failure";
  return (
    <div className="flex items-center gap-3 border-b border-line px-2 py-1.5 font-mono text-xs">
      <span className="w-16 uppercase text-ink-faint">{record.kind}</span>
      <span className={color}>exit {record.exec.exit_code}</span>
      <span className="text-ink-dim">{record.exec.duration_ms}ms</span>
      <span className="text-ink-faint">{Math.round(record.exec.max_rss_kb / 1024)}MB</span>
      {record.exec.timed_out && <span className="text-warning">timed out</span>}
      <span className="ml-auto text-ink-faint">{record.at}</span>
    </div>
  );
}

export function RuntimeTab() {
  const { runtimeInfo, refreshRuntime } = useWorkspaceContext();

  useEffect(() => {
    if (!runtimeInfo) refreshRuntime();
  }, []);

  if (!runtimeInfo) return <div className="p-3 font-mono text-xs text-ink-faint">Loading…</div>;

  return (
    <div className="flex flex-col">
      {runtimeInfo.last ? (
        <div className="border-b border-line">
          <div className="panel-title">Last execution</div>
          <ExecRow record={runtimeInfo.last} />
        </div>
      ) : (
        <div className="p-3 font-mono text-xs text-ink-faint">No executions yet.</div>
      )}
      {runtimeInfo.history.length > 0 && (
        <div>
          <div className="panel-title">History</div>
          {runtimeInfo.history.map((r, i) => (
            <ExecRow key={i} record={r} />
          ))}
        </div>
      )}
    </div>
  );
}

import { useWorkspaceContext } from "../WorkspaceContext";

export function TraceTab() {
  const { stackTrace, files, revealFrame } = useWorkspaceContext();

  if (!stackTrace) {
    return <div className="p-3 font-mono text-xs text-ink-faint">No stack trace captured yet.</div>;
  }

  return (
    <div className="flex flex-col">
      <div className="border-b border-line bg-panel px-2 py-2 font-mono text-2xs text-failure">{stackTrace.header}</div>
      <div className="divide-y divide-line">
        {stackTrace.frames.map((frame, i) => {
          const clickable = files.includes(frame.file);
          return (
            <button
              key={i}
              disabled={!clickable}
              onClick={() => revealFrame(frame.file, frame.line)}
              className={
                "focus-ring flex w-full items-center gap-2 px-2 py-1 text-left font-mono text-xs " +
                (clickable ? "text-ink-dim hover:bg-raised hover:text-ink" : "cursor-default text-ink-faint")
              }
            >
              <span>
                {frame.file}:{frame.line}
              </span>
              <span className="text-ink-faint">{frame.function}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

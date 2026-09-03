import { Link } from "react-router-dom";
import { SeverityDot, severityLabel } from "../../components/SeverityDot";
import { useWorkspaceContext } from "./WorkspaceContext";

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function StatusStrip() {
  const { run, elapsedSeconds } = useWorkspaceContext();
  if (!run) return <div className="h-9 border-b border-line" />;

  const incident = run.incident;

  return (
    <div className="flex h-9 items-center gap-4 border-b border-line px-3 font-mono text-2xs uppercase tracking-caps text-ink-dim">
      <Link to="/" className="focus-ring text-ink hover:text-ink">
        BUG LAB
      </Link>
      <span>INCIDENT #{incident.number.toString().padStart(3, "0")}</span>
      <span className="flex items-center gap-2">
        <SeverityDot severity={incident.severity} pulse={run.status === "active"} />
        {severityLabel(incident.severity)}
      </span>
      <span className="text-ink normal-case tracking-normal">{incident.title}</span>
      <span className="ml-auto">{formatElapsed(elapsedSeconds)}</span>
      <span className={run.status === "resolved" ? "text-success" : "text-running"}>
        {run.status === "resolved" ? "RESOLVED" : "ACTIVE"}
      </span>
    </div>
  );
}

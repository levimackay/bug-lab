import { SeverityDot, severityLabel } from "../../../components/SeverityDot";
import { useWorkspaceContext } from "../WorkspaceContext";

export function IncidentTab() {
  const { run } = useWorkspaceContext();
  if (!run) return null;
  const incident = run.incident;

  return (
    <div className="flex flex-col gap-4 p-3 text-xs">
      <div className="flex items-center gap-2 font-mono text-ink-dim">
        <span>#{incident.number.toString().padStart(3, "0")}</span>
        <SeverityDot severity={incident.severity} />
        <span>{severityLabel(incident.severity)}</span>
      </div>
      <div className="font-medium text-ink">{incident.title}</div>
      <div className="flex flex-col gap-2 leading-relaxed text-ink-dim">
        {incident.description.split(/\n\s*\n/).map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </div>
      <div>
        <div className="panel-title px-0">Symptoms</div>
        <ul className="flex flex-col gap-1 text-ink-dim">
          {incident.symptoms.map((s, i) => (
            <li key={i} className="before:mr-1.5 before:text-ink-faint before:content-['—']">
              {s}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <div className="panel-title px-0">Environment</div>
        <pre className="whitespace-pre-wrap border border-line bg-panel p-2 font-mono text-2xs text-ink-dim">{incident.environment}</pre>
      </div>
      <div>
        <div className="panel-title px-0">Expected</div>
        <p className="text-ink-dim">{incident.expected_behavior}</p>
      </div>
      <div>
        <div className="panel-title px-0">Broken</div>
        <p className="text-ink-dim">{incident.broken_behavior}</p>
      </div>
      <div>
        <div className="panel-title px-0">Commands</div>
        <div className="flex flex-col gap-1 font-mono text-2xs text-ink-dim">
          <div>run: {incident.commands.run}</div>
          <div>test: {incident.commands.test}</div>
          {incident.commands.build ? <div>build: {incident.commands.build}</div> : null}
        </div>
      </div>
    </div>
  );
}

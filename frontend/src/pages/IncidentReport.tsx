import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/endpoints";
import { ApiError } from "../api/http";
import type { IncidentSummary } from "../api/types";
import { ErrorState } from "../components/ErrorState";
import { PageHeader } from "../components/PageHeader";
import { SeverityDot, severityLabel } from "../components/SeverityDot";
import { SkeletonRows } from "../components/Skeleton";
import { useToast } from "../components/ToastProvider";

export default function IncidentReport() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<IncidentSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const { pushError } = useToast();
  const navigate = useNavigate();

  const load = useCallback(() => {
    if (!id) return;
    setError(null);
    api
      .incident(id)
      .then((inc) => setIncident(inc))
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.message : "Failed to load incident";
        setError(message);
        pushError(message);
      });
  }, [id, pushError]);

  useEffect(() => {
    load();
  }, [load]);

  async function startInvestigation() {
    if (!id) return;
    setStarting(true);
    try {
      const run = await api.startRun(id);
      navigate(`/runs/${run.id}`);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to start investigation");
      setStarting(false);
    }
  }

  return (
    <div className="min-h-screen bg-ground">
      <PageHeader />
      <div className="mx-auto max-w-[720px] p-6">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : !incident ? (
          <SkeletonRows count={8} />
        ) : (
          <div className="mount-stagger flex flex-col gap-5">
            <div className="flex items-center gap-2 font-mono text-xs text-ink-dim">
              <span>INCIDENT #{incident.number.toString().padStart(3, "0")}</span>
              <span>·</span>
              <SeverityDot severity={incident.severity} />
              <span>{severityLabel(incident.severity)}</span>
              <span>·</span>
              <span>{incident.system}</span>
            </div>

            <h1 className="text-2xl font-medium text-ink">{incident.title}</h1>

            <div className="flex flex-col gap-3 text-sm leading-relaxed text-ink-dim">
              {incident.description.split(/\n\s*\n/).map((para, i) => (
                <p key={i}>{para}</p>
              ))}
            </div>

            <div>
              <div className="panel-title px-0">Symptoms</div>
              <ul className="flex flex-col gap-1 text-sm text-ink-dim">
                {incident.symptoms.map((s, i) => (
                  <li key={i} className="before:mr-2 before:text-ink-faint before:content-['—']">
                    {s}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="panel-title px-0">Environment</div>
              <pre className="whitespace-pre-wrap border border-line bg-panel p-3 font-mono text-xs text-ink-dim">
                {incident.environment}
              </pre>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="panel-title px-0">Expected behaviour</div>
                <p className="text-sm text-ink-dim">{incident.expected_behavior}</p>
              </div>
              <div>
                <div className="panel-title px-0">Broken behaviour</div>
                <p className="text-sm text-ink-dim">{incident.broken_behavior}</p>
              </div>
            </div>

            <div>
              <div className="panel-title px-0">Available tools</div>
              <div className="flex gap-2 font-mono text-xs uppercase text-ink-dim">
                {incident.tools.map((t) => (
                  <span key={t} className="border border-line px-2 py-0.5">
                    {t.replace("_", " ")}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div className="panel-title px-0">Commands</div>
              <div className="flex flex-col gap-1 font-mono text-xs text-ink-dim">
                <div>run: {incident.commands.run}</div>
                <div>test: {incident.commands.test}</div>
                {incident.commands.build ? <div>build: {incident.commands.build}</div> : null}
              </div>
            </div>

            <div>
              <button className="btn btn-primary focus-ring" onClick={startInvestigation} disabled={starting}>
                {starting ? "STARTING…" : incident.active_run_id ? "RESUME" : "START INVESTIGATION"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

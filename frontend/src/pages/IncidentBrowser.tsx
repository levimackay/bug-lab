import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/endpoints";
import { ApiError } from "../api/http";
import type { Difficulty, IncidentSummary, Language } from "../api/types";
import { PageHeader } from "../components/PageHeader";
import { SeverityDot, severityLabel } from "../components/SeverityDot";
import { SkeletonRows } from "../components/Skeleton";
import { useToast } from "../components/ToastProvider";

type StatusFilter = "all" | IncidentSummary["status"];

const STATUS_LABEL: Record<IncidentSummary["status"], string> = {
  unsolved: "UNSOLVED",
  in_progress: "IN PROGRESS",
  solved: "SOLVED",
};

export default function IncidentBrowser() {
  const [incidents, setIncidents] = useState<IncidentSummary[] | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | "all">("all");
  const [language, setLanguage] = useState<Language | "all">("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const { pushError } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    api
      .incidents()
      .then((res) => {
        if (!cancelled) setIncidents(res.incidents);
      })
      .catch((err: unknown) => {
        pushError(err instanceof ApiError ? err.message : "Failed to load incidents");
      });
    return () => {
      cancelled = true;
    };
  }, [pushError]);

  const filtered = useMemo(() => {
    if (!incidents) return [];
    return incidents.filter(
      (inc) =>
        (difficulty === "all" || inc.difficulty === difficulty) &&
        (language === "all" || inc.language === language) &&
        (status === "all" || inc.status === status),
    );
  }, [incidents, difficulty, language, status]);

  return (
    <div className="min-h-screen bg-ground">
      <PageHeader />
      <div className="mx-auto max-w-5xl p-6">
        <div className="mb-4 flex gap-4 font-mono text-2xs uppercase tracking-caps">
          <Filter label="Difficulty" value={difficulty} onChange={setDifficulty} options={["beginner", "intermediate", "advanced"]} />
          <Filter label="Language" value={language} onChange={setLanguage} options={["python", "javascript", "typescript", "c"]} />
          <Filter label="Status" value={status} onChange={setStatus} options={["unsolved", "in_progress", "solved"]} />
        </div>

        {!incidents ? (
          <SkeletonRows count={10} />
        ) : (
          <table className="w-full border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-line text-left text-ink-faint">
                <th className="py-1.5 font-normal">#</th>
                <th className="py-1.5 font-normal">Severity</th>
                <th className="py-1.5 font-normal">Title</th>
                <th className="py-1.5 font-normal">System</th>
                <th className="py-1.5 font-normal">Language</th>
                <th className="py-1.5 font-normal">Difficulty</th>
                <th className="py-1.5 font-normal">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((inc) => (
                <tr
                  key={inc.id}
                  tabIndex={0}
                  onClick={() => navigate(`/incidents/${inc.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") navigate(`/incidents/${inc.id}`);
                  }}
                  className="focus-ring cursor-pointer border-b border-line text-ink-dim hover:bg-raised"
                >
                  <td className="py-1.5">{inc.number}</td>
                  <td className="py-1.5">
                    <span className="flex items-center gap-2">
                      <SeverityDot severity={inc.severity} />
                      {severityLabel(inc.severity)}
                    </span>
                  </td>
                  <td className="py-1.5 text-ink">{inc.title}</td>
                  <td className="py-1.5">{inc.system}</td>
                  <td className="py-1.5">{inc.language}</td>
                  <td className="py-1.5">{inc.difficulty}</td>
                  <td className="py-1.5">
                    {STATUS_LABEL[inc.status]}
                    {inc.status === "solved" && inc.best_score !== null ? ` (${inc.best_score})` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Filter<T extends string>({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: T | "all";
  onChange: (v: T | "all") => void;
  options: T[];
}) {
  return (
    <label className="flex items-center gap-2 text-ink-faint">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T | "all")}
        className="focus-ring border border-line bg-panel px-1 py-0.5 text-ink-dim"
      >
        <option value="all">ALL</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o.toUpperCase()}
          </option>
        ))}
      </select>
    </label>
  );
}

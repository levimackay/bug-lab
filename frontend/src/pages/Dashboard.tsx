import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/endpoints";
import { ApiError } from "../api/http";
import type { ProgressInfo } from "../api/types";
import { ErrorState } from "../components/ErrorState";
import { PageHeader } from "../components/PageHeader";
import { ProgressBar } from "../components/ProgressBar";
import { SkeletonRows } from "../components/Skeleton";
import { useToast } from "../components/ToastProvider";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function Dashboard() {
  const [progress, setProgress] = useState<ProgressInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { pushError } = useToast();

  const load = useCallback(() => {
    setError(null);
    api
      .progress()
      .then((p) => setProgress(p))
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.message : "Failed to load progress";
        setError(message);
        pushError(message);
      });
  }, [pushError]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="min-h-screen bg-ground">
      <PageHeader />
      <div className="mx-auto max-w-4xl p-6">
        {error ? (
          <ErrorState message={error} onRetry={load} />
        ) : !progress ? (
          <SkeletonRows count={8} />
        ) : (
          <div className="mount-stagger flex flex-col gap-8">
            <div>
              <div className="font-mono text-xl text-ink">
                INCIDENTS {progress.solved} / {progress.total} SOLVED
              </div>
              <Link to="/incidents" className="focus-ring mt-1 inline-block font-mono text-2xs uppercase tracking-caps text-info hover:underline">
                View all incidents →
              </Link>
            </div>

            <div>
              <div className="panel-title px-0">By difficulty</div>
              <div className="flex flex-col gap-3">
                {(Object.keys(progress.by_difficulty) as (keyof typeof progress.by_difficulty)[]).map((diff) => {
                  const d = progress.by_difficulty[diff];
                  return (
                    <div key={diff}>
                      <div className="mb-1 flex justify-between font-mono text-xs">
                        <span className="uppercase text-ink-dim">{diff}</span>
                        <span className="text-ink-faint">
                          {d.solved} / {d.total}
                        </span>
                      </div>
                      <ProgressBar value={d.solved} max={d.total} />
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="panel-title px-0">By specialisation</div>
              <div className="flex flex-col gap-3">
                {Object.entries(progress.by_category).map(([category, c]) => (
                  <div key={category}>
                    <div className="mb-1 flex justify-between font-mono text-xs">
                      <span className="uppercase text-ink-dim">{category}</span>
                      <span className="text-ink-faint">
                        {c.solved} / {c.total}
                        {c.avg_score !== null ? ` · avg ${Math.round(c.avg_score)}` : ""}
                      </span>
                    </div>
                    <ProgressBar value={c.solved} max={c.total} />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="panel-title px-0">Recent resolutions</div>
              {progress.recent.length === 0 ? (
                <div className="font-mono text-xs text-ink-faint">No resolved runs yet.</div>
              ) : (
                <table className="w-full border-collapse font-mono text-xs">
                  <thead>
                    <tr className="border-b border-line text-left text-ink-faint">
                      <th className="py-1 font-normal">#</th>
                      <th className="py-1 font-normal">Title</th>
                      <th className="py-1 text-right font-normal">Score</th>
                      <th className="py-1 text-right font-normal">Time</th>
                      <th className="py-1 text-right font-normal">Hints</th>
                      <th className="py-1 text-right font-normal">Repro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {progress.recent.map((r) => (
                      <tr key={r.run_id} className="border-b border-line text-ink-dim">
                        <td className="py-1">{r.number}</td>
                        <td className="py-1 text-ink">{r.title}</td>
                        <td className="py-1 text-right">{r.score}</td>
                        <td className="py-1 text-right">{formatTime(r.elapsed_seconds)}</td>
                        <td className="py-1 text-right">{r.hints_used}</td>
                        <td className="py-1 text-right">{r.reproduced ? "✓" : "✗"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div>
              <div className="panel-title px-0">Weakest areas</div>
              {progress.weakest.length === 0 ? (
                <div className="font-mono text-xs text-ink-faint">Not enough data yet.</div>
              ) : (
                <ul className="flex flex-col gap-1 font-mono text-xs text-ink-dim">
                  {progress.weakest.map((w) => (
                    <li key={w} className="before:mr-2 before:text-ink-faint before:content-['—']">
                      {w}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

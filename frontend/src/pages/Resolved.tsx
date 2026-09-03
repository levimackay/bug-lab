import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/endpoints";
import { ApiError } from "../api/http";
import type { Postmortem, Run, Score } from "../api/types";
import { DiffView } from "../components/DiffView";
import { PageHeader } from "../components/PageHeader";
import { SkeletonRows } from "../components/Skeleton";
import { useToast } from "../components/ToastProvider";

interface ResolvedData {
  run: Run;
  score: Score;
  postmortem: Postmortem;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function Resolved() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { pushError } = useToast();
  const [data, setData] = useState<ResolvedData | null>(null);

  useEffect(() => {
    if (!id) return;

    const routerState = location.state as { run: Run; score: Score | null; postmortem: Postmortem | null } | null;
    if (routerState?.score && routerState.postmortem) {
      setData({ run: routerState.run, score: routerState.score, postmortem: routerState.postmortem });
      return;
    }

    try {
      const raw = sessionStorage.getItem(`buglab:resolved:${id}`);
      if (raw) {
        const parsed = JSON.parse(raw) as { run: Run; score: Score | null; postmortem: Postmortem | null };
        if (parsed.score && parsed.postmortem) {
          setData({ run: parsed.run, score: parsed.score, postmortem: parsed.postmortem });
          return;
        }
      }
    } catch {
      // ignore storage errors, fall through to network fetch
    }

    api
      .run(id)
      .then((run) => {
        if (run.score) {
          setData({ run, score: run.score, postmortem: null as unknown as Postmortem });
        } else {
          navigate(`/runs/${id}`, { replace: true });
        }
      })
      .catch((err: unknown) => {
        pushError(err instanceof ApiError ? err.message : "Failed to load result");
      });
  }, [id, location.state, navigate, pushError]);

  if (!id) return null;

  return (
    <div className="min-h-screen bg-ground">
      <PageHeader />
      <div className="mx-auto max-w-4xl p-6">
        {!data ? (
          <SkeletonRows count={10} />
        ) : (
          <div className="mount-stagger flex flex-col gap-8">
            <div>
              <div className="font-mono text-2xs uppercase tracking-caps text-success">Incident resolved</div>
              <h1 className="text-2xl font-medium text-ink">{data.run.incident.title}</h1>
            </div>

            <ScoreTable score={data.score} />

            {data.postmortem && <PostmortemSection postmortem={data.postmortem} />}

            {data.postmortem && (
              <div>
                <div className="panel-title px-0">Diffs</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="mb-1 font-mono text-2xs uppercase tracking-caps text-ink-faint">Your fix</div>
                    <DiffView diff={data.postmortem.your_diff} />
                  </div>
                  <div>
                    <div className="mb-1 font-mono text-2xs uppercase tracking-caps text-ink-faint">Reference fix</div>
                    <DiffView diff={data.postmortem.reference_diff} />
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Link to="/incidents" className="btn focus-ring inline-block">
                BACK TO INCIDENTS
              </Link>
              <Link to={`/runs/${id}`} className="btn focus-ring inline-block">
                VIEW WORKSPACE
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreTable({ score }: { score: Score }) {
  const rows: [string, string][] = [
    ["Time", formatTime(score.elapsed_seconds)],
    ["Hints used", String(score.hints_used)],
    ["Reproduced", score.reproduced ? "✓" : "✗"],
    ["Tests passed", `${score.tests_passed} / ${score.tests_total}`],
    ["Base", String(score.base)],
    ["Hint penalty", `−${score.hint_penalty}`],
    ["Time penalty", `−${score.time_penalty}`],
    ["Edit penalty", `−${score.edit_penalty}`],
    ["Repro bonus", `+${score.repro_bonus}`],
  ];

  return (
    <div>
      <table className="w-full border-collapse font-mono text-sm">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label} className="border-b border-line">
              <td className="py-1.5 text-ink-dim">{label}</td>
              <td className="py-1.5 text-right text-ink">{value}</td>
            </tr>
          ))}
          {score.unnecessary_edits.length > 0 && (
            <tr className="border-b border-line align-top">
              <td className="py-1.5 text-ink-dim">Unnecessary edits ({score.unnecessary_edits.length})</td>
              <td className="py-1.5 text-right text-ink-faint">{score.unnecessary_edits.join(", ")}</td>
            </tr>
          )}
          {score.solution_cap_applied && (
            <tr className="border-b border-line">
              <td className="py-1.5 text-warning" colSpan={2}>
                Solution reveal cap applied
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="mt-3 flex items-baseline justify-between border-t border-line-strong pt-3">
        <span className="font-mono text-xs uppercase tracking-caps text-ink-faint">Score</span>
        <span className="font-mono text-2xl text-ink">{score.total}</span>
      </div>
    </div>
  );
}

function PostmortemSection({ postmortem }: { postmortem: Postmortem }) {
  const sections: [string, string][] = [
    ["Root cause", postmortem.root_cause],
    ["Why it happened", postmortem.why_it_happened],
    ["Why tests missed it", postmortem.why_tests_missed],
    ["Prevention", postmortem.prevention],
  ];
  return (
    <div>
      <div className="panel-title px-0">Postmortem</div>
      <div className="flex flex-col gap-4">
        {sections.map(([label, text]) => (
          <div key={label}>
            <div className="mb-1 font-mono text-2xs uppercase tracking-caps text-ink-faint">{label}</div>
            <p className="text-sm leading-relaxed text-ink-dim">{text}</p>
          </div>
        ))}
        <div>
          <div className="mb-1 font-mono text-2xs uppercase tracking-caps text-ink-faint">Solution</div>
          <p className="text-sm leading-relaxed text-ink-dim">{postmortem.solution_explanation}</p>
        </div>
      </div>
    </div>
  );
}

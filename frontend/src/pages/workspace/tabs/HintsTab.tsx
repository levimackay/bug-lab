import { useState } from "react";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { DiffView } from "../../../components/DiffView";
import { useWorkspaceContext } from "../WorkspaceContext";

export function HintsTab() {
  const { run, requestHint, revealSolutionDialogOpen, setRevealSolutionDialogOpen, revealSolution } = useWorkspaceContext();
  const [requesting, setRequesting] = useState(false);
  const [revealing, setRevealing] = useState(false);

  if (!run) return null;

  const incident = run.incident;
  const exhausted = run.hints_revealed >= incident.hint_count;
  const nextCost = incident.hint_costs[run.hints_revealed] ?? 0;

  async function onRequestHint() {
    setRequesting(true);
    try {
      await requestHint();
    } finally {
      setRequesting(false);
    }
  }

  async function onConfirmReveal() {
    setRevealing(true);
    setRevealSolutionDialogOpen(false);
    try {
      await revealSolution();
    } finally {
      setRevealing(false);
    }
  }

  return (
    <div className="flex flex-col gap-4 p-3">
      <div className="flex flex-col gap-2">
        {run.hints.map((hint, i) => (
          <div key={i} className="border border-line bg-panel p-2">
            <div className="mb-1 flex justify-between font-mono text-2xs uppercase tracking-caps text-ink-faint">
              <span>{hint.level}</span>
              <span>−{hint.cost}</span>
            </div>
            <div className="text-xs text-ink-dim">{hint.text}</div>
          </div>
        ))}
        {run.hints.length === 0 && <div className="font-mono text-xs text-ink-faint">No hints revealed.</div>}
      </div>

      <button className="btn focus-ring" onClick={onRequestHint} disabled={exhausted || requesting}>
        {requesting ? "REQUESTING…" : exhausted ? "NO HINTS LEFT" : `REQUEST HINT (−${nextCost})`}
      </button>

      <div className="border-t border-line pt-4">
        {!run.solution_revealed ? (
          <button className="btn focus-ring" onClick={() => setRevealSolutionDialogOpen(true)} disabled={revealing}>
            {revealing ? "REVEALING…" : "REVEAL SOLUTION"}
          </button>
        ) : (
          run.solution && (
            <div className="flex flex-col gap-2">
              <div className="panel-title px-0">Solution</div>
              <p className="text-xs text-ink-dim">{run.solution.explanation}</p>
              <DiffView diff={run.solution.diff} />
            </div>
          )
        )}
      </div>

      {revealSolutionDialogOpen && (
        <ConfirmDialog
          title="Reveal solution?"
          body="Revealing the solution caps your final score for this run. Hints already used still count against you."
          confirmLabel="REVEAL"
          onConfirm={onConfirmReveal}
          onCancel={() => setRevealSolutionDialogOpen(false)}
        />
      )}
    </div>
  );
}

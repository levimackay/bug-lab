import { useState } from "react";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ReproduceDialog } from "./ReproduceDialog";
import { useWorkspaceContext } from "./WorkspaceContext";
import type { ActionKind } from "./types";

export function ActionBar() {
  const {
    run,
    runningAction,
    doRun,
    doBuild,
    doTest,
    doSubmit,
    doReset,
    testRun,
    reproduceDialogOpen,
    setReproduceDialogOpen,
    resetDialogOpen,
    setResetDialogOpen,
  } = useWorkspaceContext();
  const [confirmingReset, setConfirmingReset] = useState(false);

  if (!run) return <div className="h-10 border-t border-line" />;

  const busy = runningAction !== null;
  const testsPass = testRun !== null && testRun.ok && testRun.summary.failed === 0 && testRun.summary.error === 0;
  const primary: ActionKind = testsPass ? "submit" : "test";

  function btnClass(kind: ActionKind, resolved = false) {
    if (runningAction === kind) return "btn btn-running focus-ring";
    if (resolved) return "btn btn-success focus-ring";
    if (kind === primary) return "btn btn-primary focus-ring";
    return "btn focus-ring";
  }

  async function onReset() {
    setConfirmingReset(true);
    setResetDialogOpen(false);
    try {
      await doReset();
    } finally {
      setConfirmingReset(false);
    }
  }

  return (
    <div className="flex h-10 items-center gap-2 border-t border-line px-2">
      <button className={btnClass("run")} onClick={doRun} disabled={busy}>
        {runningAction === "run" ? "RUNNING…" : "RUN"}
      </button>
      {run.incident.commands.build && (
        <button className={btnClass("build")} onClick={doBuild} disabled={busy}>
          {runningAction === "build" ? "BUILDING…" : "BUILD"}
        </button>
      )}
      <button className={btnClass("test")} onClick={doTest} disabled={busy}>
        {runningAction === "test" ? "RUNNING…" : "TESTS"}
      </button>
      <button className={btnClass("reproduce")} onClick={() => setReproduceDialogOpen(true)} disabled={busy}>
        REPRODUCE
      </button>
      <button
        className={btnClass("submit", run.status === "resolved")}
        onClick={doSubmit}
        disabled={busy}
      >
        {runningAction === "submit" ? "SUBMITTING…" : "SUBMIT"}
      </button>

      <div className="ml-auto">
        <button className="btn focus-ring" onClick={() => setResetDialogOpen(true)} disabled={busy || confirmingReset}>
          RESET
        </button>
      </div>

      {reproduceDialogOpen && <ReproduceDialog onClose={() => setReproduceDialogOpen(false)} />}

      {resetDialogOpen && (
        <ConfirmDialog
          title="Reset this run?"
          body="This abandons the current run and its workspace, and starts a fresh copy of the incident. This cannot be undone."
          confirmLabel="RESET"
          onConfirm={onReset}
          onCancel={() => setResetDialogOpen(false)}
        />
      )}
    </div>
  );
}

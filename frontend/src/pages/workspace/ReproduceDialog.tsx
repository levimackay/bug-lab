import { useEffect, useRef, useState } from "react";
import type { ReproduceResult } from "../../api/types";
import { useDialogFocusTrap } from "../../hooks/useDialogFocusTrap";
import { useWorkspaceContext } from "./WorkspaceContext";

export function ReproduceDialog({ onClose }: { onClose: () => void }) {
  const { files, doReproduce, run } = useWorkspaceContext();
  const testFiles = files.filter((f) => f.startsWith("tests/") || f.includes("/tests/"));
  const [path, setPath] = useState(run?.repro_test_path ?? testFiles[0] ?? "tests/test_repro.py");
  const [result, setResult] = useState<ReproduceResult | null>(null);
  const [running, setRunning] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useDialogFocusTrap(dialogRef, onClose);
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function onConfirm() {
    setRunning(true);
    try {
      const r = await doReproduce(path);
      setResult(r);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-label="Reproduce the bug" className="w-[480px] border border-line-strong bg-panel">
        <div className="panel-title border-b border-line">Reproduce</div>
        <div className="flex flex-col gap-3 p-4">
          <p className="font-mono text-2xs text-ink-dim">
            The test must fail against the original code and pass against your current workspace.
          </p>
          <label className="flex flex-col gap-1 font-mono text-2xs text-ink-faint">
            Test path
            <input
              ref={inputRef}
              list="repro-test-files"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="focus-ring border border-line bg-ground px-2 py-1 font-mono text-xs text-ink outline-none"
            />
            <datalist id="repro-test-files">
              {testFiles.map((f) => (
                <option key={f} value={f} />
              ))}
            </datalist>
          </label>

          {result && (
            <div role="status" aria-live="polite" className="flex flex-col gap-2 border-t border-line pt-3">
              <div className={"font-mono text-sm " + (result.reproduced ? "text-success" : "text-failure")}>
                {result.reproduced ? "✓ BUG REPRODUCED" : `✗ ${result.verdict}`}
              </div>
              <div className="grid grid-cols-2 gap-3 font-mono text-2xs text-ink-dim">
                <div>
                  <div className="text-ink-faint">before (pristine)</div>
                  {result.before ? (
                    <div>
                      {result.before.summary.passed} passed, {result.before.summary.failed} failed
                    </div>
                  ) : (
                    <div>—</div>
                  )}
                </div>
                <div>
                  <div className="text-ink-faint">after (workspace)</div>
                  {result.after ? (
                    <div>
                      {result.after.summary.passed} passed, {result.after.summary.failed} failed
                    </div>
                  ) : (
                    <div>—</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t border-line p-2">
          <button className="btn focus-ring" onClick={onClose}>
            CLOSE
          </button>
          <button className="btn btn-primary focus-ring" onClick={onConfirm} disabled={running || !path}>
            {running ? "RUNNING…" : "CONFIRM"}
          </button>
        </div>
      </div>
    </div>
  );
}

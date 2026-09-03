import { useEffect, useRef, useState } from "react";
import type { Language } from "../../api/types";
import { useDialogFocusTrap } from "../../hooks/useDialogFocusTrap";
import { useWorkspaceContext } from "./WorkspaceContext";

const DEFAULT_REPRO_PATH: Record<Language, string> = {
  python: "tests/test_repro.py",
  javascript: "tests/test_repro.js",
  typescript: "tests/test_repro.ts",
  c: "tests/test_repro.c",
};

export function NewFileDialog({ onClose }: { onClose: () => void }) {
  const { run, createFile } = useWorkspaceContext();
  const [path, setPath] = useState(DEFAULT_REPRO_PATH[run?.incident.language ?? "python"]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useDialogFocusTrap(dialogRef, onClose);
  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  async function onCreate() {
    if (!path.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await createFile(path.trim());
      onClose();
    } catch {
      setError("Could not create file.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-label="New file" className="w-96 border border-line-strong bg-panel">
        <div className="panel-title border-b border-line">New file</div>
        <div className="flex flex-col gap-2 p-4">
          <input
            ref={inputRef}
            value={path}
            onChange={(e) => setPath(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onCreate();
            }}
            className="focus-ring border border-line bg-ground px-2 py-1 font-mono text-xs text-ink outline-none"
          />
          {error && (
            <div role="alert" className="font-mono text-2xs text-failure">
              {error}
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t border-line p-2">
          <button className="btn focus-ring" onClick={onClose}>
            CANCEL
          </button>
          <button className="btn btn-primary focus-ring" onClick={onCreate} disabled={creating}>
            {creating ? "CREATING…" : "CREATE"}
          </button>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useRef, type ReactNode } from "react";

interface ConfirmDialogProps {
  title: string;
  body: ReactNode;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ title, body, confirmLabel = "CONFIRM", onConfirm, onCancel }: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    confirmRef.current?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key === "Tab") {
        const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
        );
        if (!focusable || focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        className="w-96 border border-line-strong bg-panel"
      >
        <div className="panel-title border-b border-line">{title}</div>
        <div id="confirm-dialog-title" className="sr-only">
          {title}
        </div>
        <div className="p-4 text-sm text-ink">{body}</div>
        <div className="flex justify-end gap-2 border-t border-line p-2">
          <button className="btn focus-ring" onClick={onCancel}>
            CANCEL
          </button>
          <button ref={confirmRef} className="btn btn-primary focus-ring" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

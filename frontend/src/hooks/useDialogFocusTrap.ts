import { useEffect, useRef, type RefObject } from "react";

/**
 * Traps Tab focus inside a dialog, closes it on Escape (via a document-level
 * listener, so it fires regardless of which element inside the dialog holds
 * focus), and restores focus to whatever was focused before the dialog opened.
 *
 * The mount/unmount effect runs exactly once — via a ref for `onClose` — so
 * that re-renders while the dialog is open (e.g. typing in a search box)
 * don't recapture "previously focused" as the dialog's own input, which
 * would break restoring focus to the real trigger element on close.
 */
export function useDialogFocusTrap(dialogRef: RefObject<HTMLElement | null>, onClose: () => void) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onCloseRef.current();
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
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus?.();
    };
    // Runs once for the dialog's mount/unmount lifecycle; dialogRef is a
    // stable ref and onCloseRef.current is read fresh inside the handler.
  }, []);
}

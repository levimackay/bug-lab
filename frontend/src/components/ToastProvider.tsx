import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

interface ToastItem {
  id: number;
  message: string;
}

interface ToastContextValue {
  pushError: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushError = useCallback(
    (message: string) => {
      const id = nextId.current++;
      setToasts((prev) => [...prev, { id, message }]);
      window.setTimeout(() => dismiss(id), 6000);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ pushError }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <button
            key={t.id}
            onClick={() => dismiss(t.id)}
            className="focus-ring block max-w-sm border border-failure bg-panel px-3 py-2 text-left font-mono text-xs text-ink"
            style={{ borderLeftWidth: 2 }}
          >
            {t.message}
          </button>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

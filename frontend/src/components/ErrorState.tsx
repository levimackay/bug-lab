export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-3 p-6 font-mono text-sm">
      <div className="text-failure">{message}</div>
      <button className="btn focus-ring" onClick={onRetry}>
        RETRY
      </button>
    </div>
  );
}

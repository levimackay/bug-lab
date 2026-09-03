function lineClass(line: string): string {
  if (line.startsWith("+") && !line.startsWith("+++")) return "bg-success/[0.12] text-ink";
  if (line.startsWith("-") && !line.startsWith("---")) return "bg-failure/[0.12] text-ink";
  if (line.startsWith("@@")) return "text-info";
  return "text-ink-faint";
}

export function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n");
  return (
    <pre className="overflow-x-auto border border-line bg-panel p-2 font-mono text-2xs leading-relaxed">
      {lines.map((line, i) => (
        <div key={i} className={lineClass(line)}>
          {line || " "}
        </div>
      ))}
    </pre>
  );
}

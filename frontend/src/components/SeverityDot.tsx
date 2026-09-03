import type { Severity } from "../api/types";

const COLOR: Record<Severity, string> = {
  low: "var(--color-severity-low)",
  medium: "var(--color-severity-medium)",
  high: "var(--color-severity-high)",
  critical: "var(--color-severity-critical)",
};

export function SeverityDot({ severity, pulse = false }: { severity: Severity; pulse?: boolean }) {
  return (
    <span
      className={pulse && severity === "critical" ? "severity-pulse inline-block" : "inline-block"}
      style={{
        width: 8,
        height: 8,
        background: COLOR[severity],
        boxShadow: "0 0 0 1px rgba(0,0,0,0.4)",
      }}
    />
  );
}

export function severityLabel(severity: Severity): string {
  return severity.toUpperCase();
}

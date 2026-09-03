import { useState } from "react";
import type { TestResult } from "../../../api/types";
import { useWorkspaceContext } from "../WorkspaceContext";

const STATUS_GLYPH: Record<TestResult["status"], string> = {
  passed: "✓",
  failed: "✗",
  error: "✗",
  skipped: "○",
};

const STATUS_COLOR: Record<TestResult["status"], string> = {
  passed: "text-success",
  failed: "text-failure",
  error: "text-failure",
  skipped: "text-ink-faint",
};

function TestRow({ test }: { test: TestResult }) {
  const [expanded, setExpanded] = useState(false);
  const canExpand = (test.status === "failed" || test.status === "error") && test.message;

  return (
    <div>
      <button
        className="focus-ring flex w-full items-center gap-2 px-2 py-1 text-left hover:bg-raised disabled:cursor-default"
        onClick={() => canExpand && setExpanded((e) => !e)}
        disabled={!canExpand}
      >
        <span className={"w-3 font-mono " + STATUS_COLOR[test.status]}>{STATUS_GLYPH[test.status]}</span>
        <span className="flex-1 truncate font-mono text-xs text-ink-dim" title={test.name}>
          {test.name}
        </span>
        <span className="font-mono text-2xs text-ink-faint">{test.duration_ms}ms</span>
      </button>
      {expanded && canExpand && (
        <div className="border-l-2 border-failure bg-panel px-3 py-2 font-mono text-2xs text-ink-dim">{test.message}</div>
      )}
    </div>
  );
}

export function TestsTab() {
  const { testRun, hiddenTests } = useWorkspaceContext();
  const [showRaw, setShowRaw] = useState(false);

  if (!testRun) {
    return <div className="p-3 font-mono text-xs text-ink-faint">No test run yet. Run TESTS from the action bar.</div>;
  }

  const { summary } = testRun;

  return (
    <div className="flex flex-col">
      <div className="border-b border-line px-2 py-1.5 font-mono text-xs">
        <span className="text-success">{summary.passed} passed</span>
        {", "}
        <span className={summary.failed > 0 ? "text-failure" : "text-ink-dim"}>{summary.failed} failed</span>
        {", "}
        <span className={summary.error > 0 ? "text-failure" : "text-ink-dim"}>{summary.error} errors</span>
        {summary.skipped > 0 && <span className="text-ink-faint">, {summary.skipped} skipped</span>}
      </div>

      {testRun.parse_error && (
        <div className="border-b border-line bg-panel px-2 py-1.5 font-mono text-2xs text-warning">{testRun.parse_error}</div>
      )}

      <div className="divide-y divide-line">
        {testRun.tests.map((t) => (
          <TestRow key={t.name} test={t} />
        ))}
      </div>

      {hiddenTests && (
        <div className="mt-2 border-t border-line">
          <div className="panel-title">Hidden tests</div>
          <div className="divide-y divide-line">
            {hiddenTests.tests.map((t) => (
              <div key={t.name} className="flex items-center gap-2 px-2 py-1">
                <span className={"w-3 font-mono " + STATUS_COLOR[t.status as TestResult["status"]]}>
                  {STATUS_GLYPH[t.status as TestResult["status"]] ?? "○"}
                </span>
                <span className="flex-1 truncate font-mono text-xs text-ink-dim" title={t.name}>
                  {t.name}
                </span>
                <span className="font-mono text-2xs text-ink-faint">hidden</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="focus-ring border-t border-line px-2 py-1.5 text-left font-mono text-2xs text-ink-faint hover:text-ink-dim" onClick={() => setShowRaw((s) => !s)}>
        {showRaw ? "hide raw output" : "show raw output"}
      </button>
      {showRaw && (
        <pre className="whitespace-pre-wrap border-t border-line bg-panel p-2 font-mono text-2xs text-ink-dim">
          {testRun.exec.stdout}
          {testRun.exec.stderr}
        </pre>
      )}
    </div>
  );
}

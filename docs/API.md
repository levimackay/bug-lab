# Bug Lab HTTP API

All routes are under `/api`. JSON in, JSON out. Errors are `{ "detail": "message" }`
with a 4xx/5xx status. There is one implicit local user; there is no auth.

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. In production the
FastAPI app serves `frontend/dist` itself.

## Shapes

```ts
type Severity = "low" | "medium" | "high" | "critical";
type Difficulty = "beginner" | "intermediate" | "advanced";
type Language = "python" | "javascript" | "typescript" | "c";
type Tool = "logs" | "stack_trace" | "tests" | "runtime";

interface IncidentSummary {
  id: string;                 // "inc-012-race-oversell"
  number: number;             // 12
  title: string;
  severity: Severity;
  difficulty: Difficulty;
  language: Language;
  system: string;             // "Inventory Service"
  categories: string[];       // specialisations: "concurrency", "memory", "networking", "algorithms", ...
  description: string;        // markdown-ish plain text, paragraphs separated by blank lines
  symptoms: string[];
  environment: string;        // preformatted tree, render in monospace verbatim
  expected_behavior: string;
  broken_behavior: string;
  tools: Tool[];              // which investigation tabs to enable
  commands: { run: string; test: string; build: string };   // shown to the user, e.g. "pytest -q"
  hint_count: number;
  hint_costs: number[];
  scoring: { base: number; par_seconds: number; repro_bonus: number };
  tags: string[];
  // progress
  status: "unsolved" | "in_progress" | "solved";
  best_score: number | null;
  active_run_id: string | null;
  attempts: number;
}

interface Hint { level: "direction" | "subsystem" | "area"; text: string; cost: number }

interface Run {
  id: string;
  incident_id: string;
  status: "active" | "resolved" | "abandoned";
  started_at: string;         // ISO 8601
  resolved_at: string | null;
  elapsed_seconds: number;    // measured server-side (started_at -> now or resolved_at)
  hints_revealed: number;
  hints: Hint[];              // only the revealed ones
  solution_revealed: boolean;
  solution: { files: string[]; explanation: string; diff: string } | null;  // only after reveal or resolve
  hypothesis: string;
  reproduced: boolean;
  repro_test_path: string | null;
  tests_run: number;          // count of test invocations (button or terminal doesn't matter: only API test runs count)
  score: Score | null;
  incident: IncidentSummary;
}

interface ExecResult {
  stdout: string; stderr: string; exit_code: number;
  duration_ms: number; timed_out: boolean; max_rss_kb: number;
}

interface Frame { file: string; line: number; function: string }
interface StackTrace { kind: "python" | "node" | "asan" | "ubsan"; header: string; frames: Frame[] }

interface TestResult { name: string; status: "passed" | "failed" | "error" | "skipped"; duration_ms: number; message: string }
interface TestRun {
  ok: boolean;
  summary: { passed: number; failed: number; error: number; skipped: number; total: number };
  tests: TestResult[];
  exec: ExecResult;
  parse_error: string;        // "" when the report parsed; otherwise why there are no results
}

interface Score {
  total: number; base: number;
  hint_penalty: number; time_penalty: number;
  unnecessary_edits: string[]; edit_penalty: number;
  repro_bonus: number; solution_cap_applied: boolean;
  elapsed_seconds: number; hints_used: number; tests_run: number; reproduced: boolean;
  tests_passed: number; tests_total: number;
}

interface Postmortem {
  root_cause: string; why_it_happened: string; why_tests_missed: string; prevention: string;
  solution_explanation: string;
  your_diff: string;          // unified diff of the user's workspace vs pristine
  reference_diff: string;     // unified diff of solution/ vs project/
}
```

## Incidents

- `GET /api/incidents` → `{ incidents: IncidentSummary[] }` ordered by number.
- `GET /api/incidents/{id}` → `IncidentSummary`.
- `POST /api/incidents/{id}/runs` → `Run`. Returns the active run if one exists, otherwise creates one (workspace copied from the incident).

## Runs

- `GET /api/runs/{id}` → `Run`.
- `POST /api/runs/{id}/reset` → `Run` (a **new** run; the old one becomes `abandoned`, its workspace is deleted).
- `PUT /api/runs/{id}/hypothesis` body `{ text: string }` → `Run`.
- `POST /api/runs/{id}/hints` → `Run` with one more hint revealed. `409` when none are left.
- `POST /api/runs/{id}/reveal-solution` body `{ confirm: true }` → `Run` with `solution` filled and `solution_revealed: true`. `400` without confirm.

## Files (all paths relative to the workspace root, forward slashes)

- `GET /api/runs/{id}/files` → `{ files: string[] }` flat sorted list. Bookkeeping dirs (`.buglab`, `.tmp`, `__pycache__`, `build`, `node_modules`) are never listed. Hidden tests are never present.
- `GET /api/runs/{id}/files/{path}` → `{ path, content, binary: boolean }` (`content` is "" for binary). `404` if missing, `400` if outside the workspace.
- `PUT /api/runs/{id}/files/{path}` body `{ content }` → `{ path, saved: true }`. Creates parent directories. Creating new files (e.g. a reproduction test) is allowed.
- `DELETE /api/runs/{id}/files/{path}` → `{ path, deleted: true }`.
- `GET /api/runs/{id}/search?q=text` → `{ matches: [{ path, line, text }] }` (case-insensitive substring, max 200).

## Execution (each runs inside the sandbox and records an event)

- `POST /api/runs/{id}/run` → `{ exec: ExecResult, stack_trace: StackTrace | null }` runs `commands.run`.
- `POST /api/runs/{id}/build` → same shape; `{ exec: null, stack_trace: null }` if the incident has no build step.
- `POST /api/runs/{id}/test` body `{ target?: string }` → `TestRun & { stack_trace: StackTrace | null }`. Increments `tests_run`.
- `POST /api/runs/{id}/reproduce` body `{ test_path: string }` →
  `{ reproduced: boolean, verdict: string, before: TestRun | null, after: TestRun | null }`.
  `before` = the user's test file against the pristine project, `after` = against the current workspace. Sets `run.reproduced` and `repro_test_path` when true.
- `POST /api/runs/{id}/submit` →
  ```ts
  {
    resolved: boolean;
    visible: TestRun;                 // the project's own tests
    hidden: { ok: boolean; summary: TestRun["summary"]; tests: { name: string; status: string; message: string }[] };
    score: Score | null;              // only when resolved
    postmortem: Postmortem | null;    // only when resolved
    run: Run;
  }
  ```
  Hidden test *bodies* are never returned; names and assertion messages are.
  Submitting an already resolved run re-runs everything but does not change the stored score.

## Evidence

- `GET /api/runs/{id}/logs` → `{ files: [{ name: string, content: string }], last_run: { stdout, stderr, exit_code, at } | null }`. `files` are the incident's `logs/` directory as currently on disk.
- `GET /api/runs/{id}/runtime` → `{ last: ExecRecord | null, history: ExecRecord[] }` where `ExecRecord = { kind: "run" | "build" | "test" | "hidden" | "reproduce", at: string, exec: ExecResult }` (newest first, max 30).

## Terminal

- `WS /api/runs/{id}/terminal` — a real shell (`zsh`) inside the sandbox, cwd = workspace.
  - client → server: text frames are raw keystrokes; a text frame that parses as JSON `{ "type": "resize", "cols": n, "rows": n }` resizes the pty.
  - server → client: text frames of terminal output (UTF-8, may contain ANSI).
  - Closing the socket kills the shell. Reconnecting spawns a fresh shell.

## Progress & misc

- `GET /api/progress` →
  ```ts
  {
    solved: number; total: number;
    by_difficulty: Record<Difficulty, { solved: number; total: number }>;
    by_category: Record<string, { solved: number; total: number; avg_score: number | null }>;
    recent: { run_id: string; incident_id: string; number: number; title: string; score: number; resolved_at: string; elapsed_seconds: number; hints_used: number; reproduced: boolean }[];
    weakest: string[];       // categories ordered by lowest solved ratio then avg score
    totals: { score_sum: number; avg_score: number | null; hints_used: number; reproduced: number; resolved_runs: number };
  }
  ```
- `GET /api/settings` → `Record<string, string>`; `PUT /api/settings` body `Record<string, string>` merges.
- `GET /api/mentor` → `{ enabled: boolean }`.
- `GET /api/health` → `{ ok: true, incidents: number, sandbox: "seatbelt" }`.

export type Severity = "low" | "medium" | "high" | "critical";
export type Difficulty = "beginner" | "intermediate" | "advanced";
export type Language = "python" | "javascript" | "typescript" | "c";
export type Tool = "logs" | "stack_trace" | "tests" | "runtime";

export interface IncidentSummary {
  id: string;
  number: number;
  title: string;
  severity: Severity;
  difficulty: Difficulty;
  language: Language;
  system: string;
  categories: string[];
  description: string;
  symptoms: string[];
  environment: string;
  expected_behavior: string;
  broken_behavior: string;
  tools: Tool[];
  commands: { run: string; test: string; build: string };
  hint_count: number;
  hint_costs: number[];
  scoring: { base: number; par_seconds: number; repro_bonus: number };
  tags: string[];
  status: "unsolved" | "in_progress" | "solved";
  best_score: number | null;
  active_run_id: string | null;
  attempts: number;
}

export interface Hint {
  level: "direction" | "subsystem" | "area";
  text: string;
  cost: number;
}

export interface Score {
  total: number;
  base: number;
  hint_penalty: number;
  time_penalty: number;
  unnecessary_edits: string[];
  edit_penalty: number;
  repro_bonus: number;
  solution_cap_applied: boolean;
  elapsed_seconds: number;
  hints_used: number;
  tests_run: number;
  reproduced: boolean;
  tests_passed: number;
  tests_total: number;
}

export interface Run {
  id: string;
  incident_id: string;
  status: "active" | "resolved" | "abandoned";
  started_at: string;
  resolved_at: string | null;
  elapsed_seconds: number;
  hints_revealed: number;
  hints: Hint[];
  solution_revealed: boolean;
  solution: { files: string[]; explanation: string; diff: string } | null;
  hypothesis: string;
  reproduced: boolean;
  repro_test_path: string | null;
  tests_run: number;
  score: Score | null;
  incident: IncidentSummary;
}

export interface ExecResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
  timed_out: boolean;
  max_rss_kb: number;
}

export interface Frame {
  file: string;
  line: number;
  function: string;
}

export interface StackTrace {
  kind: "python" | "node" | "asan" | "ubsan";
  header: string;
  frames: Frame[];
}

export interface TestResult {
  name: string;
  status: "passed" | "failed" | "error" | "skipped";
  duration_ms: number;
  message: string;
}

export interface TestRun {
  ok: boolean;
  summary: { passed: number; failed: number; error: number; skipped: number; total: number };
  tests: TestResult[];
  exec: ExecResult;
  parse_error: string;
}

export interface Postmortem {
  root_cause: string;
  why_it_happened: string;
  why_tests_missed: string;
  prevention: string;
  solution_explanation: string;
  your_diff: string;
  reference_diff: string;
}

export interface ExecRecord {
  kind: "run" | "build" | "test" | "hidden" | "reproduce";
  at: string;
  exec: ExecResult;
}

export interface RuntimeInfo {
  last: ExecRecord | null;
  history: ExecRecord[];
}

export interface LogsInfo {
  files: { name: string; content: string }[];
  last_run: { stdout: string; stderr: string; exit_code: number; at: string } | null;
}

export interface RunActionResult {
  exec: ExecResult;
  stack_trace: StackTrace | null;
}

export interface ReproduceResult {
  reproduced: boolean;
  verdict: string;
  before: TestRun | null;
  after: TestRun | null;
}

export interface SubmitResult {
  resolved: boolean;
  visible: TestRun;
  hidden: {
    ok: boolean;
    summary: TestRun["summary"];
    tests: { name: string; status: string; message: string }[];
  };
  score: Score | null;
  postmortem: Postmortem | null;
  run: Run;
}

export interface FileEntry {
  path: string;
  content: string;
  binary: boolean;
}

export interface SearchMatch {
  path: string;
  line: number;
  text: string;
}

export interface ProgressInfo {
  solved: number;
  total: number;
  by_difficulty: Record<Difficulty, { solved: number; total: number }>;
  by_category: Record<string, { solved: number; total: number; avg_score: number | null }>;
  recent: {
    run_id: string;
    incident_id: string;
    number: number;
    title: string;
    score: number;
    resolved_at: string;
    elapsed_seconds: number;
    hints_used: number;
    reproduced: boolean;
  }[];
  weakest: string[];
  totals: {
    score_sum: number;
    avg_score: number | null;
    hints_used: number;
    reproduced: number;
    resolved_runs: number;
  };
}

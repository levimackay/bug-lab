import { http } from "./http";
import type {
  ExecRecord,
  FileEntry,
  IncidentSummary,
  LogsInfo,
  ProgressInfo,
  ReproduceResult,
  Run,
  RunActionResult,
  SearchMatch,
  SubmitResult,
  TestRun,
} from "./types";

export const api = {
  incidents: () => http.get<{ incidents: IncidentSummary[] }>("/incidents"),
  incident: (id: string) => http.get<IncidentSummary>(`/incidents/${id}`),
  startRun: (incidentId: string) => http.post<Run>(`/incidents/${incidentId}/runs`),

  run: (id: string) => http.get<Run>(`/runs/${id}`),
  resetRun: (id: string) => http.post<Run>(`/runs/${id}/reset`),
  saveHypothesis: (id: string, text: string) => http.put<Run>(`/runs/${id}/hypothesis`, { text }),
  requestHint: (id: string) => http.post<Run>(`/runs/${id}/hints`),
  revealSolution: (id: string) => http.post<Run>(`/runs/${id}/reveal-solution`, { confirm: true }),

  files: (id: string) => http.get<{ files: string[] }>(`/runs/${id}/files`),
  readFile: (id: string, path: string) => http.get<FileEntry>(`/runs/${id}/files/${path}`),
  writeFile: (id: string, path: string, content: string) =>
    http.put<{ path: string; saved: true }>(`/runs/${id}/files/${path}`, { content }),
  deleteFile: (id: string, path: string) =>
    http.delete<{ path: string; deleted: true }>(`/runs/${id}/files/${path}`),
  search: (id: string, q: string) =>
    http.get<{ matches: SearchMatch[] }>(`/runs/${id}/search?q=${encodeURIComponent(q)}`),

  runAction: (id: string) => http.post<RunActionResult>(`/runs/${id}/run`),
  build: (id: string) => http.post<RunActionResult>(`/runs/${id}/build`),
  test: (id: string, target?: string) =>
    http.post<TestRun & { stack_trace: RunActionResult["stack_trace"] }>(`/runs/${id}/test`, target ? { target } : undefined),
  reproduce: (id: string, testPath: string) =>
    http.post<ReproduceResult>(`/runs/${id}/reproduce`, { test_path: testPath }),
  submit: (id: string) => http.post<SubmitResult>(`/runs/${id}/submit`),

  logs: (id: string) => http.get<LogsInfo>(`/runs/${id}/logs`),
  runtime: (id: string) => http.get<{ last: ExecRecord | null; history: ExecRecord[] }>(`/runs/${id}/runtime`),

  progress: () => http.get<ProgressInfo>("/progress"),
};

export function terminalUrl(runId: string): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/api/runs/${runId}/terminal`;
}

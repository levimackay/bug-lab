import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import type * as monaco from "monaco-editor";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/endpoints";
import { ApiError } from "../../api/http";
import type { LogsInfo, Run, RuntimeInfo, StackTrace, SubmitResult, TestRun } from "../../api/types";
import { useToast } from "../../components/ToastProvider";
import { readLocalStorage, writeLocalStorage } from "../../hooks/useLocalStorage";
import type { ActionKind, InvestigationTabId, OpenFile, SaveState } from "./types";

interface PendingReveal {
  path: string;
  line: number;
}

interface WorkspaceContextValue {
  runId: string;
  run: Run | null;
  loading: boolean;
  loadError: string | null;
  retryLoad: () => void;
  elapsedSeconds: number;
  refreshRun: () => Promise<void>;

  files: string[];
  refreshFiles: () => Promise<void>;

  openFiles: OpenFile[];
  activeFile: string | null;
  openFile: (path: string) => void;
  closeFile: (path: string) => void;
  getContent: (path: string) => string | null;
  updateContent: (path: string, content: string) => void;
  saveActiveFile: () => void;
  createFile: (path: string) => Promise<void>;

  editorRef: React.MutableRefObject<monaco.editor.IStandaloneCodeEditor | null>;
  pendingReveal: PendingReveal | null;
  revealFrame: (path: string, line: number) => void;
  clearPendingReveal: () => void;

  investigationTab: InvestigationTabId;
  setInvestigationTab: (tab: InvestigationTabId) => void;

  testRun: (TestRun & { stack_trace: StackTrace | null }) | null;
  hiddenTests: SubmitResult["hidden"] | null;
  stackTrace: StackTrace | null;
  runtimeInfo: RuntimeInfo | null;
  logsInfo: LogsInfo | null;
  refreshLogs: () => Promise<void>;
  refreshRuntime: () => Promise<void>;

  runningAction: ActionKind | null;
  doRun: () => Promise<void>;
  doBuild: () => Promise<void>;
  doTest: () => Promise<void>;
  doReproduce: (testPath: string) => Promise<Awaited<ReturnType<typeof api.reproduce>>>;
  doSubmit: () => Promise<void>;
  doReset: () => Promise<void>;

  requestHint: () => Promise<void>;
  revealSolution: () => Promise<void>;
  saveHypothesis: (text: string) => Promise<void>;

  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  fileSwitcherOpen: boolean;
  setFileSwitcherOpen: (open: boolean) => void;
  newFileDialogOpen: boolean;
  setNewFileDialogOpen: (open: boolean) => void;
  reproduceDialogOpen: boolean;
  setReproduceDialogOpen: (open: boolean) => void;
  resetDialogOpen: boolean;
  setResetDialogOpen: (open: boolean) => void;
  revealSolutionDialogOpen: boolean;
  setRevealSolutionDialogOpen: (open: boolean) => void;
  terminalFocusSignal: number;
  focusTerminal: () => void;
  terminalCollapsed: boolean;
  toggleTerminal: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function useWorkspaceContext(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspaceContext must be used within WorkspaceProvider");
  return ctx;
}

const AUTOSAVE_DELAY_MS = 1000;

export function WorkspaceProvider({ runId, children }: { runId: string; children: ReactNode }) {
  const { pushError } = useToast();
  const navigate = useNavigate();

  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const announce = useCallback((message: string) => setStatusMessage(message), []);

  const [files, setFiles] = useState<string[]>([]);

  const [openFiles, setOpenFiles] = useState<OpenFile[]>(() => readLocalStorage(`buglab:tabs:${runId}`, []));
  const [activeFile, setActiveFile] = useState<string | null>(() => readLocalStorage(`buglab:active:${runId}`, null));

  const contentCache = useRef<Map<string, string>>(new Map());
  const debounceTimers = useRef<Map<string, number>>(new Map());

  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const [pendingReveal, setPendingReveal] = useState<PendingReveal | null>(null);

  const [investigationTab, setInvestigationTab] = useState<InvestigationTabId>("incident");
  const [testRun, setTestRun] = useState<(TestRun & { stack_trace: StackTrace | null }) | null>(null);
  const [hiddenTests, setHiddenTests] = useState<SubmitResult["hidden"] | null>(null);
  const [stackTrace, setStackTrace] = useState<StackTrace | null>(null);
  const [runtimeInfo, setRuntimeInfo] = useState<RuntimeInfo | null>(null);
  const [logsInfo, setLogsInfo] = useState<LogsInfo | null>(null);

  const [runningAction, setRunningAction] = useState<ActionKind | null>(null);

  // A single slot so opening one dialog always closes any other: two dialogs
  // must never be visible (and fighting over Tab/Escape) at once.
  type DialogId = "commandPalette" | "fileSwitcher" | "newFile" | "reproduce" | "reset" | "revealSolution";
  const [openDialog, setOpenDialog] = useState<DialogId | null>(null);
  const makeDialogSetter = (id: DialogId) => (open: boolean) =>
    setOpenDialog((prev) => (open ? id : prev === id ? null : prev));

  const commandPaletteOpen = openDialog === "commandPalette";
  const setCommandPaletteOpen = makeDialogSetter("commandPalette");
  const fileSwitcherOpen = openDialog === "fileSwitcher";
  const setFileSwitcherOpen = makeDialogSetter("fileSwitcher");
  const newFileDialogOpen = openDialog === "newFile";
  const setNewFileDialogOpen = makeDialogSetter("newFile");
  const reproduceDialogOpen = openDialog === "reproduce";
  const setReproduceDialogOpen = makeDialogSetter("reproduce");
  const resetDialogOpen = openDialog === "reset";
  const setResetDialogOpen = makeDialogSetter("reset");
  const revealSolutionDialogOpen = openDialog === "revealSolution";
  const setRevealSolutionDialogOpen = makeDialogSetter("revealSolution");

  const [terminalFocusSignal, setTerminalFocusSignal] = useState(0);
  const [terminalCollapsed, setTerminalCollapsed] = useState(false);

  function focusTerminal() {
    setTerminalCollapsed(false);
    setTerminalFocusSignal((n) => n + 1);
  }

  function toggleTerminal() {
    setTerminalCollapsed((c) => !c);
  }

  // Load run + files on mount / run id change (WorkspaceProvider is remounted
  // fresh per runId, via the `key` prop in Workspace.tsx).
  const loadRun = useCallback(() => {
    setLoading(true);
    setLoadError(null);
    Promise.all([api.run(runId), api.files(runId)])
      .then(([r, f]) => {
        setRun(r);
        setElapsedSeconds(r.elapsed_seconds);
        setFiles(f.files);
      })
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.message : "Failed to load run";
        setLoadError(message);
        pushError(message);
      })
      .finally(() => setLoading(false));
  }, [runId, pushError]);

  useEffect(() => {
    loadRun();
  }, [loadRun]);

  // Local ticking clock.
  useEffect(() => {
    if (!run || run.status !== "active") return;
    const interval = window.setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => window.clearInterval(interval);
  }, [run]);

  async function refreshRun() {
    try {
      const r = await api.run(runId);
      setRun(r);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to refresh run");
    }
  }

  async function refreshFiles() {
    try {
      const f = await api.files(runId);
      setFiles(f.files);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to list files");
    }
  }

  async function refreshLogs() {
    try {
      const l = await api.logs(runId);
      setLogsInfo(l);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to load logs");
    }
  }

  async function refreshRuntime() {
    try {
      const r = await api.runtime(runId);
      setRuntimeInfo(r);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to load runtime info");
    }
  }

  function persistTabs(next: OpenFile[]) {
    setOpenFiles(next);
    writeLocalStorage(`buglab:tabs:${runId}`, next);
  }

  function persistActive(path: string | null) {
    setActiveFile(path);
    writeLocalStorage(`buglab:active:${runId}`, path);
  }

  const loadingPaths = useRef<Set<string>>(new Set());

  function loadContent(path: string) {
    if (contentCache.current.has(path) || loadingPaths.current.has(path)) return;
    loadingPaths.current.add(path);
    api
      .readFile(runId, path)
      .then((entry) => {
        contentCache.current.set(path, entry.content);
        // force a re-render so the editor picks up the newly loaded content
        setOpenFiles((prev) => [...prev]);
      })
      .catch((err: unknown) => {
        pushError(err instanceof ApiError ? err.message : `Failed to open ${path}`);
      })
      .finally(() => loadingPaths.current.delete(path));
  }

  // Tabs restored from localStorage have no content yet; fetch it before the
  // editor can show (or, worse, save) an empty buffer.
  useEffect(() => {
    for (const f of openFiles) loadContent(f.path);
  }, [runId]);

  function openFile(path: string) {
    if (!openFiles.some((f) => f.path === path)) {
      persistTabs([...openFiles, { path, saveState: "saved" }]);
    }
    persistActive(path);
    loadContent(path);
  }

  function closeFile(path: string) {
    const timer = debounceTimers.current.get(path);
    if (timer) {
      window.clearTimeout(timer);
      debounceTimers.current.delete(path);
    }
    const next = openFiles.filter((f) => f.path !== path);
    persistTabs(next);
    if (activeFile === path) {
      persistActive(next.length > 0 ? next[next.length - 1].path : null);
    }
  }

  /** null until the file's content has been fetched */
  function getContent(path: string): string | null {
    return contentCache.current.get(path) ?? null;
  }

  function setSaveState(path: string, state: SaveState) {
    setOpenFiles((prev) => prev.map((f) => (f.path === path ? { ...f, saveState: state } : f)));
    const name = path.split("/").pop();
    if (state === "saved") announce(`${name} saved.`);
    else if (state === "error") announce(`Failed to save ${name}.`);
  }

  function persistFile(path: string) {
    debounceTimers.current.delete(path);
    const content = contentCache.current.get(path);
    if (content === undefined) return; // never overwrite a file whose content was not loaded
    setSaveState(path, "saving");
    api
      .writeFile(runId, path, content)
      .then(() => setSaveState(path, "saved"))
      .catch((err: unknown) => {
        setSaveState(path, "error");
        pushError(err instanceof ApiError ? err.message : `Failed to save ${path}`);
      });
  }

  function updateContent(path: string, content: string) {
    contentCache.current.set(path, content);
    setSaveState(path, "unsaved");
    const existing = debounceTimers.current.get(path);
    if (existing) window.clearTimeout(existing);
    const timer = window.setTimeout(() => persistFile(path), AUTOSAVE_DELAY_MS);
    debounceTimers.current.set(path, timer);
  }

  function saveActiveFile() {
    if (!activeFile) return;
    const timer = debounceTimers.current.get(activeFile);
    if (timer) window.clearTimeout(timer);
    persistFile(activeFile);
  }

  async function createFile(path: string) {
    try {
      await api.writeFile(runId, path, "");
      contentCache.current.set(path, "");
      await refreshFiles();
      openFile(path);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : `Failed to create ${path}`);
      throw err;
    }
  }

  function revealFrame(path: string, line: number) {
    if (!files.includes(path)) return;
    openFile(path);
    setPendingReveal({ path, line });
  }

  function clearPendingReveal() {
    setPendingReveal(null);
  }

  async function doRun() {
    setRunningAction("run");
    announce("Running…");
    try {
      const result = await api.runAction(runId);
      setStackTrace(result.stack_trace);
      setInvestigationTab(result.stack_trace ? "trace" : "runtime");
      await Promise.all([refreshRuntime(), refreshLogs(), refreshRun()]);
      announce(`Run finished. Exit ${result.exec.exit_code}.`);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Run failed");
      announce("Run failed.");
    } finally {
      setRunningAction(null);
    }
  }

  async function doBuild() {
    setRunningAction("build");
    announce("Building…");
    try {
      const result = await api.build(runId);
      if (result.stack_trace) {
        setStackTrace(result.stack_trace);
        setInvestigationTab("trace");
      }
      await Promise.all([refreshRuntime(), refreshLogs(), refreshRun()]);
      announce(result.exec ? `Build finished. Exit ${result.exec.exit_code}.` : "Build finished.");
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Build failed");
      announce("Build failed.");
    } finally {
      setRunningAction(null);
    }
  }

  async function doTest() {
    setRunningAction("test");
    announce("Running tests…");
    try {
      const result = await api.test(runId);
      setTestRun(result);
      setHiddenTests(null);
      setStackTrace(result.stack_trace);
      setInvestigationTab("tests");
      await Promise.all([refreshLogs(), refreshRun()]);
      announce(`Tests: ${result.summary.passed} passed, ${result.summary.failed} failed.`);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Test run failed");
      announce("Test run failed.");
    } finally {
      setRunningAction(null);
    }
  }

  async function doReproduce(testPath: string) {
    setRunningAction("reproduce");
    try {
      const result = await api.reproduce(runId, testPath);
      await Promise.all([refreshLogs(), refreshRun()]);
      return result;
    } finally {
      setRunningAction(null);
    }
  }

  async function doSubmit() {
    setRunningAction("submit");
    announce("Submitting…");
    try {
      const result = await api.submit(runId);
      if (result.resolved) {
        announce("Incident resolved.");
        try {
          sessionStorage.setItem(`buglab:resolved:${runId}`, JSON.stringify(result));
        } catch {
          // ignore storage errors
        }
        navigate(`/runs/${runId}/resolved`, { state: result });
      } else {
        setTestRun({ ...result.visible, stack_trace: null });
        setHiddenTests(result.hidden);
        setInvestigationTab("tests");
        await refreshRun();
        announce(`Tests: ${result.visible.summary.passed} passed, ${result.visible.summary.failed} failed. Not resolved.`);
      }
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Submit failed");
      announce("Submit failed.");
    } finally {
      setRunningAction(null);
    }
  }

  async function doReset() {
    setRunningAction("reset");
    try {
      const next = await api.resetRun(runId);
      navigate(`/runs/${next.id}`, { replace: true });
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Reset failed");
    } finally {
      setRunningAction(null);
    }
  }

  async function requestHint() {
    try {
      const r = await api.requestHint(runId);
      setRun(r);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "No hints remaining");
    }
  }

  async function revealSolution() {
    try {
      const r = await api.revealSolution(runId);
      setRun(r);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to reveal solution");
    }
  }

  async function saveHypothesis(text: string) {
    try {
      const r = await api.saveHypothesis(runId, text);
      setRun(r);
    } catch (err) {
      pushError(err instanceof ApiError ? err.message : "Failed to save hypothesis");
    }
  }

  const value: WorkspaceContextValue = {
    runId,
    run,
    loading,
    loadError,
    retryLoad: loadRun,
    elapsedSeconds,
    refreshRun,
    files,
    refreshFiles,
    openFiles,
    activeFile,
    openFile,
    closeFile,
    getContent,
    updateContent,
    saveActiveFile,
    createFile,
    editorRef,
    pendingReveal,
    revealFrame,
    clearPendingReveal,
    investigationTab,
    setInvestigationTab,
    testRun,
    hiddenTests,
    stackTrace,
    runtimeInfo,
    logsInfo,
    refreshLogs,
    refreshRuntime,
    runningAction,
    doRun,
    doBuild,
    doTest,
    doReproduce,
    doSubmit,
    doReset,
    requestHint,
    revealSolution,
    saveHypothesis,
    commandPaletteOpen,
    setCommandPaletteOpen,
    fileSwitcherOpen,
    setFileSwitcherOpen,
    newFileDialogOpen,
    setNewFileDialogOpen,
    reproduceDialogOpen,
    setReproduceDialogOpen,
    resetDialogOpen,
    setResetDialogOpen,
    revealSolutionDialogOpen,
    setRevealSolutionDialogOpen,
    terminalFocusSignal,
    focusTerminal,
    terminalCollapsed,
    toggleTerminal,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
      {/* One status line for the whole workspace: run/test/save feedback. Toasts (errors) are announced separately, assertively. */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {statusMessage}
      </div>
    </WorkspaceContext.Provider>
  );
}

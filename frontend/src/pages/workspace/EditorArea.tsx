import Editor, { type OnMount } from "@monaco-editor/react";
import { useEffect, useRef } from "react";
import { defineIncidentConsoleTheme, ensureMonacoConfigured, languageForPath } from "./monacoSetup";
import { useWorkspaceContext } from "./WorkspaceContext";
import type { SaveState } from "./types";

ensureMonacoConfigured();

const SAVE_LABEL: Record<SaveState, string> = {
  saved: "saved",
  unsaved: "unsaved",
  saving: "saving…",
  error: "error",
};

const SAVE_COLOR: Record<SaveState, string> = {
  saved: "text-ink-faint",
  unsaved: "text-warning",
  saving: "text-info",
  error: "text-failure",
};

export function EditorArea() {
  const {
    openFiles,
    activeFile,
    openFile,
    closeFile,
    getContent,
    updateContent,
    saveActiveFile,
    editorRef,
    pendingReveal,
    clearPendingReveal,
  } = useWorkspaceContext();

  const decorationsRef = useRef<string[]>([]);

  const handleMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    defineIncidentConsoleTheme(monaco);
    editor.updateOptions({ theme: "incident-console" });
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      saveActiveFile();
    });
  };

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !pendingReveal || pendingReveal.path !== activeFile) return;
    editor.revealLineInCenter(pendingReveal.line);
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
      {
        range: {
          startLineNumber: pendingReveal.line,
          startColumn: 1,
          endLineNumber: pendingReveal.line,
          endColumn: 1,
        },
        options: { isWholeLine: true, className: "trace-line-highlight" },
      },
    ]);
    clearPendingReveal();
  }, [pendingReveal, activeFile, clearPendingReveal, editorRef]);

  if (openFiles.length === 0 || !activeFile) {
    return (
      <div className="flex flex-1 items-center justify-center font-mono text-xs text-ink-faint">
        No file open — ⌘P to find one
      </div>
    );
  }

  const content = getContent(activeFile);
  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex overflow-x-auto border-b border-line">
        {openFiles.map((f) => {
          const isActive = f.path === activeFile;
          const name = f.path.split("/").pop();
          return (
            <div
              key={f.path}
              onMouseDown={(e) => {
                if (e.button === 1) {
                  e.preventDefault();
                  closeFile(f.path);
                }
              }}
              className={
                "group flex shrink-0 items-center border-r border-line font-mono text-xs " +
                (isActive ? "bg-raised text-ink" : "text-ink-dim hover:bg-raised/60")
              }
            >
              <button
                className="focus-ring flex max-w-[180px] items-center gap-2 py-1.5 pl-3"
                aria-current={isActive ? "true" : undefined}
                title={f.path}
                onClick={() => openFile(f.path)}
              >
                <span className="truncate">{name}</span>
                {f.saveState !== "saved" && (
                  <>
                    <span
                      className={"h-1.5 w-1.5 shrink-0 " + (f.saveState === "error" ? "bg-failure" : "bg-warning")}
                      aria-hidden="true"
                    />
                    <span className="sr-only">{SAVE_LABEL[f.saveState]}</span>
                  </>
                )}
              </button>
              <button
                className="focus-ring px-2 py-1.5 text-ink-faint hover:text-ink"
                aria-label={`Close ${f.path}`}
                onClick={() => closeFile(f.path)}
              >
                ×
              </button>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between gap-2 border-b border-line px-2 py-0.5 font-mono text-2xs text-ink-faint">
        <span className="truncate" title={activeFile}>
          {activeFile}
        </span>
        <span className={"shrink-0 " + SAVE_COLOR[openFiles.find((f) => f.path === activeFile)?.saveState ?? "saved"]}>
          {SAVE_LABEL[openFiles.find((f) => f.path === activeFile)?.saveState ?? "saved"]}
        </span>
      </div>
      <div className="flex-1 overflow-hidden">
        {content === null ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-ink-faint">loading {activeFile}…</div>
        ) : (
        <Editor
          path={activeFile}
          language={languageForPath(activeFile)}
          value={content}
          theme="incident-console"
          onMount={handleMount}
          onChange={(value) => updateContent(activeFile, value ?? "")}
          options={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 13,
            minimap: { enabled: false },
            renderLineHighlight: "line",
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
        )}
      </div>
    </div>
  );
}

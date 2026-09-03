import { useEffect, useRef, useState } from "react";
import { ErrorState } from "../../components/ErrorState";
import { ResizeHandle } from "../../components/ResizeHandle";
import { SkeletonRows } from "../../components/Skeleton";
import { useMediaQuery } from "../../hooks/useMediaQuery";
import { useResizable } from "../../hooks/useResizable";
import { ActionBar } from "./ActionBar";
import { CommandPalette } from "./CommandPalette";
import { EditorArea } from "./EditorArea";
import { FileSwitcher } from "./FileSwitcher";
import { FileTree } from "./FileTree";
import { InvestigationPanel } from "./InvestigationPanel";
import { NewFileDialog } from "./NewFileDialog";
import { StatusStrip } from "./StatusStrip";
import { TerminalPanel } from "./TerminalPanel";
import { useWorkspaceContext } from "./WorkspaceContext";

export function WorkspaceLayout() {
  const ctx = useWorkspaceContext();
  const isNarrowInvestigation = useMediaQuery("(max-width: 1179px)");
  const isNarrowFiles = useMediaQuery("(max-width: 899px)");
  const [filesDrawerOpen, setFilesDrawerOpen] = useState(false);
  const [investigationDrawerOpen, setInvestigationDrawerOpen] = useState(false);

  const [filesWidth, onFilesResize, adjustFilesWidth] = useResizable("buglab:pane:files", 240, 160, 420, "x");
  const [investigationWidth, onInvestigationResize, adjustInvestigationWidth] = useResizable(
    "buglab:pane:investigation",
    360,
    260,
    560,
    "x",
    true,
  );
  const [terminalHeight, onTerminalResize, adjustTerminalHeight] = useResizable("buglab:pane:terminal", 240, 120, 480, "y", true);

  // Keep a live pointer to the latest context so the single, mount-once
  // keydown listener below never closes over stale state or handlers.
  const ctxRef = useRef(ctx);
  ctxRef.current = ctx;

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const mod = e.metaKey || e.ctrlKey;
      if (!mod) return;
      const current = ctxRef.current;
      if (e.key.toLowerCase() === "s") {
        e.preventDefault();
        current.saveActiveFile();
      } else if (e.key.toLowerCase() === "p") {
        e.preventDefault();
        current.setFileSwitcherOpen(true);
      } else if (e.key.toLowerCase() === "k") {
        e.preventDefault();
        current.setCommandPaletteOpen(true);
      } else if (e.shiftKey && e.key.toLowerCase() === "r") {
        e.preventDefault();
        void current.doTest();
      } else if (e.key === "`") {
        e.preventDefault();
        current.focusTerminal();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  if (ctx.loadError) {
    return (
      <div className="flex h-screen flex-col bg-ground">
        <StatusStrip />
        <ErrorState message={ctx.loadError} onRetry={ctx.retryLoad} />
      </div>
    );
  }

  if (ctx.loading) {
    return (
      <div className="flex h-screen flex-col bg-ground">
        <StatusStrip />
        <SkeletonRows count={10} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-ground">
      <StatusStrip />
      <div className="mount-stagger flex flex-1 overflow-hidden">
        {!isNarrowFiles ? (
          <>
            <div style={{ width: filesWidth }} className="shrink-0 overflow-hidden border-r border-line">
              <FileTree />
            </div>
            <ResizeHandle
              axis="x"
              label="Resize file tree panel"
              onMouseDown={onFilesResize}
              onKeyResize={adjustFilesWidth}
              valueNow={filesWidth}
              valueMin={160}
              valueMax={420}
            />
          </>
        ) : (
          <button
            className="focus-ring w-6 shrink-0 border-r border-line font-mono text-2xs text-ink-faint"
            onClick={() => setFilesDrawerOpen(true)}
            aria-label="Open file tree"
          >
            ▸
          </button>
        )}

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <EditorArea />
        </div>

        {!isNarrowInvestigation ? (
          <>
            <ResizeHandle
              axis="x"
              label="Resize investigation panel"
              onMouseDown={onInvestigationResize}
              onKeyResize={adjustInvestigationWidth}
              valueNow={investigationWidth}
              valueMin={260}
              valueMax={560}
            />
            <div style={{ width: investigationWidth }} className="shrink-0 overflow-hidden">
              <InvestigationPanel />
            </div>
          </>
        ) : (
          <button
            className="focus-ring w-6 shrink-0 border-l border-line font-mono text-2xs text-ink-faint"
            onClick={() => setInvestigationDrawerOpen(true)}
            aria-label="Open investigation panel"
          >
            ◂
          </button>
        )}
      </div>

      {!ctx.terminalCollapsed && (
        <ResizeHandle
          axis="y"
          label="Resize terminal panel"
          onMouseDown={onTerminalResize}
          onKeyResize={adjustTerminalHeight}
          valueNow={terminalHeight}
          valueMin={120}
          valueMax={480}
        />
      )}
      <div style={{ height: ctx.terminalCollapsed ? 28 : terminalHeight }} className="shrink-0 border-t border-line">
        {ctx.terminalCollapsed ? (
          <button
            className="focus-ring flex h-full w-full items-center px-2 font-mono text-2xs uppercase tracking-caps text-ink-faint"
            onClick={ctx.toggleTerminal}
          >
            Terminal (collapsed)
          </button>
        ) : (
          <div className="flex h-full flex-col">
            <button
              className="focus-ring panel-title flex w-full items-center justify-between border-b border-line text-left"
              onClick={ctx.toggleTerminal}
            >
              <span>Terminal</span>
            </button>
            <div className="flex-1 overflow-hidden">
              <TerminalPanel />
            </div>
          </div>
        )}
      </div>

      <ActionBar />

      {filesDrawerOpen && (
        <div className="fixed inset-0 z-40 flex" onClick={() => setFilesDrawerOpen(false)}>
          <div className="h-full w-60 border-r border-line-strong bg-panel" onClick={(e) => e.stopPropagation()}>
            <FileTree />
          </div>
        </div>
      )}

      {investigationDrawerOpen && (
        <div className="fixed inset-0 z-40 flex justify-end" onClick={() => setInvestigationDrawerOpen(false)}>
          <div className="h-full w-96 border-l border-line-strong bg-panel" onClick={(e) => e.stopPropagation()}>
            <InvestigationPanel />
          </div>
        </div>
      )}

      {ctx.commandPaletteOpen && <CommandPalette />}
      {ctx.fileSwitcherOpen && <FileSwitcher />}
      {ctx.newFileDialogOpen && <NewFileDialog onClose={() => ctx.setNewFileDialogOpen(false)} />}
    </div>
  );
}

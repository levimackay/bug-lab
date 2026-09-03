import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";
import { useEffect, useRef, useState } from "react";
import { terminalUrl } from "../../api/endpoints";
import { useWorkspaceContext } from "./WorkspaceContext";

export function TerminalPanel() {
  const { runId, terminalFocusSignal } = useWorkspaceContext();
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(true);
  const [connectAttempt, setConnectAttempt] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let disposed = false;
    let term: Terminal | null = null;
    let socket: WebSocket | null = null;
    let resizeObserver: ResizeObserver | null = null;

    // Open on the next tick (not a frame: background tabs never paint): React
    // StrictMode mounts, unmounts and remounts the panel synchronously, and an
    // xterm instance disposed in the same tick it was opened throws from its
    // own deferred measurement.
    const timer = window.setTimeout(() => {
      if (disposed) return;
      term = new Terminal({
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 13,
        theme: {
          background: "#0b0d10",
          foreground: "#d6dbe3",
          cursor: "#d6dbe3",
        },
        cursorStyle: "block",
        scrollback: 5000,
      });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(container);
      termRef.current = term;
      fitRef.current = fit;
      const t = term;

      const safeFit = (): { cols: number; rows: number } | undefined => {
        if (disposed || !t.element || t.element.clientHeight === 0) return undefined;
        try {
          fit.fit();
          return fit.proposeDimensions();
        } catch {
          return undefined;
        }
      };
      safeFit();

      const ws = new WebSocket(terminalUrl(runId));
      socket = ws;
      socketRef.current = ws;
      ws.onopen = () => {
        if (disposed) return;
        setConnected(true);
        const dims = safeFit();
        if (dims) ws.send(JSON.stringify({ type: "resize", cols: dims.cols, rows: dims.rows }));
      };
      ws.onmessage = (event: MessageEvent<string>) => {
        if (!disposed) t.write(event.data);
      };
      ws.onclose = () => {
        if (!disposed) setConnected(false);
      };
      ws.onerror = () => {
        if (!disposed) setConnected(false);
      };
      t.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) ws.send(data);
      });
      resizeObserver = new ResizeObserver(() => {
        const dims = safeFit();
        if (dims && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "resize", cols: dims.cols, rows: dims.rows }));
        }
      });
      resizeObserver.observe(container);
    }, 0);

    return () => {
      disposed = true;
      window.clearTimeout(timer);
      resizeObserver?.disconnect();
      socket?.close();
      term?.dispose();
      termRef.current = null;
      fitRef.current = null;
    };
  }, [runId, connectAttempt]);

  useEffect(() => {
    if (terminalFocusSignal > 0) termRef.current?.focus();
  }, [terminalFocusSignal]);

  return (
    <div className="relative h-full w-full overflow-hidden bg-ground">
      <div ref={containerRef} className="h-full w-full p-1" />
      {!connected && (
        <button
          className="focus-ring absolute inset-0 flex items-center justify-center bg-ground/90 font-mono text-xs text-ink-faint"
          onClick={() => setConnectAttempt((n) => n + 1)}
        >
          disconnected — click to reconnect
        </button>
      )}
    </div>
  );
}

import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import "./monacoWorkers";

let configured = false;

export function ensureMonacoConfigured(): void {
  if (configured) return;
  configured = true;
  loader.config({ monaco });
}

const EXTENSION_LANGUAGE: Record<string, string> = {
  py: "python",
  js: "javascript",
  mjs: "javascript",
  ts: "typescript",
  c: "c",
  h: "c",
  md: "markdown",
  toml: "ini",
  ini: "ini",
  json: "json",
  csv: "plaintext",
  log: "plaintext",
  txt: "plaintext",
};

export function languageForPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return EXTENSION_LANGUAGE[ext] ?? "plaintext";
}

export function defineIncidentConsoleTheme(m: typeof monaco): void {
  m.editor.defineTheme("incident-console", {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#0b0d10",
      "editor.foreground": "#d6dbe3",
      "editorGutter.background": "#0b0d10",
      "editorLineNumber.foreground": "#5c6572",
      "editorLineNumber.activeForeground": "#8b94a3",
      "editor.lineHighlightBackground": "#161a20",
      "editor.lineHighlightBorder": "#00000000",
      "editorCursor.foreground": "#d6dbe3",
      "editor.selectionBackground": "#58a6ff2e",
      "editorIndentGuide.background": "#1f242b",
      "editorWidget.background": "#111418",
      "editorWidget.border": "#1f242b",
      "editorLineDecoration.background": "#f8514933",
    },
  });
}

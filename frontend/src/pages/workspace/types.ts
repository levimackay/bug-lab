export type InvestigationTabId = "incident" | "logs" | "trace" | "tests" | "runtime" | "hypothesis" | "hints";

export type SaveState = "saved" | "unsaved" | "saving" | "error";

export interface OpenFile {
  path: string;
  saveState: SaveState;
}

export type ActionKind = "run" | "build" | "test" | "reproduce" | "submit" | "reset";

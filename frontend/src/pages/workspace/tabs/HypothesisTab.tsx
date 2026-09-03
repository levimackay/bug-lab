import { useEffect, useState } from "react";
import { useWorkspaceContext } from "../WorkspaceContext";

export function HypothesisTab() {
  const { run, saveHypothesis } = useWorkspaceContext();
  const [text, setText] = useState(run?.hypothesis ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(true);

  useEffect(() => {
    setText(run?.hypothesis ?? "");
    setSaved(true);
  }, [run?.hypothesis]);

  if (!run) return null;

  async function onSave() {
    setSaving(true);
    try {
      await saveHypothesis(text);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-2 p-3">
      <div className="panel-title px-0">Hypothesis</div>
      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setSaved(false);
        }}
        placeholder="What do you think is causing this?"
        className="focus-ring min-h-32 flex-1 resize-none border border-line bg-panel p-2 font-mono text-xs text-ink outline-none"
      />
      <div className="flex items-center gap-3">
        <button className="btn focus-ring" onClick={onSave} disabled={saving}>
          {saving ? "SAVING…" : "SAVE HYPOTHESIS"}
        </button>
        <span className="font-mono text-2xs text-ink-faint">{saved ? "saved" : "unsaved"}</span>
      </div>
    </div>
  );
}

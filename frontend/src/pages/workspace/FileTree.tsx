import { useMemo, useState } from "react";
import { useWorkspaceContext } from "./WorkspaceContext";

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
}

function buildTree(paths: string[]): TreeNode {
  const root: TreeNode = { name: "", path: "", isDir: true, children: [] };
  for (const path of paths) {
    const parts = path.split("/");
    let node = root;
    let acc = "";
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      acc = acc ? `${acc}/${part}` : part;
      const isDir = i < parts.length - 1;
      let child = node.children.find((c) => c.name === part);
      if (!child) {
        child = { name: part, path: acc, isDir, children: [] };
        node.children.push(child);
      }
      node = child;
    }
  }
  sortTree(root);
  return root;
}

function sortTree(node: TreeNode) {
  node.children.sort((a, b) => {
    if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  node.children.forEach(sortTree);
}

export function FileTree() {
  const { files, activeFile, openFile, openFiles, setNewFileDialogOpen } = useWorkspaceContext();
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const tree = useMemo(() => buildTree(files), [files]);
  const unsavedPaths = useMemo(
    () => new Set(openFiles.filter((f) => f.saveState !== "saved").map((f) => f.path)),
    [openFiles],
  );

  function toggle(path: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  function renderNode(node: TreeNode, depth: number) {
    return node.children.map((child) => (
      <div key={child.path}>
        {child.isDir ? (
          <button
            className="focus-ring flex w-full items-center gap-1 px-2 py-0.5 text-left font-mono text-xs text-ink-dim hover:bg-raised"
            style={{ paddingLeft: 8 + depth * 12 }}
            onClick={() => toggle(child.path)}
          >
            <span className="w-3 text-ink-faint">{collapsed.has(child.path) ? "▸" : "▾"}</span>
            {child.name}
          </button>
        ) : (
          <button
            className={
              "focus-ring flex w-full items-center gap-1.5 px-2 py-0.5 text-left font-mono text-xs hover:bg-raised " +
              (child.path === activeFile ? "bg-raised text-ink" : "text-ink-dim")
            }
            style={{ paddingLeft: 8 + depth * 12 + 12 }}
            onClick={() => openFile(child.path)}
          >
            <span className="flex-1 truncate">{child.name}</span>
            {unsavedPaths.has(child.path) && <span className="h-1.5 w-1.5 shrink-0 bg-warning" />}
          </button>
        )}
        {child.isDir && !collapsed.has(child.path) && renderNode(child, depth + 1)}
      </div>
    ));
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-line pr-1">
        <div className="panel-title">Files</div>
        <button
          className="focus-ring px-2 font-mono text-xs text-ink-faint hover:text-ink"
          onClick={() => setNewFileDialogOpen(true)}
          aria-label="New file"
        >
          +
        </button>
      </div>
      <div className="flex-1 overflow-auto py-1">{renderNode(tree, 0)}</div>
    </div>
  );
}

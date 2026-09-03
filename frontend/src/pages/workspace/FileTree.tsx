import { useMemo, useRef, useState } from "react";
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

interface FlatItem {
  node: TreeNode;
  depth: number;
}

function flatten(node: TreeNode, depth: number, collapsed: Set<string>, out: FlatItem[]) {
  for (const child of node.children) {
    out.push({ node: child, depth });
    if (child.isDir && !collapsed.has(child.path)) {
      flatten(child, depth + 1, collapsed, out);
    }
  }
}

export function FileTree() {
  const { files, activeFile, openFile, openFiles, setNewFileDialogOpen } = useWorkspaceContext();
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [focusedPath, setFocusedPath] = useState<string | null>(null);
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  const tree = useMemo(() => buildTree(files), [files]);
  const unsavedPaths = useMemo(
    () => new Set(openFiles.filter((f) => f.saveState !== "saved").map((f) => f.path)),
    [openFiles],
  );

  const flat = useMemo(() => {
    const out: FlatItem[] = [];
    flatten(tree, 0, collapsed, out);
    return out;
  }, [tree, collapsed]);

  const rovingPath =
    focusedPath && flat.some((f) => f.node.path === focusedPath)
      ? focusedPath
      : (activeFile && flat.some((f) => f.node.path === activeFile) ? activeFile : (flat[0]?.node.path ?? null));

  function toggle(path: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  function focusItem(path: string) {
    setFocusedPath(path);
    refs.current[path]?.focus();
  }

  function activate(item: FlatItem) {
    if (item.node.isDir) toggle(item.node.path);
    else openFile(item.node.path);
  }

  function onKeyDown(e: React.KeyboardEvent, index: number) {
    const item = flat[index];
    if (!item) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = flat[index + 1];
      if (next) focusItem(next.node.path);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = flat[index - 1];
      if (prev) focusItem(prev.node.path);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      if (item.node.isDir) {
        if (collapsed.has(item.node.path)) {
          toggle(item.node.path);
        } else {
          const next = flat[index + 1];
          if (next && next.depth > item.depth) focusItem(next.node.path);
        }
      }
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      if (item.node.isDir && !collapsed.has(item.node.path)) {
        toggle(item.node.path);
      } else if (item.depth > 0) {
        for (let i = index - 1; i >= 0; i--) {
          if (flat[i].depth < item.depth) {
            focusItem(flat[i].node.path);
            break;
          }
        }
      }
    } else if (e.key === "Home") {
      e.preventDefault();
      if (flat[0]) focusItem(flat[0].node.path);
    } else if (e.key === "End") {
      e.preventDefault();
      if (flat.length > 0) focusItem(flat[flat.length - 1].node.path);
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setFocusedPath(item.node.path);
      activate(item);
    }
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
      <div className="flex-1 overflow-auto py-1" role="tree" aria-label="Files">
        {flat.map(({ node, depth }, index) => {
          const isActive = !node.isDir && node.path === activeFile;
          const isTabbable = node.path === rovingPath;
          return (
            <button
              key={node.path}
              ref={(el) => {
                refs.current[node.path] = el;
              }}
              role="treeitem"
              aria-level={depth + 1}
              aria-expanded={node.isDir ? !collapsed.has(node.path) : undefined}
              aria-selected={!node.isDir ? isActive : undefined}
              aria-current={isActive ? "true" : undefined}
              tabIndex={isTabbable ? 0 : -1}
              title={node.path}
              className={
                "focus-ring flex w-full items-center gap-1.5 px-2 py-0.5 text-left font-mono text-xs hover:bg-raised " +
                (isActive ? "bg-raised text-ink" : "text-ink-dim")
              }
              style={{ paddingLeft: 8 + depth * 12 + (node.isDir ? 0 : 12) }}
              onClick={() => {
                setFocusedPath(node.path);
                activate({ node, depth });
              }}
              onFocus={() => setFocusedPath(node.path)}
              onKeyDown={(e) => onKeyDown(e, index)}
            >
              {node.isDir && (
                <span className="w-3 text-ink-faint" aria-hidden="true">
                  {collapsed.has(node.path) ? "▸" : "▾"}
                </span>
              )}
              <span className="flex-1 truncate">{node.name}</span>
              {!node.isDir && unsavedPaths.has(node.path) && (
                <>
                  <span className="h-1.5 w-1.5 shrink-0 bg-warning" aria-hidden="true" />
                  <span className="sr-only"> unsaved</span>
                </>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function ResizeHandle({ axis, onMouseDown }: { axis: "x" | "y"; onMouseDown: (e: React.MouseEvent) => void }) {
  return (
    <div
      onMouseDown={onMouseDown}
      className={
        "shrink-0 bg-line hover:bg-line-strong " + (axis === "x" ? "w-1 cursor-col-resize" : "h-1 cursor-row-resize")
      }
    />
  );
}

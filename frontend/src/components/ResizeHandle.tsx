const KEY_STEP = 16;

export function ResizeHandle({
  axis,
  label,
  onMouseDown,
  onKeyResize,
  valueNow,
  valueMin,
  valueMax,
}: {
  axis: "x" | "y";
  label: string;
  onMouseDown: (e: React.MouseEvent) => void;
  onKeyResize: (delta: number) => void;
  valueNow?: number;
  valueMin?: number;
  valueMax?: number;
}) {
  function onKeyDown(e: React.KeyboardEvent) {
    if (axis === "x" && e.key === "ArrowRight") {
      e.preventDefault();
      onKeyResize(KEY_STEP);
    } else if (axis === "x" && e.key === "ArrowLeft") {
      e.preventDefault();
      onKeyResize(-KEY_STEP);
    } else if (axis === "y" && e.key === "ArrowDown") {
      e.preventDefault();
      onKeyResize(KEY_STEP);
    } else if (axis === "y" && e.key === "ArrowUp") {
      e.preventDefault();
      onKeyResize(-KEY_STEP);
    }
  }

  return (
    <div
      role="separator"
      aria-orientation={axis === "x" ? "vertical" : "horizontal"}
      aria-label={label}
      aria-valuenow={valueNow}
      aria-valuemin={valueMin}
      aria-valuemax={valueMax}
      tabIndex={0}
      onMouseDown={onMouseDown}
      onKeyDown={onKeyDown}
      className={
        "focus-ring shrink-0 bg-line hover:bg-line-strong " + (axis === "x" ? "w-1 cursor-col-resize" : "h-1 cursor-row-resize")
      }
    />
  );
}

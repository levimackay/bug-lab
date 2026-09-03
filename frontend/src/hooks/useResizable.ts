import { useCallback, useRef, useState } from "react";
import { readLocalStorage, writeLocalStorage } from "./useLocalStorage";

type Axis = "x" | "y";

export function useResizable(key: string, initial: number, min: number, max: number, axis: Axis, invert = false) {
  const [size, setSize] = useState(() => readLocalStorage(key, initial));
  const startRef = useRef({ pos: 0, size: 0 });

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      startRef.current = { pos: axis === "x" ? e.clientX : e.clientY, size };

      function onMove(ev: MouseEvent) {
        const pos = axis === "x" ? ev.clientX : ev.clientY;
        const delta = (pos - startRef.current.pos) * (invert ? -1 : 1);
        const next = Math.min(max, Math.max(min, startRef.current.size + delta));
        setSize(next);
      }

      function onUp() {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        setSize((current) => {
          writeLocalStorage(key, current);
          return current;
        });
      }

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    },
    [axis, invert, key, max, min, size],
  );

  const adjust = useCallback(
    (delta: number) => {
      setSize((current) => {
        const next = Math.min(max, Math.max(min, current + delta * (invert ? -1 : 1)));
        writeLocalStorage(key, next);
        return next;
      });
    },
    [invert, key, max, min],
  );

  return [size, onMouseDown, adjust] as const;
}

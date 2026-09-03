import { useCallback, useState } from "react";

export function readLocalStorage<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeLocalStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore quota/availability errors
  }
}

export function useLocalStorage<T>(key: string, fallback: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => readLocalStorage(key, fallback));

  const set = useCallback(
    (next: T) => {
      setValue(next);
      writeLocalStorage(key, next);
    },
    [key],
  );

  return [value, set];
}

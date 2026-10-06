import { useCallback, useEffect, useState } from "react";

const KEY = "iq-compare-v2"; // v2: product ids now come from the API (the demo ids are ignored)
const MAX = 3;

let memory: string[] = [];
const listeners = new Set<(ids: string[]) => void>();

function emit() {
  for (const l of listeners) l(memory);
}

function persist() {
  try {
    localStorage.setItem(KEY, JSON.stringify(memory));
  } catch {
    /* storage unavailable */
  }
}

export function useCompare() {
  // Start empty (as the server does) and load the saved ids in the effect below; starting from `memory`
  // made the server HTML differ from the first client render when ids were saved.
  const [ids, setIds] = useState<string[]>([]);

  useEffect(() => {
    if (!memory.length) {
      try {
        const raw = localStorage.getItem(KEY);
        if (raw) {
          memory = JSON.parse(raw) as string[];
          emit();
        }
      } catch {
        /* ignore */
      }
    }
    listeners.add(setIds);
    setIds(memory);
    return () => {
      listeners.delete(setIds);
    };
  }, []);

  const toggle = useCallback((id: string) => {
    memory = memory.includes(id)
      ? memory.filter((x) => x !== id)
      : [...memory, id].slice(-MAX);
    persist();
    emit();
  }, []);

  const clear = useCallback(() => {
    memory = [];
    persist();
    emit();
  }, []);

  return { ids, toggle, clear, max: MAX, has: (id: string) => ids.includes(id) };
}

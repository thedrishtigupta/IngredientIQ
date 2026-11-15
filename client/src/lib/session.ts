import { useEffect, useState } from "react";

/**
 * The sign-in token, kept in localStorage and shared by every component.
 * Same pattern as compare-store: the server always renders "signed out"; the browser
 * loads the saved token in an effect, so the first client render matches the server HTML.
 */
const KEY = "iq-session-v1";

let token: string | null = null;
let loaded = false;
const listeners = new Set<() => void>();

function load() {
  if (loaded || typeof window === "undefined") return;
  loaded = true;
  try {
    token = localStorage.getItem(KEY);
  } catch {
    /* storage unavailable: stay signed out */
  }
}

/** Current token for API calls (null when signed out, and always on the server). */
export function getToken(): string | null {
  load();
  return token;
}

export function setToken(next: string | null) {
  load();
  token = next;
  try {
    if (next) localStorage.setItem(KEY, next);
    else localStorage.removeItem(KEY);
  } catch {
    /* storage unavailable: the session lasts until the page is closed */
  }
  for (const l of listeners) l();
}

/** { token, ready }: ready is false until the browser has read localStorage (never true on the server). */
export function useSession() {
  const [state, setState] = useState<{ token: string | null; ready: boolean }>({
    token: null,
    ready: false,
  });

  useEffect(() => {
    const sync = () => setState({ token: getToken(), ready: true });
    listeners.add(sync);
    sync();
    // Signing in or out in another tab updates this one too.
    const onStorage = (e: StorageEvent) => {
      if (e.key !== KEY) return;
      token = e.newValue;
      for (const l of listeners) l();
    };
    window.addEventListener("storage", onStorage);
    return () => {
      listeners.delete(sync);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  return state;
}

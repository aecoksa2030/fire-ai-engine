"use client";

import { create } from "zustand";
import { me as fetchMe } from "./api";

export type AuthUser = { username: string; role: string };

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  /** true while restoring a session from localStorage on first load, so
   * pages can show a loading state instead of flashing the login screen
   * for a returning, already-logged-in user. */
  hydrating: boolean;
  setSession: (token: string, user: AuthUser) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
};

const STORAGE_KEY = "aeco_auth_token";

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  hydrating: true,

  setSession: (token, user) => {
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, token);
    set({ token, user, hydrating: false });
  },

  logout: () => {
    if (typeof window !== "undefined") localStorage.removeItem(STORAGE_KEY);
    set({ token: null, user: null, hydrating: false });
  },

  /** Mirrors the Streamlit app's _restore_session_from_url(): a stored
   * token is re-validated against GET /auth/me on every load rather than
   * trusted blindly, so an expired/revoked token can't grant access just
   * because it's still sitting in storage. localStorage (not the URL) is
   * the right persistence spot here since Next.js is a real SPA with
   * client-side routing — no full-page-reload-loses-session problem to
   * work around the way Streamlit had. */
  hydrate: async () => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      set({ hydrating: false });
      return;
    }
    try {
      const data = await fetchMe(stored);
      set({ token: stored, user: { username: data.username, role: data.role }, hydrating: false });
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      set({ token: null, user: null, hydrating: false });
    }
  },
}));

/** Convenience accessor for one-off calls outside React components
 * (e.g. inside api.ts helpers) without subscribing to the store. */
export function getAuthToken() {
  return useAuthStore.getState().token;
}

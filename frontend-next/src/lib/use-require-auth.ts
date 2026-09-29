"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

/** Client-side route guard: redirects to /login once hydration has
 * settled and there's no valid session. Used at the top of every
 * protected page instead of a Next.js middleware, since auth here is a
 * client-held JWT (localStorage), not a cookie middleware can inspect
 * server-side. */
export function useRequireAuth() {
  const router = useRouter();
  // Selected as two separate primitive subscriptions rather than one
  // object-returning selector — zustand compares selector output with
  // Object.is by default, so a `(s) => ({ token: s.token, ... })`
  // selector would return a new object identity every render and
  // re-subscribe/re-render on every store change, not just when these
  // two fields actually change.
  const token = useAuthStore((s) => s.token);
  const hydrating = useAuthStore((s) => s.hydrating);

  useEffect(() => {
    if (!hydrating && !token) router.replace("/login");
  }, [hydrating, token, router]);

  return { ready: !hydrating && !!token, hydrating };
}

"use client";

import { useRequireAuth } from "@/lib/use-require-auth";
import { Sidebar } from "@/components/layout/sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { ready } = useRequireAuth();

  if (!ready) {
    // Either still hydrating (validating a stored token) or about to be
    // redirected to /login — render nothing rather than a flash of
    // protected content or a half-built shell.
    return <div className="min-h-screen bg-bg-app" />;
  }

  return (
    <div className="flex min-h-screen bg-bg-app">
      <Sidebar />
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}

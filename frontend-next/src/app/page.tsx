"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

export default function RootPage() {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const hydrating = useAuthStore((s) => s.hydrating);

  useEffect(() => {
    if (hydrating) return;
    router.replace(token ? "/analyze" : "/login");
  }, [hydrating, token, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-app text-text-secondary text-sm">
      ...
    </div>
  );
}

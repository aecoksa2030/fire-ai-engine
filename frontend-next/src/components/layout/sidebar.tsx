"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { useI18nStore, useT } from "@/lib/i18n";

const NAV_ITEMS = [
  // Projects sits first: reading the project's technical spec is meant as
  // the estimation engineer's actual first step, before opening any
  // drawing — see app/routers/projects.py's own comments on why this is a
  // deliberately standalone tool, not wired into Analyze/Archive.
  { href: "/projects", key: "nav_projects" as const },
  { href: "/analyze", key: "nav_analyze" as const },
  { href: "/archive", key: "nav_archive" as const },
  { href: "/users", key: "nav_users" as const, adminOnly: true },
];

export function Sidebar() {
  const t = useT();
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { lang, setLang } = useI18nStore();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <aside className="w-64 shrink-0 border-e border-border-subtle bg-bg-elevated flex flex-col h-screen sticky top-0">
      <div className="p-4 flex items-center gap-2.5 border-b border-border-subtle">
        <div className="h-9 w-9 rounded-[var(--radius-md)] bg-accent-soft flex items-center justify-center text-lg">
          🔥
        </div>
        <div>
          <div className="text-sm font-bold text-text-primary leading-tight">{t.brand_name}</div>
          <div className="text-[11px] text-text-secondary">{t.brand_tagline}</div>
        </div>
      </div>

      <div className="p-3 space-y-2 border-b border-border-subtle">
        <div className="flex items-center justify-between text-xs">
          <span className="text-text-muted">{t.language_label}</span>
          <button
            onClick={() => setLang(lang === "ar" ? "en" : "ar")}
            className="text-text-secondary hover:text-text-primary font-medium"
          >
            {lang === "ar" ? "English" : "العربية"}
          </button>
        </div>
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-full flex items-center justify-center gap-2 h-8 rounded-[var(--radius-sm)] border border-border bg-bg-elevated-2 text-xs text-text-secondary hover:text-text-primary transition-colors"
        >
          {theme === "dark" ? t.theme_dark : t.theme_light}
        </button>
      </div>

      {user && (
        <div className="p-3 border-b border-border-subtle">
          <div className="flex items-center gap-2 rounded-[var(--radius-sm)] bg-bg-elevated-2 px-3 py-2">
            <span className="text-sm">👤</span>
            <div className="min-w-0">
              <div className="text-sm text-text-primary truncate">{user.username}</div>
              <div className="text-[10px] uppercase tracking-wide text-accent font-semibold">
                {user.role}
              </div>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={handleLogout}
        className="mx-3 mt-3 h-9 rounded-[var(--radius-sm)] border border-border text-sm text-text-secondary hover:bg-bg-elevated-2 hover:text-text-primary transition-colors"
      >
        {t.logout}
      </button>

      <nav className="flex-1 p-3 space-y-1 mt-2">
        {NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === "admin").map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-[var(--radius-sm)] px-3 py-2.5 text-sm transition-colors border",
                active
                  ? "bg-accent-soft border-accent/35 text-accent font-semibold"
                  : "border-transparent text-text-secondary hover:bg-bg-elevated-2"
              )}
            >
              {t[item.key]}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { login, ApiError } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useI18nStore, useT } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";

export default function LoginPage() {
  const t = useT();
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const { theme, setTheme } = useTheme();
  const { lang, setLang } = useI18nStore();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await login(username, password);
      setSession(data.access_token, { username: data.username, role: data.role });
      router.push("/analyze");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.login_failed);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-app px-4">
      <div className="absolute top-4 inset-x-4 flex items-center justify-between text-sm">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="text-text-secondary hover:text-text-primary transition-colors"
        >
          {theme === "dark" ? t.theme_dark : t.theme_light}
        </button>
        <button
          onClick={() => setLang(lang === "ar" ? "en" : "ar")}
          className="text-text-secondary hover:text-text-primary transition-colors"
        >
          {lang === "ar" ? "English" : "العربية"}
        </button>
      </div>

      <div className="flex items-center gap-3 mb-8">
        <div className="h-11 w-11 rounded-[var(--radius-md)] bg-accent-soft flex items-center justify-center text-2xl">
          🔥
        </div>
        <div>
          <div className="text-lg font-bold text-text-primary leading-tight">{t.brand_name}</div>
          <div className="text-xs text-text-secondary">{t.brand_tagline}</div>
        </div>
      </div>

      <Card className="w-full max-w-sm">
        <CardContent className="pt-5">
          <h1 className="text-base font-semibold text-text-primary">{t.login_title}</h1>
          <p className="text-sm text-text-secondary mt-1 mb-5">{t.login_subtitle}</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="username">{t.username}</Label>
              <Input
                id="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">{t.password}</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-[var(--radius-sm)] px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? t.logging_in : t.login_btn}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

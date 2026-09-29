"use client";

import { useEffect } from "react";
import { ThemeProvider } from "next-themes";
import { useAuthStore } from "@/lib/auth-store";
import { useI18nStore, dirFor, hydrateLangFromStorage } from "@/lib/i18n";

/** Keeps <html lang="..." dir="..."> in sync with the language store.
 * A real attribute on the root element (not a wrapper div) is what makes
 * native browser behavior — text selection direction, form control
 * alignment, scrollbars — follow RTL/LTR correctly everywhere, the same
 * reason the Streamlit version set `direction` in its injected CSS. */
function HtmlLangSync() {
  const lang = useI18nStore((s) => s.lang);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dirFor(lang);
  }, [lang]);
  return null;
}

/** Fires once on app load to validate any stored token against the
 * backend (see auth-store.ts's hydrate()) before anything renders a
 * "logged out" state. */
function AuthHydrator() {
  const hydrate = useAuthStore((s) => s.hydrate);
  useEffect(() => {
    hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

/** Applies a previously-persisted language choice after the first paint
 * (see the long comment on i18n.ts's readInitialLang() for why this
 * can't just be the store's initial value — doing it here, from a
 * client-only effect, means it happens strictly after React has already
 * reconciled against the server-rendered "ar" HTML, so it can't trigger
 * a hydration mismatch the way reading localStorage during the store's
 * initial render did. */
function I18nHydrator() {
  useEffect(() => {
    hydrateLangFromStorage();
  }, []);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <HtmlLangSync />
      <AuthHydrator />
      <I18nHydrator />
      {children}
    </ThemeProvider>
  );
}

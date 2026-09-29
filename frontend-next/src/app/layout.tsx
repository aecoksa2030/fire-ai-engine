import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AECO — Fire & Security AI Engine",
  description: "Enterprise fire & security engineering-drawing BOQ extraction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // lang/dir start as sensible defaults for a no-JS first paint; the
    // client-side HtmlLangSync in providers.tsx (mounted just below)
    // corrects them immediately based on the stored language choice.
    // suppressHydrationWarning is the standard next-themes/i18n pattern
    // here since the server can't know the visitor's stored preference.
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

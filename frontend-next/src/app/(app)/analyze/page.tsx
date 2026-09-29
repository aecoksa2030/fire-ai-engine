"use client";

import { useRef, useState } from "react";
import dynamic from "next/dynamic";
import { UploadCloud, Loader2, Save } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { extractBoq, saveSessionData, type BoqAnalysis, type BoqComponent, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { SelectNative } from "@/components/ui/select-native";
import { BoqTable } from "@/components/boq-table";
import { DrawingChat } from "@/components/drawing-chat";
import { SaveReferencePanel } from "@/components/save-reference-panel";

// react-pdf/pdfjs-dist touches browser-only APIs (Worker, DOMMatrix, ...)
// at module scope — loading it with ssr:false keeps it out of Next's
// server render / static-generation pass entirely (it was otherwise
// printing a "please use the legacy build in Node.js" warning during
// `next build`, since the page-data-collection step imported it even
// though it's never actually rendered server-side).
const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((m) => m.PdfViewer), {
  ssr: false,
});

const PROVIDERS = [
  { value: "claude", label: "Anthropic Claude" },
  { value: "gemini", label: "Google Gemini" },
  { value: "groq", label: "Groq" },
  { value: "openrouter", label: "OpenRouter" },
];
const REPORT_TYPES = [
  { value: "fire", label: "Fire Protection" },
  { value: "security", label: "Physical Security" },
];

export default function AnalyzePage() {
  const token = useAuthStore((s) => s.token);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [provider, setProvider] = useState("claude");
  const [reportType, setReportType] = useState("fire");
  const [sessionId] = useState(() => crypto.randomUUID());

  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);
  const [result, setResult] = useState<BoqAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleAnalyze() {
    if (!file || !token) return;
    setAnalyzing(true);
    setError(null);
    setResult(null);
    setSaved(false);
    setProgress({ current: 0, total: 1 });
    try {
      await extractBoq(token, file, {
        sessionId,
        provider,
        reportType,
        onEvent: (evt) => {
          if (evt.status === "progress") {
            setProgress({ current: evt.current_page, total: evt.total_pages });
          } else if (evt.status === "completed") {
            setResult(evt.data.analysis);
          }
        },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setAnalyzing(false);
      setProgress(null);
    }
  }

  async function handleSave() {
    if (!file || !token || !result) return;
    setSaving(true);
    try {
      await saveSessionData(token, sessionId, file.name, result, file);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  // Merges a chat-table reply's components into the on-screen result —
  // see components/drawing-chat.tsx's onMergeComponents. If this analysis
  // was already saved to the archive, the merge is silently re-persisted
  // there too (same upsert endpoint as handleSave, just without re-
  // sending the file) so the archived copy doesn't go stale the moment
  // the user adds rows from a chat reply after already saving once.
  function handleMergeComponents(newComponents: BoqComponent[]) {
    setResult((prev) => {
      if (!prev) return prev;
      const merged: BoqAnalysis = { ...prev, components: [...prev.components, ...newComponents] };
      if (saved && token && file) {
        saveSessionData(token, sessionId, file.name, merged).catch((err) => {
          setError(err instanceof Error ? err.message : String(err));
        });
      }
      return merged;
    });
  }

  const highConfCount = result?.components.filter((c) => c.confidence === "high").length ?? 0;

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">🚀 Analyze New Drawing</h1>
        <p className="text-sm text-text-secondary mt-0.5">
          Upload a fire safety or security drawing (PDF) to automatically extract a bill of quantities.
        </p>
      </div>

      <Card>
        <CardContent className="pt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <Label>AI Provider</Label>
            <SelectNative value={provider} onChange={(e) => setProvider(e.target.value)}>
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </SelectNative>
          </div>
          <div className="space-y-1.5">
            <Label>Drawing & System Type</Label>
            <SelectNative value={reportType} onChange={(e) => setReportType(e.target.value)}>
              {REPORT_TYPES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </SelectNative>
          </div>
          <div className="space-y-1.5">
            <Label>Drawing file (PDF)</Label>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-9 flex items-center gap-2 px-3 rounded-[var(--radius-sm)] border border-dashed border-border bg-bg-elevated-2 text-sm text-text-secondary hover:border-accent hover:text-text-primary transition-colors"
            >
              <UploadCloud className="h-4 w-4" />
              <span className="truncate">{file ? file.name : "Choose a PDF…"}</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <div className="md:col-span-3 flex items-center gap-3">
            <Button onClick={handleAnalyze} disabled={!file || analyzing}>
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Analyzing…
                </>
              ) : (
                "Analyze"
              )}
            </Button>
            {progress && (
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-bg-elevated-3 overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-300"
                    style={{ width: `${Math.min(100, (progress.current / Math.max(1, progress.total)) * 100)}%` }}
                  />
                </div>
                <span className="text-xs text-text-secondary whitespace-nowrap">
                  Page {progress.current} / {progress.total}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-[var(--radius-md)] px-4 py-3">
          {error}
        </div>
      )}

      {/* Shown as soon as a file is chosen — previously this only
       * appeared after analysis finished, even though the file itself
       * (and react-pdf, which renders it entirely client-side from the
       * in-memory File object) is available immediately, with no reason
       * to make the user wait through the whole extraction just to see
       * their own drawing. Once results exist it moves into the grid
       * below, side by side with the BOQ table, instead of rendering
       * twice. */}
      {file && !result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PdfViewer file={file} />
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard label="Total Devices Detected" value={String(result.components.length)} />
            <MetricCard label="High Confidence Rate" value={`${highConfCount}/${result.components.length}`} />
            <MetricCard
              label="Estimated Analysis Cost"
              value={`$${(result.usage_summary?.total_cost_usd ?? 0).toFixed(4)}`}
            />
            <MetricCard label="Provider / Model" value={result.usage_summary?.model || provider} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {file && <PdfViewer file={file} />}
            <BoqTable data={result.components} />
          </div>

          {result.flagged_unclear_areas.length > 0 && (
            <Card>
              <CardContent className="pt-5">
                <h3 className="text-sm font-semibold text-text-primary mb-2">📋 Technical Observations</h3>
                <ul className="space-y-1.5">
                  {result.flagged_unclear_areas.map((note, i) => (
                    <li key={i} className="text-sm text-text-secondary bg-bg-elevated-2 rounded-[var(--radius-sm)] px-3 py-2">
                      🔹 {note}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={handleSave} disabled={saving || saved}>
              <Save className="h-4 w-4" />
              {saved ? "Saved to archive" : saving ? "Saving…" : "Save to Archive"}
            </Button>
          </div>

          {/* Chat and "save as reference" both need the session's PDF to
           * already exist server-side (app/routers/chat.py and
           * library.py both read AnalysisSession.pdf_bytes), which only
           * happens once handleSave() above has completed — so both are
           * gated on `saved`, not just on having a `result`. */}
          {saved && token && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <DrawingChat
                sessionId={sessionId}
                token={token}
                reportType={reportType}
                onMergeComponents={handleMergeComponents}
              />
              <SaveReferencePanel sessionId={sessionId} reportType={reportType} token={token} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="border-s-4 border-s-accent">
      <CardContent className="pt-4">
        <div className="text-xl font-bold text-text-primary">{value}</div>
        <div className="text-xs text-text-secondary mt-1">{label}</div>
      </CardContent>
    </Card>
  );
}

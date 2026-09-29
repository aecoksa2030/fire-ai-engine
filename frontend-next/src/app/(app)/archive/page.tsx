"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Eye, EyeOff, Pencil, Trash2, Loader2, FolderOpen } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import {
  ApiError,
  deleteSession,
  getMySessions,
  renameSession,
  saveSessionData,
  sessionPdfUrl,
  type BoqAnalysis,
  type BoqComponent,
  type SavedSession,
} from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BoqTable } from "@/components/boq-table";
import { DrawingChat } from "@/components/drawing-chat";

// Same reasoning as the Analyze page: keep react-pdf/pdfjs-dist (which
// touches browser-only APIs at module scope) out of the server render /
// static-generation pass entirely.
const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((m) => m.PdfViewer), {
  ssr: false,
});

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function ArchivePage() {
  const token = useAuthStore((s) => s.token);
  const t = useT();

  const [sessions, setSessions] = useState<SavedSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getMySessions(token)
      .then(setSessions)
      .catch((err) => setError(err instanceof ApiError ? err.message : String(err)));
  }, [token]);

  function updateOne(sessionId: string, patch: Partial<SavedSession>) {
    setSessions((prev) => prev?.map((s) => (s.session_id === sessionId ? { ...s, ...patch } : s)) ?? prev);
  }

  function removeOne(sessionId: string) {
    setSessions((prev) => prev?.filter((s) => s.session_id !== sessionId) ?? prev);
  }

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">{t.archive_title}</h1>
        <p className="text-sm text-text-secondary mt-0.5">{t.archive_subtitle}</p>
      </div>

      {error && (
        <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-[var(--radius-md)] px-4 py-3">
          {error}
        </div>
      )}

      {sessions === null && !error && (
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <Loader2 className="h-4 w-4 animate-spin" /> {t.archive_loading}
        </div>
      )}

      {sessions !== null && sessions.length === 0 && (
        <Card>
          <CardContent className="pt-5 flex flex-col items-center text-center gap-2 py-10">
            <FolderOpen className="h-8 w-8 text-text-muted" />
            <p className="text-sm text-text-secondary">{t.archive_empty}</p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {sessions?.map((session) => (
          <SessionRow
            key={session.session_id}
            session={session}
            token={token!}
            expanded={expandedId === session.session_id}
            onToggleExpand={() =>
              setExpandedId((cur) => (cur === session.session_id ? null : session.session_id))
            }
            onRenamed={(filename) => updateOne(session.session_id, { filename })}
            onDataUpdated={(data) => updateOne(session.session_id, { data })}
            onDeleted={() => removeOne(session.session_id)}
          />
        ))}
      </div>
    </div>
  );
}

function SessionRow({
  session,
  token,
  expanded,
  onToggleExpand,
  onRenamed,
  onDataUpdated,
  onDeleted,
}: {
  session: SavedSession;
  token: string;
  expanded: boolean;
  onToggleExpand: () => void;
  onRenamed: (filename: string) => void;
  onDataUpdated: (data: BoqAnalysis) => void;
  onDeleted: () => void;
}) {
  const t = useT();
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(session.filename);
  const [savingName, setSavingName] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [rowError, setRowError] = useState<string | null>(null);

  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  // Guards the fetch to "at most once per expand", independent of state —
  // using pdfBlobUrl itself as that guard would re-trigger this effect
  // the moment setPdfBlobUrl fires (it's a dependency), and the effect's
  // own cleanup would then immediately revoke the object URL it had just
  // created, before <PdfViewer> ever got to load it.
  const pdfFetchStarted = useRef(false);

  // GET /auth/sessions/{id}/pdf requires the Bearer token like every other
  // endpoint (see app/routers/auth.py) — but handing its plain URL
  // straight to react-pdf (as the previous version of this file did)
  // makes react-pdf fetch it internally with no way for us to attach an
  // Authorization header, so the backend correctly rejected it with 401
  // every time. Fetching it ourselves with the token and handing react-pdf
  // a local blob: URL instead sidesteps that — react-pdf/pdfjs happily
  // reads a blob URL with no auth of its own needed.
  useEffect(() => {
    if (!expanded || pdfFetchStarted.current) return;
    pdfFetchStarted.current = true;
    let cancelled = false;

    fetch(sessionPdfUrl(session.session_id), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`PDF fetch failed (${res.status})`);
        return res.blob();
      })
      .then((blob) => {
        if (!cancelled) setPdfBlobUrl(URL.createObjectURL(blob));
      })
      .catch((err) => {
        if (!cancelled) setPdfError(err instanceof Error ? err.message : String(err));
      });

    return () => {
      cancelled = true;
    };
  }, [expanded, session.session_id, token]);

  // Separate lifecycle for revocation: this cleanup runs with the
  // *previous* pdfBlobUrl value right before the effect re-fires with a
  // new one (or on unmount), which is the correct time to free it — never
  // the instant it's created.
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl);
    };
  }, [pdfBlobUrl]);

  async function handleRename() {
    if (!newName.trim() || newName === session.filename) {
      setRenaming(false);
      return;
    }
    setSavingName(true);
    setRowError(null);
    try {
      await renameSession(token, session.session_id, newName.trim());
      onRenamed(newName.trim());
      setRenaming(false);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSavingName(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setRowError(null);
    try {
      await deleteSession(token, session.session_id);
      onDeleted();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
      setDeleting(false);
    }
  }

  // See components/drawing-chat.tsx's onMergeComponents. Unlike the
  // Analyze page (where "the main table" is just in-memory state until
  // "Save to Archive" is clicked), a row here is already persisted — so
  // the merge updates the on-screen table immediately (optimistic, via
  // onDataUpdated bubbling up to the parent's `sessions` state) AND
  // re-persists the merged result through the same upsert endpoint
  // /auth/sessions/save uses (no `file` re-sent — the PDF already on the
  // record is left untouched), so it survives a reload instead of only
  // looking merged until the next page refresh.
  async function handleMergeComponents(newComponents: BoqComponent[]) {
    if (!session.data) return;
    const merged: BoqAnalysis = {
      ...session.data,
      components: [...session.data.components, ...newComponents],
    };
    onDataUpdated(merged);
    setRowError(null);
    try {
      await saveSessionData(token, session.session_id, session.filename, merged);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
    }
  }

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            {renaming ? (
              <div className="flex items-center gap-2">
                <Input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="h-8 text-sm max-w-xs"
                  autoFocus
                />
                <Button size="sm" onClick={handleRename} disabled={savingName}>
                  {savingName ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : t.archive_rename_save}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setRenaming(false);
                    setNewName(session.filename);
                  }}
                >
                  {t.archive_cancel}
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary truncate">{session.filename}</span>
                <button
                  onClick={() => setRenaming(true)}
                  className="text-text-muted hover:text-text-primary"
                  title={t.archive_rename_btn}
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
              </div>
            )}
            <div className="text-xs text-text-secondary mt-0.5">{formatDate(session.created_at)}</div>
          </div>

          <div className="flex items-center gap-1.5">
            <Button size="sm" variant="secondary" onClick={onToggleExpand}>
              {expanded ? (
                <>
                  <EyeOff className="h-3.5 w-3.5" /> {t.archive_hide_btn}
                </>
              ) : (
                <>
                  <Eye className="h-3.5 w-3.5" /> {t.archive_view_btn}
                </>
              )}
            </Button>

            {confirmDelete ? (
              <>
                <span className="text-xs text-danger">{t.archive_delete_confirm}</span>
                <Button size="sm" variant="destructive" onClick={handleDelete} disabled={deleting}>
                  {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : t.archive_delete_ok}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirmDelete(false)}>
                  {t.archive_cancel}
                </Button>
              </>
            ) : (
              <Button size="sm" variant="ghost" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="h-3.5 w-3.5" /> {t.archive_delete_btn}
              </Button>
            )}
          </div>
        </div>

        {rowError && <div className="text-xs text-danger mt-2">{rowError}</div>}

        {expanded && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            {pdfError ? (
              <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated p-6 text-sm text-danger">
                {pdfError}
              </div>
            ) : pdfBlobUrl ? (
              <PdfViewer file={pdfBlobUrl} />
            ) : (
              <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated p-6 text-sm text-text-muted flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" /> {t.archive_loading}
              </div>
            )}
            {session.data?.components ? (
              <BoqTable data={session.data.components} />
            ) : (
              // Sessions saved before this rewrite (or saved through a
              // different code path) may have a null/differently-shaped
              // analysis_result in the DB — guard against that instead of
              // crashing the whole table renderer on `.components` of
              // undefined, which previously took down the entire page.
              <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated p-6 text-sm text-text-muted">
                {t.archive_no_data}
              </div>
            )}
          </div>
        )}

        {/* Every archived session already has pdf_bytes saved (that's
         * exactly what /auth/sessions/save persisted) so, unlike on the
         * Analyze page, there's no "not saved yet" gate needed here —
         * the chat is always available once a session exists at all.
         * reportType is derived from the saved analysis's own
         * system_type ("Physical Security System" / "Fire Protection
         * System" — see app/services/prompts.py) since archived sessions
         * don't separately store the report_type string the Analyze page
         * used; DrawingChat only checks it for the substring "security",
         * so this string is passed through as-is. */}
        {expanded && (
          <div className="mt-4">
            <DrawingChat
              sessionId={session.session_id}
              token={token}
              reportType={session.data?.system_type}
              onMergeComponents={session.data ? handleMergeComponents : undefined}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

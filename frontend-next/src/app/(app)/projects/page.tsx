"use client";

import { useEffect, useRef, useState } from "react";
import { UploadCloud, Loader2, Trash2, FolderOpen, FileText, Eye } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import {
  ApiError,
  approveProjectSpec,
  deleteProjectSpec,
  downloadScopeXlsx,
  extractProjectSpec,
  getMyProjectSpecs,
  projectSpecPdfUrl,
  saveProjectSpec,
  updateProjectSpec,
  type ProjectSpecSummary,
  type ScopeRow,
} from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScopeTable } from "@/components/scope-table";

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function errorText(err: unknown) {
  return err instanceof ApiError ? err.message : String(err);
}

/** Projects page — stage 1 of the estimation workflow. Upload a PTS, get
 * its scope table (Area / Type of system required as per PTS), review and
 * correct it, save it, download it as Excel, and approve it into the
 * reference library (RAG) so future extractions follow it. */
export default function ProjectsPage() {
  const token = useAuthStore((s) => s.token);
  const t = useT();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The table currently on screen (freshly extracted, or opened from the list).
  const [rows, setRows] = useState<ScopeRow[] | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [refsUsed, setRefsUsed] = useState(0);
  const [filename, setFilename] = useState("");
  const [savedId, setSavedId] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const [approvedTag, setApprovedTag] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState("");
  const [approving, setApproving] = useState(false);

  const [specs, setSpecs] = useState<ProjectSpecSummary[] | null>(null);
  const [specsError, setSpecsError] = useState<string | null>(null);

  async function loadSpecs() {
    if (!token) return null;
    try {
      const list = await getMyProjectSpecs(token);
      setSpecs(list);
      return list;
    } catch (err) {
      setSpecsError(errorText(err));
      return null;
    }
  }

  useEffect(() => {
    loadSpecs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function openTable(spec: {
    rows: ScopeRow[];
    filename: string;
    savedId: number | null;
    approvedTag: string | null;
    truncated?: boolean;
    refsUsed?: number;
  }) {
    setRows(spec.rows);
    setFilename(spec.filename);
    setSavedId(spec.savedId);
    setApprovedTag(spec.approvedTag);
    setTagInput(spec.approvedTag ?? "");
    setTruncated(spec.truncated ?? false);
    setRefsUsed(spec.refsUsed ?? 0);
    setDirty(spec.savedId === null);
    setError(null);
  }

  async function handleExtract() {
    if (!file || !token) return;
    setExtracting(true);
    setError(null);
    setRows(null);
    try {
      const res = await extractProjectSpec(token, file);
      openTable({
        rows: res.data.scope,
        filename: res.filename,
        savedId: null,
        approvedTag: null,
        truncated: res.data.truncated,
        refsUsed: res.data.reference_examples_used,
      });
    } catch (err) {
      setError(errorText(err));
    } finally {
      setExtracting(false);
    }
  }

  function handleRowsChange(next: ScopeRow[]) {
    setRows(next);
    setDirty(true);
  }

  async function handleSave() {
    if (!rows || !token) return;
    setSaving(true);
    setError(null);
    try {
      const name = filename.trim() || "PTS.pdf";
      let id = savedId;
      if (id === null) {
        const res = await saveProjectSpec(token, name, { scope: rows, truncated }, file ?? undefined);
        id = res.id;
        setSavedId(id);
      } else {
        await updateProjectSpec(token, id, rows, name);
      }
      setDirty(false);
      // Show the table exactly as stored (the server drops blank rows and
      // keeps each area's rows together).
      const list = await loadSpecs();
      const stored = list?.find((s) => s.id === id);
      if (stored) setRows(stored.data.scope);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDownload() {
    if (!rows || !token) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadScopeXlsx(token, filename || "PTS", rows);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setDownloading(false);
    }
  }

  async function handleApprove() {
    if (savedId === null || !token || !tagInput.trim()) return;
    setApproving(true);
    setError(null);
    try {
      const res = await approveProjectSpec(token, savedId, tagInput.trim());
      setApprovedTag(res.tag);
      loadSpecs();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setApproving(false);
    }
  }

  async function handleDelete(specId: number) {
    if (!token) return;
    try {
      await deleteProjectSpec(token, specId);
      setSpecs((prev) => prev?.filter((s) => s.id !== specId) ?? prev);
      if (savedId === specId) {
        setRows(null);
        setSavedId(null);
      }
    } catch (err) {
      setSpecsError(errorText(err));
    }
  }

  // The PDF endpoint needs the Bearer token, so it can't be a plain link.
  async function handleViewPdf(specId: number) {
    if (!token) return;
    try {
      const res = await fetch(projectSpecPdfUrl(specId), { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(`PDF (${res.status})`);
      const url = URL.createObjectURL(await res.blob());
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setSpecsError(errorText(err));
    }
  }

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">{t.projects_title}</h1>
        <p className="text-sm text-text-secondary mt-0.5">{t.projects_subtitle}</p>
      </div>

      <Card>
        <CardContent className="pt-5 space-y-4">
          <div className="space-y-1.5">
            <Label>{t.projects_upload_label}</Label>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-9 flex items-center gap-2 px-3 rounded-[var(--radius-sm)] border border-dashed border-border bg-bg-elevated-2 text-sm text-text-secondary hover:border-accent hover:text-text-primary transition-colors md:max-w-md"
            >
              <UploadCloud className="h-4 w-4" />
              <span className="truncate">{file ? file.name : t.projects_upload_label}</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null);
                setError(null);
              }}
            />
            <p className="text-xs text-text-muted">{t.projects_upload_hint}</p>
          </div>

          <Button onClick={handleExtract} disabled={!file || extracting}>
            {extracting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> {t.projects_extracting}
              </>
            ) : (
              t.projects_extract_btn
            )}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-[var(--radius-md)] px-4 py-3">
          {error}
        </div>
      )}

      {rows && (
        <Card>
          <CardContent className="pt-5 space-y-4">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-base font-semibold text-text-primary">{t.projects_scope_title}</h2>
              {approvedTag && (
                <span className="text-xs text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5">
                  {t.projects_approved_badge}
                </span>
              )}
            </div>

            {truncated && (
              <div className="text-sm text-warning bg-warning/10 border border-warning/30 rounded-[var(--radius-md)] px-4 py-3">
                {t.projects_extract_truncated_warning}
              </div>
            )}
            {refsUsed > 0 && (
              <p className="text-xs text-text-muted">{t.projects_rag_used.replace("{n}", String(refsUsed))}</p>
            )}

            <ScopeTable rows={rows} onChange={handleRowsChange} />

            <div className="flex items-center gap-2 flex-wrap border-t border-border-subtle pt-4">
              <div className="w-full sm:w-64">
                <Input
                  value={filename}
                  onChange={(e) => {
                    setFilename(e.target.value);
                    setDirty(true);
                  }}
                  placeholder={t.projects_save_filename_label}
                  className="h-8 text-sm"
                />
              </div>
              <Button variant="secondary" size="sm" onClick={handleSave} disabled={saving || !dirty}>
                {saving ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : !dirty ? (
                  t.projects_saved_ok
                ) : savedId === null ? (
                  t.projects_save_btn
                ) : (
                  t.projects_save_changes_btn
                )}
              </Button>
              <Button variant="secondary" size="sm" onClick={handleDownload} disabled={downloading || rows.length === 0}>
                {downloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : t.projects_download_xlsx}
              </Button>
              {dirty && savedId !== null && (
                <span className="text-xs text-warning">{t.projects_unsaved_changes}</span>
              )}
            </div>

            <div className="border-t border-border-subtle pt-4 space-y-2">
              <h3 className="text-sm font-semibold text-text-primary">{t.projects_approve_title}</h3>
              <p className="text-xs text-text-secondary">{t.projects_approve_hint}</p>
              {savedId === null || dirty ? (
                <p className="text-xs text-text-muted">{t.projects_approve_need_save}</p>
              ) : (
                <div className="flex items-end gap-2 flex-wrap">
                  <div className="space-y-1 w-full sm:w-80">
                    <Label className="text-xs">{t.projects_approve_tag_label}</Label>
                    <Input
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      placeholder={t.projects_approve_tag_placeholder}
                      className="h-8 text-sm"
                    />
                  </div>
                  <Button size="sm" onClick={handleApprove} disabled={approving || !tagInput.trim()}>
                    {approving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : t.projects_approve_btn}
                  </Button>
                  {approvedTag && <span className="text-xs text-success">{t.projects_approved_ok}</span>}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-5">
          <h2 className="text-base font-semibold text-text-primary mb-3">{t.projects_saved_list_title}</h2>

          {specsError && <div className="text-sm text-danger mb-2">{specsError}</div>}

          {specs === null && !specsError && (
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Loader2 className="h-4 w-4 animate-spin" /> {t.projects_saved_loading}
            </div>
          )}

          {specs !== null && specs.length === 0 && (
            <div className="flex flex-col items-center text-center gap-2 py-8">
              <FolderOpen className="h-8 w-8 text-text-muted" />
              <p className="text-sm text-text-secondary">{t.projects_saved_empty}</p>
            </div>
          )}

          <div className="space-y-2">
            {specs?.map((spec) => (
              <div
                key={spec.id}
                className="flex items-center gap-3 flex-wrap rounded-[var(--radius-sm)] border border-border-subtle bg-bg-elevated-2 px-3 py-2.5"
              >
                <FileText className="h-4 w-4 text-text-muted shrink-0" />
                <div className="flex-1 min-w-[160px]">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary truncate">{spec.filename}</span>
                    {spec.approved_tag && (
                      <span className="text-[10px] text-success bg-success/10 border border-success/30 rounded-full px-1.5 py-0.5">
                        {t.projects_approved_badge}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-text-secondary">
                    {formatDate(spec.created_at)} · {spec.data.scope.length} rows
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {spec.has_pdf && (
                    <Button size="sm" variant="ghost" onClick={() => handleViewPdf(spec.id)}>
                      {t.projects_view_pdf_btn}
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      openTable({
                        rows: spec.data.scope,
                        filename: spec.filename,
                        savedId: spec.id,
                        approvedTag: spec.approved_tag,
                        truncated: spec.data.truncated,
                      })
                    }
                  >
                    <Eye className="h-3.5 w-3.5" /> {t.projects_view_btn}
                  </Button>
                  <DeleteButton
                    onConfirm={() => handleDelete(spec.id)}
                    label={t.projects_delete_btn}
                    confirmLabel={t.projects_delete_confirm}
                    confirmOkLabel={t.projects_delete_ok}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DeleteButton({
  onConfirm,
  label,
  confirmLabel,
  confirmOkLabel,
}: {
  onConfirm: () => void;
  label: string;
  confirmLabel: string;
  confirmOkLabel: string;
}) {
  const [confirming, setConfirming] = useState(false);
  if (confirming) {
    return (
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-danger">{confirmLabel}</span>
        <Button size="sm" variant="destructive" onClick={onConfirm}>
          {confirmOkLabel}
        </Button>
      </div>
    );
  }
  return (
    <Button size="sm" variant="ghost" onClick={() => setConfirming(true)}>
      <Trash2 className="h-3.5 w-3.5" /> {label}
    </Button>
  );
}

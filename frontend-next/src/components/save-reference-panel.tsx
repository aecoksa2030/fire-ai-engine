"use client";

import { useState } from "react";
import { BookMarked, Loader2 } from "lucide-react";
import { useT } from "@/lib/i18n";
import { ApiError, saveReferenceExample } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Port of the Streamlit app's "rag_header" section — promotes an
 * already-saved session into the reference library (POST /library/save,
 * see app/routers/library.py) so future automatic extractions of the
 * same report_type are grounded in it (see
 * app/services/reference_library_service.py). Requires the session to
 * already be saved to the archive, same precondition as DrawingChat. */
export function SaveReferencePanel({
  sessionId,
  reportType,
  token,
}: {
  sessionId: string;
  reportType: string;
  token: string;
}) {
  const t = useT();
  const [tag, setTag] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!tag.trim()) {
      setError(t.rag_tag_required);
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await saveReferenceExample(token, { session_id: sessionId, report_type: reportType, tag: tag.trim() });
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated p-4 space-y-2.5">
      <h3 className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
        <BookMarked className="h-4 w-4" /> {t.rag_header}
      </h3>
      <p className="text-xs text-text-secondary">{t.rag_caption}</p>
      <p className="text-xs text-warning bg-warning/10 border border-warning/30 rounded-[var(--radius-sm)] px-2.5 py-2">
        {t.rag_correction_caveat}
      </p>

      <div className="flex items-center gap-2">
        <Input
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder={t.rag_tag_placeholder}
          disabled={saved}
        />
        <Button size="sm" variant="secondary" onClick={handleSave} disabled={saving || saved}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
          {t.rag_save_btn}
        </Button>
      </div>

      {error && <p className="text-xs text-danger">{error}</p>}
      {saved && <p className="text-xs text-success">{t.rag_saved_ok}</p>}
    </div>
  );
}

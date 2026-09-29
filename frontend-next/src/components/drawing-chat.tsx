"use client";

import { useEffect, useRef, useState } from "react";
import { MessageCircle, Send, Loader2 } from "lucide-react";
import { useT } from "@/lib/i18n";
import { ApiError, askAboutDrawing, getChatHistory, type BoqComponent, type ChatMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SelectNative } from "@/components/ui/select-native";
import { cn } from "@/lib/utils";
import { BoqTable } from "@/components/boq-table";
import { extractChatTable } from "@/lib/chat-table";
import {
  SECURITY_PROMPTS,
  SUBSTATION_CLASS_OPTIONS,
  SECURITY_PROMPT_OPTIONS,
  type SubstationClass,
  type SecurityPromptKey,
} from "@/lib/security-prompts";
import { FIRE_PROTECTION_PROMPT } from "@/lib/fire-prompts";

type Template = "custom" | "materials" | "rooms" | "element_check" | "security" | "fire";

// Templates whose answer is asked to come back with a machine-parsable
// BOQ table attached (see askAboutDrawing's expectTable and
// lib/chat-table.ts) — both are fixed engineering-spec prompts that
// always end in "produce a Bill of Quantities", unlike the free-form/
// materials/rooms/element templates which are genuinely open questions.
const TABLE_TEMPLATES: Template[] = ["security", "fire"];

/** Interactive "ask about this drawing" chat — the direct port of the
 * Streamlit app's chat_header/chat_* section (frontend/app.py, around
 * the "Interactive chat about this drawing" comment). Reuses the same
 * PDF already stored on the session server-side (see app/routers/chat.py
 * — it requires AnalysisSession.pdf_bytes, which only exists once the
 * session has been saved via /auth/sessions/save), so this only ever
 * renders for a sessionId that is guaranteed to already be saved.
 *
 * `reportType` is optional (the archive page derives it from the saved
 * session's `system_type` — see archive/page.tsx) and unlocks one of two
 * extra fixed-prompt templates depending on what it resolves to: the
 * HCIS-style substation security prompts (lib/security-prompts.ts) when
 * it contains "security", or the TES-P-119.21 fire protection prompt
 * (lib/fire-prompts.ts) when it contains "fire" — a security chat never
 * shows the fire prompt and vice versa, since each only makes sense
 * against its own drawing type.
 *
 * `onMergeComponents`, if given, renders an "Add to main table" button
 * under any reply that came back with a parsed table (see
 * lib/chat-table.ts) — the caller decides what "the main table" means:
 * analyze/page.tsx merges into its in-memory `result` state, while
 * archive/page.tsx both updates its local session list AND re-persists
 * the merged data via saveSessionData() so it survives a reload. */
export function DrawingChat({
  sessionId,
  token,
  reportType,
  onMergeComponents,
}: {
  sessionId: string;
  token: string;
  reportType?: string;
  onMergeComponents?: (components: BoqComponent[]) => void;
}) {
  const t = useT();
  const isSecurity = reportType?.toLowerCase().includes("security") ?? false;
  const isFire = reportType?.toLowerCase().includes("fire") ?? false;
  const [messages, setMessages] = useState<ChatMessage[] | null>(null);
  const [template, setTemplate] = useState<Template>("custom");
  const [customQuestion, setCustomQuestion] = useState("");
  const [materialsDetails, setMaterialsDetails] = useState("");
  const [element, setElement] = useState("");
  const [substationClass, setSubstationClass] = useState<SubstationClass>("class1");
  const [securityPromptKey, setSecurityPromptKey] = useState<SecurityPromptKey>("video_access");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addedIndices, setAddedIndices] = useState<Set<number>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setAddedIndices(new Set());
    getChatHistory(token, sessionId)
      .then(setMessages)
      .catch(() => setMessages([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function resolveQuestion(): string | null {
    if (template === "custom") return customQuestion.trim() || null;
    if (template === "materials") {
      const details = materialsDetails.trim();
      if (!details) return null;
      return `احسبلي كميات المواد/الأجهزة في المخطط بالتفصيل ده:\n${details}`;
    }
    if (template === "rooms") {
      return "احسبلي قياسات (الأبعاد والمساحات) كل الغرف الموجودة في المخطط، واذكر رقم الصفحة لكل غرفة لو ينفع.";
    }
    if (template === "element_check") {
      const name = element.trim();
      if (!name) return null;
      return `هل يوجد ${name} في المخطط؟ لو موجود، وضّح فين بالظبط (رقم الصفحة/الموقع) وكام عدده.`;
    }
    if (template === "security") {
      return SECURITY_PROMPTS[substationClass][securityPromptKey];
    }
    if (template === "fire") {
      return FIRE_PROTECTION_PROMPT;
    }
    return null;
  }

  async function handleSend() {
    const question = resolveQuestion();
    if (!question) {
      setError(t.chat_template_need_input);
      return;
    }
    setError(null);
    setSending(true);
    // Optimistic append so the question shows immediately, matching the
    // Streamlit version's behavior of showing the user's turn right away
    // rather than waiting for the round-trip.
    setMessages((prev) => [...(prev ?? []), { role: "user", content: question }]);
    setCustomQuestion("");
    setMaterialsDetails("");
    setElement("");
    try {
      const res = await askAboutDrawing(token, sessionId, question, TABLE_TEMPLATES.includes(template));
      setMessages((prev) => [...(prev ?? []), { role: "assistant", content: res.answer }]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated">
      <div className="px-4 py-3 border-b border-border-subtle">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
          <MessageCircle className="h-4 w-4" /> {t.chat_header}
        </h3>
        <p className="text-xs text-text-secondary mt-1">{t.chat_caption}</p>
      </div>

      <div ref={scrollRef} className="max-h-80 overflow-y-auto px-4 py-3 space-y-2">
        {messages === null ? (
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> {t.archive_loading}
          </div>
        ) : messages.length === 0 ? (
          <p className="text-xs text-text-muted">{t.chat_empty}</p>
        ) : (
          messages.map((m, i) => {
            // Only assistant replies ever carry a fenced ```json table
            // block (see lib/chat-table.ts) — skip the parse for user
            // turns, whose content is always the plain prompt text.
            const parsed = m.role === "assistant" ? extractChatTable(m.content) : null;

            if (parsed?.table) {
              const added = addedIndices.has(i);
              return (
                <div key={i} className="space-y-2">
                  {parsed.text && (
                    <div className="max-w-[85%] me-auto rounded-[var(--radius-md)] bg-bg-elevated-2 text-text-primary px-3 py-2 text-sm whitespace-pre-wrap">
                      {parsed.text}
                    </div>
                  )}
                  <BoqTable data={parsed.table.components} />
                  {parsed.table.flagged_unclear_areas.length > 0 && (
                    <ul className="space-y-1">
                      {parsed.table.flagged_unclear_areas.map((note, j) => (
                        <li
                          key={j}
                          className="text-xs text-text-secondary bg-bg-elevated-2 rounded-[var(--radius-sm)] px-2.5 py-1.5"
                        >
                          🔹 {note}
                        </li>
                      ))}
                    </ul>
                  )}
                  {onMergeComponents && (
                    <div className="flex justify-end">
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={added}
                        onClick={() => {
                          onMergeComponents(parsed.table!.components);
                          setAddedIndices((s) => new Set(s).add(i));
                        }}
                      >
                        {added ? t.chat_table_added_ok : t.chat_table_add_to_main}
                      </Button>
                    </div>
                  )}
                </div>
              );
            }

            return (
              <div
                key={i}
                className={cn(
                  "max-w-[85%] rounded-[var(--radius-md)] px-3 py-2 text-sm whitespace-pre-wrap",
                  m.role === "user"
                    ? "ms-auto bg-accent-soft text-text-primary"
                    : "me-auto bg-bg-elevated-2 text-text-primary"
                )}
              >
                {m.content}
              </div>
            );
          })
        )}
        {sending && (
          <div className="me-auto max-w-[85%] rounded-[var(--radius-md)] bg-bg-elevated-2 px-3 py-2 text-sm text-text-secondary flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> {t.chat_thinking}
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-border-subtle space-y-2">
        <SelectNative value={template} onChange={(e) => setTemplate(e.target.value as Template)}>
          <option value="custom">{t.chat_template_custom}</option>
          <option value="materials">{t.chat_template_materials}</option>
          <option value="rooms">{t.chat_template_rooms}</option>
          <option value="element_check">{t.chat_template_element}</option>
          {isSecurity && <option value="security">{t.chat_template_security}</option>}
          {isFire && <option value="fire">{t.chat_template_fire}</option>}
        </SelectNative>

        {template === "custom" && (
          <div className="flex items-center gap-2">
            <Input
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
              placeholder={t.chat_placeholder}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
          </div>
        )}
        {template === "materials" && (
          <textarea
            value={materialsDetails}
            onChange={(e) => setMaterialsDetails(e.target.value)}
            placeholder={t.chat_template_materials_placeholder}
            rows={3}
            className="flex w-full rounded-[var(--radius-sm)] border border-border bg-bg-elevated-2 px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:border-accent focus-visible:ring-1 focus-visible:ring-accent"
          />
        )}
        {template === "rooms" && <p className="text-xs text-text-muted">{t.chat_template_rooms_hint}</p>}
        {template === "element_check" && (
          <Input
            value={element}
            onChange={(e) => setElement(e.target.value)}
            placeholder={t.chat_template_element_placeholder}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
        )}
        {template === "security" && (
          <div className="space-y-2">
            <p className="text-xs text-text-muted">{t.chat_security_hint}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs text-text-secondary">{t.chat_security_class_label}</label>
                <SelectNative
                  value={substationClass}
                  onChange={(e) => setSubstationClass(e.target.value as SubstationClass)}
                >
                  {SUBSTATION_CLASS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </SelectNative>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-text-secondary">{t.chat_security_prompt_label}</label>
                <SelectNative
                  value={securityPromptKey}
                  onChange={(e) => setSecurityPromptKey(e.target.value as SecurityPromptKey)}
                >
                  {SECURITY_PROMPT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </SelectNative>
              </div>
            </div>
          </div>
        )}
        {template === "fire" && <p className="text-xs text-text-muted">{t.chat_fire_hint}</p>}

        {error && <p className="text-xs text-danger">{error}</p>}

        <div className="flex justify-end">
          <Button size="sm" onClick={handleSend} disabled={sending}>
            {sending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
            {t.chat_send}
          </Button>
        </div>
      </div>
    </div>
  );
}

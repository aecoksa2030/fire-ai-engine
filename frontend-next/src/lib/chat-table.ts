import type { BoqComponent } from "./api";

export type ParsedChatTable = {
  components: BoqComponent[];
  flagged_unclear_areas: string[];
};

// Matches the fenced ```json ... ``` block the model is asked to append
// when a question was sent with expect_table:true (see
// app/services/claude_chat_service.py's TABLE_FORMAT_SUFFIX on the
// backend). Used identically for a just-arrived live reply and for a
// historical message reloaded from GET /chat/{id}/history — both are
// plain strings from the same ChatMessage.content column, so one parser
// covers both paths with no backend-shape difference to reconcile.
const JSON_BLOCK_RE = /```json\s*([\s\S]*?)```/i;

/** Splits a chat message's raw text into the human-readable prose (with
 * the fenced JSON block removed, since it's not meant to be read) and,
 * if a well-formed `{components: [...]}` block was found, the parsed
 * table data to render with <BoqTable>. Returns `table: null` — and
 * `text` unchanged — for any message that isn't one of the fixed BOQ
 * prompts (normal free-form chat answers never contain this block). */
export function extractChatTable(content: string): { text: string; table: ParsedChatTable | null } {
  const match = content.match(JSON_BLOCK_RE);
  if (!match) return { text: content, table: null };

  let parsed: unknown;
  try {
    parsed = JSON.parse(match[1]);
  } catch {
    return { text: content, table: null };
  }

  if (
    !parsed ||
    typeof parsed !== "object" ||
    !Array.isArray((parsed as { components?: unknown }).components)
  ) {
    return { text: content, table: null };
  }

  const obj = parsed as { components: BoqComponent[]; flagged_unclear_areas?: unknown };
  const table: ParsedChatTable = {
    components: obj.components,
    flagged_unclear_areas: Array.isArray(obj.flagged_unclear_areas)
      ? (obj.flagged_unclear_areas as string[])
      : [],
  };

  const text = (content.slice(0, match.index) + content.slice((match.index ?? 0) + match[0].length))
    .trim();

  return { text, table };
}

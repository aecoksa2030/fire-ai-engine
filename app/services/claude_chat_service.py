import base64
import os

import anthropic

from app.services.pricing import PRICING_PER_MILLION_TOKENS

# Powers the "chat about this drawing" feature (app/routers/chat.py) —
# upload the PDF once (already happens automatically as part of the normal
# analyze flow, via /auth/sessions/save), then ask follow-up questions,
# correct a miscount, or ask "what's on page 3" and get an answer grounded
# in the same document, instead of re-uploading it and starting over on
# every question. Deliberately a separate class from ClaudeAIService
# (claude_service.py): that one does stateless one-shot "here's one
# rendered page, extract JSON" calls with no memory between pages. This one
# keeps a real, growing conversation around ONE full multi-page PDF.
#
# Built on Claude specifically (not Gemini/Groq/OpenRouter) because of
# prompt caching: the Messages API has no server-side session of its own —
# every single turn has to resend the ENTIRE conversation from scratch,
# document included. Without caching, a 10-question review session would
# mean paying full input price to reprocess the whole PDF ten times over.
# With cache_control on the document block (see ask() below), Anthropic
# recognizes the repeated identical prefix and charges a small cache-read
# fee for it instead — the cost profile that actually makes an iterative
# back-and-forth review conversation practical instead of prohibitively
# expensive. (Below Anthropic's minimum cacheable size — roughly 1024
# tokens for a Sonnet/Opus-class model — cache_control is silently a
# no-op; a real multi-page engineering drawing PDF is comfortably over
# that, so this isn't a practical concern here.)
CHAT_SYSTEM_INSTRUCTION = (
    "You are an assistant helping a fire-protection/security engineer"
    " review an AI-generated bill-of-quantities (BOQ) extracted from the"
    " attached engineering drawing set (the full PDF — every page). Answer"
    " questions about what's on the drawings, help correct or refine"
    " component counts/types/locations when asked, and cite specific page"
    " numbers when it helps. Reply in whichever language the question was"
    " asked in (Arabic or English). Be concise and concrete — this is a"
    " working review conversation, not a formal report."
)

# Appended (only to the copy of the question actually sent to the model —
# never to what's shown to the user or persisted as their chat turn, see
# ask() below) for the fixed BOQ-generating prompts, so the reply can be
# rendered back on the frontend as a real, downloadable/editable table
# (src/lib/chat-table.ts parses this fenced block back out of the
# response) instead of just a wall of prose the user would have to
# manually retype into a spreadsheet.
TABLE_FORMAT_SUFFIX = (
    "\n\n---\n"
    "OUTPUT FORMAT (required): keep any narrative explanation SHORT — at"
    " most 2-3 sentences of summary/caveats, or skip it entirely if"
    " space is tight. Do not restate or re-derive the requirements above"
    " in prose. Then end your reply with a fenced code block that starts"
    " with ```json and ends with ``` containing ONLY a single valid JSON"
    " object of exactly this shape (no comments, no trailing commas, no"
    " extra markdown inside it):\n"
    '{"components": [{"name": string, "count": integer, "confidence":'
    ' "high" | "medium" | "low", "supplier_type": string or null}],'
    ' "flagged_unclear_areas": [string]}\n'
    "This JSON must be the COMPLETE, exhaustive bill of quantities for"
    " everything requested above — every item/category mentioned in the"
    " prompt must appear as one or more rows; do not skip, merge away,"
    " or summarize any of them out of the JSON. The JSON block is the"
    " priority — if you are at risk of running out of room, cut the"
    " prose first, never the JSON."
)


class ClaudeChatService:

  def __init__(self):
    self.client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        max_retries=5,
    )
    # Same env var / default as claude_service.py — see that file's
    # comment for why claude-fable-5 beats Sonnet on this project's actual
    # drawings. Sharing the var means one override affects both features
    # consistently rather than needing two separate env vars in sync.
    self.model = os.environ.get("CLAUDE_MODEL", "claude-fable-5")

  def _document_block(self, file_base64: str) -> dict:
    return {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": file_base64,
        },
        # Marks "cache everything up to and including this block" —
        # see the module comment above for why this is the whole point.
        "cache_control": {"type": "ephemeral"},
    }

  def ask(
      self,
      pdf_bytes: bytes,
      history: list,
      question: str,
      expect_table: bool = False,
  ) -> dict:
    """`history` is this session's prior turns in chronological order —
    a list of {"role": "user"|"assistant", "content": str} dicts, NOT
    including the new `question`. Returns {"answer": str, "usage": {...}}.

    The document block is placed on the FIRST user turn only — Claude
    doesn't need it repeated on every turn, just present once at a
    consistent position so the cached prefix matches turn over turn.

    `expect_table`: when True, the CURRENT turn only gets
    TABLE_FORMAT_SUFFIX appended to what's actually sent to the model
    (`question_for_model`) — the plain `question` passed in (and echoed
    back to the router to persist as this turn's ChatMessage) is left
    untouched, so the chat bubble the user sees/reloads never shows the
    formatting instructions, only the prompt they picked. Prior turns in
    `history` are replayed to the model exactly as they were stored.
    """
    file_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    question_for_model = question + TABLE_FORMAT_SUFFIX if expect_table else question

    if not history:
      messages = [{
          "role": "user",
          "content": [
              self._document_block(file_base64),
              {"type": "text", "text": question_for_model},
          ],
      }]
    else:
      first_turn = history[0]
      messages = [{
          "role": "user",
          "content": [
              self._document_block(file_base64),
              {"type": "text", "text": first_turn["content"]},
          ],
      }]
      for turn in history[1:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
      messages.append({"role": "user", "content": question_for_model})

    response = self.client.messages.create(
        model=self.model,
        # 4096 for a normal free-form chat turn is generous already (see
        # the original comment this replaced). But expect_table turns
        # send one of the fixed HCIS/TES-P-119.21 prompts — each already a
        # long, multi-section requirement list — and then ask the model
        # to additionally emit a full, non-summarized BOQ JSON array on
        # top of that. claude_service.py hit this exact symptom (a call
        # silently cut off mid-output) at 4096 and fixed it by doubling to
        # 8192 — see its own comment for the history — so the same fix
        # applies here for the same reason once expect_table pushes the
        # expected output that much larger.
        max_tokens=8192 if expect_table else 4096,
        system=CHAT_SYSTEM_INSTRUCTION,
        messages=messages,
    )

    answer = next(
        (b.text for b in response.content if hasattr(b, "text")), ""
    ).strip()

    # Mirrors claude_service.py's own stop_reason == "max_tokens" handling
    # (see that file for the original occurrence of this symptom) — a
    # truncated table reply is often a JSON block cut off mid-object,
    # which lib/chat-table.ts on the frontend then simply fails to parse
    # (no table renders, just the raw text) with no indication to the
    # user of *why*. Flagging it explicitly here beats leaving them to
    # guess whether the model just produced a bad answer.
    if response.stop_reason == "max_tokens":
      truncation_note = (
          "\n\n⚠️ الرد اتقطع لأنه وصل لأقصى طول مسموح به — لو الجدول ناقص"
          " أو مش ظاهر خالص، جرب تسأل عن جزء أصغر من المخطط في المرة"
          " الواحدة (مبنى أو منطقة بدل المخطط كله)."
      )
      answer = (answer + truncation_note) if answer else truncation_note.strip()

    usage = response.usage
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0

    # pricing.py's estimate_cost_usd() only knows flat input/output
    # rates — it has no idea cache write/read tokens exist, so cost is
    # computed directly here instead of routing through it. Anthropic's
    # documented cache multipliers, relative to the model's base input
    # rate: a cache WRITE costs 1.25x base input (writing to cache costs
    # slightly more than a normal call), a cache READ costs 0.1x base
    # input (the entire point — reusing the cached PDF is ~90% cheaper
    # than reprocessing it). claude-fable-5's base rate lives in
    # pricing.py's PRICING_PER_MILLION_TOKENS, reused here rather than
    # duplicated.
    base_rates = None
    for name, rates in PRICING_PER_MILLION_TOKENS.items():
      if name.lower() in self.model.lower() or self.model.lower() in name.lower():
        base_rates = rates
        break

    if base_rates:
      cost = (
          (input_tokens / 1_000_000) * base_rates["input"]
          + (cache_write_tokens / 1_000_000) * base_rates["input"] * 1.25
          + (cache_read_tokens / 1_000_000) * base_rates["input"] * 0.1
          + (output_tokens / 1_000_000) * base_rates["output"]
      )
    else:
      cost = 0.0

    return {
        "answer": answer or "الموديل رجع رد فاضي — جرب تصيغ السؤال بشكل تاني.",
        "usage": {
            "provider": "claude",
            "model": response.model,
            "input_tokens": input_tokens,
            "cache_write_tokens": cache_write_tokens,
            "cache_read_tokens": cache_read_tokens,
            "output_tokens": output_tokens,
            "total_cost_usd": round(cost, 6),
        },
    }

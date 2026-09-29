import base64
import json
import os

import anthropic

from app.services.json_utils import clean_and_parse_json
from app.services.pricing import estimate_cost_usd
from app.services.prompts import FIRE_PROTECTION_PROMPT, SECURITY_PROMPT

# Strict JSON-only system instruction. The actual task prompt (scoped to a
# single drawing page — see app/services/prompts.py) is sent as the user
# message alongside the image.
SYSTEM_INSTRUCTION = (
    "You are a strict JSON extraction API for engineering drawing takeoffs."
    " Return exactly one raw JSON object matching the schema you are given"
    " — no markdown fences, no commentary before or after it."
)


class ClaudeAIService:

  def __init__(self):
    self.client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        max_retries=5,
    )
    # Defaulting to claude-fable-5, reverting an earlier attempt to default
    # to claude-sonnet-5 for the ~5x cost saving ($2/$10 vs $10/$50 per
    # MTok). That saving only matters if the cheaper model actually
    # produces usable output — tested directly against this project's real
    # dense site-plan drawings (same prompt, same image, same pipeline),
    # Sonnet came back with zero components while Fable correctly picked
    # out dozens of individually-tagged devices. A free result is worth
    # nothing if it's empty, so accuracy wins over cost here. Override via
    # CLAUDE_MODEL to try Sonnet again — e.g. it may still be perfectly
    # fine on simpler / less symbol-dense drawings — but Fable is the
    # proven-working default until there's a similarly direct test showing
    # otherwise.
    self.model = os.environ.get("CLAUDE_MODEL", "claude-fable-5")

  def _analyze(
      self,
      file_bytes: bytes,
      prompt: str,
      system_type_on_error: str,
      media_kind: str = "image",
      reference_examples: str = "",
  ) -> str:
    # reference_examples comes from
    # app/services/reference_library_service.py — past approved projects
    # of the same report_type, serialized as text and prepended here so
    # the model has concrete grounding for typical naming/counting
    # patterns instead of relying on general knowledge alone. Empty
    # string (the default, and what a library with no saved examples yet
    # returns) is a no-op.
    if reference_examples:
      prompt = reference_examples + prompt
    file_base64 = base64.b64encode(file_bytes).decode("utf-8")

    # PDF support is GA on the Messages API (no beta header needed) as of
    # Aug 2026 — a "document" block with a single-page PDF gives Claude the
    # page's real vector text/linework instead of a fixed-DPI JPEG. Groq
    # doesn't support this, so process.py only sets media_kind="pdf" for
    # Claude/Gemini and keeps sending Groq the rendered JPEG.
    if media_kind == "pdf":
      content_block = {
          "type": "document",
          "source": {
              "type": "base64",
              "media_type": "application/pdf",
              "data": file_base64,
          },
      }
    else:
      content_block = {
          "type": "image",
          "source": {
              "type": "base64",
              "media_type": "image/jpeg",
              "data": file_base64,
          },
      }

    try:
      response = self.client.messages.create(
          model=self.model,
          # Headroom for dense pages (many distinct component types). A
          # tighter cap here can silently truncate the JSON mid-array,
          # which then either fails to parse or gets "repaired" into
          # something with far fewer components than the page actually
          # has — indistinguishable from the model just not finding much.
          # Raised 4096->8192 (matching openrouter_service.py's own fix for
          # the same symptom) after the reference_examples/RAG grounding
          # text got prepended to the prompt on every call — a longer input
          # doesn't by itself need more output room, but it was the one
          # thing that changed right before "no components at all" started
          # showing up across multiple real drawings, so ruling this out
          # cheaply is worth doing even though the exact cause is still
          # unconfirmed (see the now-visible flagged_unclear_areas error
          # banner in the frontend for the real per-page error text).
          max_tokens=8192,
          system=SYSTEM_INSTRUCTION,
          messages=[{
              "role": "user",
              "content": [
                  content_block,
                  {"type": "text", "text": prompt},
              ],
          }],
      )

      result_text = next(
          (b.text for b in response.content if hasattr(b, "text")), ""
      ).strip()
      parsed = clean_and_parse_json(result_text)

      if response.stop_reason == "max_tokens":
        parsed.setdefault("flagged_unclear_areas", []).append(
            "Response was cut off at the model's token limit — this page"
            " may have more components than were captured. Consider"
            " re-running this page alone if the count looks low."
        )

      parsed["api_usage"] = {
          "provider": "claude",
          "model": response.model,
          "input_tokens": response.usage.input_tokens,
          "output_tokens": response.usage.output_tokens,
          "total_cost_usd": estimate_cost_usd(
              response.model,
              response.usage.input_tokens,
              response.usage.output_tokens,
          ),
      }
      return json.dumps(parsed, ensure_ascii=False)

    except Exception as e:
      return json.dumps({
          "system_type": system_type_on_error,
          "components": [],
          "flagged_unclear_areas": [f"Claude Error: {str(e)}"],
      })

  def analyze_fire_alarm_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, FIRE_PROTECTION_PROMPT, "Fire Protection System", media_kind,
        reference_examples,
    )

  def analyze_security_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, SECURITY_PROMPT, "Physical Security System", media_kind,
        reference_examples,
    )

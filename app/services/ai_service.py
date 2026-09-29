import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.services.json_utils import clean_and_parse_json
from app.services.pricing import estimate_cost_usd
from app.services.prompts import FIRE_PROTECTION_PROMPT, SECURITY_PROMPT

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Current GA Gemini Flash model as of Aug 2026. Override via GEMINI_MODEL if
# Google ships a newer default you want to switch to.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Explicit schema so Gemini can't drift on field names/types — this is what
# process.py's aggregation code actually expects back.
BOQ_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "system_type": {"type": "STRING"},
        "components": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "count": {"type": "INTEGER"},
                    "supplier_type": {"type": "STRING"},
                    "unit_cost_sar": {"type": "NUMBER"},
                    "confidence": {"type": "STRING"},
                },
                "required": [
                    "name",
                    "count",
                    "supplier_type",
                    "unit_cost_sar",
                    "confidence",
                ],
            },
        },
        "flagged_unclear_areas": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": ["system_type", "components", "flagged_unclear_areas"],
}


class GeminiAIService:

  def __init__(self):
    if not GEMINI_API_KEY:
      print("⚠️ WARNING: GEMINI_API_KEY is missing!")
      self.client = None
    else:
      self.client = genai.Client(api_key=GEMINI_API_KEY)

  def _default_fallback(self, system_type: str, message: str) -> str:
    return json.dumps({
        "system_type": system_type,
        "components": [],
        "flagged_unclear_areas": [message],
    })

  def _analyze(
      self,
      file_bytes: bytes,
      prompt: str,
      system_type: str,
      media_kind: str = "image",
      reference_examples: str = "",
  ) -> str:
    if not self.client:
      return self._default_fallback(system_type, "GEMINI_API_KEY is missing.")

    # See claude_service.py's _analyze for what reference_examples is and
    # why it's a plain no-op when empty (the default / a library with no
    # saved examples for this report_type yet).
    if reference_examples:
      prompt = reference_examples + prompt

    # Gemini accepts inline PDF bytes the same way it accepts inline image
    # bytes (Part.from_bytes + mime_type) — no separate Files API call
    # needed for a single-page PDF well under the 50MB inline ceiling.
    # Sending the native page instead of a JPEG lets Gemini read the
    # page's actual embedded text (title block, scale bar, schedules)
    # rather than OCR-ing it off a raster.
    mime_type = "application/pdf" if media_kind == "pdf" else "image/jpeg"
    file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    config = types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
        response_schema=BOQ_SCHEMA,
    )

    # Gemini has no built-in retry for transient overload, and "high
    # demand" 503s show up regularly under normal load — without a retry,
    # every one of those silently drops the whole page (zero components,
    # no obvious error to the user beyond a server log line). Two short
    # retries with backoff clears most of them; anything still failing
    # after that is a real error, not a blip.
    last_error = None
    for attempt in range(3):
      try:
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, file_part],
            config=config,
        )

        parsed = clean_and_parse_json(response.text or "")

        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
          input_tokens = getattr(usage, "prompt_token_count", 0) or 0
          output_tokens = getattr(usage, "candidates_token_count", 0) or 0
          parsed["api_usage"] = {
              "provider": "gemini",
              "model": GEMINI_MODEL,
              "input_tokens": input_tokens,
              "output_tokens": output_tokens,
              "total_cost_usd": estimate_cost_usd(
                  GEMINI_MODEL, input_tokens, output_tokens
              ),
          }

        return json.dumps(parsed, ensure_ascii=False)

      except Exception as e:
        last_error = e
        error_msg = str(e)
        is_transient = any(
            marker in error_msg
            for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
        )
        if is_transient and attempt < 2:
          print(
              f"Gemini API transient error (attempt {attempt + 1}/3),"
              f" retrying: {error_msg}"
          )
          time.sleep(2 * (attempt + 1))
          continue
        print(f"Gemini API Error: {error_msg}")
        break

    return self._default_fallback(system_type, f"Gemini Error: {str(last_error)}")

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

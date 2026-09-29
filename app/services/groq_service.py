import base64
import io
import json
import os

from groq import Groq
from PIL import Image

from app.services.json_utils import clean_and_parse_json
from app.services.pricing import estimate_cost_usd
from app.services.prompts import get_groq_prompt

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# qwen/qwen3.6-27b is — as of a direct check of Groq's docs on 2026-08-17 —
# the ONLY vision-capable model Groq currently offers. The two models that
# used to cover this (meta-llama/llama-4-maverick-17b-128e-instruct and
# meta-llama/llama-4-scout-17b-16e-instruct) were deprecated by Groq in
# March and July 2026 respectively, and Groq's own suggested replacement
# (openai/gpt-oss-120b) is text-only — it does not accept image input at
# all. If you swap GROQ_MODEL for something else, confirm on
# console.groq.com/docs/vision that it actually supports image_url content
# first — most Groq models (including gpt-oss-*, including
# gpt-oss-safeguard-20b) are text-only and will reject an image request
# outright, sometimes with a confusing unrelated-looking error rather than
# "this model doesn't support images".
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b")


class GroqAIService:
  """Third comparison provider. Was originally built on the exact same
  prompts as Claude and Gemini for a clean apples-to-apples comparison, but
  now uses a shorter, Groq-only prompt (get_groq_prompt() in
  app/services/prompts.py) — Groq's account-wide 8,000 tokens-per-minute
  cap on qwen/qwen3.6-27b (same on Free and Developer plans) can't fit the
  full prompt plus an image at all, so this is a forced trade-off, not a
  design choice. See the "Sixth iteration note" in prompts.py for the full
  story and the token-accounting evidence behind it."""

  def __init__(self):
    if not GROQ_API_KEY:
      print("⚠️ WARNING: GROQ_API_KEY is missing!")
      self.client = None
    else:
      self.client = Groq(api_key=GROQ_API_KEY)

  def _default_fallback(self, system_type: str, message: str) -> str:
    return json.dumps({
        "system_type": system_type,
        "components": [],
        "flagged_unclear_areas": [message],
    })

  @staticmethod
  def _downscale_jpeg(image_bytes: bytes, max_dimension: int, quality: int = 85) -> bytes:
    """Resize a JPEG so its longest edge is at most max_dimension.

    Groq's on-demand/free tier caps qwen/qwen3.6-27b at a very low 8,000
    tokens-PER-MINUTE (not per request) — a single page from this pipeline
    (our multi-hundred-line prompt + a full-resolution engineering-drawing
    JPEG rendered at zoom=2.0 for Claude/Gemini's benefit) can exceed that
    on its own. Claude and Gemini don't have this constraint, so this
    downscale is applied only here for Groq, not in the shared renderer
    (app/services/parser_service.py) that all three providers pull from.
    Returns the original bytes unchanged if already under max_dimension —
    no point re-encoding (and losing quality) for pages that don't need it.
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
      width, height = img.size
      if max(width, height) <= max_dimension:
        return image_bytes

      scale = max_dimension / max(width, height)
      new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
      resized = img.convert("RGB").resize(new_size, Image.LANCZOS)

      out = io.BytesIO()
      resized.save(out, format="JPEG", quality=quality)
      return out.getvalue()

  def _analyze(
      self,
      file_bytes: bytes,
      prompt: str,
      system_type: str,
      media_kind: str = "image",
      reference_examples: str = "",
  ) -> str:
    if not self.client:
      return self._default_fallback(system_type, "GROQ_API_KEY is missing.")

    # See claude_service.py's _analyze for what this is. Deliberately
    # applied AFTER the media_kind guard below but BEFORE the prompt is
    # used — note this makes an already-tight prompt budget tighter still
    # (see the module docstring's TPM story), so reference_library_service
    # keeps this block small (DEFAULT_EXAMPLE_LIMIT) on purpose.
    if reference_examples:
      prompt = reference_examples + prompt

    if media_kind != "image":
      # Groq's documented vision API takes image_url content only — no
      # native PDF document input. process.py knows this and always sends
      # Groq the rendered-JPEG path (media_kind="image"), but guard here
      # too in case that ever changes, instead of silently mishandling a
      # PDF as if it were a JPEG.
      return self._default_fallback(
          system_type,
          f"Groq Error: unsupported media_kind '{media_kind}' — Groq only"
          " accepts rendered images, not native PDF pages.",
      )

    request_kwargs_base = dict(
        model=GROQ_MODEL,
        temperature=0.1,
        # Lowered from 4096. OpenAI-compatible rate limiters (Groq's API is
        # OpenAI-compatible) commonly reserve max_tokens against the TPM
        # budget as a worst-case estimate before generation even starts —
        # consistent with what was observed here: a production request
        # (compact prompt would come to roughly prompt(~700) + a fixed
        # per-image charge + max_tokens) measured at 8,757 tokens against
        # an 8,000 cap. 2048 is still generous for this compact prompt's
        # JSON output (a handful of components + short flags) and frees up
        # real headroom instead of reserving tokens a single page rarely
        # needs.
        max_tokens=2048,
    )

    if "qwen" in GROQ_MODEL.lower():
      # qwen3.6-27b runs in "thinking" mode by default, which writes its
      # reasoning as raw <think>...</think> text directly into
      # message.content (Groq's default reasoning_format is "raw"). On
      # this bounded, single-page extraction task that reasoning phase can
      # consume the entire output budget and leave content empty or
      # truncated mid-<think> — which is exactly what caused "Expecting
      # value: line 1 column 1 (char 0)" (json.loads() on an
      # empty/garbage string). reasoning_effort="none" turns thinking mode
      # off entirely so content is the direct answer; reasoning_format=
      # "hidden" is a second safety net in case any residual reasoning
      # text is produced anyway.
      #
      # "none" is a Qwen-specific value — other Groq reasoning models
      # (e.g. the gpt-oss-* family) only accept low/medium/high and 400 on
      # "none", so this is deliberately scoped to Qwen rather than applied
      # unconditionally.
      request_kwargs_base["reasoning_effort"] = "none"
      request_kwargs_base["reasoning_format"] = "hidden"

    # NOTE on what actually fixes the TPM error: the real fix is the
    # compact Groq-only prompt (get_groq_prompt(), ~1,800 tokens shorter
    # than the shared prompt) plus the lower max_tokens above. Resizing the
    # image, tested directly against production, did NOT change Groq's
    # reported "Requested" token count at all across three very different
    # resolutions (2300px/1568px/800px all reported the identical
    # "Requested 8757") — strong evidence Qwen's TPM accounting charges a
    # fixed cost per image regardless of actual resolution. This resize
    # loop is kept anyway because it's a real, if different, safety net:
    # Groq's documented hard cap is 20MB per image request, which IS
    # resolution-dependent, and smaller images mean less upload bandwidth
    # and lower latency — just don't expect it to move the TPM number.
    max_dimension_attempts = [1568, 1100, 800]
    last_error = None

    for attempt_index, max_dimension in enumerate(max_dimension_attempts):
      try:
        attempt_image_bytes = self._downscale_jpeg(file_bytes, max_dimension)
        image_base64 = base64.b64encode(attempt_image_bytes).decode("utf-8")

        request_kwargs = dict(
            request_kwargs_base,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ],
            }],
        )

        response = self.client.chat.completions.create(**request_kwargs)

        raw_content = response.choices[0].message.content or ""
        if not raw_content.strip():
          finish_reason = getattr(response.choices[0], "finish_reason", "unknown")
          raise ValueError(
              f"Groq returned an empty response (finish_reason={finish_reason})."
              " This usually means the request was rejected/filtered or hit"
              " the token limit before producing an answer."
          )
        parsed = clean_and_parse_json(raw_content)

        usage = getattr(response, "usage", None)
        if usage is not None:
          input_tokens = getattr(usage, "prompt_tokens", 0) or 0
          output_tokens = getattr(usage, "completion_tokens", 0) or 0
          parsed["api_usage"] = {
              "provider": "groq",
              "model": GROQ_MODEL,
              "input_tokens": input_tokens,
              "output_tokens": output_tokens,
              "total_cost_usd": estimate_cost_usd(
                  GROQ_MODEL, input_tokens, output_tokens
              ),
          }

        return json.dumps(parsed, ensure_ascii=False)

      except Exception as e:
        last_error = e
        error_msg = str(e)
        is_request_too_large = (
            "rate_limit_exceeded" in error_msg
            or "tokens per minute" in error_msg
            or "Request too large" in error_msg
        )
        if is_request_too_large and attempt_index < len(max_dimension_attempts) - 1:
          print(
              f"Groq request too large at max_dimension={max_dimension}"
              f" (attempt {attempt_index + 1}/{len(max_dimension_attempts)}),"
              f" retrying with a smaller image: {error_msg}"
          )
          continue
        print(f"Groq API Error: {error_msg}")
        break

    return self._default_fallback(system_type, f"Groq Error: {str(last_error)}")

  def analyze_fire_alarm_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, get_groq_prompt("fire"), "Fire Protection System", media_kind,
        reference_examples,
    )

  def analyze_security_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, get_groq_prompt("security"), "Physical Security System", media_kind,
        reference_examples,
    )

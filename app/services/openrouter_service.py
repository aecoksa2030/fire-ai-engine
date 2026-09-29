import base64
import json
import os

import httpx

from app.services.json_utils import clean_and_parse_json
from app.services.prompts import get_prompt

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fourth comparison provider, but a different kind of provider than the
# other three: Claude/Gemini/Groq each hard-code one specific model.
# OpenRouter is a router in front of hundreds of models from many vendors —
# the whole point of adding it is letting the frontend pick *which* model to
# route to per-request (see the "model" selectbox in frontend/app.py) rather
# than being locked to one. OPENROUTER_MODEL below is only the fallback used
# when no per-request model is supplied.
#
# Picked thinkingmachines/inkling as the fallback — a deliberate choice of
# something DIFFERENT from what this project already has, not a repeat of
# it. Gemini and Claude were ruled out on purpose: this project already has
# dedicated "gemini" and "claude" providers (ai_service.py / claude_service.py)
# running those exact model families in production, so routing OpenRouter to
# the same vendors again would just be a redundant, more roundabout way to
# call something we already call directly. The point of adding OpenRouter is
# reach — trying a genuinely different model and actually seeing what it
# does on these drawings, per project instruction — not another path to the
# same two vendors.
#
# What was checked (all against OpenRouter's live catalog, 2026-08-17):
#   - qwen/qwen3.7-flash — cheapest vision model on OpenRouter, but
#     third-party evals (Roboflow) rank it 22nd/23 overall with OCR dead
#     last — the wrong trade for a job that's mostly reading small symbols
#     off dense drawings. Ruled out on the same grounds as before.
#   - x-ai/grok-4.6 — independent review (Artificial Analysis, via eesel)
#     measured a 65.7% non-hallucination rate, i.e. roughly a third of its
#     wrong answers are confident fabrications rather than "I'm not sure."
#     Bad property for a tool whose output is a bill of quantities someone
#     will actually order equipment against.
#   - moonshotai/kimi-k3 — huge (2.8T/16-of-896-experts) model with native
#     vision, genuinely strong (Moonshot's own numbers put it ahead of
#     Fable 5 in a blind Frontend Code Arena eval), but Moonshot itself
#     says it still sits behind Fable 5 overall, its published wins are all
#     coding-benchmark wins (nothing OCR/document-specific), and output
#     pricing is steep ($15/MTok) — a plausible pick, just not this one.
#   - thinkingmachines/inkling ($0.95/$4.05 per MTok, 1M context) — chosen
#     because unlike a bolt-on vision adapter, it ingests images as raw
#     40x40 patches directly into the transformer stack alongside text and
#     audio (per Thinking Machines' own model card), which is architecturally
#     the kind of thing that could plausibly matter for reading small dense
#     symbols. Scored 73.3% on MMMU Pro (general multimodal understanding).
#     Honest caveat, and the actual reason this is worth trying rather than
#     trusting on paper: there's no independent OCR/document-extraction
#     benchmark for it yet, and every number in its model card is
#     Thinking-Machines-reported, not third-party audited. That's exactly
#     why it's worth running against this project's real drawings and
#     looking at the actual output — which is what was asked for.
# Override with OPENROUTER_MODEL, or better, pick a model per request from
# the frontend.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "thinkingmachines/inkling")

# Identifies this app to OpenRouter — shows up in their dashboard/rankings.
# Neither header is required for requests to work; both are optional
# courtesy headers per OpenRouter's docs.
OPENROUTER_REFERER = os.environ.get("OPENROUTER_SITE_URL", "")
OPENROUTER_APP_NAME = os.environ.get("OPENROUTER_APP_NAME", "Fire AI Engine")


class OpenRouterAIService:
  """Talks to OpenRouter's OpenAI-compatible /chat/completions endpoint
  directly over httpx rather than pulling in the `openai` SDK — httpx is
  already a project dependency (see requirements.txt) and OpenRouter's API
  surface used here (a single non-streaming chat completion with an
  image_url content block) doesn't need anything the SDK would add.

  Unlike the other three services, a model can be supplied per-instance
  (see __init__) so process.py can build a request-scoped instance when the
  frontend picks a specific OpenRouter model, instead of being stuck with
  one hard-coded model like Claude/Gemini/Groq.
  """

  def __init__(self, model: str | None = None):
    self.model = model or OPENROUTER_MODEL
    if not OPENROUTER_API_KEY:
      print("⚠️ WARNING: OPENROUTER_API_KEY is missing!")
      self.client = None
    else:
      headers = {
          "Authorization": f"Bearer {OPENROUTER_API_KEY}",
          "Content-Type": "application/json",
      }
      if OPENROUTER_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_REFERER
      if OPENROUTER_APP_NAME:
        headers["X-Title"] = OPENROUTER_APP_NAME
      self.client = httpx.Client(headers=headers, timeout=120.0)

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
      return self._default_fallback(system_type, "OPENROUTER_API_KEY is missing.")

    # See claude_service.py's _analyze for what this is.
    if reference_examples:
      prompt = reference_examples + prompt

    if media_kind != "image":
      # Same constraint as Groq: process.py currently always sends
      # media_kind="image" (the native-PDF path was reverted project-wide —
      # see parser_service.py), but guard explicitly rather than silently
      # mis-sending PDF bytes as an image_url data URI, since PDF support
      # varies a lot model-to-model on OpenRouter and isn't safe to assume.
      return self._default_fallback(
          system_type,
          f"OpenRouter Error: unsupported media_kind '{media_kind}' — this"
          " service only sends rendered images, not native PDF pages.",
      )

    image_base64 = base64.b64encode(file_bytes).decode("utf-8")

    payload_base = {
        "model": self.model,
        "temperature": 0.1,
        # Bumped from 4096. Production traffic against a reasoning-capable
        # model (thinkingmachines/inkling, this project's default — see
        # OPENROUTER_MODEL's comment, it advertises a "controllable
        # reasoning-effort dial") hit finish_reason="length" with a
        # completely EMPTY message.content: the hidden reasoning phase
        # alone ate the whole 4096-token budget before the model ever got
        # to writing the actual JSON answer. Same root cause as the
        # <think>-mode issue documented in groq_service.py for
        # qwen3.6-27b, just surfacing on a different model here. Extra
        # headroom is the first half of the fix; the "reasoning" block
        # below (capping/lowering how much of the budget reasoning gets
        # to spend) is the second half — raising max_tokens alone doesn't
        # help if reasoning is left free to consume all of it.
        "max_tokens": 8192,
        "messages": [{
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
        # Asks OpenRouter to compute and return real per-request cost in the
        # response's usage object (usage.cost, in USD/credits) instead of
        # us maintaining a static $/token table like pricing.py does for
        # the other providers. That table approach doesn't scale to
        # OpenRouter, which fronts hundreds of models across many vendors
        # with independently-changing prices — asking OpenRouter for the
        # actual charged cost per call is the only accurate option here.
        "usage": {"include": True},
    }

    # OpenRouter's unified "reasoning" request field
    # (openrouter.ai/docs/use-cases/reasoning-tokens) controls reasoning
    # token spend the same way across every vendor's reasoning models, and
    # is a documented no-op for models that don't support reasoning at
    # all — so, unlike groq_service.py (which has to special-case "qwen"
    # because Groq's reasoning params aren't unified across its models),
    # it's safe to send this on every OpenRouter request regardless of
    # which model is selected.
    #
    # Two attempts, weakest-first:
    #   1. effort="low" + exclude=True — leaves the model a small
    #      reasoning budget (OpenRouter's docs note some models reject
    #      effort="none" outright, so "low" rather than "none" first) and
    #      drops the reasoning text from the response since only the
    #      final JSON is needed.
    #   2. enabled=False — forces reasoning off entirely. Only tried if
    #      attempt 1 still comes back empty, since a handful of models
    #      only expose the on/off switch and reject "effort" altogether.
    reasoning_attempts = [
        {"effort": "low", "exclude": True},
        {"enabled": False},
    ]
    last_error = None

    for attempt_index, reasoning_config in enumerate(reasoning_attempts):
      payload = dict(payload_base, reasoning=reasoning_config)

      try:
        response = self.client.post(OPENROUTER_BASE_URL, json=payload)
        try:
          response.raise_for_status()
        except httpx.HTTPStatusError as http_err:
          # response.raise_for_status() alone only gives back the generic
          # "404 Not Found for url ..." — it never reads the response
          # body, so OpenRouter's actual explanation (which model id was
          # rejected and why) never made it into the logs. That's exactly
          # what happened with a hand-typed custom model id: the real
          # cause was hidden behind a useless generic message. Pull
          # OpenRouter's JSON error body (falling back to raw text) so the
          # log actually says what's wrong.
          try:
            body = response.json()
            detail = (body.get("error") or {}).get("message") or body
          except Exception:
            detail = response.text
          hint = (
              " — likely a mistyped or nonexistent model id; double-check"
              " the exact slug against openrouter.ai/models (it must match"
              " a model's \"id\" field exactly, e.g."
              " 'thinkingmachines/inkling', not just the model's display"
              " name)."
              if response.status_code == 404
              else ""
          )
          raise ValueError(
              f"OpenRouter HTTP {response.status_code} for model"
              f" '{self.model}': {detail}{hint}"
          ) from http_err
        data = response.json()

        choices = data.get("choices") or []
        if not choices:
          error_info = data.get("error")
          raise ValueError(
              f"OpenRouter returned no choices (error={error_info})."
          )

        raw_content = (choices[0].get("message") or {}).get("content") or ""
        if not raw_content.strip():
          finish_reason = choices[0].get("finish_reason", "unknown")
          raise ValueError(
              f"OpenRouter returned an empty response (finish_reason={finish_reason})."
              " This usually means a reasoning-capable model spent its"
              " entire token budget on hidden reasoning before writing an"
              " answer."
          )
        parsed = clean_and_parse_json(raw_content)

        usage = data.get("usage")
        if usage:
          parsed["api_usage"] = {
              "provider": "openrouter",
              # OpenRouter can route a request to a fallback model if the
              # requested one is unavailable — data["model"] reflects what
              # actually answered, which may differ from self.model. Report
              # that, not the request-time model, so cost/model stay honest.
              "model": data.get("model", self.model),
              "input_tokens": usage.get("prompt_tokens", 0) or 0,
              "output_tokens": usage.get("completion_tokens", 0) or 0,
              "total_cost_usd": usage.get("cost", 0.0) or 0.0,
          }

        return json.dumps(parsed, ensure_ascii=False)

      except Exception as e:
        last_error = e
        error_msg = str(e)
        is_empty_due_to_reasoning = "finish_reason=length" in error_msg
        if is_empty_due_to_reasoning and attempt_index < len(reasoning_attempts) - 1:
          print(
              f"OpenRouter empty response likely from reasoning overrun"
              f" (attempt {attempt_index + 1}/{len(reasoning_attempts)}),"
              f" retrying with reasoning more aggressively disabled: {error_msg}"
          )
          continue
        print(f"OpenRouter API Error: {error_msg}")
        break

    return self._default_fallback(system_type, f"OpenRouter Error: {str(last_error)}")

  def analyze_fire_alarm_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, get_prompt("fire"), "Fire Protection System", media_kind,
        reference_examples,
    )

  def analyze_security_drawing(
      self, file_bytes: bytes, media_kind: str = "image", reference_examples: str = ""
  ) -> str:
    return self._analyze(
        file_bytes, get_prompt("security"), "Physical Security System", media_kind,
        reference_examples,
    )

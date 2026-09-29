"""Shared helpers for turning a raw LLM text response into a JSON dict.

Used by every AI provider service (Claude / Gemini / Groq) so that JSON
extraction/repair behaves identically no matter which provider produced the
text. Having one implementation also means a parsing fix only needs to be
made once.
"""

import json
import re

import json_repair


def extract_json_object(text: str) -> str:
  """Strip markdown code fences and return the first {...} JSON substring."""
  text = (text or "").strip()

  if "```" in text:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
      text = match.group(1)

  match = re.search(r"\{[\s\S]*\}", text)
  return match.group(0) if match else text


def clean_and_parse_json(text: str) -> dict:
  """Extract, auto-repair, and parse a JSON object from a raw model response.

  Falls back to json_repair so that minor formatting mistakes from the model
  (trailing commas, unescaped quotes, etc.) don't blow up the whole request.
  """
  candidate = extract_json_object(text)
  repaired = json_repair.repair_json(candidate, return_objects=True)

  if isinstance(repaired, dict):
    return repaired
  if isinstance(repaired, str):
    return json.loads(repaired)
  return dict(repaired)

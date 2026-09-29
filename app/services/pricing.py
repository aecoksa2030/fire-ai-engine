"""Best-effort $/token pricing used to estimate and compare API cost across
providers.

Source: each provider's public pricing page, checked 2026-08-17. Prices
change over time — if a provider updates its rates, update the table below
(there is nothing else to change; estimate_cost_usd() just reads it).

  - Anthropic Claude: https://platform.claude.com/docs/en/about-claude/pricing
  - Google Gemini:    https://openrouter.ai/google/gemini-3.7-flash (mirrors Google's list price)
  - Groq:             https://console.groq.com/docs/models
"""

PRICING_PER_MILLION_TOKENS = {
    "claude-sonnet-5": {"input": 2.0, "output": 10.0},
    "claude-fable-5": {"input": 10.0, "output": 50.0},
    "gemini-3.7-flash": {"input": 0.375, "output": 1.875},
    "qwen/qwen3.6-27b": {"input": 0.60, "output": 3.00},
}


def estimate_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
  """Return an estimated USD cost for a single call, or 0.0 if the model
  isn't in the pricing table (rather than guessing a number)."""
  if not model_name:
    return 0.0

  key = model_name.lower()
  rates = None
  for name, r in PRICING_PER_MILLION_TOKENS.items():
    if name.lower() in key or key in name.lower():
      rates = r
      break

  if not rates:
    return 0.0

  cost = (input_tokens / 1_000_000) * rates["input"] + (
      output_tokens / 1_000_000
  ) * rates["output"]
  return round(cost, 6)

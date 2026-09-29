"""RAG-lite "reference library": lets extraction/chat prompts get grounded
in past approved projects instead of relying purely on a model's general
knowledge — the whole point being consistency with how this team actually
names/counts components, not what a model guesses from training data alone.

Deliberately the simplest version that could work. See the module-level
notes on ReferenceExample (app/database.py) and each function below for
what was intentionally left out (embeddings, vector search) and why —
that's a valid v2 if the library outgrows this, not a gap to silently
paper over here.
"""
import difflib

from app.database import ReferenceExample

# How many past examples get pulled in as grounding per request. Kept
# small on purpose: these get serialized as text and prepended to every
# single-page extraction prompt (see build_examples_block below) — too
# many and this starts eating into the same token budget the actual
# analysis needs (see groq_service.py's TPM saga for why a bloated prompt
# is a real, not theoretical, problem in this project specifically).
DEFAULT_EXAMPLE_LIMIT = 3


def retrieve_similar(db, report_type: str, tag_hint: str = None, limit: int = DEFAULT_EXAMPLE_LIMIT):
  """Returns up to `limit` ReferenceExample rows for this report_type,
  ranked by similarity to `tag_hint` when one is given.

  Deliberately NOT a vector/embedding search — see the module docstring.
  A hard filter on report_type plus simple string-similarity ranking on
  the short user-written `tag` is good enough at this library's expected
  scale (tens to low hundreds of examples) and needs zero new
  infrastructure. If the library grows into the thousands and this stops
  being precise enough, that's the trigger to revisit with real
  embeddings — not before.
  """
  candidates = (
      db.query(ReferenceExample)
      .filter(ReferenceExample.report_type == report_type)
      .order_by(ReferenceExample.created_at.desc())
      .all()
  )

  if not candidates:
    return []

  if not tag_hint or not tag_hint.strip():
    # No hint to rank against — e.g. the automatic batch analysis, which
    # runs before the user has said anything. Just take the most recent
    # N as a general "house style" reference.
    return candidates[:limit]

  scored = [
      (difflib.SequenceMatcher(None, tag_hint.lower(), c.tag.lower()).ratio(), c)
      for c in candidates
  ]
  scored.sort(key=lambda pair: pair[0], reverse=True)
  return [c for _, c in scored[:limit]]


def build_examples_block(examples: list) -> str:
  """Serializes retrieved examples into a compact text block meant to be
  prepended to a prompt. Returns "" if there's nothing to add (the common
  case for a brand-new library, or a report_type with no saved examples
  yet) so callers can unconditionally prepend the result without an
  extra "if examples:" check everywhere.

  Deliberately TEXT ONLY — this does NOT re-attach the past examples'
  actual PDF/images to the request. Re-sending N full past drawings
  alongside the current one on every single-page extraction call would
  multiply image-token cost by roughly N+1, for every provider, on every
  page of every future document — a cost explosion that contradicts the
  entire "cheap, infra-free" point of this feature. What's genuinely
  useful here (the component names/types/counts an engineer already
  confirmed were correct) fits in a few lines of text anyway. Attaching
  real past images as true multimodal few-shot examples would be a
  valid, more powerful, and deliberately separate (pricier) upgrade —
  not something to fold in by default here.
  """
  if not examples:
    return ""

  lines = [
      "REFERENCE EXAMPLES (past approved projects of the same system"
      " type, for guidance on typical component naming/types/patterns."
      " The current drawing may genuinely differ — don't force a match"
      " that isn't actually there):",
  ]
  for i, example in enumerate(examples, start=1):
    result = example.approved_result or {}
    components = result.get("components", [])
    component_summary = ", ".join(
        f"{c.get('name', '?')} x{c.get('count', '?')}" for c in components[:15]
    )
    lines.append(f"\nExample {i} ({example.tag}):")
    lines.append(f"  Components: {component_summary or '(none recorded)'}")

  return "\n".join(lines) + "\n\n---\n\n"


def save_example(
    db,
    user_id,
    report_type: str,
    tag: str,
    approved_result: dict,
    pdf_bytes: bytes = None,
    session_id: str = None,
) -> ReferenceExample:
  """Adds one approved project to the library. `approved_result` is the
  same shape as an AnalysisSession.analysis_result — the caller (see
  app/routers/library.py) currently just reuses whatever's already saved
  on that session verbatim, since there's no mechanism yet for a chat
  correction to write back into a structured result — see library.py's
  docstring for that caveat.
  """
  example = ReferenceExample(
      user_id=user_id,
      session_id=session_id,
      report_type=report_type,
      tag=tag.strip(),
      pdf_bytes=pdf_bytes,
      approved_result=approved_result,
  )
  db.add(example)
  db.commit()
  db.refresh(example)
  return example

"""Optional, user-requested readings for descriptors the lexicon does not read.

The LLM sees only descriptors Qloo actually returned and that no cue reads, with
their source (the brand's own entry or a related entity). It returns at most
three short readings in a fixed JSON shape. Every reading is checked here: the
descriptor must be one of the offered ones (copied exactly), lengths are
bounded, and numbers, percentages, ingredient names, and preference claims are
rejected. Sources are attached from MOTIF's own records, never from the LLM.

A reading is shown as "Suggested interpretation — not applied". Accepting one
records a user preference in the session and the brief. It never becomes Qloo
evidence and never changes motifs, axes, materials, or scores.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .brief import CLAIM_PATTERNS, MATERIAL_TERMS, NON_PALETTE_TERMS
from .narrative import unread_descriptors

MAX_SUGGESTIONS = 3
MAX_TEXT = 160
SOURCE_WORDS = {"own": "the brand's own Qloo entry", "brand": "related brands", "movie": "related films",
                "artist": "related music artists"}


def candidates(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = unread_descriptors(result, limit=10)
    return [{"descriptor": r["descriptor"], "from_brand_itself": r["own"],
             "source": ", ".join(SOURCE_WORDS[k] for k in r["source_kinds"]),
             "entities": r["entities"][:3], "common_in_reference_sample": r["common_in_sample"]} for r in rows]


def payload(brand: str, result: Dict[str, Any], intent: Optional[str]) -> Dict[str, Any]:
    out = {"brand": brand, "unread_descriptors": [{k: c[k] for k in ("descriptor", "from_brand_itself", "source")}
                                                  for c in candidates(result)]}
    if intent:
        out["user_intent"] = intent
    return out


def _problems(text: str) -> List[str]:
    low = text.lower()
    found = []
    if not text.strip():
        found.append("empty")
    if len(text) > MAX_TEXT:
        found.append("too long")
    if re.search(r"\d|%|percent", low):
        found.append("contains a number or percentage")
    terms = set(NON_PALETTE_TERMS) | {t for ts in MATERIAL_TERMS.values() for t in ts} | {"note", "notes", "accord"}
    for t in sorted(terms):
        if re.search(r"\b" + re.escape(t) + r"s?\b", low):
            found.append(f"names an ingredient or note ({t})")
            break
    for pattern in CLAIM_PATTERNS + (r"\b(will|would) like\b", r"\bloves?\b"):
        if re.search(pattern, low):
            found.append("makes a preference or proof claim")
            break
    return found


def validate(raw: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    """Return {'suggestions': [...], 'rejected': n}. Invalid items are dropped, never repaired."""
    offered = {c["descriptor"]: c for c in candidates(result)}
    items = raw.get("suggestions") if isinstance(raw, dict) else None
    if not isinstance(items, list):
        return {"suggestions": [], "rejected": 0, "error": "response did not have the expected shape"}
    kept, rejected, seen = [], 0, set()
    for item in items:
        if len(kept) >= MAX_SUGGESTIONS:
            rejected += 1
            continue
        if not isinstance(item, dict) or set(item) != {"descriptor", "reading", "design_question"}:
            rejected += 1
            continue
        d, reading, question = item["descriptor"], item["reading"], item["design_question"]
        if not all(isinstance(x, str) for x in (d, reading, question)) or d not in offered or d in seen:
            rejected += 1
            continue
        if _problems(reading) or _problems(question):
            rejected += 1
            continue
        seen.add(d)
        c = offered[d]
        kept.append({"id": f"s{len(kept) + 1}", "descriptor": d, "reading": reading.strip(), "design_question": question.strip(),
                     "from_brand_itself": c["from_brand_itself"], "source": c["source"], "entities": c["entities"],
                     "label": "Suggested interpretation — not applied", "decision": None})
    return {"suggestions": kept, "rejected": rejected}


def suggest(writer: Any, brand: str, result: Dict[str, Any], intent: Optional[str] = None) -> Dict[str, Any]:
    """One LLM call at most. Never raises: errors come back as a labelled status."""
    if writer is None or not hasattr(writer, "suggest"):
        return {"status": "unavailable", "message": "Suggestions need an LLM key on the server; the result is unaffected.",
                "suggestions": []}
    if not candidates(result):
        return {"status": "nothing_to_read", "message": "Every returned descriptor is already read by MOTIF's lexicon.",
                "suggestions": []}
    try:
        raw = writer.suggest(payload(brand, result, intent))
    except Exception as exc:  # API error, refusal, budget, bad JSON: no suggestions, labelled
        return {"status": "failed", "message": f"No suggestions this time ({type(exc).__name__}). The result is unaffected.",
                "suggestions": []}
    checked = validate(raw, result)
    status = "ok" if checked["suggestions"] else "failed"
    message = None if checked["suggestions"] else "No suggestion passed MOTIF's checks. The result is unaffected."
    return {"status": status, "message": message, "suggestions": checked["suggestions"], "rejected": checked["rejected"],
            "model": getattr(writer, "model", None), "usage": getattr(writer, "last_usage", None)}

"""Deterministic seed resolution from search candidates.

Rule (documented in docs/EVIDENCE_CONTRACT.md):

1. Candidates whose name equals the seed name after case/accent/whitespace
   folding are "exact". Nothing fuzzier is accepted.
2. No exact candidate                      -> unresolved (top candidates kept as near matches)
3. Exactly one exact candidate             -> resolved
4. Several exact, exactly one has a type
   listed in the seed's expected_types     -> resolved (others kept as alternatives)
5. Otherwise                               -> ambiguous (nothing selected)

A manual override in the manifest is accepted only if that entity ID was
actually returned by the search; it is never invented.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional

from .adapter import item_types


def fold_name(name: Optional[str]) -> str:
    if not isinstance(name, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.casefold().split())


def _summary(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "qloo_id": candidate.get("qloo_id"),
        "name": candidate.get("name"),
        "types": item_types(candidate),
        "evidence_id": candidate.get("evidence_id"),
        "pointer": candidate.get("pointer"),
    }


def resolve_seed(seed: Any, candidates: List[Dict[str, Any]], search_status: str) -> Dict[str, Any]:
    """`candidates` are search_candidate views (with qloo_id, name, types, pointer)."""
    result: Dict[str, Any] = {
        "status": None,
        "method": None,
        "qloo_id": None,
        "name": None,
        "types": [],
        "type_hint_match": None,
        "candidates_returned": len(candidates),
        "alternatives": [],
        "near_matches": [],
        "selected_evidence_id": None,
    }
    if search_status.startswith("skipped"):
        result.update(status="not_attempted", method=f"search not sent ({search_status})")
        return result
    if search_status not in ("ok", "ok_empty"):
        result.update(status="search_failed", method=f"search status {search_status}")
        return result

    def select(candidate: Dict[str, Any], status: str, method: str) -> Dict[str, Any]:
        types = item_types(candidate)
        result.update(
            status=status,
            method=method,
            qloo_id=candidate.get("qloo_id"),
            name=candidate.get("name"),
            types=types,
            type_hint_match=bool(set(types) & set(seed.expected_types)) if seed.expected_types else None,
            selected_evidence_id=candidate.get("evidence_id"),
        )
        return result

    if seed.override:
        wanted = seed.override.get("qloo_id") or seed.override.get("entity_id")
        chosen = [c for c in candidates if c.get("qloo_id") == wanted]
        if len(chosen) == 1:
            select(chosen[0], "resolved_manual", f"manual override: {seed.override.get('reason', 'no reason given')}")
            result["alternatives"] = [_summary(c) for c in candidates if c is not chosen[0]][:5]
            return result
        result.update(status="override_not_in_candidates", method="manual override ID was not among returned candidates")
        result["near_matches"] = [_summary(c) for c in candidates[:5]]
        return result

    target = fold_name(seed.input_name)
    exact = [c for c in candidates if c.get("qloo_id") and fold_name(c.get("name")) == target]

    if not exact:
        result.update(status="unresolved", method="no candidate name equals the seed name")
        result["near_matches"] = [_summary(c) for c in candidates[:5]]
        return result
    if len(exact) == 1:
        return select(exact[0], "resolved", "unique folded-name match")

    hinted = [c for c in exact if set(item_types(c)) & set(seed.expected_types)]
    if seed.expected_types and len(hinted) == 1:
        select(hinted[0], "resolved", "folded-name match narrowed by expected type")
        result["alternatives"] = [_summary(c) for c in exact if c is not hinted[0]]
        return result

    result.update(status="ambiguous", method=f"{len(exact)} candidates share the seed name; no unique expected-type match")
    result["alternatives"] = [_summary(c) for c in exact]
    return result


RESOLVED_STATUSES = frozenset({"resolved", "resolved_manual"})

"""Scent architecture: the continuous profile -> an olfactory structure for a perfumer.

Deterministic matching against the versioned library config/olfactory_directions.v1.json;
the LLM never chooses anything here. The target is the commitment vector of the resolved
dimensions (value x confidence; open dimensions are 0, so they constrain nothing). Each
direction's fit is its cosine similarity with that target. A direction that works against a
resolved dimension by more than a trace (target x cell <= -conflict_floor) is set aside; the
others fill opening, core, and drydown in that order, best fit first, each direction at most
once. A direction works with every resolved dimension whose sign its cell shares (every cell
in the library is a deliberate claim of at least 0.25; olfactory-1.1). A role with no eligible direction stays open to the perfumer. "Emphasize" and "avoid"
are given only where a supported (not tentative) dimension backs them.

Material references are examples of each chosen direction's class, generic name first, with a
trade name only where MOTIF read the supplier's page; they are not a formula and carry no dose.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .config import AXES

ROLES = ("opening", "core", "drydown")
STRONG_WORDS = ("supported", "firm")


def _cell(direction: Dict[str, Any], axis: str) -> float:
    c = direction["vector"].get(axis)
    return c["value"] if c else 0.0


def targets_of(axes: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    return {a: axes[a]["value"] * axes[a]["confidence"] for a in AXES if axes[a]["state"] == "resolved"}


def score_directions(axes: Dict[str, Dict[str, Any]], motif_scores: Dict[str, Dict[str, Any]],
                     vectors: Dict[str, Any], library: Dict[str, Any], lead_min: float) -> List[Dict[str, Any]]:
    m = library["matching"]
    t = targets_of(axes)
    tn = math.sqrt(sum(x * x for x in t.values()))
    imagery = {mo: set((vectors["motifs"].get(mo) or {}).get("imagery", [])) for mo, s in motif_scores.items()
               if s["score"] >= lead_min and not s["common_only"]}
    rows = []
    for d in library["directions"]:
        v = {a: _cell(d, a) for a in AXES}
        vn = math.sqrt(sum(x * x for x in v.values()))
        dot = sum(t.get(a, 0.0) * v[a] for a in AXES)
        fit = dot / (tn * vn) if tn and vn else 0.0
        against = sorted(a for a in t if t[a] * v[a] <= -m["conflict_floor"])
        toward = sorted(a for a in t if t[a] * v[a] > 0)  # olfactory-1.1: every cell is a deliberate claim
        echo = sorted(mo for mo, fams in imagery.items() if fams & set(d.get("odor_families", [])))
        bonus = m["imagery_bonus"] * max((motif_scores[mo]["score"] for mo in echo), default=0.0)
        rows.append({"id": d["id"], "label": d["label"], "roles": d["roles"], "fit": round(fit, 6),
                     "rank": round(fit + bonus, 6), "imagery_echo": echo, "works_with": toward, "works_against": against,
                     "eligible": fit >= m["min_fit"] and not against})
    rows.sort(key=lambda r: (-r["rank"], r["id"]))
    return rows


def architecture(axes: Dict[str, Dict[str, Any]], motif_scores: Dict[str, Dict[str, Any]], vectors: Dict[str, Any],
                 library: Dict[str, Any], lead_min: float, names: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """The scent architecture of one continuous result (see the module docstring)."""
    names = names or {}
    m = library["matching"]
    by_id = {d["id"]: d for d in library["directions"]}
    rows = score_directions(axes, motif_scores, vectors, library, lead_min)
    supported = {a for a in AXES if axes[a]["state"] == "resolved" and axes[a].get("confidence_word") in STRONG_WORDS}
    used, structure = set(), {}
    for role in ROLES:
        pick = next((r for r in rows if r["eligible"] and role in r["roles"] and r["id"] not in used), None)
        if pick:
            used.add(pick["id"])
        structure[role] = None if not pick else {
            "direction": pick["id"], "label": pick["label"], "fit": pick["fit"],
            "descriptors": by_id[pick["id"]]["descriptors"], "works_with": pick["works_with"],
            "imagery_echo": pick["imagery_echo"], "materials": by_id[pick["id"]]["materials"],
            "uncertainty": by_id[pick["id"]]["uncertainty"],
            "basis": "supported" if set(pick["works_with"]) & supported else "tentative"}
    emphasize = [{"direction": r["id"], "label": r["label"], "because": [a for a in r["works_with"] if a in supported]}
                 for r in rows if r["eligible"] and set(r["works_with"]) & supported][:m["max_emphasize"]]
    avoid_rows = sorted((r for r in rows if set(r["works_against"]) & supported), key=lambda r: (r["fit"], r["id"]))
    avoid = [{"direction": r["id"], "label": r["label"], "because": [a for a in r["works_against"] if a in supported]}
             for r in avoid_rows][:m["max_avoid"]]
    dims = []
    for a in AXES:
        v = axes[a]
        dims.append({"axis": a, "name": names.get(a, a), "state": v["state"],
                     "label": v.get("label") if v["state"] == "resolved" else None,
                     "confidence_word": v.get("confidence_word"), "evidence_basis": v.get("evidence_basis")})
    picks = [s for s in structure.values() if s]
    return {"library_version": library["library_version"], "status": "proposed" if picks else "open",
            "basis": None if not picks else "supported" if any(s["basis"] == "supported" for s in picks) else "tentative",
            "structure": structure, "dimensions": dims, "emphasize": emphasize, "avoid": avoid,
            "ranking": rows, "provenance_category": "motif_annotation",
            "note": "A creative structure for a perfumer, not a formula: no doses, no proportions, nothing smelled."}

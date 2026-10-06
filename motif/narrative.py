"""Plain-language readings of an engine result, shared by the web view, the brief, and the PDF.

Deterministic and descriptive only: nothing here changes motifs, strengths,
targets, or materials. Wording rules: related brands and films are "references
Qloo relates to" the brand; repetition across them is a pattern, not proof of an
aesthetic, and never a statement about an audience's taste.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import AXES

ROOT = Path(__file__).resolve().parent.parent
POLE_WORDS = {"light": "light", "dense": "dense", "raw": "raw-textured", "polished": "smooth-finished",
              "natural": "natural-feeling", "synthetic": "synthetic-feeling", "warm": "warm", "cool": "cool",
              "intimate": "close-wearing", "projecting": "diffusive", "sweet": "sweet", "dry": "dry"}
MOTIF_LABELS = {
    "restrained": "restraint", "precise": "precision", "natural": "naturalness", "opulent": "opulence",
    "intimate": "intimacy", "experimental": "experimentation", "provocative": "provocation", "heritage": "heritage",
    "industrial": "industrial character", "playful": "playfulness", "romantic": "romance", "melancholic": "melancholy",
}
AXIS_NAMES = {"warm_cool": "Temperature", "light_dense": "Weight", "raw_polished": "Texture",
              "natural_synthetic": "Impression", "intimate_projecting": "Projection", "sweet_dry": "Sweetness"}


@lru_cache(maxsize=1)
def reference_sample() -> Dict[str, Any]:
    path = ROOT / "config" / "reference_sample.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"common_descriptors": {}, "brands": []}


def is_common(descriptor: str) -> bool:
    return descriptor.strip().lower() in reference_sample()["common_descriptors"]


def _join(words: List[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def idea(name: str, result: Dict[str, Any]) -> str:
    """One sentence that states the direction; built only from targets and active motifs."""
    targets = [result["axes"][a]["value"] for a in AXES if result["axes"][a]["state"] == "target"]
    motifs = [MOTIF_LABELS.get(m, m) for m, i in sorted(result["motifs"].items()) if i["active"]
              and m not in result.get("unmapped_active_motifs", [])]
    if not targets:
        unmapped = [MOTIF_LABELS.get(m, m) for m in result.get("unmapped_active_motifs", [])]
        if unmapped:
            return f"{name} reads as {_join(unmapped)}, but MOTIF has no scent rule for that yet: the direction is an open question."
        return f"The descriptors Qloo returned for {name} do not yet support a scent direction."
    words = [POLE_WORDS.get(t, t) for t in targets]
    lead = f"A {_join(words)} scent" + (f", built on {_join(motifs)}." if motifs else ".")
    unmapped = [MOTIF_LABELS.get(m, m) for m in result.get("unmapped_active_motifs", [])]
    if unmapped:
        lead += f" {_join(unmapped).capitalize()} {'is' if len(unmapped) == 1 else 'are'} supported too, with no scent rule yet: an open question."
    return lead


def poss(name: str) -> str:
    return name + ("'" if name.endswith("s") else "'s")


def axis_basis(name: str, result: Dict[str, Any], axis: str) -> Optional[Dict[str, str]]:
    """Where a target comes from, in one honest sentence."""
    v = result["axes"][axis]
    if v["state"] != "target":
        return None
    kinds = set()
    for m in v["motifs"]:
        kinds.update(result["motifs"][m]["source_kinds"])
    own = "own" in kinds
    related = bool(kinds - {"own"})
    if own and related:
        return {"kind": "own_and_related",
                "text": f"From {poss(name)} own Qloo descriptors; the same motif also appears in references Qloo relates to {name}."}
    if own:
        return {"kind": "own_only", "text": f"From {poss(name)} own Qloo descriptors."}
    return {"kind": "related_only",
            "text": (f"Derived only from references Qloo relates to {name}, not from {poss(name)} own descriptors: "
                     "a creative suggestion, not a described trait of the brand.")}


def open_design_questions(name: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Supported motifs without a scent rule stay visible as open questions instead of being dropped."""
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    out = []
    for m in result.get("unmapped_active_motifs", []):
        info = result["motifs"][m]
        phrases = []
        for i in info["support_evidence_ids"]:
            if i in ev and ev[i]["tag_name"] not in phrases:
                phrases.append(ev[i]["tag_name"])
        label = MOTIF_LABELS.get(m, m)
        out.append({"motif": m, "label": label, "examples": phrases[:4],
                    "text": (f"Qloo descriptors point to {label} ({', '.join(phrases[:3])}). MOTIF has no scent rule for "
                             f"{label}, so it sets no direction: how should {label} be expressed in this scent?")})
    return out


def unread_descriptors(result: Dict[str, Any], limit: int = 12) -> List[Dict[str, Any]]:
    """Descriptors Qloo returned that no lexicon cue reads: own entry first, then repeated ones from references."""
    read = set()
    for info in result["motifs"].values():
        read.update(info["support_evidence_ids"])
        read.update(info["context_evidence_ids"])
        read.update(info.get("negated_evidence_ids", []))
        read.update(x["evidence_id"] for x in info.get("excluded_evidence", []))
    groups: Dict[str, Dict[str, Any]] = {}
    for e in result["evidence"]:
        tag = e["tag_name"].strip()
        if e["evidence_id"] in read or not tag or tag.lower() == "null":
            continue
        g = groups.setdefault(tag.lower(), {"descriptor": tag, "own": False, "entities": [], "source_kinds": []})
        if e["source_kind"] == "own":
            g["own"] = True
        if e["entity_name"] not in g["entities"]:
            g["entities"].append(e["entity_name"])
        if e["source_kind"] not in g["source_kinds"]:
            g["source_kinds"].append(e["source_kind"])
    rows = [g for g in groups.values() if g["own"] or len(g["entities"]) >= 2]
    for g in rows:
        g["common_in_sample"] = is_common(g["descriptor"])
    rows.sort(key=lambda g: (not g["own"], g["common_in_sample"], -len(g["entities"]), g["descriptor"].lower()))
    return rows[:limit]

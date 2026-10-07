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


STRENGTH_RANK = {"strong": 0, "moderate": 1, "weak": 2, "context_only": 3}
# Noun phrases for a direction named on its own ("MOTIF also proposes a light weight").
POLE_PHRASES = {"light": "a light weight", "dense": "a dense weight", "raw": "a raw texture",
                "polished": "a smooth-finished texture", "natural": "a natural-feeling impression",
                "synthetic": "a synthetic-feeling impression", "warm": "warmth", "cool": "coolness",
                "intimate": "close-wearing projection", "projecting": "diffusive projection", "sweet": "sweetness", "dry": "dryness"}


def _or(words: List[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " or " + words[-1]


def profile(name: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The cultural profile: active motifs ranked by the evidence that exists for them.

    Order: support in the brand's own Qloo entry first, then strength, then the number
    of source kinds, then the number of supporting descriptors. Each row says whether
    MOTIF translates the motif into a direction ("direction"), has no rule for it
    ("no_rule"), leaves its dimension open after a conflict ("open"), or the user chose the
    other pole on its dimension ("set_aside").
    """
    target_of, set_aside, split = {}, {}, {}
    for a in AXES:
        v = result["axes"][a]
        if v["state"] == "target":
            for m in v["motifs"]:
                target_of[m] = a
        for m in (v.get("user_choice") or {}).get("overrode_conflict_with", []):
            set_aside[m] = a  # the user chose the other pole on this axis
        for push in v.get("pushes", []) if v["state"] == "conflicted" else []:
            split[push["motif"]] = a  # the axis stays open: motifs point both ways
    unmapped = set(result.get("unmapped_active_motifs", []))
    rows = []
    for m, info in result["motifs"].items():
        if not info["active"]:
            continue
        axis = target_of.get(m) or set_aside.get(m) or split.get(m)
        state = ("direction" if m in target_of else "set_aside" if m in set_aside else "no_rule" if m in unmapped else "open")
        pole = result["axes"][axis]["value"] if state == "direction" else None
        rows.append({"motif": m, "label": MOTIF_LABELS.get(m, m), "own": "own" in info["source_kinds"],
                     "strength": info["strength"], "source_kinds": list(info["source_kinds"]),
                     "support_count": len(info["support_evidence_ids"]), "state": state,
                     "axis": axis, "pole": pole, "word": POLE_WORDS.get(pole) if pole else None})
    rows.sort(key=lambda r: (not r["own"], STRENGTH_RANK[r["strength"]], -len(r["source_kinds"]), -r["support_count"], r["label"]))
    return rows


def _so_far(name: str, result: Dict[str, Any], targets: List[str]) -> str:
    word = lambda a: POLE_WORDS.get(result["axes"][a]["value"], result["axes"][a]["value"])
    chosen = [a for a in targets if result["axes"][a].get("user_choice")]
    rel = [a for a in targets if a not in chosen and result["axes"][a].get("relations_only")]
    own = [a for a in targets if a not in chosen and a not in rel]
    parts = []
    if own:
        parts.append(_join([word(a) for a in own]) + " (from " + poss(name) + " own descriptors)")
    if chosen:
        parts.append(_join([word(a) for a in chosen]) + " (your choice)")
    if rel:
        parts.append(_join([word(a) for a in rel]) + (" (drawn only from references Qloo relates to " + name + ")" if parts
                                                       else ", drawn only from references Qloo relates to " + name))
    return "Proposed direction so far: " + " and ".join(parts) + "."


def headline(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """The result's lead: a status label, one title, and at most two short lines.

    The identity comes from motifs supported by the brand's own Qloo entry, ranked by
    evidence (see `profile`). A direction drawn only from references Qloo relates to
    the brand never leads the title; it is named in a line of its own. A leading motif
    MOTIF cannot translate stays in the title, and the next creative decision is named.
    """
    rows = profile(name, result)
    own = [r for r in rows if r["own"]]
    targets = [a for a in AXES if result["axes"][a]["state"] == "target"]
    rel_targets = [a for a in targets if result["axes"][a].get("relations_only")]
    composed = result["materials"]["status"] == "composed"
    lines: List[str] = []
    if own and own[0]["state"] == "direction":
        lead = [r for r in own if r["state"] == "direction"]
        title = (_join([r["label"] for r in lead]).capitalize() + ": a "
                 + _join(list(dict.fromkeys(r["word"] for r in lead))) + " scent.")
        rest = [r for r in own if r["state"] != "direction"]
        if rest:
            one = len(rest) == 1
            lines.append(_join([r["label"] for r in rest]).capitalize() + (" is" if one else " are") + " also in "
                         + poss(name) + " own descriptors; how to express " + ("it" if one else "them")
                         + " in scent is open to the perfumer.")
        if rel_targets:
            lines.append("MOTIF also proposes " + _join([POLE_PHRASES[result["axes"][a]["value"]] for a in rel_targets])
                         + ", drawn only from references Qloo relates to " + name + ".")
        if not composed and len(lines) < 2:
            lines.append("One supported direction is not enough for a composition; the other dimensions are open to the perfumer."
                         if result["outcome"] == "partial_direction" else
                         "No verified starting materials are proposed for this direction yet.")
        label = "Scent direction" if composed else "Partial direction"
    elif own:
        lead = []
        for r in own:
            if r["state"] == "direction":
                break
            lead.append(r)
        one = len(lead) == 1
        labels = [r["label"] for r in lead]
        title = "A profile led by " + _join(labels) + "."
        if all(r["state"] == "no_rule" for r in lead):
            lines.append("How to express " + _or(labels) + " in scent is open to the perfumer.")
        elif all(r["state"] == "set_aside" for r in lead):
            lines.append("You chose the other pole on " + _join(sorted({AXIS_NAMES[r["axis"]].lower() for r in lead}))
                         + ", so " + _join(labels) + " sets no direction here; how else to express "
                         + ("it" if one else "them") + " is open to the perfumer.")
        else:
            lines.append(_or(labels).capitalize() + (" sets" if one else " set") + " no direction here; how to express "
                         + ("it" if one else "them") + " is open to the perfumer.")
        lines.append(_so_far(name, result, targets) if targets else "No scent direction is proposed yet.")
        label = "Partial direction" if targets else "No direction yet"
    elif targets:
        title = "A " + _join([POLE_WORDS.get(result["axes"][a]["value"]) for a in targets]) + " direction from related references."
        lines.append(poss(name) + " own Qloo descriptors do not support a direction on their own; this one is drawn only "
                     "from references Qloo relates to the brand.")
        label = "Direction from related references"
    else:
        title = "Not enough repeated signal for a direction yet."
        rel = [r for r in rows if r["state"] == "no_rule"]
        if rel:
            lines.append("References Qloo relates to " + name + " point to " + _join([r["label"] for r in rel])
                         + "; how to express " + ("it" if len(rel) == 1 else "them") + " in scent is open to the perfumer.")
        elif result["outcome"] == "no_descriptive_data":
            lines.append("Qloo returned no descriptors MOTIF can read for " + name + ".")
        else:
            lines.append("Qloo returned descriptors for " + name + ", but none repeated enough to count.")
        label = "No direction yet"
    return {"label": label, "title": title, "lines": lines[:2], "provenance": "motif_annotation"}


def idea(name: str, result: Dict[str, Any]) -> str:
    """The headline title (kept for the brief JSON's `idea` field)."""
    return headline(name, result)["title"]


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
    chosen = (v.get("user_choice") or {}).get("overrode_conflict_with")
    if chosen:
        return {"kind": "user_choice",
                "text": "Chosen by you where motifs pointed both ways (set aside: "
                        + _join([MOTIF_LABELS.get(m, m) for m in chosen]) + ")."}
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
                    "text": f"Qloo descriptors point to {label} ({', '.join(phrases[:3])}); MOTIF has no scent rule for it yet."})
    return out


def unread_descriptors(result: Dict[str, Any], limit: int = 12) -> List[Dict[str, Any]]:
    """Descriptors Qloo returned that no lexicon cue reads: own entry first, then repeated ones from references."""
    read = {a["evidence_id"] for a in result["annotations"]}  # any lexicon match, whatever its role (both engines)
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

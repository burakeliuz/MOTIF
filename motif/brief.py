"""Brief JSON, template prose, and validation of LLM prose against the engine result.

The engine result decides everything structured. Prose (template or LLM) only
describes it. LLM prose is rejected when it names a material the engine did
not select, gives a percentage or a number that is not in the result, leaves
out an open axis, or makes a preference or proof claim.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .config import AXES

BRIEF_SCHEMA = "brief-0.2"
DISCLAIMER = ("A creative direction for a perfumer, not a formula: nothing has been smelled or balanced, there are no "
              "proportions or safety assessments, and nothing predicts who will like the scent. Related brands and films "
              "are references Qloo relates to the brand; a motif repeated there is a pattern, not proof of an aesthetic.")

AXIS_LABELS = {
    "warm_cool": "temperature (warm/cool)",
    "light_dense": "weight (light/dense)",
    "raw_polished": "texture (raw/polished)",
    "natural_synthetic": "natural/synthetic impression",
    "intimate_projecting": "projection (intimate/projecting)",
    "sweet_dry": "sweetness (sweet/dry)",
}
AXIS_WORDS = {
    "warm_cool": ("temperature",),
    "light_dense": ("weight",),
    "raw_polished": ("texture",),
    "natural_synthetic": ("natural/synthetic", "natural or synthetic", "naturalness"),
    "intimate_projecting": ("projection",),
    "sweet_dry": ("sweetness",),
}
# Words that name an ingredient; an LLM text may only use those of selected materials.
MATERIAL_TERMS = {
    "M01": ("hedione",), "M02": ("bergamot",), "M03": ("iso e super",), "M04": ("ambrox",),
    "M05": ("habanolide",), "M06": ("vetiver",), "M07": ("labdanum",), "M08": ("orris", "iris"),
}
EXTRA_ALLOWED = {"M05": ("musk",)}
NON_PALETTE_TERMS = ("sandalwood", "vanilla", "vanillin", "rose", "oud", "patchouli", "cedar", "cedarwood", "tonka",
                     "lavender", "neroli", "jasmine", "leather", "incense", "musk", "amber", "citrus", "oakmoss",
                     "tuberose", "ylang", "cardamom", "pepper", "saffron", "violet")
CLAIM_PATTERNS = (r"\bwill love\b", r"\bguarantee", r"\bproven\b", r"\bscientific", r"\bvalidated\b",
                  r"\bconsumers prefer\b", r"\baudiences? (will|would|prefers?|likes?|loves?|confirms?)\b",
                  r"\b(same|shared|its|their) audiences?\b")


def selected_ids(result: Dict[str, Any]) -> List[str]:
    return [m["material_id"] for m in result["materials"].get("selected", [])]


def open_axes(result: Dict[str, Any]) -> List[str]:
    return [a for a in AXES if result["axes"][a]["state"] != "target"]


PLAIN_AXIS = {"warm_cool": "temperature", "light_dense": "weight", "raw_polished": "texture",
              "natural_synthetic": "impression", "intimate_projecting": "projection", "sweet_dry": "sweetness"}
NOUN = {"warm": "warmth", "cool": "coolness", "light": "lightness", "dense": "density", "raw": "rawness",
        "polished": "polish", "natural": "a natural feel", "synthetic": "a synthetic feel", "intimate": "closeness",
        "projecting": "diffusion", "sweet": "sweetness", "dry": "dryness"}
MOTIF_WORD = {"restrained": "restraint", "precise": "precision", "natural": "naturalness", "opulent": "opulence",
              "intimate": "intimacy", "experimental": "experimentation", "provocative": "provocation", "heritage": "heritage",
              "industrial": "industrial character", "playful": "playfulness", "romantic": "romance", "melancholic": "melancholy"}


def _list(words: List[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def template_prose(seed_name: str, result: Dict[str, Any], intent: Optional[str] = None) -> str:
    """Plain-language brief written by a fixed template (no LLM). Rule codes and scores stay in the JSON."""
    axes = result["axes"]
    targets = [(a, axes[a]) for a in AXES if axes[a]["state"] == "target"]
    lines = [f"{seed_name}: a direction, not a formula."]
    if targets:
        parts = []
        for a, t in targets:
            why = " and ".join(MOTIF_WORD.get(m, m) for m in t["motifs"])
            note = f", only from references Qloo relates to {seed_name}, so a creative suggestion" if t.get("relations_only") else ""
            parts.append(f"a {t['value']} {PLAIN_AXIS[a]} (from {why}, {t['evidence_strength']} support{note})")
        lines.append("Aim for " + _list(parts) + ".")
    unmapped = result.get("unmapped_active_motifs") or []
    if unmapped:
        lines.append("Open design question: the descriptors also point to " + _list([MOTIF_WORD.get(m, m) for m in unmapped])
                     + ", which MOTIF has no scent rule for; how to express it is left to the perfumer.")
    mats = result["materials"]
    if mats["status"] == "composed":
        where = {"top": "at the top", "heart": "in the heart", "base": "at the base"}
        lines.append("Suggested starting materials: " + _list([f"{m['name']} {where[m['slot']]}" for m in mats["selected"]]) + ".")
        extras = [f"{m['name']} also brings {NOUN.get(u['pole'], u['pole'])}" for m in mats["selected"] for u in m["unrequested_properties"]]
        if extras:
            lines.append(_list(extras) + ": supplier-described properties on dimensions the evidence leaves open, kept as creative choices.")
        if mats.get("empty_slots"):
            lines.append("No verified material for: " + ", ".join(mats["empty_slots"]) + ".")
        if mats["verification_mode"] != "verified_only":
            lines.append("DESIGN PREVIEW: material properties are not verified against full supplier pages.")
    else:
        lines.append(f"No material composition: {result['outcome_meaning']}")
    open_list = [AXIS_LABELS[a] for a in open_axes(result)]
    if open_list:
        lines.append("Left open by the evidence: " + ", ".join(open_list) + ".")
    if intent:
        lines.append(f"Stated purpose (from the user, not evidence; it changes nothing above): {intent}")
    return " ".join(lines)


def validate_prose(text: str, result: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    low = text.lower()
    chosen = set(selected_ids(result))
    allowed_terms = {t for mid in chosen for t in MATERIAL_TERMS.get(mid, ()) + EXTRA_ALLOWED.get(mid, ())}
    forbidden = {t for mid, terms in MATERIAL_TERMS.items() if mid not in chosen for t in terms}
    forbidden |= set(NON_PALETTE_TERMS)
    forbidden -= allowed_terms
    for term in sorted(forbidden):
        if re.search(r"\b" + re.escape(term) + r"\b", low):
            problems.append(f"names an ingredient the engine did not select: {term!r}")
    if "%" in text or "percent" in low:
        problems.append("contains a percentage")
    # prose carries no scores; the only digits allowed are rule IDs such as "R3"
    stray = re.findall(r"(?<![Rr])\d+(?:\.\d+)?", text)
    if stray:
        problems.append(f"contains numbers (scores belong to the engine JSON, not the prose): {sorted(set(stray))}")
    for axis in open_axes(result):
        if not any(w in low for w in AXIS_WORDS[axis]):
            problems.append(f"does not say that {AXIS_LABELS[axis]} is open")
    for pattern in CLAIM_PATTERNS:
        for found in re.finditer(pattern, low):
            before = low[max(0, found.start() - 12):found.start()]
            if not re.search(r"\b(not|no|never|nor)\b", before):  # "not proven" is an honest statement
                problems.append(f"makes an unsupported claim ({found.group(0)!r})")
                break
    return problems


def build_brief(session: Dict[str, Any], result: Dict[str, Any], prose: Dict[str, Any],
                accepted_readings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    from .narrative import axis_basis, idea, open_design_questions  # local: narrative imports this module's constants
    name = (session.get("resolution") or {}).get("name") or "The brand"
    cited = set()
    for info in result["motifs"].values():
        cited.update(info["support_evidence_ids"])
        cited.update(info["context_evidence_ids"])
        cited.update(info["negated_evidence_ids"])
    return {
        "schema_version": BRIEF_SCHEMA,
        "data_label": session["data_label"],
        "versions": dict(result["versions"], engine=result["engine_version"], llm=prose.get("llm")),
        "seed": session["resolution"],
        "outcome": result["outcome"],
        "outcome_meaning": result["outcome_meaning"],
        "evidence": [e for e in result["evidence"] if e["evidence_id"] in cited],
        "motifs": result["motifs"],
        "unmapped_active_motifs": result["unmapped_active_motifs"],
        "axes": result["axes"],
        "materials": result["materials"],
        "idea": {"text": idea(name, result), "provenance": "motif_annotation"},
        "basis": {a: axis_basis(name, result, a) for a in AXES if result["axes"][a]["state"] == "target"},
        "open_questions": [f"{AXIS_LABELS[a]} is not decided by the evidence" for a in open_axes(result)],
        "open_design_questions": open_design_questions(name, result),
        "user_intent": ({"text": session["intent"], "provenance": "user_intent",
                         "effect": "recorded in the brief; it did not change motifs, axes, or materials"}
                        if session.get("intent") else None),
        "accepted_readings": [dict(r, provenance="user_preference",
                                   effect="accepted by the user; not Qloo evidence; no rule applied") for r in (accepted_readings or [])],
        "brief_text": {"author": prose["author"], "text": prose["text"], "note": prose.get("note")},
        "disclaimer": DISCLAIMER,
    }

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

BRIEF_SCHEMA = "brief-0.1"
DISCLAIMER = ("Creative direction for a perfumer, not a formula: no dosage, no safety or regulatory assessment, "
              "and no prediction that anyone will like the scent. Qloo relations describe aggregate cultural "
              "affinity, not shared aesthetics or individual preference.")

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
                  r"\bconsumers prefer\b", r"\baudience (will|prefers)\b")


def selected_ids(result: Dict[str, Any]) -> List[str]:
    return [m["material_id"] for m in result["materials"].get("selected", [])]


def open_axes(result: Dict[str, Any]) -> List[str]:
    return [a for a in AXES if result["axes"][a]["state"] != "target"]


def template_prose(seed_name: str, result: Dict[str, Any]) -> str:
    axes = result["axes"]
    targets = [(a, axes[a]) for a in AXES if axes[a]["state"] == "target"]
    lines = [f"{seed_name}: direction, not formula."]
    if targets:
        parts = []
        for a, t in targets:
            note = " (from Qloo relations only)" if t.get("relations_only") else ""
            parts.append(f"{AXIS_LABELS[a]} toward {t['value']}, from the motif {', '.join(t['motifs'])} "
                         f"[{t['evidence_strength']} evidence; rule {', '.join(t['rule_ids'])} is a draft hypothesis]{note}")
        lines.append("Aim for: " + "; ".join(parts) + ".")
    unmapped = result.get("unmapped_active_motifs") or []
    if unmapped:
        lines.append("Also supported but without a translation rule (shapes nothing): " + ", ".join(unmapped) + ".")
    mats = result["materials"]
    if mats["status"] == "composed":
        picks = [f"{m['name']} ({m['slot']})" for m in mats["selected"]]
        lines.append("Proposed starting materials: " + ", ".join(picks) + ".")
        extras = [f"{m['name']} brings {u['pole']} ({AXIS_LABELS[u['axis']]})"
                  for m in mats["selected"] for u in m["unrequested_properties"]]
        if extras:
            lines.append("Creative choices, not evidence: " + "; ".join(extras) + ".")
        if mats.get("empty_slots"):
            lines.append("Open slots: " + ", ".join(mats["empty_slots"]) + " (no fitting palette material).")
        if mats["verification_mode"] != "verified_only":
            lines.append("DESIGN PREVIEW: material properties are not verified against full supplier pages.")
    else:
        lines.append(f"No material composition: {result['outcome_meaning']}")
    open_list = [AXIS_LABELS[a] for a in open_axes(result)]
    if open_list:
        lines.append("Left open by the evidence: " + ", ".join(open_list) + ".")
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


def build_brief(session: Dict[str, Any], result: Dict[str, Any], prose: Dict[str, Any]) -> Dict[str, Any]:
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
        "open_questions": [f"{AXIS_LABELS[a]} is not decided by the evidence" for a in open_axes(result)],
        "brief_text": {"author": prose["author"], "text": prose["text"], "note": prose.get("note")},
        "disclaimer": DISCLAIMER,
    }

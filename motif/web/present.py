"""View model for the web UI: turns a session and its engine result into plain, labelled JSON.

Nothing here decides anything: every value comes from the engine result, the
session trace, or the versioned config. It only adds human labels and
explanations so the browser stays a thin renderer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..brief import AXIS_LABELS, open_axes
from ..config import AXES
from ..narrative import axis_basis, idea, is_common, open_design_questions, unread_descriptors

POLES = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
         "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"),
         "sweet_dry": ("sweet", "dry")}
AXIS_NAMES = {"warm_cool": "Temperature", "light_dense": "Weight", "raw_polished": "Texture",
              "natural_synthetic": "Impression", "intimate_projecting": "Projection", "sweet_dry": "Sweetness"}
SOURCE_LABELS = {"own": "Brand's own Qloo description", "brand": "Related brands", "movie": "Related films",
                 "artist": "Related music artists"}
STRENGTH_WORDS = {"strong": "Strong support", "moderate": "Moderate support", "weak": "Seen, not enough to count",
                  "context_only": "Only very common descriptors"}
TYPE_LABELS = {"urn:entity:brand": "Brand", "urn:entity:place": "Store or venue", "urn:entity:person": "Person",
               "urn:entity:book": "Book", "urn:entity:movie": "Film", "urn:entity:tv_show": "TV show",
               "urn:entity:artist": "Music artist", "urn:entity:locality": "Place name", "urn:entity:author": "Author"}
RELATIONS_ONLY_TEXT = ("Derived only from references Qloo relates to {name}, not from the brand's own descriptors: "
                       "a creative suggestion, not a described trait of the brand.")
# Plain-language copy for each palette material, written only from the supplier's own words
# quoted in config/material_palette.json (presentation, not evidence).
MATERIAL_PLAIN = {
    "M01": {"what": "a transparent, jasmine-like molecule", "scent": "transparent floral with citrus freshness"},
    "M02": {"what": "a cold-pressed citrus oil", "scent": "bright, sparkling citrus"},
    "M03": {"what": "a woody molecule (properties not verified)", "scent": "not verified"},
    "M04": {"what": "an ambery, woody molecule", "scent": "powerful ambery, musky-woody"},
    "M05": {"what": "a musk molecule", "scent": "elegant musk with a slightly woody undertone"},
    "M06": {"what": "a natural essential oil", "scent": "dry and woody, earthy and smoky"},
    "M07": {"what": "a natural absolute", "scent": "warm, leathery, woody and ambery"},
    "M08": {"what": "a natural orris (iris) extract", "scent": "earthy, with woody facets"},
}
OUTCOME_COPY = {
    "composed": ("A scent direction with verified starting materials.", None),
    "no_verified_materials": ("A scent direction, but no verified palette material fits it yet.",
                              "MOTIF only proposes materials whose properties were checked against the supplier's own pages."),
    "insufficient_eligible_materials": ("A scent direction, but too few verified materials fit it for a composition.", None),
    "partial_direction": ("Only one sensory direction is supported, so no composition is proposed.",
                          "MOTIF needs at least two supported directions before it suggests materials (a design threshold)."),
    "no_translation_rule": ("Qloo describes this brand, but MOTIF has no scent rule for what it found.",
                            "The supported motifs are listed below; MOTIF does not invent a translation for them."),
    "insufficient_evidence": ("Qloo returned descriptions, but none reached MOTIF's threshold.",
                              "Weak signals are listed below; they are not used for scent decisions."),
    "no_descriptive_data": ("Qloo returned no descriptors MOTIF can read for this brand.", None),
    "conflicted": ("The evidence points two ways on one dimension.", "Choose a direction or leave it open."),
}
MATERIAL_STATUS_COPY = {
    "composed": "Proposed starting materials. Each one matches a direction on a property checked against the supplier's own page.",
    "gated_insufficient_axes": ("No composition: MOTIF needs at least two supported directions before it suggests materials "
                                "(a design threshold). Verified materials that fit the one supported direction are listed for reference only."),
    "no_verified_materials": "No verified palette material fits these directions, so none is suggested.",
    "insufficient_eligible_materials": "Fewer than two verified materials fit these directions, so no composition is proposed.",
    "no_targets": "No direction is supported by the evidence, so no materials are suggested.",
}
MOTIF_NOTES = {
    "restrained": "Restraint", "precise": "Precision", "natural": "Naturalness", "opulent": "Opulence",
    "intimate": "Intimacy", "experimental": "Experimentation", "provocative": "Provocation", "heritage": "Heritage",
    "industrial": "Industrial character", "playful": "Playfulness", "romantic": "Romance", "melancholic": "Melancholy",
}


def candidate_view(c: Dict[str, Any], requested: str) -> Dict[str, Any]:
    types = c.get("types") or []
    wanted = {"brand": "urn:entity:brand"}.get(requested)
    selectable = (wanted in types) if wanted else True
    return {"qloo_id": c["qloo_id"], "name": c["name"], "type_label": ", ".join(TYPE_LABELS.get(t, t) for t in types) or "Unknown type",
            "detail": c.get("disambiguation") or "", "exact_name": bool(c.get("name_matches_input", True)),
            "selectable": selectable,
            "why_not": None if selectable else "MOTIF researches brands; this result is a different kind of entity."}


def _axis_words(text: Optional[str]) -> Optional[str]:
    if not text:
        return text
    for key, name in AXIS_NAMES.items():
        text = text.replace(key, name)
    return text


def evidence_view(e: Dict[str, Any], annotation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    own = e["source_kind"] == "own"
    return {"id": e["evidence_id"], "source": SOURCE_LABELS[e["source_kind"]], "source_kind": e["source_kind"],
            "common_in_sample": is_common(e["tag_name"]),
            "entity": e["entity_name"], "entity_rank": e["entity_rank"],
            "entity_role": ("the brand itself" if own else f"{SOURCE_LABELS[e['source_kind']].lower()}, result {e['entity_rank']}"),
            "tag": e["tag_name"], "tag_type": e["tag_type"],
            "request_id": e["request_id"], "request_path": (e.get("request") or {}).get("path"),
            "request_params": (e.get("request") or {}).get("params"), "fetched_at": e.get("fetched_at"),
            "json_pointer": e["json_pointer"], "provenance": e.get("provenance_category", "qloo_observation"),
            "cue": annotation.get("cue_id") if annotation else None,
            "excluded_reason": annotation.get("reason") if annotation else None}


def result_view(name: str, result: Dict[str, Any], rules: Dict[str, Any], palette: Dict[str, Any]) -> Dict[str, Any]:
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    ann = {}
    for a in result["annotations"]:
        ann.setdefault((a["motif"], a["evidence_id"]), a)
    rule_by_motif = {r["motif"]: r for r in rules["rules"]}
    axes = []
    for axis in AXES:
        v = result["axes"][axis]
        row = {"key": axis, "name": AXIS_NAMES[axis], "poles": POLES[axis], "state": v["state"], "value": v["value"]}
        if v["state"] == "target":
            row.update(basis=axis_basis(name, result, axis))
            row.update(rules=v["rule_ids"], motifs=v["motifs"], strength=v["evidence_strength"],
                       strength_label=STRENGTH_WORDS[v["evidence_strength"]], rule_confidence="Draft creative rule",
                       relations_only=bool(v.get("relations_only")),
                       relations_only_text=RELATIONS_ONLY_TEXT.format(name=name) if v.get("relations_only") else None)
        elif v["state"] == "conflicted":
            row.update(pushes=v["pushes"])
        else:
            row["note"] = "Not decided by the evidence"
        axes.append(row)
    motifs = []
    for m, info in sorted(result["motifs"].items(), key=lambda kv: (["strong", "moderate", "weak", "context_only"].index(kv[1]["strength"]), kv[0])):
        rule = rule_by_motif.get(m)
        motifs.append({
            "motif": m, "label": MOTIF_NOTES.get(m, m.title()), "strength": info["strength"],
            "strength_label": STRENGTH_WORDS[info["strength"]], "active": info["active"],
            "sources": [SOURCE_LABELS[k] for k in info["source_kinds"]],
            "relations_only": info["relations_only"],
            "rule": ({"id": rule["rule_id"], "text": f"{AXIS_NAMES[rule['axis']]} toward {rule['toward']}",
                      "rationale": rule["rationale"]} if rule else None),
            "evidence": [evidence_view(ev[i], ann.get((m, i))) for i in info["support_evidence_ids"] if i in ev],
            "context": [evidence_view(ev[i], ann.get((m, i))) for i in info["context_evidence_ids"] if i in ev],
            "excluded": [evidence_view(ev[x["evidence_id"]], ann.get((m, x["evidence_id"])))
                         for x in info.get("excluded_evidence", []) if x["evidence_id"] in ev],
        })
    by_id = {m["material_id"]: m for m in palette["materials"]}
    mats = result["materials"]

    def material_view(row: Dict[str, Any]) -> Dict[str, Any]:
        src = by_id[row["material_id"]]
        checks = src.get("property_verification", {})
        targets = {a for a in AXES if result["axes"][a]["state"] == "target"}
        props = [{"axis": AXIS_NAMES[a], "pole": p, "requested": a in targets,
                  "supplier_text": (checks.get(a) or {}).get("supporting_text"),
                  "interpretation": (checks.get(a) or {}).get("motif_interpretation"),
                  "source_url": (checks.get(a) or {}).get("source_url")}
                 for a, p in sorted(row.get("usable_profile", {}).items(), key=lambda x: AXES.index(x[0]))]
        plain = MATERIAL_PLAIN.get(row["material_id"], {})
        return {"id": row["material_id"], "name": row["name"], "slot": row.get("slot"), "score": row.get("score"),
                "kind": src["kind"], "supplier": src.get("supplier"), "plain": plain.get("what"), "scent": plain.get("scent"),
                "props": props, "supplier_short": (src.get("supplier") or "").split(" (")[0],
                "matches": [{"axis": AXIS_NAMES[a], "pole": row["usable_profile"][a],
                             "supplier_text": (checks.get(a) or {}).get("supporting_text"),
                             "interpretation": (checks.get(a) or {}).get("motif_interpretation"),
                             "source_url": (checks.get(a) or {}).get("source_url"),
                             "accessed": (checks.get(a) or {}).get("accessed")} for a in row.get("matches", [])],
                "creative_choices": [{"axis": AXIS_NAMES[u["axis"]], "pole": u["pole"],
                                      "supplier_text": (checks.get(u["axis"]) or {}).get("supporting_text")}
                                     for u in row.get("unrequested_properties", [])],
                "reason": _axis_words(row.get("reason"))}
    return {
        "outcome": result["outcome"],
        "idea": idea(name, result),
        "design_questions": open_design_questions(name, result),
        "unread": unread_descriptors(result, limit=8),
        "sample": {"brands": 7, "note": "Common in MOTIF's seven-brand reference sample; indicative only."},
        "headline": OUTCOME_COPY[result["outcome"]][0], "headline_note": OUTCOME_COPY[result["outcome"]][1],
        "direction": [{"axis": AXIS_NAMES[a], "value": result["axes"][a]["value"]} for a in AXES if result["axes"][a]["state"] == "target"],
        "open": [AXIS_NAMES[a] for a in open_axes(result)],
        "axes": axes, "motifs": motifs,
        "materials": {"status": mats["status"], "verification_mode": mats["verification_mode"],
                      "status_text": MATERIAL_STATUS_COPY.get(mats["status"], mats["status"]),
                      "selected": [material_view(m) for m in mats.get("selected", [])],
                      "candidates": [material_view(m) for m in mats.get("ranked", [])] if mats["status"] != "composed" else [],
                      "excluded": [material_view(m) for m in mats.get("excluded", [])],
                      "empty_slots": mats.get("empty_slots", []), "gate": mats.get("gate")},
        "unmapped_active": [MOTIF_NOTES.get(m, m) for m in result["unmapped_active_motifs"]],
        "versions": dict(result["versions"], engine=result["engine_version"]),
    }


def axis_labels() -> Dict[str, str]:
    return dict(AXIS_LABELS)

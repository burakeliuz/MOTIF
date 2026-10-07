"""View model for the web UI: turns a session and its engine result into plain, labelled JSON.

Nothing here decides anything: every value comes from the engine result, the
session trace, or the versioned config. It only adds human labels and
explanations so the browser stays a thin renderer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..brief import AXIS_LABELS, open_axes
from ..config import AXES
from ..narrative import (POLE_WORDS, axis_basis, headline, is_common, open_design_questions, poss, profile,
                         unread_descriptors)

POLES = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
         "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"),
         "sweet_dry": ("sweet", "dry")}
AXIS_NAMES = {"warm_cool": "Temperature", "light_dense": "Weight", "raw_polished": "Texture",
              "natural_synthetic": "Impression", "intimate_projecting": "Projection", "sweet_dry": "Sweetness"}
SOURCE_LABELS = {"own": "Brand's own Qloo description", "brand": "Related brands", "movie": "Related films",
                 "artist": "Related music artists"}
SOURCE_SHORT = {"own": "own entry", "brand": "related brands", "movie": "related films", "artist": "related artists"}
STRENGTH_WORDS = {"strong": "Strong support", "moderate": "Moderate support", "weak": "Seen, not enough to count",
                  "context_only": "Only very common descriptors"}
TYPE_LABELS = {"urn:entity:brand": "Brand", "urn:entity:place": "Store or venue", "urn:entity:person": "Person",
               "urn:entity:book": "Book", "urn:entity:movie": "Film", "urn:entity:tv_show": "TV show",
               "urn:entity:artist": "Music artist", "urn:entity:locality": "Place name", "urn:entity:author": "Author"}
RELATIONS_ONLY_TEXT = ("Derived only from references Qloo relates to {name}, not from the brand's own descriptors: "
                       "a creative suggestion, not a described trait of the brand.")
# Plain-language copy for each palette material, written only from the supplier's own words
# quoted in config/material_palette.json (presentation, not evidence). `scent` is the short label
# shown next to the name on a strip.
MATERIAL_PLAIN = {
    "M01": {"what": "a transparent, jasmine-like molecule", "scent": "transparent floral"},
    "M02": {"what": "a cold-pressed citrus oil", "scent": "bright citrus"},
    "M03": {"what": "a woody molecule (properties not verified)", "scent": "not verified"},
    "M04": {"what": "an ambery, woody molecule", "scent": "ambery, woody"},
    "M05": {"what": "a musk molecule", "scent": "musk"},
    "M06": {"what": "a natural essential oil", "scent": "dry, woody, earthy"},
    "M07": {"what": "a natural absolute", "scent": "warm, ambery"},
    "M08": {"what": "a natural orris (iris) extract", "scent": "earthy, powdery"},
}
SUPPLIER_NAMES = {"www.firmenich.com": "dsm-firmenich", "www.givaudan.com": "Givaudan", "www.iff.com": "IFF"}
QLOO_PATHS = {"/search": "search", "/entities": "the brand's own entry", "/v2/insights": "related references"}
OUTCOME_COPY = {
    "composed": ("A scent direction with verified starting materials.", None),
    "no_verified_materials": ("A scent direction, but no verified palette material fits it yet.",
                              "MOTIF only proposes materials whose properties were checked against the supplier's own pages."),
    "insufficient_eligible_materials": ("A scent direction, but too few verified materials fit it for a composition.", None),
    "partial_direction": ("Only one sensory direction is supported, so no composition is proposed.",
                          "MOTIF needs at least two supported directions before it suggests materials (a design threshold)."),
    "no_translation_rule": ("Qloo describes this brand; how to express the motifs it supports is open to the perfumer.",
                            "The supported motifs are listed below; MOTIF does not invent a translation for them."),
    "insufficient_evidence": ("Qloo returned descriptions, but none reached MOTIF's threshold.",
                              "Weak signals are listed below; they are not used for scent decisions."),
    "no_descriptive_data": ("Qloo returned no descriptors MOTIF can read for this brand.", None),
    "conflicted": ("The evidence points two ways on one dimension.", "Choose a direction or leave it open."),
}
MATERIAL_STATUS_COPY = {
    "composed": "Suggested starting materials. Each matches a direction on a property verified on the supplier's own page.",
    "gated_insufficient_axes": "No composition: one supported direction is not enough for a material proposal.",
    "no_verified_materials": "No verified palette material fits these directions, so none is suggested.",
    "insufficient_eligible_materials": "Fewer than two verified materials fit these directions, so no composition is proposed.",
    "no_targets": "No direction is supported, so no materials are suggested.",
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
    targets = [a for a in AXES if result["axes"][a]["state"] == "target"]

    def material_view(row: Dict[str, Any]) -> Dict[str, Any]:
        src = by_id[row["material_id"]]
        checks = src.get("property_verification", {})
        props = [{"axis": AXIS_NAMES[a], "pole": p, "word": POLE_WORDS.get(p, p), "requested": a in targets,
                  "supplier_text": (checks.get(a) or {}).get("supporting_text"),
                  "interpretation": (checks.get(a) or {}).get("motif_interpretation"),
                  "source_url": (checks.get(a) or {}).get("source_url")}
                 for a, p in sorted(row.get("usable_profile", {}).items(), key=lambda x: AXES.index(x[0]))]
        plain = MATERIAL_PLAIN.get(row["material_id"], {})
        urls = [x["source_url"] for x in props if x["source_url"]]
        accessed = sorted({(checks.get(a) or {}).get("accessed") for a in row.get("usable_profile", {})} - {None})
        return {"id": row["material_id"], "name": row["name"], "slot": row.get("slot"), "score": row.get("score"),
                "kind": src["kind"], "supplier": src.get("supplier"), "plain": plain.get("what"), "scent": plain.get("scent"),
                "props": props, "supplier_short": (src.get("supplier") or "").split(" (")[0],
                "fits": [f"{AXIS_NAMES[a]} → {POLE_WORDS.get(row['usable_profile'][a], row['usable_profile'][a])}"
                         for a in row.get("matches", [])],
                "source": ({"supplier": _supplier(urls[0]), "url": urls[0], "document": (src.get("source") or {}).get("document"),
                            "accessed": accessed[-1] if accessed else None} if urls else None),
                "matches": [{"axis": AXIS_NAMES[a], "pole": row["usable_profile"][a],
                             "supplier_text": (checks.get(a) or {}).get("supporting_text"),
                             "interpretation": (checks.get(a) or {}).get("motif_interpretation"),
                             "source_url": (checks.get(a) or {}).get("source_url"),
                             "accessed": (checks.get(a) or {}).get("accessed")} for a in row.get("matches", [])],
                "creative_choices": [{"axis": AXIS_NAMES[u["axis"]], "pole": u["pole"],
                                      "supplier_text": (checks.get(u["axis"]) or {}).get("supporting_text")}
                                     for u in row.get("unrequested_properties", [])],
                "reason": _axis_words(row.get("reason"))}

    selected = [material_view(m) for m in mats.get("selected", [])]
    reference = None
    if mats["status"] != "composed" and mats.get("ranked"):
        reference = {"note": "For reference only, not a composition: verified materials that fit "
                             + ("the supported direction." if len(targets) == 1 else "the supported directions."),
                     "items": [material_view(m) for m in mats["ranked"]]}
    status_text = MATERIAL_STATUS_COPY.get(mats["status"], mats["status"])
    if mats["status"] == "gated_insufficient_axes" and not reference:
        status_text += " No verified material fits the supported direction either."
    shown = selected or (reference["items"] if reference else [])
    head = headline(name, result)
    return {
        "outcome": result["outcome"],
        "headline": head,
        "idea": head["title"],
        "profile": profile_view(name, result, ev, ann, rules),
        "direction": [{"key": a, "axis": AXIS_NAMES[a], "value": result["axes"][a]["value"],
                       "word": POLE_WORDS.get(result["axes"][a]["value"]),
                       "relations_only": bool(result["axes"][a].get("relations_only")),
                       "basis": axis_basis(name, result, a),
                       "motifs": [MOTIF_NOTES.get(m, m) for m in result["axes"][a]["motifs"]]} for a in targets],
        "still_open": [{"key": a, "axis": AXIS_NAMES[a], "poles": POLES[a], "state": result["axes"][a]["state"]}
                       for a in open_axes(result)],
        "design_questions": open_design_questions(name, result),
        "unread": unread_descriptors(result, limit=8),
        "sample": {"brands": 7, "note": "Common in MOTIF's seven-brand reference sample; indicative only."},
        "outcome_text": OUTCOME_COPY[result["outcome"]][0],
        "open": [AXIS_NAMES[a] for a in open_axes(result)],
        "axes": axes, "motifs": motifs,
        "materials": {"status": mats["status"], "verification_mode": mats["verification_mode"],
                      "status_text": status_text, "selected": selected, "reference": reference,
                      "excluded": [material_view(m) for m in mats.get("excluded", [])],
                      "empty_slots": mats.get("empty_slots", []), "gate": mats.get("gate")},
        "sources": sources_view(result, shown),
        "unmapped_active": [MOTIF_NOTES.get(m, m) for m in result["unmapped_active_motifs"]],
        "versions": dict(result["versions"], engine=result["engine_version"]),
    }


def _supplier(url: Optional[str]) -> Optional[str]:
    host = urlparse(url).netloc if url else ""
    return SUPPLIER_NAMES.get(host, host) or None


MOTIF_BASIS = {
    "own_and_related": "In {poss} own Qloo descriptors and in references Qloo relates to {name}.",
    "own_only": "In {poss} own Qloo descriptors.",
    "related_only": "Only in references Qloo relates to {name}, not in {poss} own descriptors.",
}


def profile_view(name: str, result: Dict[str, Any], ev: Dict[str, Any], ann: Dict[Any, Any],
                 rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The cultural profile, ranked as in `narrative.profile`, with each motif's examples and translation."""
    rule_by_motif = {r["motif"]: r for r in rules["rules"]}
    rows = []
    for row in profile(name, result):
        info = result["motifs"][row["motif"]]
        kinds = set(info["source_kinds"])
        basis = "own_and_related" if row["own"] and kinds - {"own"} else "own_only" if row["own"] else "related_only"
        picks, seen = [], set()
        for i in sorted(info["support_evidence_ids"], key=lambda i: (ev[i]["source_kind"] != "own", i) if i in ev else (True, i)):
            if i in ev and ev[i]["tag_name"].lower() not in seen:
                seen.add(ev[i]["tag_name"].lower())
                picks.append(evidence_view(ev[i], ann.get((row["motif"], i))))
        rule = rule_by_motif.get(row["motif"])
        if row["state"] == "direction":
            translation = f"Translated as {AXIS_NAMES[row['axis']].lower()} → {row['word']}."
        elif row["state"] == "no_rule":
            translation = "Not translated into a scent dimension: open to the perfumer."
        elif row["state"] == "set_aside":
            translation = f"You chose the other pole on {AXIS_NAMES[row['axis']].lower()}, so it sets no direction here."
        else:
            translation = f"{AXIS_NAMES[row['axis']]} stays open: motifs point both ways."
        rows.append({"motif": row["motif"], "label": MOTIF_NOTES.get(row["motif"], row["motif"]), "own": row["own"],
                     "strength": row["strength"], "strength_label": STRENGTH_WORDS[row["strength"]],
                     "sources": [SOURCE_LABELS[k] for k in info["source_kinds"]],
                     "source_short": [SOURCE_SHORT[k] for k in info["source_kinds"]], "state": row["state"],
                     "axis": AXIS_NAMES[row["axis"]] if row["axis"] else None, "word": row["word"],
                     "rule_id": rule["rule_id"] if rule and row["state"] == "direction" else None,
                     "basis": {"kind": basis, "text": MOTIF_BASIS[basis].format(poss=poss(name), name=name)},
                     "translation": translation, "examples": picks[:4]})
    return rows


def sources_view(result: Dict[str, Any], materials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The sources behind a result, shared by the web page and the printed brief.

    Qloo is cited by MOTIF's request log IDs, request paths, and fetch dates (no page URL
    exists for an API response); suppliers by the page each verified property was read on.
    """
    requests: Dict[str, Dict[str, Any]] = {}
    for e in result["evidence"]:
        rid = e.get("request_id")
        if rid and rid not in requests:
            req = e.get("request") or {}
            requests[rid] = {"request_id": rid, "path": req.get("path"), "what": SOURCE_LABELS[e["source_kind"]],
                             "fetched_at": e.get("fetched_at")}
    dates = sorted({(r["fetched_at"] or "")[:10] for r in requests.values()} - {""})
    suppliers, seen = [], set()
    for m in materials:
        src = m.get("source")
        if src and (src["url"], m["name"]) not in seen:
            seen.add((src["url"], m["name"]))
            suppliers.append(dict(src, material=m["name"]))
    return {"qloo": {"api": "Qloo Hackathon API", "requests": sorted(requests.values(), key=lambda r: r["request_id"]),
                     "dates": dates},
            "suppliers": suppliers}


def axis_labels() -> Dict[str, str]:
    return dict(AXIS_LABELS)


# ---------- continuous engine ----------

CONTINUOUS_OUTCOME_COPY = {
    "direction": "A scent direction from the brand's weighted motifs.",
    "open_direction": "Motifs are supported, but every dimension is open to the perfumer.",
    "insufficient_evidence": "Qloo returned descriptors, but none repeated enough to lead a direction.",
    "no_descriptive_data": "Qloo returned no descriptors MOTIF can read for this brand.",
}
ROLE_NAMES = {"opening": "Opening", "core": "Core", "drydown": "Drydown"}
DIRECTION_SOURCE = {"IFRA19": "IFRA Fragrance Ingredient Glossary (2019)", "PALETTE": "supplier page"}


def _basis_text(name: str, own: bool, related: bool) -> str:
    if own and related:
        return f"In {poss(name)} own Qloo descriptors and in references Qloo relates to {name}."
    if own:
        return f"In {poss(name)} own Qloo descriptors."
    return f"Only in references Qloo relates to {name}, not in {poss(name)} own descriptors."


def continuous_view(name: str, result: Dict[str, Any], library: Dict[str, Any]) -> Dict[str, Any]:
    """View model of a continuous engine result for the web page and the printed brief."""
    from .. import story  # local: story imports the engine
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    ann = {}
    for a in result["annotations"]:
        ann.setdefault((a["motif"], a["evidence_id"]), a)
    axes = result["axes"]
    rows = story.profile(name, result)

    def examples(motif: str, n: int = 4) -> List[Dict[str, Any]]:
        return [evidence_view(ev[e["evidence_id"]], ann.get((motif, e["evidence_id"]))) for e in story._evidence_of(result, motif)[:n]]

    def translation(r: Dict[str, Any]) -> str:
        if r["moves"]:
            return "Moves " + story._join([m["name"].lower() + " toward " + m["word"] for m in r["moves"]]) + "."
        if r["pulls_open"]:
            text = story._join([n.lower() for n in r["pulls_open"]])
            return text[0].upper() + text[1:] + (" stays" if len(r["pulls_open"]) == 1 else " stay") + " open: motifs pull both ways."
        cells = (result["motif_scores"].get(r["motif"]) or {})
        return "No sensory claim: open to the perfumer." if cells else ""

    profile_rows = []
    for r in rows:
        kinds = set(r["source_kinds"])
        profile_rows.append({"motif": r["motif"], "label": MOTIF_NOTES.get(r["motif"], r["motif"]), "leads": r["leads"],
                             "own": r["own"], "strength_label": r["strength"].capitalize() + " support",
                             "sources": [SOURCE_LABELS[k] for k in r["source_kinds"]],
                             "source_short": [SOURCE_SHORT[k] for k in r["source_kinds"]],
                             "basis": {"kind": "own_and_related" if r["own"] and kinds - {"own"} else "own_only" if r["own"] else "related_only",
                                       "text": _basis_text(name, r["own"], bool(kinds - {"own"}))},
                             "translation": translation(r), "examples": examples(r["motif"])})
    dims = []
    for a in AXES:
        v = axes[a]
        pulls = {pole: [MOTIF_NOTES.get(m, m) for m in ms] for pole, ms in v["pulls"].items() if ms}
        row = {"key": a, "name": AXIS_NAMES[a], "poles": POLES[a], "state": v["state"]}
        if v["state"] == "resolved":
            share = story.own_share(v)
            row.update(word=story.phrase(v), confidence_word=v["confidence_word"], tentative=v["confidence_word"] not in story.STRONG_WORDS,
                       basis_text=("From references Qloo relates to the brand only." if share == 0 else
                                   "From the brand's own motifs." if share == 1 else "From the brand's own motifs and its references."),
                       design_only=v["evidence_basis"] == "design_inference_only")
        elif v["state"] == "balanced_open":
            row["open_text"] = "Open to the perfumer: " + "; ".join(f"{', '.join(ms).lower()} toward {POLE_WORDS[p]}" for p, ms in pulls.items()) + "."
        else:
            row["open_text"] = "Open to the perfumer."
        dims.append(row)
    arch = result.get("architecture") or {"status": "open", "structure": {}, "emphasize": [], "avoid": [], "basis": None}
    roles = []
    for role in ("opening", "core", "drydown"):
        s = (arch.get("structure") or {}).get(role)
        if not s:
            roles.append({"role": role, "name": ROLE_NAMES[role], "open": True})
            continue
        direction = next((d for d in library["directions"] if d["id"] == s["direction"]), None) or {"vector": {}}
        props = [{"axis": AXIS_NAMES[a], "pole": (POLES[a][0] if c["value"] < 0 else POLES[a][1]),
                  "word": POLE_WORDS[POLES[a][0] if c["value"] < 0 else POLES[a][1]], "requested": a in s["works_with"]}
                 for a, c in direction["vector"].items() if c]
        roles.append({"role": role, "name": ROLE_NAMES[role], "open": False, "label": s["label"], "descriptors": s["descriptors"],
                      "tentative": s["basis"] == "tentative", "works_with": [AXIS_NAMES[a].lower() for a in s["works_with"]],
                      "props": props, "uncertainty": s["uncertainty"],
                      "materials": [{"generic": m["generic"], "example": m.get("example"), "supplier": m.get("supplier"),
                                     "url": m.get("url"), "ifra": m.get("ifra"),
                                     "source": " + ".join(DIRECTION_SOURCE.get(x.strip(), x.strip()) for x in m["source"].split("+"))}
                                    for m in s["materials"]]})
    why_rows = []
    for w in story.why(name, result):
        why_rows.append({"name": w["name"], "word": w["word"], "state": w["state"], "confidence_word": w["confidence_word"],
                         "chain": [{"label": MOTIF_NOTES.get(c["motif"], c["motif"]), "motif": c["motif"], "toward": c["toward"],
                                    "tentative": c["tentative"], "own": c["own"],
                                    "examples": [evidence_view(ev[e["evidence_id"]], ann.get((c["motif"], e["evidence_id"]))) for e in c["examples"]]}
                                   for c in w["chain"]]})
    motifs = [{"motif": r["motif"], "label": MOTIF_NOTES.get(r["motif"], r["motif"]), "strength_label": r["strength"].capitalize() + " support",
               "active": r["leads"], "sources": [SOURCE_LABELS[k] for k in r["source_kinds"]], "relations_only": r["relations_only"],
               "translation": translation(r), "evidence": examples(r["motif"], 8), "context": [], "excluded": [], "rule": None}
              for r in rows]
    suppliers, seen = [], set()
    for r in roles:
        for m in r.get("materials", []):
            if m.get("url") and m["url"] not in seen:
                seen.add(m["url"])
                suppliers.append({"supplier": m["supplier"], "material": m["example"], "url": m["url"], "document": m["example"], "accessed": None})
    head = story.headline(name, result)
    return {
        "engine": "continuous",
        "outcome": result["outcome"], "outcome_text": CONTINUOUS_OUTCOME_COPY[result["outcome"]],
        "headline": head, "idea": head["title"],
        "profile": [p for p in profile_rows if p["leads"]],
        "minor": [p for p in profile_rows if not p["leads"]],
        "dimensions": dims,
        "still_open": [{"key": a, "axis": AXIS_NAMES[a], "poles": POLES[a], "state": axes[a]["state"]} for a in AXES if axes[a]["state"] != "resolved"],
        "architecture": {"status": arch["status"], "tentative": arch.get("basis") == "tentative", "roles": roles,
                         "emphasize": [{"label": x["label"], "because": [AXIS_NAMES[a].lower() for a in x["because"]]} for x in arch["emphasize"]],
                         "avoid": [{"label": x["label"], "because": [AXIS_NAMES[a].lower() for a in x["because"]]} for x in arch["avoid"]]},
        "why": why_rows,
        "motifs": motifs,
        "sources": dict(sources_view(result, []), suppliers=suppliers),
        "versions": dict(result["versions"], engine=result["engine_version"]),
    }


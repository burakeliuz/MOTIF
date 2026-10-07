"""Plain-language readings of a continuous engine result: headline, cultural profile, the "why"
chain, template prose, LLM prose validation, and the brief JSON.

Shared by the web page, the printed brief, and the command line; descriptive only, it changes
no score, dimension, or direction. Wording rules: the brand's own motifs lead; a direction
drawn only from references Qloo relates to the brand never leads the title; related brands
and films are "references Qloo relates to" the brand, never an audience; unknown dimensions
are "open to the perfumer"; tentative leanings say so; no numbers, percentages, or doses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .config import AXES
from .continuous import POLES

BRIEF_SCHEMA = "brief-1.0"
DIM_NAMES = {"warm_cool": "Temperature", "light_dense": "Weight", "raw_polished": "Texture",
             "natural_synthetic": "Impression", "intimate_projecting": "Projection", "sweet_dry": "Sweetness"}
POLE_WORDS = {"light": "light", "dense": "dense", "raw": "raw-textured", "polished": "smooth-finished",
              "natural": "natural-feeling", "synthetic": "synthetic-feeling", "warm": "warm", "cool": "cool",
              "intimate": "close-wearing", "projecting": "diffusive", "sweet": "sweet", "dry": "dry"}
MOTIF_LABELS = {
    "restrained": "restraint", "precise": "precision", "natural": "naturalness", "opulent": "opulence",
    "intimate": "intimacy", "experimental": "experimentation", "provocative": "provocation", "heritage": "heritage",
    "industrial": "industrial character", "playful": "playfulness", "romantic": "romance", "melancholic": "melancholy",
    "energetic": "energy", "technological": "technology",
}
STRONG_WORDS = ("supported", "firm")
DISCLAIMER = ("A creative direction for a perfumer, not a formula: nothing has been smelled or balanced, there are no "
              "proportions or safety assessments, and nothing predicts who will like the scent. Related brands and films "
              "are references Qloo relates to the brand; a motif repeated there is a pattern, not proof of an aesthetic.")
# ingredient words an LLM text may use only when the scent architecture names them
INGREDIENT_TERMS = ("sandalwood", "vanilla", "vanillin", "rose", "oud", "patchouli", "cedar", "cedarwood", "tonka", "lavender",
                    "neroli", "jasmine", "leather", "incense", "musk", "amber", "citrus", "oakmoss", "tuberose", "ylang",
                    "cardamom", "pepper", "saffron", "violet", "iris", "orris", "vetiver", "bergamot", "labdanum",
                    "hedione", "ambrox", "habanolide", "iso e super", "mint", "aldehyde", "aldehydes")
CLAIM_PATTERNS = (r"\bwill love\b", r"\bguarantee", r"\bproven\b", r"\bscientific", r"\bvalidated\b",
                  r"\bconsumers prefer\b", r"\baudiences? (will|would|prefers?|likes?|loves?|confirms?)\b",
                  r"\b(same|shared|its|their) audiences?\b")


def _join(words: List[str], last: str = "and") -> str:
    words = [w for w in words if w]
    if not words:
        return ""
    if any("," in w for w in words):  # labels such as "earthy, mossy" stay readable as one item
        return words[0] if len(words) == 1 else "; ".join(words[:-1]) + f"; {last} " + words[-1]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + f" {last} " + words[-1]


def poss(name: str) -> str:
    return name + ("'" if name.endswith("s") else "'s")


def strength_word(score: float) -> str:
    return "strong" if score >= 0.7 else "clear" if score >= 0.5 else "present" if score >= 0.3 else "minor"


def phrase(ax: Dict[str, Any]) -> str:
    """'slightly cool', 'light', 'very dense': the intensity word and the plain pole word."""
    if ax.get("pole") is None:
        return ax.get("label") or ""
    return (ax["intensity"] + " " + POLE_WORDS[ax["pole"]]).strip()


def own_share(ax: Dict[str, Any]) -> float:
    total = sum(c["weight"] for c in ax["contributors"])
    return sum(c["weight"] for c in ax["contributors"] if c["own"]) / total if total else 0.0


def _evidence_of(result: Dict[str, Any], motif: str) -> List[Dict[str, Any]]:
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    rows = [a for a in result["annotations"] if a["motif"] == motif and a["role"] == "support" and a["evidence_id"] in ev]
    rows.sort(key=lambda a: (a["source_kind"] != "own", ev[a["evidence_id"]]["tag_name"].lower(), a["evidence_id"]))
    out, seen = [], set()
    for a in rows:
        e = ev[a["evidence_id"]]
        if e["tag_name"].lower() not in seen:
            seen.add(e["tag_name"].lower())
            out.append(dict(e, cue_id=a["cue_id"]))
    return out


def profile(name: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Motifs with support, own-entry motifs first, then by score; each says which dimensions it moves."""
    rows = []
    for m, s in result["motif_scores"].items():
        if s["common_only"]:
            continue
        moves = [{"axis": a, "name": DIM_NAMES[a], "word": phrase(result["axes"][a])}
                 for a in AXES if result["axes"][a]["state"] == "resolved"
                 and any(c["motif"] == m and (c["cell_value"] < 0) == (result["axes"][a]["value"] < 0)
                         for c in result["axes"][a]["contributors"])]
        pulls = [DIM_NAMES[a] for a in AXES if result["axes"][a]["state"] == "balanced_open"
                 and any(c["motif"] == m for c in result["axes"][a]["contributors"])]
        rows.append({"motif": m, "label": MOTIF_LABELS.get(m, m), "score": s["score"], "strength": strength_word(s["score"]),
                     "leads": m in result["leading_motifs"], "own": s["own"], "relations_only": s["relations_only"],
                     "source_kinds": list(s["source_kinds"]), "moves": moves, "pulls_open": pulls})
    rows.sort(key=lambda r: (not r["leads"], not r["own"], -r["score"], r["label"]))
    return rows


def headline(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Status label, one title, at most two lines (see the module docstring for the wording rules)."""
    axes = result["axes"]
    resolved = [a for a in AXES if axes[a]["state"] == "resolved"]
    lead = [r for r in profile(name, result) if r["leads"]]
    own_lead = [r for r in lead if r["own"]]
    rank = lambda a: (axes[a]["confidence_word"] not in STRONG_WORDS, -axes[a]["confidence"], AXES.index(a))  # noqa: E731
    own_dims = sorted((a for a in resolved if own_share(axes[a]) >= 0.5), key=rank)
    rel_dims = sorted((a for a in resolved if own_share(axes[a]) < 0.5), key=rank)
    lines: List[str] = []
    if own_lead:
        labels = [r["label"] for r in own_lead[:3]]
        if own_dims:
            title = _join(labels).capitalize() + ": a " + _join([phrase(axes[a]) for a in own_dims[:3]]) + " direction."
        else:
            title = _join(labels).capitalize() + ", from " + poss(name) + " own Qloo entry."
            moving = {c["motif"] for a in resolved for c in axes[a]["contributors"]}
            still_open = [r["label"] for r in own_lead[:3] if r["motif"] not in moving]
            if still_open:
                lines.append("How to express " + _join(still_open, "or") + " in scent is open to the perfumer.")
        if rel_dims:
            lines.append("References Qloo relates to " + name + " add " + _join([phrase(axes[a]) + " " + DIM_NAMES[a].lower()
                                                                                for a in rel_dims[:3]]) + ".")
    elif lead:
        title = "A direction drawn from references Qloo relates to " + name + "."
        lines.append(poss(name) + " own Qloo descriptors do not lead a motif on their own; "
                     + _join([r["label"] for r in lead[:3]]) + " lead" + ("s" if len(lead) == 1 else "")
                     + " only with the references.")
    elif resolved:
        # no motif reaches the lead level, yet weaker signals resolve a dimension (a known engine behaviour)
        title = "Weak signals only: no motif leads yet."
        lines.append("No motif repeats enough in " + poss(name) + " Qloo descriptors or its references to lead; the leanings shown "
                     "come from weaker signals" + (" and are tentative." if all(axes[a]["confidence_word"] not in STRONG_WORDS
                                                                               for a in resolved) else "."))
    else:
        title = "Not enough repeated signal for a direction yet."
        lines.append("Qloo returned no descriptors MOTIF can read for " + name + "." if result["outcome"] == "no_descriptive_data"
                     else "Qloo returned descriptors for " + name + ", but none repeated enough to lead.")
    if lead and resolved and len(lines) < 2 and all(axes[a]["confidence_word"] not in STRONG_WORDS for a in resolved):
        lines.append("Every leaning here is tentative: MOTIF's design reading, not a supported dimension.")
    label = ("Scent direction" if any(axes[a]["confidence_word"] in STRONG_WORDS for a in resolved)
             else "Tentative direction" if resolved else "No direction yet")
    return {"label": label, "title": title, "lines": lines[:2], "provenance": "motif_annotation"}


def why(name: str, result: Dict[str, Any], per_motif: int = 2) -> List[Dict[str, Any]]:
    """Qloo descriptor -> motif -> dimension, for every resolved or contested dimension."""
    out = []
    for a in AXES:
        ax = result["axes"][a]
        if ax["state"] == "open":
            continue
        chain = []
        for c in ax["contributors"][:3]:
            chain.append({"motif": c["motif"], "label": MOTIF_LABELS.get(c["motif"], c["motif"]),
                          "toward": POLE_WORDS[POLES[a][0 if c["cell_value"] < 0 else 1]],
                          "tentative": c["cell_confidence"] == "low", "own": c["own"],
                          "examples": _evidence_of(result, c["motif"])[:per_motif]})
        out.append({"axis": a, "name": DIM_NAMES[a], "state": ax["state"],
                    "word": phrase(ax) if ax["state"] == "resolved" else "open: motifs pull both ways",
                    "confidence_word": ax.get("confidence_word"), "chain": chain})
    return out


def open_dims(result: Dict[str, Any]) -> List[str]:
    return [a for a in AXES if result["axes"][a]["state"] != "resolved"]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def coverage(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """How much of what Qloo returned MOTIF's vocabulary reads: distinct descriptors returned, distinct ones that
    support a motif, and up to three descriptors it does not read at all (the brand's own first, quoted literally)."""
    ev = result["evidence"]
    evd = {e["evidence_id"]: e for e in ev}

    def fold(t: str) -> str:
        return t.strip().lower()
    returned = {fold(e["tag_name"]) for e in ev}
    read = {fold(evd[a["evidence_id"]]["tag_name"]) for a in result["annotations"] if a["role"] == "support" and a["evidence_id"] in evd}
    touched = {fold(evd[a["evidence_id"]]["tag_name"]) for a in result["annotations"] if a["evidence_id"] in evd}
    own, seen = [], set()
    for e in ev:
        t = fold(e["tag_name"])
        if e["source_kind"] == "own" and t not in touched and t not in seen:
            seen.add(t)
            own.append(e["tag_name"].strip())
    counts: Dict[str, set] = {}
    for e in ev:
        if fold(e["tag_name"]) not in touched:
            counts.setdefault(e["tag_name"].strip(), set()).add(e["entity_id"])
    related = sorted(counts, key=lambda t: (-len(counts[t]), t.lower()))
    return {"returned": len(returned), "read": len(read), "unread_own": own[:3], "unread_related": related[:3]}


def open_summary(name: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The dimensions the evidence leaves open: one short sentence for the page ('line'), and the method detail
    behind it, grouped by why (no read motif speaks to them, the lean is too weak to decide, or motifs pull both
    ways) with how much of Qloo's vocabulary MOTIF reads ('lines', 'coverage'). Descriptive only; nothing is filled in."""
    axes = result["axes"]
    opened = open_dims(result)
    if not opened:
        return None

    def names(xs: List[str]) -> str:
        return _join([DIM_NAMES[a].lower() for a in xs])
    lines: List[Dict[str, Any]] = []
    none = [a for a in opened if axes[a]["state"] == "open" and not axes[a]["contributors"]]
    faint = [a for a in opened if axes[a]["state"] == "open" and axes[a]["contributors"]]
    both = [a for a in opened if axes[a]["state"] == "balanced_open"]
    if none:
        lines.append({"kind": "none", "dims": [DIM_NAMES[a] for a in none],
                      "text": _cap(names(none)) + ": no motif MOTIF reads in this evidence speaks to " + ("it." if len(none) == 1 else "them.")})
    if faint:
        parts = []
        for a in faint:
            poles: Dict[str, List[str]] = {}
            for c in axes[a]["contributors"]:
                poles.setdefault(POLES[a][0 if c["cell_value"] < 0 else 1], []).append(MOTIF_LABELS.get(c["motif"], c["motif"]))
            if len(poles) == 1:
                (pole, motifs), = poles.items()
                parts.append(f"{DIM_NAMES[a].lower()} {POLE_WORDS[pole]} ({', '.join(motifs)})")
            else:
                parts.append(f"{DIM_NAMES[a].lower()} both ways")
        lines.append({"kind": "faint", "dims": [DIM_NAMES[a] for a in faint],
                      "text": "Too weak to decide, faint leans only: " + "; ".join(parts) + "."})
    if both:
        parts = []
        for a in both:
            pulls = [POLE_WORDS[pole] + " (" + ", ".join(MOTIF_LABELS.get(m, m) for m in ms) + ")" for pole, ms in axes[a]["pulls"].items() if ms]
            parts.append(f"{DIM_NAMES[a].lower()}: " + " vs ".join(pulls))
        lines.append({"kind": "both", "dims": [DIM_NAMES[a] for a in both], "text": "Motifs pull both ways — " + "; ".join(parts) + "."})
    cov = coverage(name, result)
    quoted = ["“" + t + "”" for t in (cov["unread_own"] or cov["unread_related"])]
    text = (f"MOTIF's vocabulary reads {cov['read']} of the {cov['returned']} descriptors Qloo returned for {name} "
            f"and the brands and films Qloo relates to it")
    if quoted:
        text += ("; " + poss(name) + " own " if cov["unread_own"] else "; others such as ") + _join(quoted) + " are not in it yet."
    else:
        text += "."
    return {"dims": [DIM_NAMES[a] for a in opened], "line": "Open to the perfumer: " + names(opened) + ".",
            "lines": lines, "coverage": text, "counts": cov}


def scent_story(result: Dict[str, Any]) -> Optional[str]:
    """The proposed structure in one sentence, from the chosen directions' labels (MOTIF's creative proposal)."""
    arch = result.get("architecture") or {}
    if arch.get("status") != "proposed":
        return None
    st = arch["structure"]

    def label(role: str) -> Optional[str]:
        return st[role]["label"].lower().replace(", ", " and ") if st.get(role) else None
    o, c, d = label("opening"), label("core"), label("drydown")
    parts = [f"{o} to open" if o else "an opening left to the perfumer",
             f"{_article(c)} {c} core" if c else "a core left to the perfumer",
             f"{_article(d)} {d} drydown" if d else "a drydown left to the perfumer"]
    return _cap(", ".join(parts[:2]) + " and " + parts[2]) + "."


def accord_character(result: Dict[str, Any], library: Dict[str, Any]) -> Optional[str]:
    """What the chosen directions bring to the dimensions the evidence leaves open, from their documented cells in
    the olfactory library (odor data or MOTIF's design reading). A creative reading of the proposal, not evidence:
    the dimensions stay open, nothing here changes a score, a dimension, or the structure."""
    arch = result.get("architecture") or {}
    opened = open_dims(result)
    if arch.get("status") != "proposed" or not opened:
        return None
    vectors = {d["id"]: d["vector"] for d in library["directions"]}
    picks = [(role, s["direction"]) for role, s in arch["structure"].items() if s]
    leans, mixed, unset = [], [], []
    for a in opened:
        cells = [(role, vectors[d][a]["value"]) for role, d in picks if (vectors.get(d) or {}).get(a)]
        if not cells:
            unset.append(DIM_NAMES[a].lower())
        elif len({v > 0 for _, v in cells}) == 1:
            strongest = max(abs(v) for _, v in cells)
            pole = POLES[a][1 if cells[0][1] > 0 else 0]
            word = ("slightly " if strongest <= 0.25 else "") + POLE_WORDS[pole]
            # say so when the accords go against a lean the evidence shows but too weakly to decide
            faint = {POLES[a][0 if c["cell_value"] < 0 else 1] for c in result["axes"][a]["contributors"]}
            if result["axes"][a]["state"] == "open" and len(faint) == 1 and pole not in faint:
                word += f" (against the faint {POLE_WORDS[next(iter(faint))]} lean)"
            leans.append(word)
        else:
            sides: Dict[str, List[str]] = {}
            for role, v in cells:
                sides.setdefault(POLE_WORDS[POLES[a][1 if v > 0 else 0]], []).append(role)
            mixed.append(f"{DIM_NAMES[a].lower()} is mixed ("
                         + ", ".join(word + " in the " + _join(roles) for word, roles in sides.items()) + ")")
    if not (leans or mixed or unset):
        return None
    if not (leans or mixed):
        return "As built, the accords do not set " + _join(unset) + " either."
    parts = (["the accords also read " + _join(leans)] if leans else []) + mixed
    if unset:
        parts.append(_join(unset) + (" is" if len(unset) == 1 else " are") + " not set by the accords either")
    return "As built, " + "; ".join(parts) + "."


def template_prose(name: str, result: Dict[str, Any]) -> str:
    """Plain-language brief written by a fixed template (no LLM). It opens with the same lead as the page."""
    axes = result["axes"]
    lead = headline(name, result)
    parts = [f"{name}: a direction, not a formula.", lead["title"]] + lead["lines"]
    resolved = [a for a in AXES if axes[a]["state"] == "resolved"]
    if resolved:
        parts.append("Olfactory direction: " + "; ".join(f"{DIM_NAMES[a].lower()} {phrase(axes[a])} ({axes[a]['confidence_word']})"
                                                         for a in resolved) + ".")
    arch = result.get("architecture")
    if arch and arch["status"] == "proposed":
        parts.append("In scent: " + scent_story(result)[:1].lower() + scent_story(result)[1:]
                     + (" Every role rests on tentative leanings." if arch.get("basis") == "tentative" else ""))
        if arch["emphasize"]:
            parts.append("Emphasize " + _join([x["label"].lower() for x in arch["emphasize"]]) + ".")
        if arch["avoid"]:
            parts.append("Avoid " + _join([x["label"].lower() for x in arch["avoid"]], "or") + ".")
    else:
        parts.append("No scent architecture is proposed yet.")
    opened = open_dims(result)
    if opened:
        parts.append("Open to the perfumer: " + ", ".join(DIM_NAMES[a].lower() + (" (motifs pull both ways)" if axes[a]["state"] == "balanced_open" else "")
                                                         for a in opened) + ".")
    return " ".join(parts)


def _allowed_terms(result: Dict[str, Any]) -> set:
    words = set()
    arch = result.get("architecture") or {}
    for s in (arch.get("structure") or {}).values():
        if not s:
            continue
        texts = [s["label"]] + s["descriptors"] + [m.get("generic", "") + " " + m.get("example", "") for m in s["materials"]]
        words.update(w for t in texts for w in re.findall(r"[a-z][a-z®\- ]*", t.lower()))
    for key in ("emphasize", "avoid"):
        for x in arch.get(key) or []:
            words.add(x["label"].lower())
    return words


def validate_prose(text: str, result: Dict[str, Any], name: Optional[str] = None) -> List[str]:
    """Problems with an LLM text: ingredients the architecture does not name, numbers or percentages,
    an open dimension left unsaid, a claim about preference or proof."""
    problems: List[str] = []
    if name:
        text = re.sub(re.escape(name), " ", text, flags=re.IGNORECASE)
    low = text.lower()
    allowed = " | ".join(sorted(_allowed_terms(result)))
    for term in INGREDIENT_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", low) and term not in allowed:
            problems.append(f"names an ingredient the scent architecture does not name: {term!r}")
    if "%" in text or "percent" in low:
        problems.append("contains a percentage")
    stray = re.findall(r"\d+(?:\.\d+)?", text)
    if stray:
        problems.append(f"contains numbers (scores and doses do not belong in the brief): {sorted(set(stray))}")
    for a in open_dims(result):
        if DIM_NAMES[a].lower() not in low:
            problems.append(f"does not say that {DIM_NAMES[a].lower()} is open")
    for pattern in CLAIM_PATTERNS:
        for found in re.finditer(pattern, low):
            before = low[max(0, found.start() - 12):found.start()]
            if not re.search(r"\b(not|no|never|nor)\b", before):
                problems.append(f"makes an unsupported claim ({found.group(0)!r})")
                break
    return problems


def prose_payload(name: str, result: Dict[str, Any], intent: Optional[str] = None) -> Dict[str, Any]:
    """Only what the prose needs: no raw Qloo bodies, no IDs, no scores."""
    axes = result["axes"]
    lead = headline(name, result)
    arch = result.get("architecture") or {}
    return {
        "kind": "continuous",
        "reference": name,
        "lead": {"title": lead["title"], "lines": lead["lines"]},
        "motifs": [{"motif": r["label"], "strength": r["strength"], "from_the_brand_itself": r["own"],
                    "example_qloo_descriptors": [e["tag_name"] for e in _evidence_of(result, r["motif"])[:4]]}
                   for r in profile(name, result) if r["leads"]],
        "dimensions": {DIM_NAMES[a]: {"leaning": phrase(axes[a]), "confidence": axes[a]["confidence_word"],
                                      "only_from_related_references": own_share(axes[a]) == 0}
                       for a in AXES if axes[a]["state"] == "resolved"},
        "open_dimensions": [DIM_NAMES[a] for a in open_dims(result)],
        "scent_architecture": {role: ({"direction": s["label"], "descriptors": s["descriptors"], "tentative": s["basis"] == "tentative",
                                       "material_references": [m["generic"] + (f" (e.g. {m['example']})" if m.get("example") else "")
                                                               for m in s["materials"]]} if s else "open to the perfumer")
                               for role, s in (arch.get("structure") or {}).items()},
        "emphasize": [x["label"] for x in arch.get("emphasize") or []],
        "avoid": [x["label"] for x in arch.get("avoid") or []],
        **({"user_intent": intent} if intent else {}),
    }


def build_brief(session: Dict[str, Any], result: Dict[str, Any], prose: Dict[str, Any],
                accepted_readings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    name = (session.get("resolution") or {}).get("name") or "The brand"
    cited = {a["evidence_id"] for a in result["annotations"]}
    return {
        "schema_version": BRIEF_SCHEMA,
        "engine": result["engine"],
        "data_label": session["data_label"],
        "versions": dict(result["versions"], engine=result["engine_version"], llm=prose.get("llm")),
        "seed": session["resolution"],
        "outcome": result["outcome"],
        "outcome_meaning": result["outcome_meaning"],
        "headline": headline(name, result),
        "cultural_profile": [{k: r[k] for k in ("motif", "score", "strength", "leads", "own", "source_kinds")} for r in profile(name, result)],
        "evidence": [e for e in result["evidence"] if e["evidence_id"] in cited],
        "annotations": result["annotations"],
        "motif_scores": result["motif_scores"],
        "axes": result["axes"],
        "architecture": result.get("architecture"),
        "why": [{k: v for k, v in w.items() if k != "chain"} | {"chain": [{k: c[k] for k in ("motif", "toward", "tentative", "own")}
                                                                          | {"evidence_ids": [e["evidence_id"] for e in c["examples"]]}
                                                                          for c in w["chain"]]} for w in why(name, result)],
        "open_to_the_perfumer": [DIM_NAMES[a] for a in open_dims(result)],
        "user_intent": ({"text": session["intent"], "provenance": "user_intent",
                         "effect": "recorded in the brief; it did not change motifs, scores, dimensions, or the scent architecture"}
                        if session.get("intent") else None),
        "accepted_readings": [dict(r, provenance="user_preference", effect="accepted by the user; not Qloo evidence; changed nothing")
                              for r in (accepted_readings or [])],
        "brief_text": {"author": prose["author"], "text": prose["text"], "note": prose.get("note")},
        "disclaimer": DISCLAIMER,
    }

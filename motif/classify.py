"""Lexicon classification: evidence items -> cue matches -> motif support.

Every match is a `motif_annotation` (method `lexicon`) that points back to its
evidence item. A tag that matches no cue is left unclassified; nothing is
forced into a motif.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Tuple

from .evidence import SOURCE_ORDER

STRENGTH_ORDER = ("context_only", "weak", "moderate", "strong")


def normalize_text(text: str) -> List[str]:
    lowered = text.lower().replace("-", " ")
    return re.sub(r"[^a-z ]", " ", lowered).split()


class Lexicon:
    def __init__(self, lexicon: Dict[str, Any]):
        self.version = lexicon["lexicon_version"]
        match = lexicon["match"]
        self.exclude = [re.compile(p) for p in match["exclude_patterns"]]
        self.ignore_names = {n.lower() for n in match.get("ignore_tag_names", [])}
        self.bare_poles = set(match.get("bare_pole_word_tags_are_not_cues", []))
        self.negators = set(match.get("negators", []))
        self.negation_window = int(match.get("negation_window_tokens", 0))
        self.common = set(lexicon["commonness"]["common_cue_groups_in_reference_set"])
        context = match.get("context_rules", {})
        technique = context.get("technique_nouns", {})
        self.technique_sources = set(technique.get("sources", []))
        self.technique_nouns = {tuple(n.split()) for n in technique.get("nouns", [])}
        self.ambiguous = {cue: {tuple(w.split()) for w in rule["requires_any"]}
                          for cue, rule in context.get("ambiguous_cues", {}).items()}
        self.params = lexicon["support"]["parameters"]
        # (motif, cue_id, variant tokens), longest variants first so that a phrase wins over its parts
        entries: List[Tuple[str, str, Tuple[str, ...]]] = []
        for motif, groups in lexicon["cue_groups"].items():
            for group in groups:
                for variant in group["variants"]:
                    entries.append((motif, group["cue_id"], tuple(variant.split())))
        self.entries = sorted(entries, key=lambda e: (-len(e[2]), e[0], e[1], e[2]))

    @staticmethod
    def _contains(tokens: List[str], phrases) -> List[str]:
        hits = []
        for phrase in phrases:
            n = len(phrase)
            if any(tuple(tokens[i:i + n]) == phrase for i in range(len(tokens) - n + 1)):
                hits.append(" ".join(phrase))
        return sorted(hits)

    def context_exclusion(self, tag_name: str, source_kind: str, cue_id: str) -> str:
        """Reason a matched cue cannot be read safely in this tag, or '' when it can."""
        tokens = normalize_text(tag_name)
        if source_kind in self.technique_sources:
            nouns = self._contains(tokens, self.technique_nouns)
            if nouns:
                return f"describes production technique ({', '.join(nouns)}), not the look or tone"
        if cue_id in self.ambiguous and not self._contains(tokens, self.ambiguous[cue_id]):
            return f"'{cue_id}' is ambiguous here (no design context such as costume, set, or interior)"
        return ""

    def match(self, tag_name: str) -> Dict[str, Any]:
        """Return {'status': ..., 'matches': [(motif, cue_id, negated)]} for one tag name."""
        tokens = normalize_text(tag_name)
        joined = " ".join(tokens)
        if not tokens or joined in self.ignore_names:
            return {"status": "ignored_name", "matches": []}
        if any(p.search(" " + joined + " ") for p in self.exclude):
            return {"status": "excluded_pattern", "matches": []}
        if len(tokens) == 1 and tokens[0] in self.bare_poles:
            return {"status": "bare_pole_word", "matches": []}
        found: Dict[Tuple[str, str], bool] = {}
        for motif, cue_id, variant in self.entries:
            n = len(variant)
            for start in range(len(tokens) - n + 1):
                if tuple(tokens[start:start + n]) != variant:
                    continue
                window = tokens[max(0, start - self.negation_window):start]
                negated = any(t in self.negators for t in window)
                key = (motif, cue_id)
                # a non-negated occurrence anywhere in the name wins over a negated one
                found[key] = found.get(key, True) and negated
        if not found:
            return {"status": "no_cue", "matches": []}
        return {"status": "matched", "matches": sorted((m, c, neg) for (m, c), neg in found.items())}


def classify(evidence: Sequence[Dict[str, Any]], lexicon: Lexicon) -> Dict[str, Any]:
    """Annotations and per-motif support for normalized evidence."""
    annotations: List[Dict[str, Any]] = []
    unmatched = 0
    for item in evidence:
        result = lexicon.match(item["tag_name"])
        if not result["matches"]:
            unmatched += 1
            continue
        for motif, cue_id, negated in result["matches"]:
            excluded = lexicon.context_exclusion(item["tag_name"], item["source_kind"], cue_id)
            if negated:
                role = "negated"
            elif excluded:
                role = "excluded_context"
            elif cue_id in lexicon.common:
                role = "context_common_cue"
            else:
                role = "support"
            annotations.append({
                "annotation_id": f"an:{motif}:{item['evidence_id']}",
                "provenance_category": "motif_annotation",
                "method": "lexicon",
                "lexicon_version": lexicon.version,
                "motif": motif,
                "cue_id": cue_id,
                "role": role,
                "evidence_id": item["evidence_id"],
                "source_kind": item["source_kind"],
                "entity_id": item["entity_id"],
                "tag_id": item["tag_id"],
                **({"reason": excluded} if role == "excluded_context" else {}),
            })
    annotations.sort(key=lambda a: (a["motif"], SOURCE_ORDER.index(a["source_kind"]), a["evidence_id"]))

    p = lexicon.params
    anchors = set(p["anchor_sources"])
    motifs: Dict[str, Dict[str, Any]] = {}
    for motif in sorted({a["motif"] for a in annotations}):
        rows = [a for a in annotations if a["motif"] == motif]
        support = [a for a in rows if a["role"] == "support"]
        kinds = sorted({a["source_kind"] for a in support}, key=SOURCE_ORDER.index)
        own_groups = sorted({a["cue_id"] for a in support if a["source_kind"] == "own"})
        anchored = bool(set(kinds) & anchors)
        if anchored and len(kinds) >= p["strong_min_source_kinds"]:
            strength = "strong"
        elif anchored and (len(kinds) >= p["moderate_min_source_kinds"] or len(own_groups) >= p["own_route_min_cue_groups"]):
            strength = "moderate"
        elif support:
            strength = "weak"
        else:
            strength = "context_only"
        motifs[motif] = {
            "motif": motif,
            "strength": strength,
            "active": strength in ("strong", "moderate"),
            "anchored": anchored,
            "source_kinds": kinds,
            "relations_only": anchored and "own" not in kinds,
            # pre-threshold view: what each source kind contributed before any strength rule
            "support_by_source": {
                k: {"entities": len({a["entity_id"] for a in support if a["source_kind"] == k}),
                    "cue_groups": sorted({a["cue_id"] for a in support if a["source_kind"] == k})}
                for k in kinds
            },
            "own_cue_groups": own_groups,
            "support_evidence_ids": sorted({a["evidence_id"] for a in support}),
            "context_evidence_ids": sorted({a["evidence_id"] for a in rows if a["role"] == "context_common_cue"}),
            "negated_evidence_ids": sorted({a["evidence_id"] for a in rows if a["role"] == "negated"}),
            "excluded_evidence": sorted(({"evidence_id": a["evidence_id"], "reason": a["reason"]}
                                         for a in rows if a["role"] == "excluded_context"), key=lambda x: x["evidence_id"]),
        }
    return {"annotations": annotations, "motifs": motifs, "unmatched_items": unmatched}

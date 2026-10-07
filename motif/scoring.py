"""Weighted motif scores: graded support instead of binary activation (config/motif_scoring.v1.json).

A motif's score is a noisy-OR over evidence channels (own entry, related brands,
related films, related artists when fetched, and diversity: distinct cue groups and
distinct source kinds). Each channel
saturates in its evidence units, so ten related brands do not count ten times as
much as one, and a single channel can never reach 1. Same annotations and same
config give the same scores; nothing here reads the network, the clock, or an LLM.

A score is a bounded design quantity for ranking and weighting motifs. It is not a
probability and not a measure of how strongly a brand "is" a motif.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence

from .evidence import SOURCE_ORDER

COUNTED = ("support", "context_common_cue")


def _saturate(units: float, tau: float) -> float:
    return 1.0 - math.exp(-units / tau) if units > 0 else 0.0


def channel_units(kind: str, rows: Sequence[Dict[str, Any]], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Evidence units of one source kind for one motif, with the counts they come from."""
    beta = cfg["extra_item_weight"]
    support = [a for a in rows if a["role"] == "support"]
    common = [a for a in rows if a["role"] == "context_common_cue"]
    if kind == "own":
        groups = sorted({a["cue_id"] for a in support})
        common_only = sorted({a["cue_id"] for a in common} - set(groups))
        units = len(groups) + beta * (len(support) - len(groups)) + cfg["common_cue_weight"]["own"] * len(common_only)
        return {"units": units, "tags": len(support), "cue_groups": groups, "common_cue_groups": common_only}
    entities = sorted({str(a["entity_id"]) for a in support})
    common_only = sorted({str(a["entity_id"]) for a in common} - set(entities))
    units = len(entities) + beta * (len(support) - len(entities)) + cfg["common_cue_weight"]["related"] * len(common_only)
    return {"units": units, "tags": len(support), "entities": len(entities), "common_only_entities": len(common_only),
            "cue_groups": sorted({a["cue_id"] for a in support})}


def score_motifs(annotations: Iterable[Dict[str, Any]], cfg: Dict[str, Any],
                 kinds: Sequence[str] = ("own", "brand", "movie")) -> Dict[str, Dict[str, Any]]:
    """{motif: {score, channels, ...}} for every motif with at least one counted annotation.

    `kinds` are the source kinds this session fetched; a channel outside it (for example
    artist when it was not requested) contributes nothing even if annotations exist.
    """
    digits = cfg["rounding_digits"]
    rows_by_motif: Dict[str, List[Dict[str, Any]]] = {}
    for a in annotations:
        if a["role"] in COUNTED and a["source_kind"] in kinds:
            rows_by_motif.setdefault(a["motif"], []).append(a)
    out: Dict[str, Dict[str, Any]] = {}
    for motif in sorted(rows_by_motif):
        rows = rows_by_motif[motif]
        channels: Dict[str, Dict[str, Any]] = {}
        keep = 1.0
        groups = set()
        for kind in sorted({a["source_kind"] for a in rows}, key=SOURCE_ORDER.index):
            ch = cfg["channels"][kind]
            info = channel_units(kind, [a for a in rows if a["source_kind"] == kind], cfg)
            s = _saturate(info["units"], ch["tau"])
            keep *= 1.0 - ch["weight"] * s
            groups.update(info["cue_groups"])
            channels[kind] = dict(info, units=round(info["units"], digits), saturation=round(s, digits),
                                  weight=ch["weight"], contribution=round(ch["weight"] * s, digits))
        div = cfg["diversity"]
        supported_kinds = [k for k in channels if channels[k]["tags"] > 0]
        d_units = max(len(groups) - 1, 0) + max(len(supported_kinds) - 1, 0)
        d = _saturate(d_units, div["tau"])
        keep *= 1.0 - div["weight"] * d
        channels["diversity"] = {"units": d_units, "cue_groups": len(groups), "source_kinds": len(supported_kinds), "saturation": round(d, digits), "weight": div["weight"],
                                 "contribution": round(div["weight"] * d, digits)}
        kinds_with_support = supported_kinds
        out[motif] = {
            "motif": motif,
            "score": round(1.0 - keep, digits),
            "own": "own" in kinds_with_support,
            "relations_only": bool(kinds_with_support) and "own" not in kinds_with_support,
            "common_only": not kinds_with_support,
            "source_kinds": kinds_with_support,
            "cue_groups": sorted(groups),
            "support_tags": sum(channels[k]["tags"] for k in channels if k != "diversity"),
            "related_entities": sum(channels[k].get("entities", 0) for k in channels if k not in ("own", "diversity")),
            "channels": channels,
            "scoring_version": cfg["scoring_version"],
        }
    return out

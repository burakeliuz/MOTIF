"""Active motifs -> six sensory axes through the draft rules R1-R5.

An axis is `unknown` (null), `target` (one pole), or `conflicted` (null; two
active motifs push opposite poles). Unmapped motifs never move an axis. There
is no neutral or zero value.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .classify import STRENGTH_ORDER
from .config import AXES


def translate(motifs: Dict[str, Dict[str, Any]], rules: Dict[str, Any], overrides: Dict[str, str] = None) -> Dict[str, Any]:
    """`overrides`: {axis: pole or 'open'} chosen by the user for a conflicted axis (stored as manual)."""
    overrides = overrides or {}
    mapped = {r["motif"]: r for r in rules["rules"]}
    pushes: Dict[str, List[Dict[str, Any]]] = {a: [] for a in AXES}
    for motif in sorted(motifs):
        info = motifs[motif]
        rule = mapped.get(motif)
        if info["active"] and rule:
            pushes[rule["axis"]].append({"pole": rule["toward"], "rule_id": rule["rule_id"], "motif": motif,
                                         "strength": info["strength"], "relations_only": info["relations_only"]})
    axes: Dict[str, Dict[str, Any]] = {}
    for axis in AXES:
        rows = sorted(pushes[axis], key=lambda r: r["rule_id"])
        poles = sorted({r["pole"] for r in rows})
        if not rows:
            axes[axis] = {"state": "unknown", "value": None}
        elif len(poles) == 1:
            best = max(rows, key=lambda r: STRENGTH_ORDER.index(r["strength"]))
            axes[axis] = {
                "state": "target", "value": poles[0],
                "rule_ids": [r["rule_id"] for r in rows], "motifs": [r["motif"] for r in rows],
                "evidence_strength": best["strength"],
                "relations_only": all(r["relations_only"] for r in rows),
                "rule_confidence": "draft_hypothesis",
            }
        else:
            axes[axis] = {"state": "conflicted", "value": None,
                          "pushes": [{k: r[k] for k in ("pole", "rule_id", "motif", "strength")} for r in rows]}
        choice = overrides.get(axis)
        if choice and axes[axis]["state"] == "conflicted":
            if choice == "open":
                axes[axis]["user_choice"] = {"provenance_category": "manual", "choice": "left_open"}
            elif choice in poles:
                chosen = [r for r in rows if r["pole"] == choice]
                axes[axis] = {
                    "state": "target", "value": choice, "rule_ids": [r["rule_id"] for r in chosen],
                    "motifs": [r["motif"] for r in chosen],
                    "evidence_strength": max((r["strength"] for r in chosen), key=STRENGTH_ORDER.index),
                    "relations_only": all(r["relations_only"] for r in chosen),
                    "rule_confidence": "draft_hypothesis",
                    "user_choice": {"provenance_category": "manual", "choice": choice,
                                    "overrode_conflict_with": [r["motif"] for r in rows if r["pole"] != choice]},
                }
            else:
                raise ValueError(f"{choice!r} is not one of the conflicting poles {poles} on {axis}")
    unmapped_active = sorted(m for m, info in motifs.items() if info["active"] and m not in mapped)
    return {"axes": axes, "unmapped_active_motifs": unmapped_active}

"""Deterministic material scoring and composition (MOTIF_BUILD_SPEC.md section 9).

score(m) = sum over targeted axes a of weight(a) * s(m, a) / |targeted axes|
s = +1 when the material's usable profile has the target pole, -1 for the
opposite pole, 0 when the profile says nothing. The denominator is the number
of targets, so a material that matches one target of three cannot outscore one
that matches all three.

Only properties with an allowed verification status are usable. By default
that is `verified_full_page`; the design preview may add `unverified_excerpt`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .config import AXES

VERIFIED = ("verified_full_page",)
PREVIEW = ("verified_full_page", "unverified_excerpt")


def usable_profile(material: Dict[str, Any], allowed_status: Sequence[str]) -> Dict[str, str]:
    checks = material.get("property_verification", {})
    return {axis: pole for axis, pole in sorted(material["motif_profile"].items())
            if (checks.get(axis) or {}).get("status") in allowed_status}


def match_materials(axes: Dict[str, Dict[str, Any]], palette: Dict[str, Any], params: Dict[str, Any],
                    allow_unverified: bool = False) -> Dict[str, Any]:
    allowed = PREVIEW if allow_unverified else VERIFIED
    weights = params["evidence_weights"]
    targets = {a: axes[a] for a in AXES if axes[a]["state"] == "target"}
    open_axes = [a for a in AXES if axes[a]["state"] != "target"]
    base = {"verification_mode": "design_preview_unverified" if allow_unverified else "verified_only",
            "targets_count": len(targets), "open_axes": open_axes, "selected": [], "ranked": [], "excluded": []}

    if not targets:
        return dict(base, status="no_targets")

    rows = []
    for m in sorted(palette["materials"], key=lambda x: x["material_id"]):
        profile = usable_profile(m, allowed)
        row = {"material_id": m["material_id"], "name": m["name"], "role": m["composition_role"],
               "usable_profile": profile,
               "unverified_properties": sorted(set(m["motif_profile"]) - set(profile))}
        if not profile:
            base["excluded"].append(dict(row, reason="no usable (verified) properties"))
            continue
        total, matches, opposes = 0.0, [], []
        for axis in sorted(targets, key=AXES.index):
            t = targets[axis]
            w = weights[t["evidence_strength"]]
            if axis not in profile:
                continue
            if profile[axis] == t["value"]:
                total += w
                matches.append(axis)
            else:
                total -= w
                opposes.append(axis)
        row.update(score=round(total / len(targets), 6), matches=matches, opposes=opposes,
                   unrequested_properties=[{"axis": a, "pole": p, "label": "creative choice, not evidence"}
                                           for a, p in sorted(profile.items(), key=lambda x: AXES.index(x[0]))
                                           if a not in targets])
        if opposes:
            base["excluded"].append(dict(row, reason="opposite pole on " + ", ".join(opposes)))
        elif row["score"] <= 0:
            base["excluded"].append(dict(row, reason="does not match any target"))
        else:
            rows.append(row)

    def rank_key(r):
        return (-r["score"], len(r["unrequested_properties"]), r["material_id"])

    ranked = sorted(rows, key=rank_key)
    base["ranked"] = ranked
    if len(targets) < params["min_target_axes_for_composition"]:
        return dict(base, status="gated_insufficient_axes",
                    gate=f"{len(targets)} targeted axis/axes < min_target_axes_for_composition={params['min_target_axes_for_composition']} (design threshold)")
    if len(ranked) < params["min_eligible_materials"]:
        status = "no_verified_materials" if not allow_unverified and not ranked else "insufficient_eligible_materials"
        return dict(base, status=status)

    comp = params["composition"]
    slots = dict(comp["slots"])
    used = {"top": 0, "heart": 0, "base": 0}
    selected: List[Dict[str, Any]] = []

    def place(r) -> bool:
        if any(s["material_id"] == r["material_id"] for s in selected) or len(selected) >= comp["max_materials"]:
            return False
        roles = r["role"].split("|")
        if roles == ["heart", "base"]:
            roles = ["heart"] if used["heart"] == 0 else ["base"]
        for role in roles:
            if used[role] < slots[role]:
                used[role] += 1
                selected.append(dict(r, slot=role))
                return True
        return False

    covered = set()
    for axis in sorted(targets, key=lambda a: (-weights[targets[a]["evidence_strength"]], AXES.index(a))):
        if axis in covered:
            continue
        for r in ranked:
            if axis in r["matches"] and place(r):
                covered.update(r["matches"])
                break
    for r in ranked:
        if len(selected) >= comp["fill_to"]:
            break
        place(r)
    uncovered = [a for a in targets if a not in covered]
    order = {"top": 0, "heart": 1, "base": 2}
    selected.sort(key=lambda s: (order[s["slot"]], s["material_id"]))
    return dict(base, status="composed", selected=selected, uncovered_targets=uncovered,
                empty_slots=[k for k in ("top", "heart", "base") if used[k] == 0])

"""The continuous sensory engine: weighted motifs -> six continuous sensory dimensions.

Pipeline (no LLM anywhere): Qloo evidence -> lexicon annotations (lexicon-0.3, unchanged)
-> weighted motif scores (motif/scoring.py) -> per-dimension aggregation through the
researched motif-to-sensory model (config/motif_sensory_vectors.v1.json) -> olfactory
structure (motif/olfactory.py).

Per dimension, only motifs with a non-null cell contribute (null means "no relation is
claimed", never zero). Each contribution is motif score x cell confidence weight x cell
value, and the full chain evidence -> motif -> score -> contribution -> dimension is kept.
A dimension whose contributors cancel is reported as balanced and open, never as a
confident middle; "balanced" as a resolved label is reserved for evidenced neutrality
(cells of value 0), which the shipped model does not use. Same evidence and same config versions give the same result.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from .classify import Lexicon, classify
from .config import AXES
from .evidence import normalize_evidence
from .scoring import score_motifs

CONTINUOUS_ENGINE_VERSION = "continuous-1.0"
CONFIDENCE_ORDER = ("low", "medium", "high")
POLES = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
         "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"),
         "sweet_dry": ("sweet", "dry")}
OUTCOMES = {
    "no_descriptive_data": "Qloo returned no descriptor tags in the namespaces MOTIF reads: data not found.",
    "insufficient_evidence": "Descriptors were found, but no motif reached the score needed to lead a direction.",
    "open_direction": "Motifs are supported, but no sensory dimension is resolved: every dimension is open to the perfumer.",
    "direction": "At least one sensory dimension is resolved from the weighted motifs (a creative direction, not a formula).",
}


def _word(bins: Sequence[Dict[str, Any]], x: float) -> str:
    for b in bins:
        if x < b["below"]:
            return b["word"]
    return bins[-1]["word"]


def aggregate_axes(scores: Dict[str, Dict[str, Any]], vectors: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    agg = params["aggregation"]
    cw = params["confidence_weights"]
    digits = params["rounding_digits"]
    axes: Dict[str, Dict[str, Any]] = {}
    for axis in AXES:
        rows, context = [], []
        for motif in sorted(scores):
            s = scores[motif]
            cell = (vectors["motifs"].get(motif) or {}).get("cells", {}).get(axis)
            if not cell or cell.get("value") is None or s["score"] <= 0:
                continue
            if s["common_only"]:
                # only cues common across the reference brands: shown as context, never a pull
                context.append({"motif": motif, "score": s["score"], "cell_value": cell["value"]})
                continue
            w = s["score"] * cw[cell["confidence"]]
            rows.append({"motif": motif, "score": s["score"], "cell_value": cell["value"], "cell_confidence": cell["confidence"],
                         "evidence_type": cell["evidence_type"], "weight": w, "contribution": w * cell["value"],
                         "own": s["own"], "relations_only": s["relations_only"],
                         "rationale": cell.get("rationale"), "uncertainty": cell.get("uncertainty")})
        support = sum(r["weight"] for r in rows)
        mass = sum(r["weight"] * abs(r["cell_value"]) for r in rows)
        net = sum(r["contribution"] for r in rows)
        agreement = abs(net) / mass if mass > 0 else (1.0 if rows else 0.0)
        raw_value = net / support if support > 0 else None
        confidence = (1.0 - math.exp(-mass / agg["mass_tau"])) * agreement if rows else 0.0
        if mass < agg["min_mass"] and not (rows and mass == 0 and support >= agg["min_mass"]):
            state = "open"
        elif agreement < agg["min_agreement"]:
            state = "balanced_open"
        else:
            state = "resolved"
        minus, plus = POLES[axis]
        out = {"state": state, "value": round(raw_value, digits) if state == "resolved" else None,
               "raw_value": round(raw_value, digits) if raw_value is not None else None,
               "support": round(support, digits), "mass": round(mass, digits), "agreement": round(agreement, digits),
               "confidence": round(confidence, digits),
               "pulls": {minus: [r["motif"] for r in rows if r["cell_value"] < 0],
                         plus: [r["motif"] for r in rows if r["cell_value"] > 0]},
               "relations_only_share": round(sum(r["weight"] for r in rows if r["relations_only"]) / support, digits) if support else None,
               "evidence_basis": (None if not rows else "design_inference_only" if all(r["evidence_type"] == "motif_design_inference" for r in rows)
                                  else "imagery_route" if all(r["evidence_type"] == "imagery_route" for r in rows) else "mixed"),
               "best_cell_confidence": max((r["cell_confidence"] for r in rows), key=CONFIDENCE_ORDER.index, default=None),
               "common_cue_context": context,
               "contributors": [dict(r, weight=round(r["weight"], digits), contribution=round(r["contribution"], digits))
                                for r in sorted(rows, key=lambda r: (-abs(r["contribution"]), r["motif"]))]}
        if state == "resolved":
            # "balanced" only for evidenced neutrality (cells of value 0); otherwise a weak tendency keeps its pole
            neutral = mass == 0
            intensity = "balanced" if neutral else _word(params["wording_bins"], abs(raw_value))
            pole = None if neutral else (minus if raw_value < 0 else plus)
            # the word never claims more than the best cell behind it: low cells alone stay "tentative"
            word = _word(params["confidence_words"], confidence)
            cap = params["confidence_word_cap"][out["best_cell_confidence"]]
            words = [b["word"] for b in params["confidence_words"]]
            out.update(pole=pole, intensity=intensity, label=("balanced" if neutral else (intensity + " " + pole).strip()),
                       confidence_word=min(word, cap, key=words.index))
        axes[axis] = out
    return axes


def run_continuous(evidence: Sequence[Dict[str, Any]], lexicon: Dict[str, Any], scoring: Dict[str, Any],
                   vectors: Dict[str, Any], params: Dict[str, Any], kinds: Sequence[str] = ("own", "brand", "movie"),
                   olfactory: Optional[Any] = None) -> Dict[str, Any]:
    """`olfactory(axes, scores)` (motif/olfactory.py) adds the scent architecture when given."""
    items = normalize_evidence(evidence)
    classified = classify(items, Lexicon(lexicon))
    scores = score_motifs(classified["annotations"], scoring, kinds)
    axes = aggregate_axes(scores, vectors, params)
    leading = [m for m, s in scores.items() if s["score"] >= params["lead"]["min_score"] and not s["common_only"]]
    resolved = [a for a in AXES if axes[a]["state"] == "resolved"]
    if not items:
        outcome = "no_descriptive_data"
    elif not leading:
        outcome = "insufficient_evidence"
    elif not resolved:
        outcome = "open_direction"
    else:
        outcome = "direction"
    result = {
        "engine": "continuous",
        "engine_version": CONTINUOUS_ENGINE_VERSION,
        "versions": {"lexicon": lexicon["lexicon_version"], "scoring": scoring["scoring_version"],
                     "sensory_model": vectors["model_version"], "params": params["params_version"]},
        "outcome": outcome,
        "outcome_meaning": OUTCOMES[outcome],
        "evidence_count": len(items),
        "unclassified_evidence_count": classified["unmatched_items"],
        "evidence": items,
        "annotations": classified["annotations"],
        "motif_scores": scores,
        "leading_motifs": sorted(leading, key=lambda m: (-scores[m]["score"], m)),
        "axes": axes,
        "resolved_axes": resolved,
        "open_axes": [a for a in AXES if axes[a]["state"] != "resolved"],
    }
    if olfactory is not None:
        result["olfactory"] = olfactory(axes, scores)
    return result


def commitment(axes: Dict[str, Dict[str, Any]]) -> List[float]:
    """Signed commitment per dimension: value x confidence when resolved, 0 when open (no claim)."""
    return [round((axes[a]["value"] or 0.0) * axes[a]["confidence"], 6) if axes[a]["state"] == "resolved" else 0.0
            for a in AXES]

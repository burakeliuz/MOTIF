"""The deterministic engine: normalized evidence + versioned config -> engine result.

Same normalized evidence and same config versions give the same result
(byte-identical JSON with sort_keys). Input order and duplicate items do not
matter: evidence is normalized first. Nothing here reads the network, the
clock, or an LLM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import ENGINE_VERSION
from .classify import Lexicon, classify
from .config import EngineConfig
from .evidence import normalize_evidence
from .materials import match_materials
from .translate import translate

OUTCOMES = {
    "no_descriptive_data": "Qloo returned no descriptor tags in the namespaces MOTIF reads: data not found.",
    "insufficient_evidence": "Descriptors were found, but no motif reached the activation threshold.",
    "no_translation_rule": "At least one motif is supported, but none has a sensory translation rule: data exists, rule missing.",
    "conflicted": "Active motifs push an axis to opposite poles; a user choice is needed.",
    "partial_direction": "Fewer targeted axes than the composition threshold; candidates are listed, no composition.",
    "no_verified_materials": "Targets exist, but no palette material has verified properties for them.",
    "insufficient_eligible_materials": "Targets exist, but fewer than the minimum number of materials fit them.",
    "composed": "Targets and a material proposal (creative direction, not a formula).",
}


def run_engine(evidence: Sequence[Dict[str, Any]], config: EngineConfig, allow_unverified: bool = False,
               overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    items = normalize_evidence(evidence)
    lexicon = Lexicon(config.lexicon)
    classified = classify(items, lexicon)
    translated = translate(classified["motifs"], config.rules, overrides)
    axes = translated["axes"]
    materials = match_materials(axes, config.palette, config.params, allow_unverified)

    motifs = classified["motifs"]
    active = [m for m, info in motifs.items() if info["active"]]
    conflicted = [a for a, v in axes.items() if v["state"] == "conflicted" and "user_choice" not in v]
    if not items:
        outcome = "no_descriptive_data"
    elif not active:
        outcome = "insufficient_evidence"
    elif conflicted:
        outcome = "conflicted"
    elif materials["status"] == "no_targets":
        outcome = "no_translation_rule"
    elif materials["status"] == "gated_insufficient_axes":
        outcome = "partial_direction"
    else:
        outcome = materials["status"]

    return {
        "engine_version": ENGINE_VERSION,
        "versions": config.versions,
        "outcome": outcome,
        "outcome_meaning": OUTCOMES[outcome],
        "evidence_count": len(items),
        "unclassified_evidence_count": classified["unmatched_items"],
        "evidence": items,
        "annotations": classified["annotations"],
        "motifs": motifs,
        "unmapped_active_motifs": translated["unmapped_active_motifs"],
        "axes": axes,
        "conflicted_axes": conflicted,
        "materials": materials,
    }


def evidence_subset(evidence: Sequence[Dict[str, Any]], kinds: Sequence[str]) -> List[Dict[str, Any]]:
    return [e for e in evidence if e["source_kind"] in kinds]

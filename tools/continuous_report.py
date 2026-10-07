"""Phase 6 diagnostic: legacy rule engine vs continuous engine on the 13 trial brands (offline).

Used by `python3 tools/engine_compare.py analysis`. Both engines read the same evidence
(the legacy controller's fetches). Metrics:

* distinct sensory profiles: legacy = set of targets; continuous = resolved labels per
  dimension (open and balanced-open both count as "open"), and the stricter variant that
  also distinguishes open from balanced-open;
* pairwise distances: Euclidean between per-dimension commitment vectors
  (continuous: value x confidence when resolved, else 0; legacy: pole sign x evidence weight);
* dimension coverage and unresolved share; exact collisions;
* sensitivity: remove one related entity at a time; stability: drop the lowest-scoring motif.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from motif.config import AXES, load_continuous_config  # noqa: E402
from motif.continuous import aggregate_axes, commitment, run_continuous  # noqa: E402

PAIRS = [("MUJI", "Aesop"), ("MUJI", "Le Labo"), ("A24", "Supreme"), ("Gucci", "Balenciaga"), ("Ralph Lauren", "Harley-Davidson")]
LEGACY_WEIGHT = {"strong": 1.0, "moderate": 0.6}
POLE_SIGN = {"warm": -1, "cool": 1, "light": -1, "dense": 1, "raw": -1, "polished": 1, "natural": -1, "synthetic": 1,
             "intimate": -1, "projecting": 1, "sweet": -1, "dry": 1}


def signature(axes: Dict[str, Any], strict: bool = False) -> Tuple[str, ...]:
    """Resolved labels per dimension ("open" otherwise); strict adds the confidence word and tells
    open from balanced-open."""
    out = []
    for a in AXES:
        v = axes[a]
        if v["state"] == "resolved":
            out.append(v["label"] + (" · " + v["confidence_word"] if strict else ""))
        else:
            out.append(v["state"] if strict else "open")
    return tuple(out)


def medium_only(vectors: Dict[str, Any]) -> Dict[str, Any]:
    """The model without its low-confidence (tentative) cells: an ablation, not a product setting."""
    out = json.loads(json.dumps(vectors))
    for spec in out["motifs"].values():
        for a, c in spec["cells"].items():
            if c and c["confidence"] == "low":
                spec["cells"][a] = None
    return out


def near_pairs(dists: Dict[str, float]) -> List[str]:
    """Pairs closer than a quarter of the engine's own median pairwise distance (scale-free)."""
    vals = sorted(dists.values())
    median = vals[len(vals) // 2]
    return sorted(k for k, v in dists.items() if v < 0.25 * median)


def legacy_signature(result: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(result["axes"][a]["value"] if result["axes"][a]["state"] == "target" else "open" for a in AXES)


def legacy_commitment(result: Dict[str, Any]) -> List[float]:
    return [POLE_SIGN[v["value"]] * LEGACY_WEIGHT[v["evidence_strength"]] if v["state"] == "target" else 0.0
            for v in (result["axes"][a] for a in AXES)]


def dist(u, v) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(u, v)))


def continuous_of(evidence, cc) -> Dict[str, Any]:
    return run_continuous(evidence, cc.lexicon, cc.scoring, cc.vectors, cc.params)


def analysis(legacy: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    cc = load_continuous_config()
    cc_medium = type(cc)(cc.lexicon, cc.scoring, medium_only(cc.vectors), cc.params, cc.library)
    brands: Dict[str, Any] = {}
    for name, lr in legacy.items():
        r = continuous_of(lr["evidence"], cc)
        base = commitment(r["axes"])
        # sensitivity: one related entity removed at a time
        related = sorted({str(e["entity_id"]) for e in r["evidence"] if e["source_kind"] != "own"})
        moves, flips = [], 0
        for ent in related:
            alt = continuous_of([e for e in r["evidence"] if str(e["entity_id"]) != ent], cc)
            moves.append(dist(base, commitment(alt["axes"])))
            flips += signature(alt["axes"]) != signature(r["axes"])
        # stability: drop the lowest-scoring contributing motif below the lead level (a minor signal)
        scores = r["motif_scores"]
        contributing = sorted({c["motif"] for a in AXES for c in r["axes"][a]["contributors"]
                               if scores[c["motif"]]["score"] < cc.params["lead"]["min_score"]}, key=lambda m: (scores[m]["score"], m))
        drop = None
        if contributing:
            weakest = contributing[0]
            kept = {m: s for m, s in scores.items() if m != weakest}
            alt_axes = aggregate_axes(kept, cc.vectors, cc.params)
            drop = {"motif": weakest, "score": scores[weakest]["score"], "move": round(dist(base, commitment(alt_axes)), 4),
                    "label_change": signature(alt_axes) != signature(r["axes"])}
        lsig = legacy_signature(lr)
        med = continuous_of(lr["evidence"], cc_medium)
        brands[name] = {
            "outcome": r["outcome"], "legacy_outcome": lr["outcome"],
            "leading": [(m, scores[m]["score"]) for m in r["leading_motifs"]],
            "axes": {a: {k: r["axes"][a].get(k) for k in ("state", "label", "value", "confidence", "confidence_word", "agreement", "mass", "evidence_basis")} for a in AXES},
            "contributions": {a: [(c["motif"], c["contribution"]) for c in r["axes"][a]["contributors"]] for a in AXES},
            "signature": signature(r["axes"]), "strict_signature": signature(r["axes"], strict=True),
            "medium_only_signature": signature(med["axes"]),
            "commitment": base, "legacy_signature": lsig, "legacy_commitment": legacy_commitment(lr),
            "legacy_selected": sorted(m["material_id"] for m in lr["materials"].get("selected", [])),
            "sensitivity": {"related_entities": len(related), "max_move": round(max(moves) if moves else 0.0, 4),
                            "mean_move": round(sum(moves) / len(moves), 4) if moves else 0.0, "label_flips": flips},
            "drop_weakest": drop,
        }
    names = list(brands)
    pd_c = {f"{x} – {y}": round(dist(brands[x]["commitment"], brands[y]["commitment"]), 4) for x, y in itertools.combinations(names, 2)}
    pd_l = {f"{x} – {y}": round(dist(brands[x]["legacy_commitment"], brands[y]["legacy_commitment"]), 4) for x, y in itertools.combinations(names, 2)}

    def groups(key):
        g: Dict[Tuple, List[str]] = {}
        for n in names:
            g.setdefault(tuple(brands[n][key]), []).append(n)
        return [v for v in g.values() if len(v) > 1]

    share: Dict[str, float] = {}
    for b in brands.values():
        for a in AXES:
            for m, c in b["contributions"][a]:
                share[m] = share.get(m, 0.0) + abs(c)
    total = sum(share.values()) or 1.0
    return {
        "brands": brands,
        "unique": {"legacy_targets": len({b["legacy_signature"] for b in brands.values()}),
                   "legacy_materials": len({tuple(b["legacy_selected"]) for b in brands.values()}),
                   "continuous_resolved_labels": len({b["signature"] for b in brands.values()}),
                   "continuous_strict": len({b["strict_signature"] for b in brands.values()}),
                   "continuous_medium_cells_only": len({b["medium_only_signature"] for b in brands.values()})},
        "collisions": {"legacy_targets": groups("legacy_signature"), "continuous_resolved_labels": groups("signature"),
                       "continuous_strict": groups("strict_signature"), "continuous_medium_cells_only": groups("medium_only_signature")},
        "distances": {"continuous": pd_c, "legacy": pd_l,
                      "continuous_mean": round(sum(pd_c.values()) / len(pd_c), 4), "legacy_mean": round(sum(pd_l.values()) / len(pd_l), 4),
                      "continuous_min": min(pd_c.items(), key=lambda kv: kv[1]), "legacy_zero_pairs": sum(1 for v in pd_l.values() if v == 0),
                      "continuous_zero_pairs": sum(1 for v in pd_c.values() if v == 0),
                      "continuous_near_pairs": near_pairs(pd_c), "legacy_near_pairs": near_pairs(pd_l)},
        "coverage": {a: {"continuous": sum(1 for b in brands.values() if b["axes"][a]["state"] == "resolved"),
                         "legacy": sum(1 for b in brands.values() if b["legacy_signature"][AXES.index(a)] != "open")} for a in AXES},
        "unresolved_share": {"continuous": round(sum(1 for b in brands.values() for a in AXES if b["axes"][a]["state"] != "resolved") / (6 * len(brands)), 3),
                             "legacy": round(sum(1 for b in brands.values() for s in b["legacy_signature"] if s == "open") / (6 * len(brands)), 3)},
        "motif_share": {m: round(v / total, 3) for m, v in sorted(share.items(), key=lambda kv: -kv[1])},
        "pairs": {f"{x} – {y}": {"continuous": pd_c.get(f"{x} – {y}", pd_c.get(f"{y} – {x}")),
                                 "legacy": pd_l.get(f"{x} – {y}", pd_l.get(f"{y} – {x}")),
                                 "same_labels": brands[x]["signature"] == brands[y]["signature"]} for x, y in PAIRS},
        "sanrio_nearest": min(((n, pd_c.get(f"Sanrio – {n}", pd_c.get(f"{n} – Sanrio"))) for n in names if n != "Sanrio"), key=lambda kv: kv[1]),
    }


def _groups(gs: List[List[str]]) -> str:
    return "; ".join(" = ".join(g) for g in gs) or "none"


def analysis_markdown(rep: Dict[str, Any]) -> str:
    B = rep["brands"]
    short = {"warm_cool": "Temperature", "light_dense": "Weight", "raw_polished": "Texture", "natural_synthetic": "Impression",
             "intimate_projecting": "Projection", "sweet_dry": "Sweetness"}
    L = ["### C.1 Distinct profiles and distances (13 brands)", "",
         "| Measure | Legacy (engine-0.3) | Continuous (continuous-1.0) |", "|---|---|---|",
         f"| Distinct sensory profiles (resolved labels) | {rep['unique']['legacy_targets']} | {rep['unique']['continuous_resolved_labels']} |",
         f"| … with the confidence word, open vs balanced-open | | {rep['unique']['continuous_strict']} |",
         f"| … with the medium-confidence cells only (ablation: no tentative cells) | | {rep['unique']['continuous_medium_cells_only']} (identical: {_groups(rep['collisions']['continuous_medium_cells_only'])}) |",
         f"| Distinct final outputs | {rep['unique']['legacy_materials']} (selected materials) | not applicable before phase 8 (scent architecture) |",
         f"| Identical-profile groups | {_groups(rep['collisions']['legacy_targets'])} | {_groups(rep['collisions']['continuous_resolved_labels'])} |",
         f"| Mean pairwise distance (commitment vectors) | {rep['distances']['legacy_mean']} | {rep['distances']['continuous_mean']} |",
         f"| Pairs at distance 0 | {rep['distances']['legacy_zero_pairs']} of 78 | {rep['distances']['continuous_zero_pairs']} of 78 |",
         f"| Pairs closer than a quarter of the median distance (scale-free) | {len(rep['distances']['legacy_near_pairs'])} | {len(rep['distances']['continuous_near_pairs'])} |",
         f"| Closest pair (continuous) | | {rep['distances']['continuous_min'][0]} ({rep['distances']['continuous_min'][1]}) |",
         f"| Unresolved dimensions (share of 78) | {rep['unresolved_share']['legacy']} | {rep['unresolved_share']['continuous']} |", "",
         "### C.2 Dimension coverage (brands with a resolved dimension / target)", "",
         "| Dimension | Legacy | Continuous |", "|---|---|---|"]
    L += [f"| {short[a]} | {v['legacy']} | {v['continuous']} |" for a, v in rep["coverage"].items()]
    L += ["", "### C.3 Per brand (continuous)", "",
          "| Brand | Outcome | Leading motifs (score) | " + " | ".join(short[a] for a in AXES) + " | Legacy targets |",
          "|---|---|---|" + "---|" * len(AXES) + "---|"]
    for n, b in B.items():
        cells = []
        for a in AXES:
            x = b["axes"][a]
            cells.append(f"{x['label']} · {x['confidence_word']}" if x["state"] == "resolved" else ("open, pulls both ways" if x["state"] == "balanced_open" else "open"))
        lead = ", ".join(f"{m} {s:.2f}" for m, s in b["leading"]) or "none"
        tg = ", ".join(s for s in b["legacy_signature"] if s != "open") or "none"
        L.append(f"| {n} | {b['outcome']} | {lead} | " + " | ".join(cells) + f" | {tg} |")
    L += ["", "### C.4 Named pairs", "", "| Pair | Legacy distance | Continuous distance | Same resolved labels |", "|---|---|---|---|"]
    L += [f"| {p} | {v['legacy']} | {v['continuous']} | {'yes' if v['same_labels'] else 'no'} |" for p, v in rep["pairs"].items()]
    L += [f"| Sanrio vs nearest ({rep['sanrio_nearest'][0]}) | | {rep['sanrio_nearest'][1]} | |", "",
          "### C.5 Stability", "", "| Brand | Related entities | Max move, one entity removed | Mean move | Label changes | Minor contributing motif dropped (score < 0.3) | Move | Label change |",
          "|---|---|---|---|---|---|---|---|"]
    for n, b in B.items():
        s, d = b["sensitivity"], b["drop_weakest"] or {}
        L.append(f"| {n} | {s['related_entities']} | {s['max_move']} | {s['mean_move']} | {s['label_flips']} | "
                 f"{d.get('motif', '—')} ({d.get('score', 0):.2f}) | {d.get('move', 0)} | {'yes' if d.get('label_change') else 'no'} |")
    L += ["", "### C.6 Share of all contributions by motif (13 brands)", "", "| Motif | Share |", "|---|---|"]
    L += [f"| {m} | {v:.3f} |" for m, v in rep["motif_share"].items()]
    return "\n".join(L) + "\n"

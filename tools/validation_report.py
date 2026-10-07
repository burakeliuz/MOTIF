"""Phase 10 final validation, offline: the frozen legacy engine, the continuous engine with its
scent architecture, and an existing LLM-only baseline, from stored recordings only.

  python3 tools/validation_report.py [--write reports/final_validation.md] [--json PATH]
  python3 tools/validation_report.py --hash   (prints the SHA-256 of the 13 product-path results)

No Qloo request and no LLM call: Qloo responses come from the git-ignored recordings that
tools/collapse_analysis.py and tools/holdout_run.py name; the LLM-only outputs are the ones the
stage-6B trial stored in data/eval_6b/ (arm C, `claude-sonnet-5-5`, no Qloo data).

1. Determinism and repeatability: the 13 brands run twice in this process (identical canonical
   JSON), and once more in two fresh interpreters with different hash seeds (same SHA-256).
2. Collapse, stage by stage: distinct per-brand sets for the legacy engine (from the frozen
   baseline) next to the continuous engine on the product path (the continuous controller,
   exactly as the web app runs it).
3. Separation: pairwise commitment distances; overlap (Jaccard) of the chosen directions
   between brands, next to the overlap of the legacy selected materials.
4. Perturbation: each annotated descriptor left out once, and each related entity left out once:
   how often the resolved labels or the scent architecture change, and the largest move.
5. Holdout: the five pre-registered brands, replayed (the olfactory layer was built after that
   run and never saw these brands, so their architectures are an out-of-sample structure check).
6. LLM-only baseline: per dimension, how often each method commits to a pole, and agreement where
   two methods both commit. The LLM-only arm is a reference point, not ground truth.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from collapse_analysis import BRANDS  # noqa: E402  (input map only)
from continuous_report import medium_only, signature  # noqa: E402
from motif.agent import Controller  # noqa: E402
from motif.config import AXES, load_config, load_continuous_config  # noqa: E402
from motif.continuous import commitment, run_continuous  # noqa: E402
from motif.qloo import RecordedQloo  # noqa: E402

BASELINE = ROOT / "reports" / "baselines" / "legacy_engine_0.3.json"
LLM_ONLY = ROOT / "data" / "eval_6b"
LLM_DIMS = {"temperature": "warm_cool", "weight": "light_dense", "texture": "raw_polished",
            "impression": "natural_synthetic", "projection": "intimate_projecting", "sweetness": "sweet_dry"}
ROLES = ("opening", "core", "drydown")


def available() -> bool:
    return all(dirs and all(Path(d).exists() for d in dirs) for dirs, _, _ in BRANDS.values())


def canonical(x: Any) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def product_runs(cfg=None, cc=None) -> Dict[str, Dict[str, Any]]:
    """Every trial brand through the continuous controller on its recordings (the web app's path)."""
    cfg, cc = cfg or load_config(), cc or load_continuous_config()
    out = {}
    for name, (dirs, choose, _overrides) in BRANDS.items():
        access = RecordedQloo(dirs, None, 99)
        o = Controller(access, cfg, name, "brand", choose, list(cfg.params["default_domains"]),
                       engine="continuous", continuous=cc).run()
        if access.network_attempts:
            raise RuntimeError(f"{name}: the replay tried the network")
        out[name] = o["result"]
    return out


def legacy_runs(cfg=None) -> Dict[str, Dict[str, Any]]:
    cfg = cfg or load_config()
    out = {}
    for name, (dirs, choose, overrides) in BRANDS.items():
        access = RecordedQloo(dirs, None, 99)
        out[name] = Controller(access, cfg, name, "brand", choose, overrides=overrides).run()["result"]
    return out


def results_hash(results: Dict[str, Dict[str, Any]]) -> str:
    return hashlib.sha256(canonical(results).encode("utf-8")).hexdigest()


def architecture_key(r: Dict[str, Any]) -> Tuple[Optional[str], ...]:
    s = (r.get("architecture") or {}).get("structure") or {}
    return tuple((s.get(role) or {}).get("direction") for role in ROLES)


def chosen(r: Dict[str, Any]) -> set:
    return {d for d in architecture_key(r) if d}


def jaccard(a: set, b: set) -> Optional[float]:
    """Overlap of two proposals; None unless both propose something (an empty proposal is not 'different')."""
    return len(a & b) / len(a | b) if a and b else None


def spearman(xs: List[float], ys: List[float]) -> Optional[float]:
    """Rank correlation with average ranks for ties."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return round(num / den, 3) if den else None


def pole_of(axis_result: Dict[str, Any]) -> Optional[str]:
    return axis_result.get("pole") if axis_result["state"] == "resolved" else None


def _rerun(evidence, cc):
    return run_continuous(evidence, cc.lexicon, cc.scoring, cc.vectors, cc.params, library=cc.library)


def perturbation(r: Dict[str, Any], cc) -> Dict[str, Any]:
    sig, arch, base = signature(r["axes"]), architecture_key(r), commitment(r["axes"])
    annotated = sorted({a["evidence_id"] for a in r["annotations"]})
    related = sorted({str(e["entity_id"]) for e in r["evidence"] if e["source_kind"] != "own"})
    out = {}
    for kind, units, drop in (("descriptor", annotated, lambda ev, u: [e for e in ev if e["evidence_id"] != u]),
                              ("related_entity", related, lambda ev, u: [e for e in ev if str(e["entity_id"]) != u])):
        label, structure, moves = 0, 0, []
        for u in units:
            alt = _rerun(drop(r["evidence"], u), cc)
            label += signature(alt["axes"]) != sig
            structure += architecture_key(alt) != arch
            moves.append(math.dist(base, commitment(alt["axes"])))
        out[kind] = {"runs": len(units), "label_changes": label, "architecture_changes": structure,
                     "max_move": round(max(moves, default=0.0), 4)}
    return out


def llm_only() -> Dict[str, Dict[str, Optional[str]]]:
    """Structured arm-C outputs only (the first trial's arm C was free text and is not parsed)."""
    out = {}
    for f in sorted(LLM_ONLY.glob("c*_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        direction = (d.get("brief") or {}).get("direction")
        if direction:
            out[d["brand"]] = {LLM_DIMS[k]: (None if v == "open" else v) for k, v in direction.items()}
    return out


def agreement(x: Dict[str, Optional[str]], y: Dict[str, Optional[str]]) -> Dict[str, int]:
    both = [a for a in AXES if x.get(a) and y.get(a)]
    return {"both_commit": len(both), "same_pole": sum(x[a] == y[a] for a in both),
            "opposite_pole": sum(x[a] != y[a] for a in both)}


def build() -> Dict[str, Any]:
    cfg, cc = load_config(), load_continuous_config()
    cont = product_runs(cfg, cc)
    again = product_runs(cfg, cc)
    legacy = legacy_runs(cfg)
    names = list(cont)

    # 1. determinism and repeatability
    h = results_hash(cont)
    fresh = {}
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--hash"], capture_output=True, text=True, env=env, timeout=600)
        fresh[seed] = run.stdout.strip()
    import holdout_run
    determinism = {"in_process_identical": canonical(cont) == canonical(again), "sha256": h,
                   "fresh_interpreters": fresh, "repeatable": all(v == h for v in fresh.values()),
                   "traceable": [n for n in names if holdout_run.traceable(cont[n])]}

    # 2. collapse, stage by stage
    base = json.loads(BASELINE.read_text(encoding="utf-8"))

    def distinct(f) -> int:
        return len({f(cont[n]) for n in names})
    collapse = {
        "legacy": base["unique_per_stage"],
        "continuous": {
            # the first two stages use the legacy baseline's definitions (tools/legacy_baseline.py signature)
            "qloo_descriptors": distinct(lambda r: tuple(sorted({e["tag_name"].strip().lower() for e in r["evidence"]}))),
            "cue_groups": distinct(lambda r: tuple(sorted({a["cue_id"] for a in r["annotations"]}))),
            "leading_motifs": distinct(lambda r: tuple(sorted(r["leading_motifs"]))),
            "resolved_profiles": distinct(lambda r: signature(r["axes"])),
            "eligible_directions": distinct(lambda r: tuple(sorted(x["id"] for x in r["architecture"]["ranking"] if x["eligible"]))),
            "architectures": distinct(architecture_key),
        },
        "collisions": {
            "resolved_profiles": [g for g in _groups(names, lambda n: signature(cont[n]["axes"])) if len(g) > 1],
            "architectures": [g for g in _groups(names, lambda n: architecture_key(cont[n])) if len(g) > 1],
        },
        "no_architecture": [n for n in names if cont[n]["architecture"]["status"] != "proposed"],
        "tentative_only": [n for n in names if cont[n]["architecture"]["basis"] == "tentative"],
    }

    # 3. separation
    dists = {f"{x} – {y}": round(math.dist(commitment(cont[x]["axes"]), commitment(cont[y]["axes"])), 4)
             for x, y in itertools.combinations(names, 2)}
    jd = [jaccard(chosen(cont[x]), chosen(cont[y])) for x, y in itertools.combinations(names, 2)]
    jl = [jaccard({m["material_id"] for m in legacy[x]["materials"].get("selected", [])},
                  {m["material_id"] for m in legacy[y]["materials"].get("selected", [])}) for x, y in itertools.combinations(names, 2)]
    use = Counter()
    for n in names:
        use.update(chosen(cont[n]))
    vals = sorted(dists.values())
    separation = {"distance_min": min(dists.items(), key=lambda kv: kv[1]), "distance_median": round(statistics.median(vals), 4),
                  "near_pairs": sorted(k for k, v in dists.items() if v < 0.25 * statistics.median(vals)),
                  "direction_overlap_mean": round(statistics.mean([j for j in jd if j is not None]), 3),
                  "direction_overlap_pairs": sum(j is not None for j in jd),
                  "legacy_material_overlap_mean": round(statistics.mean([j for j in jl if j is not None]), 3),
                  "legacy_material_overlap_pairs": sum(j is not None for j in jl),
                  "directions_used": len(use), "direction_use": dict(sorted(use.items(), key=lambda kv: (-kv[1], kv[0])))}

    # is the differentiation forced? (a) without the low-confidence design cells; (b) does shared
    # Qloo evidence go with shared directions? Spearman over brand pairs that both propose something
    med = type(cc)(cc.lexicon, cc.scoring, medium_only(cc.vectors), cc.params, cc.library)
    ablated = {n: _rerun(cont[n]["evidence"], med) for n in names}
    tags = {n: {e["tag_name"].strip().lower() for e in cont[n]["evidence"]} for n in names}
    both = [(x, y) for x, y in itertools.combinations(names, 2) if chosen(cont[x]) and chosen(cont[y])]
    separation["medium_cells_only"] = {"profiles": len({signature(ablated[n]["axes"]) for n in names}),
                                       "architectures": len({architecture_key(ablated[n]) for n in names}),
                                       "no_architecture": [n for n in names if ablated[n]["architecture"]["status"] != "proposed"]}
    separation["evidence_tracking"] = {
        "pairs": len(both),
        "spearman_descriptor_overlap_vs_direction_overlap": spearman([jaccard(tags[x], tags[y]) for x, y in both],
                                                                     [jaccard(chosen(cont[x]), chosen(cont[y])) for x, y in both]),
        "spearman_descriptor_overlap_vs_commitment_distance": spearman(
            [jaccard(tags[x], tags[y]) for x, y in itertools.combinations(names, 2)],
            [math.dist(commitment(cont[x]["axes"]), commitment(cont[y]["axes"])) for x, y in itertools.combinations(names, 2)])}

    # 4. perturbation
    pert = {n: perturbation(cont[n], cc) for n in names}
    totals = {k: {m: sum(p[k][m] for p in pert.values()) for m in ("runs", "label_changes", "architecture_changes")}
              for k in ("descriptor", "related_entity")}

    # 5. holdout (post hoc for the olfactory layer)
    holdout = _holdout(cfg, cc)

    # 6. LLM-only baseline
    c = llm_only()
    methods = {}
    for b in c:
        if b in cont:
            methods[b] = {"continuous": {a: pole_of(cont[b]["axes"][a]) for a in AXES},
                          "legacy": {a: (legacy[b]["axes"][a]["value"] if legacy[b]["axes"][a]["state"] == "target" else None) for a in AXES},
                          "llm_only": c[b]}
    pairs = {}
    for x, y in (("continuous", "llm_only"), ("legacy", "llm_only"), ("continuous", "legacy")):
        rows = [agreement(methods[b][x], methods[b][y]) for b in methods]
        pairs[f"{x} vs {y}"] = {k: sum(r[k] for r in rows) for k in ("both_commit", "same_pole", "opposite_pole")}
    committed = {m: sum(1 for b in methods for a in AXES if methods[b][m][a]) for m in ("continuous", "legacy", "llm_only")}
    llm = {"brands": sorted(methods), "per_brand": methods, "committed": committed, "of": 6 * len(methods), "agreement": pairs,
           "distinct_profiles": {m: len({tuple(methods[b][m][a] for a in AXES) for b in methods}) for m in ("continuous", "legacy", "llm_only")}}

    return {"brands": names, "determinism": determinism, "collapse": collapse, "separation": separation,
            "perturbation": {"per_brand": pert, "totals": totals}, "holdout": holdout, "llm_only": llm,
            "profiles": {n: {"leading": cont[n]["leading_motifs"],
                             "labels": {a: (f"{cont[n]['axes'][a]['label']} · {cont[n]['axes'][a]['confidence_word']}"
                                            if cont[n]["axes"][a]["state"] == "resolved" else cont[n]["axes"][a]["state"]) for a in AXES},
                             "architecture": dict(zip(ROLES, architecture_key(cont[n]))),
                             "basis": cont[n]["architecture"]["basis"]} for n in names},
            "versions": cc.versions}


def _groups(names, key) -> List[List[str]]:
    g: Dict[Any, List[str]] = {}
    for n in names:
        g.setdefault(key(n), []).append(n)
    return list(g.values())


def _holdout(cfg, cc) -> Optional[Dict[str, Any]]:
    import holdout_run
    runs = sorted((ROOT / "data" / "motif_sessions").glob("holdout-*"))
    if not runs:
        return None
    rows = {}
    for name in holdout_run.BRANDS:
        rec = holdout_run.replay(runs[-1], name, cfg, cc)
        r = rec["outcome"].get("result")
        if not r:
            rows[name] = {"status": rec["outcome"]["status"], "outcome": rec["outcome"].get("outcome")}
            continue
        again = _rerun(r["evidence"], cc)
        rows[name] = {"status": rec["outcome"]["status"], "outcome": r["outcome"],
                      "labels": {a: (f"{r['axes'][a]['label']} · {r['axes'][a]['confidence_word']}" if r["axes"][a]["state"] == "resolved"
                                     else r["axes"][a]["state"]) for a in AXES},
                      "architecture": dict(zip(ROLES, architecture_key(r))), "basis": r["architecture"]["basis"],
                      "emphasize": [x["direction"] for x in r["architecture"]["emphasize"]],
                      "avoid": [x["direction"] for x in r["architecture"]["avoid"]],
                      "traceable": holdout_run.traceable(r),
                      "deterministic": canonical(again["axes"]) == canonical(r["axes"]) and architecture_key(again) == architecture_key(r)}
    done = [n for n, v in rows.items() if "architecture" in v]
    return {"run": runs[-1].name, "brands": rows,
            "distinct_architectures": len({tuple(rows[n]["architecture"].values()) for n in done}),
            "same_architecture": [g for g in _groups(done, lambda n: tuple(rows[n]["architecture"].values())) if len(g) > 1]}


def markdown(rep: Dict[str, Any]) -> str:
    d, c, s, p, h, l = (rep[k] for k in ("determinism", "collapse", "separation", "perturbation", "holdout", "llm_only"))
    lines = ["# Final validation (phase 10)", "",
             "Generated by `python3 tools/validation_report.py --write reports/final_validation.md` from stored",
             "recordings only: no Qloo request, no LLM call. Versions: " + ", ".join(f"`{v}`" for v in rep["versions"].values()) + ".",
             "Methods and limits: `docs/VALIDATION.md`.", "",
             "## 1. Determinism and repeatability", "",
             f"- Two runs of the 13 brands in one process: {'identical' if d['in_process_identical'] else '**different**'}.",
             f"- Fresh interpreters with hash seeds 1 and 2: {'same SHA-256' if d['repeatable'] else '**different hashes**'} "
             f"(`{d['sha256'][:16]}…`).",
             f"- Every contributor of every resolved dimension maps to Qloo evidence with a request ID and a JSON pointer: "
             f"{len(d['traceable'])} of {len(rep['brands'])} brands.", "",
             "## 2. Collapse, stage by stage (13 trial brands, distinct per-brand sets)", "",
             "| Stage | Legacy engine-0.3 | Continuous engine (product path) |", "|---|---|---|"]
    lg, ct = c["legacy"], c["continuous"]
    for label, lk, ck in (("Qloo descriptors", "qloo_descriptors", "qloo_descriptors"), ("Lexicon cue groups", "cue_groups", "cue_groups"),
                          ("Active / leading motifs", "active_motifs", "leading_motifs"), ("Sensory profile", "sensory_targets", "resolved_profiles"),
                          ("Eligible materials / directions", "eligible_materials", "eligible_directions"),
                          ("Selected materials / scent architecture", "selected_materials", "architectures")):
        lines.append(f"| {label} | {lg[lk]} | {ct[ck]} |")
    lines += ["", "Collisions (continuous): profiles " + (", ".join(" = ".join(g) for g in c["collisions"]["resolved_profiles"]) or "none")
              + "; architectures " + (", ".join(" = ".join(g) for g in c["collisions"]["architectures"]) or "none") + ".",
              f"No architecture: {', '.join(c['no_architecture']) or 'none'}. Architecture resting on tentative leanings only: "
              f"{', '.join(c['tentative_only']) or 'none'}.", "",
              "## 3. Separation", "",
              f"- Pairwise commitment distance: minimum {s['distance_min'][1]} ({s['distance_min'][0]}), median {s['distance_median']}; "
              f"pairs closer than a quarter of the median: {', '.join(s['near_pairs']) or 'none'}.",
              f"- Mean overlap (Jaccard) between two brands that both propose something: chosen directions "
              f"{s['direction_overlap_mean']} ({s['direction_overlap_pairs']} pairs); legacy selected materials "
              f"{s['legacy_material_overlap_mean']} ({s['legacy_material_overlap_pairs']} pairs).",
              f"- Directions used across the 13 architectures: {s['directions_used']} of 23; most used: "
              + ", ".join(f"{k} ({v})" for k, v in list(s["direction_use"].items())[:4]) + ".",
              f"- Without the low-confidence (tentative) design cells: {s['medium_cells_only']['profiles']} distinct profiles and "
              f"{s['medium_cells_only']['architectures']} distinct architectures; no architecture for "
              f"{', '.join(s['medium_cells_only']['no_architecture']) or 'none'}.",
              f"- Does shared Qloo evidence go with shared output? Spearman between the overlap of two brands' Qloo descriptors and "
              f"the overlap of their chosen directions: {s['evidence_tracking']['spearman_descriptor_overlap_vs_direction_overlap']} "
              f"({s['evidence_tracking']['pairs']} pairs); with their commitment distance: "
              f"{s['evidence_tracking']['spearman_descriptor_overlap_vs_commitment_distance']} (78 pairs; negative means more shared "
              "descriptors, closer profiles).", "",
              "## 4. Perturbation (one unit left out at a time)", "",
              "| Unit left out | Runs | Resolved labels change | Architecture changes |", "|---|---|---|---|"]
    for k, label in (("descriptor", "one annotated Qloo descriptor"), ("related_entity", "one related brand or film")):
        t = p["totals"][k]
        lines.append(f"| {label} | {t['runs']} | {t['label_changes']} ({_pct(t['label_changes'], t['runs'])}) | "
                     f"{t['architecture_changes']} ({_pct(t['architecture_changes'], t['runs'])}) |")
    lines += ["", "| Brand | Descriptor runs: label / architecture changes, max move | Related-entity runs: label / architecture changes, max move |",
              "|---|---|---|"]
    for n, v in p["per_brand"].items():
        a, b = v["descriptor"], v["related_entity"]
        lines.append(f"| {n} | {a['runs']}: {a['label_changes']} / {a['architecture_changes']}, {a['max_move']} | "
                     f"{b['runs']}: {b['label_changes']} / {b['architecture_changes']}, {b['max_move']} |")
    lines += ["", "## 5. Holdout brands (replayed; architecture is post hoc)", ""]
    if h:
        lines += [f"Run `{h['run']}`. Distinct architectures among the resolved brands: {h['distinct_architectures']}"
                  + (f"; shared: {', '.join(' = '.join(g) for g in h['same_architecture'])}" if h["same_architecture"] else "") + ".", "",
                  "| Brand | Outcome | Resolved dimensions | Opening / core / drydown | Basis | Traceable | Deterministic |", "|---|---|---|---|---|---|---|"]
        for n, v in h["brands"].items():
            if "architecture" not in v:
                lines.append(f"| {n} | {v['status']} / {v['outcome']} | — | — | — | — | — |")
                continue
            res = "; ".join(f"{x}" for x in v["labels"].values() if "·" in x) or "none"
            arch = " / ".join(x or "open" for x in v["architecture"].values())
            lines.append(f"| {n} | {v['outcome']} | {res} | {arch} | {v['basis'] or '—'} | {v['traceable']} | {v['deterministic']} |")
    else:
        lines.append("Holdout recordings not on disk (data/ is git-ignored); see `reports/continuous_holdout.md`.")
    lines += ["", "## 6. LLM-only baseline (existing outputs, no new call)", "",
              f"Brands with a structured LLM-only answer: {', '.join(l['brands'])} (stage-6B arm C). Committed dimensions out of {l['of']}: "
              + ", ".join(f"{k} {v}" for k, v in l["committed"].items()) + ". Distinct profiles among them: "
              + ", ".join(f"{k} {v}" for k, v in l["distinct_profiles"].items()) + ".", "",
              "| Pair | Both commit | Same pole | Opposite pole |", "|---|---|---|---|"]
    for k, v in l["agreement"].items():
        lines.append(f"| {k} | {v['both_commit']} | {v['same_pole']} | {v['opposite_pole']} |")
    lines += ["", "| Brand | Method | " + " | ".join(AXES) + " |", "|---|---|" + "---|" * len(AXES)]
    for b in l["brands"]:
        for m in ("legacy", "continuous", "llm_only"):
            lines.append(f"| {b} | {m} | " + " | ".join(l["per_brand"][b][m][a] or "open" for a in AXES) + " |")
    lines += ["", "## 7. Profiles and architectures (13 trial brands, product path)", "",
              "| Brand | Leading motifs | Resolved dimensions | Opening / core / drydown | Basis |", "|---|---|---|---|---|"]
    for n, v in rep["profiles"].items():
        res = "; ".join(x for x in v["labels"].values() if "·" in x) or "none"
        lines.append(f"| {n} | {', '.join(v['leading']) or '—'} | {res} | {' / '.join(x or 'open' for x in v['architecture'].values())} | {v['basis'] or '—'} |")
    return "\n".join(lines) + "\n"


def _pct(a: int, b: int) -> str:
    return f"{round(100 * a / b)}%" if b else "—"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write")
    ap.add_argument("--json")
    ap.add_argument("--hash", action="store_true")
    args = ap.parse_args(argv)
    if not available():
        print("recordings not on disk (data/ is git-ignored); nothing to validate", file=sys.stderr)
        return 2
    if args.hash:
        print(results_hash(product_runs()))
        return 0
    rep = build()
    if args.json:
        Path(args.json).write_text(json.dumps(rep, indent=1, ensure_ascii=False, sort_keys=True, default=list) + "\n", encoding="utf-8")
    text = markdown(rep)
    if args.write:
        Path(args.write).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

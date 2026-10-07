"""Offline comparison of the legacy rule engine and the continuous engine on the 13 trial brands.

Replays the stored Qloo responses (RecordedQloo: no network, no LLM). Both engines read
exactly the same evidence: the legacy controller's own fetches (own entry, related
brands, related films for all 13 brands; no domain was skipped).

  python3 tools/engine_compare.py scores [--markdown OUT.md]     # phase 4: motif scores
  python3 tools/engine_compare.py analysis [--markdown OUT.md] [--json OUT.json]   # phase 6

Needs the git-ignored recordings under data/ (tools/collapse_analysis.py BRANDS).
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from collapse_analysis import BRANDS  # noqa: E402  (input map only)
from legacy_baseline import replay, signature  # noqa: E402
from motif.config import AXES, load_config  # noqa: E402
from motif.scoring import score_motifs  # noqa: E402

PAIRS = [("MUJI", "Aesop"), ("MUJI", "Le Labo"), ("A24", "Supreme"), ("Gucci", "Balenciaga"),
         ("Ralph Lauren", "Harley-Davidson")]
CHECKS = [("A24", "Comme des Garçons", "provocative"), ("Gucci", "Balenciaga", "provocative"),
          ("MUJI", "Aesop", None), ("Ralph Lauren", None, "heritage"), ("Harley-Davidson", None, "heritage"),
          ("Sanrio", None, "playful")]


def load_json(name: str) -> Dict[str, Any]:
    return json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))


def legacy_results() -> Dict[str, Dict[str, Any]]:
    cfg = load_config()
    return {name: replay(name, cfg)["result"] for name in BRANDS}


def drop_entity(annotations: Sequence[Dict[str, Any]], entity_id: str) -> List[Dict[str, Any]]:
    return [a for a in annotations if str(a["entity_id"]) != str(entity_id)]


def score_table(results: Dict[str, Dict[str, Any]], scoring: Dict[str, Any]) -> Dict[str, Any]:
    """Per brand and motif: score and its inputs, plus the largest change when one related entity is removed."""
    rows: Dict[str, List[Dict[str, Any]]] = {}
    for name, r in results.items():
        scores = score_motifs(r["annotations"], scoring)
        related = sorted({str(a["entity_id"]) for a in r["annotations"] if a["source_kind"] != "own"})
        out = []
        for m, s in sorted(scores.items(), key=lambda kv: (-kv[1]["score"], kv[0])):
            worst = 0.0
            for e in related:
                alt = score_motifs(drop_entity(r["annotations"], e), scoring).get(m, {"score": 0.0})["score"]
                worst = max(worst, abs(alt - s["score"]))
            out.append({"motif": m, "score": s["score"], "own_cue_groups": len(s["channels"].get("own", {}).get("cue_groups", [])),
                        "related_entities": s["related_entities"], "cue_groups": len(s["cue_groups"]),
                        "source_kinds": s["source_kinds"], "common_only": s["common_only"],
                        "legacy_strength": r["motifs"].get(m, {}).get("strength"), "max_drop_one_entity": round(worst, 6)})
        rows[name] = out
    return rows


def scores_markdown(rows: Dict[str, List[Dict[str, Any]]]) -> str:
    L = ["| Brand | Motif | Score | Own cue groups | Related entities | Cue groups | Source kinds | Legacy strength | Max change, one related entity removed |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, out in rows.items():
        for r in out:
            kinds = ", ".join(r["source_kinds"]) or "common cues only"
            L.append(f"| {name} | {r['motif']} | {r['score']:.3f} | {r['own_cue_groups']} | {r['related_entities']} | {r['cue_groups']} | "
                     f"{kinds} | {r['legacy_strength']} | {r['max_drop_one_entity']:.3f} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["scores", "analysis"])
    ap.add_argument("--markdown")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    results = legacy_results()
    if args.command == "scores":
        rows = score_table(results, load_json("motif_scoring.v1.json"))
        text = scores_markdown(rows)
        if args.json:
            Path(args.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    else:
        from continuous_report import analysis, analysis_markdown  # noqa: E402  (phase 6)
        rep = analysis(results)
        text = analysis_markdown(rep)
        if args.json:
            Path(args.json).write_text(json.dumps(rep, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Frozen baseline of the legacy rule engine (engine-0.3, rules draft-0.2) on the 13 trial brands.

Replays the stored Qloo responses (RecordedQloo: no network, no LLM) through the
unchanged legacy engine and writes, per brand, the set reached at every stage:
consumed Qloo descriptors -> lexicon cue groups -> active motifs -> sensory targets ->
eligible materials -> selected materials. The counts of distinct per-brand sets are
recomputed here from the stage definitions below; they do not reuse
tools/collapse_analysis.py (only its BRANDS input map, so both read the same runs).

  python3 tools/legacy_baseline.py [--write reports/baselines/legacy_engine_0.3.json]

The written file also records the SHA-256 of the four legacy config files, so a later
change to them cannot pass silently (tests/test_legacy_baseline.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from collapse_analysis import BRANDS  # noqa: E402  (input map only)
from motif import ENGINE_VERSION  # noqa: E402
from motif.agent import Controller  # noqa: E402
from motif.config import load_config  # noqa: E402
from motif.qloo import RecordedQloo  # noqa: E402

LEGACY_CONFIG_FILES = ("motif_lexicon.json", "draft_rules.json", "material_palette.json", "engine_params.json")
STAGES = ("qloo_descriptors", "cue_groups", "active_motifs", "sensory_targets", "eligible_materials", "selected_materials")


def available() -> bool:
    """True when every recording the 13 brands need is on disk (git-ignored data/)."""
    return all(all(Path(d).exists() for d in dirs) and dirs for dirs, _, _ in BRANDS.values())


def replay(name: str, cfg) -> Dict[str, Any]:
    """The legacy controller's outcome for one brand, from recordings only."""
    dirs, choose, overrides = BRANDS[name]
    access = RecordedQloo(dirs, None, 99)
    out = Controller(access, cfg, name, "brand", choose, overrides=overrides).run()
    if access.network_attempts:
        raise RuntimeError(f"{name}: the replay tried the network")
    return out


def signature(result: Dict[str, Any]) -> Dict[str, List[str]]:
    """What one brand keeps at each stage, as sorted lists (the unit of the uniqueness count)."""
    return {
        "qloo_descriptors": sorted({e["tag_name"].strip().lower() for e in result["evidence"]}),
        "cue_groups": sorted({a["cue_id"] for a in result["annotations"]}),
        "active_motifs": sorted(m for m, i in result["motifs"].items() if i["active"]),
        "sensory_targets": sorted(f"{a}={v['value']}" for a, v in result["axes"].items() if v["state"] == "target"),
        "eligible_materials": sorted(m["material_id"] for m in result["materials"].get("ranked", [])),
        "selected_materials": sorted(m["material_id"] for m in result["materials"].get("selected", [])),
    }


def config_hashes() -> Dict[str, str]:
    return {f: hashlib.sha256((ROOT / "config" / f).read_bytes()).hexdigest() for f in LEGACY_CONFIG_FILES}


def build() -> Dict[str, Any]:
    cfg = load_config()
    brands = {}
    for name in BRANDS:
        out = replay(name, cfg)
        r = out["result"]
        brands[name] = {"status": out["status"], "outcome": r["outcome"], "evidence_count": r["evidence_count"],
                        "stages": signature(r)}
    unique = {s: len({json.dumps(b["stages"][s]) for b in brands.values()}) for s in STAGES}
    return {"engine": ENGINE_VERSION, "versions": cfg.versions, "config_sha256": config_hashes(),
            "brands_count": len(brands), "unique_per_stage": unique, "brands": brands,
            "note": "Frozen legacy baseline. Recomputed from recordings by tools/legacy_baseline.py; "
                    "the counts are distinct per-brand sets at each stage."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", help="write the baseline JSON here")
    args = ap.parse_args(argv)
    if not available():
        print("recordings for the 13 brands are not on disk (data/ is git-ignored)", file=sys.stderr)
        return 2
    base = build()
    print(" / ".join(f"{s} {n}" for s, n in base["unique_per_stage"].items()))
    if args.write:
        Path(args.write).parent.mkdir(parents=True, exist_ok=True)
        Path(args.write).write_text(json.dumps(base, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

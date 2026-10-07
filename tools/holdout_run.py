"""Pre-registered holdout of the continuous engine (reports/continuous_holdout.md).

  python3 tools/holdout_run.py live [--out DIR]       # live Qloo, at most 4 network attempts per brand
  python3 tools/holdout_run.py evaluate RUN_DIR [--json OUT] [--markdown OUT]   # offline, from the saved responses

Live mode sends real Qloo requests through motif/qloo.py LiveQloo with motif_spike's
DirectTransport (the only allowed integration), one access object per brand with a hard cap
of 4 network attempts (retries included), so a brand never costs more than 4 and the run
never more than 20. An entity question is answered by the pre-registered rule below, inside
the same access object, so the repeated search is served from the session cache. No LLM is
called. Evaluation replays the saved responses (RecordedQloo) and sends nothing.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from motif.agent import Controller  # noqa: E402
from motif.config import AXES, load_config, load_continuous_config  # noqa: E402
from motif.continuous import commitment, run_continuous  # noqa: E402
from motif.qloo import LiveQloo, RecordedQloo  # noqa: E402
from motif_spike.util import iso, utc_now, write_json  # noqa: E402

BRANDS = ["IKEA", "Hermès", "Bang & Olufsen", "LEGO", "Coca-Cola"]
MAX_PER_BRAND = 4


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s.casefold()) if not unicodedata.combining(c)).strip()


def choose_rule(name: str, options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pre-registered: the first returned brand whose name equals the input (case and accents folded);
    otherwise the first returned brand; otherwise none (the brand is reported as unresolved)."""
    brands = [o for o in options if "urn:entity:brand" in (o.get("types") or [])]
    exact = [o for o in brands if fold(o["name"]) == fold(name)]
    return (exact or brands or [None])[0]


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in fold(name)).strip("-")


def run_brand(access, config, cc, name: str) -> Dict[str, Any]:
    out = Controller(access, config, name, "brand", engine="continuous", continuous=cc).run()
    choice = None
    q = out.get("question") or {}
    if out["status"] == "needs_choice" and q.get("kind") == "choose_entity":
        picked = choose_rule(name, q["options"])
        choice = {"rule": choose_rule.__doc__.strip(), "picked": picked, "options": q["options"]}
        if picked:
            out = Controller(access, config, name, "brand", picked["qloo_id"], engine="continuous", continuous=cc).run()
    return {"outcome": out, "choice": choice}


def cmd_live(args) -> int:
    from motif_spike.manifest import harness_environment, live_environment, load_manifest
    from motif_spike.readiness import check_direct_readiness
    from motif_spike.transport import DirectTransport, direct_api_key
    config, cc = load_config(), load_continuous_config()
    env = live_environment(harness_environment(load_manifest()))
    ready = check_direct_readiness(env)
    if not ready.live_ready:
        print("live access is not ready; nothing was sent", file=sys.stderr)
        return 2
    budget = config.params["budget"]
    out_dir = Path(args.out or ROOT / "data" / "motif_sessions" / f"holdout-{utc_now().strftime('%Y%m%dT%H%M%SZ')}")
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for name in BRANDS:
        session_dir = out_dir / slug(name)
        transport = DirectTransport(ready.base_url, api_key=direct_api_key(env), timeout_s=budget["timeout_s"])
        access = LiveQloo(transport, ready.base_url, session_dir, MAX_PER_BRAND, budget["max_retries"],
                          budget["retry_backoff_s"], budget["timeout_s"])
        rec = run_brand(access, config, cc, name)
        total += access.network_attempts
        o = rec["outcome"]
        write_json(session_dir / "holdout.json", {"brand": name, "at": iso(utc_now()), "network_attempts": access.network_attempts,
                                                  "status": o["status"], "outcome": o.get("outcome"), "message": o.get("message"),
                                                  "resolution": o.get("resolution"), "choice": rec["choice"], "trace": o["trace"]})
        print(f"{name}: {o['status']} / {o.get('outcome')}; network attempts {access.network_attempts} (run total {total})")
    print(f"saved: {out_dir}")
    return 0


def replay(run_dir: Path, name: str, config, cc) -> Dict[str, Any]:
    d = run_dir / slug(name)
    meta = json.loads((d / "holdout.json").read_text(encoding="utf-8"))
    picked = ((meta.get("choice") or {}).get("picked") or {}).get("qloo_id")
    out = Controller(RecordedQloo(d, None, 99), config, name, "brand", picked, engine="continuous", continuous=cc).run()
    return {"meta": meta, "outcome": out}


def traceable(result: Dict[str, Any]) -> bool:
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    for a in AXES:
        for c in result["axes"][a]["contributors"]:
            rows = [x for x in result["annotations"] if x["motif"] == c["motif"] and x["role"] == "support"]
            if not rows or any(x["evidence_id"] not in ev or not ev[x["evidence_id"]].get("request_id")
                               or not ev[x["evidence_id"]].get("json_pointer") for x in rows):
                return False
    return True


def cmd_evaluate(args) -> int:
    import continuous_report
    import engine_compare
    import legacy_baseline
    config, cc = load_config(), load_continuous_config()
    run_dir = Path(args.run_dir)
    rows: Dict[str, Any] = {}
    for name in BRANDS:
        rec = replay(run_dir, name, config, cc)
        o, meta = rec["outcome"], rec["meta"]
        r = o.get("result")
        row = {"status": o["status"], "outcome": o.get("outcome"), "network_attempts": meta["network_attempts"],
               "resolution": {k: (o.get("resolution") or {}).get(k) for k in ("status", "name", "qloo_id", "method")},
               "choice": (meta.get("choice") or {}).get("picked")}
        if r:
            again = run_continuous(r["evidence"], cc.lexicon, cc.scoring, cc.vectors, cc.params)
            base = commitment(r["axes"])
            related = sorted({str(e["entity_id"]) for e in r["evidence"] if e["source_kind"] != "own"})
            moves, flips = [], 0
            for ent in related:
                alt = run_continuous([e for e in r["evidence"] if str(e["entity_id"]) != ent], cc.lexicon, cc.scoring, cc.vectors, cc.params)
                moves.append(math.dist(base, commitment(alt["axes"])))
                flips += continuous_report.signature(alt["axes"]) != continuous_report.signature(r["axes"])
            ev = {e["evidence_id"]: e for e in r["evidence"]}
            row.update(
                evidence_items=r["evidence_count"], deterministic=json.dumps(again, sort_keys=True) == json.dumps(r, sort_keys=True),
                leading=[(m, r["motif_scores"][m]["score"]) for m in r["leading_motifs"]],
                motifs={m: s["score"] for m, s in sorted(r["motif_scores"].items(), key=lambda kv: -kv[1]["score"])},
                profile={a: (f"{v['label']} · {v['confidence_word']}" if v["state"] == "resolved" else v["state"]) for a, v in r["axes"].items()},
                signature=continuous_report.signature(r["axes"]), commitment=base, traceable=traceable(r),
                support_tags={m: sorted({f"{ev[x['evidence_id']]['tag_name']} [{x['source_kind']}: {ev[x['evidence_id']]['entity_name']}]"
                                         for x in r["annotations"] if x["motif"] == m and x["role"] == "support"})
                              for m in r["leading_motifs"]},
                stability={"related_entities": len(related), "max_move": round(max(moves) if moves else 0.0, 4), "label_flips": flips})
        rows[name] = row
    trial = continuous_report.analysis(engine_compare.legacy_results()) if legacy_baseline.available() else None
    done = [n for n in BRANDS if rows[n].get("signature")]
    cross = {f"{x} – {y}": round(math.dist(rows[x]["commitment"], rows[y]["commitment"]), 4) for x, y in itertools.combinations(done, 2)}
    vs_trial = {}
    if trial:
        for n in done:
            near = min(((t, math.dist(rows[n]["commitment"], b["commitment"])) for t, b in trial["brands"].items()), key=lambda kv: kv[1])
            same = [t for t, b in trial["brands"].items() if tuple(b["signature"]) == tuple(rows[n]["signature"])]
            vs_trial[n] = {"nearest": near[0], "distance": round(near[1], 4), "same_profile_as": same}
    report = {"brands": rows, "pairwise": cross, "distinct_profiles": len({tuple(rows[n]["signature"]) for n in done}),
              "vs_trial": vs_trial, "total_network_attempts": sum(r["network_attempts"] for r in rows.values())}
    text = json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("live")
    p.add_argument("--out")
    p = sub.add_parser("evaluate")
    p.add_argument("run_dir")
    p.add_argument("--json")
    args = ap.parse_args(argv)
    return cmd_live(args) if args.cmd == "live" else cmd_evaluate(args)


if __name__ == "__main__":
    raise SystemExit(main())

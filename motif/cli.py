"""Command line for the MOTIF engine.

  python3 -m motif run --reference MUJI [--type brand|movie|artist|any]
                       [--recorded RUN] [--choose QLOO_ID] [--include-artist]
                       [--resolve-conflict AXIS=POLE|open] [--allow-unverified-materials]
                       [--max-requests N] [--json] [--data-dir DIR]
  python3 -m motif compare --reference MUJI --recorded RUN [...]
  python3 -m motif compare-engines --reference MUJI --recorded RUN [--choose ID] [--json]

`run` uses the continuous engine by default (weighted motifs -> six continuous
dimensions); `--engine legacy` runs the frozen rule engine engine-0.3 instead.
`compare-engines` replays one recording and runs both engines on the same evidence.

Live mode (no --recorded) sends real Qloo requests through motif_spike's
DirectTransport and needs the event credential in the environment. Recorded
mode replays a stored live run and sends nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from motif_spike.manifest import harness_environment, live_environment, load_manifest
from motif_spike.readiness import check_direct_readiness
from motif_spike.transport import DirectTransport, direct_api_key
from motif_spike.util import data_root, iso, utc_now, write_json

from . import ENGINE_VERSION
from .agent import Controller
from .brief import AXIS_LABELS, build_brief
from .config import AXES, load_config, load_continuous_config
from .continuous import run_continuous
from .engine import evidence_subset, run_engine
from .llm import write_prose, writer_from_env
from .qloo import LiveQloo, RecordedQloo

EXIT = {"completed": 0, "needs_choice": 3, "stopped": 4}


def _recording_dir(root: Path, value: str) -> Path:
    for candidate in (Path(value), root / "raw" / value, root / "motif_sessions" / value):
        if (candidate / "requests.jsonl").exists():
            return candidate
    raise SystemExit(f"recording {value!r} not found (looked for requests.jsonl under it, data/raw/ and data/motif_sessions/)")


def _overrides(values: Optional[List[str]]) -> Dict[str, str]:
    out = {}
    for value in values or []:
        axis, _, pole = value.partition("=")
        if axis not in AXES or not pole:
            raise SystemExit(f"--resolve-conflict expects AXIS=POLE|open with AXIS in {AXES}")
        out[axis] = pole
    return out


def _access(args, root: Path, session_dir: Path, config):
    params = config.params["budget"]
    max_requests = args.max_requests if args.max_requests is not None else params["max_requests_per_session"]
    if args.recorded:
        rec_dir = _recording_dir(root, args.recorded)
        access = RecordedQloo(rec_dir, session_dir, max_requests)
        run = access.recording_meta
        label = {"data_label": "recorded", "recorded_from": run.get("run_id") or rec_dir.name,
                 "recorded_at": run.get("started_at") or run.get("created_at")}
        return access, label
    manifest = load_manifest()
    env = live_environment(harness_environment(manifest))
    ready = check_direct_readiness(env)
    if not ready.live_ready:
        raise SystemExit("live mode is not ready (run `python3 -m motif_spike check`); nothing was sent and no recorded data was substituted")
    transport = DirectTransport(ready.base_url, api_key=direct_api_key(env), timeout_s=params["timeout_s"])
    access = LiveQloo(transport, ready.base_url, session_dir, max_requests, params["max_retries"], params["retry_backoff_s"],
                      params["timeout_s"])
    return access, {"data_label": "live", "base_url": ready.base_url}


def cmd_run(args) -> int:
    config = load_config()
    root = data_root(args.data_dir)
    session_id = f"{'rec' if args.recorded else 'live'}-{utc_now().strftime('%Y%m%dT%H%M%SZ')}-{os.getpid() % 10000:04d}"
    session_dir = root / "motif_sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    access, label = _access(args, root, session_dir, config)
    domains = list(config.params["default_domains"]) + (["artist"] if args.include_artist else [])
    continuous = load_continuous_config() if args.engine == "continuous" else None
    controller = Controller(access, config, args.reference, args.type, args.choose, domains,
                            args.allow_unverified_materials, _overrides(args.resolve_conflict),
                            engine=args.engine, continuous=continuous)
    outcome = controller.run()

    session = {"session_id": session_id, "created_at": iso(utc_now()), "engine": args.engine,
               "engine_version": (outcome.get("result") or {}).get("engine_version", ENGINE_VERSION),
               "versions": continuous.versions if continuous else config.versions, **label,
               "reference": {"input": args.reference, "type": args.type},
               "domains": domains, "resolution": outcome["resolution"], "status": outcome["status"],
               "outcome": outcome["outcome"], "question": outcome.get("question"), "trace": outcome["trace"],
               "requests": access.log, "network_attempts": access.network_attempts,
               "message": outcome.get("message")}
    brief = None
    if args.engine == "legacy" and outcome.get("result") is not None and outcome["status"] == "completed":
        llm = writer_from_env(os.environ, ledger_path=root / "llm_calls.jsonl")
        session["llm_status"] = llm["status"]
        prose = write_prose(outcome["resolution"].get("name") or args.reference, outcome["result"], llm["writer"])
        brief = build_brief(session, outcome["result"], prose)
        write_json(session_dir / "brief.json", brief)
    if outcome.get("result") is not None:
        write_json(session_dir / "engine_result.json", outcome["result"])
    write_json(session_dir / "session.json", session)

    if args.json:
        print(json.dumps(brief or (dict(session, result=outcome.get("result")) if args.engine == "continuous" else session),
                         indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _print_human(session, outcome, brief, session_dir)
    return EXIT[outcome["status"]]


def _continuous_lines(result: Dict[str, Any]) -> List[str]:
    lines = [f"Outcome: {result['outcome']} — {result['outcome_meaning']}", "Motif scores (0-1, design quantities; common-cue-only motifs marked):"]
    for m, s in sorted(result["motif_scores"].items(), key=lambda kv: (-kv[1]["score"], kv[0])):
        kinds = ", ".join(s["source_kinds"]) or "common cues only"
        lines.append(f"  {m:12} {s['score']:.3f}  {kinds}{'  (leads)' if m in result['leading_motifs'] else ''}")
    lines.append("Dimensions:")
    for a in AXES:
        v = result["axes"][a]
        if v["state"] == "resolved":
            text = f"{v['label']} ({v['confidence_word']}; basis {v['evidence_basis']})"
        else:
            text = "open" + (": contributors pull both ways" if v["state"] == "balanced_open" else "")
        pulls = "; ".join(f"{pole}: {', '.join(ms)}" for pole, ms in v["pulls"].items() if ms)
        lines.append(f"  {a:20} {text}" + (f"  [{pulls}]" if pulls else ""))
    return lines


def _print_human(session, outcome, brief, session_dir) -> None:
    banner = {"live": f"LIVE · Qloo {session.get('base_url')}",
              "recorded": f"RECORDED · Qloo data from run {session.get('recorded_from')} (not a live request)"}[session["data_label"]]
    print(banner)
    print(f"Reference: {session['reference']['input']} (type {session['reference']['type']}); "
          f"versions {session['versions']}; network attempts {session['network_attempts']}")
    print("\nResearch trace (deterministic controller):")
    for row in session["trace"]:
        req = f" [{row['request_id']} {row['request_status']}]" if row.get("request_id") else ""
        print(f"  {row['step']}. {row['action']}: {row['decision']}{req}\n     observed: {row['observed']}\n     reason: {row['reason']}")
    res = session["resolution"]
    if res.get("status") == "resolved":
        print(f"\nResolved: {res['name']} {res['qloo_id']} {res['types']} ({res['method']}); "
              f"{len(res.get('alternatives', []))} other candidates returned")
    question = session.get("question")
    if session["status"] != "completed" or question:
        print(f"\nStatus: {session['status']} / {session['outcome']}")
        if session.get("message"):
            print(f"  {session['message']}")
        if question:
            print(f"  Question ({question['kind']}): {question['why']}")
            for opt in question.get("options", []):
                print(f"    - {opt if isinstance(opt, str) else json.dumps(opt, ensure_ascii=False)}")
            print(f"  {question['how_to_answer']}")
    result = outcome.get("result")
    if result and result.get("engine") == "continuous":
        print("\n" + "\n".join(_continuous_lines(result)))
        print("\nThe written brief for the continuous engine comes with the scent architecture (phases 8-9).")
    elif result:
        print(f"\nOutcome: {result['outcome']} — {result['outcome_meaning']}")
        print("Motifs (support before thresholds):")
        for name, info in sorted(result["motifs"].items()):
            sup = "; ".join(f"{k}: {v['entities']} entities {v['cue_groups']}" for k, v in info["support_by_source"].items())
            print(f"  {name:12} {info['strength']:12} {sup or 'no non-common support'}"
                  f" | context {len(info['context_evidence_ids'])}, negated {len(info['negated_evidence_ids'])}, excluded {len(info.get('excluded_evidence', []))}")
        print("Axes:")
        for axis in AXES:
            v = result["axes"][axis]
            extra = (f" via {v['rule_ids']} ({v['evidence_strength']} evidence, rule draft_hypothesis"
                     f"{', relations only' if v.get('relations_only') else ''})") if v["state"] == "target" else ""
            print(f"  {axis:20} {v['state']:10} {v['value']}{extra}")
        mats = result["materials"]
        print(f"Materials: {mats['status']} ({mats['verification_mode']})")
        for m in mats.get("selected", []):
            extras = ", ".join(f"{u['pole']} [creative choice]" for u in m["unrequested_properties"])
            print(f"  {m['slot']:5} {m['material_id']} {m['name']} score {m['score']:.3f} matches {m['matches']}"
                  + (f"; also {extras}" if extras else ""))
        if mats["status"] != "composed":
            for m in mats.get("ranked", [])[:4]:
                print(f"  candidate {m['material_id']} {m['name']} score {m['score']:.3f} (not composed)")
    if brief:
        print(f"\nBrief ({brief['brief_text']['author']}): {brief['brief_text']['text']}")
        if brief["brief_text"].get("note"):
            print(f"  note: {brief['brief_text']['note']}")
    print(f"\nSaved: {session_dir}")


def cmd_compare(args) -> int:
    """Qloo contribution: the seed's own description (A) vs plus relations (B), same rules."""
    config = load_config()
    root = data_root(args.data_dir)
    session_dir = root / "motif_sessions" / f"cmp-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    access = RecordedQloo(_recording_dir(root, args.recorded), session_dir, 99)
    domains = ["brand", "movie"] + (["artist"] if args.include_artist else [])
    # fetch everything allowed (the comparison needs B complete), then evaluate subsets offline
    controller = Controller(access, config, args.reference, args.type, args.choose, domains)
    controller._worth_fetching = lambda domain, result: (True, "comparison fetches every allowed domain")
    outcome = controller.run()
    if outcome["status"] == "needs_choice" or not controller.evidence:
        print(json.dumps({k: outcome.get(k) for k in ("status", "outcome", "question", "message")}, indent=2))
        return 3
    report = compare_report(controller.evidence, config, args.allow_unverified_materials)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else _compare_text(args.reference, report))
    return 0


def compare_report(evidence, config, allow_unverified=False) -> Dict[str, Any]:
    a = run_engine(evidence_subset(evidence, ["own"]), config, allow_unverified)
    b = run_engine(evidence, config, allow_unverified)
    # Sensitivity check: is A empty only because the own-only route needs two cue groups?
    import copy
    relaxed_lexicon = copy.deepcopy(config.lexicon)
    relaxed_lexicon["support"]["parameters"]["own_route_min_cue_groups"] = 1
    relaxed = type(config)(relaxed_lexicon, config.rules, config.palette, config.params)
    a1 = run_engine(evidence_subset(evidence, ["own"]), relaxed, allow_unverified)
    rows = {}
    for motif in sorted(set(a["motifs"]) | set(b["motifs"])):
        ia, ib = a["motifs"].get(motif), b["motifs"].get(motif)
        rows[motif] = {
            "A_strength": ia["strength"] if ia else None, "B_strength": ib["strength"] if ib else None,
            "A_own_cue_groups": ia["own_cue_groups"] if ia else [],
            "B_source_kinds": ib["source_kinds"] if ib else [],
            "B_support_by_source": ib["support_by_source"] if ib else {},
            "new_from_relations": bool(ib and ib["support_evidence_ids"]) and not (ia and ia["support_evidence_ids"]),
            "A_blocked_by_threshold_only": bool(ia and ia["anchored"] and not ia["active"] and len(ia["own_cue_groups"]) == 1),
        }
    return {"A_outcome": a["outcome"], "B_outcome": b["outcome"],
            "A_targets": {k: v["value"] for k, v in a["axes"].items() if v["state"] == "target"},
            "B_targets": {k: v["value"] for k, v in b["axes"].items() if v["state"] == "target"},
            "A_relaxed_targets": {k: v["value"] for k, v in a1["axes"].items() if v["state"] == "target"},
            "A_relaxed_note": "A re-run with one own cue group sufficient (sensitivity check, not a product setting)",
            "B_conflicts": b["conflicted_axes"], "motifs": rows,
            "A_evidence_items": a["evidence_count"], "B_evidence_items": b["evidence_count"]}


def _compare_text(reference: str, r: Dict[str, Any]) -> str:
    lines = [f"{reference}: A = own Qloo description only ({r['A_evidence_items']} items) · B = plus related brands/movies ({r['B_evidence_items']} items)",
             f"  A outcome {r['A_outcome']}, targets {r['A_targets']}; A with a one-cue threshold: {r['A_relaxed_targets']}", f"  B outcome {r['B_outcome']}, targets {r['B_targets']}, conflicts {r['B_conflicts']}",
             "  motif         A strength (own cue groups)      B strength [source kinds]   new from relations / A blocked only by threshold"]
    for m, row in r["motifs"].items():
        lines.append(f"  {m:13} {str(row['A_strength']):12} {str(row['A_own_cue_groups']):20} {str(row['B_strength']):10} "
                     f"{str(row['B_source_kinds']):28} {row['new_from_relations']!s:5} / {row['A_blocked_by_threshold_only']}")
    return "\n".join(lines)


def cmd_compare_engines(args) -> int:
    """Legacy rule engine vs continuous engine on the same recorded evidence (offline)."""
    config = load_config()
    cc = load_continuous_config()
    root = data_root(args.data_dir)
    access = RecordedQloo(_recording_dir(root, args.recorded), None, 99)
    domains = list(config.params["default_domains"]) + (["artist"] if args.include_artist else [])
    controller = Controller(access, config, args.reference, args.type, args.choose, domains)
    controller._worth_fetching = lambda domain, result: (True, "comparison fetches every allowed domain")
    outcome = controller.run()
    if outcome["status"] == "needs_choice" and (outcome.get("question") or {}).get("kind") == "choose_entity" or not controller.evidence:
        print(json.dumps({k: outcome.get(k) for k in ("status", "outcome", "question", "message")}, indent=2))
        return 3
    legacy = run_engine(controller.evidence, config)
    cont = run_continuous(controller.evidence, cc.lexicon, cc.scoring, cc.vectors, cc.params, ["own"] + domains)
    if args.json:
        print(json.dumps({"legacy": {k: legacy[k] for k in ("engine_version", "outcome", "axes", "materials")},
                          "continuous": {k: cont[k] for k in ("engine_version", "versions", "outcome", "motif_scores", "axes")}},
                         indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    targets = {a: v["value"] for a, v in legacy["axes"].items() if v["state"] == "target"}
    print(f"{args.reference}: same evidence ({legacy['evidence_count']} items), two engines")
    print(f"\nLegacy {legacy['engine_version']}: outcome {legacy['outcome']}; targets {targets or 'none'}; "
          f"materials {[m['name'] for m in legacy['materials'].get('selected', [])] or 'none'}")
    print(f"\nContinuous {cont['engine_version']} ({', '.join(f'{k} {v}' for k, v in cont['versions'].items())}):")
    print("\n".join(_continuous_lines(cont)))
    return 0


def cmd_llm_check(args) -> int:
    """One real API call to confirm the configured model is available (counted in the call ledger)."""
    root = data_root(args.data_dir)
    llm = writer_from_env(os.environ, ledger_path=root / "llm_calls.jsonl")
    if llm["writer"] is None:
        print(llm["status"])
        return 2
    try:
        info = llm["writer"].check_model()
    except Exception as exc:
        print(f"model check failed: {type(exc).__name__} (the model is NOT switched automatically)")
        return 4
    print(f"model available: {info['id']} ({info.get('display_name')}); calls today: {llm['writer'].ledger.calls_today()}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m motif", description="MOTIF engine: Qloo evidence to a perfumer brief.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "compare", "compare-engines"):
        p = sub.add_parser(name)
        p.add_argument("--reference", required=True)
        p.add_argument("--type", default="brand", choices=["brand", "movie", "artist", "any"])
        p.add_argument("--recorded", help="replay a stored live run (run ID under data/raw or data/motif_sessions, or a path)")
        p.add_argument("--choose", help="Qloo ID of a returned candidate (answer to an entity question)")
        p.add_argument("--include-artist", action="store_true", help="also consider related music artists (off by default)")
        p.add_argument("--allow-unverified-materials", action="store_true",
                       help="DESIGN PREVIEW: also use material properties not verified against full supplier pages")
        p.add_argument("--json", action="store_true")
        p.add_argument("--data-dir")
        if name == "run":
            p.add_argument("--engine", choices=["continuous", "legacy"], default="continuous",
                           help="continuous (default) or the frozen legacy rule engine engine-0.3")
            p.add_argument("--resolve-conflict", action="append", help="AXIS=POLE or AXIS=open (legacy engine only)")
            p.add_argument("--max-requests", type=int, help="network attempt budget for a live session")
    p = sub.add_parser("llm-check", help="one real API call: is the configured LLM model available?")
    p.add_argument("--data-dir")
    args = parser.parse_args(argv)
    if args.command == "llm-check":
        return cmd_llm_check(args)
    try:
        return {"run": cmd_run, "compare": cmd_compare, "compare-engines": cmd_compare_engines}[args.command](args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

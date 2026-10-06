"""Command line: python3 -m motif_spike {check,plan,run,renormalize}."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from . import adapter
from .compare import compare
from .facts import render_facts
from .manifest import build_plan, harness_environment, live_environment, load_manifest
from .normalize import normalize_run
from .readiness import Readiness, check_direct_readiness, check_readiness
from .runner import Runner, build_reuse_index
from .transport import DirectTransport, FixtureTransport, HarnessTransport, direct_api_key, harness_command
from .util import CONFIG_DIR, FIXTURES_DIR, RunPaths, data_root, new_run_id, read_json, write_json

SCENARIOS = {
    "main": FIXTURES_DIR / "scenario_main.json",
    "auth_error": FIXTURES_DIR / "scenario_auth_error.json",
}


def _csv(value: Optional[str]) -> Optional[List[str]]:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def _registry_version() -> Optional[str]:
    path = CONFIG_DIR / "draft_rules.json"
    if not path.exists():
        return None
    return read_json(path).get("registry_version")


def _print_readiness(report: Readiness) -> None:
    def yes(flag: Optional[bool]) -> str:
        return "unknown" if flag is None else ("yes" if flag else "no")

    print("Qloo live-mode readiness (presence only; no secret value is shown; no API call)")
    print(f"  transport ...................... {report.transport}")
    if report.transport == "direct":
        print(f"  base URL ....................... {report.base_url or 'invalid or missing'}")
        print(f"  credential ..................... {report.credential_note}")
    else:
        print(f"  harness (`qloo`) found ......... {yes(report.harness_found)}")
        print(f"  harness version ................ {report.harness_version or 'unknown'} (needs >= {'.'.join(map(str, adapter.MIN_HARNESS_VERSION))})")
        print(f"  credential configured .......... {yes(report.credential_configured)}"
              + (f" (source: {report.credential_source})" if report.credential_source else ""))
    for name, present in report.env_present.items():
        value = report.non_secret_env.get(name)
        shown = f"set ({value})" if value else ("set" if present else "not set")
        print(f"  env {name:<27} {shown}")
    if report.non_secret_env.get("QLOO_BASE_URL"):
        print("  (base URL values are set for every live run from config/manifest.json)")
    if report.status_check_error:
        print(f"  status check error ............. {report.status_check_error}")
    print(f"  live mode ...................... {'READY' if report.live_ready else 'NOT READY'}")
    for reason in report.reasons:
        print(f"    - {reason}")
    if report.live_ready:
        print("  Note: 'configured' is not 'accepted'. Only a live request shows whether Qloo accepts the credential.")


def _transport_choice(args: argparse.Namespace, manifest: dict) -> str:
    return getattr(args, "transport", None) or manifest.get("live_transport", "direct")


def _live_readiness(transport: str, env: dict) -> Readiness:
    return check_direct_readiness(env=env) if transport == "direct" else check_readiness(env=env)


def cmd_check(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    report = _live_readiness(_transport_choice(args, manifest), live_environment(harness_environment(manifest)))
    _print_readiness(report)
    return 0 if report.live_ready else 2


def cmd_plan(args: argparse.Namespace) -> int:
    plan = build_plan(load_manifest(), args.plan, _csv(args.seeds), _csv(args.domains), args.max_requests)
    print(f"Plan '{plan.name}' (manifest {plan.manifest_version}); nothing is executed by this command.")
    per_seed = 1 + int(plan.seed_detail) + len(plan.domains) + 1
    print(f"  seeds: {', '.join(s.key for s in plan.seeds)}")
    print(f"  domains: {', '.join(f'{d.key}={d.entity_type}' for d in plan.domains)}")
    print(f"  harness invocations without retries: up to {per_seed * len(plan.seeds)} (budget {plan.max_requests}); "
          "each `exec entity_tags` makes an extra identifier lookup inside the harness.")
    for seed in plan.seeds:
        placeholder = f"<Qloo ID resolved for {seed.input_name}>"
        print(f"\n  [{seed.key}]")
        print("    " + adapter.display_command(adapter.search_argv(seed.input_name, plan.search_take, seed.search_type)))
        if plan.seed_detail:
            print("    " + adapter.display_command(adapter.seed_detail_argv(placeholder)))
        for domain in plan.domains:
            print("    " + adapter.display_command(adapter.related_argv(placeholder, domain.entity_type, plan.related_take, plan.explainability)))
        print("    " + adapter.display_command(adapter.seed_tags_argv(placeholder, plan.seed_tags_limit)))
    print("\n  Dependent commands run only if the search resolves the seed to exactly one returned entity.")
    return 0


def finalize(paths: RunPaths) -> Path:
    normalized = normalize_run(paths)
    comparison = compare(normalized)
    write_json(paths.normalized_dir / "comparison.json", comparison)
    facts = paths.normalized_dir / "facts.md"
    facts.write_text(render_facts(normalized, comparison), encoding="utf-8")
    return facts


def cmd_run(args: argparse.Namespace) -> int:
    root = data_root(args.data_dir)
    readiness = None
    harness_version = None
    if args.mode == "synthetic":
        scenario = read_json(SCENARIOS[args.scenario])
        plan = build_plan(scenario["manifest"], "synthetic", _csv(args.seeds), _csv(args.domains), args.max_requests)
        transport = FixtureTransport(scenario, FIXTURES_DIR)
        sleep = lambda seconds: None  # noqa: E731 - fixtures need no real back-off
        print(f"SYNTHETIC run (scenario '{args.scenario}'): local fixtures only, no network, not Qloo data.")
    else:
        if not args.plan:
            print("live mode needs --plan pilot|full (see `python3 -m motif_spike plan --plan pilot`)", file=sys.stderr)
            return 2
        manifest = load_manifest()
        plan = build_plan(manifest, args.plan, _csv(args.seeds), _csv(args.domains), args.max_requests)
        env = live_environment(plan.harness_env)
        choice = _transport_choice(args, manifest)
        report = _live_readiness(choice, env)
        if not report.live_ready:
            _print_readiness(report)
            print("\nLive run NOT started. Nothing was sent to Qloo and no synthetic data was substituted.")
            return 2
        readiness = report.to_record()
        harness_version = report.harness_version
        if choice == "direct":
            transport = DirectTransport(report.base_url, api_key=direct_api_key(env), timeout_s=plan.timeout_s)
        else:
            transport = HarnessTransport(harness_command(env), timeout_s=plan.timeout_s, env=env)
        sleep = time.sleep
        print(f"LIVE run, plan '{plan.name}': {len(plan.seeds)} seeds x {len(plan.domains)} domains, budget {plan.max_requests} invocations.")

    run_id = new_run_id(args.mode)
    paths = RunPaths(root, run_id)
    reuse = build_reuse_index(root, exclude_run=run_id) if args.mode == "live" and not args.no_reuse else {}
    runner = Runner(plan, transport, paths, scenario=args.scenario if args.mode == "synthetic" else None,
                    readiness=readiness, harness_version=harness_version, registry_version=_registry_version(),
                    reuse_index=reuse, sleep=sleep, log=print)
    run = runner.run()
    facts = finalize(paths)
    print(f"\nRun {run_id}: {run['status']} (live execution: {run['live_execution_status']})")
    print("  by status: " + ", ".join(f"{k}={v}" for k, v in sorted(run["counts"]["by_status"].items())))
    print(f"  raw:        {paths.raw_dir}")
    print(f"  normalized: {paths.normalized_dir}")
    print(f"  facts:      {facts}")
    if run.get("synthetic"):
        print("  Reminder: synthetic output is a contract check, not feasibility evidence.")
    return 3 if run["status"] == "aborted_auth_error" else 0


def _resolve_run_id(root: Path, wanted: str) -> str:
    runs = sorted((p for p in (root / "raw").glob("*") if (p / "run.json").exists()), key=lambda p: p.name.split("-", 1)[-1])
    if wanted in ("latest", "latest-live", "latest-synthetic"):
        prefix = {"latest": "", "latest-live": "live-", "latest-synthetic": "synthetic-"}[wanted]
        matching = [p.name for p in runs if p.name.startswith(prefix)]
        if not matching:
            raise SystemExit(f"no run matches {wanted!r} under {root / 'raw'}")
        return matching[-1]
    if not (root / "raw" / wanted / "run.json").exists():
        raise SystemExit(f"run {wanted!r} not found under {root / 'raw'}")
    return wanted


def cmd_renormalize(args: argparse.Namespace) -> int:
    root = data_root(args.data_dir)
    paths = RunPaths(root, _resolve_run_id(root, args.run))
    facts = finalize(paths)
    print(f"Re-normalized {paths.run_id} from saved raw output (no requests sent). Facts: {facts}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m motif_spike", description="MOTIF Qloo feasibility spike (evidence playground).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="live readiness: transport, base URL, credential presence (no values, no API call)")
    p_check.add_argument("--transport", choices=["direct", "harness"], help="default: manifest live_transport (direct)")

    p_plan = sub.add_parser("plan", help="print the harness commands a live plan would send (executes nothing)")
    p_plan.add_argument("--plan", default="pilot")
    p_plan.add_argument("--seeds", help="comma-separated seed keys (default: the plan's)")
    p_plan.add_argument("--domains", help="comma-separated domain keys (default: the plan's)")
    p_plan.add_argument("--max-requests", type=int)

    p_run = sub.add_parser("run", help="run a synthetic contract check or a live Qloo plan")
    p_run.add_argument("--mode", choices=["synthetic", "live"], required=True)
    p_run.add_argument("--plan", help="live only: pilot | full")
    p_run.add_argument("--scenario", choices=sorted(SCENARIOS), default="main", help="synthetic only")
    p_run.add_argument("--seeds", help="comma-separated seed keys (default: the plan's)")
    p_run.add_argument("--domains", help="comma-separated domain keys (default: the plan's)")
    p_run.add_argument("--max-requests", type=int, help="override the plan's invocation budget")
    p_run.add_argument("--transport", choices=["direct", "harness"], help="live only; default: manifest live_transport (direct)")
    p_run.add_argument("--no-reuse", action="store_true", help="live only: do not reuse identical successful live responses")
    p_run.add_argument("--data-dir", help="data root (default: ./data or $MOTIF_DATA_DIR)")

    p_ren = sub.add_parser("renormalize", help="rebuild normalized output and facts from saved raw output")
    p_ren.add_argument("--run", default="latest", help="run id, latest, latest-live, or latest-synthetic")
    p_ren.add_argument("--data-dir")

    args = parser.parse_args(argv)
    handlers = {"check": cmd_check, "plan": cmd_plan, "run": cmd_run, "renormalize": cmd_renormalize}
    try:
        return handlers[args.command](args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

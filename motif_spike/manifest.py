"""Request manifest: seeds, candidate domains, limits, and named plans."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .util import CONFIG_DIR, read_json

DEFAULT_MANIFEST = CONFIG_DIR / "manifest.json"

# Non-secret harness settings a manifest may pin (the event base URL). The
# credential is deliberately not on this list: it never belongs in the repo.
ALLOWED_HARNESS_ENV = ("QLOO_BASE_URL", "QLOO_TRUSTED_BASE_URL")


@dataclass
class Seed:
    key: str
    input_name: str
    expected_types: List[str] = field(default_factory=list)
    search_type: Optional[str] = None
    override: Optional[Dict[str, str]] = None
    note: str = ""


@dataclass
class Domain:
    key: str
    label: str
    entity_type: str


@dataclass
class Plan:
    name: str
    manifest_version: str
    seeds: List[Seed]
    domains: List[Domain]
    search_take: int
    related_take: int
    explainability: bool
    seed_detail: bool
    seed_tags_limit: int
    max_requests: int
    max_retries: int
    retry_backoff_s: List[float]
    timeout_s: float
    harness_env: Dict[str, str] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        return asdict(self)


def load_manifest(path: Optional[Path] = None) -> Dict[str, Any]:
    return read_json(path or DEFAULT_MANIFEST)


def harness_environment(manifest: Dict[str, Any]) -> Dict[str, str]:
    """Non-secret environment the harness must run with (for example the event base URL)."""
    env = manifest.get("harness_environment") or {}
    unknown = [name for name in env if name not in ALLOWED_HARNESS_ENV]
    if unknown:
        raise ValueError(
            f"harness_environment may only set {', '.join(ALLOWED_HARNESS_ENV)}; got {', '.join(unknown)}. "
            "Credentials never belong in the manifest."
        )
    return {name: str(value) for name, value in env.items()}


def live_environment(harness_env: Dict[str, str], base: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Environment for live harness calls: the user's environment, with the
    manifest's non-secret settings taking precedence so every run targets the event API."""
    env = dict(os.environ if base is None else base)
    env.update(harness_env)
    return env


def _pick(available: Dict[str, Any], wanted: Sequence[str], what: str) -> List[Any]:
    unknown = [k for k in wanted if k not in available]
    if unknown:
        raise ValueError(f"unknown {what}: {', '.join(unknown)} (known: {', '.join(available)})")
    return [available[k] for k in wanted]


def build_plan(
    manifest: Dict[str, Any],
    plan_name: str,
    seeds: Optional[Sequence[str]] = None,
    domains: Optional[Sequence[str]] = None,
    max_requests: Optional[int] = None,
) -> Plan:
    plans = manifest.get("plans", {})
    if plan_name not in plans:
        raise ValueError(f"unknown plan {plan_name!r} (known: {', '.join(plans)})")
    plan_cfg = plans[plan_name]
    defaults = dict(manifest.get("defaults", {}))
    defaults.update(plan_cfg.get("overrides", {}))
    overrides = manifest.get("resolution_overrides", {})

    all_seeds = {
        s["key"]: Seed(
            key=s["key"],
            input_name=s["input_name"],
            expected_types=list(s.get("expected_types", [])),
            search_type=s.get("search_type"),
            override=overrides.get(s["key"]),
            note=s.get("note", ""),
        )
        for s in manifest["seeds"]
    }
    all_domains = {d["key"]: Domain(d["key"], d["label"], d["entity_type"]) for d in manifest["domains"]}

    return Plan(
        name=plan_name,
        manifest_version=str(manifest.get("manifest_version", "unversioned")),
        seeds=_pick(all_seeds, list(seeds or plan_cfg["seeds"]), "seed"),
        domains=_pick(all_domains, list(domains or plan_cfg["domains"]), "domain"),
        search_take=int(defaults.get("search_take", 10)),
        related_take=int(defaults.get("related_take", 10)),
        explainability=bool(defaults.get("explainability", True)),
        seed_detail=bool(defaults.get("seed_detail", True)),
        seed_tags_limit=int(defaults.get("seed_tags_limit", 20)),
        max_requests=int(max_requests or plan_cfg.get("max_requests", 30)),
        max_retries=int(defaults.get("max_retries", 2)),
        retry_backoff_s=[float(x) for x in defaults.get("retry_backoff_s", [3, 10])],
        timeout_s=float(defaults.get("timeout_s", 90)),
        harness_env=harness_environment(manifest),
    )

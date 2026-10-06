"""Live-mode readiness check. Reports presence and status only, never values.

Uses the harness's own non-mutating check, `qloo setup --status --json`, which
reports whether a credential is configured and where it comes from. "Ready"
means configured, not accepted by Qloo: only a live request can show that.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from .adapter import MIN_HARNESS_VERSION
from .redact import SECRET_ENV_VARS, redact, truncate
from .transport import PROXY_KEY_PLACEHOLDER, HarnessTransport, harness_command, validate_base_url

NON_SECRET_ENV_VARS = ("QLOO_HARNESS_BIN", "QLOO_BASE_URL", "QLOO_TRUSTED_BASE_URL")


@dataclass
class Readiness:
    transport: str = "harness"
    base_url: Optional[str] = None
    credential_note: Optional[str] = None
    harness_found: bool = False
    harness_version: Optional[str] = None
    harness_version_ok: Optional[bool] = None
    credential_configured: Optional[bool] = None
    credential_source: Optional[str] = None
    status_check_error: Optional[str] = None
    env_present: Dict[str, bool] = field(default_factory=dict)
    non_secret_env: Dict[str, str] = field(default_factory=dict)
    live_ready: bool = False
    reasons: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


def _version_tuple(text: str) -> Optional[tuple]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in match.groups()) if match else None


def check_readiness(
    env: Optional[Mapping[str, str]] = None,
    command: Optional[Sequence[str]] = None,
    transport_factory: Callable[..., HarnessTransport] = HarnessTransport,
) -> Readiness:
    env = dict(os.environ if env is None else env)
    report = Readiness()
    report.env_present = {name: bool(env.get(name)) for name in SECRET_ENV_VARS + NON_SECRET_ENV_VARS}
    report.non_secret_env = {name: env[name] for name in NON_SECRET_ENV_VARS if env.get(name)}

    command = list(command) if command else harness_command(env)
    if not command:
        report.reasons.append("`qloo` not found: npm install --global @qloo/qloo-harness (Node.js >= 22.19.0)")
        return report
    transport = transport_factory(command, timeout_s=30, env=env)

    version = transport.execute(["--version"])
    if version.missing_binary:
        report.reasons.append("configured harness binary could not be started")
        return report
    report.harness_found = True
    parsed = _version_tuple(version.stdout)
    report.harness_version = ".".join(map(str, parsed)) if parsed else None
    report.harness_version_ok = bool(parsed and parsed >= MIN_HARNESS_VERSION)
    if not report.harness_version_ok:
        wanted = ".".join(map(str, MIN_HARNESS_VERSION))
        report.reasons.append(f"harness version {report.harness_version or 'unknown'} is older than {wanted} or unreadable")

    status = transport.execute(["setup", "--status", "--json"])
    try:
        payload = json.loads(status.stdout)
        qloo = payload.get("qloo", {}) if isinstance(payload, dict) else {}
        report.credential_configured = bool(qloo.get("ready"))
        source = qloo.get("source")
        report.credential_source = source if isinstance(source, str) else None
    except (ValueError, AttributeError):
        detail = status.stderr or status.stdout or "no output"
        report.status_check_error = truncate(redact(detail, env=env), 300)
    if (env.get("QLOO_API_KEY") or "").strip() == PROXY_KEY_PLACEHOLDER:
        report.credential_configured = False
        report.reasons.append("QLOO_API_KEY is the proxy placeholder; the harness would send it as the key. Use --transport direct")
    elif not report.credential_configured:
        report.reasons.append("no Qloo credential configured for the harness: run `qloo setup --qloo` (keep the key outside this folder)")

    report.live_ready = bool(report.harness_found and report.harness_version_ok and report.credential_configured)
    return report


def check_direct_readiness(env: Optional[Mapping[str, str]] = None) -> Readiness:
    """Readiness for the direct transport: a valid base URL; the key is checked by the first request."""
    env = dict(os.environ if env is None else env)
    report = Readiness(transport="direct")
    report.env_present = {name: bool(env.get(name)) for name in SECRET_ENV_VARS + NON_SECRET_ENV_VARS}
    report.non_secret_env = {name: env[name] for name in NON_SECRET_ENV_VARS if env.get(name)}
    key = (env.get("QLOO_API_KEY") or "").strip()
    if key and key != PROXY_KEY_PLACEHOLDER:
        report.credential_note = "QLOO_API_KEY from the environment (value not shown)"
    else:
        report.credential_note = ("no key in this process; relies on the cloud environment's API credential "
                                  "for the base URL host (only a live request can confirm it)")
    try:
        report.base_url = validate_base_url(env.get("QLOO_BASE_URL", ""))
    except ValueError as exc:
        report.reasons.append(f"QLOO_BASE_URL: {exc}")
        return report
    report.live_ready = True
    return report

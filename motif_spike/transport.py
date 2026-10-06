"""How adapter commands are executed.

* `DirectTransport` (live, default) sends the HTTPS request itself. The
  organizers allow participants to build their own tooling, and it keeps the
  full response body (the harness prints only part of it).
* `HarnessTransport` (live) runs the official `qloo` binary as a subprocess.
* `FixtureTransport` (synthetic) answers from local fixture files. It has no
  code path to a process or the network, and the runner never swaps one
  transport for another: a failed live call stays a failed live call.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .adapter import DRY_RUN_SUPPORTED, http_request, parse_flags

DEFAULT_TIMEOUT_S = 90.0
# Value of QLOO_API_KEY meaning "the cloud environment injects the real key".
PROXY_KEY_PLACEHOLDER = "proxy-injected"
_LOOPBACK = {"localhost", "127.0.0.1", "::1"}


@dataclass
class ProcessResult:
    exit_code: Optional[int]
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    missing_binary: bool = False


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def harness_command(env: Optional[Mapping[str, str]] = None) -> Optional[List[str]]:
    """Locate the harness: $QLOO_HARNESS_BIN (non-secret path) or `qloo` on PATH."""
    env = os.environ if env is None else env
    configured = (env.get("QLOO_HARNESS_BIN") or "").strip()
    if configured:
        return [configured] if Path(configured).exists() else shlex.split(configured)
    found = shutil.which("qloo", path=env.get("PATH"))
    return [found] if found else None


def direct_api_key(env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The key the direct transport sends, or None to let the environment inject it."""
    env = os.environ if env is None else env
    value = (env.get("QLOO_API_KEY") or "").strip()
    return None if not value or value == PROXY_KEY_PLACEHOLDER else value


def validate_base_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url or "")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in _LOOPBACK):
        raise ValueError("Qloo base URL must use HTTPS (HTTP only for a loopback test server)")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Qloo base URL must be a plain https://host[/path] without credentials or query")
    return base_url.rstrip("/")


def _api_error(message: str, exit_code: int = 5) -> str:
    # Same structure the harness prints, so adapter.classify treats both alike.
    return json.dumps({"error": True, "code": "API_ERROR", "message": message})


class DirectTransport:
    """Sends each adapter command as one HTTPS GET to the Qloo API.

    The key is attached only if a real QLOO_API_KEY is in the environment. In a
    Claude Code cloud environment the key lives in an API credential and the
    agent proxy adds it on the way out, so nothing secret exists in this process.
    """

    mode = "live"
    name = "direct"

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout_s: float = DEFAULT_TIMEOUT_S):
        self.base_url = validate_base_url(base_url)
        self._api_key = api_key
        self.timeout_s = timeout_s
        host = urllib.parse.urlparse(self.base_url).hostname
        handlers = [urllib.request.ProxyHandler({})] if host in _LOOPBACK else []
        self._opener = urllib.request.build_opener(*handlers)

    def supports_preview(self, operation: str) -> bool:
        return True

    def describe(self, argv: Sequence[str]) -> Dict[str, Any]:
        path, params = http_request(argv)
        return {"method": "GET", "url": self.base_url + path, "params": params}

    def execute(self, argv: Sequence[str], timeout_s: Optional[float] = None) -> ProcessResult:
        try:
            request = self.describe(argv)
        except (KeyError, ValueError) as exc:
            return ProcessResult(2, json.dumps({"error": True, "code": "BAD_USAGE", "message": f"bad command: {exc}"}), "", 0)
        if "--dry-run" in argv:
            return ProcessResult(0, json.dumps(request), "", 0)
        url = request["url"] + "?" + urllib.parse.urlencode(request["params"])
        headers = {"Accept": "application/json", "User-Agent": "motif-spike"}
        if self._api_key:
            headers["X-Api-Key"] = self._api_key
        started = time.monotonic()

        def elapsed() -> int:
            return int((time.monotonic() - started) * 1000)

        try:
            with self._opener.open(urllib.request.Request(url, headers=headers), timeout=timeout_s or self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            return ProcessResult(0, body, "", elapsed())
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                payload = json.loads(exc.read().decode("utf-8", errors="replace") or "null")
                if isinstance(payload, dict):
                    detail = str(payload.get("message") or payload.get("error") or "")
            except (ValueError, OSError):
                pass
            message = f"API request failed: {exc.code} {exc.reason}" + (f" ({detail[:300]})" if detail else "")
            return ProcessResult(5, _api_error(message), "", elapsed())
        except (socket.timeout, TimeoutError):
            return ProcessResult(None, "", "", elapsed(), timed_out=True)
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                return ProcessResult(None, "", "", elapsed(), timed_out=True)
            return ProcessResult(5, _api_error(f"network error: {exc.reason}"), "", elapsed())


class HarnessTransport:
    mode = "live"
    name = "harness"

    def supports_preview(self, operation: str) -> bool:
        return operation in DRY_RUN_SUPPORTED

    def __init__(self, command: Sequence[str], timeout_s: float = DEFAULT_TIMEOUT_S, env: Optional[Mapping[str, str]] = None):
        self.command = list(command)
        self.timeout_s = timeout_s
        self.env = dict(os.environ if env is None else env)
        self.env["NO_COLOR"] = "1"

    def execute(self, argv: Sequence[str], timeout_s: Optional[float] = None) -> ProcessResult:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                self.command + list(argv),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s or self.timeout_s,
                env=self.env,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return ProcessResult(None, "", "", 0, missing_binary=True)
        except subprocess.TimeoutExpired as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return ProcessResult(None, _text(exc.stdout), _text(exc.stderr), elapsed, timed_out=True)
        elapsed = int((time.monotonic() - started) * 1000)
        return ProcessResult(completed.returncode, completed.stdout or "", completed.stderr or "", elapsed)


class FixtureTransport:
    """Replays a synthetic scenario. Every answer is a local, invented document."""

    mode = "synthetic"
    name = "fixture"

    def supports_preview(self, operation: str) -> bool:
        return operation in DRY_RUN_SUPPORTED

    def __init__(self, scenario: Dict[str, Any], fixtures_dir: Path):
        self.scenario = scenario
        self.fixtures_dir = fixtures_dir
        self.calls: List[List[str]] = []
        self._cursor: Dict[int, int] = {}

    def execute(self, argv: Sequence[str], timeout_s: Optional[float] = None) -> ProcessResult:
        argv = list(argv)
        self.calls.append(argv)
        if "--dry-run" in argv:
            return ProcessResult(0, json.dumps(self._synthetic_preview(argv)), "", 0)
        for index, rule in enumerate(self.scenario.get("responses", [])):
            if self._matches(rule.get("match", {}), argv):
                sequence = rule["sequence"]
                position = self._cursor.get(index, 0)
                self._cursor[index] = position + 1
                return self._render(sequence[min(position, len(sequence) - 1)])
        missing = {"error": True, "code": "SYNTHETIC_FIXTURE_MISSING", "message": "No synthetic fixture matches this command."}
        return ProcessResult(97, json.dumps(missing), "", 0)

    _flags = staticmethod(parse_flags)

    def _matches(self, match: Dict[str, Any], argv: Sequence[str]) -> bool:
        command = match.get("command", [])
        if list(argv[: len(command)]) != list(command):
            return False
        flags = self._flags(argv)
        for flag, expected in match.get("flags", {}).items():
            if flags.get(flag) != expected:
                return False
        if "input" in match:
            try:
                payload = json.loads(flags.get("--input", "null"))
            except ValueError:
                return False
            if not isinstance(payload, dict) or any(payload.get(k) != v for k, v in match["input"].items()):
                return False
        return True

    def _render(self, response: Dict[str, Any]) -> ProcessResult:
        if response.get("timeout"):
            return ProcessResult(None, "", "", 0, timed_out=True)
        if "stdout_file" in response:
            stdout = (self.fixtures_dir / response["stdout_file"]).read_text(encoding="utf-8")
        elif "stdout_text" in response:
            stdout = response["stdout_text"]
        else:
            stdout = json.dumps(response.get("stdout"))
        return ProcessResult(response.get("exit_code", 0), stdout, response.get("stderr", ""), 0)

    def _synthetic_preview(self, argv: Sequence[str]) -> Dict[str, Any]:
        flags = {k.lstrip("-"): v for k, v in self._flags(argv).items() if k not in ("--params",)}
        command = [a for a in argv[:2] if not a.startswith("--")]
        return {
            "_synthetic_fixture": True,
            "method": "GET",
            "url": "synthetic://no-network/" + "/".join(command),
            "params": flags,
        }

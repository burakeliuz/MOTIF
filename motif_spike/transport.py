"""How harness commands are executed.

* `HarnessTransport` (live) runs the real `qloo` binary as a subprocess.
* `FixtureTransport` (synthetic) answers from local fixture files. It has no
  code path to a process or the network, and the runner never swaps one
  transport for the other: a failed live call stays a failed live call.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

DEFAULT_TIMEOUT_S = 90.0


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


class HarnessTransport:
    mode = "live"

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

    @staticmethod
    def _flags(argv: Sequence[str]) -> Dict[str, str]:
        flags: Dict[str, str] = {}
        for i, token in enumerate(argv):
            if token.startswith("--") and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                flags[token] = argv[i + 1]
        return flags

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

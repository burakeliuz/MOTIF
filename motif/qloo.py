"""Budgeted Qloo access for the engine, live or replayed from a recorded run.

Live access goes through motif_spike's existing transports (DirectTransport by
default); no other integration exists. Recorded access replays response bodies
saved by an earlier live run and never touches the network. The two never mix:
a request missing from a recording is reported as `not_recorded`, and a failed
live request is never answered from a recording, a fixture, or another endpoint.

Budget: every real network attempt (retries included) counts. A credential
failure (401, or 403 before any success) stops the session.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from motif_spike import adapter
from motif_spike.adapter import ABORT_STATUSES, DATA_STATUSES, RETRYABLE_STATUSES, classify, http_request
from motif_spike.redact import redact, truncate
from motif_spike.runner import signature
from motif_spike.util import append_jsonl, iso, read_json, read_jsonl, utc_now, write_json

SUCCESS = ("ok", "ok_empty")


class QlooAccess:
    """Common bookkeeping: request log, in-session cache, budget, abort."""

    label = "abstract"

    def __init__(self, session_dir: Optional[Path], max_requests: int):
        self.session_dir = Path(session_dir) if session_dir else None
        self.max_requests = max_requests
        self.network_attempts = 0
        self.seq = 0
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.abort_reason: Optional[str] = None
        self.successes = 0
        self.log: List[Dict[str, Any]] = []

    def _key(self, argv: Sequence[str]) -> str:
        return signature(argv, self.cache_namespace())

    def cache_namespace(self) -> str:
        raise NotImplementedError

    def request(self, operation: str, argv: List[str]) -> Dict[str, Any]:
        key = self._key(argv)
        if key in self.cache:
            cached = dict(self.cache[key])
            cached["served_from"] = "session_cache"
            return cached
        self.seq += 1
        path, params = http_request(argv)
        rec = {"request_id": f"local:req:{self.seq:04d}", "operation": operation, "path": path, "params": params,
               "signature": key, "replay_signature": signature(argv, "direct"), "access": self.label, "status": None, "attempts": [], "error": None,
               "fetched_at": None, "response_ref": None, "body": None}
        self._perform(operation, argv, rec)
        if rec["status"] in SUCCESS:
            self.cache[key] = rec
        self._persist(rec)
        return rec

    def _perform(self, operation: str, argv: List[str], rec: Dict[str, Any]) -> None:
        raise NotImplementedError

    def _persist(self, rec: Dict[str, Any]) -> None:
        public = {k: v for k, v in rec.items() if k != "body"}
        self.log.append(public)
        if self.session_dir:
            append_jsonl(self.session_dir / "requests.jsonl", public)


class LiveQloo(QlooAccess):
    label = "live"

    def __init__(self, transport: Any, base_url: str, session_dir: Optional[Path], max_requests: int,
                 max_retries: int = 2, backoff_s: Sequence[float] = (3, 10), timeout_s: float = 60,
                 sleep: Callable[[float], None] = None):
        super().__init__(session_dir, max_requests)
        self.transport = transport
        self.base_url = base_url
        self.max_retries = max_retries
        self.backoff_s = list(backoff_s)
        self.timeout_s = timeout_s
        import time
        self.sleep = sleep or time.sleep

    def cache_namespace(self) -> str:
        return f"live:{getattr(self.transport, 'name', 'unknown')}:{self.base_url}"

    def _perform(self, operation: str, argv: List[str], rec: Dict[str, Any]) -> None:
        if self.abort_reason:
            rec.update(status="skipped_after_auth_error", error={"message_redacted": self.abort_reason})
            return
        outcome = None
        result = None
        for attempt in range(self.max_retries + 1):
            if self.network_attempts >= self.max_requests:
                rec["attempts"].append({"attempt": attempt + 1, "status": "skipped_budget"})
                if outcome is None:
                    rec.update(status="skipped_budget",
                               error={"message_redacted": f"request budget of {self.max_requests} network attempts reached"})
                    return
                break
            result = self.transport.execute(argv, self.timeout_s)
            self.network_attempts += 1
            outcome = classify(operation, result)
            rec["attempts"].append({"attempt": attempt + 1, "status": outcome.status, "duration_ms": result.duration_ms})
            if outcome.status in RETRYABLE_STATUSES and attempt < self.max_retries:
                self.sleep(self.backoff_s[min(attempt, len(self.backoff_s) - 1)])
                continue
            break
        rec["status"] = outcome.status
        rec["fetched_at"] = iso(utc_now())
        if outcome.error_code or outcome.error_message:
            rec["error"] = {"code": outcome.error_code, "message_redacted": truncate(redact(outcome.error_message or ""), 1000)}
        if outcome.status in DATA_STATUSES:
            rec["body"] = outcome.doc
            if self.session_dir:
                ref = f"responses/{self.seq:04d}.json"
                (self.session_dir / "responses").mkdir(parents=True, exist_ok=True)
                (self.session_dir / ref).write_text(result.stdout, encoding="utf-8")
                rec["response_ref"] = ref
        if outcome.status in SUCCESS:
            self.successes += 1
        if outcome.status in ABORT_STATUSES or (outcome.status == "forbidden" and self.successes == 0):
            self.abort_reason = f"{outcome.status} on {rec['request_id']}; the session stops (no other credential, endpoint, or recorded data is tried)"


class RecordedQloo(QlooAccess):
    """Replays bodies saved by a live run (motif_spike run or a motif session). No network."""

    label = "recorded"

    def __init__(self, recording_dir, session_dir: Optional[Path], max_requests: int):
        """`recording_dir` is one directory or a list of them (indexes are merged; the first one wins)."""
        super().__init__(session_dir, max_requests)
        dirs = [Path(d) for d in (recording_dir if isinstance(recording_dir, (list, tuple)) else [recording_dir])]
        self.recording_dir = dirs[0]
        self.recording_dirs = dirs
        self.index: Dict[str, Dict[str, Any]] = {}
        meta_file = self.recording_dir / "run.json"
        self.recording_meta = read_json(meta_file) if meta_file.exists() else {}
        for rec_dir in dirs:
            root = rec_dir.parent.parent  # data/raw/<run> -> data
            for row in read_jsonl(rec_dir / "requests.jsonl"):
                if row.get("status") not in SUCCESS or not row.get("response_ref"):
                    continue
                ref = row["response_ref"]
                # motif_spike runs store paths relative to the data root; motif sessions relative to the session
                path = (root / ref) if ref.startswith("raw/") else (rec_dir / ref)
                self.index.setdefault(row.get("replay_signature") or row["signature"],
                                      {"path": path, "request_id": row["request_id"], "run": rec_dir.name,
                                       "fetched_at": row.get("finished_at") or row.get("fetched_at")})

    def cache_namespace(self) -> str:
        return "direct"  # recordings are keyed exactly like live direct-transport requests

    def _perform(self, operation: str, argv: List[str], rec: Dict[str, Any]) -> None:
        hit = self.index.get(rec["replay_signature"])
        if not hit or not Path(hit["path"]).exists():
            rec.update(status="not_recorded", error={"message_redacted": "this request is not in the recording; nothing is sent to Qloo in recorded mode"})
            return
        body = json.loads(Path(hit["path"]).read_text(encoding="utf-8"))
        rec.update(status=classify(operation, _Replay(json.dumps(body))).status, body=body,
                   fetched_at=hit["fetched_at"], response_ref=str(hit["path"]),
                   recorded_from={"run_id": hit.get("run") or self.recording_dir.name, "request_id": hit["request_id"]})


class _Replay:
    exit_code = 0
    stderr = ""
    timed_out = False
    missing_binary = False
    duration_ms = 0

    def __init__(self, stdout: str):
        self.stdout = stdout


def search_argv(name: str, take: int) -> List[str]:
    return adapter.search_argv(name, take)


def entity_argv(entity_id: str) -> List[str]:
    return adapter.seed_detail_argv(entity_id)


def related_argv(entity_id: str, entity_type: str, take: int) -> List[str]:
    # explainability stays on so requests match stored recordings; MOTIF does not use it
    return adapter.related_argv(entity_id, entity_type, take, explainability=True)


def save_session_meta(session_dir: Optional[Path], name: str, obj: Any) -> None:
    if session_dir:
        write_json(Path(session_dir) / name, obj)

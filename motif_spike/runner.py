"""Execute a plan: resolve each seed, then request its evidence. Writes raw output only.

Order per seed: search -> (resolved?) seed detail -> related entities per
domain -> seed tag insights. Dependent requests are never sent for a seed that
is unresolved or ambiguous. A credential failure stops the run; nothing falls
back to another endpoint, credential, or fixture.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import adapter
from .adapter import (
    ABORT_STATUSES,
    DATA_STATUSES,
    DRY_RUN_SUPPORTED,
    OP_RELATED,
    OP_SEARCH,
    OP_SEED_DETAIL,
    OP_SEED_TAGS,
    RETRYABLE_STATUSES,
    Outcome,
    classify,
)
from .manifest import Domain, Plan, Seed
from .normalize import candidate_views
from .redact import contains_secret, redact, truncate
from .resolve import RESOLVED_STATUSES, resolve_seed
from .transport import ProcessResult
from .util import RunPaths, append_jsonl, iso, read_json, read_jsonl, request_id, utc_now, write_json


def signature(argv: Sequence[str]) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(list(argv)).encode("utf-8")).hexdigest()


def build_reuse_index(root: Path, exclude_run: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Successful live responses from earlier runs, keyed by command signature."""
    index: Dict[str, Dict[str, Any]] = {}
    raw = root / "raw"
    if not raw.exists():
        return index
    for run_dir in sorted(p for p in raw.iterdir() if p.is_dir()):
        run_file = run_dir / "run.json"
        if run_dir.name == exclude_run or not run_file.exists():
            continue
        run = read_json(run_file)
        if run.get("mode") != "live" or run.get("synthetic"):
            continue
        for rec in read_jsonl(run_dir / "requests.jsonl"):
            if rec.get("status") in ("ok", "ok_empty") and rec.get("response_ref") and not rec.get("reused_from"):
                index[rec["signature"]] = {
                    "run_id": run["run_id"],
                    "request_id": rec["request_id"],
                    "executed_at": rec.get("finished_at"),
                    "path": str(root / rec["response_ref"]),
                    "api_request_preview": rec.get("api_request_preview"),
                    "preview_source": rec.get("preview_source"),
                }
    return index


class Runner:
    def __init__(
        self,
        plan: Plan,
        transport: Any,
        paths: RunPaths,
        *,
        scenario: Optional[str] = None,
        readiness: Optional[Dict[str, Any]] = None,
        harness_version: Optional[str] = None,
        registry_version: Optional[str] = None,
        reuse_index: Optional[Dict[str, Dict[str, Any]]] = None,
        sleep: Callable[[float], None] = time.sleep,
        log: Callable[[str], None] = lambda line: None,
    ):
        self.plan = plan
        self.transport = transport
        self.paths = paths
        self.mode = transport.mode
        self.synthetic = self.mode == "synthetic"
        self.scenario = scenario
        self.readiness = readiness
        self.harness_version = harness_version
        self.registry_version = registry_version
        # Synthetic runs never reuse anything; live runs reuse only live responses.
        self.reuse_index = {} if self.synthetic else dict(reuse_index or {})
        self.sleep = sleep
        self.log = log
        self.seq = 0
        self.invocations = 0
        self.successes = 0
        self.abort_reason: Optional[str] = None
        self.records: List[Dict[str, Any]] = []
        self.started_at = iso(utc_now())

    # -- public ---------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        self.paths.responses_dir.mkdir(parents=True, exist_ok=True)
        run = self._run_record(status="running")
        write_json(self.paths.run_record, run)
        try:
            for seed in self.plan.seeds:
                self._seed_flow(seed)
        except KeyboardInterrupt:
            write_json(self.paths.run_record, self._run_record(status="interrupted"))
            raise
        run = self._run_record(status="aborted_auth_error" if self.abort_reason else "completed")
        write_json(self.paths.run_record, run)
        return run

    # -- flow -------------------------------------------------------------------

    def _seed_flow(self, seed: Seed) -> None:
        search_rec, outcome = self._request(OP_SEARCH, seed, None, adapter.search_argv(seed.input_name, self.plan.search_take, seed.search_type))
        doc = outcome.doc if outcome and search_rec["status"] in DATA_STATUSES else None
        candidates = candidate_views(search_rec, doc, self.paths.run_id, self.synthetic)
        resolution = resolve_seed(seed, candidates, search_rec["status"])
        search_rec["runtime_resolution"] = {k: resolution[k] for k in ("status", "method", "qloo_id", "name")}
        self._log_record(search_rec)

        entity_id = resolution["qloo_id"] if resolution["status"] in RESOLVED_STATUSES else None
        planned: List[Tuple[str, Optional[Domain]]] = []
        if self.plan.seed_detail:
            planned.append((OP_SEED_DETAIL, None))
        planned += [(OP_RELATED, d) for d in self.plan.domains]
        planned.append((OP_SEED_TAGS, None))

        for operation, domain in planned:
            if entity_id is None:
                if self.abort_reason:
                    rec = self._skipped(operation, seed, domain, "skipped_after_auth_error", self.abort_reason)
                elif search_rec["status"] == "skipped_budget":
                    rec = self._skipped(operation, seed, domain, "skipped_budget", search_rec["skip_reason"])
                else:
                    rec = self._skipped(operation, seed, domain, "skipped_unresolved_seed", f"seed resolution: {resolution['status']}")
                self._log_record(rec)
                continue
            if operation == OP_SEED_DETAIL:
                argv = adapter.seed_detail_argv(entity_id)
            elif operation == OP_RELATED:
                argv = adapter.related_argv(entity_id, domain.entity_type, self.plan.related_take, self.plan.explainability)
            else:
                argv = adapter.seed_tags_argv(entity_id, self.plan.seed_tags_limit)
            rec, _ = self._request(operation, seed, domain, argv, entity_id)
            self._log_record(rec)

    # -- one request ------------------------------------------------------------

    def _base_record(self, operation: str, seed: Seed, domain: Optional[Domain], entity_id: Optional[str]) -> Dict[str, Any]:
        self.seq += 1
        comparability: Dict[str, Any] = {"operation": operation}
        if operation == OP_SEARCH:
            comparability.update(take=self.plan.search_take, type=seed.search_type)
        elif operation == OP_RELATED:
            comparability.update(entity_type=domain.entity_type, take=self.plan.related_take, explainability=self.plan.explainability)
        elif operation == OP_SEED_TAGS:
            comparability.update(limit=self.plan.seed_tags_limit)
        return {
            "record_type": "request",
            "request_id": request_id(self.seq),
            "seq": self.seq,
            "run_id": self.paths.run_id,
            "mode": self.mode,
            "synthetic": self.synthetic,
            "operation": operation,
            "seed_key": seed.key,
            "seed_input_name": seed.input_name,
            "seed_qloo_id": entity_id,
            "domain_key": domain.key if domain else None,
            "requested_entity_type": domain.entity_type if domain else None,
            "explainability_requested": bool(operation == OP_RELATED and self.plan.explainability),
            "comparability": comparability,
            "harness_command": None,
            "signature": None,
            "api_request_preview": None,
            "preview_source": None,
            "started_at": iso(utc_now()),
            "finished_at": None,
            "status": None,
            "attempts": [],
            "error": None,
            "response_ref": None,
            "output_shape": None,
            "result_count": None,
            "reused_from": None,
            "skip_reason": None,
            "redaction_applied": False,
        }

    def _skipped(self, operation: str, seed: Seed, domain: Optional[Domain], status: str, reason: str) -> Dict[str, Any]:
        rec = self._base_record(operation, seed, domain, None)
        rec.update(status=status, skip_reason=reason, finished_at=rec["started_at"])
        return rec

    def _request(self, operation: str, seed: Seed, domain: Optional[Domain], argv: List[str],
                 entity_id: Optional[str] = None) -> Tuple[Dict[str, Any], Optional[Outcome]]:
        rec = self._base_record(operation, seed, domain, entity_id)
        rec["harness_command"] = adapter.display_command(argv)
        rec["signature"] = signature(argv)

        if self.abort_reason:
            rec.update(status="skipped_after_auth_error", skip_reason=self.abort_reason, finished_at=rec["started_at"])
            return rec, None

        reused = self.reuse_index.get(rec["signature"])
        if reused:
            return self._reuse(rec, operation, reused)

        if self.invocations >= self.plan.max_requests:
            rec.update(status="skipped_budget", skip_reason=f"max_requests={self.plan.max_requests} reached",
                       finished_at=rec["started_at"])
            return rec, None

        if operation in DRY_RUN_SUPPORTED:
            self._preview(rec, argv)

        outcome: Optional[Outcome] = None
        result: Optional[ProcessResult] = None
        for attempt in range(self.plan.max_retries + 1):
            if attempt and self.invocations >= self.plan.max_requests:
                rec["attempts"].append({"attempt": attempt + 1, "status": "not_retried_budget"})
                break
            result = self.transport.execute(argv, self.plan.timeout_s)
            self.invocations += 1
            outcome = classify(operation, result)
            rec["attempts"].append({
                "attempt": attempt + 1, "status": outcome.status, "exit_code": result.exit_code,
                "duration_ms": result.duration_ms, "error_code": outcome.error_code,
            })
            if outcome.status in RETRYABLE_STATUSES and attempt < self.plan.max_retries:
                backoff = self.plan.retry_backoff_s[min(attempt, len(self.plan.retry_backoff_s) - 1)]
                self.sleep(backoff)
                continue
            break

        rec["status"] = outcome.status
        rec["finished_at"] = iso(utc_now())
        rec["output_shape"] = outcome.shape
        rec["result_count"] = outcome.item_count
        if outcome.error_code or outcome.error_message:
            rec["error"] = {
                "code": outcome.error_code,
                "message_redacted": truncate(redact(outcome.error_message or ""), 2000),
            }
        if operation == OP_SEED_TAGS and isinstance(outcome.doc, dict):
            requests = (outcome.doc.get("provenance") or {}).get("requests")
            if requests is not None:
                rec["api_request_preview"] = json.loads(redact(json.dumps(requests)))
                rec["preview_source"] = "workflow provenance (synthetic fixture)" if self.synthetic else "workflow provenance"

        if outcome.status in DATA_STATUSES:
            self._save_raw(rec, result.stdout, "json")
            if outcome.status in ("ok", "ok_empty"):
                self.successes += 1
                # Two seeds resolving to one entity must not trigger the same request twice.
                self.reuse_index[rec["signature"]] = {
                    "run_id": self.paths.run_id, "request_id": rec["request_id"], "executed_at": rec["finished_at"],
                    "path": str(self.paths.root / rec["response_ref"]),
                    "api_request_preview": rec["api_request_preview"], "preview_source": rec["preview_source"],
                }
        elif outcome.status == "unparseable_output" and result and result.stdout:
            self._save_raw(rec, result.stdout, "txt")

        if outcome.status in ABORT_STATUSES or (outcome.status == "forbidden" and self.successes == 0):
            self.abort_reason = f"{outcome.status} on {rec['request_id']} ({operation}); no other credential, endpoint, or fixture is tried"
        return rec, outcome

    def _preview(self, rec: Dict[str, Any], argv: List[str]) -> None:
        """Ask the harness (--dry-run, no API call) which HTTP request it would send."""
        result = self.transport.execute(argv + ["--dry-run"], 30)
        try:
            preview = json.loads(redact(result.stdout))
        except ValueError:
            preview = None
        if isinstance(preview, dict) and preview.get("error") is not True:
            rec["api_request_preview"] = preview
            rec["preview_source"] = "synthetic preview (no request)" if self.synthetic else "harness --dry-run"
        else:
            rec["preview_source"] = "unavailable: dry-run did not return a request description"

    def _reuse(self, rec: Dict[str, Any], operation: str, source: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Outcome]]:
        text = Path(source["path"]).read_text(encoding="utf-8")
        outcome = classify(operation, ProcessResult(0, text, "", 0))
        rec.update(
            status=outcome.status, finished_at=iso(utc_now()), output_shape=outcome.shape, result_count=outcome.item_count,
            reused_from={k: source[k] for k in ("run_id", "request_id", "executed_at")},
            api_request_preview=source.get("api_request_preview"),
            preview_source=source.get("preview_source") or "not captured for the reused response",
        )
        self._save_raw(rec, text, "json")
        if outcome.status in ("ok", "ok_empty"):
            self.successes += 1
        return rec, outcome

    def _save_raw(self, rec: Dict[str, Any], text: str, suffix: str) -> None:
        if contains_secret(text):
            text = redact(text)
            rec["redaction_applied"] = True
        path = self.paths.response_file(rec["seq"], suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        rec["response_ref"] = self.paths.rel(path)

    def _log_record(self, rec: Dict[str, Any]) -> None:
        self.records.append(rec)
        append_jsonl(self.paths.requests_log, rec)
        where = "/".join(x for x in (rec["seed_key"], rec.get("domain_key")) if x)
        extra = f" ({rec['result_count']} items)" if rec.get("result_count") is not None else ""
        reuse = " [reused]" if rec.get("reused_from") else ""
        self.log(f"  {rec['request_id']}  {rec['operation']:<17} {where:<22} -> {rec['status']}{extra}{reuse}")

    def _run_record(self, status: str) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for rec in self.records:
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
        if self.synthetic:
            live_status = "not_live"
        elif self.abort_reason:
            live_status = "aborted_after_credential_failure"
        elif status in ("running", "interrupted"):
            live_status = "in_progress" if status == "running" else "interrupted"
        else:
            live_status = "executed"
        return {
            "record_type": "run",
            "run_id": self.paths.run_id,
            "mode": self.mode,
            "synthetic": self.synthetic,
            "scenario": self.scenario,
            "plan_name": self.plan.name,
            "status": status,
            "live_execution_status": live_status,
            "abort_reason": self.abort_reason,
            "started_at": self.started_at,
            "finished_at": None if status == "running" else iso(utc_now()),
            "versions": {
                "adapter": adapter.ADAPTER_VERSION,
                "parser_status": adapter.PARSER_STATUS,
                "manifest": self.plan.manifest_version,
                "draft_rule_registry": self.registry_version,
                "harness": self.harness_version,
            },
            "readiness": self.readiness,
            "plan": self.plan.snapshot(),
            "counts": {"requests": len(self.records), "harness_invocations": self.invocations, "by_status": counts},
        }

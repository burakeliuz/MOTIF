"""MOTIF web server (Python standard library only; the LLM SDK is optional).

  python3 -m motif.web [--host 127.0.0.1] [--port 8000] [--recorded RUN_DIR ...]

The browser gets static files and a small JSON API. Research runs server-side in
a background thread per session; the browser polls the real session state. Keys
are read from the server environment only and never appear in any response.

Guards against unnecessary Qloo or LLM calls:
* identical requests (same reference, type, answer, and mode) return the existing
  session for 30 minutes, so refresh, back, or a double click does not start a new one;
* follow-up answers (choosing a candidate, resolving a conflict) reuse the parent
  session's Qloo access, so the search and fetched pages are served from its cache;
* per-IP and per-day session caps, a per-day Qloo attempt cap, and the LLM call
  ledger's daily cap. A cap that is reached is reported, never replaced by fake data.

`--recorded` (local development and tests only) replays stored live runs and shows
one small "Recorded preview" label; it is refused on Render. A live server shows
no recorded wording at all.

Paid LLM calls also depend on the budget guard (`guard.py`): when the call counter
would not survive a restart, Claude is paused and the labelled template is used.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from motif_spike.manifest import harness_environment, live_environment, load_manifest
from motif_spike.readiness import check_direct_readiness
from motif_spike.transport import DirectTransport, direct_api_key
from motif_spike.util import data_root, iso, utc_now, write_json

from ..agent import Controller
from ..brief import build_brief
from ..config import AXES, EngineConfig, load_config
from ..interpret import suggest as suggest_readings
from ..llm import write_prose, writer_from_env
from ..qloo import LiveQloo, RecordedQloo
from .access import AccessGate
from .guard import PAUSED_NOTE, llm_guard
from .present import candidate_view, result_view
from .usage import UsageError, UsageStore

STATIC = Path(__file__).resolve().parent / "static"
STEP_ORDER = [("resolve", "Find the brand in Qloo"), ("own", "Read the brand's own Qloo description"),
              ("brand", "Related brands"), ("movie", "Related films"), ("artist", "Related music artists"),
              ("engine", "Translate with MOTIF's rules"), ("brief", "Write the perfumer brief")]
CSP = ("default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
NAME_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,80}$")
INTENT_RE = re.compile(r"^[^\x00-\x1f\x7f]{0,140}$")
REUSE_S = 1800


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class WebSession:
    def __init__(self, sid: str, key: tuple, params: Dict[str, Any], data_label: str, parent: Optional["WebSession"]):
        self.id = sid
        self.key = key
        self.params = params
        self.parent = parent
        self.created = time.time()
        self.data_label = data_label
        self.status = "running"
        self.phase = "resolve"
        self.controller: Optional[Controller] = None
        self.access = None
        self.outcome: Optional[Dict[str, Any]] = None
        self.brief: Optional[Dict[str, Any]] = None
        self.prose: Optional[Dict[str, Any]] = None
        self.llm_configured = False
        self.suggestions: Optional[Dict[str, Any]] = None
        self.suggest_lock = threading.Lock()
        self.error: Optional[str] = None
        self.finished: Optional[float] = None
        self.retry_of: Optional[str] = None
        self.retried_by: Optional[str] = None


class Hub:
    def __init__(self, config: EngineConfig, root: Path, recorded: Optional[List[Path]] = None,
                 env: Optional[Dict[str, str]] = None):
        self.config = config
        self.env = os.environ if env is None else env  # LLM settings; tests pass their own mapping
        self.root = root
        self.recorded = recorded
        self.sessions: Dict[str, WebSession] = {}
        self.by_key: Dict[tuple, str] = {}
        self.by_ref: Dict[tuple, tuple] = {}  # reference -> (access, created, lock): one Qloo cache per reference
        self.lock = threading.Lock()
        self.ip_hits: Dict[str, deque] = defaultdict(deque)
        self.usage = UsageStore(root / "web_usage.json")
        self.limits = {"per_ip_hour": _int_env("MOTIF_WEB_SESSIONS_PER_IP_HOUR", 8),
                       "per_day": _int_env("MOTIF_WEB_SESSIONS_PER_DAY", 120),
                       "qloo_per_day": _int_env("MOTIF_QLOO_MAX_CALLS_PER_DAY", 400)}
        self.guard = llm_guard(self.env, root)
        self.live_ready = None
        if not recorded:
            env = live_environment(harness_environment(load_manifest()))
            ready = check_direct_readiness(env)
            self.live_ready = ready if ready.live_ready else None
            self.live_env = env

    # -- public API -----------------------------------------------------------------

    def _llm_configured(self) -> bool:
        return bool(self.env.get("MOTIF_ANTHROPIC_API_KEY")) and self.env.get("MOTIF_LLM_PROVIDER", "anthropic") != "off"

    def _llm_paused(self) -> bool:
        """A key is configured, but the budget guard does not allow paid calls (see guard.py)."""
        return self._llm_configured() and not self.guard["allowed"]

    def _writer(self):
        if not self.guard["allowed"]:
            return None
        return writer_from_env(self.env, ledger_path=self.root / "llm_calls.jsonl")["writer"]

    def describe(self) -> Dict[str, Any]:
        return {"mode": "recorded" if self.recorded else "live",
                "mode_label": "Recorded preview" if self.recorded else None,  # a live server shows no mode wording
                "live_available": bool(self.recorded or self.live_ready),
                "llm": "paused" if self._llm_paused() else "configured" if self._llm_configured() else "template",
                "examples": ["MUJI", "Ralph Lauren"], "versions": self.config.versions}

    def create(self, body: Dict[str, Any], ip: str) -> (int, Dict[str, Any]):
        reference = str(body.get("reference", "")).strip()
        if not NAME_RE.match(reference):
            return 400, {"error": "Enter a brand name (1 to 80 characters)."}
        ref_type = body.get("type", "brand")
        if ref_type not in ("brand", "any"):
            return 400, {"error": "The MVP researches brands."}
        intent = " ".join(str(body.get("intent") or "").split())
        if not INTENT_RE.match(intent):
            return 400, {"error": "Keep the creative intent to one line of at most 140 characters."}
        choose = body.get("choose") or None
        overrides = body.get("resolve_conflict") or {}
        if not isinstance(overrides, dict) or any(k not in AXES or not isinstance(v, str) for k, v in overrides.items()):
            return 400, {"error": "Invalid conflict answer."}
        parent = self.sessions.get(str(body.get("parent", ""))) if body.get("parent") else None
        mode = "recorded" if self.recorded else "live"
        key = (mode, reference.casefold(), ref_type, choose or "", json.dumps(overrides, sort_keys=True), intent.casefold())
        budget = self.config.params["budget"]["max_requests_per_session"]
        with self.lock:
            existing = self.by_key.get(key)
            if existing and self.sessions[existing].status != "error" and time.time() - self.sessions[existing].created < REUSE_S:
                return 200, {"id": existing, "reused": True}
            if not self.recorded and not self.live_ready:
                return 503, {"error": "Live Qloo access is not configured on this server.", "kind": "qloo_unavailable"}
            if parent is None:  # follow-ups are answers to a question, not new research
                hits = self.ip_hits[ip]
                while hits and time.time() - hits[0] > 3600:
                    hits.popleft()
                if len(hits) >= self.limits["per_ip_hour"]:
                    return 429, {"error": "Too many new searches from this connection; please try again in an hour.", "kind": "rate_limited"}
            try:  # reserve before any paid call; unused Qloo budget is released after the run
                if parent is None and not self.usage.reserve("sessions", 1, self.limits["per_day"]):
                    return 429, {"error": "Today's demo capacity is used up; please try again tomorrow.", "kind": "daily_cap"}
                if not self.usage.reserve("qloo", budget, self.limits["qloo_per_day"]):
                    if parent is None:
                        self.usage.release("sessions", 1)
                    return 429, {"error": "Today's Qloo request budget for this demo is used up.", "kind": "qloo_cap"}
            except UsageError:
                return 503, {"error": "The demo's usage budget cannot be verified right now, so no new research is started.",
                             "kind": "budget_unverified"}
            if parent is None:
                self.ip_hits[ip].append(time.time())
            sid = secrets.token_urlsafe(9)
            session = WebSession(sid, key, {"reference": reference, "type": ref_type, "choose": choose, "overrides": overrides,
                                            "intent": intent or None}, mode, parent)
            session.reserved = budget
            session.day = self.usage.clock()
            self.sessions[sid] = session
            self.by_key[key] = sid
        threading.Thread(target=self._run, args=(session,), daemon=True).start()
        return 202, {"id": sid, "reused": False}

    def view(self, sid: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(sid)
        if not s:
            return None
        name = s.params["reference"]
        out: Dict[str, Any] = {"id": s.id, "status": s.status, "phase": s.phase, "reference": name,
                               "data_label": s.data_label, "steps": self._steps(s), "message": s.error,
                               "choose": s.params["choose"], "overrides": s.params["overrides"],
                               "intent": s.params.get("intent"),
                               "intent_effect": ("Used in the brief only; it changed no motif, direction, or material."
                                                 if s.params.get("intent") else None),
                               "retry": self._retry_state(s)}
        o = s.outcome
        if o:
            res = o.get("resolution") or {}
            if res.get("status") == "resolved":
                name = res.get("name") or name
                out["resolution"] = {"name": res.get("name"), "type": res.get("types"), "method": res.get("method"),
                                     "others": len(res.get("alternatives") or [])}
            q = o.get("question")
            if q and q["kind"] == "choose_entity":
                out["question"] = {"kind": "choose_entity", "why": q["why"],
                                   "options": [candidate_view(c, s.params["type"]) for c in q["options"]]}
            elif q and q["kind"] == "conflict":
                out["question"] = {"kind": "conflict", "axis": q["axis"], "why": q["why"], "options": q["options"]}
            if o.get("result") is not None:
                out["result"] = result_view(name, o["result"], self.config.rules, self.config.palette)
                out["outcome"] = o["result"]["outcome"]
            else:
                out["outcome"] = o.get("outcome")
            if o.get("status") == "stopped":
                out["message"] = self._stop_message(o)
                out["stop_reason"] = o.get("outcome")
                if o.get("result") is not None:
                    out["result"]["headline"] = dict(out["result"]["headline"], label="Partial result")
        if s.prose:
            out["brief"] = {"author": s.prose["author"], "text": s.prose["text"], "note": s.prose.get("note"),
                            "model": (s.prose.get("llm") or {}).get("model") if s.prose["author"] == "llm" else None}
        out["suggestions"] = self._suggestions_view(s)
        if s.access is not None and s.data_label == "recorded":
            out["recorded_from"] = sorted({d.name for d in getattr(s.access, "recording_dirs", [])})
        if o and o.get("result") is not None:
            fetched = sorted({e.get("fetched_at") for e in o["result"]["evidence"] if e.get("fetched_at")})
            out["fetched"] = [fetched[0], fetched[-1]] if fetched else None
        return out

    # -- one controlled retry after a failed Qloo request ---------------------------

    RETRYABLE = ("stopped_request_failed", "error")

    def _retry_kind(self, s: WebSession) -> Optional[str]:
        if s.status == "error":
            return "error"
        if s.status == "stopped" and s.outcome:
            return s.outcome.get("outcome")
        return None

    def _retry_state(self, s: WebSession) -> Dict[str, Any]:
        retryable = self._retry_kind(s) in self.RETRYABLE
        return {"available": retryable and s.retry_of is None and s.retried_by is None,
                "used": s.retry_of is not None, "retried_by": s.retried_by}

    def retry(self, sid: str) -> (int, Dict[str, Any]):
        """Re-run a search stopped by a failed Qloo request, once. Requests that succeeded are served
        from the session cache; only the failed step is sent again, within a fresh, reserved budget."""
        s = self.sessions.get(sid)
        if not s:
            return 404, {"error": "Unknown session."}
        if self._retry_kind(s) not in self.RETRYABLE:
            return 409, {"error": "Only a search stopped by a failed Qloo request can be retried."}
        budget = self.config.params["budget"]["max_requests_per_session"]
        with self.lock:
            if s.retried_by:
                return 200, {"id": s.retried_by, "reused": True}
            if s.retry_of is not None:
                return 409, {"error": "This search was already retried once. Please start a new search later."}
            if not self.recorded and not self.live_ready:
                return 503, {"error": "Live Qloo access is not configured on this server.", "kind": "qloo_unavailable"}
            try:
                if not self.usage.reserve("qloo", budget, self.limits["qloo_per_day"]):
                    return 429, {"error": "Today's Qloo request budget for this demo is used up.", "kind": "qloo_cap"}
            except UsageError:
                return 503, {"error": "The demo's usage budget cannot be verified right now, so nothing is retried.",
                             "kind": "budget_unverified"}
            new_id = secrets.token_urlsafe(9)
            session = WebSession(new_id, s.key + ("retry", s.id), dict(s.params), s.data_label, s)
            session.retry_of = s.id
            session.reserved = budget
            session.day = self.usage.clock()
            self.sessions[new_id] = session
            self.by_key[session.key] = new_id
            self.by_key[s.key] = new_id  # an identical new request now lands on the retried search
            s.retried_by = new_id
        threading.Thread(target=self._run, args=(session,), daemon=True).start()
        return 202, {"id": new_id, "reused": False}

    def brief(self, sid: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(sid)
        return s.brief if s else None

    # -- user-requested interpretation suggestions (never part of the engine result) --------

    def _suggestions_view(self, s: WebSession) -> Dict[str, Any]:
        if s.suggestions is not None:
            return s.suggestions
        has_result = bool(s.outcome and s.outcome.get("result") is not None and s.status in ("completed", "stopped"))
        message = (None if s.llm_configured else
                   "Suggestions need Claude, which is paused on this server; the result is unaffected." if self._llm_paused() else
                   "Suggestions need an LLM key on the server; the result is unaffected.")
        return {"status": "not_requested" if (s.llm_configured and has_result) else "unavailable", "suggestions": [],
                "message": message}

    def suggest(self, sid: str) -> (int, Dict[str, Any]):
        s = self.sessions.get(sid)
        if not s:
            return 404, {"error": "Unknown session."}
        if not (s.outcome and s.outcome.get("result") is not None and s.status in ("completed", "stopped")):
            return 409, {"error": "Suggestions are available once a result exists."}
        with s.suggest_lock:  # one LLM call per session, reused on repeat requests
            if s.suggestions is None:
                name = (s.outcome.get("resolution") or {}).get("name") or s.params["reference"]
                s.suggestions = suggest_readings(self._writer(), name, s.outcome["result"], s.params.get("intent"))
        return 200, s.suggestions

    def decide(self, sid: str, suggestion_id: str, decision: str) -> (int, Dict[str, Any]):
        s = self.sessions.get(sid)
        if not s or not s.suggestions:
            return 404, {"error": "No suggestions for this session."}
        if decision not in ("accept", "reject", "undo"):
            return 400, {"error": "Invalid decision."}
        for item in s.suggestions["suggestions"]:
            if item["id"] == suggestion_id:
                item["decision"] = {"accept": "accepted", "reject": "rejected", "undo": None}[decision]
                item["label"] = ("Accepted by you — your interpretation, not Qloo evidence; no rule applied"
                                 if decision == "accept" else "Suggested interpretation — not applied")
                if s.brief is not None:  # rebuild the brief text record only; no new call
                    s.brief = self._build_brief(s)
                    self._persist(s)
                return 200, s.suggestions
        return 404, {"error": "Unknown suggestion."}

    # -- research ---------------------------------------------------------------------

    def _ref_key(self, session: WebSession) -> tuple:
        return (session.data_label, session.params["reference"].casefold(), session.params["type"])

    def _access(self, session: WebSession):
        if session.parent is not None and session.parent.access is not None:
            return session.parent.access, self.by_ref.get(self._ref_key(session.parent), (None, 0, threading.Lock()))[2]
        with self.lock:  # same reference within the reuse window: same Qloo cache, nothing fetched twice
            hit = self.by_ref.get(self._ref_key(session))
            if hit and time.time() - hit[1] < REUSE_S:
                return hit[0], hit[2]
            access = self._new_access(self.root / "web_sessions" / session.id)
            entry = (access, time.time(), threading.Lock())
            self.by_ref[self._ref_key(session)] = entry
            return access, entry[2]

    def _new_access(self, sdir: Path):
        budget = self.config.params["budget"]
        if self.recorded:
            return RecordedQloo(self.recorded, sdir, budget["max_requests_per_session"])
        transport = DirectTransport(self.live_ready.base_url, api_key=direct_api_key(self.live_env), timeout_s=30)
        return LiveQloo(transport, self.live_ready.base_url, sdir, budget["max_requests_per_session"],
                        budget["max_retries"], budget["retry_backoff_s"], 30)

    def _build_brief(self, s: WebSession) -> Dict[str, Any]:
        accepted = [{k: v for k, v in item.items() if k in ("descriptor", "reading", "design_question", "source", "entities",
                                                             "from_brand_itself")}
                    for item in (s.suggestions or {}).get("suggestions", []) if item.get("decision") == "accepted"]
        meta = {"data_label": s.data_label, "resolution": s.outcome["resolution"], "intent": s.params.get("intent")}
        return build_brief(meta, s.outcome["result"], s.prose, accepted)

    def _run(self, s: WebSession) -> None:
        used = 0
        try:
            access, ref_lock = self._access(s)
            s.access = access
            with ref_lock:  # sessions sharing one Qloo cache run one at a time
                before = access.network_attempts
                if s.retry_of is not None:  # the reserved retry budget comes on top of what was already used
                    access.max_requests = max(access.max_requests, access.network_attempts + s.reserved)
                original = access.request

                def tracked(operation, argv):
                    if operation == "search":
                        s.phase = "resolve"
                    elif operation == "seed_detail":
                        s.phase = "own"
                    else:
                        s.phase = {"urn:entity:brand": "brand", "urn:entity:movie": "movie",
                                   "urn:entity:artist": "artist"}.get(argv[argv.index("--type") + 1], "brand")
                    return original(operation, argv)

                access.request = tracked
                p = s.params
                controller = Controller(access, self.config, p["reference"], p["type"], p["choose"], overrides=p["overrides"])
                s.controller = controller
                try:
                    outcome = controller.run()
                finally:
                    access.request = original
                    used = access.network_attempts - before
            self._release(s, used)
            s.phase = "engine"
            s.outcome = outcome
            if outcome.get("result") is not None and outcome["status"] == "completed":
                s.phase = "brief"
                writer = self._writer()
                s.llm_configured = writer is not None
                name = (outcome.get("resolution") or {}).get("name") or p["reference"]
                s.prose = write_prose(name, outcome["result"], writer, intent=p.get("intent"))
                if writer is None and self._llm_paused():
                    s.prose["note"] = PAUSED_NOTE
                s.brief = self._build_brief(s)
            elif outcome.get("result") is not None:
                s.llm_configured = self._writer() is not None
            self._persist(s, outcome["status"])  # write files before the session reads as finished
            s.phase = "done"
            s.status = outcome["status"]
        except Exception as exc:  # never leak internals; record the kind only
            self._release(s, used)
            s.error = f"Something went wrong on the server ({type(exc).__name__}). No partial result is shown as complete."
            s.phase = "done"
            s.status = "error"
        finally:
            s.finished = time.time()

    def _release(self, s: WebSession, used: int) -> None:
        """Return the unused part of the Qloo reservation once; keeping it is the safe direction on error."""
        if getattr(s, "released", False):
            return
        s.released = True
        try:
            self.usage.release("qloo", max(0, getattr(s, "reserved", 0) - used), getattr(s, "day", None))
        except UsageError:
            pass

    def _persist(self, s: WebSession, status: Optional[str] = None) -> None:
        sdir = self.root / "web_sessions" / s.id
        sdir.mkdir(parents=True, exist_ok=True)
        meta = {"id": s.id, "created": iso(utc_now()), "params": s.params, "data_label": s.data_label,
                "status": status or s.status, "outcome": (s.outcome or {}).get("outcome"), "trace": (s.outcome or {}).get("trace"),
                "network_attempts": getattr(s.access, "network_attempts", None), "versions": self.config.versions,
                "prose": {k: v for k, v in (s.prose or {}).items() if k != "text"} or None,
                "suggestions": s.suggestions}
        write_json(sdir / "session.json", meta)
        if s.brief:
            write_json(sdir / "brief.json", s.brief)

    def _steps(self, s: WebSession) -> List[Dict[str, Any]]:
        trace = list(s.controller.trace) if s.controller else []
        done = {}
        for row in trace:
            act = row["action"]
            k = "resolve" if act == "resolve" else "own" if act == "fetch_own" else act.split(":")[1] if act.startswith("fetch_related") else None
            if k:
                done[k] = row
        domains = (s.controller.domains if s.controller else self.config.params["default_domains"])
        steps = []
        finished = s.status != "running"
        for key, label in STEP_ORDER:
            if key in ("brand", "movie", "artist") and key not in domains:
                continue
            who = "Qloo" if key in ("resolve", "own", "brand", "movie", "artist") else "MOTIF"
            row = done.get(key)
            if row:
                status = {"skip": "skipped", "stop": "stopped", "ask_user": "waiting"}.get(row["decision"], "done")
                cached = row.get("served_from") == "session_cache"
                detail = row["reason"] if status in ("skipped", "stopped", "waiting") else ("reused from this session" if cached else None)
            elif s.phase == key and not finished:
                status, detail = "running", None
            elif key == "engine" and s.outcome and s.outcome.get("result") is not None:
                status, detail = "done", None
            elif key == "brief" and s.prose:
                status = "done"
                if s.prose["author"] == "llm":
                    who = "Claude"
                    detail = "written by " + (s.prose.get("llm") or {}).get("model", "LLM") + ", checked against the engine result"
                else:
                    detail = s.prose.get("note")
            elif key == "brief" and s.phase == "brief" and not finished:
                status, detail = "running", None
                who = "Claude" if s.llm_configured else "MOTIF"
            else:
                status, detail = ("not_run" if finished else "pending"), None
            if status in ("pending", "not_run", "skipped"):
                who = None  # a source label appears only once that stage has actually run
            steps.append({"key": key, "label": label, "status": status, "detail": detail, "who": who})
        return steps

    @staticmethod
    def _stop_message(o: Dict[str, Any]) -> str:
        kind = o.get("outcome")
        return {"stopped_access_error": "Qloo refused the request (credential or permission). Nothing else was tried.",
                "stopped_budget": "This search reached its Qloo request budget.",
                "stopped_request_failed": "A Qloo request failed, even after automatic retries.",
                "not_found": "Qloo returned no entity for this name.",
                "invalid_choice": "That choice was not among Qloo's results.",
                "stopped_not_recorded": "This request is not in the stored recording (recorded mode sends nothing live)."
                }.get(kind, o.get("message") or "The research stopped.")


PUBLIC_FILES = {"/login": "login.html", "/login.js": "login.js", "/app.css": "app.css", "/favicon.svg": "favicon.svg"}
APP_FILES = {"/": "index.html", "/app.js": "app.js", "/strips.js": "strips.js", "/print.js": "print.js", "/print.css": "print.css"}


def make_handler(hub: Hub, gate: Optional[AccessGate] = None):
    """`gate` defaults to the environment's access settings (fail-closed: protection on)."""
    gate = gate if gate is not None else AccessGate.from_env(os.environ)

    class Handler(BaseHTTPRequestHandler):
        server_version = "MOTIF"
        sys_version = ""

        def log_message(self, fmt, *args):  # no request logging of bodies or headers
            pass

        def _headers(self, code: int, ctype: str, length: int, extra: Optional[Dict[str, str]] = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()

        def _json(self, code: int, obj: Any, extra=None):
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self._headers(code, "application/json; charset=utf-8", len(data), extra)
            self.wfile.write(data)

        def _ip(self) -> str:
            fwd = self.headers.get("X-Forwarded-For", "")
            return fwd.split(",")[0].strip() if fwd else self.client_address[0]

        def _file(self, name: str):
            data = (STATIC / name).read_bytes()
            ctype = {"html": "text/html; charset=utf-8", "css": "text/css; charset=utf-8",
                     "js": "text/javascript; charset=utf-8", "svg": "image/svg+xml"}[name.rsplit(".", 1)[1]]
            self._headers(200, ctype, len(data))
            self.wfile.write(data)

        def _redirect(self, location: str):
            self._headers(303, "text/plain; charset=utf-8", 0, {"Location": location})

        def _authorized(self) -> bool:
            return gate.allowed(self.headers.get("Cookie"))

        def _deny(self, path: str):
            if path.startswith("/api/") or path.endswith(".js"):
                return self._json(401, {"error": "Sign-in required.", "kind": "auth_required"})
            return self._redirect("/login")

        def _same_origin(self) -> bool:
            origin = self.headers.get("Origin")
            return not origin or urlparse(origin).netloc == self.headers.get("Host", "")

        def _body(self) -> Optional[Dict[str, Any]]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 4096:
                return None
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return None
            return body if isinstance(body, dict) else None

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/healthz":  # for the host's health check: no data, no API calls
                return self._json(200, {"ok": True})
            if path == "/login" and (not gate.enabled or self._authorized()):
                return self._redirect("/")
            if path in PUBLIC_FILES:
                return self._file(PUBLIC_FILES[path])
            if not self._authorized():
                return self._deny(path)
            if path == "/api/config":
                return self._json(200, hub.describe())
            m = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]{6,20})(/brief\.json)?", path)
            if m:
                if m.group(2):
                    brief = hub.brief(m.group(1))
                    if not brief:
                        return self._json(404, {"error": "No brief for this session."})
                    return self._json(200, brief, {"Content-Disposition": 'attachment; filename="motif-brief.json"'})
                view = hub.view(m.group(1))
                return self._json(200, view) if view else self._json(404, {"error": "Unknown session."})
            if path in APP_FILES:
                return self._file(APP_FILES[path])
            if re.fullmatch(r"/brief/[A-Za-z0-9_-]{6,20}", path):  # printable brief; data comes from the session API
                return self._file("print.html")
            return self._json(404, {"error": "Not found."})

        def do_POST(self):
            path = urlparse(self.path).path
            if not self._same_origin():
                return self._json(403, {"error": "Cross-origin request refused."})
            if path == "/api/login":
                body = self._body()
                if body is None:
                    return self._json(400, {"error": "Invalid request."})
                code, payload, token = gate.login(body.get("password"), self._ip())
                return self._json(code, payload, {"Set-Cookie": gate.cookie(token)} if token else None)
            if not self._authorized():  # checked before anything that could reach Qloo or the LLM
                return self._deny(path)
            m = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]{6,20})/retry", path)
            if m:
                code, payload = hub.retry(m.group(1))
                return self._json(code, payload)
            m = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]{6,20})/suggestions(?:/(s[0-9]))?", path)
            if m and not m.group(2):
                code, payload = hub.suggest(m.group(1))
                return self._json(code, payload)
            if m:
                body = self._body()
                if body is None:
                    return self._json(400, {"error": "Invalid request."})
                code, payload = hub.decide(m.group(1), m.group(2), str(body.get("decision", "")))
                return self._json(code, payload)
            if path != "/api/sessions":
                return self._json(404, {"error": "Not found."})
            body = self._body()
            if body is None:
                return self._json(400, {"error": "Invalid request."})
            code, payload = hub.create(body, self._ip())
            self._json(code, payload)

    return Handler


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m motif.web")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--recorded", nargs="*", help="LOCAL DEVELOPMENT ONLY: replay stored live runs (refused on Render)")
    parser.add_argument("--data-dir")
    args = parser.parse_args(argv)
    if args.recorded is not None and os.environ.get("RENDER"):
        print("Refused: --recorded is for local development and tests; it never runs on Render.", flush=True)
        return 2
    root = data_root(args.data_dir)
    recorded = [Path(p) for p in args.recorded] if args.recorded else None
    hub = Hub(load_config(), root, recorded)
    gate = AccessGate.from_env(os.environ)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(hub, gate))
    mode = "RECORDED (local preview)" if recorded else ("LIVE" if hub.live_ready else "LIVE (Qloo not configured)")
    print(f"MOTIF web on http://{args.host}:{args.port} · {mode} · LLM {hub.describe()['llm']} "
          f"(budget guard {hub.guard['mode']}: {hub.guard['reason']}) · {gate.describe()}", flush=True)
    server.serve_forever()
    return 0

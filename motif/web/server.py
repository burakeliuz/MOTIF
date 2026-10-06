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

`--recorded` (local preview only) replays stored live runs and labels every
result RECORDED; it is off unless the flag is given.
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
from ..llm import write_prose, writer_from_env
from ..qloo import LiveQloo, RecordedQloo
from .present import candidate_view, result_view

STATIC = Path(__file__).resolve().parent / "static"
STEP_ORDER = [("resolve", "Find the brand in Qloo"), ("own", "Read the brand's own Qloo description"),
              ("brand", "Related brands"), ("movie", "Related films"), ("artist", "Related music artists"),
              ("engine", "Translate with MOTIF's rules"), ("brief", "Write the perfumer brief")]
CSP = ("default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
NAME_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,80}$")


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
        self.error: Optional[str] = None
        self.finished: Optional[float] = None


class Hub:
    def __init__(self, config: EngineConfig, root: Path, recorded: Optional[List[Path]] = None,
                 env: Optional[Dict[str, str]] = None):
        self.config = config
        self.env = os.environ if env is None else env  # LLM settings; tests pass their own mapping
        self.root = root
        self.recorded = recorded
        self.sessions: Dict[str, WebSession] = {}
        self.by_key: Dict[tuple, str] = {}
        self.lock = threading.Lock()
        self.ip_hits: Dict[str, deque] = defaultdict(deque)
        self.day_sessions: Dict[str, int] = defaultdict(int)
        self.day_qloo: Dict[str, int] = defaultdict(int)
        self.limits = {"per_ip_hour": _int_env("MOTIF_WEB_SESSIONS_PER_IP_HOUR", 8),
                       "per_day": _int_env("MOTIF_WEB_SESSIONS_PER_DAY", 120),
                       "qloo_per_day": _int_env("MOTIF_QLOO_MAX_CALLS_PER_DAY", 400)}
        self.live_ready = None
        if not recorded:
            env = live_environment(harness_environment(load_manifest()))
            ready = check_direct_readiness(env)
            self.live_ready = ready if ready.live_ready else None
            self.live_env = env

    # -- public API -----------------------------------------------------------------

    def describe(self) -> Dict[str, Any]:
        llm = writer_from_env(self.env)
        return {"mode": "recorded" if self.recorded else "live",
                "mode_label": ("Recorded preview · stored Qloo data" if self.recorded else "Live · Qloo API"),
                "live_available": bool(self.recorded or self.live_ready),
                "llm": "configured" if llm["writer"] else "template",
                "examples": ["MUJI", "Ralph Lauren"], "versions": self.config.versions}

    def create(self, body: Dict[str, Any], ip: str) -> (int, Dict[str, Any]):
        reference = str(body.get("reference", "")).strip()
        if not NAME_RE.match(reference):
            return 400, {"error": "Enter a brand name (1 to 80 characters)."}
        ref_type = body.get("type", "brand")
        if ref_type not in ("brand", "any"):
            return 400, {"error": "The MVP researches brands."}
        choose = body.get("choose") or None
        overrides = body.get("resolve_conflict") or {}
        if not isinstance(overrides, dict) or any(k not in AXES or not isinstance(v, str) for k, v in overrides.items()):
            return 400, {"error": "Invalid conflict answer."}
        parent = self.sessions.get(str(body.get("parent", ""))) if body.get("parent") else None
        key = ("recorded" if self.recorded else "live", reference.casefold(), ref_type, choose or "",
               json.dumps(overrides, sort_keys=True))
        today = iso(utc_now())[:10]
        with self.lock:
            existing = self.by_key.get(key)
            if existing and self.sessions[existing].status != "error" and time.time() - self.sessions[existing].created < 1800:
                return 200, {"id": existing, "reused": True}
            if not self.recorded and not self.live_ready:
                return 503, {"error": "Live Qloo access is not configured on this server.", "kind": "qloo_unavailable"}
            if parent is None:  # follow-ups are answers to a question, not new research
                hits = self.ip_hits[ip]
                while hits and time.time() - hits[0] > 3600:
                    hits.popleft()
                if len(hits) >= self.limits["per_ip_hour"]:
                    return 429, {"error": "Too many new searches from this connection; please try again in an hour.", "kind": "rate_limited"}
                if self.day_sessions[today] >= self.limits["per_day"]:
                    return 429, {"error": "Today's demo capacity is used up; please try again tomorrow.", "kind": "daily_cap"}
                if self.day_qloo[today] + self.config.params["budget"]["max_requests_per_session"] > self.limits["qloo_per_day"]:
                    return 429, {"error": "Today's Qloo request budget for this demo is used up.", "kind": "qloo_cap"}
                hits.append(time.time())
                self.day_sessions[today] += 1
            sid = secrets.token_urlsafe(9)
            session = WebSession(sid, key, {"reference": reference, "type": ref_type, "choose": choose, "overrides": overrides},
                                 "recorded" if self.recorded else "live", parent)
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
                               "choose": s.params["choose"], "overrides": s.params["overrides"]}
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
        if s.prose:
            out["brief"] = {"author": s.prose["author"], "text": s.prose["text"], "note": s.prose.get("note"),
                            "model": (s.prose.get("llm") or {}).get("model") if s.prose["author"] == "llm" else None}
        if s.access is not None and s.data_label == "recorded":
            out["recorded_from"] = sorted({d.name for d in getattr(s.access, "recording_dirs", [])})
        if o and o.get("result") is not None:
            fetched = sorted({e.get("fetched_at") for e in o["result"]["evidence"] if e.get("fetched_at")})
            out["fetched"] = [fetched[0], fetched[-1]] if fetched else None
        return out

    def brief(self, sid: str) -> Optional[Dict[str, Any]]:
        s = self.sessions.get(sid)
        return s.brief if s else None

    # -- research ---------------------------------------------------------------------

    def _access(self, session: WebSession):
        if session.parent is not None and session.parent.access is not None:
            return session.parent.access  # same cache and budget: answers never repeat requests
        return self._new_access(self.root / "web_sessions" / session.id)

    def _new_access(self, sdir: Path):
        budget = self.config.params["budget"]
        if self.recorded:
            return RecordedQloo(self.recorded, sdir, budget["max_requests_per_session"])
        transport = DirectTransport(self.live_ready.base_url, api_key=direct_api_key(self.live_env), timeout_s=30)
        return LiveQloo(transport, self.live_ready.base_url, sdir, budget["max_requests_per_session"],
                        budget["max_retries"], budget["retry_backoff_s"], 30)

    def _run(self, s: WebSession) -> None:
        today = iso(utc_now())[:10]
        try:
            access = self._access(s)
            s.access = access
            before = access.network_attempts
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
            controller = Controller(access, self.config, p["reference"], p["type"], p["choose"],
                                    overrides=p["overrides"])
            s.controller = controller
            outcome = controller.run()
            access.request = original
            s.phase = "engine"
            s.outcome = outcome
            with self.lock:
                self.day_qloo[today] += access.network_attempts - before
            if outcome.get("result") is not None and outcome["status"] == "completed":
                s.phase = "brief"
                llm = writer_from_env(self.env, ledger_path=self.root / "llm_calls.jsonl")
                name = (outcome.get("resolution") or {}).get("name") or p["reference"]
                s.prose = write_prose(name, outcome["result"], llm["writer"])
                session_meta = {"data_label": s.data_label, "resolution": outcome["resolution"]}
                s.brief = build_brief(session_meta, outcome["result"], s.prose)
            s.status = outcome["status"]
            s.phase = "done"
            self._persist(s)
        except Exception as exc:  # never leak internals; record the kind only
            s.status = "error"
            s.error = f"Something went wrong on the server ({type(exc).__name__}). No partial result is shown as complete."
            s.phase = "done"
        finally:
            s.finished = time.time()

    def _persist(self, s: WebSession) -> None:
        sdir = self.root / "web_sessions" / s.id
        sdir.mkdir(parents=True, exist_ok=True)
        meta = {"id": s.id, "created": iso(utc_now()), "params": s.params, "data_label": s.data_label,
                "status": s.status, "outcome": (s.outcome or {}).get("outcome"), "trace": (s.outcome or {}).get("trace"),
                "network_attempts": getattr(s.access, "network_attempts", None), "versions": self.config.versions,
                "prose": {k: v for k, v in (s.prose or {}).items() if k != "text"} or None}
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
                detail = ("written by " + (s.prose.get("llm") or {}).get("model", "LLM") + ", checked against the engine result"
                          if s.prose["author"] == "llm" else s.prose.get("note"))
            elif key == "brief" and s.phase == "brief" and not finished:
                status, detail = "running", None
            else:
                status, detail = ("not_run" if finished else "pending"), None
            steps.append({"key": key, "label": label, "status": status, "detail": detail})
        return steps

    @staticmethod
    def _stop_message(o: Dict[str, Any]) -> str:
        kind = o.get("outcome")
        return {"stopped_access_error": "Qloo refused the request (credential or permission). Nothing else was tried.",
                "stopped_budget": "This search reached its Qloo request budget.",
                "stopped_request_failed": "A Qloo request failed after bounded retries.",
                "not_found": "Qloo returned no entity for this name.",
                "invalid_choice": "That choice was not among Qloo's results.",
                "stopped_not_recorded": "This request is not in the stored recording (recorded mode sends nothing live)."
                }.get(kind, o.get("message") or "The research stopped.")


def make_handler(hub: Hub):
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

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/healthz":
                return self._json(200, {"ok": True})
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
            name = {"/": "index.html", "/app.css": "app.css", "/app.js": "app.js", "/favicon.svg": "favicon.svg"}.get(path)
            if not name:
                return self._json(404, {"error": "Not found."})
            data = (STATIC / name).read_bytes()
            ctype = {"html": "text/html; charset=utf-8", "css": "text/css; charset=utf-8",
                     "js": "text/javascript; charset=utf-8", "svg": "image/svg+xml"}[name.rsplit(".", 1)[1]]
            self._headers(200, ctype, len(data))
            self.wfile.write(data)

        def do_POST(self):
            if urlparse(self.path).path != "/api/sessions":
                return self._json(404, {"error": "Not found."})
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 4096:
                return self._json(400, {"error": "Invalid request."})
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return self._json(400, {"error": "Invalid JSON."})
            if not isinstance(body, dict):
                return self._json(400, {"error": "Invalid request."})
            code, payload = hub.create(body, self._ip())
            self._json(code, payload)

    return Handler


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m motif.web")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--recorded", nargs="*", help="LOCAL PREVIEW ONLY: replay stored live runs (labelled RECORDED)")
    parser.add_argument("--data-dir")
    args = parser.parse_args(argv)
    root = data_root(args.data_dir)
    recorded = [Path(p) for p in args.recorded] if args.recorded else None
    hub = Hub(load_config(), root, recorded)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(hub))
    mode = "RECORDED (local preview)" if recorded else ("LIVE" if hub.live_ready else "LIVE (Qloo not configured)")
    print(f"MOTIF web on http://{args.host}:{args.port} · {mode} · LLM {hub.describe()['llm']}", flush=True)
    server.serve_forever()
    return 0

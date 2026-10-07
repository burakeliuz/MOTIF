"""Web layer checks (SYNTHETIC Qloo bodies, no network; loopback HTTP only).

The hub is wired to the fake transport from motif_fakes, so these tests cover the
server's guards (dedupe, follow-up reuse, caps, validation, no key in responses)
and the view model, never Qloo or Anthropic.
"""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import (AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, entities_body, insights_body, ok,
                              search_body)
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import (AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, entities_body, insights_body, ok,
                             search_body)
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

from motif.qloo import LiveQloo
from motif.web.access import COOKIE, FAILS_GLOBAL, FAILS_PER_IP, SESSION_TTL_S, AccessGate
from motif.llm import BudgetExhausted, CallLedger
from motif.web.server import Hub, make_handler
from motif.web.usage import UsageError, UsageStore

SEED = "SYN-BRAND-1"
SECRET = "placeholder-TEST-ONLY-not-a-key-7f3c"
BRAND_TAGS = [(f"SYN-B{i}", f"SYN Brand {i}", [("Clean Lines", AESTHETIC), ("Muted", STYLE), ("Natural Materials", AESTHETIC)])
              for i in range(3)]


def routes(search=None):
    search = search or search_body([(SEED, "Synthbrand", "urn:entity:brand"), ("SYN-PLACE", "Synthbrand", "urn:entity:place")])
    bodies = {"search": search,
              "entity": entities_body(SEED, "Synthbrand", [("Unpretentious", TONE), ("Clean Lines", AESTHETIC), ("Natural Materials", AESTHETIC),
                                                           ("Dark Palette", AESTHETIC), ("Tactile Paper", AESTHETIC)]),
              "urn:entity:brand": insights_body(BRAND_TAGS),
              "urn:entity:movie": insights_body([("SYN-M1", "SYN Film", [("Muted", STYLE)])]),
              "urn:entity:artist": insights_body([])}

    def answer(argv):
        if argv[:2] == ["api", "search"]:
            return ok(bodies["search"])
        if argv[:2] == ["api", "entity"]:
            return ok(bodies["entity"])
        return ok(bodies[argv[argv.index("--type") + 1]])
    return answer


class FakeHub(Hub):
    """A live-mode hub whose Qloo access is the synthetic fake transport."""

    def __init__(self, root, env=None, search=None, limits=None):
        super().__init__(CONFIG, Path(root), recorded=[Path(root) / "unused"],
                         env=env if env is not None else {"MOTIF_LLM_PROVIDER": "off"})
        self.recorded = None
        self.live_ready = SimpleNamespace(base_url="https://example.invalid")
        self.transports = []
        self.search = search
        self.limits.update(limits or {})

    def _new_access(self, sdir):
        transport = FakeTransport(routes(self.search))
        self.transports.append(transport)
        return LiveQloo(transport, "https://example.invalid", sdir, 8, max_retries=2, backoff_s=[0, 0], sleep=lambda s: None)


def wait(hub, sid):
    for _ in range(400):
        v = hub.view(sid)
        if v["status"] != "running":
            return v
        time.sleep(0.01)
    raise AssertionError("session did not finish")


def settle(hub):
    for sid in list(hub.sessions):
        wait(hub, sid)


def calls(hub):
    return sum(len(t.calls) for t in hub.transports)


class HubFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.hubs = []
        self.addCleanup(lambda: [settle(h) for h in self.hubs])

    def make(self, **kw):
        hub = FakeHub(self.tmp.name, **kw)
        self.hubs.append(hub)
        return hub

    def test_full_flow_gives_a_labelled_result_and_never_draws_unknown_axes(self):
        hub = self.make()
        code, r = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
        self.assertEqual(code, 202)
        v = wait(hub, r["id"])
        self.assertEqual(v["status"], "completed")
        self.assertEqual(v["data_label"], "live")
        self.assertEqual([s["key"] for s in v["steps"]], ["resolve", "own", "brand", "movie", "engine", "brief"])
        self.assertTrue(all(s["status"] in ("done", "skipped") for s in v["steps"]))
        self.assertEqual(v["result"]["engine"], "continuous")
        opened = [dim["name"] for dim in v["result"]["dimensions"] if dim["state"] != "resolved"]
        for dim in v["result"]["dimensions"]:
            if dim["state"] != "resolved":
                self.assertNotIn("word", dim)  # nothing for the UI to place on the scale
        summary = v["result"]["open_summary"]
        self.assertEqual(summary["dims"] if summary else [], opened)  # every open dimension, told once
        self.assertEqual(v["brief"]["author"], "template")
        self.assertIn(v["result"]["architecture"]["status"], ("proposed", "open"))
        self.assertNotEqual(v["result"]["outcome_text"], v["result"]["outcome"])  # every outcome has plain-language copy
        for m in v["result"]["motifs"]:
            for e in m["evidence"]:
                self.assertEqual(e["provenance"], "qloo_observation")
                self.assertTrue(e["json_pointer"].startswith("/"))

    def test_identical_requests_reuse_the_session_and_send_nothing_new(self):
        hub = self.make()
        _, first = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
        wait(hub, first["id"])
        before = calls(hub)
        code, again = hub.create({"reference": "  synthbrand "}, "10.0.0.1")
        self.assertEqual((code, again), (200, {"id": first["id"], "reused": True}))
        self.assertEqual(calls(hub), before)

    def test_a_choice_reuses_the_parent_access_so_the_search_is_not_repeated(self):
        twins = search_body([(SEED, "Synthbrand", "urn:entity:brand"), ("SYN-BRAND-2", "Synthbrand", "urn:entity:brand"),
                             ("SYN-PLACE", "Synthbrand", "urn:entity:place")])
        hub = self.make(search=twins, limits={"per_ip_hour": 1})
        _, asked = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
        q = wait(hub, asked["id"])
        self.assertEqual(q["status"], "needs_choice")
        options = {o["qloo_id"]: o for o in q["question"]["options"]}
        self.assertTrue(options[SEED]["selectable"])
        self.assertFalse(options.get("SYN-PLACE", {"selectable": False})["selectable"])
        # the follow-up is an answer, not a new search: it is not rate limited and reuses the parent's access
        code, chosen = hub.create({"reference": "Synthbrand", "choose": SEED, "parent": asked["id"]}, "10.0.0.1")
        self.assertEqual(code, 202)
        v = wait(hub, chosen["id"])
        self.assertEqual(v["status"], "completed")
        self.assertEqual(len(hub.transports), 1)
        searches = [c for c in hub.transports[0].calls if c[:2] == ["api", "search"]]
        self.assertEqual(len(searches), 1)
        self.assertEqual(v["steps"][0]["detail"], "reused from this session")
        self.assertEqual(v["choose"], SEED)

    def test_caps_and_input_validation(self):
        hub = self.make(limits={"per_ip_hour": 1})
        self.assertEqual(hub.create({"reference": ""}, "10.0.0.1")[0], 400)
        self.assertEqual(hub.create({"reference": "x" * 81}, "10.0.0.1")[0], 400)
        self.assertEqual(hub.create({"reference": "Synthbrand", "type": "movie"}, "10.0.0.1")[0], 400)
        self.assertEqual(hub.create({"reference": "Synthbrand", "resolve_conflict": {"not_an_axis": "x"}}, "10.0.0.1")[0], 400)
        self.assertEqual(hub.create({"reference": "Synthbrand"}, "10.0.0.1")[0], 202)
        code, body = hub.create({"reference": "Otherbrand"}, "10.0.0.1")
        self.assertEqual((code, body["kind"]), (429, "rate_limited"))
        self.assertEqual(hub.create({"reference": "Otherbrand"}, "10.0.0.2")[0], 202)
        daily = self.make(limits={"qloo_per_day": 3})
        self.assertEqual(daily.create({"reference": "Synthbrand"}, "10.0.0.3")[1]["kind"], "qloo_cap")

    def test_without_live_access_the_server_says_so_and_runs_nothing(self):
        hub = self.make()
        hub.live_ready = None
        code, body = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
        self.assertEqual((code, body["kind"]), (503, "qloo_unavailable"))
        self.assertEqual(hub.transports, [])

    def test_llm_failure_shows_labelled_template_and_the_key_never_reaches_a_response(self):
        env = {"MOTIF_ANTHROPIC_API_KEY": SECRET, "MOTIF_LLM_MAX_CALLS": "0"}
        hub = self.make(env=env)
        _, r = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
        v = wait(hub, r["id"])
        self.assertEqual(v["brief"]["author"], "template")
        self.assertIsNone(v["brief"]["model"])
        text = json.dumps([hub.describe(), v, hub.brief(r["id"])])
        self.assertNotIn(SECRET, text)
        self.assertNotIn("TEST-ONLY", text)
        stored = "".join(p.read_text(encoding="utf-8") for p in Path(self.tmp.name).rglob("*") if p.is_file())
        self.assertNotIn(SECRET, stored)


class HttpLayer(unittest.TestCase):
    """Loopback only: static files, security headers, JSON errors."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.hub = FakeHub(cls.tmp.name)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.hub, AccessGate(False, None)))
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        settle(cls.hub)
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def get(self, path):
        try:
            with self.opener.open(self.base + path, timeout=5) as res:
                return res.status, dict(res.headers), res.read()
        except urllib.error.HTTPError as err:
            return err.code, dict(err.headers), err.read()

    def post(self, body):
        req = urllib.request.Request(self.base + "/api/sessions", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(req, timeout=5) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_static_pages_carry_security_headers(self):
        for path in ("/", "/app.js", "/app.css", "/favicon.svg"):
            code, headers, _ = self.get(path)
            self.assertEqual(code, 200, path)
            self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.get("/../motif/llm.py")[0], 404)
        self.assertEqual(self.get("/healthz")[0], 200)

    def test_the_client_never_builds_html_from_data(self):
        js = self.get("/app.js")[2].decode("utf-8")
        code = "\n".join(line for line in js.splitlines() if not line.lstrip().startswith(("*", "/*", "//")))
        for sink in (".innerHTML", ".outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            self.assertNotIn(sink, code)

    def test_bad_requests_get_json_errors(self):
        self.assertEqual(self.post(b"not json")[0], 400)
        self.assertEqual(self.post(b"[]")[0], 400)
        self.assertEqual(self.post(b"x" * 5000)[0], 400)
        self.assertEqual(self.get("/api/sessions/unknown-id-123")[0], 404)
        code, body = self.post(json.dumps({"reference": "Synthbrand"}).encode())
        self.assertIn(code, (200, 202))
        status, _, raw = self.get("/api/sessions/" + body["id"])
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()


PASSWORD = "review-only-test-password-91"  # test value, not a real credential


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GatedServer:
    """A loopback server with the access gate on; its hub uses the synthetic fake transport."""

    def __init__(self, password):
        self.tmp = tempfile.TemporaryDirectory()
        env = {"MOTIF_ANTHROPIC_API_KEY": "placeholder-TEST-ONLY-not-a-key", "MOTIF_LLM_MAX_CALLS": "5"}
        self.hub = FakeHub(self.tmp.name, env=env)
        self.created = []
        original = self.hub.create
        self.hub.create = lambda body, ip: (self.created.append(body), original(body, ip))[1]
        self.gate = AccessGate(True, password)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.hub, self.gate))
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
        self.seen = []

    def close(self):
        settle(self.hub)
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def call(self, method, path, body=None, cookie=None, headers=None):
        h = dict(headers or {})
        if cookie:
            h["Cookie"] = cookie
        if body is not None:
            h["Content-Type"] = "application/json"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with self.opener.open(req, timeout=5) as res:
                out = res.status, dict(res.headers), res.read()
        except urllib.error.HTTPError as err:
            out = err.code, dict(err.headers), err.read()
        self.seen.append(json.dumps(out[1]) + out[2].decode("utf-8", "replace"))
        return out

    def login(self, password, ip="10.9.9.9"):
        return self.call("POST", "/api/login", {"password": password}, headers={"X-Forwarded-For": ip})


class AccessGateHttp(unittest.TestCase):
    """The review gate: nothing behind it, and nothing that reaches Qloo or the LLM, works without sign-in."""

    def setUp(self):
        self.srv = GatedServer(PASSWORD)
        self.addCleanup(self.srv.close)

    def assert_nothing_started(self):
        self.assertEqual(self.srv.created, [])           # the hub was never asked to research
        self.assertEqual(self.srv.hub.sessions, {})
        self.assertEqual(self.srv.hub.transports, [])     # so no Qloo transport was ever built
        self.assertFalse((Path(self.srv.tmp.name) / "llm_calls.jsonl").exists())  # and no LLM call was logged

    def test_unauthorized_requests_reach_no_api_and_start_nothing(self):
        for cookie in (None, f"{COOKIE}=forged-token", "other=1"):
            code, _, body = self.srv.call("POST", "/api/sessions", {"reference": "Synthbrand"}, cookie=cookie)
            self.assertEqual((code, json.loads(body)["kind"]), (401, "auth_required"))
            for path in ("/api/config", "/api/sessions/abcdefgh", "/api/sessions/abcdefgh/brief.json", "/app.js"):
                self.assertEqual(self.srv.call("GET", path, cookie=cookie)[0], 401, path)
            code, headers, _ = self.srv.call("GET", "/", cookie=cookie)
            self.assertEqual((code, headers["Location"]), (303, "/login"))
        self.assert_nothing_started()

    def test_health_check_and_sign_in_page_stay_public_without_data(self):
        code, headers, body = self.srv.call("GET", "/healthz")
        self.assertEqual((code, json.loads(body)), (200, {"ok": True}))
        self.assertNotIn("Set-Cookie", headers)
        for path in ("/login", "/login.js", "/app.css", "/favicon.svg"):
            self.assertEqual(self.srv.call("GET", path)[0], 200, path)
        self.assert_nothing_started()

    def test_correct_password_sets_a_strict_cookie_that_opens_the_api(self):
        self.assertEqual(self.srv.login("wrong")[0], 401)
        code, headers, _ = self.srv.login(PASSWORD)
        self.assertEqual(code, 200)
        cookie = headers["Set-Cookie"]
        for flag in ("HttpOnly", "Secure", "SameSite=Strict", "Path=/", f"Max-Age={SESSION_TTL_S}"):
            self.assertIn(flag, cookie)
        pair = cookie.split(";")[0]
        self.assertEqual(self.srv.call("GET", "/api/config", cookie=pair)[0], 200)
        self.assertEqual(self.srv.call("GET", "/", cookie=pair)[0], 200)
        self.assertEqual(self.srv.call("GET", "/login", cookie=pair)[0], 303)
        code, _, body = self.srv.call("POST", "/api/sessions", {"reference": "Synthbrand"}, cookie=pair)
        self.assertEqual(code, 202)
        self.assertEqual(len(self.srv.hub.transports), 1)
        # the password never comes back in any header or body
        self.assertFalse(any(PASSWORD in seen for seen in self.srv.seen))

    def test_cross_origin_posts_are_refused(self):
        code, _, _ = self.srv.call("POST", "/api/login", {"password": PASSWORD}, headers={"Origin": "https://evil.example"})
        self.assertEqual(code, 403)
        self.assertEqual(self.srv.gate.tokens, {})

    def test_wrong_attempts_are_limited_per_client_and_globally(self):
        for _ in range(FAILS_PER_IP):
            self.assertEqual(self.srv.login("nope", ip="10.1.1.1")[0], 401)
        self.assertEqual(self.srv.login(PASSWORD, ip="10.1.1.1")[0], 429)  # locked even with the right password
        self.assertEqual(self.srv.login(PASSWORD, ip="10.1.1.2")[0], 200)  # another client is unaffected
        # spoofing a new address per attempt still hits the global limit
        for i in range(FAILS_GLOBAL):
            self.srv.login("nope", ip=f"10.2.0.{i}")
        self.assertEqual(self.srv.login(PASSWORD, ip="10.3.3.3")[0], 429)


class AccessGateClosed(unittest.TestCase):
    def test_protection_on_without_a_password_keeps_everything_closed(self):
        srv = GatedServer(None)
        self.addCleanup(srv.close)
        code, _, body = srv.login("")
        self.assertEqual((code, json.loads(body)["kind"]), (503, "access_closed"))
        self.assertEqual(srv.login("anything")[0], 503)
        self.assertEqual(srv.call("POST", "/api/sessions", {"reference": "Synthbrand"})[0], 401)
        self.assertEqual(srv.call("GET", "/api/config")[0], 401)
        self.assertEqual(srv.call("GET", "/healthz")[0], 200)
        self.assertEqual(srv.created, [])
        self.assertEqual(srv.hub.transports, [])


class AccessGateUnit(unittest.TestCase):
    def test_environment_defaults_are_fail_closed(self):
        self.assertTrue(AccessGate.from_env({}).enabled)
        self.assertFalse(AccessGate.from_env({}).configured)
        self.assertFalse(AccessGate.from_env({}).allowed(None))
        self.assertTrue(AccessGate.from_env({"MOTIF_ACCESS_PASSWORD": PASSWORD}).configured)
        self.assertFalse(AccessGate.from_env({"MOTIF_ACCESS_PROTECTION": "off"}).enabled)
        self.assertTrue(AccessGate.from_env({"MOTIF_ACCESS_PROTECTION": "off"}).allowed(None))

    def test_tokens_expire(self):
        now = [1000.0]
        gate = AccessGate(True, PASSWORD, clock=lambda: now[0])
        _, _, token = gate.login(PASSWORD, "10.0.0.1")
        self.assertTrue(gate.allowed(f"{COOKIE}={token}"))
        now[0] += SESSION_TTL_S + 1
        self.assertFalse(gate.allowed(f"{COOKIE}={token}"))
        self.assertEqual(gate.login(123, "10.0.0.1")[0], 401)  # non-string passwords are wrong, not errors

    def test_the_password_is_not_kept_in_plain_text(self):
        gate = AccessGate(True, PASSWORD)
        self.assertNotIn(PASSWORD, repr(vars(gate)))
        self.assertNotIn(PASSWORD, gate.describe())


class FakeWriter:
    """Stands in for the LLM; counts calls; never touches the network."""

    model = "fake-model"

    def __init__(self, suggestions=None, fail=False):
        self.calls = 0
        self.suggestions = suggestions
        self.fail = fail

    def describe(self):
        return {"provider": "fake", "model": self.model}

    def write(self, payload, feedback=None):
        raise RuntimeError("prose not exercised here")

    def suggest(self, payload):
        self.calls += 1
        if self.fail:
            raise RuntimeError("api error")
        return self.suggestions


class BudgetCounters(unittest.TestCase):
    def test_concurrent_reservations_never_pass_the_cap_and_survive_a_new_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            stores = [UsageStore(path) for _ in range(4)]  # separate objects, as after a restart or in two processes
            granted = []
            threads = [threading.Thread(target=lambda st=st: granted.append(st.reserve("qloo", 8, 40))) for st in stores * 5]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertEqual(granted.count(True), 5)
            self.assertEqual(UsageStore(path).today()["qloo"], 40)
            UsageStore(path).release("qloo", 6)
            self.assertEqual(UsageStore(path).today()["qloo"], 34)

    def test_unverifiable_budget_starts_no_research(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = FakeHub(tmp)
            (Path(tmp) / "web_usage.json").write_text("not json", encoding="utf-8")
            code, body = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
            self.assertEqual((code, body["kind"]), (503, "budget_unverified"))
            self.assertEqual((hub.sessions, hub.transports), ({}, []))

    def test_llm_ledger_reserves_before_the_call_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "llm_calls.jsonl"
            a, b = CallLedger(path, 2), CallLedger(path, 2)
            a.reserve("messages.create", "m")
            b.reserve("interpret", "m")
            a.record({"kind": "messages.create", "status": "ok"})  # results are not counted twice
            with self.assertRaises(BudgetExhausted):
                b.reserve("interpret", "m")
            blocked = CallLedger(Path(tmp) / "missing-dir" / "x" / "ledger.jsonl", 5)
            (Path(tmp) / "missing-dir").write_text("a file where a directory should be", encoding="utf-8")
            with self.assertRaises(BudgetExhausted):
                blocked.reserve("interpret", "m")


class IntentAndReadings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def hub(self, writer=None):
        hub = FakeHub(self.tmp.name)
        hub._writer = lambda: writer
        self.addCleanup(lambda: settle(hub))
        return hub

    def test_intent_is_recorded_apart_and_changes_neither_result_nor_requests(self):
        hub = self.hub()
        _, plain = hub.create({"reference": "Synthbrand", "choose": SEED}, "10.0.0.1")
        a = wait(hub, plain["id"])
        before = calls(hub)
        _, with_intent = hub.create({"reference": "Synthbrand", "choose": SEED, "intent": "a home scent for the store"}, "10.0.0.1")
        b = wait(hub, with_intent["id"])
        self.assertNotEqual(plain["id"], with_intent["id"])
        self.assertEqual(calls(hub), before)  # same reference: the Qloo cache is reused
        self.assertEqual(a["result"]["dimensions"], b["result"]["dimensions"])
        self.assertEqual(a["result"]["architecture"], b["result"]["architecture"])
        brief = hub.brief(with_intent["id"])
        self.assertEqual(brief["user_intent"]["provenance"], "user_intent")
        self.assertNotIn("a home scent", json.dumps(brief["evidence"]))
        self.assertIn("scent direction remain unchanged", b["intent_effect"])
        self.assertEqual(hub.create({"reference": "Synthbrand", "intent": "x" * 141}, "10.0.0.1")[0], 400)

    def test_suggestions_are_checked_cached_and_kept_out_of_the_evidence(self):
        raw = {"suggestions": [
            {"descriptor": "Dark Palette", "reading": "A taste for shadowed, low-key surfaces.", "design_question": "Keep the scent dim and quiet?"},
            {"descriptor": "Made Up", "reading": "Not offered.", "design_question": "?"},
            {"descriptor": "Tactile Paper", "reading": "Use 30% more vetiver.", "design_question": "?"},
            {"descriptor": "Tactile Paper", "reading": "Paper-like tactility.", "design_question": "Dry or soft?", "extra": 1},
        ]}
        writer = FakeWriter(raw)
        hub = self.hub(writer)
        _, r = hub.create({"reference": "Synthbrand", "choose": SEED}, "10.0.0.1")
        view = wait(hub, r["id"])
        self.assertEqual(view["suggestions"]["status"], "not_requested")  # nothing is called before the user asks
        self.assertEqual(writer.calls, 0)
        code, sg = hub.suggest(r["id"])
        self.assertEqual(code, 200)
        self.assertEqual([x["descriptor"] for x in sg["suggestions"]], ["Dark Palette"])
        self.assertEqual(sg["rejected"], 3)
        self.assertTrue(sg["suggestions"][0]["from_brand_itself"])
        self.assertEqual(sg["suggestions"][0]["label"], "Suggested interpretation — not applied")
        hub.suggest(r["id"])
        self.assertEqual(writer.calls, 1)  # reused within the session
        result_before = json.dumps(hub.view(r["id"])["result"], sort_keys=True)
        hub.decide(r["id"], "s1", "accept")
        brief = hub.brief(r["id"])
        self.assertEqual(brief["accepted_readings"][0]["provenance"], "user_preference")
        self.assertNotIn("shadowed", json.dumps(brief["evidence"]) + json.dumps(brief["motif_scores"]) + json.dumps(brief["axes"])
                         + json.dumps(brief["architecture"]))
        self.assertEqual(json.dumps(hub.view(r["id"])["result"], sort_keys=True), result_before)
        hub.decide(r["id"], "s1", "reject")
        self.assertEqual(hub.brief(r["id"])["accepted_readings"], [])
        self.assertEqual(hub.decide(r["id"], "s1", "maybe")[0], 400)

    def test_suggestions_degrade_without_a_key_or_on_api_errors(self):
        hub = self.hub(None)
        _, r = hub.create({"reference": "Synthbrand", "choose": SEED}, "10.0.0.1")
        wait(hub, r["id"])
        self.assertEqual(hub.suggest(r["id"])[1]["status"], "unavailable")
        failing = self.hub(FakeWriter(fail=True))
        _, r2 = failing.create({"reference": "Synthbrand", "choose": SEED}, "10.0.0.2")
        v = wait(failing, r2["id"])
        self.assertEqual(v["status"], "completed")
        self.assertEqual(failing.suggest(r2["id"])[1]["status"], "failed")


class GatedNewRoutes(unittest.TestCase):
    def test_suggestions_decisions_and_print_page_need_sign_in(self):
        srv = GatedServer(PASSWORD)
        self.addCleanup(srv.close)
        for path in ("/api/sessions/abcdefgh/suggestions", "/api/sessions/abcdefgh/suggestions/s1"):
            self.assertEqual(srv.call("POST", path, {"decision": "accept"})[0], 401, path)
        code, headers, _ = srv.call("GET", "/brief/abcdefgh")
        self.assertEqual((code, headers["Location"]), (303, "/login"))
        self.assertEqual(srv.call("GET", "/strips.js")[0], 401)
        self.assertEqual(srv.created, [])


class ProseWording(unittest.TestCase):
    def test_audience_claims_are_rejected(self):
        from motif.brief import validate_prose
        result = {"materials": {"selected": []}, "axes": {a: {"state": "unknown"} for a in
                  ("warm_cool", "light_dense", "raw_polished", "natural_synthetic", "intimate_projecting", "sweet_dry")}}
        text = "Temperature, weight, texture, natural/synthetic, projection and sweetness stay open. Its audience loves calm."
        self.assertTrue(any("claim" in p for p in validate_prose(text, result)))

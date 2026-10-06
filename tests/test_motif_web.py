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
from motif.web.server import Hub, make_handler

SEED = "SYN-BRAND-1"
SECRET = "placeholder-TEST-ONLY-not-a-key-7f3c"
BRAND_TAGS = [(f"SYN-B{i}", f"SYN Brand {i}", [("Clean Lines", AESTHETIC), ("Muted", STYLE), ("Natural Materials", AESTHETIC)])
              for i in range(3)]


def routes(search=None):
    search = search or search_body([(SEED, "Synthbrand", "urn:entity:brand"), ("SYN-PLACE", "Synthbrand", "urn:entity:place")])
    bodies = {"search": search,
              "entity": entities_body(SEED, "Synthbrand", [("Unpretentious", TONE), ("Clean Lines", AESTHETIC), ("Natural Materials", AESTHETIC)]),
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
        for axis in v["result"]["axes"]:
            if axis["state"] != "target":
                self.assertIsNone(axis["value"])  # nothing for the UI to place on the scale
        self.assertEqual(v["brief"]["author"], "template")
        mats = v["result"]["materials"]
        self.assertNotEqual(mats["status_text"], mats["status"])  # every material status has plain-language copy
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
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.hub))
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

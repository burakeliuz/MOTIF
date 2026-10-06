"""Direct HTTPS transport: request mapping, key handling, errors, end to end."""

import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

from motif_spike import adapter, cli
from motif_spike.adapter import classify, http_request, locate_items
from motif_spike.manifest import load_manifest
from motif_spike.transport import DirectTransport, direct_api_key, validate_base_url
from motif_spike.util import RunPaths, read_json, read_jsonl, resolve_pointer

SECRET = "hack_test-SHOULD-NOT-APPEAR"

ENTITY = {"entity_id": "LOCAL-ENT-1", "name": "A24", "types": ["urn:entity:brand"], "tags": []}
RESPONSES = {
    "/search": {"success": True, "results": [ENTITY, {"entity_id": "LOCAL-ENT-2", "name": "A24 Cafe", "types": ["urn:entity:place"]}]},
    "/entities": {"success": True, "results": [dict(ENTITY, properties={"description": "local test entity"})]},
    "/v2/insights:urn:entity:movie": {"success": True, "results": {"entities": [
        {"entity_id": "LOCAL-MOV-1", "name": "Local Film", "subtype": "urn:entity:movie", "popularity": 0.5,
         "query": {"affinity": 0.9}, "tags": [{"id": "local:tag:k1", "name": "K1", "type": "urn:tag:keyword:media"}]}]}},
    "/v2/insights:urn:tag": {"success": True, "results": {"tags": [
        {"tag_id": "local:tag:k1", "name": "K1", "subtype": "urn:tag:keyword:media", "types": ["urn:entity:movie"],
         "query": {"affinity": 0.7}}]}},
}


class FakeQloo(BaseHTTPRequestHandler):
    seen = []
    status = 200

    def do_GET(self):
        url = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        FakeQloo.seen.append({"path": url.path, "params": params, "api_key": self.headers.get("X-Api-Key")})
        if FakeQloo.status != 200:
            self.send_response(FakeQloo.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": "denied"}).encode())
            return
        key = url.path + (":" + params["filter.type"] if url.path == "/v2/insights" else "")
        body = RESPONSES.get(key, {"success": True, "results": {"entities": []}})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):
        pass


class LocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeQloo)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeQloo.seen = []
        FakeQloo.status = 200


class RequestMapping(unittest.TestCase):
    def test_commands_map_to_the_same_requests_the_harness_sends(self):
        self.assertEqual(http_request(adapter.search_argv("A24", 10)), ("/search", {"query": "A24", "take": "10"}))
        self.assertEqual(http_request(adapter.seed_detail_argv("ID")), ("/entities", {"entity_ids": "ID"}))
        self.assertEqual(http_request(adapter.related_argv("ID", "urn:entity:movie", 10, True)), ("/v2/insights", {
            "filter.type": "urn:entity:movie", "signal.interests.entities": "ID", "take": "10", "feature.explainability": "true"}))
        self.assertEqual(http_request(adapter.seed_tags_argv("ID", 20)), ("/v2/insights", {
            "filter.type": "urn:tag", "signal.interests.entities": "ID", "take": "20"}))

    def test_placeholder_key_is_never_sent(self):
        self.assertIsNone(direct_api_key({"QLOO_API_KEY": "proxy-injected"}))
        self.assertIsNone(direct_api_key({}))
        self.assertEqual(direct_api_key({"QLOO_API_KEY": SECRET}), SECRET)

    def test_base_url_must_be_https_except_loopback(self):
        with self.assertRaises(ValueError):
            validate_base_url("http://hackathon.api.qloo.com")
        with self.assertRaises(ValueError):
            validate_base_url("https://user:pw@hackathon.api.qloo.com")
        self.assertEqual(validate_base_url("https://hackathon.api.qloo.com/"), "https://hackathon.api.qloo.com")

    def test_direct_tag_body_is_recognized(self):
        items, shape = locate_items(adapter.OP_SEED_TAGS, RESPONSES["/v2/insights:urn:tag"])
        self.assertEqual((len(items), shape, items[0][0]), (1, "results.tags", "/results/tags/0"))

    def test_tests_cannot_reach_the_network(self):
        result = DirectTransport("https://hackathon.api.qloo.com").execute(adapter.search_argv("A24", 1), 5)
        self.assertEqual(classify(adapter.OP_SEARCH, result).status, "network_error")


class DirectTransportBehaviour(LocalServer):
    def test_no_key_header_without_a_real_key(self):
        result = DirectTransport(self.base).execute(adapter.search_argv("A24", 2))
        self.assertEqual(classify(adapter.OP_SEARCH, result).status, "ok")
        self.assertIsNone(FakeQloo.seen[0]["api_key"])

    def test_real_key_is_sent_only_as_header(self):
        DirectTransport(self.base, api_key=SECRET).execute(adapter.search_argv("A24", 2))
        self.assertEqual(FakeQloo.seen[0]["api_key"], SECRET)
        self.assertNotIn(SECRET, json.dumps(FakeQloo.seen[0]["params"]))

    def test_dry_run_sends_nothing_and_shows_the_exact_request(self):
        result = DirectTransport(self.base).execute(adapter.search_argv("A24", 2) + ["--dry-run"])
        self.assertEqual(FakeQloo.seen, [])
        self.assertEqual(json.loads(result.stdout)["url"], self.base + "/search")

    def test_http_errors_keep_their_meaning(self):
        for status, expected in ((401, "auth_error"), (403, "forbidden"), (429, "rate_limited"), (503, "server_error"), (400, "rejected_request")):
            FakeQloo.status = status
            result = DirectTransport(self.base).execute(adapter.search_argv("A24", 2))
            self.assertEqual(classify(adapter.OP_SEARCH, result).status, expected, status)


class DirectEndToEnd(LocalServer):
    def test_live_run_over_direct_transport(self):
        manifest = load_manifest()
        manifest["harness_environment"] = {"QLOO_BASE_URL": self.base, "QLOO_TRUSTED_BASE_URL": self.base}
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"QLOO_API_KEY": "proxy-injected"}), \
                mock.patch.object(cli, "load_manifest", lambda: manifest):
            with contextlib.redirect_stdout(io.StringIO()):
                code = cli.main(["run", "--mode", "live", "--plan", "pilot", "--seeds", "a24", "--domains", "movie", "--data-dir", tmp])
            root = Path(tmp)
            paths = RunPaths(root, next((root / "raw").iterdir()).name)
            requests = read_jsonl(paths.requests_log)
            observations = read_jsonl(paths.normalized_dir / "observations.jsonl")
            run = read_json(paths.run_record)
            facts = (paths.normalized_dir / "facts.md").read_text(encoding="utf-8")
            for obs in observations:
                raw = json.loads((root / obs["raw_ref"]["file"]).read_text(encoding="utf-8"))
                self.assertEqual(resolve_pointer(raw, obs["raw_ref"]["pointer"]).get(obs["qloo_id_field"]), obs["qloo_id"])
        self.assertEqual(code, 0)
        self.assertEqual(run["versions"]["transport"], "direct")
        self.assertEqual([r["status"] for r in requests], ["ok", "ok", "ok", "ok"])
        self.assertTrue(all(r["preview_source"].startswith("direct client") for r in requests))
        self.assertTrue(all(s["api_key"] is None for s in FakeQloo.seen))
        kinds = {o["kind"] for o in observations}
        self.assertEqual(kinds, {"search_candidate", "seed_entity", "related_entity", "tag_insight"})
        movie = next(o for o in observations if o["kind"] == "related_entity")
        self.assertEqual(movie["tags"][0]["id"], "local:tag:k1")
        self.assertIn("Transport | direct", facts)


if __name__ == "__main__":
    unittest.main()

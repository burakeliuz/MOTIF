"""End-to-end checks: synthetic isolation, provenance, error states, live guards."""

try:
    from . import _netguard  # noqa: F401
except ImportError:  # started as a top-level module (discover -s tests)
    import _netguard  # noqa: F401
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from motif_spike import cli, readiness
from motif_spike.manifest import build_plan, harness_environment, live_environment, load_manifest
from motif_spike.normalize import normalize_run
from motif_spike.readiness import check_readiness
from motif_spike.runner import Runner, build_reuse_index
from motif_spike.transport import HarnessTransport
from motif_spike.util import RunPaths, read_json, read_jsonl, resolve_pointer

FAKE_QLOO = [sys.executable, str(Path(__file__).with_name("fake_qloo.py"))]
SECRET = "sk-test-SHOULD-NOT-APPEAR-123"


def _forbidden(*args, **kwargs):
    raise AssertionError("synthetic mode attempted a process or network call")


def run_cli(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(argv)
    return code, out.getvalue()


def only_run(root: Path, prefix: str) -> RunPaths:
    runs = [p.name for p in (root / "raw").iterdir() if p.name.startswith(prefix)]
    assert len(runs) == 1, runs
    return RunPaths(root, runs[0])


class SyntheticRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        with mock.patch.object(subprocess, "run", _forbidden), mock.patch.object(subprocess, "Popen", _forbidden), \
                mock.patch.object(socket.socket, "connect", _forbidden):
            cls.code, cls.output = run_cli(["run", "--mode", "synthetic", "--data-dir", cls.tmp.name])
        cls.paths = only_run(cls.root, "synthetic-")
        cls.requests = read_jsonl(cls.paths.requests_log)
        cls.observations = read_jsonl(cls.paths.normalized_dir / "observations.jsonl")
        cls.resolutions = {r["seed_key"]: r for r in read_json(cls.paths.normalized_dir / "seed_resolutions.json")}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def request(self, operation, seed, domain=None):
        return next(r for r in self.requests if (r["operation"], r["seed_key"], r["domain_key"]) == (operation, seed, domain))

    def test_completes_without_process_or_network(self):
        self.assertEqual(self.code, 0)
        self.assertIn("SYNTHETIC run", self.output)

    def test_every_record_is_marked_synthetic(self):
        run = read_json(self.paths.run_record)
        self.assertTrue(run["synthetic"])
        self.assertEqual(run["live_execution_status"], "not_live")
        self.assertTrue(all(r["synthetic"] for r in self.requests))
        self.assertTrue(self.observations)
        for obs in self.observations:
            self.assertTrue(obs["synthetic"])
            self.assertEqual(obs["provenance_category"], "synthetic_fixture")
        facts = (self.paths.normalized_dir / "facts.md").read_text(encoding="utf-8")
        self.assertIn("NOT QLOO DATA", facts)
        self.assertIn("not_evaluated", facts)

    def test_every_observation_points_back_to_its_literal_raw_values(self):
        for obs in self.observations:
            raw = json.loads((self.root / obs["raw_ref"]["file"]).read_text(encoding="utf-8"))
            item = resolve_pointer(raw, obs["raw_ref"]["pointer"])
            self.assertEqual(item.get(obs["qloo_id_field"]), obs["qloo_id"])
            self.assertEqual(item.get("name"), obs["name"])
            for score in obs["scores"]:
                self.assertEqual(resolve_pointer(raw, score["pointer"]), score["value"])
            for tag in obs.get("tags") or []:
                self.assertEqual(resolve_pointer(raw, tag["pointer"]).get("id"), tag["id"])
            self.assertTrue(obs["evidence_id"].startswith("local:obs:"))

    def test_missing_fields_stay_missing(self):
        bare = next(o for o in self.observations if o["qloo_id"] == "SYNTHETIC-ENT-M105")
        self.assertEqual(bare["tags"], [])
        self.assertIsNone(bare["attributes"])
        self.assertEqual([s["field"] for s in bare["scores"]], ["query.affinity"])
        self.assertTrue({"tags", "properties", "popularity"} <= set(bare["missing_fields"]))
        unscored_tag = next(o for o in self.observations if o["qloo_id"] == "synthetic:tag:keyword:brand:fx_b1" and o["kind"] == "tag_insight")
        self.assertEqual(unscored_tag["scores"], [])
        coverage = read_json(self.paths.normalized_dir / "coverage.json")
        absent = {r["request_id"]: r["requested_but_absent"] for r in coverage["requests"]}
        self.assertEqual(absent[self.request("related_entities", "alpha", "artist")["request_id"]], ["explainability"])

    def test_duplicates_are_linked_and_counted_once(self):
        alpha_movie = self.request("related_entities", "alpha", "movie")["request_id"]
        m102 = [o for o in self.observations if o["request_id"] == alpha_movie and o["qloo_id"] == "SYNTHETIC-ENT-M102"]
        self.assertEqual([o["rank"] for o in m102], [2, 4])
        self.assertIsNone(m102[0]["duplicate_of"])
        self.assertEqual(m102[1]["duplicate_of"], m102[0]["evidence_id"])
        comparison = read_json(self.paths.normalized_dir / "comparison.json")
        movie = next(g for g in comparison["related_entity_overlap"] if g["comparability"]["entity_type"] == "urn:entity:movie")
        self.assertEqual(movie["result_counts"], {"alpha": 4, "beta": 5})
        self.assertEqual(movie["pairwise"][0]["intersection"], 2)

    def test_explicit_error_states(self):
        book = self.request("related_entities", "alpha", "book")
        self.assertEqual(book["status"], "ok")
        self.assertEqual([a["status"] for a in book["attempts"]], ["rate_limited", "ok"])
        self.assertEqual(self.request("related_entities", "beta", "artist")["status"], "ok_empty")
        self.assertEqual(self.request("related_entities", "beta", "book")["status"], "rejected_request")
        self.assertEqual(self.request("seed_detail", "beta")["status"], "not_found")
        tags = self.request("seed_tags", "beta")
        self.assertEqual(tags["status"], "transient_error")
        self.assertEqual(len(tags["attempts"]), 3)
        for seed in ("gamma", "delta"):
            dependents = [r for r in self.requests if r["seed_key"] == seed and r["operation"] != "search"]
            self.assertTrue(dependents)
            self.assertTrue(all(r["status"] == "skipped_unresolved_seed" and not r["attempts"] for r in dependents))

    def test_seed_resolution_outcomes(self):
        self.assertEqual(self.resolutions["alpha"]["status"], "resolved")
        beta = self.resolutions["beta"]
        self.assertEqual((beta["status"], beta["qloo_id"]), ("resolved", "SYNTHETIC-ENT-B001"))
        self.assertEqual([a["qloo_id"] for a in beta["alternatives"]], ["SYNTHETIC-ENT-B002"])
        self.assertEqual(self.resolutions["gamma"]["status"], "ambiguous")
        self.assertIsNone(self.resolutions["gamma"]["qloo_id"])
        self.assertEqual(self.resolutions["delta"]["status"], "unresolved")
        self.assertTrue(all(r["matches_runtime_decision"] for r in self.resolutions.values()))

    def test_tag_shares_count_each_seed_from_its_own_observations(self):
        comparison = read_json(self.paths.normalized_dir / "comparison.json")
        movie = next(b for b in comparison["sample_tag_shares"] if b["comparability"]["entity_type"] == "urn:entity:movie")
        beta_tags = {row["tag_id"] for row in movie["per_seed"]["beta"]}
        self.assertNotIn("synthetic:tag:streaming_service:media:fx_s1", beta_tags)

    def test_evidence_excerpt_refuses_synthetic_runs(self):
        from motif_spike.excerpt import render_excerpt
        with self.assertRaises(ValueError):
            render_excerpt(self.paths)

    def test_renormalize_is_deterministic(self):
        before = (self.paths.normalized_dir / "observations.jsonl").read_text(encoding="utf-8")
        normalize_run(self.paths)
        self.assertEqual(before, (self.paths.normalized_dir / "observations.jsonl").read_text(encoding="utf-8"))

    def test_auth_error_stops_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli(["run", "--mode", "synthetic", "--scenario", "auth_error", "--data-dir", tmp])
            paths = only_run(Path(tmp), "synthetic-")
            statuses = [r["status"] for r in read_jsonl(paths.requests_log)]
        self.assertEqual(code, 3)
        self.assertEqual(statuses[0], "auth_error")
        self.assertTrue(all(s == "skipped_after_auth_error" for s in statuses[1:]))


class LiveGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.log = self.root / "fake_calls.jsonl"
        self.manifest = read_json(Path(cli.CONFIG_DIR) / "manifest.json")

    def tearDown(self):
        self.tmp.cleanup()

    def live_run(self, mode="ok", seeds=("a24",), domains=("movie",), max_requests=None, reuse=True):
        env = dict(os.environ, QLOO_API_KEY=SECRET, FAKE_QLOO_MODE=mode, FAKE_QLOO_LOG=str(self.log))
        plan = build_plan(self.manifest, "pilot", list(seeds), list(domains), max_requests)
        paths = RunPaths(self.root, f"live-test-{len(list((self.root / 'raw').glob('*'))) if (self.root / 'raw').exists() else 0}")
        index = build_reuse_index(self.root) if reuse else {}
        with mock.patch.dict(os.environ, {"QLOO_API_KEY": SECRET}):
            run = Runner(plan, HarnessTransport(FAKE_QLOO, env=env), paths, reuse_index=index, sleep=lambda s: None).run()
            normalize_run(paths)
        return run, paths

    def calls(self):
        return read_jsonl(self.log)

    def test_readiness_reports_presence_only(self):
        ready = check_readiness(env=dict(os.environ, QLOO_API_KEY=SECRET), command=FAKE_QLOO)
        self.assertTrue(ready.live_ready)
        self.assertEqual(ready.credential_source, "environment")
        self.assertNotIn(SECRET, json.dumps(ready.to_record()))
        missing = check_readiness(env={k: v for k, v in os.environ.items() if k != "QLOO_API_KEY"}, command=FAKE_QLOO)
        self.assertFalse(missing.live_ready)

    def test_live_mode_without_harness_refuses_and_writes_nothing(self):
        with mock.patch.dict(os.environ, {"PATH": "", "QLOO_HARNESS_BIN": ""}):
            code, out = run_cli(["run", "--mode", "live", "--plan", "pilot", "--transport", "harness", "--data-dir", self.tmp.name])
        self.assertEqual(code, 2)
        self.assertIn("no synthetic data was substituted", out)
        self.assertFalse((self.root / "raw").exists())

    def test_rejected_credential_stops_without_fallback_or_leak(self):
        run, paths = self.live_run(mode="reject", seeds=("a24", "muji"))
        records = read_jsonl(paths.requests_log)
        self.assertEqual(run["status"], "aborted_auth_error")
        self.assertEqual(records[0]["status"], "forbidden")
        self.assertTrue(all(r["status"] == "skipped_after_auth_error" for r in records[1:]))
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(read_jsonl(paths.normalized_dir / "observations.jsonl"), [])
        for path in self.root.rglob("*"):
            if path.is_file() and path != self.log:
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(SECRET, text, path)
                self.assertNotIn("SYNTHETIC", text, path)

    def test_identical_successful_requests_are_reused_not_resent(self):
        first, _ = self.live_run()
        sent_first = len(self.calls())
        self.assertEqual(first["counts"]["harness_invocations"], sent_first)
        second, paths = self.live_run()
        self.assertEqual(len(self.calls()), sent_first)
        self.assertEqual(second["counts"]["harness_invocations"], 0)
        records = read_jsonl(paths.requests_log)
        self.assertTrue(all(r["reused_from"] and r["status"] == "ok" for r in records))
        third, _ = self.live_run(reuse=False)
        self.assertEqual(len(self.calls()), 2 * sent_first)

    def test_reuse_never_crosses_transports(self):
        from motif_spike.runner import signature
        self.live_run()
        argv = ["api", "search", "--query", "A24", "--take", "10", "--json"]
        self.assertNotEqual(signature(argv, "harness"), signature(argv, "direct"))
        self.assertTrue(build_reuse_index(self.root, transport="harness"))
        self.assertEqual(build_reuse_index(self.root, transport="direct"), {})

    def test_two_seeds_resolving_to_one_entity_share_requests(self):
        # The fake search returns the same entity ID for every query.
        run, paths = self.live_run(seeds=("a24", "muji"))
        records = read_jsonl(paths.requests_log)
        muji_dependents = [r for r in records if r["seed_key"] == "muji" and r["operation"] != "search"]
        self.assertTrue(all(r["reused_from"]["run_id"] == paths.run_id for r in muji_dependents))

    def test_budget_is_enforced(self):
        run, paths = self.live_run(seeds=("a24", "muji"), domains=("movie", "artist", "brand"), max_requests=3)
        statuses = [r["status"] for r in read_jsonl(paths.requests_log)]
        self.assertEqual(run["counts"]["harness_invocations"], 3)
        self.assertEqual(len(self.calls()), 3)
        self.assertEqual(statuses[3:], ["skipped_budget"] * (len(statuses) - 3))
        resolutions = {r["seed_key"]: r for r in read_json(paths.normalized_dir / "seed_resolutions.json")}
        self.assertEqual(resolutions["a24"]["status"], "resolved")
        self.assertEqual(resolutions["muji"]["status"], "not_attempted")


class EventBaseUrl(unittest.TestCase):
    HACKATHON = "https://hackathon.api.qloo.com"

    def test_live_manifest_pins_the_event_api(self):
        plan = build_plan(load_manifest(), "pilot")
        self.assertEqual(plan.harness_env, {"QLOO_BASE_URL": self.HACKATHON, "QLOO_TRUSTED_BASE_URL": self.HACKATHON})

    def test_manifest_cannot_carry_a_credential(self):
        with self.assertRaises(ValueError):
            harness_environment({"harness_environment": {"QLOO_API_KEY": "should-never-be-here"}})

    def test_manifest_overrides_the_shell_but_keeps_the_key(self):
        env = live_environment({"QLOO_BASE_URL": self.HACKATHON},
                               base={"QLOO_BASE_URL": "https://other.example", "QLOO_API_KEY": SECRET})
        self.assertEqual(env["QLOO_BASE_URL"], self.HACKATHON)
        self.assertEqual(env["QLOO_API_KEY"], SECRET)

    def test_live_cli_run_sends_every_call_to_the_event_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "calls.jsonl"
            overrides = {"QLOO_API_KEY": SECRET, "FAKE_QLOO_MODE": "ok", "FAKE_QLOO_LOG": str(log), "QLOO_BASE_URL": "https://stale.example"}
            with mock.patch.dict(os.environ, overrides), \
                    mock.patch.object(cli, "harness_command", lambda env=None: FAKE_QLOO), \
                    mock.patch.object(readiness, "harness_command", lambda env=None: FAKE_QLOO):
                code, out = run_cli(["run", "--mode", "live", "--plan", "pilot", "--transport", "harness", "--seeds", "a24", "--domains", "movie",
                                     "--data-dir", str(Path(tmp) / "data")])
            calls = read_jsonl(log)
            paths = only_run(Path(tmp) / "data", "live-")
            facts = (paths.normalized_dir / "facts.md").read_text(encoding="utf-8")
        self.assertEqual(code, 0, out)
        self.assertTrue(calls)
        self.assertEqual({c["base_url"] for c in calls}, {self.HACKATHON})
        self.assertIn(self.HACKATHON, facts)
        self.assertNotIn(SECRET, facts)


if __name__ == "__main__":
    unittest.main()

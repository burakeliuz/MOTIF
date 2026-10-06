"""Research controller, Qloo access, and prose on SYNTHETIC bodies and a fake transport (no network)."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import (AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, entities_body, http_error, insights_body,
                              ok, search_body)
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import (AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, entities_body, http_error, insights_body,
                             ok, search_body)
import json
import tempfile
import unittest
from pathlib import Path

from motif.agent import Controller
from motif.brief import validate_prose
from motif.engine import run_engine
from motif.llm import write_prose, writer_from_env
from motif.qloo import LiveQloo, RecordedQloo

SEED = "SYN-SEED"
BRAND_TAGS = [("SYN-B1", "SYN Brand One", [("Understated", AESTHETIC), ("Clean Lines", AESTHETIC)]),
              ("SYN-B2", "SYN Brand Two", [("Earthy Tones", AESTHETIC), ("Clean Lines", AESTHETIC)])]


def routes(search=None, own=None, brand=None, movie=None, artist=None):
    search = search or search_body([(SEED, "Synthbrand", "urn:entity:brand"), ("SYN-PLACE", "Synthbrand", "urn:entity:place")])
    own = own or entities_body(SEED, "Synthbrand", [("Unpretentious", TONE), ("Clean Lines", AESTHETIC), ("Natural Materials", AESTHETIC)])
    bodies = {"search": search, "entity": own,
              "urn:entity:brand": brand or insights_body(BRAND_TAGS),
              "urn:entity:movie": movie or insights_body([("SYN-M1", "SYN Film", [("Muted", STYLE)])]),
              "urn:entity:artist": artist or insights_body([])}

    def answer(argv):
        if argv[:2] == ["api", "search"]:
            body = bodies["search"]
        elif argv[:2] == ["api", "entity"]:
            body = bodies["entity"]
        else:
            body = bodies[argv[argv.index("--type") + 1]]
        return body if not isinstance(body, dict) else ok(body)
    return answer


def live(transport, max_requests=8, session_dir=None):
    return LiveQloo(transport, "https://example.invalid", session_dir, max_requests, max_retries=2,
                    backoff_s=[0, 0], sleep=lambda s: None)


class ControllerFlow(unittest.TestCase):
    def test_end_to_end_records_each_decision_and_never_repeats_a_request(self):
        transport = FakeTransport(routes())
        out = Controller(live(transport), CONFIG, "Synthbrand", "brand", allow_unverified=True).run()
        self.assertEqual(out["status"], "completed")
        self.assertEqual(out["resolution"]["qloo_id"], SEED)
        self.assertEqual([t["action"] for t in out["trace"]],
                         ["resolve", "fetch_own", "fetch_related:brand", "fetch_related:movie", "finish"])
        self.assertTrue(all(t["reason"] for t in out["trace"]))
        self.assertEqual(len(transport.calls), len({json.dumps(c) for c in transport.calls}))
        targets = {a: v["value"] for a, v in out["result"]["axes"].items() if v["state"] == "target"}
        self.assertEqual(targets, {"light_dense": "light", "raw_polished": "polished", "natural_synthetic": "natural"})

    def test_corroborating_domain_is_skipped_only_when_provably_useless(self):
        own = entities_body(SEED, "Synthbrand", [("Typewriter Font", AESTHETIC)])  # no cue at all
        transport = FakeTransport(routes(own=own, brand=insights_body([])))
        out = Controller(live(transport), CONFIG, "Synthbrand").run()
        movie_step = next(t for t in out["trace"] if t["action"] == "fetch_related:movie")
        self.assertEqual(movie_step["decision"], "skip")
        self.assertIn("cannot change", movie_step["reason"])
        self.assertFalse(any("urn:entity:movie" in c for c in transport.calls))

    def test_unmapped_anchored_motif_still_justifies_the_fetch(self):
        # An unmapped motif with anchored support can change the outcome, so movies must be fetched.
        own = entities_body(SEED, "Synthbrand", [("Classic", TONE)])
        movie = insights_body([("SYN-M1", "SYN Film", [("Timeless", STYLE)])])
        transport = FakeTransport(routes(own=own, brand=insights_body([]), movie=movie))
        out = Controller(live(transport), CONFIG, "Synthbrand").run()
        movie_step = next(t for t in out["trace"] if t["action"] == "fetch_related:movie")
        self.assertEqual(movie_step["decision"], "fetched")
        self.assertEqual(out["result"]["motifs"]["heritage"]["strength"], "moderate")
        self.assertEqual(out["outcome"], "no_translation_rule")  # would have been insufficient_evidence if skipped

    def test_ambiguous_name_asks_and_offers_requested_type_candidates(self):
        search = search_body([("SYN-P1", "Synthbrand", "urn:entity:place"), ("SYN-P2", "Synthbrand", "urn:entity:place"),
                              (SEED, "Synthbrand Fragrances", "urn:entity:brand")])
        transport = FakeTransport(routes(search=search))
        out = Controller(live(transport), CONFIG, "Synthbrand", "brand").run()
        self.assertEqual(out["status"], "needs_choice")
        offered = [o["qloo_id"] for o in out["question"]["options"]]
        self.assertEqual(offered, ["SYN-P1", "SYN-P2", SEED])
        self.assertEqual(len(transport.calls), 1)  # nothing fetched for an unchosen entity

    def test_type_any_with_two_exact_types_asks(self):
        out = Controller(live(FakeTransport(routes())), CONFIG, "Synthbrand", "any").run()
        self.assertEqual(out["outcome"], "needs_entity_choice")

    def test_choice_must_be_a_returned_candidate(self):
        bad = Controller(live(FakeTransport(routes())), CONFIG, "Synthbrand", choose="SYN-NOT-RETURNED").run()
        self.assertEqual(bad["outcome"], "invalid_choice")
        good = Controller(live(FakeTransport(routes())), CONFIG, "Synthbrand", "any", choose=SEED, allow_unverified=True).run()
        self.assertEqual(good["resolution"]["method"], "user_choice")

    def test_credential_error_stops_without_any_substitute(self):
        transport = FakeTransport(lambda argv: http_error(401))
        out = Controller(live(transport), CONFIG, "Synthbrand").run()
        self.assertEqual(out["outcome"], "stopped_access_error")
        self.assertIsNone(out["result"])
        self.assertEqual(len(transport.calls), 1)

    def test_rate_limit_retries_are_bounded_by_the_budget(self):
        transport = FakeTransport(lambda argv: http_error(429))
        access = live(transport, max_requests=2)
        out = Controller(access, CONFIG, "Synthbrand").run()
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(access.network_attempts, 2)
        self.assertEqual(out["status"], "stopped")

    def test_budget_exhaustion_stops_with_a_partial_result(self):
        transport = FakeTransport(routes())
        out = Controller(live(transport, max_requests=3), CONFIG, "Synthbrand").run()
        self.assertEqual(out["outcome"], "stopped_budget")
        self.assertTrue(out.get("partial_result"))
        self.assertEqual(len(transport.calls), 3)


class AccessAndCache(unittest.TestCase):
    def test_cache_is_used_only_for_the_identical_request(self):
        transport = FakeTransport(routes())
        access = live(transport)
        a = access.request("seed_detail", ["api", "entity", "--id", SEED, "--json"])
        b = access.request("seed_detail", ["api", "entity", "--id", SEED, "--json"])
        c = access.request("seed_detail", ["api", "entity", "--id", "SYN-OTHER", "--json"])
        self.assertEqual(b["served_from"], "session_cache")
        self.assertNotIn("served_from", c)
        self.assertEqual(len(transport.calls), 2)
        self.assertNotEqual(a["signature"], c["signature"])

    def test_live_and_recorded_caches_never_share_a_namespace(self):
        live_access = live(FakeTransport(routes()))
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requests.jsonl").write_text("", encoding="utf-8")
            recorded = RecordedQloo(Path(tmp), None, 5)
            self.assertNotEqual(live_access.cache_namespace(), recorded.cache_namespace())

    def test_recorded_mode_never_reaches_the_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Path(tmp) / "rec"
            access = live(FakeTransport(routes()), session_dir=session)
            Controller(access, CONFIG, "Synthbrand").run()
            replay = RecordedQloo(session, None, 5)
            out = Controller(replay, CONFIG, "Synthbrand", allow_unverified=True).run()
            self.assertEqual(out["status"], "completed")
            missing = replay.request("seed_detail", ["api", "entity", "--id", "SYN-NEVER-FETCHED", "--json"])
            self.assertEqual(missing["status"], "not_recorded")
            self.assertEqual(replay.network_attempts, 0)


class Prose(unittest.TestCase):
    def setUp(self):
        transport = FakeTransport(routes())
        self.result = Controller(live(transport), CONFIG, "Synthbrand", allow_unverified=True).run()["result"]

    def test_template_prose_passes_the_validator_and_names_open_axes(self):
        out = write_prose("Synthbrand", self.result, None)
        self.assertEqual(out["author"], "template")
        self.assertEqual(validate_prose(out["text"], self.result), [])
        for word in ("temperature", "projection", "sweetness"):
            self.assertIn(word, out["text"])

    def test_llm_text_adding_engine_external_claims_is_rejected(self):
        bad = ("A light polished scent with sandalwood at 20%, proven to please. Temperature, projection and "
               "sweetness stay open.")
        problems = validate_prose(bad, self.result)
        self.assertTrue(any("sandalwood" in p for p in problems))
        self.assertTrue(any("percentage" in p for p in problems))
        self.assertTrue(any("claim" in p for p in problems))
        self.assertTrue(any("projection" in p for p in validate_prose("Light and polished.", self.result)))

    def test_llm_writer_falls_back_to_the_template_after_bounded_retries(self):
        class Fake:
            calls = 0

            def describe(self):
                return {"provider": "fake", "model": "fake"}

            def write(self, payload, feedback=None):
                Fake.calls += 1
                return "Add vanilla. Temperature, projection, sweetness open."

        out = write_prose("Synthbrand", self.result, Fake())
        self.assertEqual(out["author"], "template")
        self.assertEqual(Fake.calls, 2)
        self.assertIn("failed validation", out["note"])

    def test_valid_llm_text_is_kept_and_labelled(self):
        class Good:
            def describe(self):
                return {"provider": "fake", "model": "fake"}

            def write(self, payload, feedback=None):
                names = " and ".join(m["name"] for m in payload["materials"])
                return (f"Aim light and polished with a natural impression; start from {names}. "
                        "Temperature, projection and sweetness are not set by the evidence.")

        out = write_prose("Synthbrand", self.result, Good())
        self.assertEqual(out["author"], "llm")

    def test_without_llm_configuration_the_template_is_used(self):
        self.assertIsNone(writer_from_env({})["writer"])
        # only MOTIF's own variable is read; the SDK's default variable is ignored
        self.assertIsNone(writer_from_env({"ANTHROPIC_API_KEY": "x"})["writer"])
        self.assertIsNone(writer_from_env({"MOTIF_ANTHROPIC_API_KEY": "x", "MOTIF_LLM_PROVIDER": "off"})["writer"])

    def test_default_model_and_explicit_key(self):
        try:
            import anthropic  # noqa: F401
        except ImportError:
            self.skipTest("anthropic SDK not installed")
        out = writer_from_env({"MOTIF_ANTHROPIC_API_KEY": "test-not-a-key"})
        self.assertEqual(out["writer"].model, "claude-sonnet-5-5")
        self.assertEqual(writer_from_env({"MOTIF_ANTHROPIC_API_KEY": "t", "MOTIF_LLM_MODEL": "m"})["writer"].model, "m")

    def test_call_budget_and_api_errors_fall_back_to_labelled_template(self):
        from motif.llm import AnthropicProseWriter, CallLedger

        class FailingClient:
            class messages:
                @staticmethod
                def create(**kw):
                    raise ConnectionError("network down")

        ledger = CallLedger(None, 1)
        writer = AnthropicProseWriter("k", "claude-sonnet-5-5", client=FailingClient(), ledger=ledger)
        out = write_prose("Synthbrand", self.result, writer)
        self.assertEqual(out["author"], "template")
        self.assertIn("call failed", out["note"])
        self.assertEqual(ledger.calls_today(), 1)  # the failed call is still counted
        out2 = write_prose("Synthbrand", self.result, writer)  # budget of 1 now exhausted: no call at all
        self.assertEqual(out2["llm"]["attempts"][0]["error"], "BudgetExhausted")
        self.assertEqual(ledger.calls_today(), 1)

if __name__ == "__main__":
    unittest.main()

"""Checks added in the post-6B review (SYNTHETIC data only, no network).

* the result's lead: motifs from the brand's own entry lead; a direction drawn only
  from related references never leads; untranslated motifs stay in the title;
* web and printed brief read the same fields (reference list, sources, headline);
* a live server shows no recorded-mode wording, and recorded mode is refused on Render;
* the LLM budget guard pauses Claude when its counter would not survive a restart;
* one controlled retry after a failed Qloo request, behind the sign-in gate.
"""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, evidence_item, http_error
    from .test_motif_web import PASSWORD, FakeHub, GatedServer, routes, settle, wait
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, FakeTransport, evidence_item, http_error
    from test_motif_web import PASSWORD, FakeHub, GatedServer, routes, settle, wait
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from motif.brief import template_prose, validate_prose
from motif.engine import run_engine
from motif.narrative import headline, profile
from motif.qloo import LiveQloo
from motif.web import server as web_server
from motif.web.guard import PAUSED_NOTE, llm_guard
from motif.web.present import result_view

STATIC = Path(__file__).resolve().parent.parent / "motif" / "web" / "static"


def engine(items):
    return run_engine([evidence_item(*i) for i in items], CONFIG)


# own entry, related brands, related films (all invented)
SUPREME_LIKE = [("own", "SYN-1", "Edgy", TONE), ("own", "SYN-1", "Rebellious", TONE),
                ("brand", "SYN-B1", "Provocative", TONE), ("brand", "SYN-B1", "Understated", STYLE),
                ("movie", "SYN-M1", "Muted", STYLE)]
LELABO_LIKE = [("own", "SYN-1", "Fragrance Shop", AESTHETIC),
               ("brand", "SYN-B1", "Clean Lines", AESTHETIC), ("brand", "SYN-B1", "Muted", STYLE),
               ("movie", "SYN-M1", "Clean Lines", AESTHETIC), ("movie", "SYN-M1", "Understated", STYLE)]
AESOP_LIKE = [("own", "SYN-1", "Clean Lines", AESTHETIC), ("own", "SYN-1", "Botanical", AESTHETIC),
              ("brand", "SYN-B1", "Architectural", AESTHETIC), ("brand", "SYN-B1", "Natural Materials", AESTHETIC),
              ("brand", "SYN-B1", "Muted", STYLE), ("movie", "SYN-M1", "Understated", STYLE),
              ("movie", "SYN-M1", "Structured", AESTHETIC)]


class Lead(unittest.TestCase):
    def test_an_untranslated_own_motif_leads_and_a_relations_only_direction_does_not(self):
        r = engine(SUPREME_LIKE)
        h = headline("Synthsupreme", r)
        self.assertEqual(h["title"], "A profile led by provocation.")
        self.assertEqual(h["label"], "Partial direction")
        self.assertIn("open to the perfumer", h["lines"][0])
        self.assertIn("drawn only from references Qloo relates to Synthsupreme", h["lines"][1])
        self.assertNotIn("light", h["title"])
        self.assertNotIn("no scent rule", h["title"])

    def test_a_direction_only_from_references_is_labelled_as_such(self):
        h = headline("Synthlabo", engine(LELABO_LIKE))
        self.assertEqual(h["label"], "Direction from related references")
        self.assertTrue(h["title"].endswith("direction from related references."))
        self.assertIn("do not support a direction on their own", h["lines"][0])

    def test_own_motifs_lead_and_relation_only_targets_move_to_a_line(self):
        r = engine(AESOP_LIKE)
        h = headline("Synthsop", r)
        self.assertEqual(h["title"], "Precision and naturalness: a smooth-finished and natural-feeling scent.")
        self.assertEqual(h["lines"], ["MOTIF also proposes a light weight, drawn only from references Qloo relates to Synthsop."])
        rows = profile("Synthsop", r)
        self.assertEqual([x["own"] for x in rows], sorted([x["own"] for x in rows], reverse=True))  # own first

    def test_no_signal_says_so_and_the_template_opens_with_the_same_lead(self):
        r = engine([("own", "SYN-1", "Fragrance Shop", AESTHETIC)])
        self.assertEqual(headline("Synthnone", r)["label"], "No direction yet")
        for items in (SUPREME_LIKE, LELABO_LIKE, AESOP_LIKE):
            r = engine(items)
            text = template_prose("Synth24", r)
            self.assertIn(headline("Synth24", r)["title"], text)
            self.assertEqual(validate_prose(text, r, "Synth24"), [])  # a brand name with digits is not a stray number


class WebAndPrintAgree(unittest.TestCase):
    def test_partial_result_lists_the_same_reference_materials_with_sources_or_claims_none(self):
        r = engine(SUPREME_LIKE)
        v = result_view("Synthsupreme", r, CONFIG.rules, CONFIG.palette)
        mats = v["materials"]
        self.assertEqual(mats["selected"], [])
        ref = mats["reference"]
        self.assertTrue(ref["items"])
        self.assertEqual({s["material"] for s in v["sources"]["suppliers"]}, {m["name"] for m in ref["items"]})
        for s in v["sources"]["suppliers"]:
            self.assertTrue(s["url"].startswith("https://"))
        # a partial result without fitting materials makes no claim of a list
        no_fit = json.loads(json.dumps(r))
        no_fit["materials"]["ranked"] = []
        v2 = result_view("Synthsupreme", no_fit, CONFIG.rules, CONFIG.palette)
        self.assertIsNone(v2["materials"]["reference"])
        self.assertNotIn("listed", v2["materials"]["status_text"])
        self.assertIn("No verified material fits", v2["materials"]["status_text"])

    def test_qloo_is_cited_by_request_and_date_never_by_a_made_up_url(self):
        v = result_view("Synthsop", engine(AESOP_LIKE), CONFIG.rules, CONFIG.palette)
        q = v["sources"]["qloo"]
        self.assertTrue(q["requests"])
        self.assertNotIn("http", json.dumps(q))

    def test_the_printed_brief_reads_the_shared_fields_and_has_no_empty_list_text(self):
        js = (STATIC / "print.js").read_text(encoding="utf-8")
        for field in ("r.headline", "mats.reference", "r.sources", "r.direction", "r.still_open", "r.profile"):
            self.assertIn(field, js)
        self.assertNotIn("supplier pages (", js)
        self.assertNotIn("Set by the evidence", js)
        app = (STATIC / "app.js").read_text(encoding="utf-8")
        for field in ("r.headline", "mats.reference", "r.sources", "r.still_open"):
            self.assertIn(field, app)
        for name in ("print.js", "strips.js"):
            code = "\n".join(line for line in (STATIC / name).read_text(encoding="utf-8").splitlines()
                             if not line.lstrip().startswith(("*", "/*", "//")))
            for sink in (".innerHTML", ".outerHTML", "insertAdjacentHTML", "document.write", "eval("):
                self.assertNotIn(sink, code, name)


class NoRecordedWordingLive(unittest.TestCase):
    def test_live_views_carry_no_recorded_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = FakeHub(tmp)
            self.assertIsNone(hub.describe()["mode_label"])
            _, body = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
            view = wait(hub, body["id"])
            text = json.dumps(view).lower()
            self.assertNotIn("recorded", text)
            settle(hub)
        app = (STATIC / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("Recorded data", app)

    def test_recorded_mode_is_refused_on_render(self):
        with mock.patch.dict("os.environ", {"RENDER": "true"}), \
                mock.patch.object(web_server, "ThreadingHTTPServer", side_effect=AssertionError("must not start")):
            self.assertEqual(web_server.main(["--recorded", "data/raw/x"]), 2)


MOUNTS = "overlay / overlay rw 0 0\n/dev/vdb /var/data ext4 rw 0 0\ntmpfs /tmp tmpfs rw 0 0\n"


class BudgetGuard(unittest.TestCase):
    def test_counters_must_survive_a_restart_before_claude_is_used_on_render(self):
        self.assertTrue(llm_guard({}, Path("/srv/data"), MOUNTS)["allowed"])  # not on Render: local disk
        self.assertFalse(llm_guard({"RENDER": "true"}, Path("/srv/data"), MOUNTS)["allowed"])
        self.assertTrue(llm_guard({"RENDER": "true", "MOTIF_DATA_DIR": "/var/data"}, Path("/var/data/motif"), MOUNTS)["allowed"])
        self.assertFalse(llm_guard({"RENDER": "true", "MOTIF_DATA_DIR": "/tmp/m"}, Path("/tmp/m"), MOUNTS)["allowed"])
        provider = llm_guard({"RENDER": "true", "MOTIF_LLM_BUDGET_GUARD": "provider"}, Path("/srv"), MOUNTS)
        self.assertEqual((provider["allowed"], provider["durable"]), (True, False))
        self.assertFalse(llm_guard({"MOTIF_LLM_BUDGET_GUARD": "off"}, Path("/srv"), MOUNTS)["allowed"])
        self.assertFalse(llm_guard({"MOTIF_LLM_BUDGET_GUARD": "yes please"}, Path("/srv"), MOUNTS)["allowed"])

    def test_a_paused_claude_makes_no_call_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = FakeHub(tmp, env={"RENDER": "true", "MOTIF_ANTHROPIC_API_KEY": "placeholder-TEST-ONLY-not-a-key"})
            self.assertEqual(hub.describe()["llm"], "paused")
            self.assertIsNone(hub._writer())
            _, body = hub.create({"reference": "Synthbrand"}, "10.0.0.1")
            view = wait(hub, body["id"])
            self.assertEqual(view["brief"]["author"], "template")
            self.assertEqual(view["brief"]["note"], PAUSED_NOTE)
            self.assertIn("paused", view["suggestions"]["message"])
            self.assertEqual(hub.suggest(body["id"])[1]["status"], "unavailable")
            self.assertFalse((Path(tmp) / "llm_calls.jsonl").exists())
            settle(hub)


class FlakyHub(FakeHub):
    """Related-film requests fail `fail_times` times with `status` (retries included), then answer."""

    def __init__(self, root, fail_times=3, status=503, **kw):
        super().__init__(root, **kw)
        self.fail_left = fail_times
        self.status = status

    def _new_access(self, sdir):
        base = routes(self.search)

        def answer(argv):
            if "--type" in argv and argv[argv.index("--type") + 1] == "urn:entity:movie" and self.fail_left > 0:
                self.fail_left -= 1
                return http_error(self.status)
            return base(argv)
        transport = FakeTransport(answer)
        self.transports.append(transport)
        return LiveQloo(transport, "https://example.invalid", sdir, 8, max_retries=2, backoff_s=[0, 0], sleep=lambda s: None)


class Retry(unittest.TestCase):
    def test_one_retry_resends_only_the_failed_step_within_a_reserved_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = FlakyHub(tmp)
            _, body = hub.create({"reference": "Synthbrand", "choose": "SYN-BRAND-1"}, "10.0.0.1")
            first = wait(hub, body["id"])
            self.assertEqual((first["status"], first["stop_reason"]), ("stopped", "stopped_request_failed"))
            self.assertTrue(first["result"])  # the partial result actually collected is shown
            self.assertEqual(first["result"]["headline"]["label"], "Partial result")
            self.assertTrue(first["retry"]["available"])
            self.assertTrue(all(s["who"] is None for s in first["steps"] if s["status"] in ("not_run", "pending", "skipped")))
            sent_before = [list(c) for c in hub.transports[0].calls]
            code, again = hub.retry(body["id"])
            self.assertEqual(code, 202)
            done = wait(hub, again["id"])
            self.assertEqual(done["status"], "completed")
            new_calls = hub.transports[0].calls[len(sent_before):]
            self.assertEqual(len(new_calls), 1)  # only the failed films request went out again
            self.assertIn("urn:entity:movie", new_calls[0])
            self.assertEqual(hub.retry(body["id"]), (200, {"id": again["id"], "reused": True}))
            self.assertEqual(hub.retry(again["id"])[0], 409)  # at most one retry
            self.assertEqual(hub.create({"reference": "Synthbrand", "choose": "SYN-BRAND-1"}, "10.0.0.1")[1]["id"], again["id"])
            usage = hub.usage.today()
            self.assertEqual((usage["sessions"], usage["qloo"]), (1, len(hub.transports[0].calls)))
            settle(hub)

    def test_credential_errors_are_never_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            hub = FlakyHub(tmp, fail_times=1, status=401)
            _, body = hub.create({"reference": "Synthbrand", "choose": "SYN-BRAND-1"}, "10.0.0.1")
            view = wait(hub, body["id"])
            self.assertEqual(view["stop_reason"], "stopped_access_error")
            self.assertFalse(view["retry"]["available"])
            self.assertEqual(hub.retry(body["id"])[0], 409)
            settle(hub)

    def test_retry_needs_sign_in(self):
        srv = GatedServer(PASSWORD)
        self.addCleanup(srv.close)
        self.assertEqual(srv.call("POST", "/api/sessions/abcdefgh/retry", {})[0], 401)
        self.assertEqual(srv.created, [])


if __name__ == "__main__":
    unittest.main()

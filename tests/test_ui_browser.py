"""Browser checks of the start page, the result page, and the printed brief (SYNTHETIC data, loopback only).

Runs tests/ui_check.js in headless Chromium against a local server whose Qloo access is the
synthetic fake transport; no LLM is configured. The page cannot reach the network: every
non-loopback request is aborted, and proxy settings are removed from the browser's environment. Skipped when Node.js,
Playwright, or Chromium is not available (set MOTIF_PLAYWRIGHT_MODULE and MOTIF_CHROMIUM to
point at them).
"""

try:
    from . import _netguard  # noqa: F401
    from .test_motif_web import FakeHub, calls, settle
except ImportError:
    import _netguard  # noqa: F401
    from test_motif_web import FakeHub, calls, settle
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from motif.web.access import AccessGate
from motif.web.server import EXAMPLES, make_handler

HERE = Path(__file__).resolve().parent
MODULE = os.environ.get("MOTIF_PLAYWRIGHT_MODULE", "/opt/node-tools/node_modules/playwright")
CHROME = os.environ.get("MOTIF_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
AVAILABLE = bool(shutil.which("node")) and Path(MODULE).exists() and Path(CHROME).exists()
CONTEXT = {"Flagship store": "A signature scent for the flagship stores", "Hotel lobby": "An ambient scent for a hotel lobby",
           "Fashion show": "A scent direction for a fashion show", "Product launch": "A scent for a product launch",
           "Private event": "An atmospheric scent for a private event", "Retail pop-up": "An ambient scent for a retail pop-up",
           "Exhibition": "A scent direction for a cultural exhibition", "Brand dinner": "A scent for an intimate brand dinner"}


@unittest.skipUnless(AVAILABLE, "Node.js, Playwright, or Chromium not available")
class StartResultAndBrief(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.hub = FakeHub(cls.tmp.name)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cls.hub, AccessGate(False, None)))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        shots = os.environ.get("MOTIF_UI_SHOTS")
        env = {k: v for k, v in os.environ.items() if "proxy" not in k.lower()}
        run = subprocess.run(["node", str(HERE / "ui_check.js"), base, MODULE, CHROME] + ([shots] if shots else []),
                             capture_output=True, text=True, timeout=240, env=env)
        cls.out = json.loads(run.stdout.strip().splitlines()[-1])
        settle(cls.hub)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def setUp(self):
        self.assertNotIn("fatal", self.out)
        self.c = self.out["checks"]

    def test_brand_quick_picks_fill_the_field_and_send_nothing(self):
        self.assertEqual(self.c["brand_picks"], EXAMPLES)
        self.assertEqual(self.c["brand_after_pick"], "Comme des Garçons")
        self.assertEqual(self.c["brand_pick_pressed"], "true")
        self.assertEqual(self.c["posts_after_picks"], 0)

    def test_application_context_picks_fill_an_editable_field(self):
        self.assertEqual(dict(self.c["context_picks"]), CONTEXT)
        self.assertEqual(self.c["context_label"], "Application context (optional)")
        self.assertEqual(self.c["context_placeholder"], "What are you designing the scent for?")
        self.assertIn("frame the final brief", self.c["context_hint"])
        self.assertEqual(self.c["context_after_pick"], "An ambient scent for a hotel lobby")
        self.assertEqual(self.c["context_after_edit"], "An ambient scent for a hotel lobby in Istanbul")
        self.assertEqual(self.c["context_pick_pressed_after_edit"], "false")

    def test_free_text_runs_one_research_and_reaches_the_brief(self):
        self.assertTrue(all(p == "/api/sessions" for p in self.c["posts_after_result"]))
        self.assertEqual(len(self.hub.sessions), len(self.c["posts_after_result"]))
        session = next(iter(self.hub.sessions.values()))
        self.assertEqual(session.params["reference"], "Synthbrand")
        self.assertEqual(session.params["intent"], "A scent for a private gallery opening")
        self.assertIn("A scent for a private gallery opening", self.c["result_context_line"])

    def test_open_decisions_and_suggestions_are_gone_from_the_result_and_the_pdf(self):
        self.assertIsNone(self.c["result_banned"])
        self.assertFalse(self.c["result_has_suggest_block"])
        self.assertIsNone(self.c["pdf_banned"])
        sid = next(iter(self.hub.sessions))
        arch = self.hub.view(sid)["result"]["architecture"]
        extra = ["Emphasize and avoid"] if arch["emphasize"] or arch["avoid"] else []
        self.assertEqual([s[2:] for s in self.c["result_sections"]],
                         ["Cultural profile", "Olfactory direction", "Scent architecture"] + extra
                         + ["Why: Qloo \u2192 motif \u2192 scent", "The brief"])
        self.assertEqual([s[2:] for s in self.c["pdf_sections"]],
                         ["Cultural profile", "Olfactory direction", "Scent architecture"] + extra + ["Why", "The brief"])
        self.assertEqual(self.c["pdf_pages"], 1)

    def test_open_dimensions_and_roles_say_so_plainly(self):
        self.assertEqual(self.c["result_role_names"], ["Opening", "Core", "Drydown"])
        self.assertEqual(self.c["pdf_open_count"] > 0, self.c["result_open_count"] > 0)

    def test_no_internal_wording_and_the_context_appears_once(self):
        self.assertIsNone(self.c["result_internal"])
        self.assertIsNone(self.c["pdf_internal"])
        self.assertEqual(self.c["result_context_count"], 1)
        self.assertEqual(self.c["pdf_context_count"], 1)
        self.assertGreaterEqual(self.c["result_qloo_line"], 1)
        self.assertGreaterEqual(self.c["pdf_qloo_line"], 1)

    def test_the_brief_page_sends_no_request_and_nothing_leaves_the_machine(self):
        self.assertEqual(self.c["posts_after_pdf"], self.c["posts_after_result"])
        self.assertEqual(calls(self.hub), 4)  # search, own entry, related brands, related films: one research only
        self.assertFalse((Path(self.tmp.name) / "llm_calls.jsonl").exists())
        self.assertEqual(self.out["errors"], [])

    def test_the_brief_downloads_as_a_real_one_page_pdf(self):
        self.assertEqual(self.c["result_actions"], ["Download brief (PDF)"])
        self.assertEqual(self.c["download_name"], "MOTIF-Synthbrand-Brief.pdf")
        self.assertEqual(self.c["download_magic"], "%PDF-")
        self.assertEqual(self.c["download_pages"], 1)
        self.assertEqual(self.c["download_status"], "Downloaded MOTIF-Synthbrand-Brief.pdf.")

    def test_labels_do_not_run_under_their_descriptions(self):
        self.assertEqual(self.c["desktop_label_overflow"], [])
        self.assertEqual(self.c["mobile_label_overflow"], [])

    def test_no_horizontal_overflow(self):
        for key in ("desktop_start_overflow", "mobile_start_overflow", "desktop_result_overflow", "mobile_result_overflow"):
            self.assertLessEqual(self.c[key], 0, key)


if __name__ == "__main__":
    unittest.main()


class RemovedSectionsStayOutOfTheSource(unittest.TestCase):
    """Runs everywhere (no browser needed): the removed sections are not rendered by either page."""

    def test_no_open_decisions_or_suggestions_in_the_page_code(self):
        static = HERE.parent / "motif" / "web" / "static"
        for name in ("app.js", "print.js"):
            code = (static / name).read_text(encoding="utf-8")
            for gone in ("Open decisions", "Suggested interpretations", "Unread here", "suggestionsBlock",
                         "decisionsBlock", "Your notes", "Brief purpose", "only smelling can decide"):
                self.assertNotIn(gone, code, f"{gone!r} in {name}")

"""The brief as a real PDF download (motif/web/briefpdf.py): behind the review gate, one A4 page,
rendered from the session already on the server with no new Qloo or LLM request (SYNTHETIC data)."""

try:
    from . import _netguard  # noqa: F401
    from .test_motif_web import COOKIE, PASSWORD, GatedServer, calls, wait
except ImportError:
    import _netguard  # noqa: F401
    from test_motif_web import COOKIE, PASSWORD, GatedServer, calls, wait
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from motif.web import briefpdf

STATIC = Path(__file__).resolve().parent.parent / "motif" / "web" / "static"


def pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf))


class FileName(unittest.TestCase):
    def test_brand_is_folded_to_a_safe_ascii_name(self):
        self.assertEqual(briefpdf.filename("Balenciaga"), "MOTIF-Balenciaga-Brief.pdf")
        self.assertEqual(briefpdf.filename("Comme des Garçons"), "MOTIF-Comme-des-Garcons-Brief.pdf")
        self.assertEqual(briefpdf.filename("Bang & Olufsen"), "MOTIF-Bang-Olufsen-Brief.pdf")
        self.assertEqual(briefpdf.filename('"/\\'), "MOTIF-Brand-Brief.pdf")


@unittest.skipUnless(briefpdf.available(), "fpdf2 is not installed (pip install -r requirements.txt)")
class Download(unittest.TestCase):
    def setUp(self):
        self.srv = GatedServer(PASSWORD)
        self.addCleanup(self.srv.close)

    def signed_in(self):
        code, headers, _ = self.srv.login(PASSWORD)
        self.assertEqual(code, 200)
        return headers["Set-Cookie"].split(";")[0]

    def test_the_pdf_is_behind_the_review_gate(self):
        for cookie in (None, f"{COOKIE}=forged-token"):
            code, headers, body = self.srv.call("GET", "/api/sessions/abcdefgh/brief.pdf", cookie=cookie)
            self.assertEqual((code, json.loads(body)["kind"]), (401, "auth_required"))
            self.assertNotIn("application/pdf", headers.get("Content-Type", ""))
        self.assertEqual(self.srv.hub.sessions, {})

    def test_download_is_one_page_and_sends_nothing_new(self):
        cookie = self.signed_in()
        code, _, body = self.srv.call("POST", "/api/sessions", {"reference": "Synthbrand", "intent": "A hotel lobby"}, cookie=cookie)
        sid = json.loads(body)["id"]
        wait(self.srv.hub, sid)
        before = calls(self.srv.hub)
        ledger = Path(self.srv.tmp.name) / "llm_calls.jsonl"
        ledger_before = ledger.read_bytes() if ledger.exists() else b""
        sessions_before = set(self.srv.hub.sessions)
        rendered = []
        original = briefpdf.render
        briefpdf.render = lambda view: (rendered.append(1), original(view))[1]
        self.addCleanup(setattr, briefpdf, "render", original)

        code, headers, pdf = self.srv.call("GET", f"/api/sessions/{sid}/brief.pdf", cookie=cookie)
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Type"], "application/pdf")
        self.assertEqual(headers["Content-Disposition"], 'attachment; filename="MOTIF-Synthbrand-Brief.pdf"')
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertEqual(pages(pdf), 1)
        # a second download serves the same file without rendering again
        self.assertEqual(self.srv.call("GET", f"/api/sessions/{sid}/brief.pdf", cookie=cookie)[2], pdf)
        self.assertEqual(len(rendered), 1)
        # nothing new reached Qloo or the LLM, and no session was started
        self.assertEqual(calls(self.srv.hub), before)
        self.assertEqual(ledger.read_bytes() if ledger.exists() else b"", ledger_before)
        self.assertEqual(set(self.srv.hub.sessions), sessions_before)

        if shutil.which("pdftotext"):  # selectable text, the context once, and no internal wording
            with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                f.write(pdf)
                f.flush()
                text = subprocess.run(["pdftotext", f.name, "-"], capture_output=True, text=True).stdout
            self.assertIn("SYNTHBRAND", text)
            self.assertIn("Cultural evidence sourced from", text)
            self.assertEqual(text.count("A hotel lobby"), 1)
            self.assertNotRegex(text, r"(?i)technical json|engine-\d|lexicon-\d|draft rule")
            # open dimensions in one paragraph, and the evidence apart from the creative proposal
            self.assertNotRegex(text, r"(Temperature|Weight|Texture|Impression|Projection|Sweetness): Open to the perfumer")
            self.assertIn("QLOO EVIDENCE", text)
            self.assertRegex(text, r"CREATIVE\s+PROPOSAL")

    def test_unknown_session_and_missing_brief_answer_plainly(self):
        cookie = self.signed_in()
        code, _, body = self.srv.call("GET", "/api/sessions/abcdefgh/brief.pdf", cookie=cookie)
        self.assertEqual((code, json.loads(body)["error"]), (404, "Unknown session."))


class NoJsonDownloadInTheInterface(unittest.TestCase):
    """Runs everywhere: the pages offer the PDF brief and no JSON download (the developer API stays)."""

    def test_pages_offer_only_the_pdf(self):
        for name in ("app.js", "print.js", "print.html", "index.html", "download.js"):
            code = (STATIC / name).read_text(encoding="utf-8")
            for gone in ("brief.json", "Technical JSON", "technical JSON", "Download JSON", "Print or save as PDF", "window.print"):
                self.assertNotIn(gone, code, f"{gone!r} in {name}")
        self.assertIn("Download brief (PDF)", (STATIC / "download.js").read_text(encoding="utf-8"))
        self.assertIn("/brief.pdf", (STATIC / "download.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

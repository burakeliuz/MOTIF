"""The researched motif-to-sensory model and its odor evidence stay consistent with their own rules.

Offline: reads only the committed JSON (the odor datasets themselves are not needed).
"""

try:
    from . import _netguard  # noqa: F401
except ImportError:
    import _netguard  # noqa: F401
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import sensory_evidence  # noqa: E402
import sensory_model_review  # noqa: E402

CANDIDATES = ROOT / "config" / "candidates"
MODEL = json.loads((CANDIDATES / "motif_sensory_vectors.v1.json").read_text(encoding="utf-8"))
EVIDENCE = json.loads((CANDIDATES / "odor_axis_evidence.v1.json").read_text(encoding="utf-8"))


class ModelRules(unittest.TestCase):
    def test_the_self_review_finds_no_problem(self):
        rep = sensory_model_review.review(MODEL, EVIDENCE)
        self.assertEqual(rep["problems"], [])

    def test_forbidden_stereotypes_stay_null(self):
        cells = lambda m: MODEL["motifs"][m]["cells"]  # noqa: E731
        self.assertIsNone(cells("playful")["sweet_dry"])
        self.assertIsNone(cells("melancholic")["warm_cool"])
        self.assertIsNone(cells("heritage")["warm_cool"])
        self.assertIsNone(cells("industrial")["natural_synthetic"])
        self.assertEqual(MODEL["motifs"]["romantic"]["imagery"], [])
        self.assertIsNone(cells("restrained")["intimate_projecting"])

    def test_no_cell_claims_more_than_its_evidence(self):
        for m, spec in MODEL["motifs"].items():
            for a, c in spec["cells"].items():
                if c is None:
                    continue
                self.assertNotEqual(c["confidence"], "high", f"{m}.{a}")
                if c["confidence"] == "low":
                    self.assertEqual(c["strength"], "weak", f"{m}.{a}")
                self.assertIn(c["strength"], ("weak", "moderate"), f"{m}.{a}")
                if c["evidence_type"] == "motif_design_inference":
                    self.assertIn("design_origin", c)

    def test_the_dry_pole_is_never_data_supported(self):
        dry = EVIDENCE["summary"].get("sweet_dry:dry", {})
        self.assertTrue(all(s["class"] == "none" for s in dry.values()))
        for m, spec in MODEL["motifs"].items():
            c = spec["cells"]["sweet_dry"]
            if c and c["direction"] == "dry":
                self.assertEqual(c["evidence_type"], "motif_design_inference", m)


class Evidence(unittest.TestCase):
    def test_summary_follows_from_the_measurements(self):
        recomputed = sensory_evidence.summarize(EVIDENCE["measurements"])
        self.assertEqual(json.loads(json.dumps(recomputed)), EVIDENCE["summary"])

    def test_sources_say_what_was_read(self):
        for src in EVIDENCE["sources"].values():
            self.assertIn("dataset only", src["read"])
        self.assertEqual(set(EVIDENCE["files_sha256"]), set(sensory_evidence.FILES))


if __name__ == "__main__":
    unittest.main()

"""Phase 6 diagnostic stays true: the continuous engine separates the 13 trial brands better than the
frozen legacy engine (runs only when the git-ignored recordings are on disk)."""

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

import legacy_baseline  # noqa: E402


@unittest.skipUnless(legacy_baseline.available(), "recordings of the 13 trial brands are not on disk")
class ContinuousVsLegacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import continuous_report
        import engine_compare
        cls.rep = continuous_report.analysis(engine_compare.legacy_results())

    def test_less_collapse_than_the_legacy_engine(self):
        u, d = self.rep["unique"], self.rep["distances"]
        self.assertEqual(u["legacy_targets"], 7)
        self.assertGreaterEqual(u["continuous_resolved_labels"], 11)
        self.assertGreaterEqual(u["continuous_medium_cells_only"], 9)
        self.assertEqual(d["continuous_zero_pairs"], 0)
        self.assertLess(len(d["continuous_near_pairs"]), len(d["legacy_near_pairs"]))
        self.assertLess(self.rep["unresolved_share"]["continuous"], self.rep["unresolved_share"]["legacy"])

    def test_every_dimension_is_reachable(self):
        self.assertTrue(all(v["continuous"] > 0 for v in self.rep["coverage"].values()))

    def test_tentative_dimensions_rest_on_low_cells_only(self):
        for b in self.rep["brands"].values():
            for a in b["axes"].values():
                if a["state"] == "resolved" and a["evidence_basis"] == "design_inference_only" and a["confidence_word"] == "firm":
                    self.fail("a design-only dimension reads firm")

    def test_deterministic(self):
        import continuous_report
        import engine_compare
        again = continuous_report.analysis(engine_compare.legacy_results())
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(self.rep, sort_keys=True))


if __name__ == "__main__":
    unittest.main()

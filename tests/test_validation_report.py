"""Phase 10 validation report (tools/validation_report.py): runs only when the git-ignored recordings exist."""

try:
    from . import _netguard  # noqa: F401
except ImportError:
    import _netguard  # noqa: F401
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import validation_report  # noqa: E402


class Helpers(unittest.TestCase):
    def test_overlap_ignores_empty_proposals(self):
        self.assertIsNone(validation_report.jaccard(set(), {"a"}))
        self.assertEqual(validation_report.jaccard({"a", "b"}, {"b", "c"}), 1 / 3)

    def test_spearman_with_ties(self):
        self.assertEqual(validation_report.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertEqual(validation_report.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(validation_report.spearman([1, 1, 1], [1, 2, 3]))

    def test_agreement_counts_only_where_both_commit(self):
        x = {"warm_cool": "warm", "light_dense": "dense", "raw_polished": None}
        y = {"warm_cool": "warm", "light_dense": "light", "raw_polished": "raw"}
        self.assertEqual(validation_report.agreement(x, y), {"both_commit": 2, "same_pole": 1, "opposite_pole": 1})


@unittest.skipUnless(validation_report.available(), "recordings of the 13 trial brands are not on disk")
class OnRecordings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = validation_report.build()

    def test_deterministic_and_repeatable_across_interpreters(self):
        d = self.rep["determinism"]
        self.assertTrue(d["in_process_identical"])
        self.assertTrue(d["repeatable"], d["fresh_interpreters"])
        self.assertEqual(d["traceable"], self.rep["brands"])

    def test_no_collapse_regression_against_the_legacy_baseline(self):
        c = self.rep["collapse"]
        self.assertGreaterEqual(c["continuous"]["resolved_profiles"], c["legacy"]["sensory_targets"])
        self.assertGreaterEqual(c["continuous"]["architectures"], c["legacy"]["selected_materials"])

    def test_the_report_text_is_stable(self):
        self.assertEqual(validation_report.markdown(self.rep), validation_report.markdown(validation_report.build()))


if __name__ == "__main__":
    unittest.main()

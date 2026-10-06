"""Seed resolution never selects a similar-but-different entity."""

try:
    from . import _netguard  # noqa: F401
except ImportError:  # started as a top-level module (discover -s tests)
    import _netguard  # noqa: F401
import unittest

from motif_spike.manifest import Seed
from motif_spike.resolve import fold_name, resolve_seed


def candidate(qloo_id, name, types, index=0):
    return {"qloo_id": qloo_id, "name": name, "types": {"types": types}, "evidence_id": f"local:obs:0001-{index:03d}",
            "pointer": f"/{index}"}


class ResolveSeed(unittest.TestCase):
    def seed(self, name="Comme des Garçons", expected=("urn:entity:brand",), override=None):
        return Seed(key="s", input_name=name, expected_types=list(expected), override=override)

    def test_fold_name_handles_case_accents_whitespace_only(self):
        self.assertEqual(fold_name("Comme des  GARÇONS"), fold_name("comme des garcons"))
        self.assertNotEqual(fold_name("Nike"), fold_name("Nike SB"))

    def test_unique_exact_match_resolves(self):
        result = resolve_seed(self.seed(), [candidate("ID1", "Comme des Garcons", ["urn:entity:brand"])], "ok")
        self.assertEqual((result["status"], result["qloo_id"]), ("resolved", "ID1"))
        self.assertTrue(result["type_hint_match"])

    def test_near_match_is_not_selected(self):
        result = resolve_seed(self.seed("Nike"), [candidate("ID1", "Nike SB", ["urn:entity:brand"])], "ok")
        self.assertEqual(result["status"], "unresolved")
        self.assertIsNone(result["qloo_id"])
        self.assertEqual(result["near_matches"][0]["qloo_id"], "ID1")

    def test_expected_type_breaks_tie_between_exact_matches(self):
        candidates = [candidate("P1", "Ralph Lauren", ["urn:entity:person"], 0), candidate("B1", "Ralph Lauren", ["urn:entity:brand"], 1)]
        result = resolve_seed(self.seed("Ralph Lauren"), candidates, "ok")
        self.assertEqual((result["status"], result["qloo_id"]), ("resolved", "B1"))
        self.assertEqual([a["qloo_id"] for a in result["alternatives"]], ["P1"])

    def test_same_type_duplicates_are_ambiguous(self):
        candidates = [candidate("B1", "Nike", ["urn:entity:brand"], 0), candidate("B2", "NIKE", ["urn:entity:brand"], 1)]
        result = resolve_seed(self.seed("Nike"), candidates, "ok")
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["qloo_id"])

    def test_failed_search_is_not_unresolved(self):
        self.assertEqual(resolve_seed(self.seed(), [], "rate_limited")["status"], "search_failed")
        self.assertEqual(resolve_seed(self.seed(), [], "ok_empty")["status"], "unresolved")

    def test_override_must_be_a_returned_candidate(self):
        candidates = [candidate("B1", "Nike", ["urn:entity:brand"], 0), candidate("B2", "Nike", ["urn:entity:brand"], 1)]
        ok = resolve_seed(self.seed("Nike", override={"qloo_id": "B2", "reason": "reviewed"}), candidates, "ok")
        self.assertEqual((ok["status"], ok["qloo_id"]), ("resolved_manual", "B2"))
        invented = resolve_seed(self.seed("Nike", override={"qloo_id": "NOT-RETURNED"}), candidates, "ok")
        self.assertEqual(invented["status"], "override_not_in_candidates")
        self.assertIsNone(invented["qloo_id"])


if __name__ == "__main__":
    unittest.main()

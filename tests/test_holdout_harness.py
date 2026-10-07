"""The holdout harness answers an entity question by its pre-registered rule within 4 network attempts
(SYNTHETIC bodies, fake transport, no network)."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import CONFIG, FakeTransport, search_body
    from .test_motif_agent import SEED, live, routes
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import CONFIG, FakeTransport, search_body
    from test_motif_agent import SEED, live, routes
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import holdout_run  # noqa: E402
from motif.config import load_continuous_config  # noqa: E402


class Harness(unittest.TestCase):
    def test_ambiguous_name_is_resolved_by_the_rule_inside_the_budget(self):
        search = search_body([("SYN-FILM", "Synthbrand", "urn:entity:movie"), (SEED, "SYNTHBRAND", "urn:entity:brand"),
                              ("SYN-OTHER", "Synthbrand", "urn:entity:brand")])
        transport = FakeTransport(routes(search=search))
        access = live(transport, max_requests=holdout_run.MAX_PER_BRAND)
        rec = holdout_run.run_brand(access, CONFIG, load_continuous_config(), "Synthbrand")
        self.assertEqual(rec["choice"]["picked"]["qloo_id"], SEED)  # first returned brand with the same folded name
        self.assertEqual(rec["outcome"]["status"], "completed")
        self.assertLessEqual(access.network_attempts, 4)
        self.assertEqual(sum(1 for c in transport.calls if c[:2] == ["api", "search"]), 1)

    def test_rule_folds_case_and_accents(self):
        opts = [{"qloo_id": "m", "name": "Hermes", "types": ["urn:entity:movie"]},
                {"qloo_id": "b", "name": "HERMES", "types": ["urn:entity:brand"]}]
        self.assertEqual(holdout_run.choose_rule("Hermès", opts)["qloo_id"], "b")
        self.assertIsNone(holdout_run.choose_rule("Hermès", opts[:1]))


if __name__ == "__main__":
    unittest.main()

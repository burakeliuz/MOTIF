"""The legacy rule engine (engine-0.3, rules draft-0.2) stays reproducible as a baseline.

* Always: the four legacy config files are byte-identical to the frozen baseline, unless
  their version string changed (a versioned change is allowed; a silent edit is not).
* When the git-ignored recordings of the 13 trial brands are on disk: replaying them gives
  exactly the frozen per-brand stage sets and the 13/13/12/7/7/3 uniqueness counts.
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

import legacy_baseline  # noqa: E402
from motif.config import load_config  # noqa: E402

BASELINE = json.loads((ROOT / "reports" / "baselines" / "legacy_engine_0.3.json").read_text(encoding="utf-8"))


class FrozenConfig(unittest.TestCase):
    def test_legacy_config_is_unchanged_or_versioned(self):
        versions = load_config().versions
        hashes = legacy_baseline.config_hashes()
        pairs ={"lexicon": "motif_lexicon.json", "rules": "draft_rules.json", "palette": "material_palette.json",
                 "params": "engine_params.json"}
        for key, name in pairs.items():
            if versions[key] == BASELINE["versions"][key]:
                self.assertEqual(hashes[name], BASELINE["config_sha256"][name],
                                 f"{name} changed without a version bump (still {versions[key]})")

    def test_baseline_counts_are_the_reported_ones(self):
        self.assertEqual(BASELINE["brands_count"], 13)
        self.assertEqual([BASELINE["unique_per_stage"][s] for s in legacy_baseline.STAGES], [13, 13, 12, 7, 7, 3])


@unittest.skipUnless(legacy_baseline.available(), "recordings of the 13 trial brands are not on disk (data/ is git-ignored)")
class ReplayedBaseline(unittest.TestCase):
    def test_replay_matches_the_frozen_baseline(self):
        if load_config().versions != BASELINE["versions"]:
            self.skipTest("legacy config versions changed; regenerate the baseline deliberately")
        now = legacy_baseline.build()
        self.assertEqual(now["unique_per_stage"], BASELINE["unique_per_stage"])
        for name, frozen in BASELINE["brands"].items():
            self.assertEqual(now["brands"][name], frozen, name)


if __name__ == "__main__":
    unittest.main()

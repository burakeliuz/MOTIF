"""The inactive draft registry must keep the rev 0.2 baseline intact."""

try:
    from . import _netguard  # noqa: F401
except ImportError:  # started as a top-level module (discover -s tests)
    import _netguard  # noqa: F401
import unittest

from motif_spike.util import CONFIG_DIR, read_json


class DraftRegistryBaseline(unittest.TestCase):
    def setUp(self):
        self.registry = read_json(CONFIG_DIR / "draft_rules.json")

    def test_registry_is_inactive(self):
        self.assertEqual(self.registry["status"], "inactive_draft")
        self.assertIsNone(self.registry["unknown_axis_value"])

    def test_six_axes_with_fixed_names_and_pole_order(self):
        axes = [(a["key"], a["first_pole"], a["second_pole"]) for a in self.registry["axes"]]
        self.assertEqual(axes, [
            ("warm_cool", "warm", "cool"),
            ("light_dense", "light", "dense"),
            ("raw_polished", "raw", "polished"),
            ("natural_synthetic", "natural", "synthetic"),
            ("intimate_projecting", "intimate", "projecting"),
            ("sweet_dry", "sweet", "dry"),
        ])

    def test_twelve_candidate_motifs(self):
        ids = {m["id"] for m in self.registry["motifs"]}
        self.assertEqual(ids, {"restrained", "experimental", "intimate", "industrial", "romantic", "heritage",
                               "playful", "provocative", "natural", "precise", "opulent", "melancholic"})

    def test_exactly_five_draft_rules(self):
        rules = {(r["rule_id"], r["motif"], r["axis"], r["toward"]) for r in self.registry["rules"]}
        self.assertEqual(rules, {
            ("R1", "restrained", "light_dense", "light"),
            ("R2", "intimate", "intimate_projecting", "intimate"),
            ("R3", "precise", "raw_polished", "polished"),
            ("R4", "opulent", "light_dense", "dense"),
            ("R5", "natural", "natural_synthetic", "natural"),
        })

    def test_restrained_never_maps_to_projection(self):
        for rule in self.registry["rules"]:
            if rule["motif"] == "restrained":
                self.assertNotEqual(rule["axis"], "intimate_projecting")
        removed = self.registry["removed_rules"]
        self.assertTrue(any(r["from_motif"] == "restrained" and r["axis"] == "intimate_projecting" for r in removed))

    def test_seven_motifs_stay_unmapped(self):
        mapped = {r["motif"] for r in self.registry["rules"]}
        unmapped = set(self.registry["unmapped_motifs"])
        self.assertEqual(len(unmapped), 7)
        self.assertFalse(mapped & unmapped)
        self.assertEqual(mapped | unmapped, {m["id"] for m in self.registry["motifs"]})

    def test_material_palette_not_invented(self):
        self.assertEqual(self.registry["materials"]["status"], "not_defined")

    def test_worked_example_is_documented_not_executed(self):
        example = self.registry["worked_example"]
        self.assertEqual(example["status"], "documented_expectations_only")
        self.assertTrue(all(f["synthetic"] for f in example["fixtures"]))
        self.assertEqual(example["expected"]["domain_support"], {"restrained": 3, "precise": 2, "intimate": 1})
        self.assertNotIn("intimate_projecting", example["expected"]["qualitative_targets"])


if __name__ == "__main__":
    unittest.main()

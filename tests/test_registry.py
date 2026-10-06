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


class Stage3DesignConfigs(unittest.TestCase):
    """The stage-3 lexicon and palette must stay inside the rev 0.2 baseline."""

    def setUp(self):
        self.registry = read_json(CONFIG_DIR / "draft_rules.json")
        self.lexicon = read_json(CONFIG_DIR / "motif_lexicon.json")
        self.palette = read_json(CONFIG_DIR / "material_palette.json")
        self.axes = {a["key"]: (a["first_pole"], a["second_pole"]) for a in self.registry["axes"]}

    def test_lexicon_uses_only_the_twelve_motifs(self):
        self.assertEqual(set(self.lexicon["cue_groups"]), {m["id"] for m in self.registry["motifs"]})

    def test_palette_profiles_use_baseline_axes_and_poles(self):
        for material in self.palette["materials"]:
            for axis, pole in material["motif_profile"].items():
                with self.subTest(material=material["material_id"], axis=axis):
                    self.assertIn(pole, self.axes[axis])
                    self.assertIn(axis, material["basis_terms"])

    def test_palette_entries_keep_source_apart_from_mapping(self):
        for material in self.palette["materials"]:
            with self.subTest(material=material["material_id"]):
                self.assertTrue(material["source"]["urls"])
                self.assertIn(material["source"]["status"], self.palette["verification"]["status_values"])
                self.assertNotIn("motif_profile", material["source"])

    def test_palette_01_has_no_sourced_intimate_material(self):
        # MOTIF_BUILD_SPEC.md 9.1: no supplier excerpt supported skin-close use in palette-0.1.
        if self.palette["palette_version"] not in ("palette-0.1", "palette-0.2", "palette-0.3"):
            self.skipTest("later palettes may add a sourced intimate material")
        self.assertFalse(any(m["motif_profile"].get("intimate_projecting") == "intimate"
                             for m in self.palette["materials"]))


if __name__ == "__main__":
    unittest.main()

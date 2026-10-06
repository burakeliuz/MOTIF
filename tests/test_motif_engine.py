"""Engine behaviour on SYNTHETIC evidence (invented tags, never Qloo data)."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled, verified_palette
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled, verified_palette
import json
import unittest

from motif.classify import Lexicon
from motif.engine import run_engine

LEX = Lexicon(CONFIG.lexicon)


def dumps(result):
    return json.dumps(result, sort_keys=True)


# Restraint anchored in own + brand + movie; precision in own + brand; nature in own + brand.
THREE_AXES = [
    ev("own", "SYN-SEED", "Unpretentious", TONE), ev("own", "SYN-SEED", "Clean Lines", AESTHETIC),
    ev("own", "SYN-SEED", "Natural Materials", AESTHETIC),
    ev("brand", "SYN-B1", "Understated", AESTHETIC), ev("brand", "SYN-B1", "Clean Lines", AESTHETIC),
    ev("brand", "SYN-B2", "Earthy Tones", AESTHETIC),
    ev("movie", "SYN-M1", "Muted", STYLE),
]


class Matching(unittest.TestCase):
    def test_word_boundaries(self):
        self.assertEqual(LEX.match("Lushness")["matches"], [])
        self.assertEqual(LEX.match("Overstructured")["matches"], [])
        self.assertEqual(LEX.match("Lush")["matches"], [("opulent", "lush", False)])

    def test_variants_of_one_cue_group_are_one_descriptor(self):
        self.assertEqual(LEX.match("Minimalism")["matches"], LEX.match("Minimalist")["matches"])

    def test_negation_is_not_support(self):
        self.assertEqual(LEX.match("Not Minimalist")["matches"], [("restrained", "minimalist", True)])
        self.assertEqual(LEX.match("Never Understated")["matches"], [("restrained", "understated", True)])
        # a prefix inside a word is not a negation
        self.assertEqual(LEX.match("Unpretentious")["matches"], [("restrained", "unpretentious", False)])

    def test_technique_phrases_in_media_tags_do_not_count(self):
        evidence = [ev("own", "S", "Muted", AESTHETIC), ev("movie", "M1", "Sparse interviewing", STYLE),
                    ev("movie", "M2", "Precision editing", STYLE), ev("movie", "M3", "Restrained long takes", STYLE)]
        result = run_engine(evidence, CONFIG)
        info = result["motifs"]["restrained"]
        self.assertEqual(info["source_kinds"], ["own"])  # none of the technique phrases supports
        reasons = " ".join(x["reason"] for x in info["excluded_evidence"])
        self.assertIn("interviewing", reasons)
        self.assertIn("takes", reasons)
        # the same word on a brand's aesthetic tag is not a film technique
        self.assertEqual(LEX.context_exclusion("Sparse Interiors", "brand", "sparse"), "")

    def test_ambiguous_lush_needs_a_design_context(self):
        self.assertIn("ambiguous", LEX.context_exclusion("Lush", "movie", "lush"))
        self.assertIn("ambiguous", LEX.context_exclusion("Lush", "brand", "lush"))
        self.assertEqual(LEX.context_exclusion("Lush costume design", "movie", "lush"), "")
        self.assertEqual(LEX.context_exclusion("Opulent production design", "movie", "opulent"), "")

    def test_genre_names_bare_poles_and_null_are_not_forced(self):
        self.assertEqual(LEX.match("Baroque Pop")["status"], "excluded_pattern")
        self.assertEqual(LEX.match("Raw")["status"], "bare_pole_word")
        self.assertEqual(LEX.match("null")["status"], "ignored_name")
        self.assertEqual(LEX.match("Typewriter Font")["status"], "no_cue")


class Support(unittest.TestCase):
    def test_order_and_duplicates_do_not_change_the_result(self):
        base = run_engine(THREE_AXES, CONFIG)
        noisy = shuffled(THREE_AXES + THREE_AXES[:3] + [dict(THREE_AXES[3])])
        self.assertEqual(dumps(run_engine(noisy, CONFIG)), dumps(base))

    def test_repeats_inside_one_source_kind_add_no_support(self):
        many = [ev("brand", f"SYN-B{i}", "Clean Lines", AESTHETIC) for i in range(8)]
        result = run_engine([ev("own", "SYN-SEED", "Clean Lines", AESTHETIC)] + many, CONFIG)
        self.assertEqual(result["motifs"]["precise"]["source_kinds"], ["own", "brand"])
        self.assertEqual(result["motifs"]["precise"]["strength"], "moderate")

    def test_own_route_counts_cue_groups_not_repeated_words(self):
        same_word = run_engine([ev("own", "S", "Classic", TONE), ev("own", "S", "Classic Tailoring", AESTHETIC)], CONFIG)
        self.assertEqual(same_word["motifs"]["heritage"]["strength"], "weak")
        two_words = run_engine([ev("own", "S", "Provocative", TONE), ev("own", "S", "Edgy", TONE)], CONFIG)
        self.assertEqual(two_words["motifs"]["provocative"]["strength"], "moderate")

    def test_media_alone_cannot_create_a_motif(self):
        result = run_engine([ev("movie", "SYN-M1", "Muted", STYLE), ev("movie", "SYN-M2", "Understated", STYLE),
                             ev("artist", "SYN-A1", "Reserved", STYLE)], CONFIG)
        self.assertEqual(result["motifs"]["restrained"]["strength"], "weak")
        self.assertEqual(result["outcome"], "insufficient_evidence")

    def test_common_cues_are_context_only(self):
        result = run_engine([ev("own", "S", "Minimalist", AESTHETIC), ev("brand", "B", "Minimalist Design", AESTHETIC)], CONFIG)
        self.assertEqual(result["motifs"]["restrained"]["strength"], "context_only")


class AxesAndOutcomes(unittest.TestCase):
    def test_unknown_axes_stay_null_and_restrained_never_sets_projection(self):
        result = run_engine(THREE_AXES, CONFIG)
        targets = {a: v["value"] for a, v in result["axes"].items() if v["state"] == "target"}
        self.assertEqual(targets, {"light_dense": "light", "raw_polished": "polished", "natural_synthetic": "natural"})
        for axis in ("warm_cool", "intimate_projecting", "sweet_dry"):
            self.assertEqual(result["axes"][axis], {"state": "unknown", "value": None})

    def test_conflict_leaves_the_axis_null_until_the_user_chooses(self):
        evidence = THREE_AXES + [ev("brand", "SYN-B3", "Baroque Prints", AESTHETIC), ev("movie", "SYN-M2", "Opulent", STYLE)]
        result = run_engine(evidence, CONFIG, allow_unverified=True)
        self.assertEqual(result["outcome"], "conflicted")
        self.assertEqual(result["axes"]["light_dense"]["state"], "conflicted")
        self.assertIsNone(result["axes"]["light_dense"]["value"])
        for m in result["materials"]["ranked"] + result["materials"].get("selected", []):
            self.assertNotIn("light_dense", m["matches"])
        chosen = run_engine(evidence, CONFIG, allow_unverified=True, overrides={"light_dense": "dense"})
        self.assertEqual(chosen["axes"]["light_dense"]["value"], "dense")
        self.assertEqual(chosen["axes"]["light_dense"]["user_choice"]["provenance_category"], "manual")
        left_open = run_engine(evidence, CONFIG, overrides={"light_dense": "open"})
        self.assertIsNone(left_open["axes"]["light_dense"]["value"])

    def test_missing_data_vs_missing_rule_vs_weak_evidence(self):
        self.assertEqual(run_engine([], CONFIG)["outcome"], "no_descriptive_data")
        unmapped = run_engine([ev("own", "S", "Provocative", TONE), ev("brand", "B", "Subversive", TONE)], CONFIG)
        self.assertEqual(unmapped["outcome"], "no_translation_rule")
        self.assertEqual(unmapped["unmapped_active_motifs"], ["provocative"])
        weak = run_engine([ev("own", "S", "Muted", AESTHETIC)], CONFIG)
        self.assertEqual(weak["outcome"], "insufficient_evidence")

    def test_single_axis_is_gated_even_in_the_design_preview(self):
        result = run_engine([ev("own", "S", "Clean Lines", AESTHETIC), ev("brand", "B", "Structured", AESTHETIC)],
                            CONFIG, allow_unverified=True)
        self.assertEqual(result["outcome"], "partial_direction")
        self.assertEqual(result["materials"]["selected"], [])
        self.assertTrue(result["materials"]["ranked"])  # candidates are shown, not composed


class Materials(unittest.TestCase):
    def test_unverified_properties_are_not_used_by_default(self):
        nothing_verified = verified_palette(CONFIG, set())
        result = run_engine(THREE_AXES, nothing_verified)
        self.assertEqual(result["outcome"], "no_verified_materials")
        self.assertEqual(result["materials"]["verification_mode"], "verified_only")
        preview = run_engine(THREE_AXES, nothing_verified, allow_unverified=True)
        self.assertEqual(preview["materials"]["verification_mode"], "design_preview_unverified")

    def test_the_live_palette_never_uses_the_unverified_iso_e_super(self):
        result = run_engine(THREE_AXES, CONFIG)
        ids = [m["material_id"] for m in result["materials"]["selected"] + result["materials"]["ranked"]]
        self.assertNotIn("M03", ids)
        self.assertIn("M03", [m["material_id"] for m in result["materials"]["excluded"]])

    def test_only_verified_properties_count(self):
        # verify Hedione's light property only: its unverified 'polished' must neither score nor appear
        config = verified_palette(CONFIG, {("M01", "light_dense"), ("M02", "*")})
        result = run_engine(THREE_AXES, config)
        hedione = next(m for m in result["materials"]["ranked"] if m["material_id"] == "M01")
        self.assertEqual(hedione["usable_profile"], {"light_dense": "light"})
        self.assertEqual(hedione["unverified_properties"], ["intimate_projecting", "raw_polished"])
        self.assertEqual(hedione["matches"], ["light_dense"])

    def test_a_partial_match_cannot_outscore_a_full_match(self):
        result = run_engine(THREE_AXES, CONFIG)
        scores = {m["material_id"]: m["score"] for m in result["materials"]["ranked"]}
        self.assertGreater(scores["M01"], scores["M05"])  # light+polished beats polished only
        self.assertGreater(scores["M02"], scores["M08"])  # light+natural beats natural only
        # M05 and M08 tie at 0.2 here; the tie goes to the one adding fewer unrequested properties (M08)
        self.assertEqual([s["material_id"] for s in result["materials"]["selected"]], ["M02", "M01", "M08"])

    def test_extra_character_is_labelled_a_creative_choice(self):
        evidence = [ev("own", "S", "Baroque Prints", AESTHETIC), ev("brand", "B", "Ornate", AESTHETIC),
                    ev("own", "S", "Tailored", AESTHETIC), ev("brand", "B", "Structured", AESTHETIC)]
        result = run_engine(evidence, CONFIG, allow_unverified=True)
        picked = {m["material_id"]: m for m in result["materials"]["selected"]}
        self.assertIn("M04", picked)
        self.assertEqual(picked["M04"]["unrequested_properties"],
                         [{"axis": "intimate_projecting", "pole": "projecting", "label": "creative choice, not evidence"}])
        self.assertNotIn("dosage", json.dumps(result).lower())


if __name__ == "__main__":
    unittest.main()

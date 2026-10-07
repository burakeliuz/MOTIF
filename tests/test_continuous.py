"""The continuous sensory engine on SYNTHETIC evidence (invented tags, never Qloo data).

Logic tests use a small test-only sensory model so that each property is checked in isolation;
the shipped model is checked for consistency and loaded through the normal config path.
"""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled
import json
import unittest

from motif.config import AXES, load_continuous_config
from motif.continuous import commitment, run_continuous

CC = load_continuous_config()


def cell(value, confidence="medium"):
    return {"value": value, "confidence": confidence, "evidence_type": "motif_design_inference"}


def model(cells):
    """cells: {motif: {axis: value}}; every other cell is null."""
    return {"model_version": "test-model", "motifs": {m: {"cells": {a: (cell(v) if v is not None else None) for a, v in axes.items()}}
                                                       for m, axes in cells.items()}}


def run(evidence, vectors=None):
    return run_continuous(evidence, CC.lexicon, CC.scoring, vectors or CC.vectors, CC.params)


OWN_EDGY = [ev("own", "S", "Edgy", AESTHETIC), ev("own", "S", "Rebellious", AESTHETIC), ev("brand", "B1", "Subversive", AESTHETIC)]
OWN_LUSH = [ev("own", "S", "Lush", AESTHETIC), ev("own", "S", "Opulent", AESTHETIC), ev("brand", "B2", "Sumptuous", AESTHETIC)]


class Aggregation(unittest.TestCase):
    def test_null_cells_contribute_nothing(self):
        r = run(OWN_EDGY, model({"provocative": {"sweet_dry": 0.5}}))
        self.assertEqual(r["axes"]["sweet_dry"]["state"], "resolved")
        self.assertEqual(r["axes"]["sweet_dry"]["pole"], "dry")
        for a in AXES:
            if a != "sweet_dry":
                self.assertEqual(r["axes"][a]["state"], "open")
                self.assertEqual(r["axes"][a]["contributors"], [])
                self.assertIsNone(r["axes"][a]["value"])

    def test_opposite_pulls_stay_open_instead_of_a_confident_middle(self):
        r = run(OWN_EDGY + OWN_LUSH, model({"provocative": {"sweet_dry": 0.5}, "opulent": {"sweet_dry": -0.5}}))
        ax = r["axes"]["sweet_dry"]
        self.assertEqual(ax["state"], "balanced_open")
        self.assertIsNone(ax["value"])
        self.assertLess(ax["agreement"], CC.params["aggregation"]["min_agreement"])
        self.assertEqual(sorted(ax["pulls"]["sweet"] + ax["pulls"]["dry"]), ["opulent", "provocative"])

    def test_low_confidence_cells_alone_read_tentative(self):
        low = {"model_version": "test-model", "motifs": {"provocative": {"cells": {"raw_polished": cell(-0.25, "low")}}}}
        ax = run(OWN_EDGY, low)["axes"]["raw_polished"]
        self.assertEqual(ax["state"], "resolved")
        self.assertEqual(ax["confidence_word"], "tentative")
        self.assertEqual(ax["evidence_basis"], "design_inference_only")
        self.assertEqual(ax["label"], "slightly raw")

    def test_common_cue_motifs_are_context_not_pulls(self):
        r = run([ev("brand", f"B{i}", "Minimalist", AESTHETIC) for i in range(8)] + OWN_EDGY,
                model({"restrained": {"light_dense": -0.5}, "provocative": {"sweet_dry": 0.5}}))
        ax = r["axes"]["light_dense"]
        self.assertEqual(ax["contributors"], [])
        self.assertEqual([c["motif"] for c in ax["common_cue_context"]], ["restrained"])
        self.assertEqual(ax["state"], "open")

    def test_value_is_the_weighted_mean_of_cell_values(self):
        r = run(OWN_EDGY, model({"provocative": {"light_dense": 0.5}}))
        self.assertAlmostEqual(r["axes"]["light_dense"]["value"], 0.5, places=6)
        self.assertEqual(r["axes"]["light_dense"]["label"], "dense")

    def test_weak_evidence_alone_leaves_an_axis_open(self):
        weak_low = {"model_version": "test-model", "motifs": {"provocative": {"cells": {"sweet_dry": cell(0.25, "low")}}}}
        r = run([ev("movie", "M1", "Edgy", STYLE)], weak_low)
        self.assertEqual(r["axes"]["sweet_dry"]["state"], "open")
        self.assertEqual(r["outcome"], "insufficient_evidence")

    def test_trace_runs_from_evidence_to_dimension(self):
        r = run(OWN_EDGY)
        ev_ids = {e["evidence_id"] for e in r["evidence"]}
        for a in AXES:
            for c in r["axes"][a]["contributors"]:
                s = r["motif_scores"][c["motif"]]
                self.assertEqual(c["score"], s["score"])
                cited = [x for x in r["annotations"] if x["motif"] == c["motif"] and x["role"] in ("support", "context_common_cue")]
                self.assertTrue(cited and all(x["evidence_id"] in ev_ids for x in cited))
                self.assertAlmostEqual(c["contribution"], round(c["weight"] * c["cell_value"], 6), places=5)


class Determinism(unittest.TestCase):
    def test_order_and_duplicates_do_not_change_the_result(self):
        evidence = OWN_EDGY + OWN_LUSH + [ev("movie", "M1", "Muted", STYLE)]
        a = json.dumps(run(evidence), sort_keys=True)
        self.assertEqual(a, json.dumps(run(shuffled(evidence + evidence[:3])), sort_keys=True))
        self.assertEqual(a, json.dumps(run(evidence), sort_keys=True))

    def test_no_evidence_is_no_data(self):
        r = run([])
        self.assertEqual(r["outcome"], "no_descriptive_data")
        self.assertEqual(commitment(r["axes"]), [0.0] * 6)


class ShippedModel(unittest.TestCase):
    def test_cells_match_direction_and_strength(self):
        sv = CC.vectors["strength_values"]
        poles = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
                 "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"), "sweet_dry": ("sweet", "dry")}
        for m, spec in CC.vectors["motifs"].items():
            for a in AXES:
                c = spec["cells"][a]
                if c is None:
                    continue
                sign = -1 if c["direction"] == poles[a][0] else 1
                self.assertEqual(c["value"], sign * sv[c["strength"]], f"{m}.{a}")
                self.assertIn(c["confidence"], CC.params["confidence_weights"])

    def test_restraint_never_sets_projection(self):
        self.assertIsNone(CC.vectors["motifs"]["restrained"]["cells"]["intimate_projecting"])

    def test_every_lexicon_motif_has_an_entry(self):
        self.assertEqual(set(CC.vectors["motifs"]), set(CONFIG.lexicon["cue_groups"]))


if __name__ == "__main__":
    unittest.main()

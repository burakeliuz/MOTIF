"""Scent architecture: the olfactory library's rules and the deterministic matching (offline)."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, CONFIG, evidence_item as ev
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, CONFIG, evidence_item as ev
import csv
import json
import re
import sys
import unittest
from pathlib import Path

from motif.config import AXES, load_continuous_config
from motif.continuous import run_continuous
from motif.olfactory import architecture

ROOT = Path(__file__).resolve().parent.parent
CC = load_continuous_config()
LIB = CC.library
EVIDENCE = json.loads((ROOT / "config" / "candidates" / "odor_axis_evidence.v1.json").read_text(encoding="utf-8"))
PALETTE_URLS = {(v or {}).get("source_url") for m in CONFIG.palette["materials"]
                for v in m.get("property_verification", {}).values() if (v or {}).get("status") == "verified_full_page"}
POLES = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
         "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"), "sweet_dry": ("sweet", "dry")}
IFRA = ROOT / "data" / "external" / "pyrfume"


def axes(**resolved):
    """Synthetic resolved axes: name=(value, confidence, word); every other axis open."""
    out = {}
    for a in AXES:
        if a in resolved:
            v, c, w = resolved[a]
            out[a] = {"state": "resolved", "value": v, "confidence": c, "confidence_word": w, "label": "x", "evidence_basis": "mixed"}
        else:
            out[a] = {"state": "open", "value": None, "confidence": 0.0}
    return out


class Library(unittest.TestCase):
    def test_shape_and_values(self):
        ids = [d["id"] for d in LIB["directions"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(18 <= len(ids) <= 24)
        for d in LIB["directions"]:
            self.assertTrue(set(d["roles"]) <= {"opening", "core", "drydown"} and d["roles"], d["id"])
            self.assertEqual(set(d["vector"]), set(AXES), d["id"])
            for a, c in d["vector"].items():
                if c is None:
                    continue
                self.assertIn(abs(c["value"]), (0.25, 0.5), f"{d['id']}.{a}")
                self.assertTrue(c["basis"].startswith(("odor_data:", "design:")), f"{d['id']}.{a}")
            for word in d["descriptors"] + [d["label"]]:
                self.assertFalse(re.search(r"\d|%", word), f"{d['id']}: {word}")

    def test_odor_data_cells_follow_the_evidence(self):
        summary = EVIDENCE["summary"]
        for d in LIB["directions"]:
            for a, c in d["vector"].items():
                if not c or not c["basis"].startswith("odor_data"):
                    continue
                pole = POLES[a][0] if c["value"] < 0 else POLES[a][1]
                classes = [summary.get(f"{a}:{pole}", {}).get(f, {}).get("class", "none") for f in d["odor_families"]]
                self.assertTrue(any(k != "none" for k in classes), f"{d['id']}.{a} has no supporting family")
                if "x2" in c["basis"]:
                    self.assertIn("replicated", classes, f"{d['id']}.{a}")
                self.assertNotEqual(pole, "dry", f"{d['id']}: no dataset supports dry")

    def test_trade_names_only_from_pages_read(self):
        for d in LIB["directions"]:
            for m in d["materials"]:
                if "example" in m:
                    self.assertIn("PALETTE", m["source"], d["id"])
                    self.assertIn(m["url"], PALETTE_URLS, d["id"])
                for value in m.values():
                    self.assertFalse(re.search(r"\d+\s*%|\bppm\b|\bdose", str(value), re.I), d["id"])

    @unittest.skipUnless((IFRA / "ifra_2019__behavior.csv").exists(), "IFRA glossary data not on disk (data/ is git-ignored)")
    def test_generic_names_and_descriptors_are_in_the_ifra_glossary(self):
        beh = list(csv.DictReader((IFRA / "ifra_2019__behavior.csv").open(encoding="utf-8")))
        mol = {r["CID"]: r["name"] for r in csv.DictReader((IFRA / "ifra_2019__molecules.csv").open(encoding="utf-8"))}
        stim = {r["Stimulus"]: r["CID"] for r in csv.DictReader((IFRA / "ifra_2019__stimuli.csv").open(encoding="utf-8"))}
        rows = [(mol.get(stim.get(b["Stimulus"], ""), ""), [b["Descriptor 1"], b["Descriptor 2"], b["Descriptor 3"]]) for b in beh]
        for d in LIB["directions"]:
            for m in d["materials"]:
                if "IFRA19" in m["source"]:
                    self.assertTrue(any(m["generic"] in name and descs == m["ifra"] for name, descs in rows), f"{d['id']}: {m['generic']}")


class Matching(unittest.TestCase):
    def test_nothing_resolved_means_an_open_architecture(self):
        a = architecture(axes(), {}, CC.vectors, LIB, 0.3)
        self.assertEqual(a["status"], "open")
        self.assertEqual(set(a["structure"].values()), {None})
        self.assertEqual((a["emphasize"], a["avoid"]), ([], []))

    def test_conflicting_directions_are_set_aside_and_roles_respected(self):
        a = architecture(axes(light_dense=(-0.5, 0.8, "supported"), sweet_dry=(0.25, 0.3, "tentative")), {}, CC.vectors, LIB, 0.3)
        picked = [s["direction"] for s in a["structure"].values() if s]
        self.assertEqual(len(picked), len(set(picked)))
        by_id = {d["id"]: d for d in LIB["directions"]}
        for role, s in a["structure"].items():
            if s:
                self.assertIn(role, by_id[s["direction"]]["roles"])
        for s in a["structure"].values():
            if s:
                self.assertLessEqual(_cell(by_id[s["direction"]], "light_dense"), 0.0, s["direction"])
        self.assertIn("amber_resinous", [x["direction"] for x in a["avoid"]])

    def test_emphasize_and_avoid_need_a_supported_dimension(self):
        a = architecture(axes(light_dense=(-0.5, 0.3, "tentative"), warm_cool=(0.25, 0.3, "tentative")), {}, CC.vectors, LIB, 0.3)
        self.assertEqual((a["emphasize"], a["avoid"]), ([], []))
        self.assertEqual(a["basis"], "tentative")

    def test_engine_result_carries_a_deterministic_architecture(self):
        evidence = [ev("own", "S", n, AESTHETIC) for n in ("Muted", "Understated", "Natural Materials", "Earthy")]
        r1 = run_continuous(evidence, CC.lexicon, CC.scoring, CC.vectors, CC.params, library=LIB)
        r2 = run_continuous(list(reversed(evidence)), CC.lexicon, CC.scoring, CC.vectors, CC.params, library=LIB)
        self.assertEqual(json.dumps(r1["architecture"], sort_keys=True), json.dumps(r2["architecture"], sort_keys=True))
        self.assertEqual(r1["versions"]["olfactory"], LIB["library_version"])


def _cell(d, a):
    c = d["vector"].get(a)
    return c["value"] if c else 0.0


sys.path.insert(0, str(ROOT / "tools"))
import legacy_baseline  # noqa: E402


@unittest.skipUnless(legacy_baseline.available(), "recordings of the 13 trial brands are not on disk")
class TrialBrands(unittest.TestCase):
    def test_architectures_differ_far_more_than_the_legacy_materials(self):
        import engine_compare
        sigs = set()
        for lr in engine_compare.legacy_results().values():
            r = run_continuous(lr["evidence"], CC.lexicon, CC.scoring, CC.vectors, CC.params, library=LIB)
            sigs.add(tuple((s or {}).get("direction") for s in r["architecture"]["structure"].values()))
        self.assertGreaterEqual(len(sigs), 9)  # legacy: 3 distinct material sets


if __name__ == "__main__":
    unittest.main()

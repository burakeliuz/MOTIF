"""Engine checks on RECORDED live Qloo data (local only; no network).

The stage-2 run and the T1 sessions live in git-ignored data/. Where they are
absent (a fresh clone, CI), these tests skip with the reason. They replay
stored bodies through RecordedQloo, which never sends a request.
"""

try:
    from . import _netguard  # noqa: F401
except ImportError:
    import _netguard  # noqa: F401
import json
import unittest
from pathlib import Path

from motif.agent import Controller
from motif.config import load_config
from motif.qloo import RecordedQloo
from motif_spike.util import resolve_pointer

DATA = Path(__file__).resolve().parent.parent / "data"
STAGE2 = DATA / "raw" / "live-20261006T103307Z-660d"
CONFIG = load_config()
LE_LABO_BRAND = "25C88914-2BC2-4E6B-A787-A8DD2DD4F45E"


def session_for(name, needs_choice=False):
    root = DATA / "motif_sessions"
    if not root.exists():
        return None
    for d in sorted(root.glob("live-*")):
        meta = json.loads((d / "session.json").read_text(encoding="utf-8")) if (d / "session.json").exists() else {}
        if meta.get("reference", {}).get("input") == name and meta.get("status") == "completed":
            return d
    return None


def run(recording, name, **kw):
    access = RecordedQloo(recording, None, 99)
    out = Controller(access, CONFIG, name, **kw).run()
    return out, access


def targets(result):
    return {a: v["value"] for a, v in result["axes"].items() if v["state"] == "target"}


@unittest.skipUnless(STAGE2.exists(), "recorded stage-2 live run not present (data/ is git-ignored)")
class ReferenceBrands(unittest.TestCase):
    def test_muji_chain_matches_the_design_example_and_is_traceable(self):
        out, access = run(STAGE2, "MUJI", allow_unverified=True)
        result = out["result"]
        self.assertEqual(targets(result), {"light_dense": "light", "raw_polished": "polished", "natural_synthetic": "natural"})
        self.assertEqual([(m["slot"], m["material_id"]) for m in result["materials"]["selected"]],
                         [("top", "M02"), ("heart", "M01"), ("base", "M03")])
        self.assertEqual(access.network_attempts, 0)
        # every support item resolves to the literal tag in the stored body
        bodies = {r["request_id"]: json.loads(Path(r["response_ref"]).read_text(encoding="utf-8")) for r in access.log}
        for info in result["motifs"].values():
            for eid in info["support_evidence_ids"]:
                item = next(e for e in result["evidence"] if e["evidence_id"] == eid)
                raw = resolve_pointer(bodies[item["request_id"]], item["json_pointer"])
                self.assertEqual(raw["name"], item["tag_name"])

    def test_muji_verified_only_uses_verified_properties_and_flags_extras(self):
        out, _ = run(STAGE2, "MUJI")
        mats = out["result"]["materials"]
        self.assertEqual(mats["verification_mode"], "verified_only")
        self.assertEqual([(m["slot"], m["material_id"]) for m in mats["selected"]], [("top", "M02"), ("heart", "M01"), ("base", "M05")])
        extras = {m["material_id"]: [u["pole"] for u in m["unrequested_properties"]] for m in mats["selected"]}
        self.assertEqual(extras, {"M02": ["sweet"], "M01": ["projecting"], "M05": ["warm"]})

    def test_ralph_lauren_dense_is_flagged_relations_only(self):
        out, _ = run(STAGE2, "Ralph Lauren", allow_unverified=True)
        axes = out["result"]["axes"]
        self.assertEqual(targets(out["result"]), {"light_dense": "dense", "raw_polished": "polished"})
        self.assertTrue(axes["light_dense"]["relations_only"])
        selected = out["result"]["materials"]["selected"]
        self.assertEqual([(m["slot"], m["material_id"]) for m in selected], [("heart", "M03"), ("base", "M04"), ("base", "M05")])
        extras = {m["material_id"]: [u["pole"] for u in m["unrequested_properties"]] for m in selected}
        self.assertEqual(extras, {"M03": [], "M04": ["projecting"], "M05": ["warm"]})

    def test_known_limitations_stay_visible(self):
        self.assertEqual(run(STAGE2, "Comme des Garçons", allow_unverified=True)[0]["result"]["outcome"], "partial_direction")
        a24 = run(STAGE2, "A24")[0]["result"]
        self.assertEqual(a24["outcome"], "no_translation_rule")
        self.assertEqual(a24["unmapped_active_motifs"], ["provocative"])
        nike, _ = run(STAGE2, "Nike")
        self.assertEqual(nike["result"]["outcome"], "insufficient_evidence")
        # heritage has anchored (brand) support below strong, so movies are fetched, not skipped
        self.assertEqual(next(t for t in nike["trace"] if t["action"] == "fetch_related:movie")["decision"], "fetched")


class HeldOutBrands(unittest.TestCase):
    """T1 (reports/holdout_t1.md). Frozen rules; these brands are no longer independent validation."""

    def test_le_labo_needs_a_choice_then_gives_two_relation_only_axes(self):
        rec = session_for("Le Labo")
        if rec is None:
            self.skipTest("recorded T1 session for Le Labo not present")
        asked, _ = run(rec, "Le Labo")
        self.assertEqual(asked["status"], "needs_choice")
        self.assertIn(LE_LABO_BRAND, [o["qloo_id"] for o in asked["question"]["options"]])
        chosen, _ = run(rec, "Le Labo", choose=LE_LABO_BRAND)
        axes = chosen["result"]["axes"]
        self.assertEqual(targets(chosen["result"]), {"light_dense": "light", "raw_polished": "polished"})
        self.assertTrue(axes["light_dense"]["relations_only"] and axes["raw_polished"]["relations_only"])

    def test_patagonia_gives_one_axis_and_no_composition(self):
        rec = session_for("Patagonia")
        if rec is None:
            self.skipTest("recorded T1 session for Patagonia not present")
        out, _ = run(rec, "Patagonia", allow_unverified=True)
        self.assertEqual(out["result"]["outcome"], "partial_direction")
        self.assertEqual(targets(out["result"]), {"natural_synthetic": "natural"})
        # lexicon-0.3: the T1 misreads no longer count as support (post-hoc fix; not independent validation)
        evidence = {e["evidence_id"]: e["tag_name"] for e in out["result"]["evidence"]}
        motifs = out["result"]["motifs"]
        supported = {evidence[i] for m in ("opulent", "restrained") if m in motifs for i in motifs[m]["support_evidence_ids"]}
        self.assertFalse({"Lush", "Sparse interviewing", "Sparse lyrical editing"} & supported)


if __name__ == "__main__":
    unittest.main()

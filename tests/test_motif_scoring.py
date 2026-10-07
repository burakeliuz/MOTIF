"""Weighted motif scores (scoring-1.0) on SYNTHETIC evidence; the 13 trial brands when recordings exist."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, CONFIG, STYLE, TONE, evidence_item as ev, shuffled
import json
import sys
import unittest
from pathlib import Path

from motif.classify import Lexicon, classify
from motif.evidence import normalize_evidence
from motif.scoring import score_motifs

ROOT = Path(__file__).resolve().parent.parent
SCORING = json.loads((ROOT / "config" / "motif_scoring.v1.json").read_text(encoding="utf-8"))
LEX = Lexicon(CONFIG.lexicon)


def scores(evidence, kinds=("own", "brand", "movie")):
    return score_motifs(classify(normalize_evidence(evidence), LEX)["annotations"], SCORING, kinds)


def related(kind, n, tag_name="Edgy", ttype=AESTHETIC, start=0):
    return [ev(kind, f"SYN-{kind[0].upper()}{i}", tag_name, ttype if kind != "movie" else STYLE) for i in range(start, start + n)]


class Bounds(unittest.TestCase):
    def test_scores_are_bounded_and_saturate(self):
        one = scores(related("brand", 1))["provocative"]["score"]
        ten = scores(related("brand", 10))["provocative"]["score"]
        self.assertGreater(one, 0)
        self.assertLess(ten, SCORING["channels"]["brand"]["weight"])  # one channel never reaches its weight
        self.assertLess(ten, 10 * one)
        everything = scores([ev("own", "S", n, AESTHETIC) for n in ("Edgy", "Rebellious", "Subversive", "Provocative")]
                            + related("brand", 10) + related("movie", 10))["provocative"]["score"]
        self.assertLess(everything, 1.0)

    def test_adding_evidence_never_lowers_a_score(self):
        base = related("brand", 2)
        before = scores(base)["provocative"]["score"]
        for extra in (related("brand", 1, start=5), related("movie", 1), [ev("own", "S", "Edgy", AESTHETIC)],
                      [ev("brand", "SYN-B0", "Rebellious", AESTHETIC)]):
            self.assertGreaterEqual(scores(base + extra)["provocative"]["score"], before)

    def test_order_and_duplicates_do_not_matter(self):
        evidence = [ev("own", "S", "Edgy", AESTHETIC)] + related("brand", 3) + related("movie", 2)
        a = scores(evidence)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(scores(shuffled(evidence + evidence[:2])), sort_keys=True))


class Channels(unittest.TestCase):
    def test_own_entry_is_the_anchor(self):
        own = scores([ev("own", "S", "Edgy", AESTHETIC)])["provocative"]
        brand = scores(related("brand", 1))["provocative"]
        self.assertGreater(own["score"], brand["score"])
        self.assertTrue(own["own"])
        self.assertTrue(brand["relations_only"])

    def test_source_diversity_beats_the_same_volume_in_one_channel(self):
        spread = scores(related("brand", 2) + related("movie", 2))["provocative"]["score"]
        stacked = scores(related("brand", 4))["provocative"]["score"]
        self.assertGreater(spread, stacked)

    def test_cue_diversity_adds_credit(self):
        same = scores([ev("brand", "SYN-B1", "Edgy", AESTHETIC), ev("brand", "SYN-B2", "Edgy", AESTHETIC)])["provocative"]
        varied = scores([ev("brand", "SYN-B1", "Edgy", AESTHETIC), ev("brand", "SYN-B2", "Rebellious", AESTHETIC)])["provocative"]
        self.assertGreater(varied["score"], same["score"])
        self.assertEqual(same["channels"]["diversity"]["units"], 0)

    def test_artist_counts_only_when_fetched(self):
        evidence = [ev("artist", "SYN-A1", "Edgy", STYLE)]
        self.assertNotIn("provocative", scores(evidence))
        self.assertIn("provocative", scores(evidence, kinds=("own", "brand", "movie", "artist")))


class CommonAndExcluded(unittest.TestCase):
    def test_common_cues_count_little_and_are_flagged(self):
        common = scores(related("brand", 6, tag_name="Minimalist"))["restrained"]
        real = scores(related("brand", 6, tag_name="Understated"))["restrained"]
        self.assertTrue(common["common_only"])
        self.assertLess(common["score"], real["score"] / 3)

    def test_negated_and_excluded_matches_never_count(self):
        out = scores([ev("own", "S", "Not Edgy", AESTHETIC), ev("movie", "M1", "Precision editing", STYLE)])
        self.assertNotIn("provocative", out)
        self.assertNotIn("precise", out)


sys.path.insert(0, str(ROOT / "tools"))
import legacy_baseline  # noqa: E402


@unittest.skipUnless(legacy_baseline.available(), "recordings of the 13 trial brands are not on disk")
class TrialBrands(unittest.TestCase):
    """The phase 4 checks (docs/MOTIF_SCORING.md section 4) stay true."""

    @classmethod
    def setUpClass(cls):
        cls.s = {}
        for name in ("A24", "Comme des Garçons", "Gucci", "Balenciaga", "MUJI", "Aesop", "Ralph Lauren", "Harley-Davidson", "Sanrio"):
            r = legacy_baseline.replay(name, CONFIG)["result"]
            cls.s[name] = {m: v["score"] for m, v in score_motifs(r["annotations"], SCORING).items()}

    def test_graded_differences_where_the_legacy_labels_were_equal(self):
        self.assertLess(self.s["A24"]["provocative"] + 0.1, self.s["Comme des Garçons"]["provocative"])
        self.assertLess(self.s["Gucci"]["provocative"] + 0.1, self.s["Balenciaga"]["provocative"])

    def test_muji_and_aesop_rank_their_motifs_differently(self):
        top = lambda b: sorted(("restrained", "precise", "natural"), key=lambda m: -self.s[b][m])  # noqa: E731
        self.assertEqual(top("MUJI")[0], "restrained")
        self.assertEqual(top("Aesop")[0], "precise")

    def test_own_heritage_and_playfulness_score(self):
        self.assertGreater(self.s["Ralph Lauren"]["heritage"], 0.5)
        self.assertGreater(self.s["Harley-Davidson"]["heritage"], 0.5)
        self.assertEqual(max(self.s["Harley-Davidson"], key=self.s["Harley-Davidson"].get), "heritage")
        self.assertEqual(max(self.s["Sanrio"], key=self.s["Sanrio"].get), "playful")


if __name__ == "__main__":
    unittest.main()

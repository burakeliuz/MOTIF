"""Plain-language readings of a continuous result (motif/story.py) and its web view (SYNTHETIC evidence)."""

try:
    from . import _netguard  # noqa: F401
    from .motif_fakes import AESTHETIC, STYLE, TONE, evidence_item as ev
except ImportError:
    import _netguard  # noqa: F401
    from motif_fakes import AESTHETIC, STYLE, TONE, evidence_item as ev
import copy
import json
import unittest

from motif import story
from motif.config import load_continuous_config
from motif.continuous import run_continuous
from motif.llm import write_prose
from motif.web.present import continuous_view

CC = load_continuous_config()


def result(evidence):
    return run_continuous(evidence, CC.lexicon, CC.scoring, CC.vectors, CC.params, library=CC.library)


# own entry: restraint and nature; related brands add opulence (a relations-only pull on weight)
OWN_QUIET = [ev("own", "S", n, AESTHETIC) for n in ("Muted", "Understated", "Natural Materials", "Earthy")] + \
            [ev("brand", "B1", "Muted", AESTHETIC), ev("brand", "B2", "Botanical", AESTHETIC)]
RELATED_ONLY = [ev("brand", f"B{i}", n, AESTHETIC) for i, n in enumerate(("Lush", "Opulent", "Sumptuous", "Lavish"))] + \
               [ev("movie", "M1", "Lush", STYLE)]


class FakeWriter:
    def __init__(self, text):
        self.text, self.calls, self.payloads = text, 0, []

    def describe(self):
        return {"provider": "fake", "model": "fake-model"}

    def write(self, payload, feedback=None):
        self.calls += 1
        self.payloads.append(payload)
        return self.text


class Headline(unittest.TestCase):
    def test_own_motifs_lead_the_title(self):
        r = result(OWN_QUIET)
        h = story.headline("Synthquiet", r)
        top = max(r["motif_scores"], key=lambda m: r["motif_scores"][m]["score"])
        self.assertTrue(h["title"].startswith(story.MOTIF_LABELS[top].capitalize()))
        self.assertIn("restraint", h["title"])
        self.assertIn("direction", h["title"])
        self.assertEqual(h["label"], "Scent direction")

    def test_a_direction_from_references_only_never_leads_the_title(self):
        h = story.headline("Synthlux", result(RELATED_ONLY))
        self.assertEqual(h["title"], "A direction drawn from references Qloo relates to Synthlux.")
        self.assertNotIn("dense", h["title"])

    def test_own_motif_without_a_dimension_of_its_own_leads_and_the_references_are_named(self):
        r = result([ev("own", "S", n, AESTHETIC) for n in ("Heritage", "Classic", "Timeless")]
                   + [ev("brand", f"B{i}", n, AESTHETIC) for i, n in enumerate(("Precise", "Meticulous", "Tailored", "Precise"))])
        h = story.headline("Synthold", r)
        self.assertEqual(h["title"], "Heritage, from Synthold's own Qloo entry.")
        self.assertIn("How to express heritage in scent is open to the perfumer.", h["lines"])
        self.assertTrue(any(x.startswith("References Qloo relates to Synthold add") for x in h["lines"]))

    def test_no_signal_says_so(self):
        h = story.headline("Synthnone", result([ev("own", "S", "Typewriter Font", AESTHETIC)]))
        self.assertEqual(h["label"], "No direction yet")


class Prose(unittest.TestCase):
    def test_template_passes_its_own_checks_and_names_every_open_dimension(self):
        r = result(OWN_QUIET)
        text = story.template_prose("Synthquiet", r)
        self.assertEqual(story.validate_prose(text, r, "Synthquiet"), [])
        for a in story.open_dims(r):
            self.assertIn(story.DIM_NAMES[a].lower(), text.lower())
        self.assertNotRegex(text, r"\d|%")

    def test_validation_rejects_ingredients_numbers_and_claims(self):
        r = result(OWN_QUIET)
        opened = " ".join(story.DIM_NAMES[a] for a in story.open_dims(r)) + " are open to the perfumer."
        self.assertTrue(any("ingredient" in p for p in story.validate_prose("Add oud and tonka. " + opened, r)))
        self.assertTrue(any("percentage" in p for p in story.validate_prose("Use 20% of it. " + opened, r)))
        self.assertTrue(any("claim" in p for p in story.validate_prose("Its audience loves calm. " + opened, r)))
        self.assertEqual(story.validate_prose("Synth24 stays quiet. " + opened, r, "Synth24"), [])

    def test_digits_inside_named_materials_are_not_doses(self):
        r = result(OWN_QUIET)  # its drydown names "3-octanol" and "methyl 2,4-dihydroxy-3,6-dimethylbenzoate"
        self.assertIn("3-octanol", story._material_names(r))
        opened = " ".join(story.DIM_NAMES[a] for a in story.open_dims(r)) + " are open to the perfumer."
        text = "The drydown could draw on 3-octanol or methyl 2,4-dihydroxy-3,6-dimethylbenzoate. " + opened
        self.assertEqual(story.validate_prose(text, r), [])
        self.assertEqual(story.validate_prose("3\u2011Octanol could lead it. " + opened, r), [])  # case, typographic hyphen
        bare = copy.deepcopy(r)  # the same words when the architecture does not name these materials
        for s in bare["architecture"]["structure"].values():
            if s:
                s["materials"] = []
        self.assertTrue(any("numbers" in p for p in story.validate_prose(text, bare)))
        for dose in ("Use 2% 3-octanol.", "Add 5 drops of 3-octanol.", "Blend 3-octanol 1:3 with the core.",
                     "Keep 3-octanol at 0.5 parts.", "Try 13-octanol."):
            problems = story.validate_prose(dose + " " + opened, r)
            self.assertTrue(any("numbers" in p or "percentage" in p for p in problems), dose)
        self.assertTrue(any("percentage" in p for p in story.validate_prose("3-octanol at ten percent. " + opened, r)))
        self.assertTrue(any("claim" in p for p in story.validate_prose("3-octanol is proven to please. " + opened, r)))
        self.assertTrue(any("ingredient" in p for p in story.validate_prose("3-octanol and oud. " + opened, r)))

    def test_llm_text_is_used_only_when_it_passes(self):
        r = result(OWN_QUIET)
        opened = " ".join(story.DIM_NAMES[a] for a in story.open_dims(r)) + " stay open to the perfumer."
        good = FakeWriter("A quiet, natural direction. " + opened)
        out = write_prose("Synthquiet", r, good, intent="a scent for a reading room")
        self.assertEqual(out["author"], "llm")
        self.assertEqual(good.payloads[0]["kind"], "continuous")
        self.assertEqual(good.payloads[0]["user_intent"], "a scent for a reading room")
        self.assertEqual(out["llm"]["prompt_version"], "prose-c1.0")
        bad = FakeWriter("Add 3 drops of oud. " + opened)
        out = write_prose("Synthquiet", r, bad)
        self.assertEqual(out["author"], "template")
        self.assertEqual(bad.calls, 2)  # one controlled retry with the problems as feedback


class OpenDimensionsAndStory(unittest.TestCase):
    """Open dimensions are told once, grouped by why; the proposal is read from its documented character; nothing is filled in."""

    def test_each_open_dimension_appears_once_under_its_reason(self):
        r = result(OWN_QUIET)
        states = {a: r["axes"][a]["state"] for a in r["axes"]}
        o = story.open_summary("Synthquiet", r)
        self.assertEqual(o["dims"], [story.DIM_NAMES[a] for a in story.open_dims(r)])
        named = [d for line in o["lines"] for d in line["dims"]]
        self.assertEqual(sorted(named), sorted(o["dims"]))
        self.assertLessEqual({line["kind"] for line in o["lines"]}, {"none", "faint", "both"})
        self.assertEqual({a: r["axes"][a]["state"] for a in r["axes"]}, states)  # reading changes nothing
        self.assertLessEqual(o["counts"]["read"], o["counts"]["returned"])
        self.assertIn(f"reads {o['counts']['read']} of the {o['counts']['returned']} descriptors", o["coverage"])
        # the page shows one short sentence; the reasons and the counts are the method detail
        self.assertEqual(o["line"], "Open to the perfumer: " + story._join([d.lower() for d in o["dims"]]) + ".")
        self.assertNotRegex(o["line"], r"\d")

    def test_a_faint_lean_is_named_but_stays_open(self):
        r = result([ev("brand", "B1", "Clean Lines", AESTHETIC)])
        self.assertEqual(r["axes"]["warm_cool"]["state"], "open")
        o = story.open_summary("Synthfaint", r)
        self.assertIn("Too weak to decide, faint leans only: temperature cool (precision).", [x["text"] for x in o["lines"]])

    def test_the_accords_never_silently_contradict_a_faint_lean(self):
        r = result([ev("brand", "B1", "Clean Lines", AESTHETIC)])  # a faint cool lean on temperature
        vectors = {d["id"]: d["vector"] for d in CC.library["directions"]}
        cells = [vectors[s["direction"]]["warm_cool"]["value"] for s in r["architecture"]["structure"].values()
                 if s and vectors[s["direction"]].get("warm_cool")]
        character = story.accord_character(r, CC.library) or ""
        if cells and all(v < 0 for v in cells):  # the chosen accords lean warm: the text must say it goes against the lean
            self.assertIn("warm (against the faint cool lean)", character)
        else:
            self.assertNotIn("against the faint", character.split("warm")[0] if "warm" in character else "")

    def test_a_contested_dimension_names_both_sides(self):
        r = result([ev("own", "S", n, AESTHETIC) for n in ("Muted", "Understated", "Opulent", "Lavish")])
        self.assertEqual(r["axes"]["light_dense"]["state"], "balanced_open")
        both = next(x["text"] for x in story.open_summary("Synthboth", r)["lines"] if x["kind"] == "both")
        self.assertIn("weight: light (restraint) vs dense (opulence)", both)

    def test_the_story_and_the_accords_character_come_from_the_proposal(self):
        r = result(OWN_QUIET)
        arch = r["architecture"]
        text = story.scent_story(r)
        for s in arch["structure"].values():
            if s:
                self.assertIn(s["label"].lower().replace(", ", " and "), text.lower())
        character = story.accord_character(r, CC.library) or ""
        resolved_words = {story.POLE_WORDS[r["axes"][a]["pole"]] for a in r["axes"] if r["axes"][a]["state"] == "resolved"}
        vectors = {d["id"]: d["vector"] for d in CC.library["directions"]}
        for a in story.open_dims(r):
            cells = [vectors[s["direction"]][a]["value"] for s in arch["structure"].values() if s and vectors[s["direction"]].get(a)]
            if cells and len({v > 0 for v in cells}) == 1:
                self.assertIn(story.POLE_WORDS[story.POLES[a][1 if cells[0] > 0 else 0]], character)
        self.assertNotRegex(character, r"\d|%")
        self.assertIsNone(story.accord_character(result([ev("own", "S", "Typewriter Font", AESTHETIC)]), CC.library))
        self.assertTrue(resolved_words)

    def test_a_common_word_that_counts_lightly_is_disclosed(self):
        r = result([ev("own", "S", "Minimalist", AESTHETIC), ev("movie", "M1", "Understated", STYLE)])
        row = next(p for p in continuous_view("Synthcommon", r, CC.library)["profile"] + continuous_view("Synthcommon", r, CC.library)["minor"]
                   if p["motif"] == "restrained")
        self.assertEqual(row["basis"]["kind"], "related_only")
        self.assertIn("“minimalist”", row["common"])
        self.assertIn("Synthcommon's own entry", row["common"])


class View(unittest.TestCase):
    def test_weak_signals_are_listed_when_nothing_leads(self):
        v = continuous_view("Synthweak", result([ev("brand", "B1", "Muted", AESTHETIC)]), CC.library)
        self.assertEqual(v["profile"], [])
        self.assertEqual([m["motif"] for m in v["minor"]], ["restrained"])
        self.assertEqual(v["headline"]["title"], "Weak signals only: no motif leads yet.")
        self.assertIn("weaker signals", v["headline"]["lines"][0])

    def test_open_dimensions_are_not_drawn_and_sources_are_honest(self):
        v = continuous_view("Synthquiet", result(OWN_QUIET), CC.library)
        opened = [d["name"] for d in v["dimensions"] if d["state"] != "resolved"]
        for d in v["dimensions"]:
            if d["state"] != "resolved":
                self.assertNotIn("word", d)
        self.assertEqual(v["open_summary"]["dims"], opened)
        self.assertEqual(sorted(x for line in v["open_summary"]["lines"] for x in line["dims"]), sorted(opened))
        q = v["sources"]["qloo"]
        self.assertTrue(q["requests"])
        self.assertNotIn("http", json.dumps(q))
        urls = {m["url"] for r in v["architecture"]["roles"] for m in r.get("materials", []) if m.get("url")}
        self.assertEqual({s["url"] for s in v["sources"]["suppliers"]}, urls)
        for u in urls:
            self.assertTrue(u.startswith("https://"))
        self.assertEqual([r["role"] for r in v["architecture"]["roles"]], ["opening", "core", "drydown"])

    def test_brief_json_keeps_user_data_apart(self):
        r = result(OWN_QUIET)
        brief = story.build_brief({"data_label": "live", "resolution": {"name": "Synthquiet"}, "intent": "a reading room"},
                                  r, {"author": "template", "text": story.template_prose("Synthquiet", r)})
        self.assertEqual(brief["schema_version"], "brief-1.0")
        self.assertEqual(brief["user_intent"]["provenance"], "user_intent")
        self.assertNotIn("reading room", json.dumps(brief["evidence"]) + json.dumps(brief["axes"]) + json.dumps(brief["architecture"]))
        cited = {e["evidence_id"] for e in brief["evidence"]}
        for w in brief["why"]:
            for c in w["chain"]:
                self.assertTrue(set(c["evidence_ids"]) <= cited)


if __name__ == "__main__":
    unittest.main()

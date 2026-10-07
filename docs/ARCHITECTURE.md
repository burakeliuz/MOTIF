# Architecture

MOTIF turns a brand's cultural descriptors, as returned by Qloo, into a scent
direction and a one-page brief for a perfumer. Roles are fixed:

| Role | Who | Never |
|---|---|---|
| Evidence | **Qloo**: the brand's own entry, the brands and films Qloo relates to it, their descriptors | invented, replaced by fixtures, or called an audience |
| Translation | **MOTIF**: deterministic, versioned rules and models | an LLM step; a formula, dose, or preference prediction |
| Prose | **LLM** (optional, `claude-sonnet-5-5`): writes the brief text from the finished result, then validated | chooses a motif, dimension, direction, or material |

## 1. Pipeline

```
Qloo search → brand entity → own entry + related brands + related films      motif/agent.py, motif/qloo.py
   │  every value copied literally with request ID and JSON pointer           motif/evidence.py
   ▼
lexicon cues (55 cues, 14 motifs, context rules)   lexicon-0.4                motif/classify.py
   ▼
weighted motif scores (14 motifs, 0–1)             scoring-1.0                motif/scoring.py
   ▼
six continuous dimensions                          sensory-1.1, continuous-params-1.0   motif/continuous.py
   (temperature, weight, texture, impression, projection, sweetness;
    resolved with a confidence word, or open / pulled both ways)
   ▼
scent architecture (opening, core, drydown;        olfactory-1.1              motif/olfactory.py
   emphasize / avoid when supported)
   ▼
readings and brief (headline, profile, why-chain,  brief-1.0, prose-c1.0      motif/story.py, motif/llm.py
   template or validated LLM prose)
   ▼
web page and one-page PDF                                                     motif/web/
```

The **controller** (`motif/agent.py`) is a deterministic state machine: it
resolves the entity (asking the user only when Qloo returns several brands),
fetches the configured domains within a request budget, and runs the engine.
It never falls back from a failed live call to recorded data, another endpoint,
or another credential.

## 2. The steps

**Evidence.** Each Qloo descriptor becomes an evidence item with its entity,
source kind (`own`, `brand`, `movie`), tag, request ID, and JSON pointer.
Category: `qloo_observation`.

**Lexicon** (`config/motif_lexicon.v1.json`; the legacy engine keeps its frozen
`config/motif_lexicon.json`). Versioned cue groups map descriptors to 14 candidate
motifs (restraint, precision, naturalness, opulence, intimacy, experimentation,
provocation, heritage, industrial character, playfulness, romance, melancholy,
energy, technology). Context rules drop technique nouns in film tags, and look or
material words that qualify a film's story or acting ("Understated humanism").
Cue groups common to the reference set count only at a reduced weight. Category:
`motif_annotation`.

**Motif scores** (`config/motif_scoring.v1.json`). A noisy-OR over channels with
saturation: the brand's own entry, related brands, related films, and the
diversity of cue groups and source kinds. The own entry weighs most; a motif
supported only by common cues is shown as context, never as a lead.
`docs/MOTIF_SCORING.md`.

**Dimensions** (`config/motif_sensory_vectors.v1.json`,
`config/continuous_params.v1.json`). Each motif has a signed cell per dimension
or none (25 of 84 cells; 5 medium-confidence, 20 low; the energy and technology
cells are MOTIF's creative design decisions). Per dimension, the
score-weighted contributions give a value, a mass, and an agreement; below the
thresholds the dimension stays open, and when motifs cancel out it is "open:
motifs pull both ways". A resolved dimension carries a confidence word capped
by its best cell: "supported" (medium) or "tentative" (low cells only).
`docs/SENSORY_MODEL_RESEARCH.md`.

**Scent architecture** (`config/olfactory_directions.v1.json`). 23 accord-type
directions, each with roles, a labelled sensory vector (odor data or design),
descriptors, and material references (IFRA 2019 glossary generic names; trade
names only from supplier pages MOTIF read). Fit is the cosine between the
resolved commitment and the direction; directions that work against a resolved
dimension are set aside; opening, core, and drydown are filled best first; an
empty role is "open to the perfumer". `docs/OLFACTORY_LAYER.md`.

**Readings and brief** (`motif/story.py`). The headline leads with the brand's
own motifs; a direction drawn only from references Qloo relates to the brand
never leads the title. The why-chain links each resolved dimension to its
motifs and their Qloo phrases. The scent idea (the proposal in one sentence)
leads the page, labelled as MOTIF's creative proposal; the chosen accords' own
character for the open dimensions, from their library cells, follows the role
strips and changes no dimension. Open dimensions are one short sentence; why they
are open (no read motif speaks to them, too weak to decide, or motifs pull both
ways) and how many of the returned descriptors MOTIF reads are a closed "Method
detail". The brief JSON (`brief-1.0`) keeps the user's
application context and accepted readings apart from the evidence (categories
`user_intent`, `user_preference`); they change nothing.

**Prose** (`motif/llm.py`). With `MOTIF_ANTHROPIC_API_KEY`, one call writes the
brief text from the result (`prose-c1.0`); the text is checked (no ingredient
outside the architecture, no numbers, no audience or validation claims, every
open dimension named). One controlled retry; otherwise the labelled template.
Every call is reserved in `data/llm_calls.jsonl` before it is sent.

## 3. Web app

`python3 -m motif.web` (standard library server, vanilla JS). Keys stay on the
server; the page never builds HTML from data. Result sections: Cultural profile
→ Olfactory direction → Scent architecture → Emphasize and avoid (only when
supported) → Why: Qloo → motif → scent → The brief; the brief prints as one A4
page; "Download brief (PDF)" returns a real PDF rendered on the server from the same session view (`motif/web/briefpdf.py`, fpdf2, no new Qloo or LLM request). Guards: the review gate (`motif/web/access.py`, fail-closed), per-IP and
daily session caps, a daily Qloo cap, the LLM ledger and budget guard, request
reuse within 30 minutes. Recorded mode is local only and refused on Render.

## 4. Determinism and versions

The same evidence and versions give the same result (checked across
interpreters, `docs/VALIDATION.md`). Every result carries its versions:
`lexicon-0.4`, `scoring-1.0`, `sensory-1.1`, `continuous-params-1.0`,
`olfactory-1.1`, `continuous-1.0`, `brief-1.0`, and the prose prompt. Config
changes need a version bump and a written reason.

## 5. Legacy engine

The rule engine `engine-0.3` (five draft rules R1–R5 in `config/draft_rules.json`,
binary motif strength, the 7-material palette `palette-0.3`) is kept unchanged
as a baseline: `python3 -m motif run --engine legacy`,
`python3 -m motif compare-engines`, and `reports/baselines/legacy_engine_0.3.json`
(per-stage collapse 13/13/12/7/7/3 on the 13 trial brands, config hashes
checked by `tests/test_legacy_baseline.py`). R1 restraint → light,
R2 intimacy → close-wearing, R3 precision → smooth-finished, R4 opulence →
dense, R5 naturalness → natural-feeling; their relations survive as the five
medium-confidence cells of `sensory-1.0` (unchanged in `sensory-1.1`).

## 6. Repository map

```
motif/agent.py      controller (deterministic research flow)
motif/qloo.py       live access (budget, retries, session cache) and recorded replay
motif/evidence.py   Qloo responses → evidence items
motif/classify.py   lexicon → motif annotations
motif/scoring.py    weighted motif scores
motif/continuous.py six continuous dimensions with the trace
motif/olfactory.py  scent architecture
motif/story.py      headline, profile, why-chain, template prose, checks, brief JSON
motif/llm.py        optional prose writer and call ledger
motif/web/          server, view model (present.py), review gate, usage caps, static UI
motif/translate.py, materials.py, brief.py, narrative.py, engine.py   legacy engine
tools/              offline analyses: baseline, engine comparison, holdout, sensory evidence and review, validation
config/             versioned lexicon, models, library, legacy rules and palette, manifest
reports/            analyses and validation (literal Qloo values only as curated excerpts)
```

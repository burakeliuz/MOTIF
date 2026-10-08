# Sensory model research: 12 motifs × 6 dimensions (`sensory-1.0`)

Phase 3 of the engine refactor (2026-10-07). Outputs:
`config/motif_sensory_vectors.v1.json` (the model, revision r2; promoted from
`config/candidates/` unchanged in phase 5 and loaded by the continuous engine) and
`config/candidates/odor_axis_evidence.v1.json` (the odor-family evidence it
cites). Tools: `tools/sensory_evidence.py` computes the evidence from open
datasets; `tools/sensory_model_review.py` checks the model (rules, data agreement,
quoted numbers, coverage, similarity; exit code 1 on a problem). The model is
MOTIF's creative mapping, not perception science.

## 1. What the model has to do

The legacy engine translated 5 of 12 motifs, each to one pole of one dimension
(R1–R5), and reached 4 of 12 poles on the 13 trial brands
(`docs/ENGINE_REDESIGN.md`). The new model gives each motif a signed value on
every dimension where MOTIF can defend a relation, and `null` everywhere else.

| Dimension | −1 | +1 |
|---|---|---|
| `warm_cool` (temperature) | warm | cool |
| `light_dense` (weight) | light | dense |
| `raw_polished` (texture) | raw | polished |
| `natural_synthetic` (impression) | natural | synthetic |
| `intimate_projecting` (projection) | intimate | projecting |
| `sweet_dry` (sweetness) | sweet | dry |

`null` = MOTIF makes no claim; it contributes nothing (never zero). 0 would mean
evidenced neutrality; no cell uses it.

## 2. What could and could not be read in this session

The requested hierarchy was peer-reviewed olfaction → crossmodal research
(Spence, Crisinel) → perfumery literature (Jellinek, Zarzo & Stanton, the Edwards
wheel) → odor databases (Good Scents) → supplier documents.

The research environment could not reach the academic and reference hosts
this needs (among others `pmc.ncbi.nlm.nih.gov`, `www.frontiersin.org`,
`www.mdpi.com`, `journals.sagepub.com`, `academic.oup.com`, `link.springer.com`,
`en.wikipedia.org`, `www.thegoodscentscompany.com`; checked through the agent
proxy on 2026-10-07). A first research run with six agents was stopped because
every page fetch was refused; under "never cite unread sources", nothing they saw
only as search-result titles is used. **No crossmodal or perfumery literature was
consulted**, and the model cites none.

What was readable: the Pyrfume public data archive on
`raw.githubusercontent.com`. Three curated datasets were read as data:

| Key | Dataset | What was read | Scale |
|---|---|---|---|
| D85 | Dravnieks (1985), *Atlas of Odor Character Profiles*, ASTM DS61 | `dravnieks_1985/behavior_1.csv`: panel applicability of 146 descriptors, incl. WARM, COOL/COOLING, LIGHT, HEAVY, SWEET, DRY/POWDERY | 160 stimuli |
| KV16 | Keller & Vosshall (2016), *Olfactory perception of chemically diverse molecules*, BMC Neuroscience | `keller_2016/behavior.csv`: 55 subjects, 0–100 ratings incl. WARM, COLD, SWEET, and pleasantness | 960 stimuli (about 480 molecules × 2 dilutions; not independent) |
| LEF | Leffingwell odor dataset (Sanchez-Lengeling et al. release) | `leffingwell/behavior.csv`: 113 binary expert labels incl. warm, dry, sweet | about 3,500 molecules |

The books and articles themselves were not read; bibliographic details are the
ones printed in the Pyrfume manifests. File SHA-256 are recorded in the evidence
JSON; the datasets stay in the git-ignored `data/external/pyrfume/`
(`python3 tools/sensory_evidence.py --fetch` downloads them).

## 3. Method

Each non-null cell carries a direction, a strength (weak 0.25, moderate 0.5), a
confidence (low, medium), an evidence type, a rationale, a design origin, the
odor-step sources it cites (if any), and an uncertainty note.

- **`motif_design_inference`** (18 cells): MOTIF's reasoning from the cue words
  to a sensory quality. Five restate the legacy rules R1–R5 (origin recorded as
  `design_origin`, not as a reference: MOTIF's own documents do not support a
  claim). Where odor data is merely *consistent* with a design cell (e.g. woody
  odors are rated less sweet), it is listed but never presented as support.
- **`imagery_route`** (5 cells): MOTIF imagines odor imagery for a motif (design
  inference, stated as such in every rationale), and published odor-descriptor
  data associates that imagery with a pole.

Rules, checked by the review tool:

- **Confidence.** *Medium* only when a design inference states the core meaning
  of the cue words, or an imagery word appears among the motif's own cues and its
  odor step is replicated. *Low* otherwise. *High* is not used: no cell has direct
  empirical support for the motif-to-dimension link.
- **Strength.** Design inference: at most moderate. Imagery route: moderate only
  when the odor step is replicated in both rated datasets with both r ≥ 0.3 and
  survives the pleasantness control; otherwise weak. **Any low-confidence cell is
  weak**, so a dimension that rests on low cells can read at most "slightly …".
- **Forbidden without an explicit project decision** (`config/draft_rules.json` draft-0.2):
  playful = sweet, melancholic = cool, romantic = floral, heritage = warm,
  industrial = synthetic. These cells stay null.

| Kind of support | Where it appears |
|---|---|
| Empirical / perceptual | only the odor-family → pole step of the 5 imagery routes (D85, KV16) |
| Perfumery convention | not read in this session; LEF's expert labels only agree or contradict |
| MOTIF design inference | every motif → dimension link, and every motif → imagery link |

## 4. Odor family × pole evidence

`tools/sensory_evidence.py` groups each dataset's own descriptors into 17 odor
families and measures each **pole with its own descriptor** (no contrasts: in D85
WARM and COOL are unrelated, r ≈ −0.04, and so are SWEET and DRY/POWDERY, so a
contrast would turn "rated less cool" into "warmer"). Per family and pole: Pearson
r across stimuli (D85, KV16), phi (LEF), a deterministic bootstrap 95% interval,
r without the five stimuli highest on the family, and KV16's partial r with
pleasantness held constant.

A rated dataset **supports** a pole when r ≥ 0.2, the interval stays above 0, and
r stays ≥ 0.1 without the top five stimuli; **×2** = both rated datasets;
**less** = r ≤ −0.2 with the interval below 0 (rated *less* on that pole, which is
never support for the opposite pole). *weak* = smallest supporting r < 0.3;
† = the KV16 association disappears with pleasantness held constant. No dataset
has a usable dry descriptor, so **the dry pole is never supported by data**; D85's
"DRY, POWDERY" is reported as *powdery*. Texture, impression, and projection have
no descriptor in any dataset.

| Family | warm | cool | light | dense | sweet | powdery |
|---|---|---|---|---|---|---|
| animalic | · | less (D85 −0.39, KV16 −0.21) | less (D85 −0.51) | ×1 (D85 +0.46) | less (D85 −0.43, KV16 −0.52) | · |
| burnt / tar | ×1 weak (KV16 +0.20) | less (D85 −0.25) | less (D85 −0.42) | ×1 (D85 +0.49) | less (D85 −0.41, KV16 −0.38) | · |
| chemical / solvent | · | ×1 weak (KV16 +0.29) | · | ×1 weak (D85 +0.22) | less (D85 −0.29) | · |
| citrus | · | ×1 weak (D85 +0.30) | ×1 (D85 +0.40) | less (D85 −0.25) | ×1 (D85 +0.35) | · |
| earthy / musty | · | less (D85 −0.31) | less (D85 −0.33) | · | less (D85 −0.40) | ×1 weak (D85 +0.28) |
| floral | · | · | ×1 (D85 +0.49) | less (D85 −0.30) | **×2** (D85 +0.48, KV16 +0.58) | · |
| fruity | · | · | ×1 (D85 +0.33) | less (D85 −0.29) | **×2** (D85 +0.67, KV16 +0.76) | less (D85 −0.20) |
| gourmand / balsamic | **×2** (D85 +0.36, KV16 +0.41) | · | · | · | **×2** (D85 +0.37, KV16 +0.45) | · |
| green / herbal | · | · | · | · | · | · |
| incense | ×1 (D85 +0.31) | ×1 (D85 +0.32) | ×1 (D85 +0.38) | · | ×1 (D85 +0.46) | · |
| leathery | · | · | · | · | less (D85 −0.30) | · |
| metallic | · | · | less (D85 −0.24) | ×1 weak (D85 +0.24) | less (D85 −0.33) | · |
| minty / camphor | · | ×1 (D85 +0.87) | ×1 weak (D85 +0.27) | · | · | · |
| musk | · (D85 +0.23, not robust) | · | · | · | · | ×1 (D85 +0.39) |
| soapy / aldehydic | · | · | ×1 (D85 +0.31) | less (D85 −0.23) | · | ×1 (D85 +0.33) |
| spicy | **×2** weak (D85 +0.49, KV16 +0.26) | · | · | · | ×1 weak (D85 +0.27) | · |
| woody | · | · | · | · | less (KV16 −0.28) | ×1 (D85 +0.36) |

Readings that matter for the model: balsamic/gourmand and spicy notes are rated
warmer in two datasets, and sweeter (balsamic) independently of pleasantness;
floral and fruity notes are rated sweeter in two datasets; burnt/tar and animalic
notes are rated heavier (one dataset) and less sweet (two); **metal is not rated
cold** (D85 METALLIC is temperature-neutral, and its top stimuli are sulfur and
amine off-notes, so the family is weak as imagery); **musk alone has no robust
temperature, weight, or sweetness association** (D85 MUSK; the warmth of
"musky" families comes from animalic notes, and KV16's lay "musky" tracks
sweaty); incense is rated both warmer and cooler (ambiguous); woody notes are
powdery and less sweet, not "dry" in any measured sense.

Limits: single molecules at fixed dilutions, not perfumes; American panels (D85
1980s, KV16 New York volunteers); D85 COOL is largely trigeminal cooling (mint,
camphor) and KV16 COLD peaks for solvents, neither is perfumery "freshness"; D85
LIGHT/HEAVY partly tracks pleasantness (FRAGRANT r −0.58 with HEAVY); about 100
correlations without multiple-comparison control. The data supports only the
family → pole step, never anything about a brand.

## 5. The model (r2)

| Motif | warm − / + cool | light − / + dense | raw − / + polished | natural − / + synthetic | intimate − / + projecting | sweet − / + dry |
|---|---|---|---|---|---|---|
| restrained |  | −0.50 M |  |  |  |  |
| intimate |  |  |  |  | −0.50 M |  |
| precise | +0.25 L |  | +0.50 M |  |  |  |
| opulent | −0.25 L* | +0.50 M |  |  | +0.25 L | −0.25 L* |
| natural |  |  | −0.25 L | −0.50 M |  | +0.25 L |
| experimental |  |  | −0.25 L | +0.25 L |  |  |
| provocative | −0.25 L* | +0.25 L* | −0.25 L |  | +0.25 L | +0.25 L |
| heritage |  |  |  |  |  |  |
| playful |  | −0.25 L |  |  | +0.25 L |  |
| melancholic |  |  |  |  |  |  |
| romantic |  |  |  |  |  |  |
| industrial |  | +0.25 L* | −0.25 L |  |  | +0.25 L |

M/L = medium/low confidence; * = imagery route; blank = null. 23 of 72 cells;
5 medium (the five legacy links, now graded and capped at moderate), 18 low.
Every pole is reachable (legacy: 4 of 12): warm 2, cool 1, light 2, dense 3,
raw 4, polished 1, natural 1, synthetic 1, intimate 1, projecting 3, sweet 1,
dry 3 motifs.

| Motif | Imagery (MOTIF design inference) | Claims and why | Notable nulls |
|---|---|---|---|
| restrained | none (amount, not character) | light (R1) | projection (no `restrained → intimate`), texture (minimal can be raw or refined), sweetness (R1 decides none) |
| intimate | none ("skin musk" rejected: musk alone is neutral in the data) | close-to-skin presence (R2) | temperature (the "warm skin" idiom is not supported), weight (R2) |
| precise | none ("clean lines → soapy" would be a pun) | polished (R3); slightly cool, tentative (crisp construction) | impression (craft can be natural; abstraction belongs to experimental), sweetness |
| opulent | balsamic, spice, floral | dense (R4); slightly warm and slightly sweet (balsamic, spice, floral: odor step replicated, imagery not in the cues, so low); slightly projecting | texture (baroque vs polished finish) |
| natural | none ("earthy → musty" would be a pun) | natural impression (R5); slightly raw (earthy, handcrafted only); slightly dry, tentative (woody notes are only rated *less sweet*) | temperature, weight |
| experimental | none (chemical/metallic rejected: off-note families) | slightly raw (deconstructed); slightly synthetic (conceptual) | sweetness ("not sweet" is not a direction) |
| provocative | smoke, tar, leather, animalic | slightly raw, dry, projecting (design); slightly warm (burnt/tar, one dataset) and slightly dense (burnt/tar and animalic, one dataset) | impression |
| heritage | none | no claim: refinement vs patina is undecided, heritage = warm is forbidden | all; stays in the cultural profile, open to the perfumer |
| playful | none (fruity/sweet is the forbidden stereotype) | slightly light, slightly projecting (outgoing), tentative | sweetness (forbidden) |
| melancholic | none ("damp earth" is mould, not mood) | no claim: a close presence would duplicate intimate; cool is forbidden | all |
| romantic | none (romantic = floral is forbidden) | no claim: without the floral stereotype only closeness remains, which duplicates intimate | all |
| industrial | tar, rubber, metal | slightly raw, slightly dry (design); slightly dense (burnt/tar, one dataset) | impression (industrial = synthetic forbidden), temperature (metal is not rated cold) |

## 6. Self-review (`python3 tools/sensory_model_review.py`)

| Check | Result (r2) |
|---|---|
| Value = direction × strength; enums; rules (low → weak, design ≤ moderate, moderate imagery needs replicated robust data, no high) | pass |
| Forbidden stereotype cells | all null |
| Imagery routes supported by at least one imagery family | 5 of 5 |
| Quoted numbers match the family's measured values | pass (checked in rationales, uncertainty, and null notes) |
| Near-identical motif vectors (cosine ≥ 0.9) | none; most similar: provocative–industrial 0.78, restrained–playful 0.71, opulent–provocative 0.51 |
| Opposite pairs | restrained–opulent −0.76, precise–natural −0.36, intimate–provocative −0.45; **natural–industrial +0.47** (they share raw texture and dryness; their natural vs manufactured contrast is not encoded because industrial = synthetic needs an explicit project decision) |
| Design cell against its own imagery | opulent → dense, while floral imagery is rated lighter (noted in the cell's uncertainty) |
| Stereotypes | the five named in draft-0.2 are excluded; remaining low cells are marked tentative |
| Forced axes | 49 of 72 cells null; three motifs make no claim at all |
| Circularity | intimate → intimate and natural → natural are name matches; recorded in their uncertainty notes and capped at moderate |
| Collapse risk | the claims that can resolve a dimension with "supported" are only the five medium cells; the rest are tentative leanings. Phase 6 measures differentiation with and without the tentative cells |
| "Just R1–R5 with numbers"? | the medium core is R1–R5; 18 further low cells reach the 8 poles R1–R5 never touched, always labelled tentative. Graded motif scores, not the cells alone, carry most of the difference between brands (phase 6) |

## 7. Review and the one revision

The first candidate (r1, 35 cells) was reviewed from three independent lenses
(method and honesty, a perfumer's reading, engine behaviour), each reading the
model, the data, and the code, and replaying the 13 trial brands offline. Main
findings, all verified against the data before acting:

- **Blocker: forbidden stereotypes returned with a data veneer.** r1 had playful
  → sweet, romantic → floral → sweet/light, industrial → synthetic. The odor step
  (fruity → sweet) is near-definitional co-use of words and does not support the
  imagery step, which is the stereotype itself. → all null in r2.
- **Blocker: confidence words overstated.** Several low, unreferenced cells could
  add up to "firm" or "supported". → low cells are weak in r2, and the engine caps
  a dimension's confidence word at the best cell behind it (phase 5).
- **The data step was mis-specified.** Poles were contrasts of unrelated
  descriptors; "rated drier" meant "rated less sweet"; MUSK and ANIMAL were one
  family (musk alone is neutral); incense and tar were one family; D85 LIGHT/HEAVY
  partly tracks pleasantness. → per-pole measurement, split families, bootstrap,
  drop-top-5, pleasantness control; dry is never data-supported.
- **Strength had no rule** and the only strong cells were legacy name matches. →
  strength rule; design inference capped at moderate; legacy origin recorded as
  `design_origin`, not as a reference.
- **Perfumer corrections**: romantic and melancholic weight nulled (romantic
  florals are dense, melancholy reads muted), provocative's sweetness reduced and
  musk removed, precise → synthetic nulled (tailoring is not synthetic),
  experimental's chemical/metallic imagery rejected (literal off-notes), common-cue
  motifs excluded from the aggregation (engine).
- **Inconsistent nulls**: heritage → polished nulled (same ambiguity as restraint's
  texture).

The third lens (engine behaviour and code correctness) did not finish: the
session's usage limit stopped it, and its findings are lost. Its scope was
partly covered by the method lens, which recomputed the data independently and
confirmed every quoted number of r1, and by the phase 5 engine changes taken from
both completed reviews (common-cue motifs excluded, confidence word capped,
evidence basis per dimension, cell rationale carried into the trace). Code
correctness of `tools/sensory_evidence.py` r2 is checked by
`tests/test_sensory_model.py` (the summary is recomputed from the stored
measurements) and by the reviewer-verified spot values in section 4.

Gate: no near-identical vectors; guesses are labelled and capped as tentative;
the model is the five legacy links plus labelled leanings across all twelve poles,
not R1–R5 alone. Passed, with the honest consequence that most new claims are
tentative.

## 8. Not read; to verify when the network allows

Named only as a reading list, not as support: crossmodal correspondence studies
on odors and temperature, pitch, shape, and texture (Spence, Crisinel, Deroy and
colleagues); Zarzo & Stanton's analyses of perfumers' descriptor spaces; the
Geneva Emotion and Odor Scale (Chrea and colleagues); M. Edwards' fragrance
wheel; P. Jellinek's odor-effect classification; Arctander's material
monographs; the IFRA fragrance ingredient glossary. Full-text access to
`pmc.ncbi.nlm.nih.gov`, `www.frontiersin.org`, and the publishers' hosts would
allow this. Design questions that would change the model: any of the five
forbidden pairs; whether heritage, romance, or melancholy should carry a
sensory claim at all.

## 9. After validation (phase 10)

The model is the product's sensory layer now (`continuous-1.0`, scent
architecture `olfactory-1.1`). The final validation (`docs/VALIDATION.md`) shows
what rests on it: removing its 18 low-confidence cells leaves 9 of 11 distinct
profiles and 7 of 11 distinct architectures on the 13 trial brands, so a third
of the architectural differences come from MOTIF's design readings, which the
product labels "tentative". The tentative dry lean (9 of 13 brands) remains. No
cell was changed after phase 3's revision; any change needs a new version and a
new holdout.

## 10. `sensory-1.1`: two motifs as creative design decisions (2026-10-07)

`lexicon-0.4` reads energy and technology words that Qloo returned for the
recorded brands, so the model gains two motifs. By project decision their
translations are documented as MOTIF's creative design decisions, not
researched: no odor data was sought, and each motif claims one weak,
low-confidence cell, so a dimension resting on it alone reads "tentative".

| Motif | Cell | Reading | Left open (why) |
|---|---|---|---|
| energy (energetic, dynamic, sporty) | projection → diffusive | movement outward, a presence that reaches others | temperature (heat as easily as freshness), weight (quick and light or forceful and dense) |
| technology (technological, technical, futuristic) | impression → synthetic-feeling | an engineered, abstract impression (an impression, not ingredient origin) | temperature ("cold technology" is a cliché; metal is temperature-neutral in odor data), texture (rugged utility or seamless finish) |

No odor imagery is assigned to either. The twelve `sensory-1.0` motifs and the
five forbidden pairs are unchanged; technology → synthetic-feeling is not the
forbidden industrial = synthetic pair, which reads exposed materials. The
model now claims 25 of 84 cells (5 medium, 20 low).

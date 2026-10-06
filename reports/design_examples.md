# MOTIF design examples (stage 3)

> **Design examples, not engine output.** The values below were computed in
> stage 3 by a scratch script that applies `config/motif_lexicon.json`
> (lexicon-0.1), `config/draft_rules.json` (draft-0.2, rules R1–R5) and
> `config/material_palette.json` (palette-0.1) to the stored live run
> `live-20261006T103307Z-660d`. No MOTIF engine exists yet. Stage 4 must
> reproduce these results from the same inputs (`MOTIF_BUILD_SPEC.md`, section 17).
> The lexicon was written after reading these same five seeds, so it is tuned
> on them. Treat the numbers as a worked specification, not as validation.

Every chain below keeps four layers apart:

| Layer | Provenance category | Where it comes from |
|---|---|---|
| Returned value | `qloo_observation` | A literal tag name and ID with its request (`req NNNN`) and JSON Pointer; requests are listed in `reports/evidence_excerpt.md` |
| Cue match → motif | `motif_annotation` (method `lexicon`, `lexicon-0.1`) | MOTIF's classification rule, not a Qloo label |
| Motif → axis | `design_rule` (R1–R5, draft-0.2) | A creative hypothesis, not a finding |
| Axis → material | `design_rule` (palette-0.1 profile) plus a supplier descriptor | MOTIF's creative mapping, resting on a supplier excerpt |

Two separate confidence labels are always shown:

- **Evidence strength** (`strong` / `moderate` / `weak` / `context_only`) measures how much
  returned data supports a motif.
- **Rule confidence** is `draft_hypothesis` for every rule R1–R5 and every
  material profile. Strong evidence does not make a rule more true.

## 1. Brand evaluation

Scope: the seed's own descriptors (`aesthetic_property`, `personal_style`,
`emotional_tone` tags) and related brands, movies, and music artists (top 10
each). "Non-common cue" means a lexicon cue that is not common across the
reference set (see `config/motif_lexicon.json` → `commonness`).

| Criterion | A24 | MUJI | Comme des Garçons | Nike | Ralph Lauren |
|---|---|---|---|---|---|
| Own descriptor tags (3 namespaces) | 10 (one is the literal string "null") | 16 | 15 | 13 | 12 |
| Distinct non-common cues found | 11 | 14 | 20 | 3 | 12 |
| Related entities with a non-common cue (brand / movie / artist, of 10 each) | 1 / 6 / 3 | 7 / 10 / 0 | 10 / 6 / 6 | 1 / 0 / 1 | 10 / 3 / 0 |
| Distinct from the other seeds (stage 2, returned IDs) | Shares 2 movies and 1 artist with CDG | No shared results | Shares results with A24 (movies, artist) and RL (books) | Shares 7 of 10 artists with RL | Shares 7 of 10 artists with Nike |
| Traceable chain to an axis (enriched) | No active mapped motif → 0 axes | 3 axes | 1 axis | 0 axes | 2 axes |
| Qloo relations add beyond the seed's own description (axes: own only → enriched) | 0 → 0 | 0 → 3 | 0 → 1 | 0 → 0 | 0 → 2 |

### Likely causes of weak results

Each cause is a hypothesis; where the evidence does not decide it, it says so.

- **A24: translation rules, not data.** The data is rich (11 cues, 6 movies
  with cues). The only motif that reaches `moderate` is `provocative`
  (own "Provocative", "Edgy"; related brand Vice "Provocative"), which has no
  axis rule. A secondary factor is the entity type: A24 is a film company, and
  its related brands are media platforms whose "Minimalist…" descriptors
  describe interfaces (common cue, so context only).
- **Comme des Garçons: translation rules, not data.** It has the most cues (20).
  Its strongest motifs, `experimental` (strong) and `provocative`/`industrial`
  (moderate), are all unmapped by design (draft-0.2 forbids, for example,
  industrial → synthetic). Only `precise` → polished reaches an axis.
- **Nike: undecided between data coverage and query scope.** Its own aesthetic
  tags are about logos and technology ("Minimalist Logo Design",
  "Technological Aesthetics", "Performance-Driven Silhouettes", "Dynamic
  Motion Lines"). The related brands are sports clubs and platforms, the
  people are footballers, and the movies are sports films whose style tags
  describe camera technique. Whether a different query (for example related
  brands filtered by industry) would help is untested.
- **MUJI and Ralph Lauren music domain: query scope.** MUJI's artists are all
  tagged Japanese rock and pop; Nike's and Ralph Lauren's artists overlap
  (hip hop). No style tag of these artists matched a cue, so music adds
  nothing for these seeds. It also does no harm.

## 2. Selection

**Demo and design examples: MUJI and Ralph Lauren.**

- Both give a complete, traceable chain whose active motifs are anchored in the
  seed's own tags or in related brands, with movies as corroboration.
- They lead to different directions: light vs dense, with polished shared, so
  the demo shows the engine discriminating rather than always answering the same.
- Ralph Lauren is the less comfortable case. Its `dense` target rests on
  evidence returned only by Qloo relations (one related brand plus two movies).
  This is shown, not hidden.

**Acceptance scenarios that must also be shown (not hidden):**

- Comme des Garçons: strong identity, but only one axis can be set. The rules
  are the gap.
- A24: rich data, no axis can be set.
- Nike: thin, mostly common descriptors, so evidence is insufficient.

These are listed in `MOTIF_BUILD_SPEC.md`, section 17.

No new brand was queried in stage 3, and no extra Qloo request was made. A
held-out check is planned as stage-4 task T1; it needs the owner's OK.

## 3. Chain A: MUJI

Seed: "MUJI" → `urn:entity:brand` **Muji** `E12201A5-CC50-40AF-97AE-C54A2CA303F7`
(req 0010; 7 same-name `urn:entity:place` candidates not chosen).

### 3.1 Evidence → motif (`motif_annotation`, lexicon-0.1)

| Motif | Strength | Sources | Returned values (literal, with provenance) |
|---|---|---|---|
| restrained | strong | own, brand, movie | own "Unpretentious" `emotional_tone` (req 0011 `/results/0/tags/41`); brand Global Work "Unpretentious" (req 0012 `/results/entities/1/tags/36`); movies: Still Walking "Muted" (req 0013 `/results/entities/0/tags/79`), Like Father, Like Son "Understated elegance" (`/results/entities/1/tags/4`), Our Little Sister "Restrained" (`/results/entities/3/tags/19`), Maborosi "Sparse mise en scene" (`/results/entities/7/tags/50`), Burning "Understated" (`/results/entities/8/tags/122`), and others |
| precise | strong | own, brand, movie | own "Clean Lines" `aesthetic_property` (req 0011 `/results/0/tags/12`); brands GU, Lepsim, Urban Research "Clean Lines" (req 0012 `/results/entities/3/tags/14`, `/7/tags/2`, `/8/tags/3`); movies A Sun "Meticulous" (req 0013 `/results/entities/5/tags/44`), Asako I & II "Meticulous composition" (`/results/entities/6/tags/117`) |
| natural | moderate | own, brand | own "Natural Materials" (req 0011 `/results/0/tags/11`); brands Creema "Handcrafted", "Natural Materials" (req 0012 `/results/entities/0/tags/1`, `/0/tags/2`), studio CLIP "Natural Tones", "Earthy Color Palette" (`/4/tags/2`, `/4/tags/5`), Niko And... "Earthy Tones" (`/5/tags/3`), Urban Research "Natural Tones" (`/8/tags/4`) |
| heritage | weak | own | own `personal_style` "timeless" (unmapped motif) |
| melancholic | weak | movie | Shoplifters "Melancholic warmth" (unmapped motif) |
| intimate | context_only | — | 12 matches, all of the common cue group "intimate" |

The three "Clean Lines" brands carry the same tag ID. Together they count as
one source (brand), not three pieces of evidence.

### 3.2 Motif → sensory targets (`design_rule`, draft-0.2)

| Axis | Target | Rule | Evidence strength | Rule confidence |
|---|---|---|---|---|
| warm_cool | `null` | — | — | — |
| light_dense | light | R1 restrained | strong | draft_hypothesis |
| raw_polished | polished | R3 precise | strong | draft_hypothesis |
| natural_synthetic | natural (impression) | R5 natural | moderate | draft_hypothesis |
| intimate_projecting | `null` (intimate is context only; restrained does not imply it) | — | — | — |
| sweet_dry | `null` | — | — | — |

### 3.3 Targets → materials (palette-0.1)

Scores are computed as
`sum(weight × (+1 match / −1 opposite / 0 absent)) / number of targeted axes`,
with weights strong 1.0 and moderate 0.6. These are design parameters.

| Material | Score | Matches | Unrequested properties | Selected |
|---|---|---|---|---|
| M01 HEDIONE® | 0.667 | light, polished | none | heart |
| M02 Bergamot oil | 0.533 | light, natural | none | top |
| M03 ISO E SUPER® | 0.333 | polished | none | base (tie with M05 broken by fewer unrequested properties) |
| M05 HABANOLIDE® | 0.333 | polished | warm | no |
| M08 Orris butter | 0.200 | natural | none | no (3 materials reached) |
| M06 Vetiver oil Haiti | −0.133 | natural; opposes polished | dry | excluded (opposite pole) |
| M04 AMBROX® SUPER, M07 Labdanum | −0.333 | oppose light | projecting / warm | excluded |

### 3.4 Short perfumer brief (design example)

> **MUJI: direction, not formula.** Aim for a light, polished impression with
> a natural aesthetic. Restraint and clean, precise lines run through the
> brand's own Qloo tags, its related brands, and the style tags of related
> films. Natural materials and earthy tones appear in its own tags and in
> related brands.
>
> - **Proposed starting materials:** bergamot oil (top; light, natural
>   impression), HEDIONE® (heart; transparent, polished), ISO E SUPER® (base;
>   smooth, velvety).
> - **Left open by the evidence:** temperature, projection, and sweetness. One
>   supplier excerpt mentions a sweet, fruity facet of bergamot, so the
>   perfumer should decide.
>
> Ingredient descriptors are from supplier excerpts that are still unverified
> in full. No dosage or regulatory assessment is given.

## 4. Chain B: Ralph Lauren

Seed: "Ralph Lauren" → `urn:entity:brand` **Ralph Lauren**
`2723B38E-C3E2-435F-A77B-A94A92D68D07` (req 0037). Same-name `urn:entity:person`
and `urn:entity:author` candidates were returned. The expected type (brand)
decided the choice; in the product, a type-less query would ask the user.

### 4.1 Evidence → motif

| Motif | Strength | Sources | Returned values |
|---|---|---|---|
| precise | moderate | own, brand | own "Classic Tailoring" `aesthetic_property` (req 0038 `/results/0/tags/34`); brands Armani Exchange "Clean Lines" (req 0039 `/results/entities/0/tags/3`), Louis Vuitton "Structured Silhouettes" (`/1/tags/34`), Calvin Klein "Clean Lines" (`/4/tags/24`), Hugo Boss "Tailored", "Structured" (`/5/tags/18`, `/5/tags/19`), Emporio Armani "Sharp Tailoring" (`/8/tags/11`), Fendi "Architectural Silhouettes" (`/9/tags/35`). Movie "Precision editing" is a common cue (context only). |
| opulent | moderate | brand, movie | brand Versace "Baroque Prints" (req 0039 `/results/entities/2/tags/38`); movies Crazy Rich Asians "Opulent production design", "Ornate costume spectacle", "Lush" (req 0040 `/results/entities/2/tags/25`, `/97`, `/101`), Mamma Mia! Here We Go Again "Lush" (`/results/entities/5/tags/162`) |
| heritage | moderate | own, brand | own "Classic Tailoring", "Classic"; brands Louis Vuitton "Timeless", Tommy Hilfiger "Classic Silhouettes" (unmapped motif; no axis) |
| provocative | weak | brand | Versace, Guess, Gucci (unmapped) |
| restrained | weak | movie | Marriage Story "Restrained"; the "Minimalist…" cues are common, so context only |

"Classic Tailoring" supports two motifs (precise and heritage). It is still a
single returned value.

### 4.2 Targets

| Axis | Target | Rule | Evidence strength |
|---|---|---|---|
| light_dense | dense | R4 opulent | moderate. **Rests on Qloo relations only** (no own descriptor; one related brand) |
| raw_polished | polished | R3 precise | moderate |
| warm_cool, natural_synthetic, intimate_projecting, sweet_dry | `null` | — | — |

### 4.3 Materials

| Material | Score | Unrequested properties | Selected |
|---|---|---|---|
| M04 AMBROX® SUPER | 0.300 | **projecting** | base (covers dense; tie with M07 broken by material ID) |
| M03 ISO E SUPER® | 0.300 | none | heart (covers polished) |
| M05 HABANOLIDE® | 0.300 | **warm** | base |
| M07 Labdanum absolute | 0.300 | warm | no (base slots full) |
| M01 HEDIONE® | 0.000 | — | excluded (opposes dense) |
| M02 Bergamot oil, M06 Vetiver | negative | — | excluded |

No palette material can serve as a top note without contradicting `dense`, so
the top stays open.

### 4.4 Short perfumer brief (design example)

> **Ralph Lauren: direction, not formula.** Aim for a dense, polished
> impression. Precision appears in the brand's own "Classic Tailoring" tag and
> in the tailoring and structure tags of related fashion brands. Density comes
> only from Qloo relations (a baroque-print brand and two lush, ornate films),
> so treat it as the weaker half of the brief.
>
> - **Proposed starting materials:** ISO E SUPER® (heart; smooth, velvety),
>   AMBROX® SUPER (base; powerful amber).
> - **Creative choices, not evidence:** AMBROX® SUPER also brings diffusion
>   (projection) and HABANOLIDE® (base) brings warmth. Neither is asked for by
>   the evidence.
> - **Left open:** top note, temperature, natural/synthetic impression, and
>   sweetness.
> - **Heritage:** the evidence also supports "heritage", which has no
>   translation rule and therefore does not shape the scent.

## 5. Qloo's contribution: seed description only vs plus relations

Rules, lexicon, thresholds, and palette are identical in both columns.

- **"Seed only"** uses Qloo's `/entities` tags of the seed. This is the seed's
  own description as returned by Qloo, so it is still Qloo data.
- **"Plus relations"** adds related brands, movies, and artists.

A baseline without any Qloo data (model memory) is a separate, deferred
evaluation (`docs/DEFERRED_DESIGN.md`).

| Seed | Seed only: active motifs → axes | Plus relations: active motifs → axes | What changed |
|---|---|---|---|
| MUJI | none active (restrained, precise, natural, heritage all weak) → 0 axes | restrained strong, precise strong, natural moderate → light, polished, natural | Three motifs supported by the seed's own tags were corroborated by relations. |
| Ralph Lauren | heritage moderate (unmapped) → 0 axes | precise moderate, opulent moderate, heritage moderate → dense, polished | Precise was corroborated; opulent is new and comes from relations only. |
| Comme des Garçons | experimental, provocative moderate (unmapped) → 0 axes | experimental strong; provocative, industrial, precise moderate → polished | Polished comes from relations only. The brand's own identity stays untranslated. |
| A24 | provocative moderate (unmapped) → 0 axes | provocative moderate (corroborated by Vice) → 0 axes | Corroboration only; no sensory change. |
| Nike | none (only the common "Minimalist") → 0 axes | none (weak only) → 0 axes | No contribution shown. |

Read-out:

- In 3 of 5 seeds, relations turned a description that could not move any
  axis into a partial direction (3, 2, and 1 axes).
- In 2 of 5 seeds they changed no sensory decision.
- No axis that was set in the seed-only column was overturned, because none
  was set there.
- Five seeds and a lexicon tuned on them support no general claim. In
  particular, the seed-only column is empty partly by construction: the own
  description alone can only reach `moderate` with two distinct non-common
  cues.

## 6. Contradictory evidence

The real data produced **no** axis conflict under these rules. Ralph Lauren
has `opulent` (moderate) but `restrained` stays weak; MUJI has no `opulent`.
The conflict behaviour is therefore specified with a **synthetic fixture**
(`synthetic_fixture`, never evidence):

> SYNTHETIC: a seed with `restrained` = strong and `opulent` = moderate.
> R1 pushes `light_dense` toward light and R4 toward dense. The axis becomes
> `conflicted`: value `null`, both motifs and their evidence shown, no
> material ranked on that axis. The agent asks the user to pick one direction
> or to leave the axis open (`MOTIF_BUILD_SPEC.md`, section 8.4).

# MOTIF Qloo feasibility report

**Recommendation: `narrow`.** Continue with MOTIF, but build it on the subset of
Qloo surfaces that returned descriptive and differentiated evidence: the seed's
own descriptor tags, plus related brands, movies, and music artists with their
style/aesthetic fields. Do not use unscoped tag insights, people, or books for
motif evidence, and use places only with care. Reasons and uncertainties are in
section 10.

- Date: 2026-10-06
- Brief: `MOTIF_QLOO_FEASIBILITY.md` rev 0.2, section 10
- Live runs: pilot `live-20261006T102530Z-61e1` (12 requests) and full
  `live-20261006T103307Z-660d` (45 requests: 33 sent, 12 reused from the pilot)
- Endpoint: `https://hackathon.api.qloo.com`, direct HTTPS transport, all 45 requests HTTP 200
- Parser: adapter 0.2.0, `verified` against the direct-transport bodies of the pilot
- Evidence excerpt (literal values with request IDs and JSON Pointers):
  [`reports/evidence_excerpt.md`](evidence_excerpt.md). Raw responses stay in
  git-ignored `data/` (regenerate with the commands at the end).

How to read this report: **Observed** lists returned values and counts only.
**Judgment** is MOTIF's interpretation. No motif was annotated, no sensory axis
was set, and no scent was generated.

Separate judgments (brief section 10):

| Question | Judgment |
|---|---|
| Data availability | **High.** All 5 seeds resolved, and all 6 domains returned 10 results with tags, properties, affinity, and explainability. |
| Descriptive sufficiency | **Partial.** Strong for the seed's own descriptor tags and for related brands, movies, and artists. Weak for people (occupations), books (subject matter), unscoped tag insights (venue and payment tags), and places (amenities). |
| Profile differentiation | **High at the level of returned entities**: 0 shared IDs in 55 of 60 seed-pair/domain comparisons. **Moderate at the level of descriptor words**: some descriptors recur across very different seeds (for example `urn:tag:personal_style:qloo:minimalist` on 4 of 5 seeds). |

## 1. Resolution status for all five seeds

**Observed.** Every seed resolved to exactly one `urn:entity:brand` on an exact
name match (case and accents folded). The expected type separated the brand
from same-name places, and for Ralph Lauren also from a person and an author
entity. No override was used, and no seed is untested.

| Seed | Returned name | Returned ID | Same-name candidates not chosen | Source |
|---|---|---|---|---|
| A24 | A24 | `7E904879-87BC-4BA6-B4AB-6E380A4C250D` | 2 places | req 0001 |
| MUJI | Muji | `E12201A5-CC50-40AF-97AE-C54A2CA303F7` | 7 places (stores) | req 0010 |
| Comme des Garçons | Comme des Garcons | `3637BC2E-B2D1-4496-9BD7-938E4FAE81AD` | places | req 0019 |
| Nike | Nike | `C70CE2B8-0AD1-4150-BF18-5A6347F2E860` | places | req 0028 |
| Ralph Lauren | Ralph Lauren | `2723B38E-C3E2-435F-A77B-A94A92D68D07` | 1 person, 1 author, places | req 0037 |

**Judgment.** Brand resolution is reliable for these well-known names. For
other inputs, the expected type remains necessary: the search returns stores
and people with the same name.

## 2. Supported and tested domains, request status, available fields

**Observed.** Each seed used 9 request kinds (`/search`, `/entities`,
`/v2/insights` × 6 entity types, and `/v2/insights` with `filter.type=urn:tag`).
All 45 requests had status `ok`. There were no empty, forbidden, rate-limited, or
unrecognized responses, and no retries.

| Request group | Items | With tags | Descriptive fields seen (literal property names) |
|---|---|---|---|
| seed `/entities` | 5 | 5 | `description`, `short_description`, `industry`, `products`; tags in about 25 `urn:tag:*:qloo` namespaces |
| related `urn:entity:brand` | 50 | 50 | `aesthetic_properties` 50/50, `style_description` 50/50, `emotional_tone` 50/50, `personal_style`, `core_values`, `lifestyle` |
| related `urn:entity:movie` | 50 | 50 | `style_description` 50/50, `emotional_tone_description` 50/50, `genre_description`, `plot_themes_description`, `keywords`; tags mostly `urn:tag:keyword:media` |
| related `urn:entity:artist` | 50 | 50 | `adjectives_for_music` 50/50, `performance_style` 50/50, `characteristics`; tags mostly `urn:tag:style:qloo` |
| related `urn:entity:book` | 50 | 30 | `description`, publication fields; tags `genre:media`, `keyword:qloo`, `style:qloo` |
| related `urn:entity:person` | 50 | 50 | biographical fields; tags `wikipedia_category:wikidata`, `occupation:person` |
| related `urn:entity:place` | 50 | 50 | `ambience_description` 48/50, `physical_setting_description` 48/50; tags `amenity`, `ambience`, `decor` |
| tag insights (`urn:tag`, take 20) | 100 | n/a | `tag_id`, `name`, `types`, `subtype`, `tag_value`, `popularity`, `query.affinity` |

Per related entity, `query.affinity`, `query.measurements.audience_growth`
(absent for books), and `query.explainability` were returned. Each insights
body also carries an aggregate `query.explainability`.

**Judgment.** Every candidate domain from the brief is available under the
hackathon key. The useful field surface is much richer than the documentation
examples suggested. The descriptive `properties` text fields and the
`aesthetic_property`/`style`/`emotional_tone` tag namespaces are not described in
the docs we could read. We do not know how Qloo produces them (see section 8).

## 3. Returned tag and attribute examples with provenance

**Observed.** Each seed's own `urn:tag:aesthetic_property:qloo` tags, copied
literally (req `/results/0/tags` of the seed's `/entities` request):

| Seed | `aesthetic_property` | `emotional_tone` | Source |
|---|---|---|---|
| A24 | Minimalist, High-Contrast, Atmospheric, Raw, Authentic | Provocative, Introspective, Edgy, Sophisticated, Cerebral | req 0002 |
| MUJI | Neutral Color Palette, Natural Materials, Clean Lines, Functional Minimalist Form, Unbranded Packaging | Calm, Practical, Unpretentious, Serene, Functional | req 0011 |
| Comme des Garçons | Deconstructed Silhouettes, Asymmetry, Dark Palette, Conceptual Graphics, Raw Edges | Provocative, Intellectual, Mysterious, Subversive, Sophisticated | req 0020 |
| Nike | Minimalist Logo Design, Technological Aesthetics, Performance-Driven Silhouettes, Dynamic Motion Lines | Bold, Motivating, Energetic, Empowering, Confident | req 0029 |
| Ralph Lauren | Classic Tailoring, Preppy Patterns, Neutral Color Palettes, Signature Polo Logo | Sophisticated, Nostalgic, Refined, Confident | req 0038 |

Related-entity examples:

- MUJI → movie #1 *Still Walking*, `urn:tag:style:qloo`: Warm, Intimate,
  Minimalist, Tender long takes, Knee high framing, Atmospheric (req 0013 `/results/entities/0`).
- A24 → movie #1 *Eighth Grade*, `properties.style_description`: "Quiet,
  observational cinematography blends naturalistic lighting and intimate framing
  with vlog-style inserts to create a confessional, subtly cinematic portrait of
  adolescence." (req 0004 `/results/entities/0/properties/style_description`).
- MUJI → brand #1 Creema, `properties.aesthetic_properties`: Handcrafted,
  Natural Materials, Minimalist, Varied Textures (req 0012 `/results/entities/0`).

More examples for every seed and domain are in the evidence excerpt.

**Judgment.** These are the strongest evidence MOTIF has found: short, literal,
namespaced descriptors of visual style and tone, linked to a stable tag ID.

## 4. Differences and overlap between seed profiles (comparable requests)

**Observed.** Shared returned IDs between seeds, comparing identical request
parameters (10 results per seed per domain). The other 55 of 60 seed-pair/domain comparisons shared none.

| Domain | Pair | Shared | Shared names |
|---|---|---|---|
| artist | Nike / Ralph Lauren | 7 of 13 | Wiz Khalifa, Jay-Z, DJ Khaled, Tyga, Lil' Wayne, 50 Cent, Drake&Orson |
| movie | A24 / Comme des Garçons | 2 of 18 | Lady Bird, The Favourite |
| artist | A24 / Comme des Garçons | 1 of 19 | Blood Orange |
| book | Comme des Garçons / Ralph Lauren | 2 of 18 | Norma Jean; The Truth Will Set You Free, But First It Will Piss You Off! |
| place | Nike / Ralph Lauren | 2 of 18 | ZT The Golden Hotel Barcelona, Meliá Paris La Défense |

Own descriptor tag IDs shared by more than one seed (same ID only):
`personal_style:minimalist` (CDG, MUJI, Nike, Ralph Lauren); `core_value:innovation`
(A24, CDG, Nike); `emotional_tone:sophisticated` (A24, CDG, Ralph Lauren);
`market_archetype:heritage` (CDG, Nike, Ralph Lauren); `market_archetype:mainstream`
(MUJI, Nike, Ralph Lauren); plus 11 IDs shared by two seeds (full list in the
excerpt). No `aesthetic_property` ID was shared by two seeds.

**Judgment.**

- Related-entity lists separate the five seeds clearly.
- The one large overlap (Nike/Ralph Lauren artists, all hip hop) suggests that
  the music domain may reflect a shared audience rather than a shared aesthetic.
- At the descriptor level, the `aesthetic_property` namespace differentiates the
  seeds. The `personal_style`, `core_value`, and `market_archetype` namespaces
  differentiate them less.

## 5. Repeated descriptive patterns across domains (without invented semantics)

**Observed.** These are tag IDs that appear on related entities of two or more
domains for the same seed (identical IDs only; facts sheet section 6):

| Seed | Tag IDs in ≥ 2 domains | Most frequent examples |
|---|---|---|
| A24 | 43 | `style:qloo:intimate` (artist, book, movie; 19 entities), `theme:qloo:identity` (12), `audience:qloo:reflective` (9) |
| Comme des Garçons | 35 | `theme:qloo:identity` (15), `style:qloo:intimate` (11), `style:qloo:atmospheric` (10) |
| Ralph Lauren | 33 | `theme:qloo:fame` (8), `style:qloo:intimate` (7), `style:qloo:raw` (3) |
| Nike | 32 | `style:qloo:dynamic` (5), `style:qloo:energetic` (13), `keyword:qloo:championship` (3) |
| MUJI | 5 | `theme:qloo:love` (10), `theme:qloo:nature` (5), `keyword:qloo:home` (2) |

Cross-domain recurrence is limited to the media domains (movie, artist, book)
and occasionally brand. Brand, person, and place mostly use their own namespaces.

**Judgment.**

- Repeated patterns can be observed by ID without any interpretation, but only
  inside the shared `style`/`theme` namespaces of the media domains.
- MUJI shows few repeats. Its music results are tagged Japanese rock and pop
  (`genre:music` "Japanese" 10/10).
- `style:qloo:intimate` recurs for four of five seeds, so it may be common
  rather than distinctive (see section 6).

## 6. Do globally common results dominate?

**Observed.**

- Related-entity `popularity` is high overall: the median per domain is
  0.93–0.996, except books (0.67). The few IDs shared by two seeds have a slightly higher median than
  unshared ones (for example, artists 0.9989 vs 0.9914).
- Tag insights: all 100 have `query.affinity` between 0.99794 and 1, and
  `popularity` ≥ 0.81. Every seed's top 20 includes place-namespace tags, for
  example "Discover" / "VISA" / "JCB" `urn:tag:credit_card:place`, "Five Star"
  `urn:tag:hotel_rating:place`, and "Esquites" `urn:tag:specialty_dish:place`.
  "Identifies as women-owned" `urn:tag:inclusivity:place` is returned for all 5 seeds.
- `minimalist` appears in the own descriptors of all 5 seeds. For 4 seeds it is
  the same ID (`urn:tag:personal_style:qloo:minimalist`); for A24 it is
  `urn:tag:aesthetic_property:qloo:minimalist`. Related brands carry a
  "Minimalist…" value in `aesthetic_properties` for A24 9/10, MUJI 10/10,
  CDG 3/10, Nike 7/10, and Ralph Lauren 5/10.

**Judgment.**

- Related-entity lists are not dominated by the same globally popular items:
  overlap is near zero.
- Unscoped tag insights are dominated by saturated, generic venue and payment
  tags and are not usable as seed descriptors.
- "Minimalist" is too common in Qloo's descriptor vocabulary to count as
  distinctive evidence alone. A later classifier needs a way to discount such
  descriptors (for example, by their frequency across a reference set of seeds).
  That is a stage-3 design question, not a finding about the seeds.

## 7. Quantitative fields and possible enrichment analysis

**Observed.** Returned numeric fields (full run): `query.affinity` on related
entities, 0.824–0.988 (300 values); `popularity`, 0.0016–1;
`query.measurements.audience_growth`, −1.732 to 1 (250 values, absent for
books); tag-insight `query.affinity`, 0.998–1.

With a single seed signal, every per-entity explainability record (300/300)
attributes a score of 1 to the seed, and every aggregate `avg_score` is 1.

**Judgment.**

- Affinity orders results within one request. It is not comparable across
  requests and is not a percentage of people. Explainability adds nothing with
  a single seed; it may matter later with multiple input signals.
- No valid enrichment or lift can be calculated: there is no population
  denominator. The facts sheet's "sample tag shares" compare frequencies
  between top-10 samples only (for example Nike movies: `style:qloo:kinetic`
  10/10 vs pooled 12/48). These are descriptive and depend on which five seeds
  were pooled.

## 8. Missing semantic information that blocks motif classification

**Observed.**

- No olfactory descriptors were returned. Words like "Fragrance" appear only as
  product or industry tags (`product_service:qloo` "Fragrance" 14×,
  `subsidiary:qloo` "Ralph Lauren Fragrances") or as plot keywords
  (`keyword:media` "Sense of smell", "Perfume").
- No documentation was available to us for the descriptive fields
  (`aesthetic_properties`, `style_description`, `emotional_tone`,
  `adjectives_for_music`, …). It does not say how they are produced, dated, or
  validated.
- Four literal tag names are the string "null" (for example A24
  `urn:tag:personal_style:qloo`, req 0002).
- Books: 20 of 50 returned no tags. People: tags are occupations and Wikipedia
  categories.

**Judgment.**

- The cultural-to-olfactory step remains entirely MOTIF's own design rules, as
  intended. Qloo cannot validate it.
- The descriptive fields read like generated summaries. MOTIF must cite them as
  "Qloo-supplied descriptor" and not as independent ground truth, and must keep
  the literal value and pointer.
- Tags whose literal name is "null" must be treated as absent, not as a style.

## 9. Which MOTIF decisions the evidence could support, and which it cannot

**Could support (with provenance):**

- Choosing which cultural references inform a brief: related brands, movies, and
  artists per seed, distinct across seeds.
- Citing literal descriptors as evidence for a later, separately labelled
  `motif_annotation`.

  As a rough indicator only, here is how often a candidate motif name appears
  as a substring of a descriptor tag name. These are literal substring counts
  over the seed's own tags and related entities in the `aesthetic_property`,
  `personal_style`, `emotional_tone`, `style`, `ambience`, `decor`, and
  `market_archetype` namespaces. They are not annotations, and "natural" also
  matches "Naturalistic":

  | Name | A24 | MUJI | CDG | Nike | RL |
  |---|---|---|---|---|---|
  | intimate | 23 | 14 | 15 | 5 | 10 |
  | experimental | 7 | 2 | 15 | 0 | 0 |
  | natural | 6 | 16 | 7 | 0 | 3 |
  | heritage | 2 | 2 | 6 | 8 | 11 |
  | provocative | 3 | 0 | 8 | 0 | 3 |
  | industrial | 4 | 6 | 4 | 2 | 0 |
  | romantic | 1 | 2 | 3 | 1 | 4 |
  | playful | 2 | 4 | 4 | 0 | 1 |
  | melancholic | 2 | 2 | 0 | 0 | 0 |
  | restrained | 0 | 1 | 1 | 0 | 1 |
  | precise | 1 | 0 | 0 | 0 | 0 |
  | opulent | 0 | 0 | 0 | 0 | 1 |

- A request-to-result explanation for judges: every value is traceable to a
  request and JSON Pointer.

**Cannot support:**

- Any sensory-axis value or scent direction by itself. The five draft rules stay
  inactive, and every axis stays `null` until a motif annotation and rule exist.
- Claims that an audience will like a scent, or that related entities share an
  aesthetic merely because of an affinity.
- Motifs without matching vocabulary in the returned descriptors ("precise",
  "opulent", and "restrained" are nearly absent). Section 8 also limits how much
  weight any descriptor can carry.

## 10. Recommendation: `narrow`

**Why continue:** Access works end to end. All seeds resolve, and every domain
returns rich, namespaced, traceable descriptors. Related-entity profiles are
clearly distinct across seeds. This is a credible basis for explainable
cultural grounding.

**Why narrow rather than continue as planned:**

1. Use as evidence: the seed's own `/entities` tags (`aesthetic_property`,
   `emotional_tone`, `personal_style`, `core_value`), plus related brands
   (`aesthetic_properties`, `emotional_tone`), movies (`urn:tag:style:qloo`,
   `style_description`), and artists (`urn:tag:style:qloo`, `adjectives_for_music`).
2. Drop unscoped tag insights (generic, saturated venue and payment tags), people
   (occupations), and books (subject matter; 40% untagged). Use places only for
   `ambience`/`decor` and with a note that results look location-driven (Nike and
   Ralph Lauren both returned Barcelona and Paris hotels).
3. Treat very common descriptors ("Minimalist", "Intimate") as weak evidence.
   Treat the music domain as possibly audience-driven (Nike/Ralph Lauren hip hop
   overlap; MUJI → Japanese rock).

**Remaining uncertainties:**

- How Qloo generates and updates the descriptive fields.
- Whether a tag-type filter (for example `filter.tag.types`) would make tag
  insights useful; untested.
- Stability over time and across `take` sizes; untested.
- Coverage for less famous inputs (all five seeds are globally known brands).
- Event quota and rate limits; unpublished; the 45 requests sent across both runs
  hit no limit.

These go to stage 3 (`MOTIF_BUILD_SPEC.md`).

## Reproduce

```sh
python3 -m motif_spike check                            # READY (direct transport)
python3 -m motif_spike run --mode live --plan pilot     # 12 requests
python3 -m motif_spike run --mode live --plan full      # reuses identical pilot requests
python3 -m motif_spike excerpt --run latest-live        # reports/evidence_excerpt.md
```

Live results can change over time. Request IDs above refer to the full run
`live-20261006T103307Z-660d`.

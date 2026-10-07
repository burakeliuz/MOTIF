# Weighted motif scoring (`scoring-1.0`)

Phase 4 of the engine refactor. Config: `config/motif_scoring.v1.json`. Code:
`motif/scoring.py`. Offline table on the 13 trial brands:
`python3 tools/engine_compare.py scores` (needs the git-ignored recordings).

## 1. Why

The legacy engine reduces support to a count of distinct source kinds and two
labels (moderate, strong). Very different amounts of evidence get the same
label (Comme des Garçons' provocation on 17 tags and 8 entities is "moderate",
like A24's on 3 tags and 2 entities), and the first identical pair of brands
appears exactly there (MUJI = Aesop). `docs/ENGINE_REDESIGN.md` §2.

## 2. What is counted

The lexicon is unchanged (`lexicon-0.3`): the same annotations, the same
context exclusions and negations. Only roles `support` (in full) and
`context_common_cue` (at a reduced weight) count; `negated` and
`excluded_context` never count.

| Input | How it enters |
|---|---|
| Own entry: distinct supporting cue groups | 1 unit each (the brand's own description is the anchor) |
| Related brands / films / artists: distinct supporting entities | 1 unit each, per source kind |
| Supporting tags beyond those groups or entities | 0.25 unit each (more tags on the same entity add a little) |
| Common cue groups (frozen lexicon-0.3 commonness: intimate, minimalist, playful) | 0.3 unit per group in the own entry; 0.1 unit per related entity whose only match is common |
| Diversity: distinct supporting cue groups and distinct source kinds | (groups − 1) + (kinds − 1) units in a separate channel |
| Related artists | only when the session fetched them (off by default) |

## 3. Formula

For each channel `c` (own, brand, movie, artist, diversity):

    s_c = 1 − exp(−units_c / tau_c)                 saturation, 0 ≤ s_c < 1
    score = 1 − Π_c (1 − weight_c · s_c)             noisy-OR, 0 ≤ score < 1

| Channel | weight | tau | Reading |
|---|---|---|---|
| own | 0.70 | 1 | one own cue group ≈ 0.44 on its own; three ≈ 0.67 |
| brand | 0.55 | 3 | one related brand ≈ 0.16; five ≈ 0.45 |
| movie | 0.35 | 3 | one related film ≈ 0.10; five ≈ 0.28 |
| artist | 0.30 | 3 | only when fetched |
| diversity | 0.20 | 3 | four cue groups from two kinds of source ≈ 0.15 |

Properties, by construction:

- **Bounded and saturating.** No channel reaches its weight, and the score never
  reaches 1. Ten related brands do not count ten times as much as one.
- **Source diversity matters without being a count.** Independent channels
  combine multiplicatively (noisy-OR), and the diversity channel adds credit for
  each further kind of source, so two related brands and two related films score
  higher than four related brands (0.427 vs 0.405 in the tests), although a
  related brand alone still counts more than a related film.
- **Own anchor.** The own entry has the largest weight and the fastest
  saturation: it describes the brand itself.
- **Monotone and smooth.** Adding evidence never lowers a score; removing one
  entity changes it by a bounded amount (measured below).
- **Deterministic.** Same annotations and config give the same scores (rounded
  to 6 digits for output only).

What the score is not: not a probability, not a percentage, not "how much" a
brand is a motif. It is a design quantity used to weight motifs in the
continuous sensory engine and to rank them in the profile. The product shows
words, not these numbers; numbers stay in the technical JSON.

## 4. Offline results on the 13 brands

Phase 4 checks (scores, inputs, legacy strength):

| Check | Result |
|---|---|
| A24 vs Comme des Garçons, provocation | 0.699 (own 2 groups, 1 related entity) vs 0.863 (own 3 groups, 7 entities, 4 groups); legacy: both "moderate" |
| Gucci vs Balenciaga, provocation | 0.643 (own 1, 2 entities) vs 0.838 (own 2, 6 entities, 4 groups); legacy: both "moderate" |
| MUJI vs Aesop | MUJI: restraint 0.799 > precision 0.758 > naturalness 0.728; Aesop: precision 0.774 > restraint 0.645 > naturalness 0.631. Legacy: the same three active motifs, identical targets |
| Ralph Lauren, heritage | 0.669 (own + 2 related brands); leads with precision 0.754 |
| Harley-Davidson, heritage | 0.556 (own + 1 related brand), its top motif |
| Sanrio, playfulness | 0.719 (own + 3 related brands); legacy "moderate" |

Stability: removing any single related entity changes a motif score by at most
0.233 (Patagonia's precision, which rests on one related brand with two cue
groups); for motifs at or above the lead level of 0.3 the largest change is
0.195; the median change over all motifs is 0.056. Motifs carried by a single
related entity (score 0.156) disappear when that entity is removed, as they
should: they are minor signals and never lead a result.

Known limits:

- Scores inherit the lexicon's coverage: a brand whose own descriptors fall
  outside the 47 cue groups (Nike) still gets little.
- Related evidence is volume-dominated (about 94% of read items); saturation and
  the lower related weights limit, but do not remove, that confound.
- Common cues still give every brand a small floor on intimacy, restraint, and
  playfulness (0.01–0.28 when nothing else supports them). These motifs are
  flagged `common_only` and never lead a result.
- Weights and taus are design choices calibrated by inspection on these 13
  brands, then frozen for the pre-registered holdout (phase 7).

The full per-brand table (every motif, score, own cue groups, related entities, cue groups, source kinds, legacy strength, and the largest change when one related entity is removed) is `reports/motif_scores.md`.

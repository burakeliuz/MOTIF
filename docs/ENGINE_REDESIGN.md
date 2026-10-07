# Engine redesign: from five binary rules to a continuous sensory model

Status: phase 2 of the engine and product refactor (2026-10-07). This document
fixes the baseline and the goals before any new model is built. Later phases
add their results to the sections marked "filled in later".

## 1. Baseline (frozen)

The legacy engine stays in the repository unchanged and remains runnable; it is
the comparison point for every later claim.

| Part | Version | What it does |
|---|---|---|
| Engine | `engine-0.3` | `motif/engine.py` → `classify.py` → `translate.py` → `materials.py` |
| Lexicon | `lexicon-0.3` | 12 motifs, 47 cue groups (54 variants), read namespaces: own `aesthetic_property`, `personal_style`, `emotional_tone`; related brands `aesthetic_property`, `emotional_tone`; films and artists `style` |
| Support | lexicon-0.3 `support` | strength = number of distinct source kinds with a non-common cue; anchors own/brand; *strong* ≥ 3 kinds, *moderate* ≥ 2 kinds or own with ≥ 2 cue groups; active = strong or moderate |
| Rules | `draft-0.2` | R1 restrained → light, R2 intimate → intimate, R3 precise → polished, R4 opulent → dense, R5 natural → natural; 7 motifs unmapped |
| Palette | `palette-0.3` | 8 materials, 7 with verified properties |
| Parameters | `params-0.1` | composition needs ≥ 2 targets; fill to 3; slots top 1, heart 2, base 2 |

Frozen record: `reports/baselines/legacy_engine_0.3.json`, written by
`tools/legacy_baseline.py`. It holds, for each of the 13 trial brands, the set
kept at every stage, plus the SHA-256 of the four legacy config files.
`tests/test_legacy_baseline.py` fails if a legacy config file changes without a
version bump, and, when the git-ignored recordings are on disk, if a replay no
longer gives the frozen sets.

Independent reproduction (phase 2, from the stored live responses, no network,
no LLM; stage definitions written fresh in `tools/legacy_baseline.py`):

| Stage | Distinct per-brand sets / 13 |
|---|---|
| Qloo descriptors MOTIF consumes | 13 |
| Lexicon cue groups matched | 13 |
| Active motifs | 12 |
| Sensory targets | 7 |
| Eligible materials | 7 |
| Selected materials | 3 |

This matches `reports/collapse_analysis.md` (13/13/12/7/7/3).

## 2. Problems demonstrated

From `reports/collapse_analysis.md` (measured on the same 13 brands):

1. **Binary activation discards graded evidence.** 243 support items on 202
   entities become 99 counted source kinds and two strength labels. Comme des
   Garçons' provocation (17 items, 8 entities, 4 cue groups) and A24's (3 items,
   2 entities) get the same label. First identical pair: MUJI = Aesop.
2. **One motif → one pole loses most motifs and most dimensions.** Only 18 of 30
   active motifs (60%) have a rule. Four brands (A24, Nike, Harley-Davidson,
   Sanrio) end with no direction and become identical. Only 4 of 12 poles are
   ever reached; temperature, projection, and sweetness are unknown for all 13.
   Brands with the same mapped subset get the same targets regardless of
   everything else (Comme des Garçons = Balenciaga; Ralph Lauren = Gucci).
3. **Composition gate and a small palette compress further.** The two-target
   gate empties four brands that have a direction; fill-to-three merges Le Labo
   into MUJI/Aesop; 7 verified materials, 2–4 eligible per profile. 7 → 3.
4. **Narrow reading.** 5% of returned tags are in the namespaces MOTIF reads;
   81% of what is read matches no cue. This limits richness but not
   distinctness (all 13 brands stay distinct through the lexicon stage).
5. **Related references dominate the read evidence** (about 94% of items), so any
   volume-based weight is confounded by how many related entities happen to
   carry a cue.

## 3. What the new engine must improve

The continuous engine (phases 3–5) replaces the five binary rules as the
primary engine. It must:

1. **Keep graded motif support.** A deterministic, bounded 0–1 motif score with
   saturation (phase 4, `config/motif_scoring.v1.json`), built from what the
   lexicon already annotates: distinct own cue groups, distinct related
   entities, source diversity, an own-entry anchor, a commonness penalty.
2. **Let every motif speak on several dimensions, or on none.** A researched
   12 × 6 motif-to-sensory model (phase 3) where a cell is a signed value in
   [-1, 1] with confidence and evidence type, or `null` when nothing supports a
   relation. No cell is forced.
3. **Aggregate continuously and keep the trace.** Per dimension, the
   score-weighted contributions of the motifs that have a value there (null
   contributes nothing), with contributors, magnitudes, agreement, and conflicts
   kept. A near-cancellation is reported as low confidence ("balanced, open"),
   never as a confident neutral.
4. **Not collapse brands that differ in their evidence.** Measured on the same
   13 brands against the frozen baseline (phase 6): distinct profiles, pairwise
   distances, dimension coverage, unresolved share, collisions, and stability
   under small perturbations.
5. **Stay traceable end to end.** Qloo descriptor → motif → score →
   contribution → dimension, with no LLM anywhere in the chain.
6. **Feed an olfactory layer instead of a fixed 7-material list.** The scent
   architecture (phase 8) is matched deterministically from the continuous
   target; supplier materials become optional references with their identity
   and source, not the sensory authority.

## 4. What it must NOT claim

- **Not perception science.** Motif-to-sensory values are MOTIF's creative
  mapping, informed where possible by crossmodal and perfumery literature and
  labelled by evidence type. A cell supported only by MOTIF's reasoning says so.
- **Not a formula.** No ingredients with doses, no proportions, no safety or
  regulatory statements. Material references are examples of a class.
- **Not a preference prediction.** Nothing says who will like the scent;
  related brands and films are "references Qloo relates to" a brand, never an
  audience.
- **Not objective correctness.** Better separation between brands is not proof
  that a direction is right. Differentiation is measured, not validated against
  a ground truth (none exists).
- **Not certainty where evidence is thin.** Unknown is a valid answer; low
  confidence stays visible as "open to the perfumer".
- **Not a percentage or a lift.** Scores are bounded design quantities shown as
  words in the product; exact numbers stay in the technical JSON.

## 5. Results (filled in later)

Phase 6 (13-brand diagnostic), phase 7 (pre-registered holdout), and phase 10
(final validation) add their numbers here.

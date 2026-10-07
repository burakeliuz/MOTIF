# Continuous engine analysis: 13 trial brands, legacy vs continuous

Phase 6 of the engine refactor, offline, 2026-10-07. **No Qloo request, no LLM
call.** The 13 brands of `reports/trial_6b.md` are replayed from their stored
live responses (`RecordedQloo`); both engines read exactly the same evidence
(own entry, related brands, related films for every brand). Legacy =
`engine-0.3` (rules `draft-0.2`, frozen baseline, `reports/baselines/`).
Continuous = `continuous-1.0` with `scoring-1.0`, `sensory-1.0` (r2), and
`continuous-params-1.0`. Reproduce (needs the git-ignored recordings):

```sh
python3 tools/engine_compare.py analysis --markdown /tmp/a.md --json /tmp/a.json
python3 -m motif compare-engines --reference MUJI --recorded live-20261006T103307Z-660d
```

Two runs give byte-identical JSON (deterministic).

Definitions. A **profile** is the set of resolved labels over the six
dimensions (open otherwise); the legacy profile is its target set. **Commitment**
per dimension = value × confidence when resolved, 0 when open (legacy: pole sign ×
evidence weight 1.0 strong / 0.6 moderate). Distances are Euclidean between
commitment vectors; the two engines use different scales, so the scale-free row
(pairs closer than a quarter of the engine's own median distance) is the fair
comparison. **Tentative** = a dimension that rests only on low-confidence cells
(MOTIF design opinion); the **ablation** row removes all such cells.

## 1. Results

### C.1 Distinct profiles and distances (13 brands)

| Measure | Legacy (engine-0.3) | Continuous (continuous-1.0) |
|---|---|---|
| Distinct sensory profiles (resolved labels) | 7 | 11 |
| … with the confidence word, open vs balanced-open | | 11 |
| … with the medium-confidence cells only (ablation: no tentative cells) | | 9 (identical: MUJI = Aesop; Nike = Sanrio; Ralph Lauren = Harley-Davidson = Balenciaga) |
| Distinct final outputs | 3 (selected materials) | not applicable before phase 8 (scent architecture) |
| Identical-profile groups | MUJI = Aesop; A24 = Nike = Harley-Davidson = Sanrio; Comme des Garçons = Balenciaga; Ralph Lauren = Gucci | A24 = Supreme; Comme des Garçons = Balenciaga |
| Mean pairwise distance (commitment vectors) | 0.8748 | 0.2869 |
| Pairs at distance 0 | 7 of 78 | 0 of 78 |
| Pairs closer than a quarter of the median distance (scale-free) | 7 | 2 |
| Closest pair (continuous) | | A24 – Supreme (0.0544) |
| Unresolved dimensions (share of 78) | 0.795 | 0.526 |

### C.2 Dimension coverage (brands with a resolved dimension / target)

| Dimension | Legacy | Continuous |
|---|---|---|
| Temperature | 0 | 5 |
| Weight | 6 | 5 |
| Texture | 7 | 7 |
| Impression | 3 | 6 |
| Projection | 0 | 5 |
| Sweetness | 0 | 9 |

### C.3 Per brand (continuous)

| Brand | Outcome | Leading motifs (score) | Temperature | Weight | Texture | Impression | Projection | Sweetness | Legacy targets |
|---|---|---|---|---|---|---|---|---|---|
| MUJI | direction | restrained 0.80, precise 0.76, natural 0.73, heritage 0.44 | slightly cool · tentative | light · supported | slightly polished · supported | natural · supported | open | slightly dry · tentative | light, polished, natural |
| A24 | direction | provocative 0.70, restrained 0.45 | slightly warm · tentative | open, pulls both ways | slightly raw · tentative | open | open, pulls both ways | slightly dry · tentative | none |
| Comme des Garçons | direction | provocative 0.86, experimental 0.86, precise 0.60, restrained 0.37 | open, pulls both ways | open, pulls both ways | open, pulls both ways | slightly synthetic · tentative | slightly projecting · tentative | slightly dry · tentative | polished |
| Nike | insufficient_evidence | none | open | open | open | open | open | open | none |
| Ralph Lauren | direction | precise 0.75, heritage 0.67, opulent 0.35, provocative 0.35, restrained 0.32 | open, pulls both ways | open, pulls both ways | slightly polished · supported | open | slightly projecting · tentative | open, pulls both ways | dense, polished |
| Le Labo | direction | restrained 0.68, precise 0.66, industrial 0.44, heritage 0.31 | slightly cool · tentative | open, pulls both ways | slightly polished · supported | natural · tentative | open | slightly dry · tentative | light, polished |
| Patagonia | direction | natural 0.56 | open | open | open, pulls both ways | natural · supported | open | slightly dry · tentative | natural |
| Aesop | direction | precise 0.77, restrained 0.65, natural 0.63 | slightly cool · tentative | slightly light · supported | slightly polished · supported | natural · supported | open | slightly dry · tentative | light, polished, natural |
| Supreme | direction | provocative 0.72, restrained 0.48 | slightly warm · tentative | open, pulls both ways | slightly raw · tentative | open | open, pulls both ways | slightly dry · tentative | light |
| Gucci | direction | precise 0.66, provocative 0.64, opulent 0.53, heritage 0.49 | open, pulls both ways | dense · supported | slightly polished · supported | open | slightly projecting · tentative | open, pulls both ways | dense, polished |
| Harley-Davidson | direction | heritage 0.56, provocative 0.44, precise 0.38, industrial 0.35 | open, pulls both ways | slightly dense · tentative | open, pulls both ways | open | open | slightly dry · tentative | none |
| Sanrio | direction | playful 0.72 | open | slightly light · tentative | open | open | slightly projecting · tentative | open | none |
| Balenciaga | direction | provocative 0.84, precise 0.81, experimental 0.58, industrial 0.56, restrained 0.48, opulent 0.47, heritage 0.33 | open, pulls both ways | open, pulls both ways | open, pulls both ways | slightly synthetic · tentative | slightly projecting · tentative | slightly dry · tentative | polished |

### C.4 Named pairs

| Pair | Legacy distance | Continuous distance | Same resolved labels |
|---|---|---|---|
| MUJI – Aesop | 0.4 | 0.2326 | no |
| MUJI – Le Labo | 0.8246 | 0.4555 | no |
| A24 – Supreme | 0.6 | 0.0544 | yes |
| Gucci – Balenciaga | 0.7211 | 0.3006 | no |
| Ralph Lauren – Harley-Davidson | 0.8485 | 0.2459 | no |
| Sanrio vs nearest (Nike) | | 0.1067 | |

### C.5 Stability

| Brand | Related entities | Max move, one entity removed | Mean move | Label changes | Minor contributing motif dropped (score < 0.3) | Move | Label change |
|---|---|---|---|---|---|---|---|
| MUJI | 20 | 0.0124 | 0.004 | 0 | — (0.00) | 0 | no |
| A24 | 20 | 0.0787 | 0.0047 | 2 | opulent (0.10) | 0.0481 | yes |
| Comme des Garçons | 20 | 0.0283 | 0.0025 | 0 | opulent (0.10) | 0.0283 | no |
| Nike | 20 | 0.0 | 0.0 | 0 | — (0.00) | 0 | no |
| Ralph Lauren | 20 | 0.2232 | 0.0203 | 5 | — (0.00) | 0 | no |
| Le Labo | 20 | 0.1249 | 0.0156 | 3 | natural (0.16) | 0.126 | yes |
| Patagonia | 20 | 0.0749 | 0.0066 | 1 | industrial (0.16) | 0.0142 | no |
| Aesop | 20 | 0.1231 | 0.015 | 2 | experimental (0.16) | 0.0911 | no |
| Supreme | 20 | 0.0957 | 0.0077 | 2 | experimental (0.16) | 0.0211 | yes |
| Gucci | 20 | 0.0431 | 0.0076 | 0 | industrial (0.16) | 0.027 | no |
| Harley-Davidson | 20 | 0.0097 | 0.0015 | 0 | — (0.00) | 0 | no |
| Sanrio | 20 | 0.0038 | 0.0007 | 0 | — (0.00) | 0 | no |
| Balenciaga | 20 | 0.0677 | 0.0117 | 3 | — (0.00) | 0 | no |

### C.6 Share of all contributions by motif (13 brands)

| Motif | Share |
|---|---|
| precise | 0.261 |
| provocative | 0.232 |
| restrained | 0.146 |
| opulent | 0.116 |
| natural | 0.112 |
| industrial | 0.070 |
| experimental | 0.034 |
| intimate | 0.014 |
| playful | 0.014 |

## 2. Answers

1. **Did the continuous model reduce collapse?** Yes, measurably. Distinct
   sensory profiles 7 → 11 of 13; pairs at distance 0: 7 → 0; scale-free near
   pairs 7 → 2; unresolved dimensions 80% → 53%. The legacy "no direction" group
   (A24, Nike, Harley-Davidson, Sanrio) splits: A24, Harley-Davidson, and Sanrio
   receive different leanings; Nike stays empty and is reported as insufficient
   evidence (only common cues). MUJI and Aesop no longer coincide (MUJI: light,
   natural, both supported; Aesop: slightly light, natural, with weaker cool and
   polished leanings), and neither do Ralph Lauren and Gucci (Gucci: dense,
   supported; Ralph Lauren: open on weight).
2. **Is the differentiation artificial?** Partly, and it is labelled. With the
   medium-confidence cells only (the five legacy links, now graded) there are 9
   distinct profiles; the remaining two distinctions come from tentative cells
   that the product must show as tentative. Absolute distances are small (mean
   0.29), and much of the separation comes from graded motif scores rather than
   from new claims. The two remaining collisions (A24 = Supreme; Comme des
   Garçons = Balenciaga) mirror nearly identical motif profiles (provocation 0.70
   / 0.72 with restraint 0.45 / 0.48; provocation, experimentation, precision in
   both): the engine does not force them apart. Separating them would need more
   of Qloo's evidence to be read (lexicon coverage), not a different sensory
   model.
3. **Which dimensions separate brands?** Texture (polished vs raw vs open, 7
   brands resolved), impression (natural vs synthetic, 6), temperature (cool vs
   warm, 5), weight (light vs dense, 5), projection (5, always projecting).
   Sweetness resolves for 9 brands but always as "slightly dry · tentative", so
   it separates little.
4. **Do some motifs dominate?** Precision (26% of all contributions) and
   provocation (23%) carry about half; restraint 15%, opulence 12%, naturalness
   11%. Precision is frequent in related fashion references; its polished leaning
   is medium-confidence (legacy R3), its cool leaning tentative.
5. **Are some dimensions or poles still unused?** No dimension is unused (legacy:
   temperature, projection, sweetness never reached). Poles never resolved on
   these 13 brands: sweet (only opulence leans sweet, weakly, and it is
   outweighed), intimate (no brand has a strong intimate motif; common cues are
   context only). Polished and cool come from precision alone.
6. **Is it stable?** Removing any single related entity moves a brand's
   commitment vector by at most 0.22 (Ralph Lauren) and on average by at most
   0.03. Labels change in 0–5 of 20 removals per brand: brands whose motifs pull
   both ways sit near the agreement and mass thresholds (Ralph Lauren 5, Le Labo
   3, Balenciaga 3). Dropping the weakest minor motif (score < 0.3) changes a
   label for 3 brands (A24, Le Labo, Supreme). Wording is therefore less stable
   than the underlying numbers, which argues for showing confidence words and
   "pulls both ways" rather than hiding borderline cases.

## 3. Gate

The model is not collapsing: profiles, distances, coverage, and unresolved share
all improve on the frozen baseline, and the remaining collisions are explained
upstream (motif profiles), not by the sensory model. Gate passed; the scent
architecture (phase 8) may be built. Weaknesses carried forward, not tuned away
on these 13 brands (that would be fitting the test set):

- a tentative dry bias (9 of 13 brands lean "slightly dry"; no sweet result);
- precision and provocation dominate; restraint/precision/naturalness brands
  remain close (MUJI, Aesop, Le Labo) even if no longer identical;
- label flips near thresholds for brands with opposed motifs;
- lexicon coverage still decides what can be read (Nike gets nothing).

The phase 7 holdout tests these parameters, frozen, on five new brands.

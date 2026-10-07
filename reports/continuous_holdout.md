# Continuous engine holdout (pre-registered)

Phase 7 of the engine refactor. **Part A is the pre-registration. It is
committed before any Qloo request of this holdout is sent; nothing in it is
changed after the results are seen.** Part B (results) is added in a separate
commit.

## Part A — pre-registration (2026-10-07)

### A.1 Purpose

Test the continuous engine, frozen as built and calibrated on the 13 trial
brands, on five brands it has never seen: does it resolve them, read motifs,
give them distinct and traceable profiles, without structural failure?

### A.2 Brands and reasons

None of these was ever researched by MOTIF. Some appear in stored responses only
as related entities of other brands (for example Hermès among Gucci's and
Balenciaga's related brands, LEGO among Sanrio's); they were never a seed, and no
rule, lexicon, or parameter was set with them in view. Mix: five industries, not
five fashion labels.

| Brand | Industry | Role in the mix |
|---|---|---|
| IKEA | home furnishings | mass market; design-led |
| Hermès | luxury leather goods and fashion | luxury |
| Bang & Olufsen | consumer electronics | design-led |
| LEGO | toys | playful / cultural |
| Coca-Cola | beverages | mass market; cultural icon |

### A.3 Frozen versions

Code at commit `f300cd3` (phase 6) plus the harness committed with this file;
`lexicon-0.3`, `scoring-1.0`, `sensory-1.0` (revision r2),
`continuous-params-1.0`, `continuous-1.0`. Legacy `engine-0.3` is not used here.
No parameter, cell, threshold, lexicon entry, or rule may change between this
commit and part B. If a bug is found while evaluating, it is reported in part B
and the results stay as produced by the frozen code.

### A.4 Procedure and budget

- `python3 tools/holdout_run.py live`, brands in the order above. Live access
  through `motif/qloo.py` `LiveQloo` with motif_spike's `DirectTransport` against
  `https://hackathon.api.qloo.com`; nothing else.
- One access object per brand with a hard cap of **4 network attempts**
  (retries included): search, the brand's own entry, related brands, related
  films. Total at most **20**. If a retry consumes the budget, the brand is
  evaluated on what was fetched and the stop is reported; no second run.
- Entity choice, if Qloo returns several candidates: the first returned brand
  whose name equals the input after folding case and accents; otherwise the
  first returned brand; otherwise the brand is unresolved. The repeated search
  is served from the session cache (no extra request).
- **No LLM call.** Raw responses are recorded in the git-ignored
  `data/motif_sessions/holdout-*/`; evaluation replays them offline
  (`python3 tools/holdout_run.py evaluate RUN_DIR`).
- A failed request is never replaced by recorded data, another endpoint, or
  another credential.

### A.5 Criteria (reported for every brand)

| # | Criterion | Measured as |
|---|---|---|
| C1 | Resolution | resolved to a brand entity within the budget; the rule's choice, if used |
| C2 | Motif coverage | number of leading motifs (score ≥ 0.3, not common-cue only); list of motif scores |
| C3 | Differentiation | distinct resolved-label profiles among the five; nearest of the 13 trial brands (commitment distance) and any identical profile |
| C4 | Traceability | every contributor of every resolved dimension maps to support annotations, evidence items, request IDs, and JSON pointers (automated) |
| C5 | Semantic misreads | manual reading of every supporting descriptor of each leading motif; a descriptor whose meaning does not fit the motif counts as a misread; rate reported |
| C6 | Stability | largest commitment move and label changes when any one related entity is removed |
| C7 | Failures | request failures, budget stops, unresolved names, no data |
| — | Determinism | two evaluations of the same recordings give identical results |

**Structural failure** (blocks the phase 13 merge): an exception in the engine;
a non-deterministic result; an untraceable contributor (C4); a cell forbidden by
the model rules appearing in a result; a "supported" or "firm" word on a dimension
that rests only on low-confidence cells; or fewer than 4 of 5 brands resolved
(C1) for reasons inside MOTIF (Qloo outages are reported, not counted). Weak
coverage, misreads, collisions, and instability are findings to report, not
structural failures.

### A.6 No predictions

No expectation is recorded about which motifs, dimensions, or leanings any of
these brands should receive.

## Part B — results (2026-10-07, after the run)

Run `data/motif_sessions/holdout-20261007T123346Z` (git-ignored), started after
the pre-registration commit `ba7fea1`; frozen code, no parameter changed. **17
network attempts in total** (budget 20), no failed request, no retry, **no LLM
call**. Evaluation: `python3 tools/holdout_run.py evaluate RUN_DIR` (offline).

### B.1 Per brand

| Brand | C1 resolution | Requests | C2 leading motifs (score) | Profile (resolved · confidence; other dimensions open) | C6 one entity removed: max move, label changes |
|---|---|---|---|---|---|
| IKEA | **unresolved**: the 10 search results were all IKEA stores (`urn:entity:place`), no brand entity; the rule found no brand | 1 | — | — | — |
| Hermès | resolved (single match) | 4 | heritage 0.82, precision 0.64, opulence 0.54, restraint 0.43, provocation 0.43 | texture slightly polished · supported; projection slightly projecting · tentative; temperature, weight, sweetness pull both ways | 0.071, 2 of 20 |
| Bang & Olufsen | resolved (single match) | 4 | precision 0.87, restraint 0.63, heritage 0.58, industrial 0.45 | weight slightly light · supported; texture slightly polished · supported; temperature slightly cool · tentative | 0.055, 0 of 20 |
| LEGO | resolved by the pre-registered rule: first returned brand, "The Lego Group" (no exact "LEGO" brand among the candidates) | 4 | playfulness 0.35 | texture slightly polished · tentative (from two minor motifs only); weight pulls both ways | 0.024, 3 of 20 |
| Coca-Cola | resolved (single match) | 4 | heritage 0.31 | texture slightly polished · tentative (from three minor motifs only) | 0.031, 1 of 20 |

C4 traceability: every contributor of every resolved dimension maps to support
annotations, evidence items, request IDs, and JSON pointers (4 of 4 brands).
Determinism: two evaluations identical (4 of 4). No dimension reads "supported"
or "firm" on low-confidence cells alone; no forbidden cell appears.

### B.2 Differentiation (C3)

- Among the four resolved brands, **3 distinct profiles**: LEGO and Coca-Cola
  share the same resolved labels (both only "texture slightly polished,
  tentative"; commitment distance 0.012).
- Against the 13 trial brands: **Hermès has the same resolved profile as Ralph
  Lauren** (distance 0.097); LEGO and Coca-Cola are nearest to Nike (0.015,
  0.027), the trial brand with no direction; Bang & Olufsen is distinct (nearest
  Ralph Lauren, 0.184).

### B.3 Semantic misreads (C5), manual reading

All 59 supporting descriptors of the leading motifs were read. **5 misreads
(8%)**:

| Brand / motif | Descriptor (entity) | Why it is a misread |
|---|---|---|
| Bang & Olufsen / industrial | "Industrial Design" (Mark Levinson), "Industrial Design" (Sonos) | the design discipline, not an industrial aesthetic |
| Bang & Olufsen / industrial | "Industrial Precision" (Bowers & Wilkins) | manufacturing precision, not an industrial look |
| Bang & Olufsen / precision | "Precision cut" (film *Steve Jobs*) | an editing technique the context rules do not catch |
| Hermès / precision | "Meticulous practical effects" (film *The Shape of Water*) | a production technique |

Bang & Olufsen's industrial motif (0.45) rests mostly on misreads (3 of 5); its
industrial cells are low-confidence, so the effect on the profile is small, but
the motif would be shown in the cultural profile.

### B.4 Coverage (C2) and other findings

- **LEGO's own entry is outside the lexicon**: "Modular Geometry",
  "Interlocking Texture", "Vibrant Primary Colors", "Creative", "Nostalgic" match
  no cue; "Playful" matches the playful cue but counts at the reduced
  common-cue weight because "playful" was common in the five stage-2 reference
  brands. Playfulness reaches 0.35 mostly through two related films.
- **Coca-Cola**: only heritage leads (0.31, two related brands); heritage
  carries no sensory claim in `sensory-1.0`, so the profile is nearly empty.
- **Minor motifs can resolve a dimension**: for LEGO and Coca-Cola the only
  resolved dimension comes from motifs below the lead level (precision 0.16 on
  one related brand), shown as tentative. The `min_mass` of 0.05 allows this.
- **IKEA**: MOTIF's search sends no entity type, so ten store locations crowd out
  the brand. The adapter supports a type filter (`search_argv(..., type_hint)`),
  but MOTIF does not use it.

### B.5 Verdict

**No structural failure** (pre-registered definition): no engine exception, no
non-determinism, no untraceable contributor, no forbidden cell, no overclaimed
word, and 4 of 5 brands resolved. Findings, not failures, that limit the product:
weak coverage for brands whose descriptors fall outside the 47 cue groups
(LEGO, Coca-Cola), one cross-set collision (Hermès = Ralph Lauren), one in-set
collision (LEGO = Coca-Cola), an 8% misread rate concentrated on
"industrial design", and IKEA unresolved by an untyped search. None of these is
fixed in this phase; candidate fixes (typed search with a fallback, context rules
for "industrial design" and film techniques, a commonness set that is not
fashion-heavy, a lead-level floor for resolving a dimension) are listed for the
owner in `docs/ENGINE_REDESIGN.md` and would need their own version bumps and a
new holdout.

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

## Part B — results

(Added in a separate commit after the run.)

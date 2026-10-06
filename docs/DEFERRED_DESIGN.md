# Deferred design (documented now, not implemented in the spike)

Brief sections 6 and 11 ask for these to be written down before the engine
exists. Nothing here runs in the playground.

## Worked example: regression expectations for the later engine

Source of truth: `config/draft_rules.json` → `worked_example` (inactive, synthetic).

Fixtures B1 (brand), F1 (movie), and M1 (music artist) are hand-written,
labelled synthetic, and carry manually assigned motifs. With the
demonstration-only support threshold of two distinct domains:

- Domain support: restrained 3, precise 2, intimate 1.
- Active motifs: restrained, precise.
- Qualitative targets: `light_dense` toward light (R1), `raw_polished` toward polished (R3).
- Unknown (null): `warm_cool`, `natural_synthetic`, `intimate_projecting`, `sweet_dry`.
- Materials: not selected.

When the engine is built, its tests must show:

1. Reordering fixtures does not change the result.
2. Duplicating B1 within the same domain adds no domain support.
3. Removing F1 drops precise to one domain, so polished becomes unknown.
4. Intimate (1 domain) does not reappear through restrained: the old
   `restrained → intimate` rule is removed, and projection belongs only to R2.
5. Unknown axes are written as unknown in the brief, never as neutral values.

The threshold of 2 is a demonstration parameter. Multiple domains are not
necessarily independent evidence.

## Later evaluation: seed-only baseline vs Qloo-enriched

Purpose: show what Qloo contributes without treating "a different answer" as proof of improvement.

Hold fixed: motif vocabulary, `draft_rules.json` version, annotation method
and prompt version, brief template, and seeds.

Runs per seed:

1. **Baseline**: interpretation from the seed name alone. Every motif claim is
   recorded as `motif_annotation` with method `model_inference` or `manual`,
   explicitly not Qloo evidence.
2. **Enriched**: the same process, allowed to cite only `qloo_observation`
   evidence IDs from a live run.

Record per seed:

- which observations substantiate, contradict, or change each motif decision;
- which sensory targets change, which stay the same, and which stay unknown in both;
- motif claims in the baseline that the enriched run cannot support (candidates for model memory);
- evidence gaps: motifs no returned field speaks to.

Read-out rules:

- A changed output alone is not an improvement. Qloo may add value by
  substantiating, by contradicting, or by exposing an unsupported claim.
- Report counts with denominators and the seeds involved. No significance
  claims from five seeds.
- No fragrance-preference or audience-acceptance claim follows from either run.

## Stage-3 decisions deferred (2026-10-06)

Decided items live in `MOTIF_BUILD_SPEC.md`. The items below were consciously
left open. Each states why and the smallest step that would unblock it.

| Item | Why deferred | Smallest next step |
|---|---|---|
| Rules for the seven unmapped motifs (experimental, provocative, heritage, industrial, playful, melancholic, romantic) | No justified sensory mapping; the draft-0.2 notice forbids shortcuts such as heritage → warm | Write one candidate rule with its rationale and "decides nothing about" list, review it against Comme des Garçons and A24 evidence, and bump the rules version |
| An `intimate` path (R2) | "intimate" style tags appear for all five reference seeds, so lexicon-0.1 treats them as context; no palette entry has an `intimate` profile | Find a non-common cue set for closeness in held-out data (task T1), and a sourced material whose supplier descriptor supports skin-close use |
| Multi-reference input (2–3 references) | Support counting across seeds (are two seeds' own tags two anchors?) is undesigned and untested | Define per-seed anchors and a merge rule, and test on two recorded seeds |
| LLM suggestions for descriptors the lexicon misses | Would reintroduce non-determinism into classification | A suggestion-only UI: the user accepts a suggestion, it is stored as a `manual` annotation, and it is never applied automatically |
| People, books, places, and scoped tag insights | Stage 2 found occupations, subject matter, location effects, and generic venue tags | Test `filter.tag.types` scoping and place `ambience`/`decor` on two recorded seeds before adding any domain |
| Commonness reference set | Five seeds is a small reference; one query must not define its own reference | Extend the frozen reference with the T1 held-out brands and bump the lexicon version |
| Material palette beyond 8 entries | Only sourced entries are allowed; descriptors not yet read in full | Task T2 (full supplier pages), then add entries only with a source and an uncertainty note |
| Shipping recorded Qloo values in the public demo | Event data terms are unclear | The owner asks the organizers; until then recorded mode is off in the public build |

### Critical gaps that the spec does not paper over

- **Lexicon validation.** All numbers in `reports/design_examples.md` come
  from the five seeds the lexicon was written on. Smallest step: task T1
  (≤ 10 Qloo requests, owner's OK).
- **Material descriptors.** They are search excerpts of supplier pages.
  Smallest step: task T2 (read 8 pages in full, or the owner checks them manually).
- **Official rules.** They were read through search excerpts only. Smallest
  step: the owner opens qloo.devpost.com and confirms the hosted-demo rule,
  the criteria, and the deadline.

## Stage-4 items deferred (2026-10-06)

| Item | Status | Smallest next step |
|---|---|---|
| Bounded LLM tool selection | Proposed, not implemented (the owner limited the LLM to text) | If approved: the LLM picks among the controller's allowed actions; code keeps the budget, allow-list, returned-ID rule, and stop conditions; the trace marks LLM-chosen steps |
| LLM phrasing of questions | Template questions only | Same validator pattern as prose; options are always rendered by code |
| T2 material verification | Blocked: supplier domains denied by the environment network policy | The owner allows the supplier domains (or checks 8 pages by hand); then set `verified_full_page` per property with URL, date, and supporting text (palette-0.3) |
| Lexicon changes suggested by T1 | Proposed in `reports/holdout_t1.md` §2.5, not applied | Apply as lexicon-0.3 and evaluate on fresh held-out brands (T1 brands are no longer independent) |
| Cross-session cache | In-session cache and explicit recorded replay only | Decide with hosting (stage 5): key by transport, base URL, and full request signature; label cached results with their fetch time |
| Publishing recorded Qloo data | Unresolved: the kit's API_ACCESS.md does not address it | The owner asks the organizers; until then the public demo has no recorded mode |

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

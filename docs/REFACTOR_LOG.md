# Engine and product refactor log (2026-10-07)

One entry per phase of the full engine and product refactor. Each phase runs its
offline tests, records what changed, and ends with a checkpoint commit on
`claude/wizardly-carson-y19ryg`. `main` is not touched until phase 13.

## Phase 0: repository state

- `origin/main` = `620072b` (6A/6B, four-brand trial, Devpost drafts).
- Branch = `c5daedf`, two commits ahead of `main` and none behind:
  `ac3f61e` (offline collapse diagnostic) and `c5daedf` (presentation pass).
  `main` contains neither.
- Tests: 159, all passing.
- Deployed Render commit: not determinable from this environment. The egress
  proxy refuses `motif-pxh8.onrender.com`, and `/healthz` returns `{"ok": true}`
  with no version. The owner deploys `main` manually, so the deployed commit is
  at most `620072b`.
- Work continues on the branch; nothing is merged.

## Phase 1: UI cleanup, engine unchanged

Changed (web result, printed brief, start page):

- Application context appears once, on its own line above the brief. The fixed
  template no longer appends "Application context: ..." to the prose, and the LLM
  prompt (`prose-0.6`) tells Claude not to quote or restate it.
- Removed from the page and the PDF: the "Written by MOTIF's fixed template"
  bylines and the LLM status variants, the version footer, the versions and step
  statuses in the evidence fold, Qloo request IDs and paths in the sources, rule
  wording ("Draft rule", "no scent rule", "MOTIF does not yet translate"), the
  repeated "supplier-described" line, and the LLM mention on the start page.
- Claude is still disclosed when it wrote the prose ("Prose drafted by Claude
  from this result and checked against it"); a template brief carries no byline
  and never shows the Claude chip, so it is never presented as LLM output.
- Unknown dimensions now read "Open to the perfumer".
- "Cultural evidence sourced from Qloo" leads the profile and the sources, and
  heads the PDF; each phrase still opens its Qloo trace, and the full trace fold
  links the technical JSON.
- Kept in the technical JSON: versions, rule IDs, request IDs, template/LLM
  notes, open design questions.

Checks: 160 tests pass (one new browser test: no internal wording, context once,
Qloo line present in web and PDF). The collapse diagnostic is byte-identical to
the baseline (markdown and JSON). A recorded-data scan of MUJI, Ralph Lauren,
A24, Supreme, and Sanrio found no internal wording, the context once in web and
PDF, and one-page PDFs. No Qloo or LLM request was made.

## Phase 2: legacy engine frozen as the baseline

- `tools/legacy_baseline.py` replays the 13 trial brands from recordings through
  the unchanged legacy engine with stage definitions written fresh (not the
  collapse script's code) and reproduces 13/13/12/7/7/3.
- `reports/baselines/legacy_engine_0.3.json`: frozen per-brand stage sets,
  counts, legacy config versions, and SHA-256 of the four legacy config files.
- `tests/test_legacy_baseline.py`: the legacy config cannot change silently; the
  replay must match the frozen sets when recordings are on disk.
- `docs/ENGINE_REDESIGN.md`: baseline, problems demonstrated, what the new
  engine must improve, what it must not claim.
- No engine behaviour changed; no Qloo or LLM request.

## Phase 3: sensory model research (candidate, not loaded)

- Network policy blocks academic and reference hosts; a six-agent literature run
  was stopped (every fetch refused) and nothing it saw is cited. Open datasets
  from the Pyrfume archive were read instead: Dravnieks 1985, Keller & Vosshall
  2016, Leffingwell (data only; files' SHA-256 recorded; data stays git-ignored).
- `tools/sensory_evidence.py` → `config/candidates/odor_axis_evidence.v1.json`:
  17 odor families × poles, one pole descriptor at a time, bootstrap interval,
  drop-top-5, pleasantness control. The dry pole has no data support.
- `config/candidates/motif_sensory_vectors.v1.json` (`sensory-1.0`, revision r2):
  23 of 72 cells; 5 medium (the legacy R1–R5 links, capped at moderate), 18 low
  (always weak, read as tentative); the five stereotypes forbidden by draft-0.2
  stay null; heritage, melancholic, romantic make no claim.
- Review: r1 was reviewed from three lenses (method, perfumer, engine); the
  engine lens was stopped by the session usage limit. Findings, all checked
  against the data, drove the one revision (r2). `tools/sensory_model_review.py`
  checks the rules, quoted numbers, coverage, and similarity;
  `tests/test_sensory_model.py` runs it.
- Gate: no near-identical vectors, guesses labelled and capped, not R1–R5 alone.
- No engine behaviour changed; no Qloo or LLM request.

## Phase 4: weighted motif scoring

- `motif/scoring.py`, `config/motif_scoring.v1.json` (`scoring-1.0`): bounded,
  saturating noisy-OR over channels (own entry, related brands, related films,
  related artists only when fetched, diversity of cue groups and source kinds),
  common-cue penalty, own-entry anchor. Deterministic.
- `docs/MOTIF_SCORING.md`; `reports/motif_scores.md` (13 brands, offline);
  `tests/test_motif_scoring.py` (bounds, monotonicity, saturation, own anchor,
  source and cue diversity, artist only when fetched, common and negated cues,
  order independence; the six named checks when recordings exist).
- Checks: A24 0.699 vs Comme des Garçons 0.863 (provocation), Gucci 0.643 vs
  Balenciaga 0.838, MUJI led by restraint vs Aesop led by precision, heritage
  for Ralph Lauren 0.669 and Harley-Davidson 0.556 (its top motif), Sanrio
  playfulness 0.719. One related entity removed: at most 0.233 (a motif on one
  related brand), at most 0.195 for motifs at the lead level, median 0.056.
- Gate: graded differences where the legacy labels were equal, no instability
  beyond single-entity minor signals. Not wired into the product yet.

## Phase 5: continuous sensory engine (primary engine from the command line)

- `motif/continuous.py` (`continuous-1.0`) + `config/continuous_params.v1.json`:
  per dimension, contributions = motif score × cell confidence weight × cell
  value over non-null cells only; value = weighted mean; mass, agreement,
  confidence; states open / balanced_open (contributors pull both ways; never a
  confident middle) / resolved. Motifs supported only by common cues are context,
  never pulls. The confidence word is capped by the best cell behind it (low cells
  alone → "tentative"); each dimension records its evidence basis and each
  contributor its rationale and uncertainty: evidence → motif → score →
  contribution → dimension, no LLM.
- `config/motif_sensory_vectors.v1.json`: promoted unchanged from candidates.
- `motif/agent.py`: `engine="continuous"` fetches every configured domain and asks
  no conflict question; `engine="legacy"` (default inside the web server until
  phase 9) is unchanged. `python3 -m motif run` defaults to the continuous engine
  (`--engine legacy` keeps the baseline); `python3 -m motif compare-engines`
  runs both on the same recorded evidence.
- Tests: `tests/test_continuous.py` (null cells, opposite pulls, weighted mean,
  weak evidence, tentative wording, common cues as context, trace, determinism,
  shipped-model consistency), two controller tests in `tests/test_motif_agent.py`.
- Engine changes taken from the phase 3 review: common-cue exclusion, word cap,
  evidence basis, 'balanced' only for evidenced neutrality.

## Phase 6: 13-brand diagnostic, legacy vs continuous

- `tools/continuous_report.py` (via `tools/engine_compare.py analysis`) →
  `reports/continuous_engine_analysis.md`: profiles, distances (raw and
  scale-free), coverage, unresolved share, collisions, sensitivity to one related
  entity, stability when a minor motif is dropped, motif shares, an ablation
  without tentative cells, the named pairs, and answers to the six questions.
- Result: 7 → 11 distinct profiles (9 without tentative cells); zero-distance
  pairs 7 → 0; unresolved 80% → 53%; all six dimensions reachable. Deterministic.
- Gate: not collapsing; weaknesses recorded, not tuned on these 13 brands.
- `tests/test_continuous_analysis.py` keeps the result (when recordings exist).

## Phase 7: pre-registered holdout

- Pre-registration `reports/continuous_holdout.md` part A and the harness
  `tools/holdout_run.py` (+ `tests/test_holdout_harness.py`) committed in
  `ba7fea1` before any request. Live run: 17 Qloo requests (cap 20), no LLM.
- Part B (this commit): no structural failure; 4 of 5 resolved (IKEA not:
  untyped search); 3 distinct profiles among the 4; Hermès = Ralph Lauren;
  misreads 5 of 59 (8%); weak coverage for LEGO and Coca-Cola. Nothing tuned.

## Phase 8: olfactory layer (scent architecture)

- `config/olfactory_directions.v1.json` (`olfactory-1.0`): 23 directions (accord
  types) with roles, labelled sensory cells (odor data vs MOTIF design),
  descriptors, material references (IFRA 2019 generic names and descriptors from
  the Pyrfume digitization; trade names only from supplier pages read in
  palette-0.3), uncertainties, and the matching parameters.
- `motif/olfactory.py`: deterministic cosine matching from the continuous target,
  conflicts set aside, opening/core/drydown or "open to the perfumer",
  emphasize/avoid only when a supported dimension backs them, tentative basis
  labelled. Wired into the continuous engine and the command line.
- `docs/OLFACTORY_LAYER.md`; `tests/test_olfactory.py` (library rules, evidence
  consistency, trade names, IFRA names, matching, determinism, 13 brands).
- 13 brands: 11 distinct structures (legacy: 3 material sets).

## Phase 9: brief redesign on the continuous engine

- The web app and the printed brief now run the continuous engine (the legacy
  engine stays on the command line as `--engine legacy`, and as the frozen
  baseline). The web controller fetches every configured domain and asks no
  conflict question: an unresolved or two-way dimension is shown as open to the
  perfumer.
- `motif/story.py` (`brief-1.0`): plain-language readings of a continuous
  result: the cultural profile (own-entry motifs lead), the headline (the brand's
  own motifs lead the title; a direction drawn only from related references
  never leads it and is said to come from "references Qloo relates to" the
  brand), the why-chain (Qloo descriptor → motif → dimension), the template
  prose, the prose checks (no ingredient outside the architecture, no numbers or
  percentages, no audience or validation claims, every open dimension named),
  and the brief JSON (user intent and accepted readings kept apart from
  evidence).
- `motif/llm.py`: a continuous prompt (`prose-c1.0`) and dispatch by engine;
  same ledger, same one controlled retry, same labelled template on failure.
- Result page and PDF sections: Cultural profile → Olfactory direction → Scent
  architecture → Emphasize and avoid (only when a supported dimension backs it)
  → Why: Qloo → motif → scent → The brief. Open dimensions and empty roles read
  "Open to the perfumer"; the application context appears once, with no claim
  that it changed anything; the Qloo source line and the request trail stay;
  material references are examples of a class with a trade name only where
  MOTIF read the supplier's page. The conflict question, the material dialog,
  and the old material/how/direction blocks are removed from the page code.
- The command line writes the continuous brief too (`run`, default engine).
- Lists of labels that contain commas ("earthy, mossy") are joined with
  semicolons in the brief text and the PDF.
- Found in the recorded-data review of 17 brands (13 trial, 4 resolved
  holdout): repeated sentences on the page (each profile row restated its
  source sentence; the "why" chains re-quoted the profile's Qloo phrases; Nike's
  empty profile repeated the headline). Now each Qloo phrase is quoted once on
  the page, related-only motifs are marked "references only", and an empty
  profile lists the weaker signals. Headline gaps: an own motif with no
  dimension of its own now reads "Heritage, from Hermès' own Qloo entry." (not
  a bare "Heritage."); weak signals that resolve a dimension without any leading
  motif now say so instead of "Not enough repeated signal".
- `olfactory-1.1` (version bump with a written reason in the library and in
  `docs/OLFACTORY_LAYER.md`): "works with" is sign-based; eligibility is
  unchanged, so no structure changed on the 17 brands. A stricter conflict rule
  was tried and rejected.
- Review of the 17 recorded brands on the final pages: one A4 page each, no
  horizontal overflow (desktop and phone), the application context once, the Qloo
  source line present, no internal wording, no page errors. IKEA stops at the
  entity question (Qloo returns only stores), as in the holdout.
- Tests: `tests/test_story.py` (headline rules, prose checks, LLM dispatch and
  retry, view honesty, brief JSON); web, review, and browser tests updated to the
  new sections (browser: section order from the served data, role names, "open
  to the perfumer" on both pages, one A4 page, context once, no internal
  wording, no extra request).

## Phase 10: final validation

- `tools/validation_report.py` → `reports/final_validation.md`;
  `tests/test_validation_report.py`; `docs/VALIDATION.md` (methods, results,
  limits, gates).
- Deterministic in process and across interpreters with different hash seeds;
  13 of 13 trial brands traceable.
- Collapse: legacy 13/13/12/7/7/3 → continuous 13/13/12/11/12/11 (descriptors,
  cue groups, motifs, profiles, eligible materials or directions, final output).
- Forcing check (negative findings kept): without the tentative design cells,
  11 → 7 distinct architectures; literal Qloo descriptor overlap barely predicts
  output overlap (Spearman 0.08). Perturbation: one descriptor left out changes
  labels in 6% and the architecture in 4% of 523 runs.
- Holdout replay with the architecture added post hoc: LEGO = Coca-Cola = Ralph
  Lauren share one tentative structure (single "slightly polished" texture).
- LLM-only baseline: no new call (11 of the 20-call daily cap already used); the
  four structured stage-6B answers: the LLM commits 19 of 24 dimensions, the
  continuous engine 10, legacy 3; where continuous and LLM both commit, 7 of 8
  agree. Agreement is not validation.
- Full suite: 228 tests, all pass (network blocked; browser and PDF included).
  Secret scan of tracked files: only the existing test sentinels.

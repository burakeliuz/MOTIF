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

# MOTIF working notes for Claude Code

Current phase: **Qloo feasibility spike** (roadmap stage 1 done offline; stage 2 = live run).
Read `MOTIF_QLOO_FEASIBILITY.md` (rev 0.2) before changing anything. Then read
`README.md`, `docs/QLOO_ACCESS_NOTES.md`, and `reports/feasibility.md`.

## Communication with the project owner

- The owner follows progress live on a phone. Write every user-facing message in Turkish, including the short progress notes between steps and tool-call descriptions.
- Use plain language for a non-technical reader; longer is fine. The first time a technical term appears (for example harness, API, JSON, commit), explain it in one short sentence.
- Code, code comments, and repository documents stay in English (the hackathon submission is in English).

## Commands

- `python3 -m unittest`: run before every commit.
- `python3 -m motif_spike check | plan --plan pilot | run --mode synthetic | run --mode live --plan pilot|full | renormalize --run latest-live`

## Non-negotiables

- Never ask for, print, store, or commit a credential. The harness holds it (`qloo setup --qloo` or `QLOO_API_KEY`).
- Qloo access goes only through `@qloo/qloo-harness` (`qloo api` / `qloo exec`). Do not add a direct HTTP client or a second integration.
- Never fall back from a failed live call to fixtures, another endpoint, or another credential.
- Keep `qloo_observation`, `motif_annotation`, `design_rule`, and `synthetic_fixture` separate. Synthetic data is never evidence.
- Copy returned values literally with their raw pointer. Do not infer cultural traits from entity names or model memory.
- Keep the six axes and pole order. Unknown axes are `null`. Five draft rules only; no `restrained → intimate`.
- Scores are reported as returned: no percentages, no cross-request averaging, no "lift".
- During the spike: no frontend, motif classifier, sensory engine, material list, or brief generation.

## When live output first arrives

`adapter.PARSER_STATUS` is `unverified`. Compare `data/raw/<run>/responses/*.json`
with `adapter.locate_items` / `item_view`. Fix the parsers if shapes differ,
re-run `renormalize`, and only then set the status to `verified`. Live data
stays in git-ignored `data/`. The curated judgments go in `reports/feasibility.md`.

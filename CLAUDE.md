# MOTIF working notes for Claude Code

Current phase: **Qloo feasibility spike** (roadmap stage 1 done offline; stage 2 = live run).
Read `MOTIF_QLOO_FEASIBILITY.md` (rev 0.2) before changing anything. Then read
`README.md`, `docs/QLOO_ACCESS_NOTES.md`, and `reports/feasibility.md`.

## Communication with the project owner

- The owner follows progress live on a phone. Write every user-facing message in Turkish, including the short progress notes between steps and tool-call descriptions.
- Use plain language for a non-technical reader; longer is fine. The first time a technical term appears (for example harness, API, JSON, commit), explain it in one short sentence.
- Code, code comments, and repository documents stay in English (the hackathon submission is in English).

## Branches and main

- `main` is the public default branch (judges and new cloud sessions start from it). Work happens on the session's own branch.
- Never push to `main` without the owner's explicit OK in the current session. When a stage ends, show `git log origin/main..HEAD` in plain Turkish and ask whether to update `main` (fast-forward only).
- New sessions clone `main`, so unmerged work on an old session branch is invisible to them: remind the owner before they open a new session.

## Roadmap (revised 2026-10-06)

One Claude Code cloud session per stage; each stage ends with tests, a push to the session branch, and the `main` question below.

1. Offline preparation: done.
2. Live Qloo test: pilot, then full plan after the owner's OK; `reports/feasibility.md`; a small curated evidence excerpt in `reports/`; `docs/SUBMISSION_NOTES.md` skeleton.
3. Product decisions: `MOTIF_BUILD_SPEC.md`, including runtime LLM yes/no, web stack, and whether to host a demo. The spike rules above end when this spec is accepted.
4. Engine and agentic flow, end to end from the command line.
5. Interface (and hosting only if the spec chose it).
6. Clean-environment setup test, demo, and Devpost texts.

Every stage adds to `docs/SUBMISSION_NOTES.md`, mapped to the six items of the kit's submission guide (see `docs/QLOO_ACCESS_NOTES.md`).

## Commands

- `python3 -m unittest`: run before every commit.
- `python3 -m motif_spike check | plan --plan pilot | run --mode synthetic | run --mode live --plan pilot|full | renormalize --run latest-live`

## Non-negotiables

- Never ask for, print, store, or commit a credential. In the cloud environment the key is an environment API credential that the agent proxy injects; `QLOO_API_KEY=proxy-injected` is only a placeholder. Locally: `QLOO_API_KEY` or `qloo setup --qloo`.
- Qloo access goes through `motif_spike/transport.py` only: `DirectTransport` (default; the organizers allow own tooling) or `HarnessTransport` (`--transport harness`). Do not add a third integration.
- Never fall back from a failed live call to fixtures, another endpoint, or another credential.
- Keep `qloo_observation`, `motif_annotation`, `design_rule`, and `synthetic_fixture` separate. Synthetic data is never evidence.
- Copy returned values literally with their raw pointer. Do not infer cultural traits from entity names or model memory.
- Keep the six axes and pole order. Unknown axes are `null`. Five draft rules only; no `restrained → intimate`.
- Scores are reported as returned: no percentages, no cross-request averaging, no "lift".
- During the spike: no frontend, motif classifier, sensory engine, material list, or brief generation.

## Live access facts (organizer email, 2026-10-05)

- Hackathon keys only work against `https://hackathon.api.qloo.com`; `config/manifest.json` → `harness_environment` sets it for every live run.
- Verified 2026-10-06: the cloud environment's API credential for `hackathon.api.qloo.com` opens the host and injects the key into requests that carry no `X-Api-Key` header. It does not replace a header the harness already sends, so the harness transport fails with 403 there; use the direct transport.
- Tests block all network access (`tests/__init__.py`); never weaken that.
- Help channel: Discord `#qloo-hackathon`.

## When live output first arrives

`adapter.PARSER_STATUS` is `unverified`. Compare `data/raw/<run>/responses/*.json`
with `adapter.locate_items` / `item_view`. Fix the parsers if shapes differ,
re-run `renormalize`, and only then set the status to `verified`. Live data
stays in git-ignored `data/`. The curated judgments go in `reports/feasibility.md`.

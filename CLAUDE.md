# MOTIF working notes for Claude Code

Current phase: **stage 6B done on the session branch** (art direction A with scent strips, creative intent, user-accepted LLM readings, printable brief, persistent budget counters; spec rev 0.4; two-brand trial in `reports/trial_6b.md`). Hosted demo: https://motif-pxh8.onrender.com (behind the review password; deploys from `main` by the owner). Pending owner decisions: rule R6 + one material (`docs/STAGE_6A_DECISIONS.md` §0.1), the gate at judging time. Next: stage 6 (clean-environment test, final checks on Oct 27–28, Devpost edits by the owner).
Read `MOTIF_QLOO_FEASIBILITY.md` (rev 0.2) and `MOTIF_BUILD_SPEC.md` before
changing anything. Then read `README.md`, `docs/QLOO_ACCESS_NOTES.md`,
`reports/feasibility.md`, `reports/design_examples.md`, and `reports/holdout_t1.md`.

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
3. Product decisions: `MOTIF_BUILD_SPEC.md` written (runtime LLM optional, Python stdlib web stack, hosted demo required by the official rules). The spike rules below end when the owner accepts this spec.
4. Engine and agentic flow, end to end from the command line.
5. Interface and hosting: done; deployed by the owner at https://motif-pxh8.onrender.com.
   6A/6B. Product review and the chosen experience: done on the session branch (see `docs/STAGE_6A_DECISIONS.md`).
6. Clean-environment setup test, demo, and Devpost texts.

Every stage adds to `docs/SUBMISSION_NOTES.md`, mapped to the six items of the kit's submission guide (see `docs/QLOO_ACCESS_NOTES.md`).

## Commands

- `python3 -m unittest`: run before every commit.
- `python3 -m motif.web [--recorded RUN_DIR ...]` (local preview: `--recorded` replays stored runs, labelled; never in the public demo) and `python3 -m motif llm-check` (one real Anthropic call)
- `python3 -m motif run --reference NAME [--type brand|any] [--choose ID] [--recorded RUN] [--include-artist] [--allow-unverified-materials]` and `python3 -m motif compare --reference NAME --recorded RUN`
- `python3 -m motif_spike check | plan --plan pilot | run --mode synthetic | run --mode live --plan pilot|full | renormalize --run latest-live | excerpt --run latest-live`

## Non-negotiables

- Never ask for, print, store, or commit a credential. In the cloud environment the key is an environment API credential that the agent proxy injects; `QLOO_API_KEY=proxy-injected` is only a placeholder. Locally: `QLOO_API_KEY` or `qloo setup --qloo`.
- Qloo access goes through `motif_spike/transport.py` only: `DirectTransport` (default; the organizers allow own tooling) or `HarnessTransport` (`--transport harness`). The engine wraps it in `motif/qloo.py` (budget, retries, session cache, explicit recorded replay). Do not add a third integration.
- Never fall back from a failed live call to fixtures, another endpoint, or another credential.
- Keep `qloo_observation`, `motif_annotation`, `design_rule`, and `synthetic_fixture` separate. Synthetic data is never evidence.
- Copy returned values literally with their raw pointer. Do not infer cultural traits from entity names or model memory.
- Keep the six axes and pole order. Unknown axes are `null`. Five draft rules only; no `restrained → intimate`.
- Scores are reported as returned: no percentages, no cross-request averaging, no "lift".
- The spec was accepted for stage 4 (rev 0.2). Build in its order: interface and hosting in stage 5, without changing engine decisions in the UI. `motif_spike/` stays intact.
- Research control is a deterministic state machine (`motif/agent.py`). The LLM writes validated prose only; giving it tool choice needs the owner's approval.
- LLM: key only from `MOTIF_ANTHROPIC_API_KEY`; default `claude-sonnet-5-5`; never switch models silently; every real call goes through the ledger (`data/llm_calls.jsonl`). A failed call or invalid text shows the labelled template, never as LLM output.
- Web review gate (`motif/web/access.py`): password only from `MOTIF_ACCESS_PASSWORD`; protection on by default and fail-closed; every page and API except `/healthz` and the sign-in page is behind it. Open it (`MOTIF_ACCESS_PROTECTION=off`) only on the owner's word.
- Creative intent and accepted LLM readings are user data (`user_intent`, `user_preference`): never evidence, never change motifs, axes, materials, or scores. The LLM may suggest readings only on the user's request, at most three, validated in `motif/interpret.py`.
- Wording: related brands and films are "references Qloo relates to" a brand; never claim anything about audiences.
- Budget counters (`data/web_usage.json`, `data/llm_calls.jsonl`) reserve before spending and fail closed; do not bypass them.
- Web: keys stay server-side; the UI never builds HTML from data; no fake progress; identical requests and answers must not repeat Qloo or LLM calls.
- Live matching uses only material properties with `verified_full_page`; unverified ones appear only in the labelled design preview.
- Held-out brands used once (T1: Le Labo, Patagonia) are no longer independent validation.
- `config/motif_lexicon.json`, `config/material_palette.json`, and `config/draft_rules.json` are versioned design rules: change them only with a version bump and a written reason. Material profiles are MOTIF's creative mapping; supplier descriptors stay in `source` and are not verified in full until task T2.
- Results of the engine are a creative direction, never a formula, dosage, or preference prediction. Unknown or conflicted axes stay `null`.

## Live access facts (organizer email, 2026-10-05)

- Hackathon keys only work against `https://hackathon.api.qloo.com`; `config/manifest.json` → `harness_environment` sets it for every live run.
- Verified 2026-10-06: the cloud environment's API credential for `hackathon.api.qloo.com` opens the host and injects the key into requests that carry no `X-Api-Key` header. It does not replace a header the harness already sends, so the harness transport fails with 403 there; use the direct transport.
- Tests block all network access (`tests/__init__.py`); never weaken that.
- Help channel: Discord `#qloo-hackathon`.

## Live output

`adapter.PARSER_STATUS` is `verified` for direct-transport bodies (pilot of
2026-10-06). If a new response shape appears (`unrecognized_shape`), fix the
parsers, re-run `renormalize`, and re-check before trusting it. Live data stays
in git-ignored `data/`; a new session has none until it re-runs the plans.
Curated judgments are in `reports/feasibility.md`; the committable literal
excerpt is regenerated with `python3 -m motif_spike excerpt --run latest-live`.

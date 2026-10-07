# MOTIF working notes for Claude Code

Current phase: **engine refactor (phases 0–13) done and on `main` (70c3711, fast-forwarded with the owner's OK on 2026-10-07); Render not redeployed; on the session branch after it: real PDF brief download, JSON download removed from the UI, label/description overlap fixed, the Adidas/OpenAI review (`reports/adidas_openai_review.md`), then `lexicon-0.4` (energy and technology motifs, two precision words, a narrative-tone context rule; continuous engine only) with `sensory-1.1` (their cells as creative design decisions) and a scent-first page and PDF (scent idea up front, open dimensions in one sentence, reasons and counts in a closed method detail)** (2026-10-07: the product runs the continuous engine `continuous-1.0` (weighted motif scores, a researched motif-to-sensory model from open odor data, six continuous dimensions), a 23-direction scent architecture (`olfactory-1.1`), the redesigned one-page brief, and a final validation; the rule engine `engine-0.3` with R1–R5 is kept as the frozen legacy baseline. Read `docs/REFACTOR_LOG.md`, `docs/ARCHITECTURE.md`, `docs/VALIDATION.md`). Hosted demo: https://motif-pxh8.onrender.com (behind the review password; deploys from `main` by the owner). Pending owner decisions: the `main` update for these session-branch changes and the Render deploy; decision 2, Claude spending on the free host (`docs/STAGE_6A_DECISIONS.md` §0.4); the gate at judging time; the candidate engine fixes listed in `docs/ENGINE_REDESIGN.md` §5 and `reports/adidas_openai_review.md` §6 proposal 3 (each needs a version bump and a new holdout). Decision 1 (R6 + one material) concerns only the legacy engine now. Next: stage 6 (clean-environment test, final checks on Oct 27–28, Devpost edits by the owner).
Read `MOTIF_QLOO_FEASIBILITY.md` (rev 0.2) and `MOTIF_BUILD_SPEC.md` before
changing anything. Then read `README.md`, `docs/ARCHITECTURE.md`, `docs/VALIDATION.md`, `docs/QLOO_ACCESS_NOTES.md`,
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
   6R. Engine and product refactor, phases 0–13: done (see `docs/REFACTOR_LOG.md`).
6. Clean-environment setup test, demo, and Devpost texts.

Every stage adds to `docs/SUBMISSION_NOTES.md`, mapped to the six items of the kit's submission guide (see `docs/QLOO_ACCESS_NOTES.md`).

## Commands

- `python3 -m unittest`: run before every commit.
- `python3 -m motif.web [--recorded RUN_DIR ...]` (local preview: `--recorded` replays stored runs, labelled; never in the public demo) and `python3 -m motif llm-check` (one real Anthropic call)
- `python3 -m motif run --reference NAME [--type brand|any] [--choose ID] [--recorded RUN] [--include-artist] [--engine continuous|legacy] [--allow-unverified-materials]` (continuous is the default; the materials flag and `--resolve-conflict` apply to legacy only), `python3 -m motif compare --reference NAME --recorded RUN`, and `python3 -m motif compare-engines --reference NAME --recorded RUN`
- Offline analyses (need the git-ignored recordings): `python3 tools/validation_report.py [--write reports/final_validation.md]`, `python3 tools/engine_compare.py analysis`, `python3 tools/legacy_baseline.py`, `python3 tools/holdout_run.py evaluate RUN_DIR`, `python3 tools/sensory_model_review.py`
- `python3 -m motif_spike check | plan --plan pilot | run --mode synthetic | run --mode live --plan pilot|full | renormalize --run latest-live | excerpt --run latest-live`

## Non-negotiables

- Never ask for, print, store, or commit a credential. In the cloud environment the key is an environment API credential that the agent proxy injects; `QLOO_API_KEY=proxy-injected` is only a placeholder. Locally: `QLOO_API_KEY` or `qloo setup --qloo`.
- Qloo access goes through `motif_spike/transport.py` only: `DirectTransport` (default; the organizers allow own tooling) or `HarnessTransport` (`--transport harness`). The engine wraps it in `motif/qloo.py` (budget, retries, session cache, explicit recorded replay). Do not add a third integration.
- Never fall back from a failed live call to fixtures, another endpoint, or another credential.
- Keep `qloo_observation`, `motif_annotation`, `design_rule`, and `synthetic_fixture` separate. Synthetic data is never evidence.
- Copy returned values literally with their raw pointer. Do not infer cultural traits from entity names or model memory.
- Keep the six axes and pole order. Unknown or contested dimensions stay open ("open to the perfumer"; `null` in the legacy engine). The five draft rules R1–R5 belong to the frozen legacy engine (`engine-0.3`, `--engine legacy`, baseline in `reports/baselines/`); the product runs `continuous-1.0`. No `restrained → intimate`, and none of the cells listed under `forbidden_without_owner_decision` in `config/motif_sensory_vectors.v1.json` without the owner's decision.
- Scores are reported as returned: no percentages, no cross-request averaging, no "lift".
- The spec was accepted for stage 4 (rev 0.2). Build in its order: interface and hosting in stage 5, without changing engine decisions in the UI. `motif_spike/` stays intact.
- Research control is a deterministic state machine (`motif/agent.py`). The LLM writes validated prose only; giving it tool choice needs the owner's approval.
- LLM: key only from `MOTIF_ANTHROPIC_API_KEY`; default `claude-sonnet-5-5`; never switch models silently; every real call goes through the ledger (`data/llm_calls.jsonl`). A failed call or invalid text shows the labelled template, never as LLM output.
- Web review gate (`motif/web/access.py`): password only from `MOTIF_ACCESS_PASSWORD`; protection on by default and fail-closed; every page and API except `/healthz` and the sign-in page is behind it. Open it (`MOTIF_ACCESS_PROTECTION=off`) only on the owner's word.
- Brief purpose (creative intent) and accepted LLM readings are user data (`user_intent`, `user_preference`): never evidence, never change motifs, axes, materials, or scores. The LLM may suggest readings only on the user's request, at most three, validated in `motif/interpret.py`.
- The result's headline comes from `story.headline` (`narrative.headline` for the legacy engine): the brand's own motifs lead; a direction drawn only from related references never leads the title.
- Wording: related brands and films are "references Qloo relates to" a brand; never claim anything about audiences.
- Budget counters (`data/web_usage.json`, `data/llm_calls.jsonl`) reserve before spending and fail closed; do not bypass them. `MOTIF_LLM_BUDGET_GUARD` (default `auto`) pauses Claude on Render unless the data directory is on a persistent mount or the owner confirms a provider-side spend limit (`provider`); do not weaken it.
- Recorded mode is for local development and tests only: refused on Render, never labelled or shown as live, and a live server shows no recorded wording.
- Web: keys stay server-side; the UI never builds HTML from data; no fake progress; identical requests and answers must not repeat Qloo or LLM calls.
- Scent architecture: material references are examples of a direction's class (IFRA 2019 glossary generic names); a trade name appears only where MOTIF read the supplier's full page (`verified_full_page` in the palette). Legacy matching uses only `verified_full_page` properties; unverified ones appear only in the labelled design preview.
- Held-out brands used once are no longer independent validation: T1 (Le Labo, Patagonia) and the phase-7 continuous holdout (IKEA, Hermès, Bang & Olufsen, LEGO, Coca-Cola; its architectures were added post hoc).
- Versioned design rules: `config/motif_lexicon.v1.json` (continuous lexicon), `config/motif_scoring.v1.json`, `config/motif_sensory_vectors.v1.json`, `config/continuous_params.v1.json`, `config/olfactory_directions.v1.json`, and (legacy) `config/motif_lexicon.json` (frozen `lexicon-0.3`), `config/material_palette.json`, `config/draft_rules.json`, `config/engine_params.json`. Change them only with a version bump and a written reason; the legacy files are hash-checked against the frozen baseline. Material profiles are MOTIF's creative mapping; supplier descriptors stay in `source`.
- Results of the engine are a creative direction, never a formula, dosage, or preference prediction. Tentative leanings (low-confidence design cells only) are labelled tentative.

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

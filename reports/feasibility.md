# MOTIF Qloo feasibility report

**Verdict: `not_evaluated`.** No live Qloo request has been made with an event
credential. Nothing below is evidence about Qloo coverage, the five seeds, or
MOTIF's premise.

- Date: 2026-10-04
- Brief: `MOTIF_QLOO_FEASIBILITY.md` rev 0.2
- Playground: adapter 0.1.0, parser `unverified`
- Credential status: not configured in this environment (`python3 -m motif_spike check` → NOT READY)

## What is ready

- Live and synthetic modes with no fallback between them; a credential error stops the run.
- Access only through the event's supported harness (`qloo api search/entity/insights`, `qloo exec entity_tags`).
  Command lines were validated against harness 0.1.26 by dry-run and by no-key failures.
- Raw harness output and normalized evidence kept in separate trees, each
  observation linked to its raw file and JSON Pointer. Explicit statuses for
  empty, unresolved, ambiguous, forbidden, rate-limited, rejected, and similar outcomes.
- Seed resolution rule (exact name after case/accent folding; ambiguity reported, never guessed).
- Per-run facts sheet: resolution, request status, field coverage, examples
  with provenance, ID overlap, global-commonness check, cross-domain tag
  recurrence, sample tag shares (not lift), numeric field inventory.
- 40 tests on Python 3.9–3.13, including synthetic isolation (no process or
  network), provenance round-trip, duplicates, missing fields, error states,
  credential abort without leaks, reuse, and budget.

## Results by required section

| # | Section (brief §10) | State |
|---|---|---|
| 1 | Resolution status for all five seeds | not evaluated: no live search was run |
| 2 | Supported and tested domains, request status, available fields | not evaluated |
| 3 | Returned tag and attribute examples with provenance | none: no Qloo data has been retrieved |
| 4 | Differences and overlap between seed profiles | not evaluated |
| 5 | Repeated descriptive patterns across domains | not evaluated |
| 6 | Whether globally common results dominate | not evaluated |
| 7 | Quantitative fields and possible enrichment analysis | not evaluated; only sample enrichment within retrieved samples is designed, and lift is not computable without a population denominator |
| 8 | Missing semantic information that blocks motif classification | not evaluated |
| 9 | MOTIF decisions the evidence could or could not support | not evaluated; no scent or motif was generated |
| 10 | Recommendation (continue / narrow / pause) | none yet |

Data availability, descriptive sufficiency, and profile differentiation each
remain `not_evaluated`.

## Pre-live risks from documentation and harness source (not data findings)

These come from reading docs and source code. They say what to check in
the live run, not what the answer is.

1. **Tag insights route.** `qloo api insights` prints only `results.entities`, so it
   cannot return tag insights. The playground uses `qloo exec entity_tags`,
   which returns at most 20 compact tags (ID, name, type, popularity, affinity) per seed,
   without namespace scoping.
2. **Descriptor type.** Qloo's documented movie example mixes plot keywords
   with streaming-service tags. If the seeds' related entities look similar,
   tags may describe plot or distribution rather than visual or material style.
   The facts sheet counts tags per namespace so this can be judged from the data.
3. **Score scale and comparability.** Docs describe affinity as normalized per
   query. Cross-seed comparison therefore relies on returned IDs and rank, not
   on score differences.
4. **Explainability.** With one seed as the only signal, per-result
   explainability is expected to point back to that seed and add little.
5. **Event terms.** The organizers' kickoff email (2026-10-05) gives the
   event base URL (`https://hackathon.api.qloo.com`), now pinned in
   `config/manifest.json`. Quota, rate limit, and expiry are still unknown.
   The hackathon developer guide on `docs.qloo.com` could not be read from
   this environment (network policy). The budgets (20 pilot / 60 full) are
   conservative guesses.
6. **Access route wording.** The kickoff email names `qloo exec` and
   `qloo mcp` as supported; the kit also lists `qloo api`, which MOTIF needs
   because the exec workflows drop per-entity tags. To be confirmed with the
   organizers.

## Verification log

- Read: hackathon kit (README, API access, safe use, troubleshooting,
  submission, CLI and MCP starters), docs-public reference pages, and
  `@qloo/qloo-harness` 0.1.26 source (installed in a scratch folder, not in
  this repo).
- Ran without a credential: `qloo --version`, `qloo setup --status --json`,
  dry-runs of MOTIF's search/entity/insights commands (no API call), and the four
  MOTIF commands without a key (all fail locally with an auth error before any network call).
- One unintended request: while checking options, `qloo api tags` (which has
  no dry-run) sent one request with a placeholder, non-credential key. It
  returned `403 Forbidden` and no data.
- Not done: any request with a real credential.

## To run the live evaluation

1. Install Node.js ≥ 22.19.0 and `npm install --global @qloo/qloo-harness`.
2. Configure the event credential outside this repo: `qloo setup --qloo`, or
   `QLOO_API_KEY` in the environment settings of a cloud session. In the
   cloud environment, also allow `hackathon.api.qloo.com` under network
   access. The base URL itself is set by `config/manifest.json`.
3. `python3 -m motif_spike check` → READY, with base URL `https://hackathon.api.qloo.com`.
4. `python3 -m motif_spike run --mode live --plan pilot`. Inspect the facts
   sheet and the raw shapes, fix the parsers if needed, then set
   `PARSER_STATUS` to `verified`.
5. `python3 -m motif_spike run --mode live --plan full`. Then write sections
   1–10 above from the facts sheet, with judgments kept separate from
   observations.

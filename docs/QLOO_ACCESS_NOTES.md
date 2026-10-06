# Qloo access notes (checked 2026-10-04, updated 2026-10-05, before any live credential)

These notes record what was read in official documentation, in the public
harness package's source, and in the organizers' kickoff email. None of it is
a live observation. Re-check everything marked *open* once the event
credential is configured.

## Organizer kickoff email (shared by the project owner, 2026-10-05)

- The hackathon kicked off on September 30; submissions are due October 30 on Devpost.
- Keys are requested through the form in the developer guide
  (`docs.qloo.com/reference/qloo-llm-hackathon-developer-guide#getting-your-api-key`)
  and usually arrive by email within one business day. Keys are personal.
- **Hackathon keys only work against the hackathon API.** The harness must
  run with `QLOO_BASE_URL=https://hackathon.api.qloo.com` and
  `QLOO_TRUSTED_BASE_URL=https://hackathon.api.qloo.com`. MOTIF sets both
  from `config/manifest.json` for every live run, overriding any other shell
  value. Not yet verified live.
- `qloo setup --status` should report "Qloo data: ready" once the key is added.
- First-request example: `qloo exec find_tags` for "jazz" returns five tags
  all named Jazz with different types. This matches MOTIF's rule of never
  merging tags by display name.
- The email names `qloo exec` and `qloo mcp` as supported at the event (and not
  the harness's chat, plan, or build modes). It does not mention `qloo api`,
  which the kit's `docs/API_ACCESS.md` lists as a supported surface. MOTIF
  uses `qloo api` because the exec workflows drop per-entity tags (`describe`
  and `recommend` both compact entities). *Open: confirm on Discord that
  `qloo api` is acceptable.*
- Help: Discord `#qloo-hackathon`. Private matters such as a leaked key: email `ian@qloo.com`.
- Rules repeated: keep the key on your machine or server; send no personal
  data to Qloo; results describe what groups tend to like, not individuals.

## Submission guide and judging (kit `docs/SUBMISSION.md`, read 2026-10-06)

Each submission should include:

1. A short product problem statement.
2. The Qloo workflow or MCP tools used and why they fit the problem.
3. A redacted request-to-result explanation, including entity/tag choices.
4. A short demo or screenshots with no credential or personal data.
5. Setup steps another participant can run from a clean environment.
6. Known limitations, including what the result does not establish.

Judges are asked to consider usefulness, technical execution, provenance and
user clarity, responsible data handling, and reproducibility. Projects are
"stronger when they use Qloo results as evidence in a clear product flow".
A hosted demo is not listed as a requirement; a short demo or screenshots is.
The kit's `docs/SAFE_USE.md` also asks projects to separate a Qloo result from
the project's own interpretation and to ask for clarification when an entity
or tag choice would materially change a result.

## Direct transport (2026-10-06)

- The kickoff email lets participants "build your own tooling", so MOTIF's
  default live transport is now its own HTTPS client (`DirectTransport`).
  It sends the same parameters the harness sends (dry-run verified) and saves
  the complete response body, so tag results and top-level fields are no
  longer lost. The harness remains available with `--transport harness`.
- Live check on 2026-10-06 in the cloud environment: with the key stored as an
  environment API credential (host `hackathon.api.qloo.com`, header
  `X-Api-Key`, no prefix), a request without an `X-Api-Key` header returned
  HTTP 200 and `/search?query=A24&take=3` listed `A24` as `urn:entity:brand`.
  The same request through the harness returned 403: the harness sends its own
  placeholder key header, and the proxy does not replace it.
- During development two test cases accidentally ran the default (direct)
  transport against the real API (at most 16 requests, results discarded).
  Tests now block all network access.

## Cloud environment network

As of 2026-10-05, this project's Claude Code cloud environment refuses
connections to `hackathon.api.qloo.com` (egress policy, CONNECT 403). The
host must be added under the environment's network access before a live run
there. `api.qloo.com` and `registry.npmjs.org` were reachable; `docs.qloo.com`
and `devpost.com` were not.

## Sources read

- `qloo/qloo-hackathon-kit` (GitHub, main): README, `docs/API_ACCESS.md`,
  `docs/SAFE_USE.md`, `docs/TROUBLESHOOTING.md`, `docs/SUBMISSION.md`, and the CLI
  and MCP starters.
- `qloo/docs-public` (GitHub, main): search, entities, insights deep dive, parameters,
  taste analysis, onboarding, affinity score docs.
- `@qloo/qloo-harness` 0.1.26 from npm, installed in a scratch folder (not in this
  repo). Its `--help` output and `dist/` source were read, and `--dry-run` was
  used with a placeholder key (dry-run sends nothing).
- **Not read:** the hackathon developer guide on docs.qloo.com. This environment's
  egress policy refused the connection to `docs.qloo.com`. *Open.*

## Supported access route

- The kit lists the event's supported surfaces as `qloo explore`, `qloo exec`,
  `qloo api`, and `qloo mcp` from `@qloo/qloo-harness` (Node.js ≥ 22.19.0, harness
  ≥ 0.1.26). All share one credential and one quota.
- MOTIF therefore calls only `qloo api …` and `qloo exec …`. It does not call
  the HTTP API directly, and it never reads or passes the credential: the
  harness takes it from `qloo setup --qloo` (private config outside the repo)
  or `QLOO_API_KEY`.
- Readiness: `qloo setup --status --json` reports `qloo.ready` and
  `qloo.source` (`missing`, `environment`, ...) without the value. With a
  placeholder key it reports ready, so "ready" means configured, not accepted.
- Event base URL: now known from the kickoff email (see above).
- Event quota, rate limit, and expiry: still unpublished in the material
  available to us. *Open.* The manifest budgets (20 pilot / 60 full
  invocations) are conservative guesses, not event limits.

## What the harness prints (source, v0.1.26)

| Command used by MOTIF | HTTP request (dry-run verified) | What stdout contains |
|---|---|---|
| `qloo api search --query Q --take N --json` | `GET /search?query=Q&take=N` | the response's `results` value (list), not the whole body |
| `qloo api entity --id ID --json` | `GET /entities?entity_ids=ID` | the first entity object only |
| `qloo api insights --type T --signal-entities ID --take N --json --params '{"feature.explainability": true}'` | `GET /v2/insights?filter.type=T&signal.interests.entities=ID&take=N&feature.explainability=true` | `results.entities` (full entity objects); top-level fields such as aggregate explainability are dropped |
| `qloo exec entity_tags --input '{"entities":[ID],"limit":N}'` | `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=ID&take=N` (from source; exec has no dry-run) | workflow envelope with compact tags `{id, name, type, popularity, affinity}`, `status`, `interpretation`, `provenance.requests` |

Consequences for MOTIF:

1. `qloo api insights --type urn:tag` would print `[]` even when tags exist,
   because it prints only `results.entities`. Tag insights therefore use
   `qloo exec entity_tags`. Trusting the empty list would mistake a projection
   artifact for "no tags".
2. `qloo exec recommend` compacts entities and drops their `tags`. Related
   entities therefore use `qloo api insights`, which keeps tags and
   properties.
3. `exec entity_tags` returns at most 20 tags, without `filter.tag.types` or
   `filter.parents.types` scoping. Given a UUID, the harness first performs an
   `/entities` identifier lookup, so each call is about two API calls.
4. The `--dry-run` URL uses the harness config's `base_url` (or
   `https://api.qloo.com`) and ignores a `QLOO_BASE_URL` environment
   override, which the real request does honour. Because MOTIF sets the event
   base URL through the environment, preview URLs in the request log show
   `api.qloo.com` while requests go to `hackathon.api.qloo.com`. The facts
   sheet states the base URL actually used.
5. `qloo api tags` has no `--dry-run`.

## Errors (source and observation)

- `qloo api` failures print `{"error": true, "code": ..., "message": ...}`.
  Exit codes: 2 BAD_USAGE, 3 AUTH_FAILED (no key), 4 NOT_FOUND, 5 API_ERROR, 6 CONFIG_ERROR.
  The HTTP status appears only inside `message` (`API request failed: 429 Too Many Requests`),
  so MOTIF reads it from the text.
- `qloo exec` failures print `{"error": {"code", "layer", "retryable", "recovery"}, ...}`
  (exit 4 for `QLOO_AUTH`).
- Verified locally without a key: all four MOTIF commands fail before any
  network call with AUTH_FAILED (exit 3) or QLOO_AUTH (exit 4), which
  MOTIF classifies as `auth_error`.
- Observed once, unintentionally: `qloo api tags` (no dry-run available) was
  run with a placeholder key and returned `{"error":true,"code":"API_ERROR","message":"API request failed: 403 Forbidden"}`.
  No data was returned. MOTIF treats a 403 before any success as a credential failure.
- The harness itself does not retry `qloo api` calls. MOTIF retries rate-limit,
  5xx, timeout, and harness-flagged retryable failures at most twice (3 s, then 10 s).

## Live observations (2026-10-06)

Pilot `live-20261006T102530Z-61e1` and full run `live-20261006T103307Z-660d`
(direct transport, 45 requests sent, all HTTP 200, no rate limit hit). These
resolve several *open* items below. Details: `reports/feasibility.md`.

- All six candidate entity types (brand, movie, artist, book, person, place)
  return results under the hackathon key.
- Body shapes: `/search` and `/entities` → `{"results": [entity]}` (entity tags
  use `tag_id`); `/v2/insights` → `{"success", "results": {"entities"|"tags": [...]},
  "query": {"explainability"}}` (entity tags use `id`). Recorded in
  `motif_spike/adapter.py`; `PARSER_STATUS` is `verified` for these bodies.
- Entities carry descriptive namespaces not shown in the docs examples:
  `urn:tag:aesthetic_property:qloo`, `emotional_tone`, `personal_style`,
  `urn:tag:style:qloo`, and properties such as `aesthetic_properties`,
  `style_description`, and `adjectives_for_music`. How they are produced is
  undocumented in what we could read.
- `query.affinity` observed between 0.824 and 0.988 on related entities, and
  between 0.998 and 1 on tag insights.
- With one seed as the only signal, explainability attributes every result to
  that seed (score 1; aggregate `avg_score` 1), as expected.
- Unscoped tag insights (`filter.type=urn:tag`) return mostly place tags
  (payments, hotel ratings, dishes) at affinity ≈ 1.

## Data semantics from documentation

- Response shapes (docs examples): insight entities carry `entity_id`, `name`,
  `type`, `subtype`, `properties` (`description`, `short_descriptions`, …),
  `popularity`, `tags[] {id, name, type}`, and `query.affinity`. Raw tag
  insights carry `tag_id`, `types`, `subtype`, `tag_value`, and `query`.
- The documented movie example mixes plot keywords (`urn:tag:keyword:media`)
  with distribution tags (`urn:tag:streaming_service:media`). Whether MOTIF's
  seeds return style- or material-level descriptors is *open* and must be read
  from tag namespaces in the live facts sheet.
- Affinity: the docs describe a 0–100 range "expressed as a percentage". The
  numeric scale of `query.affinity` in live output is *open*. The docs also
  say scores are normalized per query, and advise comparing relative position
  within a result list rather than raw scores. MOTIF never averages scores
  across requests and never presents them as percentages of people.
- Explainability (`feature.explainability=true`): per-result
  `query.explainability` shows which input entities contributed. With a single
  seed as the only signal, this is expected to attribute everything to the
  seed (an inference from the docs, *open*).
- Qloo results describe aggregate affinities, not individual preferences or
  identity (kit SAFE_USE). An affinity does not establish shared aesthetics.
- The `openapi-schema.json` in docs-public is the generic OpenAPI 3.1
  meta-schema, not a Qloo API specification. No machine-readable Qloo spec was
  available.

## Entity types

The harness type list: `urn:entity:movie`, `tv_show`, `book`, `brand`, `artist`,
`person`, `actor`, `director`, `author`, `locality`, `videogame`, `podcast`,
`place`. MOTIF's candidate domains map to brand, movie, artist, book, person,
and place. Whether each is available under the event credential is *open*
until the pilot.

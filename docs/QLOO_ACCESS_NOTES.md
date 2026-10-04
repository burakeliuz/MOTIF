# Qloo access notes (checked 2026-10-04, before any live credential)

These notes record what was read in official documentation and in the public
harness package's source. None of it is a live observation. Re-check
everything marked *open* once the event credential is configured.

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
- Event quota, rate limit, expiry, and base URL: the kit says organizers
  publish them separately. *Open.* The manifest budgets (20 pilot / 60 full
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
   override, which the real request does honour. MOTIF records the preview as
   "harness --dry-run" and the env-var presence separately.
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

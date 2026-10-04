# MOTIF evidence contract (spike v0.1)

This is MOTIF's internal record contract. It does not describe Qloo's wire format.
It implements section 9 of `MOTIF_QLOO_FEASIBILITY.md` (rev 0.2) and keeps four
kinds of information apart:

| Provenance category | Meaning | Produced in this spike? |
|---|---|---|
| `qloo_observation` | A literal value returned by the Qloo harness in a live run, linked to its raw file and JSON Pointer | Yes (live runs) |
| `synthetic_fixture` | Invented test data from `fixtures/synthetic/` | Yes (synthetic runs) |
| `motif_annotation` | A manual or LLM classification of observations into a motif, with method and version | No (later phase) |
| `design_rule` | A versioned, human-authored cultural-to-olfactory mapping (`config/draft_rules.json`, inactive) | Stored, not applied |

Synthetic records can never become `qloo_observation`. The category comes from
the run mode, and the synthetic transport has no route to Qloo.

## Files of one run

```
data/raw/<run_id>/run.json              run record
data/raw/<run_id>/requests.jsonl        one request record per planned request
data/raw/<run_id>/responses/NNNN.json   harness stdout, verbatim (only for usable outputs)
data/normalized/<run_id>/run.json       run record + normalization metadata
data/normalized/<run_id>/seed_resolutions.json
data/normalized/<run_id>/observations.jsonl
data/normalized/<run_id>/coverage.json
data/normalized/<run_id>/comparison.json
data/normalized/<run_id>/facts.md       human-readable facts sheet (no verdict)
```

Raw and normalized outputs are separate trees. `renormalize` rebuilds the
normalized tree from raw files without sending requests. Run IDs look like
`live-20261004T120000Z-ab12` or `synthetic-...`.

The saved raw document is what the harness printed, not the HTTP body. The
harness projects responses (for example, `qloo api insights` prints only
`results.entities`; see `QLOO_ACCESS_NOTES.md`). Provenance therefore points
into the harness output.

## Local identifiers

All IDs minted by MOTIF start with `local:` (`local:req:0007`,
`local:obs:0007-003`, `local:seed:a24`). Qloo IDs are copied only from
returned fields (`qloo_id`, with `qloo_id_field` naming the source key) and are
never constructed.

## Records

### Run (`run.json`)

`run_id`, `mode` (`live` | `synthetic`), `synthetic`, `scenario`, `plan_name`,
`status` (`running` | `completed` | `aborted_auth_error` | `interrupted`),
`live_execution_status` (`not_live` | `executed` | `aborted_after_credential_failure` | `interrupted`),
`abort_reason`, `started_at`, `finished_at`, `versions` (adapter, parser status,
manifest, draft rule registry, harness), `readiness` (presence-only check),
`plan` (full snapshot), and `counts`.

### Request (`requests.jsonl`)

`request_id`, `seq`, `operation` (`search` | `seed_detail` | `related_entities` | `seed_tags`),
`seed_key`, `seed_input_name`, `seed_qloo_id`, `domain_key`, `requested_entity_type`,
`explainability_requested`, `comparability` (the parameters that must match
for cross-seed comparison), `harness_command` (display form, no secrets),
`signature`, `api_request_preview` and `preview_source` (from `--dry-run` or
workflow provenance), `status`, `attempts[]`, `error` (code plus redacted message),
`response_ref`, `output_shape`, `result_count`, `reused_from`, `skip_reason`,
`redaction_applied`, and timestamps. Search records also carry the
`runtime_resolution` that decided whether dependent requests were sent.

### Seed resolution (`seed_resolutions.json`)

`input_name`, `expected_types`, `status`, `method`, returned `qloo_id`,
`name`, `types`, `type_hint_match`, `candidates_returned`, `alternatives`,
`near_matches`, `selected_evidence_id`, `search_request_id`, `raw_ref`, and
`matches_runtime_decision`.

Resolution rule. Names are compared after case, accent and whitespace folding
only:

| Situation | Status |
|---|---|
| exactly one returned candidate has the seed's name | `resolved` |
| several do, exactly one has an expected type | `resolved` (others listed as alternatives) |
| several do, no unique expected-type match | `ambiguous`; nothing selected |
| none does | `unresolved`; top candidates listed as near matches |
| the search itself failed | `search_failed` |
| manual override naming a returned candidate | `resolved_manual` |
| manual override naming an ID that was not returned | `override_not_in_candidates` |
| search not sent (run stopped or budget exhausted) | `not_attempted` |

Dependent requests are sent only for `resolved` and `resolved_manual`.

### Observation (`observations.jsonl`)

One record per returned item (search candidate, seed entity, related entity, tag insight):

| Field | Content |
|---|---|
| `evidence_id`, `request_id`, `run_id` | local identifiers |
| `provenance_category`, `synthetic` | `qloo_observation` or `synthetic_fixture` |
| `kind` | `search_candidate`, `seed_entity`, `related_entity`, `tag_insight` |
| `query_context` | operation, seed, seed Qloo ID, domain, requested type, harness command, API params |
| `rank`, `result_set_size` | position in the originating result list (1-based), kept separate from scores |
| `qloo_id`, `qloo_id_field`, `name`, `types` | literal returned values |
| `attributes` | the returned `properties` object, verbatim, or `null` |
| `description_fields` | which description-like properties were present |
| `tags[]` | literal `id`, `name`, `type` (`value` if present), each with its own pointer |
| `scores[]` | `{field, value, pointer}` for `query.affinity`, `affinity`, `popularity` when numeric |
| `explanation` | returned `query.explainability` with pointer, or `null` |
| `missing_fields`, `empty_fields` | expected-but-absent and present-but-empty fields |
| `duplicate_of` | earlier `evidence_id` with the same Qloo ID in the same result list |
| `raw_ref` | `{file, pointer}` into the saved harness output |

Absent values stay absent: no default score, tag, description, or rank is filled in.

### Coverage (`coverage.json`)

Status counts; per request: shape, result count, missing and empty field counts,
and `requested_but_absent` (for example explainability). Per operation and
domain: items, unique IDs, items with tags, descriptions, affinity and
explanations, distinct tag IDs, and tag-type counts. It also lists
non-OK requests, unrecognized shapes, and whether the harness resolved
`seed_tags` input to the requested ID.

### Comparison (`comparison.json`)

Computed only across requests with identical `comparability` parameters:

- ID overlap (pairwise Jaccard), appearance distribution, IDs returned for every seed,
  and returned popularity by appearance count (global commonness check).
- Tag IDs recurring across domains for one seed.
- Sample tag shares: k/n for one seed vs K/N for the pooled seeds of the group.
  Each seed is counted from its own observations. This is labelled sample enrichment, never lift.
- Inventory of numeric fields (count, min, max). No cross-request averaging.

### Later phases (contract only, not implemented)

- **Annotation**: `motif_id`, `evidence_ids[]` with cited fields or spans, `method`
  (`manual` | `llm`), `annotation_version` (rule or prompt), `limitations`,
  `provenance_category: motif_annotation`.
- **Sensory target**: all six axes from `config/draft_rules.json`; per axis `direction`
  (a pole or `null`), `value` (nullable number; `null` means unknown, never 0 or
  a midpoint), `rule_ids[]`, `motif_refs[]`.

## Request statuses

| Status | Meaning |
|---|---|
| `ok` / `ok_empty` | Recognized output with results / with zero results |
| `partial` | Workflow reported partial or degraded results (kept, flagged) |
| `needs_input` | Harness-side resolution could not use the input |
| `unrecognized_shape` / `unparseable_output` | Output saved for inspection, not normalized |
| `auth_error` | Credential missing or rejected: the run stops |
| `forbidden` | HTTP 403. Before any success it is treated as a credential failure and the run stops; after a success it means the operation is not permitted |
| `rate_limited`, `server_error`, `transient_error`, `network_error`, `timeout` | Retried within the bounded budget (default 2 retries) |
| `rejected_request` | HTTP 400/422: parameter rejected or unsupported |
| `not_found` | Entity not found / 404 |
| `bad_usage`, `config_error`, `harness_error`, `api_error`, `harness_missing` | Other explicit failures |
| `skipped_unresolved_seed`, `skipped_after_auth_error`, `skipped_budget` | Not sent, with reason |
| `fixture_missing` | Synthetic mode only |

An empty result, an unsupported feature, an unresolved seed, and a credential
or rate-limit error are always different statuses. No status triggers a
fallback to fixtures, another endpoint, or another credential.

## Score rules

Scores are stored exactly as returned, with their field path. They are not
percentages of people, confidence values, or scent suitability. Qloo documents
affinity as normalized per query, so scores from different requests are never
averaged or compared directly. Rank is a separate field.

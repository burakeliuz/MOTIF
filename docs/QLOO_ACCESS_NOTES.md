# Qloo integration notes

How MOTIF calls Qloo, what comes back, and how each returned value stays
traceable. Live facts below were observed on the hackathon API in October 2026;
everything else comes from Qloo's public documentation and the hackathon kit.

## Requests per brand

A resolved brand costs four requests, all `GET` against
`https://hackathon.api.qloo.com` (hackathon keys only work there; the base URL
is fixed in `config/manifest.json`):

| Step | Request | Used for |
|---|---|---|
| 1 | `/search?query=<name>&take=10` | resolve the typed name to one entity; several brands → the user chooses |
| 2 | `/entities?entity_ids=<id>` | the brand's own descriptors (tags and properties) |
| 3 | `/v2/insights?filter.type=urn:entity:brand&signal.interests.entities=<id>&take=10&feature.explainability=true` | brands Qloo relates to the brand, with their descriptors |
| 4 | `/v2/insights?filter.type=urn:entity:movie&signal.interests.entities=<id>&take=10&feature.explainability=true` | films Qloo relates to the brand, with their descriptors |

Music (`urn:entity:artist`) is off by default (`--include-artist`). The
controller (`motif/agent.py`) runs these steps within a request budget; the
access layer (`motif/qloo.py`) adds bounded retries, a per-session cache (an
answered entity question or a changed application context repeats no request),
and an explicit recorded replay for local development.

## Transport

- **Direct** (default, `motif_spike/transport.py: DirectTransport`): MOTIF's own
  HTTPS client. It keeps the complete response body, so tag results and
  top-level fields such as aggregate explainability are not lost. The key comes
  from the environment (`QLOO_API_KEY`) or from a proxy that adds the
  `X-Api-Key` header; it is never written to a log, a session file, or a report.
- **Harness** (`--transport harness`): the official `qloo` CLI from
  `@qloo/qloo-harness` (≥ 0.1.26, Node.js ≥ 22.19.0), with
  `QLOO_BASE_URL` and `QLOO_TRUSTED_BASE_URL` set from the manifest.
- **No fallback.** A failed live request stays failed: no fixture, other
  endpoint, or other credential is tried. A credential error (401/403 before any
  success) stops the session. Rate limits, 5xx, and timeouts are retried at most
  twice (3 s, then 10 s). The automated tests block all network access.

## Response shapes (verified live)

Pilot `live-20261006T102530Z-61e1` and full run `live-20261006T103307Z-660d`:
45 requests, all HTTP 200, no rate limit. The parsers in `motif_spike/adapter.py`
mark these shapes `verified`.

- `/search` and `/entities` → `{"results": [entity]}`; entity tags carry `tag_id`.
- `/v2/insights` → `{"success", "results": {"entities" | "tags": [...]},
  "query": {"explainability"}}`; entity tags carry `id`.
- Entities carry descriptive namespaces beyond the documentation examples:
  `urn:tag:aesthetic_property:qloo`, `urn:tag:emotional_tone:qloo`,
  `urn:tag:personal_style:qloo`, `urn:tag:style:qloo`, and properties such as
  `aesthetic_properties` and `style_description`. These are MOTIF's main
  evidence. How Qloo produces them is not documented in the material we read, so
  MOTIF cites them as Qloo-supplied descriptors, not as ground truth.
- All six tested entity types (brand, movie, artist, book, person, place)
  return results under the hackathon key.
- `query.affinity` was observed between 0.824 and 0.988 on related entities.
  With one brand as the only signal, explainability attributes every result to
  that brand, as expected.

## Reading the data

- Tags keep their full namespace. Two tags with the same display name but
  different IDs are never merged ("Minimalist" exists both as
  `aesthetic_property` and as `personal_style`).
- Affinity ranks results within one request. MOTIF never averages scores across
  requests, never shows them as percentages, and computes no "lift".
- Qloo results describe aggregate affinities, not individuals. Related brands
  and films are shown as "references Qloo relates to" the brand; an affinity does
  not establish a shared aesthetic or audience.
- Name resolution: "Le Labo" returns two shops (`urn:entity:place`) with the
  exact name and the brand as "Le Labo Fragrances" (`urn:entity:brand`); "IKEA"
  returns only stores. MOTIF offers every returned candidate of the requested
  type and asks, instead of guessing.

## Redacted request-to-result example

From the full live run `live-20261006T103307Z-660d` (request `req 0011`):

```http
GET https://hackathon.api.qloo.com/entities?entity_ids=E12201A5-CC50-40AF-97AE-C54A2CA303F7
X-Api-Key: [REDACTED]
```

Response `200` (excerpt, literal values):

```json
{
  "results": [
    {
      "name": "Muji",
      "entity_id": "E12201A5-CC50-40AF-97AE-C54A2CA303F7",
      "types": ["urn:entity:brand"],
      "tags": [
        {"name": "Natural Materials", "type": "urn:tag:aesthetic_property:qloo", "tag_id": "urn:tag:aesthetic_property:qloo:natural_materials"},
        {"name": "Clean Lines", "type": "urn:tag:aesthetic_property:qloo", "tag_id": "urn:tag:aesthetic_property:qloo:clean_lines"},
        {"name": "Calm", "type": "urn:tag:emotional_tone:qloo", "tag_id": "urn:tag:emotional_tone:qloo:calm"}
      ]
    }
  ]
}
```

- The input "MUJI" returned 10 search candidates: one `urn:entity:brand` named
  "Muji" and stores (`urn:entity:place`). The brand was chosen; the stores were
  listed as alternatives.
- Each descriptor becomes an evidence item with its entity, source kind (`own`,
  `brand`, `movie`), request ID, and JSON Pointer to the raw response. In the
  product, every Qloo phrase on the page opens this record.

Request log of one engine session (Patagonia, 2026-10-06):

```text
local:req:0001  GET /search?query=Patagonia&take=10                                  -> 200
local:req:0002  GET /entities?entity_ids=DB4CE34E-3A63-4947-946F-9D52502C5762        -> 200
local:req:0003  GET /v2/insights?filter.type=urn:entity:brand&signal.interests.entities=DB4CE34E-...&take=10&feature.explainability=true -> 200
local:req:0004  GET /v2/insights?filter.type=urn:entity:movie&signal.interests.entities=DB4CE34E-...&take=10&feature.explainability=true -> 200
X-Api-Key: [REDACTED] on every request (never stored)
```

More request-to-result pairs with JSON Pointers: `reports/evidence_excerpt.md`.
The record format: `docs/EVIDENCE_CONTRACT.md`.

## Data handling

- Raw responses stay in the git-ignored `data/` folder. Only small curated
  excerpts with literal values and pointers are committed (`reports/`).
- MOTIF sends Qloo a brand name and entity IDs only; no personal data.
- Synthetic fixtures (`fixtures/synthetic/`) are labelled `synthetic` everywhere
  and are never used as evidence.

## Harness output (`@qloo/qloo-harness` 0.1.26)

Relevant only to `--transport harness`. Read from the package source and
`--dry-run`:

| Harness command | HTTP request | What stdout contains |
|---|---|---|
| `qloo api search --query Q --take N --json` | `GET /search?query=Q&take=N` | the `results` list, not the whole body |
| `qloo api entity --id ID --json` | `GET /entities?entity_ids=ID` | the first entity object only |
| `qloo api insights --type T --signal-entities ID --take N --json --params '{"feature.explainability": true}'` | `GET /v2/insights?filter.type=T&signal.interests.entities=ID&take=N&feature.explainability=true` | `results.entities` only; top-level fields such as aggregate explainability are dropped |
| `qloo exec entity_tags --input '{"entities":[ID],"limit":N}'` | `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=ID&take=N` | a workflow envelope with compact tags `{id, name, type, popularity, affinity}` |

Consequences: `qloo api insights --type urn:tag` prints `[]` even when tags
exist, so tag insights use `qloo exec entity_tags`; `qloo exec recommend`
drops entity tags, so related entities use `qloo api insights`. The dry-run URL
shows the config's base URL and ignores a `QLOO_BASE_URL` override that the real
request honours; the facts sheet states the base URL actually used.

Errors: `qloo api` prints `{"error": true, "code", "message"}` (exit 2 bad usage,
3 auth failed, 4 not found, 5 API error, 6 config error; the HTTP status appears
only inside `message`). `qloo exec` prints `{"error": {"code", "layer",
"retryable", "recovery"}}`. MOTIF classifies both into its request statuses
(`docs/EVIDENCE_CONTRACT.md`).

## Sources

- [Qloo public API documentation](https://github.com/qloo/docs-public): search,
  entities, insights, parameters, taste analysis, affinity scores.
- [Qloo hackathon kit](https://github.com/qloo/qloo-hackathon-kit): `docs/API_ACCESS.md`,
  `docs/SAFE_USE.md`, `docs/TROUBLESHOOTING.md`, and the CLI starter.
- `@qloo/qloo-harness` 0.1.26 from npm (help output, source, and dry runs).

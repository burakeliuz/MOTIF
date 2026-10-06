# MOTIF Qloo spike: run facts `synthetic-20261006T103904Z-ac61`

> **SYNTHETIC FIXTURE RUN: NOT QLOO DATA.** Every entity, tag, score, and ID below was invented locally to exercise the pipeline. It is not evidence about Qloo, the seed identities, or MOTIF feasibility.

| Field | Value |
|---|---|
| Mode | synthetic (scenario: main) |
| Plan | synthetic |
| Run status | completed |
| Live execution status | not_live |
| Abort reason | — |
| Started / finished (UTC) | 2026-10-06T10:39:04Z / 2026-10-06T10:39:04Z |
| Transport | fixture |
| Harness version | — |
| Base URL | not applicable |
| Adapter / parser status at run time | 0.2.0 / verified |
| Parser status at normalization | verified |
| Manifest version | synthetic-1 |
| Draft rule registry | draft-0.2 (inactive draft; not applied by the spike) |
| Feasibility verdict | not_evaluated (this sheet lists facts only) |

Parser basis: direct-transport HTTP bodies of live pilot run live-20261006T102530Z-61e1 (2026-10-06), compared with locate_items/item_view; harness-output shapes remain documentation-based.

## 1. Seed resolution

| Seed | Input | Status | Method | Returned ID | Returned name | Returned types | Candidates |
|---|---|---|---|---|---|---|---|
| alpha | Synthetic Seed Alpha | resolved | unique folded-name match | SYNTHETIC-ENT-A001 | Synthetic Seed Alpha | urn:entity:brand | 2 |
| beta | Synthetic Seed Beta | resolved | folded-name match narrowed by expected type | SYNTHETIC-ENT-B001 | Synthetic Seed Beta | urn:entity:brand | 2 |
| gamma | Synthetic Seed Gamma | ambiguous | 2 candidates share the seed name; no unique expected-type m… | — | — | — | 2 |
| delta | Synthetic Seed Delta | unresolved | no candidate name equals the seed name | — | — | — | 1 |
- `beta` alternatives: synthetic seed  BÉTA (SYNTHETIC-ENT-B002, urn:entity:artist)
- `gamma` alternatives: Synthetic Seed Gamma (SYNTHETIC-ENT-G001, urn:entity:brand); Synthetic Seed Gamma (SYNTHETIC-ENT-G002, urn:entity:brand)
- `delta` near matches: Synthetic Seed Deltaform (SYNTHETIC-ENT-D001, urn:entity:brand)

## 2. Requests

| Status | Count | Meaning |
|---|---|---|
| not_found | 1 | Entity not found / HTTP 404. |
| ok | 10 | Harness returned a recognized document with at least one re… |
| ok_empty | 1 | Harness returned a recognized document with zero results. |
| rejected_request | 1 | HTTP 400/422: parameters rejected (possibly unsupported). |
| skipped_unresolved_seed | 10 | Not sent: the seed did not resolve to exactly one entity. |
| transient_error | 1 | Harness flagged a retryable failure; retried within the bud… |

Invocations answered by local fixtures (nothing reached Qloo), including retries and excluding dry-run previews: 17. Responses reused from earlier identical live requests: 0.

Requests without a usable result:

| Request | Operation | Seed / domain | Status | Code | Message (redacted) |
|---|---|---|---|---|---|
| local:req:0008 | seed_detail | beta | not_found | NOT_FOUND | Entity not found. (synthetic fixture) |
| local:req:0011 | related_entities | beta/book | rejected_request | API_ERROR | API request failed: 400 Bad Request (synthetic fixture) |
| local:req:0012 | seed_tags | beta | transient_error | QLOO_UPSTREAM | Retry later. (synthetic fixture) |
| local:req:0014 | seed_detail | gamma | skipped_unresolved_seed | — | seed resolution: ambiguous |
| local:req:0015 | related_entities | gamma/movie | skipped_unresolved_seed | — | seed resolution: ambiguous |
| local:req:0016 | related_entities | gamma/artist | skipped_unresolved_seed | — | seed resolution: ambiguous |
| local:req:0017 | related_entities | gamma/book | skipped_unresolved_seed | — | seed resolution: ambiguous |
| local:req:0018 | seed_tags | gamma | skipped_unresolved_seed | — | seed resolution: ambiguous |
| local:req:0020 | seed_detail | delta | skipped_unresolved_seed | — | seed resolution: unresolved |
| local:req:0021 | related_entities | delta/movie | skipped_unresolved_seed | — | seed resolution: unresolved |
| local:req:0022 | related_entities | delta/artist | skipped_unresolved_seed | — | seed resolution: unresolved |
| local:req:0023 | related_entities | delta/book | skipped_unresolved_seed | — | seed resolution: unresolved |
| local:req:0024 | seed_tags | delta | skipped_unresolved_seed | — | seed resolution: unresolved |

## 3. Field coverage by operation and domain

Expected fields come from documentation; 'missing' means not returned, never a negative value.

| Group | Request statuses | Items | Unique IDs | With tags | With description | With affinity | With explanation | Distinct tag IDs | Top tag types |
|---|---|---|---|---|---|---|---|---|---|
| related_entities:artist | ok 1, ok_empty 1, skipped_unresolved_seed 2 | 4 | 4 | 3 | 0 | 4 | 0 | 4 | synthetic:tag:genre:music (4), synthetic:tag:keyword:media … |
| related_entities:book | ok 1, rejected_request 1, skipped_unresolved_seed 2 | 3 | 3 | 3 | 1 | 3 | 1 | 3 | synthetic:tag:genre:book (3), synthetic:tag:keyword:media (… |
| related_entities:movie | ok 2, skipped_unresolved_seed 2 | 10 | 7 | 9 | 3 | 10 | 3 | 6 | synthetic:tag:keyword:media (8), synthetic:tag:genre:media … |
| search | ok 4 | 7 | 7 | 1 | 1 | 0 | 0 | 1 | synthetic:tag:style (1) |
| seed_detail | not_found 1, ok 1, skipped_unresolved_seed 2 | 1 | 1 | 1 | 1 | 0 | 0 | 2 | synthetic:tag:style (1), synthetic:tag:keyword:brand (1) |
| seed_tags | ok 1, skipped_unresolved_seed 2, transient_error 1 | 4 | 4 | 0 | 0 | 3 | 0 | 4 | synthetic:tag:style (1), synthetic:tag:keyword:media (1), s… |

Requested but not returned: local:req:0004 (alpha/artist): explainability

Missing expected fields (count of items): local:req:0001: properties×1, tags×1; local:req:0003: explainability×3, popularity×1, properties×1, tags×1; local:req:0004: explainability×4, properties×4; local:req:0005: explainability×2, properties×2; local:req:0006: affinity×1, popularity×1; local:req:0007: properties×1, tags×1; local:req:0009: explainability×4, properties×4; local:req:0013: properties×2, tags×2; local:req:0019: properties×1, tags×1

## 4. Returned examples with provenance

Literal values as returned. `raw` points to the saved response (full HTTP body for the direct transport, harness output otherwise) and the JSON Pointer of the item.

### `alpha`

- Seed entity **Synthetic Seed Alpha**: Fixture Style ST1 [synthetic:tag:style]; Fixture Brand Keyword B1 [synthetic:tag:keyword:brand]. Description fields: properties.description, properties.short_description. raw `raw/synthetic-20261006T103904Z-ac61/responses/0002.json#`
- Tag insights (top 4 of 4): Fixture Style ST1 [synthetic:tag:style] affinity=0.97; Fixture Keyword K1 [synthetic:tag:keyword:media] affinity=0.9; Fixture Quiet [synthetic:tag:genre:music] affinity=0.85; Fixture Brand Keyword B1 [synthetic:tag:keyword:brand] affinity=—. raw `raw/synthetic-20261006T103904Z-ac61/responses/0006.json`
- Related **movie** (5 returned):
  - #1 Fixture Film 101 (`SYNTHETIC-ENT-M101`) affinity=0.95, popularity=0.9; tags: Fixture Keyword K1 [synthetic:tag:keyword:media]; Fixture Genre G1 [synthetic:tag:genre:media]; Fixture Streaming S1 [synthetic:tag:streaming_service:media]; Fixture Quiet [synthetic:tag:keyword:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0003.json#/0`
  - #2 Fixture Film 102 (`SYNTHETIC-ENT-M102`) affinity=0.91, popularity=0.7; tags: Fixture Keyword K2 [synthetic:tag:keyword:media]; Fixture Genre G1 [synthetic:tag:genre:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0003.json#/1`
  - #3 Fixture Film 103 (`SYNTHETIC-ENT-M103`) affinity=0.88, popularity=0.5; tags: Fixture Keyword K1 [synthetic:tag:keyword:media]; Fixture Streaming S1 [synthetic:tag:streaming_service:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0003.json#/2`
- Related **artist** (4 returned):
  - #1 Fixture Artist 101 (`SYNTHETIC-ENT-R101`) affinity=0.92, popularity=0.7; tags: Fixture Music Genre M1 [synthetic:tag:genre:music]; Fixture Keyword K1 [synthetic:tag:keyword:media]; Fixture Quiet [synthetic:tag:genre:music]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0004.json#/0`
  - #2 Fixture Artist 102 (`SYNTHETIC-ENT-R102`) affinity=0.89, popularity=0.6; tags: Fixture Music Genre M1 [synthetic:tag:genre:music]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0004.json#/1`
  - #3 Fixture Artist 103 (`SYNTHETIC-ENT-R103`) affinity=0.84, popularity=0.4; tags: no tags returned. raw `raw/synthetic-20261006T103904Z-ac61/responses/0004.json#/2`
- Related **book** (3 returned):
  - #1 Fixture Book 101 (`SYNTHETIC-ENT-K101`) affinity=0.9, popularity=0.45; tags: Fixture Keyword K1 [synthetic:tag:keyword:media]; Fixture Book Genre BK1 [synthetic:tag:genre:book]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0005.json#/0`
  - #2 Fixture Book 102 (`SYNTHETIC-ENT-K102`) affinity=0.86, popularity=0.3; tags: Fixture Book Genre BK1 [synthetic:tag:genre:book]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0005.json#/1`
  - #3 Fixture Book 103 (`SYNTHETIC-ENT-K103`) affinity=0.82, popularity=0.28; tags: Fixture Book Genre BK2 [synthetic:tag:genre:book]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0005.json#/2`

### `beta`

- Related **movie** (5 returned):
  - #1 Fixture Film 101 (`SYNTHETIC-ENT-M101`) affinity=0.93, popularity=0.9; tags: Fixture Keyword K1 [synthetic:tag:keyword:media]; Fixture Genre G1 [synthetic:tag:genre:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0009.json#/0`
  - #2 Fixture Film 103 (`SYNTHETIC-ENT-M103`) affinity=0.9, popularity=0.5; tags: Fixture Keyword K1 [synthetic:tag:keyword:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0009.json#/1`
  - #3 Fixture Film 201 (`SYNTHETIC-ENT-M201`) affinity=0.87, popularity=0.3; tags: Fixture Keyword K2 [synthetic:tag:keyword:media]. raw `raw/synthetic-20261006T103904Z-ac61/responses/0009.json#/2`

### `gamma`

Search candidates only (see section 1); no dependent request was sent or none returned data.

### `delta`

Search candidates only (see section 1); no dependent request was sent or none returned data.

## 5. Overlap between seeds (comparable requests only)

**related_entities / urn:entity:movie**. Seeds: alpha, beta; unique results per seed: alpha 4, beta 5

| A | B | Shared IDs | Union | Jaccard |
|---|---|---|---|---|
| alpha | beta | 2 | 7 | 0.2857 |

Returned IDs by number of seeds they appear for: 1 seed(s): 5, 2 seed(s): 2.
Returned for every seed: Fixture Film 101, Fixture Film 103.
Returned `popularity` by appearance count: 1: median 0.275 (n=4); 2: median 0.7 (n=2).

**related_entities / urn:entity:artist**. Seeds: alpha, beta; unique results per seed: alpha 4, beta 0

Fewer than two seeds returned results in this group; overlap is not informative.

**related_entities / urn:entity:book**. Seeds: alpha; unique results per seed: alpha 3

Fewer than two seeds returned results in this group; overlap is not informative.

**seed_tags / limit 5**. Seeds: alpha; unique results per seed: alpha 4

Fewer than two seeds returned results in this group; overlap is not informative.

## 6. Tag IDs recurring across domains (per seed)

Same tag ID on related entities of different domains for one seed. Different IDs with similar names are not merged.

- `alpha`: 10 distinct tag IDs across artist, book, movie; 1 appear in two or more domains.
  - Fixture Keyword K1 `synthetic:tag:keyword:media:fx_k1` [synthetic:tag:keyword:media]: artist, book, movie; 4 entities
- `beta`: 4 distinct tag IDs across movie; 0 appear in two or more domains.

## 7. Sample tag shares (retrieved samples only; not lift)

k/n = seed's results carrying the tag; K/N = pooled results of all seeds in the same group. Ratios from top-N samples are descriptive only and are not population lift.

**urn:entity:movie** (pooled unique entities: 7)

| Seed | Tag | Tag type | k/n | K/N | Sample enrichment |
|---|---|---|---|---|---|
| alpha | Fixture Genre G1 | synthetic:tag:genre:media | 2/4 | 2/7 | 1.75 |
| alpha | Fixture Keyword K1 | synthetic:tag:keyword:media | 2/4 | 2/7 | 1.75 |
| alpha | Fixture Streaming S1 | synthetic:tag:streaming_service:media | 2/4 | 2/7 | 1.75 |
| alpha | Fixture Quiet | synthetic:tag:keyword:media | 1/4 | 1/7 | 1.75 |
| alpha | Fixture Keyword K2 | synthetic:tag:keyword:media | 1/4 | 2/7 | 0.875 |
| beta | Fixture Genre G2 | synthetic:tag:genre:media | 2/5 | 2/7 | 1.4 |
| beta | Fixture Keyword K1 | synthetic:tag:keyword:media | 2/5 | 2/7 | 1.4 |
| beta | Fixture Genre G1 | synthetic:tag:genre:media | 1/5 | 2/7 | 0.7 |
| beta | Fixture Keyword K2 | synthetic:tag:keyword:media | 1/5 | 2/7 | 0.7 |

## 8. Quantitative fields returned

| Item kind | Field | Values | Min | Max | Requests |
|---|---|---|---|---|---|
| related_entity | popularity | 16 | 0.2 | 0.9 | 4 |
| related_entity | query.affinity | 17 | 0.8 | 0.95 | 4 |
| search_candidate | popularity | 7 | 0.1 | 0.61 | 4 |
| seed_entity | popularity | 1 | 0.61 | 0.61 | 1 |
| tag_insight | affinity | 3 | 0.85 | 0.97 | 1 |
| tag_insight | popularity | 3 | 0.3 | 0.8 | 1 |

## 9. Notes

- Overlap and recurrence use returned Qloo IDs only; display names are never matched or merged.
- Only requests with identical comparability parameters (operation, entity type, take, explainability or limit) are compared.
- Affinity and popularity are reported as returned; they are not percentages of people, confidence, or scent suitability, and are not averaged across requests.
- Sample shares compare tag frequency inside the retrieved top-N results of seeds in the same comparable group. They are not lift: there is no population denominator.
- This sheet establishes what Qloo returned for these requests. It does not establish shared aesthetics, audience preferences, motif labels, or fragrance suitability.

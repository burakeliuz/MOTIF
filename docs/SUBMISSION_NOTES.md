# MOTIF submission notes (working skeleton)

Running notes for the Devpost submission, organized by the six items of the Qloo
hackathon kit's submission guide (`docs/SUBMISSION.md` in `qloo/qloo-hackathon-kit`;
summary in `docs/QLOO_ACCESS_NOTES.md`). Every roadmap stage adds to this file.
`TBD` marks what later stages decide.

Status: stage 2 (live Qloo feasibility) done on 2026-10-06. Product decisions are
pending (stage 3, `MOTIF_BUILD_SPEC.md`).

## 1. Product problem statement

Draft: Brands, events, and creative teams that want a scent identity usually
start from mood boards and adjectives that are hard to justify. MOTIF translates
a brand's cultural context into an explainable olfactory direction and a
perfumer brief. Every cultural claim is traced back to returned Qloo data, and
every sensory choice is traced to a named, human-authored design rule.

MOTIF produces a creative direction. It does not produce a formula, a dosage, or
a prediction that an audience will like a scent.

- Target user and use case: TBD (stage 3)
- Final wording: TBD (stage 6)

## 2. Qloo workflow used and why it fits

Used in the feasibility stage, against `https://hackathon.api.qloo.com`:

| Step | Request | Why |
|---|---|---|
| Resolve the input | `GET /search?query=<name>&take=10` | Get Qloo's own entity ID and type. MOTIF accepts only an exact name match, narrowed by the expected type, and reports ambiguity instead of guessing. |
| Describe the input | `GET /entities?entity_ids=<id>` | The entity's own tags, including the `aesthetic_property`, `emotional_tone`, and `personal_style` namespaces. |
| Cross-domain context | `GET /v2/insights?filter.type=urn:entity:<brand\|movie\|artist\|book\|person\|place>&signal.interests.entities=<id>&take=10&feature.explainability=true` | Related entities with affinity, tags, and descriptive properties (for example `style_description`). |
| Tag insights | `GET /v2/insights?filter.type=urn:tag&signal.interests.entities=<id>&take=20` | Tested. Without a namespace filter, the results were generic venue and payment tags, so the feasibility report recommends dropping this step. |

Why our own HTTPS client instead of the `qloo` CLI: the organizers' kickoff
email allows participants to build their own tooling. Our client keeps the
complete response body, while the CLI prints only part of it (for example,
`qloo api insights` drops tag results and the aggregate explainability). The
client sends no key header itself: the key is supplied by the runtime
environment and never enters the code, logs, or data files.

Stage 3 keeps: the seed's own descriptor tags, plus related brands, movies, and
artists (see `reports/feasibility.md`, section 10).

- Final runtime flow (agentic steps, MCP or not): TBD (stage 3/4)

## 3. Redacted request-to-result explanation

Example from the full live run `live-20261006T103307Z-660d` (request `req 0011`; the credential is never stored):

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

Entity and tag choices:

- The input "MUJI" returned 10 search candidates. One was a `urn:entity:brand`
  named "Muji", and the others were stores (`urn:entity:place`). MUJI's expected
  type is brand, so the brand was chosen and the stores were listed as
  alternatives.
- Tags are kept with their full namespace. Two tags with the same display name
  but different IDs are never merged; for example, "Minimalist" exists both as
  `aesthetic_property` and as `personal_style`.

More request-to-result pairs, with JSON Pointers: `reports/evidence_excerpt.md`.

- How the final product shows this to users: TBD (stage 5)

## 4. Demo or screenshots

TBD (stage 6). It must contain no credential and no personal data. Whether to
host a demo is a stage-3 decision.

## 5. Setup from a clean environment

Current (feasibility playground; Python 3.9+, standard library only):

```sh
git clone https://github.com/burakeliuz/MOTIF && cd MOTIF
python3 -m unittest                                   # offline tests; network blocked
python3 -m motif_spike run --mode synthetic           # no key, no network
# with a hackathon key provided by the environment (QLOO_API_KEY or a proxy-injected credential):
python3 -m motif_spike check
python3 -m motif_spike run --mode live --plan pilot
```

- Final product setup, verified in a clean environment: TBD (stage 6)

## 6. Known limitations

Known from the feasibility stage (`reports/feasibility.md`):

- Qloo returns no olfactory information. The cultural-to-scent step is MOTIF's
  own versioned design rules, and Qloo cannot validate it.
- How Qloo produces its descriptive fields (`aesthetic_properties`,
  `style_description`, …) is undocumented in the material available to us.
  MOTIF cites them as Qloo-supplied descriptors, not ground truth.
- Some descriptors are common across very different brands (for example
  `personal_style` "minimalist" on 4 of 5 test brands). They carry little
  distinguishing weight.
- Affinity scores rank results within one request only. They are not
  percentages of people and are not compared across requests. No population
  "lift" is computed.
- Results describe aggregate cultural affinities, not individuals. An affinity
  between two entities does not show that they share an aesthetic.
- Tested only on five globally known brands. Coverage for smaller inputs is
  unknown, and live results can change over time.
- Event quota and rate limits are unpublished.

- Limitations of the final product: TBD (stages 3–6)

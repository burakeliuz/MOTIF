# MOTIF submission notes (working skeleton)

Running notes for the Devpost submission, organized by the six items of the Qloo
hackathon kit's submission guide (`docs/SUBMISSION.md` in `qloo/qloo-hackathon-kit`;
summary in `docs/QLOO_ACCESS_NOTES.md`). Every roadmap stage adds to this file.
`TBD` marks what later stages decide.

Status: stage 2 (live Qloo feasibility) done on 2026-10-06; stage 3 product
decisions written in `MOTIF_BUILD_SPEC.md` (rev 0.1, 2026-10-06). Worked design
examples: `reports/design_examples.md`.

## 0. Event requirements (kept apart from the kit's advice)

Official (Qloo Agentic Hackathon, [qloo.devpost.com](https://qloo.devpost.com/)).
Checked on 2026-10-06 through search-engine excerpts of the official page and
rules, because devpost.com could not be opened from the build environment.
The owner must confirm these on the page itself.

- Deadline: October 30, 2026, 11:45 pm EDT (October 31, 06:45 Türkiye time).
- A functional demo hosted externally that judges can try end to end; local-only
  or private-access submissions do not qualify. A demo video is reported as not required.
- A public repository with all code, assets, and run instructions, plus a text description.
- Judging criteria: Technological Implementation, Design, Potential Impact,
  and Quality of the Idea (no weights seen).

The six items below follow the kit's `docs/SUBMISSION.md`. They are advice, not
the official rules.

## 1. Product problem statement

Draft: Brands, events, and creative teams that want a scent identity usually
start from mood boards and adjectives that are hard to justify. MOTIF translates
a brand's cultural context into an explainable olfactory direction and a
perfumer brief. Every cultural claim is traced back to returned Qloo data, and
every sensory choice is traced to a named, human-authored design rule.

MOTIF produces a creative direction. It does not produce a formula, a dosage, or
a prediction that an audience will like a scent.

- Target user (stage 3): brand, creative, or experience teams, and the
  perfumers working for them, who start a scent identity (a store scent, a
  launch event, a brand fragrance) and need a brief they can justify.
- Product flow (stage 3):
  1. The user enters a brand.
  2. The agent resolves it with Qloo search and asks when the name is ambiguous.
  3. The agent collects the brand's own Qloo descriptors and related brands,
     movies, and music artists.
  4. A deterministic engine maps descriptors to motifs, motifs to six sensory
     axes, and axes to a small, sourced material palette.
  5. The output is a short perfumer brief with an evidence panel; open axes
     stay open.
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

Stage 3 keeps: the seed's own descriptor tags (`/entities`), plus related
brands, movies, and artists (`/v2/insights`, take 10, without explainability,
which with one seed always attributes everything to the seed). It drops
unscoped tag insights, people, books, and places (`MOTIF_BUILD_SPEC.md`,
sections 4–5).

Runtime flow (decided in stage 3, built in stage 4):

- An agent with six bounded tools: resolve, ask the user, fetch the seed
  description, fetch related entities, run the engine, finish.
- The LLM (Claude, optional) chooses questions and writes prose.
- Classification, scores, and material choices come only from the
  deterministic engine.
- Without an LLM key, a fixed planner runs the same tools.
- No MCP in the MVP.

What Qloo demonstrably adds (stage-3 design examples, same rules with and without relations):

| Seed | Own Qloo description only | Plus Qloo relations |
|---|---|---|
| MUJI | 0 sensory axes | 3 axes (light, polished, natural) |
| Ralph Lauren | 0 axes | 2 axes (dense, polished) |
| Comme des Garçons | 0 axes | 1 axis |
| A24 | 0 axes | 0 axes |
| Nike | 0 axes | 0 axes |

Relations mostly corroborate motifs that the brand's own tags already hint at.
In two cases they add a direction the own tags do not contain: Ralph Lauren
"dense" and Comme des Garçons "polished". Five brands and a lexicon tuned on
them support no general claim.

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

- How the final product shows this to users: the result screen lists every motif
  with its literal Qloo values, entity, request, and JSON Pointer
  (`MOTIF_BUILD_SPEC.md`, section 14). Screens: TBD (stage 5).

## 4. Demo or screenshots

A hosted demo is required by the official rules (section 0), so MOTIF will be
deployed (`MOTIF_BUILD_SPEC.md`, section 15). The provider is chosen in stage 5.
Screenshots: TBD (stage 6). They must contain no credential and no personal data.

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

- Stage 3 additions:
  - The motif lexicon was tuned on the same five brands it is shown on; a
    held-out check is planned.
  - Seven of twelve candidate motifs (for example experimental, provocative,
    heritage) have no translation rule, so brands whose identity rests on them
    (Comme des Garçons, A24) get little or no sensory direction.
  - "Intimate" is too common in Qloo style tags to count as evidence, so the
    intimate/projecting axis cannot be set from evidence today.
  - Material descriptors come from supplier pages located by search but not
    yet read in full.
- Limitations of the final product: TBD (stages 4–6)

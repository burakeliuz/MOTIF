# MOTIF build specification

Revision 0.1 · 2026-10-06 · Stage 3 (product decisions) · Owner: Burak Eliuz

This document turns the stage-2 findings (`reports/feasibility.md`,
recommendation **narrow**) into a buildable MVP. It is the contract for
stage 4 (engine and agentic flow) and stage 5 (interface and hosting).
Worked numbers for every rule below are in `reports/design_examples.md`.

How to read it:

- **Observed** facts come from live Qloo responses (stage-2 runs of 2026-10-06) and cite them.
- **Design** choices are ours. Weights, thresholds, cue lists, and material
  profiles are design parameters with explicit versions, not validated statistics.
- **Verified elsewhere** marks facts taken from official pages, with how they were checked.

## 1. Decision

**Continue with a narrowed scope.**

- Live data gives traceable, distinct cultural evidence for brands through
  three surfaces: the seed's own descriptor tags, related brands, and related
  movies (related music artists add little but cost nothing).
- Under the same rules, 2 of 5 test brands (MUJI, Ralph Lauren) reach a
  multi-axis direction.
- One test brand (Comme des Garçons) reaches one axis.
- Two test brands (A24, Nike) reach none: one because of rule coverage, one
  because its descriptors are thin.

The MVP must show those failures honestly, not hide them.

What MOTIF produces is a creative direction and a starting material proposal
for a perfumer. It is not a formula, a dosage, a regulatory assessment, or a
prediction that anyone will like the scent.

## 2. Competition requirements, kit advice, and our own goals

Kept apart on purpose.

### 2.1 Official requirements (Qloo Agentic Hackathon, Devpost)

Source: the event page [qloo.devpost.com](https://qloo.devpost.com/). This
environment could not open devpost.com (network policy). The items below come
from search-engine excerpts of the official page and rules on 2026-10-06.
**The owner must confirm them on the page itself** (section 17).

- Deadline: **October 30, 2026, 11:45 pm EDT = October 31, 2026, 06:45 Türkiye time.**
  This matches the date recorded in earlier stages.
- **A functional, hosted demo is required:** a live, working app that judges
  can try end to end. Submissions that only run locally or rely on private
  access do not qualify. A demo video is reported as not required.
- A public code repository (GitHub, GitLab, or Bitbucket) with all source
  code, assets, and instructions needed to run the project.
- A text description of what the project does and its key features.
- Judging criteria (no weights seen in the excerpts):
  - **Technological Implementation:** how thoroughly and skillfully the
    project uses Qloo; working, non-trivial code.
  - **Design:** a complete, coherent product experience, not a proof of concept.
  - **Potential Impact:** a credible, specific case for a real problem and
    audience, addressed by what is demonstrated.
  - **Quality of the Idea:** a creative, non-obvious use of Qloo and a
    genuine understanding of the problem space.

### 2.2 Kit recommendations (not rules)

Source: `qloo/qloo-hackathon-kit` `docs/SUBMISSION.md`, read 2026-10-06.

- Six submission items: problem statement; Qloo workflow and why; a redacted
  request-to-result explanation; a demo or screenshots without credentials or
  personal data; clean-environment setup steps; known limitations.
- Judges "should consider usefulness, technical execution, provenance and user
  clarity, responsible data handling, and reproducibility". The kit itself
  says the exact rubric is published separately; that is section 2.1.

### 2.3 MOTIF quality goals (ours)

- Every cultural claim in the output traces to a returned Qloo value (request
  ID + JSON Pointer).
- Every sensory and material choice traces to a versioned rule.
- Unknown stays unknown.
- Identical evidence and versions give identical scores and selections.
- Failures (insufficient, conflicting, ambiguous, API error) are first-class
  screens, not hidden.

## 3. Users, problem, and core flow

**Primary user:** a brand, creative, or experience team (or the perfumer
working for them) starting a scent identity: a signature store scent, a launch
event, or a brand fragrance.

**Problem:** scent briefs usually start from adjectives that nobody can trace
or defend ("make it feel like us"). MOTIF grounds the brief in what Qloo
returns about the brand and its cultural neighbourhood, shows the chain from
each returned descriptor to each sensory decision, and states plainly what the
evidence does not decide.

**Core flow (MVP):**

1. The user enters one reference (a brand or creative identity) and its type
   (default: brand).
2. The agent resolves it with Qloo search. On ambiguity it asks the user to
   choose among the returned candidates.
3. The agent collects evidence: the seed's own description, related brands,
   movies, and artists.
4. The deterministic engine classifies cues into motifs, derives sensory
   targets, and ranks palette materials.
5. Depending on the engine status:
   - **Insufficient or conflicting:** the agent explains what is missing or in
     conflict and offers the next step (choose a direction, add a reference,
     or stop).
   - **Otherwise:** a short perfumer brief is produced with an evidence panel
     and a JSON download.

## 4. Scope

### Included in the MVP

- Single-reference input with type selection; entity disambiguation by the user.
- Qloo evidence: seed `/entities` tags; `/v2/insights` related `brand`,
  `movie`, and `artist` (take 10).
- Lexicon classifier (`config/motif_lexicon.json`), five translation rules R1–R5
  (`config/draft_rules.json`), and 8-material palette
  (`config/material_palette.json`).
- Deterministic matching and composition rules, gates against misleading scores,
  explicit conflict and unknown handling.
- An agent loop with a bounded tool set (LLM-driven when a key is configured;
  a deterministic planner otherwise).
- Brief: a structured JSON (engine) plus prose (LLM, or a template when there is no LLM).
- Web UI (5 screens, section 14), hosted demo, and clearly labelled live,
  recorded, and synthetic modes.

### Deferred (with reason)

- **Unscoped tag insights** (`filter.type=urn:tag`): generic venue and payment
  tags at affinity ≈ 1 (stage 2, section 6).
- **People and books:** occupations, subject matter, 40% of books untagged.
- **Places:** location-driven results. A possible later source of `ambience`/`decor` cues.
- **Multi-reference input** (2–3 references merged): useful but untested; the
  support counting across seeds needs its own design.
- **Rules for unmapped motifs** (experimental, provocative, heritage,
  industrial, playful, melancholic, romantic): no justified rule yet. A24 and
  Comme des Garçons show the cost of this gap.
- **LLM classification of descriptors the lexicon misses:** possible later as
  *suggestions* the user must accept; never automatic in the MVP.
- **Seed-only vs model-memory baseline evaluation:** see `docs/DEFERRED_DESIGN.md`.
- Dosage, formula, IFRA or regulatory checks, cost, sourcing, user accounts, and payments.

## 5. Qloo access and provenance

Transport: the existing `motif_spike/transport.py` `DirectTransport` (HTTPS to
`https://hackathon.api.qloo.com`). The key is added by the server environment,
never by the browser. The harness transport stays available. No third
integration is added.

| Step | Request | Fields used | Notes |
|---|---|---|---|
| Resolve | `GET /search?query=<name>&take=10` (+ `types=<urn>` when the user picked a type) | `entity_id`, `name`, `types`, `disambiguation`, `popularity` | Candidates are only ever chosen from returned IDs |
| Seed description | `GET /entities?entity_ids=<id>` | `properties.short_description`; `tags[]` (`tag_id`, `name`, `type`) in namespaces `aesthetic_property`, `personal_style`, `emotional_tone` | Other namespaces are kept as context, not as cues |
| Related | `GET /v2/insights?filter.type=urn:entity:{brand\|movie\|artist}&signal.interests.entities=<id>&take=10` | `entity_id`, `name`, `query.affinity` (rank only), `tags[]` (`id`, `name`, `type`) in `aesthetic_property`/`emotional_tone` (brand) and `style` (movie, artist) | `feature.explainability` dropped: with one seed it always attributes everything to the seed (stage 2, section 7) |

- Budget: at most **5 Qloo requests per resolved reference** (1 search, 1
  entities, 3 insights) and **8 per session**. Retries follow the existing
  rule: bounded, never to another endpoint or credential.
- Cache: identical successful requests are reused within a session, and
  across sessions for 24 h (design parameter). Cached results are labelled
  with their original fetch time.
- Provenance: every evidence item keeps
  `{request_id, request (method, path, non-secret params), fetched_at,
  json_pointer, literal value, tag_id}`. The response body is kept server-side
  for the session and is not served to the browser beyond the literal values
  shown.

## 6. Ambiguity and user questions

| Situation (observed examples) | Behaviour |
|---|---|
| Exactly one exact-name candidate of the chosen type ("MUJI" → 1 brand + 7 places, req 0010) | Choose it; show the others as "also returned" with their types |
| Several exact-name candidates of the chosen type, or type "any" with several types ("Ralph Lauren" → brand, person, author, req 0037) | **Ask:** list returned candidates (name, type, `disambiguation`, short description if present); no default selection |
| No exact-name match | **Ask:** show near matches; the user may pick one or rephrase. Never pick a "similar" entity silently |
| Zero results | Empty state: "Qloo returned no entity for this name"; suggest checking spelling or type |
| The same display name for different tag IDs | Never merged; shown with their namespace |
| A selected entity of an unexpected type (for example a person) | Allowed. The engine runs, and the brief says the related evidence describes that entity's audience neighbourhood, not a brand |

## 7. Motif classification (`config/motif_lexicon.json`, lexicon-0.1)

- **Method:** deterministic lexicon matching. Each match is stored as a
  `motif_annotation` with `method: "lexicon"`, `lexicon_version`, the matched
  cue, and the evidence item.
- **Inputs:** only the namespaces listed in section 5. Tags with the literal
  name "null" are ignored. Music-genre names inside style tags are excluded
  ("Baroque Pop" is not opulence). A tag whose whole name is a bare axis pole
  word ("Raw", "Polished", "Warm") never sets anything.
- **Commonness:** cue groups matched for ≥ 4 of the 5 reference seeds are
  *common* and count only as context. In lexicon-0.1 these are `intimate`,
  `minimalist`, `playful`, and `precise`. The reference set is frozen per
  lexicon version.
- **Support and strength** (design parameters):
  - Support counts distinct **source kinds** (`own`, `brand`, `movie`,
    `artist`) with at least one non-common cue.
  - Repeats of a cue or tag ID inside one source kind add nothing.
  - `own` and `brand` are **anchors**.
  - **strong** = anchored and ≥ 3 source kinds.
  - **moderate** = anchored and ≥ 2 source kinds, or ≥ 2 distinct non-common
    own cues.
  - **weak** = anything below moderate.
  - **context_only** = common cues only.
  - A motif is **active** when strong or moderate.
- **Why anchors:** media-only evidence describes film or music form. For
  example, Nike's related boxing films carry "Handheld intimacy" and "Close
  up intimacy" (req 0031). Such evidence may corroborate a motif but must not
  create one.
- **Known weaknesses:**
  - Phrase matching misreads some tags ("Quiet deadpan humor" was removed as a
    cue for this reason; "Understated humor" still matches restrained).
  - The lexicon was tuned on the five seeds it is shown on. Stage-4 task T1
    checks it on held-out brands.
  - The UI lets the user reject an individual cue match. The rejection is
    stored as a `manual` annotation and re-runs the engine.

## 8. Sensory axes and translation

### 8.1 Axes

The six baseline axes and their pole order are unchanged:
`warm_cool`, `light_dense`, `raw_polished`, `natural_synthetic`,
`intimate_projecting`, `sweet_dry`. Each axis has the state `unknown` (value
`null`), `target` (a pole), or `conflicted` (value `null`). There is no zero,
midpoint, or neutral value.

### 8.2 Rules (`config/draft_rules.json`, draft-0.2, unchanged)

| Rule | Active motif | Moves | Decides nothing about |
|---|---|---|---|
| R1 | restrained | light_dense → light | projection, sweetness, temperature |
| R2 | intimate | intimate_projecting → intimate | lightness, longevity |
| R3 | precise | raw_polished → polished | natural/synthetic, temperature |
| R4 | opulent | light_dense → dense | sweetness, projection |
| R5 | natural | natural_synthetic → natural (impression) | ingredient origin, safety, sourcing |

The other seven motifs are shown with their evidence and never move an axis.
`restrained → intimate` stays removed. In lexicon-0.1, R2 cannot fire, because
"intimate" is a common cue in the reference set. This is an observed property
of the data, recorded as a limitation.

### 8.3 Two separate confidences

Each target carries:

- `evidence_strength`: the strongest active motif behind it;
- `rule_confidence`: `draft_hypothesis` for all R1–R5.

The UI shows both side by side and never multiplies them into one score.

### 8.4 Missing, weak, and contradictory evidence

- Missing: the axis stays `unknown`, and the brief says it is open.
- Weak: the motif is listed under "seen but not enough"; it never moves an axis.
- **Contradictory:** two active motifs push the same axis to opposite poles
  (only R1 vs R4 is possible today). The axis becomes `conflicted`, no
  material is ranked on it, and the agent asks the user to choose a pole or
  leave it open. The user's choice is stored as a `manual` override with its
  own label. The real data showed no conflict, so the acceptance test uses a
  synthetic fixture (`reports/design_examples.md`, section 6).

## 9. Material palette and matching

### 9.1 Palette (`config/material_palette.json`, palette-0.1)

| ID | Material | Kind | Profile (MOTIF's creative mapping) | Role |
|---|---|---|---|---|
| M01 | HEDIONE® (dsm-firmenich 964898) | molecule | light, polished | heart |
| M02 | Bergamot oil (Italy) | natural extract | light, natural | top |
| M03 | ISO E SUPER® (IFF) | material grade | polished | heart/base |
| M04 | AMBROX® SUPER (dsm-firmenich 909158) | molecule | dense, projecting | base |
| M05 | HABANOLIDE® (dsm-firmenich 947303) | molecule | polished, warm | base |
| M06 | Vetiver oil Haiti | natural extract | natural, raw, dry | base |
| M07 | Labdanum absolute | natural extract | dense, warm | base |
| M08 | Orris butter | natural extract | natural | heart |

- Every entry keeps three things apart:
  - `source`: the supplier URL and the descriptor excerpt;
  - `motif_profile` and `basis_terms`: MOTIF's reading, a `design_rule`;
  - `uncertainties`.
- A specific material grade is never treated as a generic note or accord, and
  vice versa.
- **Verification status:** every entry is `source_located_excerpt_only`. The
  supplier's own page was found, but this environment could not open supplier
  domains, so the descriptors are search excerpts. Stage-4 task T2 must read
  the full pages (or the owner checks them) before the demo cites them.
- No palette entry represents the `intimate` pole. An intimate target would
  stay unmatched, and the brief would say so.

### 9.2 Deterministic scoring

For targeted axes `A` (state `target` only), with weight `w(a)` = 1.0 when the
evidence is strong and 0.6 when moderate:

```
score(m) = Σ_{a∈A} w(a) · s(m,a) / |A|
s = +1 if profile(m,a) == target(a); −1 if profile has the opposite pole; 0 if profile is absent
```

- The denominator is the number of targeted axes, not the axes the material
  covers. A material matching one of three targets cannot outscore one
  matching three.
- Scores are rounded to 3 decimals for display only.

### 9.3 Composition rules

1. **Gate:** with fewer than 2 targeted axes, or fewer than 2 eligible
   materials, there is no composition. The UI shows the ranked candidates
   under "not enough direction for a composition" (Comme des Garçons case).
2. **Eligible** means score > 0 and no opposite pole on any targeted axis.
3. **Coverage pass:** visit the targeted axes by weight (descending), then in
   canonical axis order. For each axis not yet covered, add the
   highest-scoring eligible material that matches it.
4. **Fill pass:** add eligible materials by score until 3 are selected
   (maximum 4).
5. **Slots:** 1 top, 2 heart, 2 base. A `heart|base` material takes a heart
   slot when no heart is selected yet, otherwise a base slot.
6. **Ties** are broken by fewer unrequested properties, then `material_id`.
7. **Unrequested properties:** any profile pole on an axis whose state is not
   `target` is listed as "creative choice, not evidence". Examples: M04 brings
   projection, M05 warmth.

Expected results (design examples):

| Seed | Selection |
|---|---|
| MUJI | M02 top, M01 heart, M03 base |
| Ralph Lauren | M03 heart, M04 base, M05 base; top open |
| Comme des Garçons | gated: one axis |
| A24 | no targets |
| Nike | no targets |

## 10. Output schema (brief JSON, `brief_schema` 0.1)

```json
{
  "schema_version": "brief-0.1",
  "data_label": "live | recorded | synthetic",
  "versions": {"engine": "...", "lexicon": "lexicon-0.1", "rules": "draft-0.2", "palette": "palette-0.1",
               "llm": {"model": "...", "effort": "...", "prompt_version": "..."} | null},
  "seed": {"input": "MUJI", "qloo_id": "E12201A5-...", "name": "Muji", "type": "urn:entity:brand",
           "resolution": "auto_single_match | user_choice", "alternatives": [...]},
  "evidence": [{"evidence_id": "local:ev:...", "source_kind": "own|brand|movie|artist", "entity": "...",
                "tag_name": "...", "tag_id": "...", "request_id": "...", "json_pointer": "...", "fetched_at": "..."}],
  "motifs": [{"motif": "restrained", "strength": "strong", "active": true, "source_kinds": [...],
              "evidence_ids": [...], "context_only_evidence_ids": [...], "rejected_by_user": [...]}],
  "axes": {"light_dense": {"state": "target", "value": "light", "rule_ids": ["R1"], "evidence_strength": "strong",
                           "rule_confidence": "draft_hypothesis"},
           "warm_cool": {"state": "unknown", "value": null}},
  "materials": {"status": "composed | gated_insufficient_axes | no_targets",
                "selected": [{"material_id": "M02", "role": "top", "score": 0.533, "matches": [...],
                              "unrequested_properties": [], "source_status": "source_located_excerpt_only"}],
                "excluded": [{"material_id": "M06", "reason": "opposite pole on raw_polished"}]},
  "open_questions": ["temperature, projection and sweetness are not decided by the evidence"],
  "brief_text": {"author": "llm | template", "text": "..."},
  "disclaimer": "Creative direction, not a formula..."
}
```

Everything except `brief_text` and `versions.llm` is produced by the engine.

## 11. Agent design

### 11.1 Tools (server-side functions; the only actions the agent can take)

| Tool | Does | Allowed when |
|---|---|---|
| `resolve_reference(name, type)` | Qloo search; returns the candidates | At start, or after the user rephrases |
| `ask_user(question, options)` | Pauses the session and shows options in the UI | Ambiguity (section 6), conflict (8.4), insufficient evidence, budget reached |
| `fetch_seed_description(entity_id)` | `/entities` | The entity was chosen from returned candidates |
| `fetch_related(entity_id, domain)` | `/v2/insights`, domain ∈ {brand, movie, artist} | After the seed description; budget left |
| `run_engine()` | Classification, targets, and materials over the session evidence | At least the seed description is present |
| `finish(brief_prose)` | Ends the session with prose for the engine output | `run_engine` has returned in this state |

Code (not the model) enforces the rules:

- the request budget;
- the allowed domains;
- that an entity ID must come from a returned candidate list;
- that `finish` is only possible after `run_engine`.

### 11.2 Decisions the agent makes

1. **Which candidate:** auto only in the single-match case; otherwise it asks.
2. **Whether to fetch all three domains:** the MVP always fetches brand,
   movie, and artist (3 calls). The agent may skip artist when the user asks
   for speed. A deliberately small decision space.
3. **What to do with the engine status:**
   - `composed`: write the brief.
   - `gated_insufficient_axes` or `no_targets`: explain what is missing (from
     the engine's motif table) and ask whether to stop or try another
     reference.
   - `conflicted` axis: ask the user to choose.
4. **How to phrase the brief:** prose only, from the engine JSON.

### 11.3 Stop conditions

- Brief finished.
- User stops.
- Credential failure (401/403): the session ends, the error is shown, and
  there is no fallback.
- Budget exhausted.
- 3 questions without a usable answer.

### 11.4 Deterministic planner (no LLM key)

The same tools in a fixed order:

1. Resolve; ask on ambiguity.
2. Fetch the seed description.
3. Fetch brand, movie, and artist.
4. Run the engine.
5. Template brief.

This is the reference path for tests.

### 11.5 Guarding the LLM's prose

- The prompt gives the model only the engine JSON (no raw Qloo bodies).
- The code validates the returned prose:
  - every material named must be in `materials.selected`;
  - every axis with state `unknown` or `conflicted` must be named as open;
  - no percentage or score other than those in the JSON may appear.
- On a validation failure: one retry with the error message, then the
  template brief, with a visible note "LLM text failed validation".

## 12. LLM choice and cost

- **Provider and model (proposal):** Anthropic Claude via the official
  `anthropic` Python SDK.
  - Default model: `claude-opus-5-5` (USD 4 per million input tokens, 20 per
    million output; cache reads 0.20). Pricing from the Claude API reference
    bundled with this environment, cached 2026-09-25.
  - Cheaper option: `claude-sonnet-5-5` (2 / 10 per million). **The owner decides.**
- **Request settings:**
  - adaptive thinking with `output_config.effort` set explicitly (`low` for
    the planner, `medium` for prose);
  - `tool_choice: auto` with `strict: true` tools, because forced tool choice
    is rejected on these models;
  - server-side refusal fallback (`fallbacks: "default"` with beta
    `server-side-fallback-2026-07-01`);
  - stable system prompt and tool list first, for prompt caching.
- **Cost estimate per session (assumptions, to be measured in stage 4 from `response.usage`):**
  - planner: about 5 turns, about 40k input tokens in total, of which about
    20k are cache reads;
  - prose: about 6k input and 1.5k output;
  - total output including thinking: about 4.5k.

  | Model | Per session | 300 judging sessions |
  |---|---|---|
  | Opus 5.5 | about USD 0.20 | about USD 60 |
  | Sonnet 5.5 | about USD 0.10 | about USD 30 |

  Cache-write premiums and retries are not included.
- **Variability:** the LLM never classifies, scores, or selects. It chooses
  questions and writes prose. Each session stores the model ID, effort,
  prompt version, the tool-call trace, the raw LLM text, and the validator
  result next to the engine snapshot.

## 13. Modes and labels

| Mode | Needs | What works | Label on every screen |
|---|---|---|---|
| Live | Qloo key (server) + optional LLM key | Everything; agent prose with LLM, template without | `LIVE · Qloo <fetch time>` |
| No LLM | Qloo key | Everything except free-form agent conversation and LLM prose; template brief | `LIVE · template brief` |
| Recorded | Nothing | Pre-built sessions for MUJI, Ralph Lauren, and the acceptance seeds, from stored evidence snapshots; the engine re-runs live on them | `RECORDED · Qloo data fetched 2026-10-06 (run …)` |
| Synthetic | Nothing | The conflict fixture and the tests | `SYNTHETIC · not Qloo data` |

- Recorded mode is chosen explicitly by the user (a button). It is never used
  silently after a live failure.
- Whether a small set of stored Qloo values may be shipped in a public demo
  must be confirmed with the organizers (section 17). Until then, recorded
  mode stays off in the public deployment.

## 14. Web stack and screens

- **Stack:** the Python standard library HTTP server (`http.server`
  `ThreadingHTTPServer`) serving one static HTML/CSS/vanilla-JS page and a
  small JSON API.
  - The engine stays standard-library only, so tests remain offline and
    dependency-free.
  - The only runtime dependency is the `anthropic` SDK (pinned), loaded only
    when an LLM key is set.
  - Runtime: Python 3.11 in a container (the current SDK major version needs ≥ 3.10).
- **API:**
  - `POST /api/session` → session ID;
  - `POST /api/session/{id}/answer`;
  - `GET /api/session/{id}` (state, trace, result);
  - `GET /api/session/{id}/brief.json`.
- **Screens:**
  1. **Start:** reference name, type (brand default / movie / artist / any),
     and a mode badge.
  2. **Choose:** returned candidates (name, type, disambiguation); "none of these".
  3. **Working:** the agent trace. Each Qloo call is shown with its status, and
     each step is labelled "agent decision" or "engine".
  4. **Result:**
     - motifs with strength and expandable evidence rows (literal value,
       entity, request, pointer);
     - six axes with their state, rule, evidence strength, and rule confidence;
     - selected and excluded materials with reasons and unrequested
       properties;
     - the brief and a JSON download.
  5. **Problem states:**
     - credential error (stop, no fallback);
     - rate limit or timeout (bounded retry, then "try later");
     - not found;
     - insufficient evidence (shows the weak motifs and what is missing);
     - conflict (choose a pole or leave it open);
     - budget reached.

## 15. Hosting (required by the rules)

Minimal safe deployment:

- One small container on a managed platform with secret environment
  variables and HTTPS. Candidates: Render web service, Google Cloud Run, or
  Fly.io. **Choose in stage 5** after the owner checks the current free-tier
  terms and billing on the provider's own site; nothing about their current
  dashboards is assumed here.
- Secrets `QLOO_API_KEY` and `ANTHROPIC_API_KEY` live only in the platform's
  secret settings; they are never in the repository, the image, logs, or the
  browser.
- Protection:
  - per-IP rate limit (for example 5 sessions per hour);
  - global session cap per day;
  - Qloo budget per session (section 5);
  - an LLM spend limit set in the Anthropic account if available.
  - When a cap is reached, the UI says so; it does not fall back to fake data.
- No user accounts and no personal data. Inputs are brand names; logs keep
  session traces without IP addresses beyond the rate-limit window.
- Recorded and synthetic modes keep the demo usable when the live API is
  unavailable, clearly labelled and only on explicit choice (section 13).

## 16. Reproducibility boundary

- **Guaranteed:** the same evidence snapshot (the literal values with their
  provenance) and the same `engine`, `lexicon`, `rules`, and `palette`
  versions give byte-identical engine JSON. Input order and duplicate items
  do not change the result. This is tested.
- **Not guaranteed:**
  - Live Qloo results can change over time; snapshots are stored per session
    and downloadable.
  - LLM questions and prose vary between runs; they are stored with their
    versions and never feed back into scores.
- Every config change bumps its version string. Old snapshots can be re-run on
  old versions.

## 17. Stage-4 work order and acceptance

### 17.1 Work order

| Task | Content | Notes |
|---|---|---|
| T0 | Package `motif/` (engine) next to `motif_spike/` (spike stays as is); evidence snapshot format; reuse `transport.py` | — |
| T1 | **Held-out check of lexicon-0.1** on 2 new brands (≤ 10 Qloo requests: 2 × search, entities, and 3 insights) | Needs the owner's OK before any request; report hits and misses; adjust the lexicon and bump the version only with the reason written down |
| T2 | Verify the 8 supplier pages in full; set `verified_full_page` or correct the profiles | Needs access to the supplier domains (owner action, section 18) |
| T3 | Classifier (lexicon) + annotation records | — |
| T4 | Translation (R1–R5), axis states, conflict handling | — |
| T5 | Matcher, composition, gates, unrequested properties | — |
| T6 | Brief JSON + template brief | — |
| T7 | Deterministic planner + CLI (`python3 -m motif run --reference MUJI --type brand [--recorded]`) | — |
| T8 | LLM agent loop + prose validator (optional at run time) | — |
| T9 | Tests for AC1–AC11 | Stage 5 adds AC12 |

### 17.2 Acceptance criteria

Recorded evidence snapshots of the stage-2 run serve as fixtures. They are
labelled recorded live data and stay out of git unless the organizers allow
it. Otherwise, tests use them locally and CI uses synthetic equivalents.

- **AC1 MUJI (real):**
  - Targets: light (R1, strong), polished (R3, strong), natural (R5, moderate).
  - warm_cool, intimate_projecting, and sweet_dry are `null`.
  - Selection: M02 top, M01 heart, M03 base.
  - Every motif cites the evidence listed in `reports/design_examples.md`, section 3.
- **AC2 Ralph Lauren (real):**
  - Targets: dense (R4, moderate; flagged "relations only"), polished (R3, moderate).
  - Selection: M03 heart, M04 base, M05 base.
  - Unrequested properties: projecting (M04), warm (M05).
  - Top note open.
- **AC3 insufficient evidence (real):**
  - Nike: no active mapped motif, no axes, `materials.status = no_targets`.
  - A24: the same status, with `provocative` shown as active but unmapped.
  - The agent offers to stop or try another reference.
- **AC4 single-axis direction (real):** Comme des Garçons gives polished only,
  `gated_insufficient_axes`, and a ranked candidate list without a composition.
- **AC5 conflicting evidence (synthetic):**
  - `light_dense` is `conflicted` with value null.
  - No material is ranked on it.
  - The agent asks.
  - The user's choice is stored as a `manual` override and labelled.
- **AC6 ambiguous entity (real):**
  - "Ralph Lauren" with type `any` → question listing the returned brand,
    person, and author candidates.
  - "MUJI" with type brand → auto-select, with the 7 places shown as alternatives.
  - No path selects an ID that was not returned.
- **AC7 API errors:**
  - 401 or 403 → the session stops with a credential message, no further
    requests, no recorded or synthetic substitute.
  - 429 / 5xx / timeout → bounded retries, then an explicit error state.
  - Tested with the existing network-blocked test harness.
- **AC8 determinism:**
  - Same snapshot + versions → identical engine JSON.
  - Shuffled evidence → identical.
  - A duplicated related entity → identical support.
  - The worked-example regressions in `docs/DEFERRED_DESIGN.md` pass.
- **AC9 modes:**
  - The no-LLM run produces the full engine output and a template brief.
  - The LLM prose passes the validator, or the template is used with a note.
- **AC10 secrets:**
  - No key in the repository, logs, HTML, or JSON.
  - Keys are read only server-side.
  - Tests never reach the network.
- **AC11 labels:** every result screen and JSON carries `data_label`
  (live, recorded, or synthetic).
- **AC12 (stage 5) hosted:** the public URL runs the live flow end to end and
  shows a clear state when a cap or error stops it.

### 17.3 Schedule

| Date | Milestone |
|---|---|
| Oct 15 | Stage 4 done (CLI end to end) |
| Oct 24 | Stage 5 done: working hosted MVP (internal target) |
| Oct 27 | Stage 6: submission package |
| Oct 31, 06:45 TRT | Deadline |

## 18. Open items

| Item | Owner | Blocking |
|---|---|---|
| Confirm the hosted-demo rule, the four criteria, and the deadline on qloo.devpost.com (the excerpts could not be opened here) | Owner | Hosting plan |
| Ask the organizers (Discord `#qloo-hackathon`) whether a small set of stored Qloo values may be shown in a public demo (recorded mode) | Owner | Recorded mode in public |
| Decide the LLM model (Opus 5.5 default vs Sonnet 5.5) and create an Anthropic API key with a spend limit; store it only as a secret | Owner | T8 |
| OK for ≤ 10 held-out Qloo requests (T1) | Owner | Lexicon freeze |
| Access to supplier domains for T2 (environment network setting) or a manual check of 8 pages | Owner | Citing material descriptors publicly |
| Choose a hosting provider in stage 5 | Owner + stage 5 | AC12 |
| Rules for unmapped motifs (experimental, provocative, heritage, …) | Later | No (deferred) |

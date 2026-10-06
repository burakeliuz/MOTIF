# MOTIF submission notes (working skeleton)

Running notes for the Devpost submission, organized by the six items of the Qloo
hackathon kit's submission guide (`docs/SUBMISSION.md` in `qloo/qloo-hackathon-kit`;
summary in `docs/QLOO_ACCESS_NOTES.md`). Every roadmap stage adds to this file.
`TBD` marks what later stages decide.

Status: stage 2 (live Qloo feasibility) done on 2026-10-06; stage 3 product
decisions in `MOTIF_BUILD_SPEC.md`; stage 4 (engine and research flow, command
line) done on 2026-10-06 with the spec at rev 0.2; stage 5 (web interface,
verified materials, LLM prose, hosting files) done on 2026-10-06 with the spec at
rev 0.3. Worked design examples: `reports/design_examples.md`.

## 0. Event requirements (kept apart from the kit's advice)

Official (Qloo Agentic Hackathon, [qloo.devpost.com](https://qloo.devpost.com/)).
Checked on 2026-10-06 through search-engine excerpts of the official page and
rules, because devpost.com could not be opened from the build environment.
The owner must confirm these on the page itself.

- Deadline: October 30, 2026, 11:45 pm EDT (October 31, 06:45 Türkiye time).
  Judging period: November 2–16, 2026 (US Eastern), so the demo must work until at
  least November 17 in Türkiye. Suggested final access and budget check: October 27–28.
- A functional demo hosted externally that judges can try end to end. A demo video
  is reported as not required.
- **Private access (corrected 2026-10-06):** the official rules' Testing section,
  read in full by the owner, accepts login details in the testing instructions for
  private sites; the hackathon homepage has wording against private access; the
  rules say the official rules prevail in a conflict. MOTIF keeps its review
  password for now. Two things need the organizers' confirmation before relying
  on it: that a password-protected demo is accepted, and that the testing
  instructions field is visible only to judges. The password is never written
  into a public description. (The build environment cannot open devpost.com, so
  this rests on the owner's reading.)
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

## 2b. Stage 4: what runs and what Qloo demonstrably adds

The command `python3 -m motif run --reference "<brand>"` runs a deterministic
research controller:

1. Search, with a question when the name is ambiguous.
2. The brand's own `/entities` tags.
3. Related brands.
4. Related movies, but only when they can still change the result.
5. Lexicon motifs, the six sensory axes via rules R1–R5, verified-only
   material matching, and a brief.

Every step logs its action, the observed state, and the reason. The LLM, when
configured, only writes validated prose.

**Qloo's contribution, measured with identical rules** (`python3 -m motif compare`):

- **A** = the brand's own Qloo description only.
- **A′** = A with one own cue sufficient (a sensitivity check: is A empty only
  because of the threshold?).
- **B** = A plus related brands and movies.

| Brand | A | A′ | B | Reading |
|---|---|---|---|---|
| MUJI | 0 axes | light, polished, natural | light, polished, natural | Relations corroborate (strength weak → strong/moderate); no new direction |
| Patagonia (held-out) | 0 | natural | natural | Corroboration only |
| Ralph Lauren | 0 | polished | dense, polished | "dense" comes from relations only (one related brand + two movies) |
| Comme des Garçons | 0 | none | polished | "polished" comes from relations only |
| Le Labo (held-out) | 0 | none | light, polished | Both axes come from relations only (co-liked minimal fashion and skincare brands) |
| A24 | 0 | none | none | None |
| Nike | 0 | none | none | None |

A is empty for every brand largely because of the design threshold, so A = 0
is **not** evidence that Qloo improved quality.

- **What relations do show:**
  - In 2 of 7 brands they corroborate what the brand's own tags already hint at.
  - In 3 of 7 they add a direction that the own tags do not contain.
- **The caveat:** being co-liked with other brands is not the same as sharing
  their aesthetic, so those relation-only axes are flagged `relations_only`
  in every output.
- Seven brands, and a lexicon partly written on five of them, support no
  general claim.

## 2c. Stage 5: interface, verified materials, and LLM prose

**Web flow** (`python3 -m motif.web`, stdlib server, vanilla JS):

1. Start: one brand field plus two example buttons (MUJI, Ralph Lauren) that
   start the real flow.
2. Entity choice when Qloo's search is ambiguous: brands can be chosen; stores
   and other entity types are shown, disabled, with the reason (live check:
   "Le Labo" offers two shops and the brand "Le Labo Fragrances").
3. Research: each line is a real controller step read from the server
   (resolve, own description, related brands, related films, translation,
   brief), with skip and stop reasons. No percentages or simulated progress.
4. Result: direction summary; six axes, where an unknown axis has no mark (it
   is open, not a midpoint); motifs with clickable Qloo phrases (entity, field,
   JSON position, request, fetch date, and MOTIF's reading kept separate);
   verified materials with the supplier's own words, MOTIF's interpretation,
   and the supplier link; the brief; and a provenance panel (Qloo vs MOTIF).
5. Partial and error states: partial direction, no translation rule,
   insufficient evidence, research stopped (partial result labelled
   incomplete), not found, rate or budget caps, server error.

**Verified materials (task T2, palette-0.3).** Seven materials now have
properties checked against the supplier's full page on 2026-10-06, with URL,
date, supporting text, and MOTIF's interpretation stored per property. The
supplier text supports the descriptor; the mapping to an axis is MOTIF's
design. ISO E SUPER (IFF) stays unverified because iff.com returned HTTP 403
(bot protection) to the build environment; it is never used live.

**LLM prose.** The brief's wording can be written by `claude-sonnet-5-5`
(configurable, never switched silently). The model receives only the engine
result (no raw Qloo bodies, IDs, or scores), cannot choose motifs, targets, or
materials, and its text is validated against the result; otherwise the
labelled template is shown. Stage-5 real calls: 3 (one model check; two MUJI
briefs, the first from the command line and the second from the web interface:
1,102 and 1,178 input tokens, 313 and 314 output tokens, estimated $0.0053 and
$0.0055 at the listed $2 / $10 per million tokens). Both briefs passed
validation on the first attempt.

**Live check of the interface (2026-10-06).** 8 live Qloo requests in total:
MUJI (search, own entry, related brands, related films) and Le Labo (search,
then, after choosing the brand, own entry, related brands, related films; the
search was not repeated).

## 2d. Stage 6A: review of product logic and Qloo contribution (proposals)

`docs/STAGE_6A_DECISIONS.md` compares the original idea with the current
product, separates common from distinctive Qloo descriptors on the recorded
brands, plans a three-arm evaluation (own entry only, plus relations, LLM only),
and maps each judging criterion to product evidence. Its items are proposals
until the owner approves them; no engine or deployment change was made.

## 2e. Stage 6B: the chosen experience and a two-brand trial

- **Interface:** art direction A (editorial) with Top/Heart/Base scent strips. The
  result leads with a plain scent idea, then the starting materials (each strip is
  MOTIF's visual shorthand for supplier-described properties, darker where the
  direction asks for them, lighter on dimensions the evidence leaves open), a
  short cultural basis per direction, open decisions, and the brief. "How it was
  made" is closed by default; technical records sit one level deeper.
- **Creative intent:** an optional line stored as `user_intent`; it appears in the
  brief and changes no motif, direction, or material.
- **Suggested interpretations:** on request, Claude may suggest up to three
  readings for descriptors the lexicon does not read, validated against a JSON
  schema and MOTIF's checks; accepting one records the user's note, never Qloo
  evidence. Live example (Supreme): readings for its own "Exclusive", "Defiant",
  and "Vibrant Color Palettes".
- **Honest basis per direction:** "from the brand's own descriptors", "the same
  motif also appears in references Qloo relates to the brand", or "derived only
  from those references: a creative suggestion". Motifs without a rule stay as
  open design questions (Comme des Garçons: experimentation and provocation).
- **Printable brief:** `/brief/<id>` renders one A4 page from the stored result;
  the technical JSON stays a separate download.
- **Budgets:** daily counters persist in a file with a lock and reserve-then-release
  accounting; LLM calls are reserved in the ledger before they are sent; both fail
  closed. One Qloo cache per brand means changing the intent repeats no request.
- **Two-brand trial** (`reports/trial_6b.md`, pre-registered): Aesop received the
  same direction and materials as MUJI, with "light" only from related references;
  Supreme received one relation-only direction plus provocation as an open
  question, and no materials. An LLM-only brief (same intent) was more vivid and
  more practical on first read but untraceable and outside the verified palette.
  No human rating was made; no arm is called better.

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

### Stage-4 live trace (held-out brand Patagonia, session of 2026-10-06; key never stored)

```text
local:req:0001  GET /search?query=Patagonia&take=10                                  -> 200
local:req:0002  GET /entities?entity_ids=DB4CE34E-3A63-4947-946F-9D52502C5762        -> 200
local:req:0003  GET /v2/insights?filter.type=urn:entity:brand&signal.interests.entities=DB4CE34E-...&take=10&feature.explainability=true -> 200
local:req:0004  GET /v2/insights?filter.type=urn:entity:movie&signal.interests.entities=DB4CE34E-...&take=10&feature.explainability=true -> 200
Header on every request: X-Api-Key: [REDACTED] (added by the environment, never by MOTIF's code)
```

Result:

- Resolved to `urn:entity:brand` Patagonia.
- `natural` (moderate): own "Earthy Color Palettes" (req 0002) and The North
  Face "Earthy and High-Visibility Tones" (req 0003).
- Sensory target: natural impression (R5) only. The other five axes stay
  `null`.
- Outcome `partial_direction`: one axis is below the two-axis composition
  threshold (a design parameter), so no materials are proposed.

## 4. Demo or screenshots

Hosted demo: <https://motif-pxh8.onrender.com> (Render free web service, deployed
from `main` by the owner; keys are server-side environment variables).

The demo is behind a review password (`MOTIF_ACCESS_PROTECTION=on`,
`MOTIF_ACCESS_PASSWORD`). Whether it stays on for judging is the owner's decision
after the organizers confirm (section 0); turning it off is one environment
variable. Copy-ready Devpost texts and a testing-instructions draft with a
password placeholder: `docs/DEVPOST_SUBMISSION.md`.

Server variables (names only): `QLOO_API_KEY`, `MOTIF_ACCESS_PROTECTION`,
`MOTIF_ACCESS_PASSWORD`, `MOTIF_ANTHROPIC_API_KEY` (optional), `MOTIF_LLM_MODEL`, `MOTIF_LLM_MAX_CALLS`,
`MOTIF_QLOO_MAX_CALLS_PER_DAY`, `MOTIF_WEB_SESSIONS_PER_DAY`,
`MOTIF_WEB_SESSIONS_PER_IP_HOUR`.

Screenshots of the start, result, and partial screens were taken in the local
preview. Result screenshots show recorded Qloo data, so they are not committed
until data sharing is confirmed (section 6). They must contain no credential and
no personal data.

## 5. Setup from a clean environment

Current (engine CLI, stage 4; Python 3.9+, standard library only; the LLM is optional):

```sh
git clone https://github.com/burakeliuz/MOTIF && cd MOTIF
python3 -m unittest                                   # offline tests; network blocked; recorded-data tests skip
# with the hackathon key in the environment (QLOO_API_KEY, or a proxy-injected credential):
python3 -m motif_spike check                          # must say READY
python3 -m motif run --reference "MUJI" --type brand  # live research, at most 4 Qloo requests for a resolved brand
# optional LLM prose: pip install -r requirements.txt; set MOTIF_ANTHROPIC_API_KEY (model default claude-sonnet-5-5)
python3 -m motif.web                                  # web interface on http://127.0.0.1:8000
```

A clean clone has no recordings (`data/` is git-ignored), so `--recorded` needs
a live run first.

- Final product setup, verified in a clean environment: TBD (stage 6)

## 6. Known limitations

- Stage 6B additions:
  - **Low specificity among minimal brands:** MUJI, Le Labo, and Aesop all receive
    light/polished/natural and the same three materials. Five rules and seven
    verified materials cannot separate them; what makes each distinct sits in
    descriptors MOTIF does not translate (for example Aesop's "Architectural Store
    Interiors"). The suggestion layer shows such descriptors but changes nothing.
  - **Counters on the free host:** daily counters and the LLM ledger live on the
    instance's disk, which a free Render instance resets on restart or redeploy;
    within one instance they hold across concurrent requests. Provider-side
    limits (Anthropic workspace spend limit, the Qloo key's quota) remain the
    outer guard. A persistent store would need a paid disk or an external
    service (not set up; owner decision).
  - **The two trial brands** are no longer independent if rule R6 is adopted.


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
- Stage 4 additions:
  - **No material property is verified yet.** The supplier pages were blocked
    in the build environment, so live runs propose no materials; a labelled
    design preview can show them.
  - **Lexicon blind spots seen on held-out brands:**
    - film-technique words ("Sparse interviewing") and landscape words
      ("Lush" mountains) can match cues (only weak so far);
    - frequent own descriptors such as "Neutral Tones", "Functional", and
      "Rugged Utility" match no cue.
  - **Name resolution:** brand names may resolve to shops or to a variant name
    ("Le Labo" → "Le Labo Fragrances"); MOTIF asks the user instead of guessing.
  - **Relation-only axes:** these describe a brand's co-liked neighbourhood,
    not the brand itself.
  - **Data sharing:** whether raw or recorded Qloo responses may appear in a
    public repository or demo is not addressed by the kit's `API_ACCESS.md`.
    Raw data stays private (`data/` is git-ignored); only small curated
    excerpts are committed. Organizer confirmation is pending.
- Stage 5 additions:
  - **Post-hoc lexicon fixes.** Lexicon-0.3 (technique nouns in film and
    artist tags; "lush" needs a design context; "precise" no longer counted as
    common) was written after seeing the held-out brands. Le Labo and Patagonia
    are therefore no longer independent validation; a new held-out set is needed.
  - **One material unverified.** ISO E SUPER could not be read from iff.com
    (HTTP 403, bot protection). Axis mappings of verified materials remain
    MOTIF's design, not supplier claims.
  - **Hosting limits.** On the free instance, sessions live in memory and are
    lost when the service sleeps; daily caps restart with the process; the
    per-IP limit trusts the first `X-Forwarded-For` entry (best effort).
- Limitations of the final product: TBD (stage 6)

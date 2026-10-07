# Stage 6A: product logic, Qloo contribution, and art direction

Status: **proposal of 2026-10-06, updated after the owner's 6B decisions (see §0).**
Nothing in this document is approved by being written down; §0 records what the owner approved. Each item below is marked **current** (already in the product),
**proposed** (recommended for 6B), or **awaiting approval** (the owner decides).
Stage 6A changed no engine code, made no live Qloo or LLM call, and did not
touch the deployed demo (`https://motif-pxh8.onrender.com`, behind the review gate).

The analysis uses only recorded data: the stage-2 run
(`live-20261006T103307Z-660d`: MUJI, Ralph Lauren, Comme des Garçons, A24,
Nike) and the T1 sessions (Le Labo, Patagonia). The visual prototypes, the
sample brief, and their screenshots contain recorded Qloo values, so they stay
in git-ignored `data/design_preview/stage6a/` and are shared privately with
the owner. Quoted Qloo phrases in this document are limited to those already in
the committed curated excerpt (`reports/evidence_excerpt.md`,
`reports/design_examples.md`).

## 0. Owner decisions for 6B (2026-10-06) and what was built

| ID | Decision by the owner | Status after 6B |
|---|---|---|
| D12 | Art direction **A (editorial)** as the base: the "If a brand / were a / scent." headline, A's typography, layout, and colour. Only B's Top/Heart/Base strips are adopted, redrawn in A's language. The "B with A's mobile patterns" mix was not chosen. | Implemented in `motif/web/static/` |
| D2 | Brand plus an optional one-line creative intent; a second alternative is not required. | Implemented: `user_intent`, shown in the brief, never changes motifs, axes, or materials |
| D3 | Alternative reading | Not built (not required) |
| D9 | The LLM keeps writing the brief and may offer at most three user-accepted readings for descriptors the lexicon does not read. No tool choice, rules, materials, or scores. | Implemented: `motif/interpret.py`, labelled "Suggested interpretation — not applied", accept/reject per session |
| D7 | A small trial with two fresh brands instead of six; the 24 Qloo requests and 6–12 LLM calls are not approved. | Run within 8 Qloo requests and 5 LLM calls: `reports/trial_6b.md` |
| D13 | The review password stays. Removing it for judges is not an automatic requirement. | Gate kept; see §1 correction |
| D4 | Distinctive vs. common descriptors | Shown as information only, from a frozen seven-brand sample (`config/reference_sample.json`); no effect on scores |
| D5, D6, D8, D11 | Relation-only label, per-direction basis, unmapped motifs as open questions, one-page brief and PDF | Implemented |
| D10 | Palette extension | Still awaiting approval, now tied to one rule candidate (§0.1) |

### 0.1 Decision package awaiting approval: one rule and one material

Superseded by §0.3 (measured on 13 brands, with the material checked).

Measured offline on the nine recorded brands (no new request; configs unchanged):

| Candidate | Rationale | Effect on the recorded brands | Risk |
|---|---|---|---|
| **R6: provocation → raw texture** (counterpart of R3, precision → polished) | Edgy, rebellious, subversive descriptors read as an unpolished, transgressive texture; a design hypothesis like R1–R5 | 6 of 9 unchanged. Comme des Garçons: texture becomes **conflicted** (polished from related references vs. raw from its own descriptors) and the user chooses. A24: first direction (**raw**, partial). Supreme: **raw + light**, composed with bergamot and vetiver. | Written after seeing CDG, A24, and Supreme, so none of them would be independent evidence for it; needs fresh brands |
| **Olibanum (frankincense) oil**, one specific supplier grade, verified on a full Givaudan or Firmenich page | The only verified raw material today is vetiver; an incense family material would give R6 a second raw option. Verify dry/raw only if the supplier's words support it | No effect unless R6 is approved | Supplier text may not support "raw"; then it is not added |

Lavender (cool) and benzoin (sweet/warm) stay out: no rule can target cool, sweet, or warm, so adding them would change no result. Vetiver and bergamot already exist.

### 0.2 Correction: competition access

The 6A text below said a demo behind private access "does not appear to qualify". The owner read the full official rules on 2026-10-06: their Testing section accepts login details in the testing instructions for private sites, while the hackathon homepage carries wording against private access, and the rules say the official rules prevail in a conflict. MOTIF therefore keeps the review gate; whether a password-protected demo is accepted, and whether the testing-instructions field is visible only to judges, must be confirmed with the organizers. The build environment could not open `qloo.devpost.com` (egress blocked), so this rests on the owner's reading.

### 0.3 Decision 1 (revised 2026-10-07): the R6 rule and one material, not applied

Status: **not applied**; the live default stays rules draft-0.2 and palette-0.3.
The exact candidate text is in `config/candidates/r6_and_olibanum.json`, which the
engine never loads. Measured offline on 13 brands: the nine recorded ones and the
four fresh brands of the second trial (`reports/trial_6b.md` §3), whose responses
R6 had never seen.

**Why R6 is meaningful.** Provocation is the motif MOTIF meets most often without a
rule: it is supported by the brand's own Qloo entry for A24, Comme des Garçons,
Supreme, Gucci, and Balenciaga (5 of 13). "Edgy", "Rebellious", and "Subversive"
describe a refusal of polish, and raw texture is the one pole of MOTIF's six
dimensions that reads as unpolished. One verified raw material exists (vetiver).

**When it is wrong or narrowing.**

- Provocation staged with polish: in Gucci, Balenciaga, and Comme des Garçons, R6
  pits provocation (raw) against precision (polished) and turns texture into a
  conflict instead of a direction. On the fresh brands it touched (2 of 2), R6
  produced only conflicts.
- With one verified raw material, every provocative brand that composes gets
  vetiver (Supreme: bergamot and vetiver). A composition appearing is not success.
- It maps an attitude to a surface texture; provocation in a scent may rather be
  a contrast, an unexpected pairing, or a deliberate dissonance.

**Why other ways to express provocation fall outside the current engine.** A rule
maps one motif to one pole of one dimension, and the composition step picks
materials that match the poles; nothing picks materials to clash, so contrast or
dissonance cannot be stated. Single-pole alternatives exist but do not help:
provocation → synthetic has no verified synthetic material (Comme des Garçons
would still "compose" with HEDIONE, AMBROX SUPER, and HABANOLIDE, matching only
polished); provocation → projecting reuses HEDIONE and AMBROX SUPER, the same
materials as the calm brands. The engine also treats any two active motifs in a
conflict as equals: it does not let the brand's own evidence outrank related
references, or strong outrank moderate. Changing that is a separate engine
decision, not proposed here.

**Effect, kept apart (baseline → +R6; the material alone changes nothing)**

| Brand | Set | Untranslated motifs | Directions | Conflicts | Materials | +olibanum |
|---|---|---|---|---|---|---|
| MUJI | recorded | none | light, polished, natural | none | bergamot, HEDIONE, HABANOLIDE | no change |
| A24 | recorded | provocation → none | none → **raw** (one direction, no composition) | none | none (reference: vetiver) | no change |
| Comme des Garçons | recorded | experimentation, provocation → experimentation | polished (related only) → none | none → **texture** | none | no change |
| Nike | recorded | none | none | none | none | no change |
| Ralph Lauren | recorded | heritage | dense (related only), polished | none | AMBROX SUPER, HABANOLIDE | no change |
| Le Labo | recorded | none | light, polished (both related only) | none | bergamot, HEDIONE, HABANOLIDE | no change |
| Patagonia | recorded | none | natural | none | none | no change |
| Aesop | recorded | none | light (related only), polished, natural | none | bergamot, HEDIONE, HABANOLIDE | no change |
| Supreme | recorded | provocation → none | light (related only) → light, **raw** | none | none → **bergamot, vetiver** | no change |
| Gucci | fresh | provocation → none | dense, polished (both related only) → dense | none → **texture** | AMBROX SUPER, HABANOLIDE → none | no change |
| Harley-Davidson | fresh | heritage | none | none | none | no change |
| Sanrio | fresh | playfulness | none | none | none | no change |
| Balenciaga | fresh | provocation, experimentation, industrial, romance → without provocation | polished → none | weight (left open) → weight, **texture** | none | no change |

R6 changes 5 of 13 brands: one new partial direction (A24), one new composition
(Supreme), three new conflicts (Comme des Garçons, Gucci, Balenciaga). "Both"
equals "+R6" for every brand.

**The material.** "Incense" is a family (frankincense, myrrh, elemi …), not one
raw material. The specific grade checked is Givaudan's **Frankincense Oil Somalia
FairWild** (Boswellia carterii, essential oil), full page read 2026-10-07:
"Woody, Spicy, Balsamic, Terpenic … frankincense develops a powerful spicy and
citrus profile, wrapped in a resinous warmth. These notes evolve into a warmer,
spicy, persistent character with ambery and woody-balsamic notes." The supplier's
words support **warm** only; nothing supports raw or dry (Givaudan's resinoid page
carries the same text). dsm-firmenich lists OLIBANUM EO, RES, SFE, and the
pyrogenated RES VULCAIN (described as leathery and smoky in search-index text),
but its pages refuse automated access from this environment (bot protection,
HTTP 403), so nothing there is verified. With warm only, the material changes
none of the 13 results, because no rule targets warm.

**Recommendation.** Do not adopt R6 or the material now. Provocation stays a named
open design question, which the result now puts in its headline. If the owner
still wants R6 before judging, the effects above are what it does; applying it
means copying the candidate rule into `config/draft_rules.json` as draft-0.3 with
a written reason, and the 13 brands then stop being independent checks.

### 0.4 Decision 2 (2026-10-07): paid persistence for the spending counters

The hosted demo runs on a Render free web service. Its filesystem is lost on every
redeploy, restart, and idle spin-down (after 15 minutes without traffic), and a
free service cannot attach a disk ([Render: free instances](https://render.com/docs/free)).
MOTIF's counters (`web_usage.json`, `llm_calls.jsonl`) live in the data directory,
`MOTIF_DATA_DIR` or `./data` (on Render `/opt/render/project/src/data`, inside the
ephemeral deploy). Checked in code and tests:

| Case | Behaviour |
|---|---|
| file missing (fresh instance) | counts start at zero: the daily caps reset with the instance |
| file corrupt or unwritable | fail-closed: no new research (503), template brief (no LLM call) |
| concurrent requests | file lock plus atomic replace; the cap holds within one instance and across processes on one disk |
| restart, redeploy, spin-down | everything above resets; a password holder could exceed the daily LLM cap across restarts |

What this round changed (code, reviewable): `MOTIF_LLM_BUDGET_GUARD` (default
`auto`). On Render, Claude is used only when `MOTIF_DATA_DIR` sits on its own
persistent mount; otherwise Claude is **paused**: briefs come from MOTIF's labelled
template and interpretation suggestions are unavailable, with a short message.
Qloo calls keep their per-instance counters (hackathon requests carry no price).
Demo impact on the free plan: no Claude text and no suggestions; everything else
works.

Options for the owner (nothing has been created):

| Option | Monthly cost (list prices, read 2026-10-06) | What to set | Effect |
|---|---|---|---|
| A. Keep free; Claude paused | $0 | nothing (default `auto`) | fail-closed; template briefs |
| B. Keep free; provider-side cap | $0 plus the capped Claude spend | in the Claude Console (Settings → Workspaces), create a workspace for MOTIF (organization admins only), set its monthly cap on the workspace's **Spend limits** tab (limits cannot be set on the Default Workspace and cannot exceed the organization's), create the API key in that workspace, put it in `MOTIF_ANTHROPIC_API_KEY` on Render, set `MOTIF_LLM_BUDGET_GUARD=provider` ([Anthropic: workspaces](https://platform.claude.com/docs/en/manage-claude/workspaces)) | Claude works; Anthropic enforces the hard cap; MOTIF's own counters stay best-effort |
| C. Paid persistence | ≈ $7.25: Starter web service $7 plus a 1 GB disk at $0.25/GB ([pricing](https://render.com/pricing)) | plan Starter, disk mounted at `/var/data`, `MOTIF_DATA_DIR=/var/data` (see the comment at the end of `render.yaml`) | counters and ledger survive restarts and deploys; deploys lose zero-downtime and the service stays single-instance ([disks](https://render.com/docs/disks)) |

A plan upgrade alone gives no persistence: the counters must live on the disk's
mount path. A Postgres Basic database ($6/month) could hold the counters for a
free web service, but it needs new code and a dependency, and a free Postgres
expires after 30 days, before judging ends; not recommended. Recommended: **B**,
because it is free, the cap is enforced by Anthropic, and MOTIF changes nothing
but one variable; **C** if the owner wants MOTIF's own daily caps to hold too.

### 0.5 Engine and product refactor (2026-10-07): decisions taken under the refactor brief

The owner's refactor brief (phases 0–13) asked for the smallest defensible
choice at each step, documented, and an owner question only for paid
resources, keys and security, or a choice the evidence cannot support. These
were taken on that basis; details in `docs/REFACTOR_LOG.md`.

| ID | Decision | Why | Where |
|---|---|---|---|
| E1 | The product runs the continuous engine (`continuous-1.0`); the rule engine `engine-0.3` with R1–R5 stays unchanged as the legacy baseline (`--engine legacy`) | the rule engine collapsed 13 brands to 3 material sets | `docs/ENGINE_REDESIGN.md` |
| E2 | The motif-to-sensory model is built from open odor-descriptor datasets (Dravnieks 1985, Keller & Vosshall 2016, Leffingwell, IFRA 2019 via Pyrfume) and labelled design readings; heritage, romance, and melancholy carry no claim; the five forbidden pairs stay forbidden | academic hosts are blocked in this environment; open data was reachable | `docs/SENSORY_MODEL_RESEARCH.md` |
| E3 | Scoring weights and saturation set by inspection on the 13 trial brands, then frozen before a pre-registered five-brand holdout | no ground truth to fit against | `docs/MOTIF_SCORING.md`, `reports/continuous_holdout.md` |
| E4 | The web app asks no conflict question: a dimension the motifs pull both ways is shown "open to the perfumer" | an undecidable choice is the perfumer's, not the user's | `motif/agent.py` |
| E5 | Scent architecture from a 23-direction library; material references are IFRA glossary generic names, trade names only from supplier pages MOTIF read; `olfactory-1.1` fixed a scale error | the 7-material palette was the last collapse stage | `docs/OLFACTORY_LAYER.md` |
| E6 | The LLM writes prose only (`prose-c1.0`), validated; it chooses nothing | unchanged authority rule (D9: L0) | `motif/llm.py`, `motif/story.py` |
| E7 | No new LLM call for the LLM-only baseline; the four structured stage-6B answers are reused | 11 of the 20-call daily cap already used | `docs/VALIDATION.md` |
| E8 | Candidate engine fixes from the holdout (typed search, "industrial design" context rule, a non-fashion commonness set, a lead-level floor, wider lexicon) are listed, not applied | each would need a version bump and a new holdout | `docs/ENGINE_REDESIGN.md` §5 |

Effect on earlier decisions: decision 1 (§0.3, R6 + olibanum) concerns only the
legacy engine now; the continuous model already lets provocation lean raw
(tentatively), so the recommendation is to close it as not applied. Decision 2
(§0.4, Claude spending on the free host) is unchanged and still the owner's.

## 1. Competition basis (search-index text, not full pages)

On 2026-10-06 the official pages <https://qloo.devpost.com/> and
<https://qloo.devpost.com/rules> could not be opened directly (bot
verification). What follows is taken from the search-engine index of those
pages and must be re-checked against the full current text before submission.

- Four equally weighted criteria: technological implementation (including the
  use of Qloo), design, potential impact, quality of the idea. Ties go to the
  technical criterion first. Equal weights are no guarantee of any score.
- A working external demo, a public repository, and an open-source license are
  expected; a video is not required. On private access, see the correction in §0.2.
- Implication we draw: a product that would work the same without Qloo does not
  meet the intended differentiation, and more API calls are not value by themselves.

### What we will show for each criterion (proposed)

| Criterion | Concrete product evidence to show | Exists today? |
|---|---|---|
| Technological implementation / Qloo use | Per brand: what the brand's own entry says vs. what references Qloo relates to it (related brands, films) add, measured with identical rules (A/A′/B), with every phrase traceable to entity and request; distinctive vs. common descriptors | A/A′/B and traceability: yes. Distinctiveness and the per-axis "why it changed" view: proposed (§3) |
| Design | One coherent art direction (§8) where the scent idea leads and the evidence is one tap away; a printable brief | Current UI works but was not liked; two prototypes in this stage |
| Potential impact | A one-page brief a brand/creative team can hand to a perfumer (§7), with open decisions spelled out | Brief exists as text and JSON; the readable one-page layout and PDF are proposed |
| Quality of the idea | "If this brand were a scent": cultural motifs → sensory direction, honest about what culture cannot decide | Yes for brands with clear aesthetics (MUJI, Le Labo); weak for brands whose identity is conceptual (CDG, A24) |

## 2. The original idea compared with today

### 2.1 What works (keep)

- **MUJI is legible end to end** (current): own descriptors and the references Qloo relates to MUJI
  agree on restraint, precision, and naturalness; three axes set,
  three left open; verified materials with the supplier's own words.
- **Provenance is honest** (current): Qloo values are copied literally with
  their position; relation-only directions are flagged; unknown axes stay empty.
- **The demo is real** (current): live Qloo, LLM prose under validation,
  deterministic controller, verified palette, deployed behind a gate.

### 2.2 Where it falls short

A lexicon that matches tags is not cultural understanding, and passing tests is
not creative quality. The recorded data shows three gaps.

1. **Distinctive motifs are lost.** Comme des Garçons' own entry contains
   *Deconstructed Silhouettes*, *Subversive*, *Avant-Garde*, and *Provocative*.
   "Deconstructed silhouettes" also appears on four of the brands Qloo relates to CDG,
   and "subversive" on two. Today these feed motifs (`experimental`,
   `provocative`) that have no translation rule, so CDG ends as
   `partial_direction` with only *polished*, and that axis comes from
   relations. A24's own *High-Contrast* and its films' recurring "confessional"
   tone match nothing; A24 ends as `no_translation_rule`.
2. **Common adjectives dominate.** Across the seven recorded brands, these
   descriptors occur for at least five of them: minimalist, sophisticated,
   authentic, atmospheric, raw, intimate, lush, warm, functional, cinematic,
   moody, stylized. They say little about any one brand. Specific, repeated
   patterns are elsewhere: MUJI "approachable" (5 related brands), "serene"
   (own entry and related brands); Patagonia "technical" (own entry and 4
   related brands); Nike "passionate" (4 related brands).
3. **Rules cover only five poles.** R1–R5 can set light, dense, polished,
   natural, and intimate (and intimate is in practice blocked as too common).
   Warm/cool, sweet/dry, raw, synthetic, and projecting can never be a target
   today, whatever Qloo returns. This, not the palette, is the main
   expressiveness limit (§6).

### 2.3 User and flow

**Assumed user (not validated):** a brand or creative team preparing a brief
for a perfumer, who needs a defensible starting direction and the reasons for
it. Nothing here is confirmed by a customer conversation; no perfumer has
reviewed the output yet.

| Flow | What it adds | Risk | Verdict |
|---|---|---|---|
| Brand only (current) | Simple; every claim traceable | Conceptual brands get little direction | Keep as the base |
| Brand + one-line creative intent | Lets the team say what the scent is for ("a home fragrance for the store") | Intent can overwrite evidence if mixed in | **Proposed:** stored as a separate `user_intent` layer; shown in the brief; may choose between already supported alternatives; never creates an axis, a motif, or a material |
| Brand + choose between alternative directions | Turns relation-led and distinctive readings into a choice instead of a silent merge | More UI; alternatives must be real, not invented | **Proposed, smallest form:** offer an alternative only when the evidence actually contains one (own vs. audience neighbourhood disagree, or a distinctive motif lacks a rule) |

Smallest useful flow for 6B (proposed, **awaiting approval**): brand input,
optional one-line intent, then one result with at most one evidence-backed
alternative reading. Events and other new input types stay out of scope.

## 3. Using Qloo more meaningfully

### 3.1 Keep four sources apart (plus one proposed)

| Layer | Example | Category |
|---|---|---|
| Brand's own descriptors | MUJI's own *Clean Lines*, *Natural Materials* | `qloo_observation` |
| Qloo relations | "Brands/films Qloo relates to the brand" (the list itself) | `qloo_observation` |
| Descriptors of related entities | *Muted* on *Still Walking* | `qloo_observation`, marked as a neighbour's property |
| User's stated intent (proposed) | "for a store home fragrance" | new `user_intent`, never evidence |
| MOTIF's readings and translations | motif *restraint* → weight *light* | `motif_annotation`, `design_rule` |

A neighbour's property is never automatically the brand's property. A direction
that only those references support is labelled **from related references only**
(today: `relations_only`) everywhere, including the brief.

### 3.2 Shared, distinctive, and conflicting motifs (proposed)

- **Shared:** supported by the brand's own entry and by related entities
  (MUJI restraint, precision, naturalness). Strongest reading.
- **Distinctive:** a descriptor family that is rare across a fixed reference
  set of brands but repeats for this brand (CDG "deconstructed", MUJI
  "approachable"). Proposed rule: weight a cue group by how few reference
  brands carry it; the reference set and cut-off are versioned design
  parameters. Seven brands is too small a reference set for anything but a
  prototype; 6B should freeze a larger list (cost: one entity request per
  added brand) or present distinctiveness as indicative only.
- **Conflicting:** motifs that push one axis to opposite poles (existing
  `conflicted` state), or own entry and neighbourhood disagreeing. Shown as a
  choice, never averaged.
- Many related entities from one Qloo request are **one** source, not many
  independent confirmations; strength counts source kinds, not entities
  (current behaviour, keep).
- Affinity scores rank results within one request. They are not aesthetic
  similarity and not a probability of liking a scent (current rule, keep).

### 3.3 Other domains and endpoints

Documented and observed (`docs/QLOO_ACCESS_NOTES.md`): `/search`, `/entities`,
`/v2/insights` with `filter.type` for brand, movie, artist, book, person, and
place; unscoped tag insights returned mostly place tags. No other endpoint is
assumed.

- **Music:** already supported (`--include-artist`), off by default because
  across the five reference brands it never changed a target. Keep off unless
  a distinctive-motif test shows it does.
- **Places, books, people:** no sensory question they answer that brands and
  films do not; no change of decision identified. Not added.

### 3.4 Keep the A/A′/B measurement and explain it per axis (proposed)

Keep A (own entry only), A′ (one own cue sufficient), and B (own + relations)
with identical rules (`docs/SUBMISSION_NOTES.md` §2b; A = 0 everywhere is a
threshold effect, not proof of quality). Proposed 6B addition: for each axis,
one plain sentence: "from Muji's own descriptors; the same motif also appears in references Qloo relates to Muji",
"derived only from references Qloo relates to Muji", or "unchanged: relations added
nothing new". A direction added by relations is not a supported brand property.

## 4. 6B evaluation plan (proposed, awaiting approval)

Three arms answer different questions:

| Arm | Question it answers |
|---|---|
| E1: engine, brand's own entry only | Baseline: what the brand's self-description supports |
| E2: engine, own entry + Qloo relations | What Qloo's cross-domain relations add under identical rules (E2 vs. E1) |
| E3: LLM only (Claude, same user request, no Qloo, no engine) | What a strong general model produces from its own knowledge; tests whether grounding adds specificity and traceability, not whether the LLM "knows" brands |

- **Not weakened:** E3 gets the same request text and output structure as the
  brief, may use its own knowledge, and uses the same model as the prose
  writer. Its prompt is fixed and committed before the run.
- **Brands:** six fresh brands, pre-registered before any request (not the
  seven used so far), mixing clear and conceptual aesthetics.
- **Criteria (1–5 each):** specificity to the brand, fit with the reference,
  traceability of each claim, usability of the brief for a perfumer.
  Traceability is structurally absent in E3; that is reported, not hidden.
- **Raters:** the owner, blind to the arm. A perfumer's rating would be
  valuable; none is arranged, and none will be claimed.
- **Reporting:** descriptive only. Without independent human ratings, no
  superiority claim.
- **Budget:** about 4 Qloo requests per brand for E2 (E1 is a subset; 24 in
  total) and 6 LLM calls for E3 (plus up to 6 for E2 prose).

## 5. Translation engine and agent

- **No arbitrary single-word mappings** ("experimental → iris" is rejected). A
  supported motif without a rule stays in the brief as a motif with its
  translation **open** (current outcome `no_translation_rule`; proposed: show
  it in the brief and the PDF, not only as a status). A new rule needs a
  written rationale, a version bump, and a check on fresh brands.
- **Keep:** six axes, empty unknowns, data vs. interpretation, no
  "restrained → intimate", thresholds and weights as design parameters.
- **Reliability means:** literal data transfer, consistent creative decisions
  (same input and versions give the same output), and usefulness to the user.
  Not a scientifically correct scent, not a finished formula.

### 5.1 The deterministic controller: what it does and where it stops

It resolves the brand (asks when ambiguous; offers only returned IDs), always
fetches the anchor sources, fetches films only when they can still change the
result, stops on access errors and budget, and never retries into a fallback.
Limits:

- fixed domain order and a fixed budget (8 attempts);
- it cannot notice a semantic gap (CDG's *Dark Palette* matches nothing, so it
  is invisible to the controller);
- it cannot try an alias or a better query when the name resolves badly; it can
  only ask;
- it cannot judge whether a neighbourhood is relevant (Le Labo's neighbourhood
  is minimal fashion and skincare: plausible but unverified).

### 5.2 LLM authority options (awaiting approval; nothing implemented)

| Option | What the LLM would do | Never | Assessment |
|---|---|---|---|
| L0 (current) | Writes validated prose only | Choose motifs, axes, scores, materials | Keep |
| L1 | Suggests a reading for own descriptors that match no cue ("Dark Palette" → candidate motif), shown as "suggested reading, not used" until the user accepts it; accepted suggestions become `user_intent`, not evidence | Set axes or materials; change scores | Possible 6B addition if the owner wants it; would address §2.2 gap 1 visibly; adds 1 call per brand |
| L2 | Plans research (which domain next) | Exceed the budget or the allow-list | Not recommended: two or three domains leave little to plan |

## 6. Palette and brief

### 6.1 Coverage of the seven verified materials

| Pole | Verified materials | Can a rule target it today? |
|---|---|---|
| light | HEDIONE, Bergamot | yes (R1) |
| dense | AMBROX SUPER, Labdanum | yes (R4) |
| polished | HEDIONE, AMBROX SUPER, HABANOLIDE (ISO E SUPER unverified) | yes (R3) |
| raw | Vetiver | no |
| natural | Bergamot, Vetiver, Orris | yes (R5) |
| synthetic | none | no |
| warm | HABANOLIDE, Labdanum | no |
| cool | none | no |
| intimate | none | R2 exists, blocked as too common |
| projecting | HEDIONE, AMBROX SUPER | no |
| sweet | Bergamot | no |
| dry | Vetiver | no |

### 6.2 Proposed small extension (awaiting approval)

Families and accords (citrus, aromatic, incense, balsamic) are not materials;
each proposal names one specific supplier grade to verify on a full page
(Givaudan or Firmenich, both reachable), with the supplier's words kept apart
from MOTIF's axis mapping. Candidates, to be verified, not claimed:

- **Olibanum / frankincense oil** for the incense family: candidate for dry
  and raw.
- **Lavender oil** for the aromatic family: candidate for cool.
- **Benzoin resinoid** for the balsamic family: candidate for sweet and warm.

Vetiver and bergamot already exist; a second citrus is not needed. Adding
materials for poles that no rule can target changes no result, so each
material ships together with a rule decision or is not added. ISO E SUPER
stays unverified and blocks nothing.

### 6.3 One-screen MUJI brief (from the real recorded output)

Structure: scent idea → target character → relation to the brand → material
roles → open decisions. Plain descriptions come before technical names.
Supplier phrases are quoted; nothing is described as smelled or balanced.

> **Muji.** Restraint you can smell: a light, smooth-finished scent with a
> natural feel, closer to a well-made unbranded object than to an ornament.
> *(MOTIF's reading of the evidence; nothing has been smelled.)*
>
> **Target character.** Light (weight, from the motif restraint, strong
> support) · Polished (texture, from precision, strong) · Natural (impression,
> from naturalness, moderate). Left open: temperature, projection, sweetness.
>
> **Why this fits Muji.** Muji's own Qloo entry: Clean Lines, Natural
> Materials, Unpretentious, Functional Minimalist Form. Brands Qloo relates
> to Muji (Urban Research, Creema) repeat Minimalist, Natural Tones, Clean
> Lines; films Qloo relates to Muji (Still Walking, Like Father, Like Son)
> repeat Muted, Understated elegance. These corroborate Muji's own description;
> they do not define it.
>
> **Starting materials.** Top: bergamot oil (a cold-pressed citrus oil;
> Givaudan: "bright and sparkling citrus facet") opens light and natural; it
> also brings sweetness, a creative choice. Heart: HEDIONE® (a transparent,
> jasmine-like molecule; Firmenich: "elegant, transparent floral") carries
> lightness and smooth finish; it also adds diffusion, a creative choice.
> Base: HABANOLIDE® (a musk molecule; Firmenich: "extremely elegant and
> substantive musk note") keeps the finish polished; it also brings warmth, a
> creative choice.
>
> **Open decisions.** Warm or cool? Diffusive or close? Sweet or dry opening?
> Proportions and whether it reads as Muji can only be decided by smelling.

The A4 PDF layout (one page) and the technical JSON stay separate: the PDF
carries the five sections above plus a provenance footer; the JSON keeps the
full evidence trail. Sample: `data/design_preview/stage6a/muji-brief-sample.pdf`
(private).

## 7. Art direction: two working prototypes (private preview)

Both use the same MUJI content and show start, research, result, and a mobile
layout; small **Qloo / MOTIF / Claude** labels mark real stages; the scent idea
leads the result; "How was it made?" opens the readable basis; technical
details sit one level deeper. No request times, URNs, JSON paths, or rule codes
in the main flow. No live calls; labelled as a design preview. Fonts are from
Google Fonts (open licenses); all graphics are drawn in code, so there are no
stock images or third-party image rights.

| | A · Editorial art direction | B · Contemporary scent atelier |
|---|---|---|
| Idea | A culture magazine: the brief as a feature spread | A perfumer's bench: smelling strips as the main object |
| Type | Archivo (wide and condensed display) + Newsreader (text) | Familjen Grotesk (UI and display) + IBM Plex Mono (labels) |
| Colour | Cool off-white, black, one signal vermilion | Stone grey, graphite green, one leaf-yellow for "active" |
| Signature | Huge condensed words; open axes as outlined (hollow) words | Each material is a strip textured only by its verified properties; creative-choice properties drawn faint and dashed |
| Research view | A table of contents filling in; a scan line on the running step | Strips filling one by one; the running strip "dips" |
| Mobile | Input pinned to the thumb zone; the current step pinned at the bottom; materials swipe sideways | Strips lie down as bands; the trio of strips becomes the header |
| Strength | Very legible; confident hierarchy | Ownable, sensory, explains verified vs. creative visually |
| Risk | Can read as a generic magazine template | Pattern key needs a legend; denser to build |

Files (private, git-ignored): `data/design_preview/stage6a/prototype-A-editorial.html`,
`prototype-B-atelier.html`, `muji-brief.html`, `shots/`.

## 8. Decision register

| ID | Decision | Status |
|---|---|---|
| D1 | Brand input stays the base flow; events and new modules stay out | current |
| D2 | Optional one-line intent as a separate `user_intent` layer | awaiting approval |
| D3 | Offer one alternative reading only when the evidence contains one | awaiting approval |
| D4 | Distinctive-motif weighting with a versioned reference set | proposed |
| D5 | "From related references only" label for relation-only directions in UI and brief | proposed (extends current `relations_only`) |
| D6 | Per-axis plain explanation of what relations changed | proposed |
| D7 | E1/E2/E3 evaluation on six pre-registered fresh brands | awaiting approval (spends Qloo and LLM budget) |
| D8 | Unmapped motifs shown in brief and PDF with translation open; no ad-hoc mappings | proposed |
| D9 | LLM authority: L0 stays; L1 only with explicit approval | awaiting approval |
| D10 | Palette +3 (olibanum, lavender, benzoin) only together with matching rule decisions | awaiting approval |
| D11 | One-page brief + PDF export; JSON stays separate | proposed |
| D12 | Art direction A or B (or B with A's mobile patterns) | awaiting approval |
| D13 | Remove the review gate before submission | awaiting approval (at submission time) |
| E1–E8 | Engine and product refactor decisions (§0.5) | current on the session branch |

## 9. Acceptance conditions for 6B

6B starts only after the owner approves the product direction (D2, D3), the
art direction (D12), and, if wanted, the LLM authority (D9). Then:

1. The engine still passes every existing test; any rule, lexicon, or palette
   change carries a version bump and a written reason.
2. Every claim in the result and the PDF maps to one of the five layers in §3.1;
   relation-only directions read "derived only from references Qloo relates to the brand".
3. Unknown axes stay empty in every view, including the PDF.
4. The chosen art direction is implemented for start, research, result, and
   mobile with real data, without fake progress, and without building HTML
   from data.
5. The PDF fits one page for MUJI and Ralph Lauren and contains no technical
   identifiers in its main body.
6. If D7 is approved: the evaluation is pre-registered, run once, and reported
   descriptively, with raters and their independence stated.
7. Live calls stay within budgets the owner sets; recorded data stays private.

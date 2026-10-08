# Stage 6B trial: two fresh brands (pre-registered)

## 1. Pre-registration (committed before any request for these brands)

Written 2026-10-06, before any Qloo or LLM request for the two brands below.
Rules are frozen at commit `cc555f4`: engine-0.3, lexicon-0.3, rules draft-0.2,
palette-0.3, params-0.1, reference sample sample-0.1, prose prompt prose-0.4,
interpretation prompt interpret-0.1. If any rule changes after the results are
seen, these brands stop being independent checks, and the first results stay
recorded below unchanged.

**Brands** (never used in MOTIF before; chosen for contrasting aesthetics):

1. **Aesop**: expected to be aesthetically legible (like MUJI or Le Labo).
2. **Supreme**: expected to rest on attitude and graphics rather than materials
   (closer to A24 or Comme des Garçons).

No prediction of the outcome is made here beyond these expectations.

**Shared creative intent** for every arm: "a signature scent for the brand's flagship stores".

**Arms and the question each answers**

| Arm | What runs | Question |
|---|---|---|
| A | The engine on the brand's own Qloo descriptors only (`motif compare` on the B session's recording) | What does the brand's own Qloo entry support? |
| A′ | As A with one own cue sufficient (sensitivity check) | Is A empty only because of the threshold? |
| B | The engine with related brands and films (the live web flow) | What do Qloo's relations add under identical rules? |
| C | Claude alone (`claude-sonnet-5-5`, effort low), the same intent, no Qloo data, no engine | What does a strong general model write from its own knowledge for the same request? |

A/B measure the contribution of Qloo's relations. C is a wider product
comparison: it tests whether grounding adds specificity and traceability, not
whether the model "knows" the brands. C is not weakened: it may use its own
knowledge, gets the same intent and output structure, and is run before B so
nothing from B can leak into it.

**Arm C prompt (fixed)**

- System: "You are a senior fragrance creative director helping a brand team brief a perfumer."
- User: "Brand: {brand}. Creative intent: a signature scent for the brand's
  flagship stores. Write a scent direction brief for a perfumer in plain
  English, about 200 words: the scent idea, the target character, three
  starting materials with their roles (top, heart, base), and the open
  decisions. No formula, proportions, or percentages. Use your own knowledge of
  the brand."

**What is compared (descriptively)**

- Specificity: does the output name things particular to this brand, or could
  it describe many brands?
- Fit with the reference: do the claims match what the brand's own Qloo entry
  says?
- Traceability: can each claim be traced to a source (Qloo entity and field,
  supplier page)?
- Brief usability: does it give a perfumer a direction, starting roles, and
  open decisions?

No human rating has been arranged. The notes below are the build agent's
descriptive observations, not an evaluation, and support no claim that one arm
is better.

**Budget**: at most 10 live Qloo requests and 5 real LLM calls for the whole
stage, retries included: C 2 calls; B prose 2 calls; one suggestion request on
one brand. If a name is ambiguous, the answer reuses the cached search.

## 2. Results (first run, frozen rules; kept as-is)

Run on 2026-10-06 in the order C, then B, so nothing from B reached C.

**Requests and calls actually used:** 8 live Qloo requests (4 per brand: search,
own entry, related brands, related films; both names resolved to a single brand
without a question) and 5 real LLM calls (C: 2; B brief prose: 2, both passed
validation on the first attempt; one suggestion request for Supreme). Estimated
LLM cost about $0.03 in total (ledger: `data/llm_calls.jsonl`, git-ignored).

### 2.1 A / A′ / B (engine, identical rules)

| Brand | A (own entry only) | A′ (one own cue sufficient) | B (plus related brands and films) |
|---|---|---|---|
| Aesop | insufficient evidence, no direction | polished, natural | **light, polished, natural**; composed: bergamot (top), HEDIONE (heart), HABANOLIDE (base) |
| Supreme | insufficient evidence | none | **light** only (partial, no materials); provocation supported with no rule |

Basis per direction in B:

- Aesop: polished and natural come from Aesop's own descriptors (for example
  "Architectural Store Interiors" read as precision, "Botanical Minimalism" as
  naturalness) and also appear in related references; **light comes only from
  related references** (restraint is not in Aesop's own entry).
- Supreme: **light comes only from related references**; provocation is
  supported by Supreme's own "Edgy" and by related brands, and stays an open
  design question because no rule translates it.

As before, A is empty because of the threshold; A′ shows what the own entry
alone can support. Relations corroborate two of Aesop's directions and add one;
for Supreme they add the only direction.

### 2.2 C (Claude alone, same intent, ~260 words each)

Both C briefs are vivid and practical: a store-scent idea, named starting
materials with roles, and operational open questions (diffusion strength,
regional variants, allergens). Aesop: bitter orange or petitgrain, cypress or
vetiver, cedarwood with incense or labdanum. Supreme: black pepper, Virginia
cedarwood, an Ambroxan-style amber musk.

### 2.3 Descriptive notes (build agent, not a human evaluation)

| Criterion | B (engine with relations) | C (LLM only) |
|---|---|---|
| Specificity | Low for Aesop: the same direction and materials as MUJI and Le Labo. Supreme: thin (one relation-only direction). | Higher on first read: brand-specific imagery (apothecary interiors, skate culture). |
| Fit with the reference | Directions match words in each brand's own Qloo entry where they come from it; "light" for both brands does not come from their own entries and is labelled so. | Plausible and in places consistent with the own Qloo entries (Aesop's architecture and botany), but from model memory. |
| Traceability | Every direction traces to a Qloo entity and field; every material property to a supplier page. | None: no claim can be traced to a source. Most named materials are outside MOTIF's verified palette (vetiver and labdanum, suggested for Aesop, are in it). |
| Brief usability | Clear roles and open decisions, but a thin brief when evidence is thin (Supreme: no materials). | Ready to hand to a perfumer as a creative starting point; includes practical store considerations MOTIF does not cover. |

What this shows, without ranking the arms: MOTIF's value is grounding and
honesty about what is unknown, while its translation layer is too narrow to make
minimal brands distinct and too thin for attitude-led brands. The suggestion
layer surfaced Supreme's own "Exclusive", "Defiant", and "Vibrant Color
Palettes"; none of these changes the direction today.

### 2.4 Revisions after seeing the results

None applied. A rule candidate (R6, provocation → raw texture) and one palette
candidate were proposed separately and tested offline in §3.8; neither was
adopted. Had R6 been adopted, Aesop and Supreme would no longer be independent
checks for it.

## 3. Second trial: four fresh brands (pre-registered 2026-10-07)

### 3.1 Pre-registration (committed before any request for these brands)

Written 2026-10-07, before any Qloo or LLM request for the four brands below.
Product code frozen at commit `c82aef7`: engine-0.3, lexicon-0.3, rules
draft-0.2, palette-0.3, params-0.1, reference sample sample-0.1, prose prompt
prose-0.5 (the brief now opens with MOTIF's own lead), interpretation prompt
interpret-0.1. Nothing below changes these; if anything changes after the
results are seen, these brands stop being independent checks and the first
results stay recorded here unchanged. Failures are kept; no brand is swapped.

**Brands** (never used in MOTIF before; chosen for contrasting cultural
positions, not for expected results):

| Brand | Why it is in the set |
|---|---|
| Gucci | maximalist luxury fashion: tests the opulence path (R4, dense) against a polished house |
| Harley-Davidson | rugged American heritage outside fashion: tests motifs MOTIF has no rule for (heritage, industrial) |
| Sanrio | playful character brand: tests a profile led by a motif without a rule (playfulness) |
| Balenciaga | provocative luxury fashion with sharp tailoring: stress test for the R6 candidate (provocation → raw) against precision → polished |

**Arms** (same shared intent for every arm: "a signature scent for the brand's flagship stores")

| Arm | What runs | Question |
|---|---|---|
| A | engine on the brand's own Qloo entry only, from the B recording | what does the own entry support? |
| A′ | as A, one own cue group sufficient (sensitivity check) | is A empty only because of the threshold? |
| B | the live web flow (search, own entry, related brands, related films when the controller fetches them), then the brief | what do Qloo's relations add under identical rules? |
| C | Claude alone (`claude-sonnet-5-5`, effort low), no Qloo data, no engine; JSON with a schema like the brief: one-sentence idea, cultural basis, six dimensions (a pole or "open"), three materials with role and why, open decisions | what does a strong general model propose from its own knowledge? |
| R6 / olibanum what-if | offline on the B recordings, after B is recorded: baseline, +R6, +olibanum, both | does the unapproved rule or material change these fresh brands, and how? |

C runs first for all four brands, so nothing from B can reach it. A, A′, and
the what-ifs reuse the B responses; they send no request. R6 was written on
2026-10-06, before these brands were chosen,
so they are independent checks of its behaviour, not of its creative merit.
The olibanum what-if uses only what Givaudan's full page for "Frankincense Oil
Somalia FairWild" supports (read 2026-10-07): warm, nothing else.

**Fixed choices**: if a name is ambiguous, the brand-type candidate whose name
matches the input is chosen (the first one in Qloo's order if several); the
answer reuses the cached search. Interpretation suggestions are requested for
Harley-Davidson and Sanrio only.

**Budget for this round**: at most 20 live Qloo network attempts (enforced by
`MOTIF_QLOO_MAX_CALLS_PER_DAY=20` on the trial server; 16 expected) and at most
15 real LLM calls (enforced by `MOTIF_LLM_MAX_CALLS=15` in the ledger): C 4,
B brief 4 to 8 (one re-write allowed after a failed check), suggestions 2. No
Render or hosted-demo request.

**What is compared (descriptively; no human rating, so no "better")**

- Specificity: does the output name things particular to this brand?
- Cultural grounding: can each claim be traced to a Qloo entity and field?
- Creative usability: a direction, starting roles, and open decisions a perfumer can act on?
- False claims: statements the brand's own Qloo entry contradicts, audience claims, invented facts.

### 3.2 What was actually used

Run on 2026-10-07 in the pre-registered order: C for all four brands, then B
for each brand through the real web interface (local live server, access gate
on), then the suggestions, then the offline analyses.

| | Live Qloo network attempts | Real Claude calls | Estimated Claude cost |
|---|---|---|---|
| C (four brands) | 0 | 4 | $0.0436 |
| B brief prose (four brands; every text passed the checks on the first attempt) | 16 (4 per brand, no retries) | 4 | $0.0234 |
| Suggestions (Harley-Davidson, Sanrio) | 0 | 2 | $0.0115 |
| Gallery session (MUJI, live, final interface; per-session budget capped at 4 so the round cap could not be passed) | 4 | 1 | $0.0064 |
| **Round total** (caps: 20 and 15) | **20** | **11** | **≈ $0.085** |

Costs are the ledger's estimates (`data/llm_calls.jsonl`, list prices of
2026-10-06). Qloo hackathon requests have no per-request price.

**Deviation (recorded before the result was seen).** Balenciaga's live run
stopped at a question the pre-registration did not cover: weight was pulled
toward light (restraint) and dense (opulence), both only from related
references. The neutral answer "Leave it open" was used. The follow-up was
computed from the stored live responses of that same session, as the web flow
would have done (no new request), and the brief went through the same prose
code path with one real Claude call. The browser script stopped at that
question, so Balenciaga has no live screenshot.

### 3.3 A / A′ / B (engine, identical rules)

| Brand | A (own entry) | A′ (one own cue) | B (with related brands and films) |
|---|---|---|---|
| Gucci | insufficient (provocation weak) | none | **dense, polished**, both only from related references; composed: AMBROX SUPER and HABANOLIDE (both base); provocation supported with no rule |
| Harley-Davidson | insufficient (heritage weak) | none | no direction: heritage supported (own entry and related brands), no rule |
| Sanrio | insufficient (playfulness weak) | none | no direction: playfulness supported (own entry and related brands), no rule |
| Balenciaga | provocation supported, no rule | polished | **polished** (precision, strong: own entry, brands, films); weight conflicted between relation-only motifs, left open; provocation, experimentation, industrial character supported with no rule |

Headlines shown to the user (deterministic, `narrative.headline`): Gucci "A
profile led by provocation." (partial direction); Harley-Davidson "A profile
led by heritage."; Sanrio "A profile led by playfulness." (no direction yet);
Balenciaga "Precision: a smooth-finished scent." with provocation,
experimentation, and industrial character named as the next creative decision.

What relations added: they lifted each brand's own leading motif to the
threshold (heritage, playfulness, provocation) and, for Gucci, added the only
directions (dense, polished). They did not add a direction for Harley-Davidson
or Sanrio, because MOTIF has no rule for heritage or playfulness.

### 3.4 C (Claude alone, same purpose, structured like the brief)

All four C briefs are specific and usable as creative starting points, and each
is consistent with words in the brand's own Qloo entry that MOTIF's lexicon does
not read (C never saw them): Gucci "eclectic maximalism … vintage-meets-
contemporary" (Qloo: Eclectic, Maximalist, Vintage-Inspired); Harley-Davidson
leather, chrome, and a raw, dry direction (Qloo: motorcycle leathers, Chrome
Details, Rugged); Sanrio sweet, pastel, cheerful (Qloo: Sweet, Pastel Color
Palette, Cheerful); Balenciaga architecture, oversized shapes, industrial stores,
a raw texture (Qloo: Architectural Silhouettes, Oversized Proportions, Industrial
Design). Directions: Gucci warm, dense, polished, natural; Harley-Davidson warm,
dense, raw, natural, intimate, dry; Sanrio warm, light, polished, intimate,
sweet; Balenciaga cool, raw, projecting, dry. Materials are mostly accords or
materials outside MOTIF's verified palette (labdanum, orris, vetiver, bergamot
are in it).

### 3.5 Descriptive comparison (build agent's notes, not a human rating)

| Criterion | B (engine with relations) | C (Claude alone) |
|---|---|---|
| Specificity | Gucci: two relation-only directions and two base materials; Balenciaga: one direction; Harley-Davidson and Sanrio: a clear profile but no direction | High: brand history, stores, characters, named accords for every brand |
| Cultural grounding | Every motif, direction, and quote opens its Qloo entity and request or the supplier page; directions drawn only from references are labelled | None traceable; consistent with the brands' own Qloo entries in all four cases, from model memory |
| Creative usability | Strong where a direction exists (roles, supplier words, open decisions); thin where the leading motif has no rule | Ready to hand to a perfumer; includes store practicalities (diffusion, dwell time) MOTIF does not cover |
| False or unsupported claims | No audience claims; three wording slips in Claude's B prose passed the checks: Gucci "AMBROX SUPER, chosen as projecting" (it was chosen for dense and polished; projecting is a side property), Harley-Davidson "supported by … the brand itself" (it was related brands), Sanrio "one cultural descriptor" (one was read; more were returned) | Audience statements (Sanrio "a multigenerational audience of children, teens, nostalgic adults and tourists"; Harley-Davidson "a broad community") and historical facts that no source in this trial checks |

What this shows, without ranking the arms: for fresh, attitude-led brands,
Qloo's own entries carry the character (C's vivid briefs agree with them), but
MOTIF's five rules translate only one of the four leading motifs (precision).
The prose validator catches wrong materials, numbers, missing open dimensions,
and claims, not misattributed reasons; that is a known gap.

### 3.6 User table (B results, plain terms)

| Brand | Distinctive motif (own entry) | Direction | Materials | What Qloo's relations added | Open gap |
|---|---|---|---|---|---|
| Gucci | provocation | dense, smooth-finished (related references only) | AMBROX SUPER, HABANOLIDE (base) | both directions; lifted provocation to the threshold | no rule for provocation; maximalism and glamour unread |
| Harley-Davidson | heritage | none | none | lifted heritage to the threshold | no rule for heritage; Rugged, Chrome Details, motorcycle leathers unread |
| Sanrio | playfulness | none | none | lifted playfulness to the threshold | no rule for playfulness; Sweet, Pastel, Cheerful unread |
| Balenciaga | precision (with provocation, experimentation, industrial character) | smooth-finished; weight left open | none (one direction; reference only: HABANOLIDE, HEDIONE, AMBROX SUPER) | corroborated precision; added the weight conflict | no rule for three own motifs; conflict between relation-only motifs |
| MUJI (gallery run) | restraint, precision, naturalness | light, smooth-finished, natural-feeling | bergamot (top), HEDIONE (heart), HABANOLIDE (base) | corroboration only | the same direction as Aesop |

### 3.7 Why MUJI and Aesop collapse to the same result

- **Data**: different descriptors reach the same three motifs. MUJI: Unpretentious,
  Clean Lines, Natural Materials (own). Aesop: Architectural Store Interiors,
  Botanical Minimalism (own); restraint only from related references.
- **Lexicon**: twelve motif groups; many different descriptors land in the same group.
- **Rules**: one motif, one pole: restraint → light, precision → polished,
  naturalness → natural. Same motifs, same three targets.
- **Materials**: for light + polished + natural, AMBROX SUPER and labdanum are
  excluded (dense), vetiver too (raw), ISO E SUPER is unverified. Four materials
  remain; the best per role is the same set: bergamot (top), HEDIONE (heart),
  HABANOLIDE (base). Strength changes the scores (HEDIONE 0.667 for MUJI, 0.533
  for Aesop) but not the order. Le Labo (light, polished, both relation-only)
  gets the same three, with orris dropping out.

More distinct results would need more rules (more motifs reaching more
dimensions), more verified materials per pole, or a reading of the brand's own
unread descriptors; none of these is approved today.

### 3.8 R6 and olibanum on the fresh brands (offline what-if)

| Brand | +R6 (provocation → raw) | +olibanum (warm only, per Givaudan's page) |
|---|---|---|
| Gucci | texture becomes **conflicted** (raw from Gucci's own provocation vs polished from related references); weight stays dense; no composition until the user chooses | no change |
| Harley-Davidson | no change | no change |
| Sanrio | no change | no change |
| Balenciaga | texture becomes **conflicted** too (raw from provocation vs polished from strong precision); two open conflicts | no change |

R6 produced a conflict, not a direction, on both fresh brands it touched. R6
and the olibanum material were not adopted; the legacy engine keeps rules
draft-0.2 and palette-0.3.

### 3.9 Offline regression on the existing recordings

The nine earlier brands were replayed offline with this round's code: outcomes,
targets, conflicts, and materials are unchanged from 6B (only wording and
layout changed). A / A′ / B recomputed for them (no request), so the comparison
now covers 13 brands:

| Brand | A (own entry) | A′ (one own cue) | B (with relations) |
|---|---|---|---|
| MUJI | none | light, polished, natural | light, polished, natural |
| A24 | none (provocation, no rule) | none | none (provocation, no rule) |
| Comme des Garçons | none (no rule) | none | polished (related only) |
| Nike | none | none | none |
| Ralph Lauren | none | polished | dense (related only), polished |
| Le Labo | none | none | light, polished (both related only) |
| Patagonia | none | natural | natural |
| Aesop | none | polished, natural | light (related only), polished, natural |
| Supreme | none | none | light (related only) | The UI was checked in a browser on recorded data at 1440×900,
1280×720, and 390×844 (no horizontal scroll, no fixed bar, input visible on the
first screen), including one simulated failed request and the retry, and the
conflict question on synthetic data. The full offline suite has 152 tests.

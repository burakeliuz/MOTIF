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
candidate are proposed in `docs/STAGE_6A_DECISIONS.md` §0.1. If R6 is adopted,
Aesop and Supreme are no longer independent checks for it.

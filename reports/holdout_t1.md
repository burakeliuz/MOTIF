# T1: held-out brand check (pre-registered)

## 1. Pre-registration (written and committed before any request for these brands)

Date: 2026-10-06. Nothing about these brands had been requested from Qloo by
this project before this file was committed.

**Frozen versions:** `engine-0.1`, `lexicon-0.2`, `draft-0.2` (rules R1–R5),
`palette-0.2`, `params-0.1` (default domains: brand and movie; artist off).
The first evaluation uses them unchanged. Any later rule change gets a new
version, the first results stay in this file, and these two brands then stop
counting as independent validation.

**Brands and why (chosen before seeing any result):**

- **Le Labo** (fragrance house): the category closest to MOTIF's users and
  absent from the five reference brands. It tests whether the lexicon reads a
  perfume brand's own descriptors and its neighbourhood.
- **Patagonia** (outdoor apparel): a category outside fashion, film, and home
  goods. It tests the lexicon in a different cultural world (function,
  nature, activism) where the cue list may simply not apply.

Neither brand was chosen because it is expected to succeed. If a brand does
not resolve, or resolves ambiguously, that is the result; it will not be
replaced.

**Request plan and budget:** each brand runs as one live session of
`python3 -m motif run --reference "<name>" --type brand --max-requests 5`.

- Up to 4 requests per brand: search, `/entities`, related brands, related
  movies. The controller may skip movies when they cannot change the result.
- Hard cap: 5 network attempts per session including retries, so at most
  10 in total.
- No other Qloo request is made for T1.

**What counts as success (beyond "≥ 2 axes"):**

1. **Traceability:** every active motif cites literal Qloo values with
   request and pointer.
2. **Plausible grounding:** a reader can see why each cue matched, and no
   match is a misread of the tag (for example a genre, a technique, or a
   negation).
3. **Gaps reported:** missing axes, unmapped motifs, and weak evidence are
   shown, not filled.
4. **Differentiation:** the two brands' directions differ from each other,
   and from the closest reference brand, where the evidence differs.
5. **Honest failure:** when the evidence is thin or the rules miss it, the
   outcome says so (`insufficient_evidence`, `no_translation_rule`, or
   `partial_direction`).

Two brands cannot establish general validity. The result can only show
whether the frozen rules behave sensibly outside the brands they were written on.

## 2. Results

(Filled in after the live runs; first results are kept even if rules change later.)

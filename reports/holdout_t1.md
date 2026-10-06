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

## 2. Results (first evaluation, frozen rules; kept as-is)

### 2.1 Requests actually sent

Live requests to `https://hackathon.api.qloo.com` through `DirectTransport`.
Sessions are in git-ignored `data/motif_sessions/`.

| Session | Brand | Network attempts | Statuses |
|---|---|---|---|
| live-20261006T124256Z-0688 | Le Labo | 1 | search ok → stopped for a user choice |
| live-20261006T124335Z-0729 | Le Labo (user choice) | 4 | search, entities, related brands, related movies: all ok |
| live-20261006T124400Z-0751 | Patagonia | 4 | search, entities, related brands, related movies: all ok |
| **Total** | | **9 of 10** | No retries, no errors |

### 2.2 Le Labo

**Resolution (a real defect, found by T1):**

- "Le Labo" returned 10 candidates.
- The only exact-name matches were two shops (`urn:entity:place`, Nantes and Lyon).
- The brand came back as **"Le Labo Fragrances"** (`urn:entity:brand`,
  `25C88914-2BC2-4E6B-A787-A8DD2DD4F45E`, rank 3).
- engine-0.1 asked the user to choose but offered only the two shops.
- Fix (engine-0.2): entity questions now also offer every returned candidate
  of the requested type. The fix concerns the question only, not
  classification or translation.
- The brand was then chosen through the normal `--choose` answer. **The
  evaluator made this choice** (the designed user step), not an automatic
  substitution.

**Own Qloo descriptors (literal):**

- `aesthetic_property`: Industrial Aesthetic, Laboratory-Inspired Packaging,
  Minimalist Labeling, Neutral Tones, Typewriter Font.
- `emotional_tone`: Artistic, Introspective, Minimalist, Sophisticated.

Only "Industrial Aesthetic" matched a cue (`industrial`, unmapped). "Minimalist"
is a common cue. "Neutral Tones" and "Laboratory-Inspired" have no cue.

**Related:**

- Brands: Maison Margiela Fragrances, Malin & Goetz, La Bouche Rouge Paris,
  COS, Aesop, Mansur Gavriel, James Perse, Everlane, Diptyque, Quince.
- Movies: Lady Bird, Call Me by Your Name, Little Women, Phantom Thread, The
  Favourite, Marriage Story, Crazy Rich Asians, I, Tonya, Roma, Beautiful Boy.

**Engine result:**

- `restrained` moderate. Brands: James Perse "Understated", "Unpretentious";
  Mansur Gavriel "Understated Hardware"; Everlane and Quince "Understated".
  Movies: Marriage Story "Restrained", Beautiful Boy "Muted".
- `precise` moderate. Brands: COS "Architectural Silhouettes", "Clean Lines";
  James Perse, Maison Margiela Fragrances, Mansur Gavriel, Everlane, and Quince
  "Clean Lines"; Aesop "Architectural Store Interiors". Movies: The Favourite
  "Dryly composed symmetry", Phantom Thread "Sartorially meticulous".
- Targets: **light** (R1) and **polished** (R3), both **relations only**.
- Weak and unmapped: natural (Aesop "Botanical Minimalism"), heritage, opulent
  (movies), industrial (own).
- Outcome: `no_verified_materials`. No material is proposed because no
  palette property is verified (T2).

**Judgment:**

- (1) Traceable: yes.
- (2) Grounding is plausible: the neighbourhood is topical (fragrance,
  skincare, minimal fashion), and the matched tags read as intended. But the
  direction describes the neighbourhood, not Le Labo's own tags, and "Clean
  Lines" now appears around MUJI, Ralph Lauren, and Le Labo. It may become a
  common cue once the reference set grows.
- (3) Gaps are shown.
- (4) Differentiation is limited: the targets equal MUJI's minus `natural`,
  and the related movies overlap heavily with the reference brands' film
  lists (a generic prestige-film cluster).
- (5) Honest, but this is the weakest kind of success: two axes resting
  entirely on co-liked brands.

### 2.3 Patagonia

**Resolution:** a unique exact brand match.

**Own Qloo descriptors (literal):**

- `aesthetic_property`: Earthy Color Palettes, Functional, Minimalist Branding,
  Rugged Utility, Technical Performance Design.
- `emotional_tone`: Authentic, Conscientious, Purposeful, Reliable.
- `personal_style`: Functional, Minimalist, Outdoor-Casual, Technical.

**Related:**

- Brands: Recreational Equipment Inc, The North Face, Backcountry, Backpacker
  Magazine, Osprey, Arc'teryx, Smartwool, Icebreaker, American Alpine Club,
  Fjällräven.
- Movies: The Dawn Wall, Free Solo, Meru, Valley Uprising, Mountain, Sherpa,
  Touching the Void, The Wildest Dream, Virunga, K2: Siren of the Himalayas.

**Engine result:**

- `natural` moderate: own "Earthy Color Palettes"; The North Face "Earthy and
  High-Visibility Tones".
- Target: **natural impression** (R5) only, so the outcome is
  `partial_direction` with no composition.

**Lexicon misreads, all in the weak tier and without effect on targets:**

- `opulent` from "Lush" on K2 and Mountain: these describe landscapes, not opulence.
- `restrained` from "Sparse lyrical editing" and "Sparse interviewing": these
  describe film technique.
- `industrial` from REI "Rugged Industrial Elements".

**Judgment:**

- (1) Traceable: yes.
- (2) The active motif is plausible; the misreads show that the lexicon does
  not separate technique and landscape words from aesthetic ones.
- (3) Gaps are shown. The brand's most specific own descriptors ("Rugged
  Utility", "Technical Performance Design", "Functional") have no cue or rule,
  so the data is there but the rules are missing.
- (4) The direction differs from the other brands.
- (5) Honest failure to compose.

### 2.4 Overall reading

- **Activation:** the frozen rules did not over-claim. Every active motif
  rests on matched tags that read as intended.
- **Coverage:** coverage of brands' own descriptors is low. Le Labo had 0 and
  Patagonia 1 of their own descriptors as a non-common cue for a mapped motif.
- **Where the axes come from:** one of the two brands got two axes, and both
  rest on relations only. The other got one axis.
- **Defect found:** the disambiguation question; fixed in engine-0.2.
- Two brands prove nothing general. These two brands are now known to the
  project and no longer count as independent validation.

### 2.5 Rule changes proposed after seeing these results (NOT applied)

Each needs a new lexicon version and fresh held-out brands to evaluate:

1. Exclude film-technique words as cue carriers (editing, interviewing,
   framing, handheld, close up, montage).
2. Exclude landscape readings of "lush" in movie tags (for example, require
   an aesthetic namespace for `opulent`).
3. Consider cue groups for frequent own descriptors that currently match
   nothing: "neutral tones/palette" (MUJI, Le Labo) and "functional" (MUJI,
   Nike, Patagonia). Any motif assignment for them is a creative decision and
   must be justified first.
4. Re-compute commonness with a larger reference set; "clean lines" is a
   candidate common cue.

## 3. Post-hoc re-run with lexicon-0.3 and palette-0.3 (stage 5; NOT independent validation)

Sections 1 and 2 stay as written. After reading those results, stage 5 applied
changes 1 and 2 of §2.5 as general rules (lexicon-0.3: technique nouns in film
and artist tags are context, not cues; "lush" needs a design context such as
costume, set, interior, or fabric) and verified seven palette materials
(palette-0.3). Because the rules were changed after seeing these two brands,
the numbers below show that the fixes do what they were written to do; they do
not validate the lexicon. Fresh held-out brands are needed for that.

Re-run on the same recorded T1 sessions (no new requests), engine-0.3:

| Brand | Outcome | Targets (strength; relations only?) | Set aside by context rules | Materials |
|---|---|---|---|---|
| Le Labo (brand "Le Labo Fragrances", chosen) | `composed` | light (moderate; yes), polished (moderate; yes) | "Lush", "Handheld intimacy" | M02 top, M01 heart, M05 base (verified properties only) |
| Patagonia | `partial_direction` | natural (moderate; no) | "Lush", "Minimalist framing", "Sparse interviewing", "Sparse lyrical editing" | none (one axis is below the two-axis threshold) |

- The targets are the same as in the first evaluation; what changed is that
  the misread phrases no longer count as support, and Le Labo now gets
  materials because verified properties exist.
- Changes 3 and 4 of §2.5 (cue groups for "neutral tones" and "functional";
  re-computing commonness) are still not applied.
- A live web run for "Le Labo" on 2026-10-06 (stage-5 interface check, 4
  requests) gave the same choice question (two shops, one brand) and the same
  result.

# Olfactory layer: scent architecture (`olfactory-1.1`)

Phase 8 of the engine refactor (2026-10-07). Config:
`config/olfactory_directions.v1.json`. Code: `motif/olfactory.py`, called by the
continuous engine (`result["architecture"]`). Tests: `tests/test_olfactory.py`.

## 1. What replaces "starting materials"

The legacy engine picked 2–4 of 7 verified supplier materials; on the 13 trial
brands that gave 3 distinct outputs, 8 of them empty. The scent architecture
describes a structure a perfumer can build from:

- **Opening, core, drydown**: one olfactory direction (an accord type) per role,
  or "open to the perfumer" when no direction fits.
- **Dimensions**: temperature, weight, texture, impression (natural/synthetic),
  spatial presence (projection), sweetness, each with its word and confidence
  ("slightly cool · tentative") or "open".
- **Emphasize / avoid**: given only where a *supported* dimension backs them.
- **Material references**: examples of each chosen direction's class, generic
  name first ("methyl dihydrojasmonate (e.g. HEDIONE®)"); optional, never a
  formula, no doses or proportions.

Nothing is hard-coded per brand: every structure is computed from the brand's
continuous profile.

## 2. The library (23 directions)

Each direction has an id, label, family, possible roles, a sensory vector over
the six dimensions, descriptors, odor families, material references, and an
uncertainty note. A cell is **odor data** (`d`) when the direction's odor family
supports that pole in `config/candidates/odor_axis_evidence.v1.json` (×2 → 0.5,
×1 → 0.25), or **MOTIF design** (`m`), 0.25, or 0.5 for the accord's defining
quality. "Rated less sweet" is never used as data for "dry", and no data supports
"dry" at all (`docs/SENSORY_MODEL_RESEARCH.md` §4).

| Direction | Roles | Sensory leaning (d = odor data, m = MOTIF design) | Material references (class first) |
|---|---|---|---|
| Bright citrus | opening | slightly cool (d), slightly natural (m), slightly projecting (m), slightly sweet (d) | limonene; citral; bergamot oil (natural) (e.g. Bergamot Oil Italy) |
| Aromatic herbs | opening, core | slightly cool (m), natural (m), slightly dry (m) | linalool; fenchone |
| Green, leafy | opening | slightly cool (m), slightly raw (m), natural (m) | 3-hexenal; nerone |
| Minty coolness | opening | cool (d) | menthol |
| Aldehydic, clean | opening | slightly polished (m), synthetic (m), slightly projecting (m) | decanal; undec-9-enal |
| Watery, ozonic | opening, core | slightly cool (m), light (m), synthetic (m) | 6-methoxy-2,6-dimethylheptanal; 3-(4-ethylphenyl)-2,2-dimethylpropanal |
| Transparent floral | core | light (m), slightly polished (m), slightly projecting (m), slightly sweet (d) | methyl dihydrojasmonate (e.g. HEDIONE®) |
| Rich white floral | core | slightly warm (m), slightly dense (m), projecting (m), sweet (d) | linalyl benzoate; benzyl acetate |
| Rose | core | slightly natural (m), slightly sweet (d) | rhodinol; nerolidol |
| Powdery iris, violet | core, drydown | polished (m), slightly intimate (m) | beta-irone; dihydro-alpha-ionone; orris butter (natural) (e.g. Orris Pallida Butter (France)) |
| Juicy fruit | opening, core | slightly projecting (m), sweet (d) | gamma-decalactone; alpha-damascone |
| Warm spice | core | slightly warm (d), slightly projecting (m), slightly sweet (d) | cinnamaldehyde; isoeugenol |
| Fresh spice | opening | slightly raw (m), slightly projecting (m), slightly dry (m) | none named |
| Gourmand, vanilla | drydown | warm (d), slightly dense (m), slightly intimate (m), sweet (d) | vanillin; ethyl maltol; coumarin |
| Resinous amber | drydown | warm (d), dense (m), slightly natural (m), slightly sweet (d) | sclareol; labdanum absolute (natural) (e.g. Labdanum Absolute Spain Clear) |
| Dry woods | core, drydown | slightly raw (m), slightly natural (m), dry (m) | cedrol; vetiverol; vetiver oil (natural) (e.g. Vetiver Oil Haiti) |
| Creamy woods | drydown | slightly warm (m), polished (m), slightly intimate (m), slightly sweet (m) | santalol; ebanol |
| Ambery-woody molecule | drydown | slightly polished (m), synthetic (m), projecting (m), slightly dry (m) | (-)-ambroxide (e.g. AMBROX® SUPER) |
| Clean musk | drydown | polished (m), slightly synthetic (m), intimate (m) | galaxolide; celestolide; a musk molecule (e.g. HABANOLIDE®) |
| Leather, animalic | drydown | slightly dense (d), raw (m), slightly dry (m) | civetone; 6-methylquinoline |
| Smoke, incense | core, drydown | slightly warm (d), slightly dense (d), raw (m), slightly dry (m) | 2,4-dimethylphenol; guaiol |
| Earthy, mossy | drydown | slightly raw (m), natural (m), slightly dry (m) | 3-octanol; methyl 2,4-dihydroxy-3,6-dimethylbenzoate |
| Mineral, metallic | opening, core | slightly raw (m), synthetic (m), slightly dry (m) | none named |

## 3. Who is the authority for what

| Source | Role | Not used for |
|---|---|---|
| Qloo | the cultural evidence behind the motifs | anything olfactory |
| MOTIF's sensory model and this library | the translation (design, labelled) | claims of perception science |
| Open odor-descriptor data (Dravnieks 1985, Keller & Vosshall 2016) | only the odor-family → pole cells marked `d` | brands, materials |
| IFRA Fragrance Ingredient Glossary (2019), as digitized in the Pyrfume archive | the generic name and the three IFRA descriptors of a material reference | strength, dose, safety |
| Supplier pages (dsm-firmenich, Givaudan), read in palette-0.3 | identity and provenance of a trade-name example | **the sensory authority**: a supplier's adjectives do not set any cell |

A trade name appears only where MOTIF read the supplier's own page
(`config/material_palette.json`, `verified_full_page`); `tests/test_olfactory.py`
enforces it, and checks that every generic name and its IFRA descriptors are in
the glossary data (when the git-ignored data is present).

## 4. Matching (deterministic; the LLM never chooses)

1. Target = the commitment of each resolved dimension (value × confidence); open
   dimensions are 0 and constrain nothing.
2. Fit = cosine similarity between the target and the direction's vector.
3. A direction that works against a resolved dimension by at least 0.05
   (target × cell) is set aside.
4. Eligible directions (fit ≥ 0.3) fill opening, core, drydown in that order,
   best first, each direction once; a small bonus (0.1 × motif score) ranks a
   direction higher when a leading motif's odor imagery names its family
   (opulence, provocation, industrial only). The bonus never makes a direction
   eligible.
5. A direction *works with* every resolved dimension whose sign its cell
   shares (every cell in the library is a deliberate claim of at least 0.25).
   A role is labelled supported when its direction works with a supported
   dimension, tentative otherwise.
6. Emphasize: up to three eligible directions that work with a supported
   dimension. Avoid: up to three directions that work against a supported
   dimension (by the conflict floor above). A structure resting only on
   tentative dimensions is labelled tentative and has no emphasize or avoid list.

`olfactory-1.1` (2026-10-07) changed only rule 5. In 1.0, "works with" reused
the conflict floor on target × cell; with small targets (about 0.1) a direction
whose whole fit came from a resolved dimension was listed as working with
nothing, and its role was labelled tentative even when that dimension was
supported (found on the Hermès holdout brief in phase 9). Eligibility is
unchanged, so no structure changed on the 13 trial or 4 resolved holdout
brands; role bases, emphasize lists, and the "fits" lines can change. A
stricter variant (any opposite-sign cell sets a direction aside) was tried and
rejected: with five resolved dimensions it left MUJI with one role of three
and made more brands share a structure.

## 5. On the 13 trial brands (offline, `olfactory-1.1`)

| Brand | Opening | Core | Drydown | Basis | Emphasize | Avoid | Legacy materials |
|---|---|---|---|---|---|---|---|
| MUJI | Aromatic herbs | Transparent floral | Earthy, mossy | supported | Aromatic herbs; Transparent floral; Green, leafy | Mineral, metallic; Aldehydic, clean; Smoke, incense | Bergamot oil (Italy), HEDIONE®, HABANOLIDE® |
| A24 | Fresh spice (tentative) | Smoke, incense (tentative) | Dry woods (tentative) | tentative | — | — | none |
| Comme des Garçons | Aldehydic, clean (tentative) | Mineral, metallic (tentative) | Ambery-woody molecule (tentative) | tentative | — | — | none |
| Nike | open | open | open | — | — | — | none |
| Ralph Lauren | Aldehydic, clean | Powdery iris, violet | Creamy woods | supported | Powdery iris, violet; Creamy woods; Aldehydic, clean | Leather, animalic; Smoke, incense; Dry woods | AMBROX® SUPER, HABANOLIDE® |
| Le Labo | Aromatic herbs (tentative) | Powdery iris, violet | Creamy woods | supported | Powdery iris, violet; Creamy woods | Smoke, incense; Leather, animalic | Bergamot oil (Italy), HEDIONE®, HABANOLIDE® |
| Patagonia | Aromatic herbs | Dry woods | Earthy, mossy | supported | Aromatic herbs; Earthy, mossy; Green, leafy | Aldehydic, clean; Mineral, metallic; Watery, ozonic | none |
| Aesop | Aromatic herbs | Dry woods | Earthy, mossy | supported | Aromatic herbs; Earthy, mossy; Green, leafy | Mineral, metallic; Aldehydic, clean; Ambery-woody molecule | Bergamot oil (Italy), HEDIONE®, HABANOLIDE® |
| Supreme | Fresh spice (tentative) | Dry woods (tentative) | Smoke, incense (tentative) | tentative | — | — | none |
| Gucci | open | Rich white floral | Resinous amber | supported | Resinous amber; Rich white floral; Ambery-woody molecule | Watery, ozonic; Transparent floral | AMBROX® SUPER, HABANOLIDE® |
| Harley-Davidson | Fresh spice (tentative) | Smoke, incense (tentative) | Leather, animalic (tentative) | tentative | — | — | none |
| Sanrio | Watery, ozonic (tentative) | Transparent floral (tentative) | Ambery-woody molecule (tentative) | tentative | — | — | none |
| Balenciaga | Aldehydic, clean (tentative) | Mineral, metallic (tentative) | Ambery-woody molecule (tentative) | tentative | — | — | none |

Distinct structures: 11 of 13 (legacy: 3 distinct material sets). Same structure: Comme des Garçons = Balenciaga; Patagonia = Aesop.

The two remaining identical structures follow identical or near-identical
sensory profiles (Comme des Garçons = Balenciaga already in phase 6; Patagonia and
Aesop differ only in weaker or tentative dimensions). Six of the 13 structures
(A24, Comme des Garçons, Supreme, Harley-Davidson, Sanrio, Balenciaga) rest only
on tentative dimensions and say so; Nike has no structure (insufficient evidence).

## 5b. Reading the proposal (presentation, no matching change)

The result page and the brief lead with the chosen structure in one sentence,
the scent idea ("Watery and ozonic to open, a transparent floral core and a
powdery iris and violet drydown"), and after the role strips say what the
chosen accords bring to the
dimensions the evidence leaves open, from their cells in this library: a
dimension all chosen accords lean the same way on is named with that lean
("slightly" when no cell is stronger than 0.25); one they disagree on is
"mixed", with the role of each side; one none of them touches is not set by
them either. When the accords go against a lean the evidence shows too weakly
to decide, the text says so. This is MOTIF's creative reading of the proposal, labelled so; the
dimensions stay open and nothing in the matching changes (`motif/story.py`
`scent_story`, `accord_character`).

## 6. Limits

- The library is MOTIF's MVP vocabulary of 23 accord types; most cells are
  design readings, and only temperature, weight, and sweetness have any data.
- Cosine fit rewards shape, not strength; a brand with one tentative dimension
  still receives a full structure, labelled tentative.
- No fresh-spice or mineral ingredient is named in the digitized glossary, so
  those directions carry no material reference.
- Nothing has been smelled; a perfumer may reject any direction.

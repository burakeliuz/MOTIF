# MOTIF evidence excerpt: run `live-20261006T103307Z-660d`

Provenance category: `qloo_observation`. Every value below is copied literally from a live Qloo response; nothing is inferred, translated, or merged by display name. MOTIF adds no motif, axis, or scent judgment here (see `reports/feasibility.md` for judgments, kept separate).

- Run: `live-20261006T103307Z-660d` (plan `full`, 2026-10-06T10:33:07Z to 2026-10-06T10:33:38Z UTC)
- Base URL: https://hackathon.api.qloo.com; transport: direct
- Parser status at normalization: verified
- Selection: seed resolution; the seed's own tags in 7 descriptive namespaces (other namespaces counted only); top 3 related entities per domain with at most 6 descriptor tags each; top 10 tag insights per seed.
- `req NNNN` is the run's local request ID (table at the end). Pointers are JSON Pointers into that request's saved response, which stays in git-ignored `data/raw/`.
- Affinity and popularity are copied as returned. They are not percentages of people, confidence, or scent suitability, and are not comparable across requests.

## 1. Seed resolution

| Seed input | Status | Returned name | Returned ID | Returned types | Source |
|---|---|---|---|---|---|
| A24 | resolved | A24 | `7E904879-87BC-4BA6-B4AB-6E380A4C250D` | urn:entity:brand | req 0001 |
| MUJI | resolved | Muji | `E12201A5-CC50-40AF-97AE-C54A2CA303F7` | urn:entity:brand | req 0010 |
| Comme des Garçons | resolved | Comme des Garcons | `3637BC2E-B2D1-4496-9BD7-938E4FAE81AD` | urn:entity:brand | req 0019 |
| Nike | resolved | Nike | `C70CE2B8-0AD1-4150-BF18-5A6347F2E860` | urn:entity:brand | req 0028 |
| Ralph Lauren | resolved | Ralph Lauren | `2723B38E-C3E2-435F-A77B-A94A92D68D07` | urn:entity:brand | req 0037 |

## Seed `a24` (A24)

- `properties.short_description` (req 0002 `/results/0/properties/short_description`): "A24 is an American independent entertainment company specializing in film and television production and distribution, known for unique and acclaimed movies."
- Own tags by namespace (req 0002 `/results/0/tags`):
  - `urn:tag:aesthetic_property:qloo`: "Minimalist", "High-Contrast", "Atmospheric", "Raw", "Authentic"
  - `urn:tag:personal_style:qloo`: "null"
  - `urn:tag:emotional_tone:qloo`: "Provocative", "Introspective", "Edgy", "Sophisticated", "Cerebral"
  - `urn:tag:core_value:qloo`: "Creativity", "Originality", "Artistic Integrity", "Independence", "Innovation"
  - `urn:tag:market_archetype:qloo`: "Niche", "Avant-Garde", "Challenger", "Cult"
  - `urn:tag:keyword:qloo`: "Auteur Cinema", "Independent Film", "Gen Z Cinema", "Modern Cult Classics", "Curation"
  - `urn:tag:cultural_relevance:qloo`: "Contemporary Cinema", "Internet Culture", "Modern Art", "Fashion Subcultures", "Indie Music Scene"
  - other namespaces (count only): `urn:tag:brand_subtype:qloo` 1, `urn:tag:brand_type:qloo` 1, `urn:tag:business_model:qloo` 3, `urn:tag:competitor_brand:qloo` 5, `urn:tag:customer_segment:qloo` 4, `urn:tag:industry:qloo` 3, `urn:tag:influencer_appeal:qloo` 5, `urn:tag:interest_adjacency:qloo` 5, `urn:tag:key_market:qloo` 1, `urn:tag:lifestyle:qloo` 10, `urn:tag:partnership:qloo` 5, `urn:tag:product_service:qloo` 8, `urn:tag:similar_brand:qloo` 5, `urn:tag:target_age_group:qloo` 2, `urn:tag:target_gender:qloo` 1, `urn:tag:target_income_level:qloo` 2, `urn:tag:wikipedia_category` 7

**Related brand** (req 0003, 10 returned; top 3; shown: `urn:tag:aesthetic_property:qloo` tags + `properties.emotional_tone`)

- #1 hitRECord (affinity 0.9295760331981086; `/results/entities/0`): tags "Minimalist", "Community-Focused", "User-Centric", "Functional"; emotional_tone "Inclusive", "Collaborative", "Inspiring", "Creative", "Accessible"
- #2 MUBI (affinity 0.9087998795888385; `/results/entities/1`): tags "Minimalist", "Cinematic", "Elegant", "Editorial-focused", "Dark-toned"; emotional_tone "Sophisticated", "Contemplative", "Introspective", "Appreciative"
- #3 Vice (affinity 0.9030223919700427; `/results/entities/2`): tags "Low-Fidelity Photography", "Raw Video Editing", "Bold Typography", "Street-Style Imagery"; emotional_tone "Provocative", "Gritty", "Authentic", "Urgent"

**Related movie** (req 0004, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Eighth Grade (affinity 0.946171832493123; `/results/entities/0`): tags "Naturalistic", "Cinematic", "Vlog inflected", "Observational", "Realistic", "Awkwardly tender"
- #2 Lady Bird (affinity 0.9435141126241621; `/results/entities/1`): tags "Quiet deadpan humor", "Handmade mirror motifs", "Naturalistic", "Warm", "Intimate", "Colorful"
- #3 The Florida Project (affinity 0.9389979999104002; `/results/entities/2`): tags "Child centric", "Documentary infused", "Sunlit gritty", "Handheld", "Naturalistic", "Neon pastel"

**Related artist** (req 0005, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Weyes Blood (affinity 0.9711410848759696; `/results/entities/0`): tags "Vintage Synth Pop", "Intimate", "Orchestral Indie", "Baroque Pop", "Psychedelic Folk", "Dreamy Folk"
- #2 Angel Olsen (affinity 0.9673223698010498; `/results/entities/1`): tags "Engaging", "Alternative Rock", "Americana", "Singer-Songwriter", "Raw", "Dream Pop"
- #3 Alvvays (affinity 0.9657567856861967; `/results/entities/2`): tags "Energetic", "Engaging", "Jangly Indie Pop", "Intimate", "Nostalgic Alternative Rock", "Reverb-Heavy Dream Pop"

**Related book** (req 0006, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Supreme Inequality: The Supreme Court's Fifty-Year Battle for a More Unjust America (affinity 0.8661253162435394; `/results/entities/0`): tags "Revelatory", "Analytical", "Critical", "Insightful", "Historical"
- #2 The Guarded Gate: Bigotry, Eugenics and the Law That Kept Two Generations of Jews, Italians, and Other European Immigrants Out of America (affinity 0.8651397181650388; `/results/entities/1`): tags "Analytical", "Comprehensive", "Engaging", "Historical", "Thought-provoking"
- #3 The Agenda: How a Republican Supreme Court is Reshaping America (affinity 0.8649256330049276; `/results/entities/2`): tags "Analytical", "Insightful", "Critical", "Informative"

**Related person** (req 0007, 10 returned; top 3; shown: `urn:tag:occupation:person` tags)

- #1 Rostam Batmanglij (affinity 0.9579623137569201; `/results/entities/0`): tags "Musician", "Record Producer", "Singer-songwriter", "Songwriter"
- #2 Hamilton Leithauser (affinity 0.956326660891017; `/results/entities/1`): tags "Singer"
- #3 Lauren Mayberry (affinity 0.9545012139184484; `/results/entities/2`): tags "Songwriter", "Journalist", "Singer", "Singer-songwriter"

**Related place** (req 0008, 10 returned; top 3; shown: `urn:tag:ambience:qloo` tags + `urn:tag:decor:qloo` tags)

- #1 New Museum (affinity 0.9465947528211965; `/results/entities/0`): tags "Industrial chic", "Modern", "Provocative", "Cultural", "Stylish", "Experimental"
- #2 Shaker Meadows (affinity 0.945018789574147; `/results/entities/1`): tags "Charming", "Country farmhouse", "Clean", "Historic", "Serene", "Comfortable"
- #3 The Noguchi Museum (affinity 0.9423361240197725; `/results/entities/2`): tags "Charming", "Nature focused", "Relaxing", "Historic", "Unique", "Zen"

**Tag insights** (req 0009, `filter.type=urn:tag`, no namespace filter; top 10 of 20)

| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |
|---|---|---|---|---|
| 1 | Esquites | urn:tag:specialty_dish:place | 1 | `/results/tags/0` |
| 2 | Narratively Focused | urn:tag:style:qloo | 1 | `/results/tags/1` |
| 3 | Bar | urn:tag:genre:place | 1 | `/results/tags/2` |
| 4 | Four Star | urn:tag:hotel_rating:place | 1 | `/results/tags/3` |
| 5 | Identifies as women-owned | urn:tag:inclusivity:place | 1 | `/results/tags/4` |
| 6 | Discover | urn:tag:credit_card:place | 1 | `/results/tags/5` |
| 7 | Inexpensive | urn:tag:cost_description:place | 1 | `/results/tags/6` |
| 8 |  indie | urn:tag:genre:music | 1 | `/results/tags/7` |
| 9 | Lies | urn:tag:keyword:qloo | 0.9997470915528579 | `/results/tags/8` |
| 10 |  episodic | urn:tag:plot:qloo | 0.9995460843805246 | `/results/tags/9` |

## Seed `muji` (MUJI)

- `properties.short_description` (req 0011 `/results/0/properties/short_description`): "Muji is a Japanese retail brand offering minimalist, quality household goods, clothing, stationery, and furniture."
- Own tags by namespace (req 0011 `/results/0/tags`):
  - `urn:tag:aesthetic_property:qloo`: "Neutral Color Palette", "Natural Materials", "Clean Lines", "Functional Minimalist Form", "Unbranded Packaging"
  - `urn:tag:personal_style:qloo`: "minimalist", "casual", "functional", "gender-neutral", "timeless", "scandinavian-inspired"
  - `urn:tag:emotional_tone:qloo`: "Calm", "Practical", "Unpretentious", "Serene", "Functional"
  - `urn:tag:core_value:qloo`: "Simplicity", "Functionality", "Sustainability", "Rationality", "Quality"
  - `urn:tag:market_archetype:qloo`: "Mainstream"
  - `urn:tag:keyword:qloo`: "Minimalism", "Organization", "Utilitarian", "No-Brand", "Essentialism"
  - `urn:tag:cultural_relevance:qloo`: "Minimalist Design Movement", "Japanese Aesthetic Influence", "Sustainable Lifestyle Movement"
  - other namespaces (count only): `urn:tag:brand_subtype:qloo` 1, `urn:tag:brand_type:qloo` 1, `urn:tag:business_model:qloo` 1, `urn:tag:competitor_brand:qloo` 5, `urn:tag:customer_segment:qloo` 4, `urn:tag:genre:brand` 1, `urn:tag:industry:qloo` 6, `urn:tag:influencer_appeal:qloo` 5, `urn:tag:interest_adjacency:qloo` 5, `urn:tag:key_market:qloo` 5, `urn:tag:lifestyle:qloo` 9, `urn:tag:partnership:qloo` 2, `urn:tag:price_level:qloo` 1, `urn:tag:product_service:qloo` 9, `urn:tag:similar_brand:qloo` 5, `urn:tag:subsidiary:qloo` 1, `urn:tag:sustainability_initiative:qloo` 5, `urn:tag:target_age_group:qloo` 3, `urn:tag:target_gender:qloo` 1, `urn:tag:target_income_level:qloo` 2, `urn:tag:wikipedia_category` 9

**Related brand** (req 0012, 10 returned; top 3; shown: `urn:tag:aesthetic_property:qloo` tags + `properties.emotional_tone`)

- #1 Creema (affinity 0.9459117800280578; `/results/entities/0`): tags "Handcrafted", "Natural Materials", "Minimalist", "Varied Textures"; emotional_tone "Warm", "Creative", "Inspired", "Authentic"
- #2 Global Work (affinity 0.9425126756862122; `/results/entities/1`): tags "Clean Silhouettes", "Neutral Color Palettes", "Functional Details", "Minimalist Design", "Soft Textures"; emotional_tone "Friendly", "Reliable", "Comforting", "Unpretentious"
- #3 Soeasy (affinity 0.9387661012522345; `/results/entities/2`): tags "Minimalist", "Instructional", "Bright", "Clear", "Relatable"; emotional_tone "Helpful", "Resourceful", "Encouraging", "Approachable", "Efficient"

**Related movie** (req 0013, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Still Walking (affinity 0.9235040321435563; `/results/entities/0`): tags "Warm", "Intimate", "Minimalist", "Tender long takes", "Knee high framing", "Atmospheric"
- #2 Like Father, Like Son (affinity 0.9202612735111809; `/results/entities/1`): tags "Understated elegance", "Domestic tableau", "Poetic restraint", "Observational", "Quietly resonant", "Muted"
- #3 Shoplifters (affinity 0.91955058962273; `/results/entities/2`): tags "Domestic minimalism", "Melancholic warmth", "Intimate", "Quietly poetic", "Warm grainy texture", "Lyrical"

**Related artist** (req 0014, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 BUMP OF CHICKEN (affinity 0.9875519950112409; `/results/entities/0`): tags "Energetic Pop Rock", "Expressive", "Introspective Folk Rock", "Engaging", "Melodic Alternative Rock", "Emotive J-Rock"
- #2 ASIAN KUNG-FU GENERATION (affinity 0.9798474079364377; `/results/entities/1`): tags "Engaging", "Dynamic", "Emo", "Alternative Rock", "J-Rock", "Post Punk"
- #3 RADWIMPS (affinity 0.9777051547394635; `/results/entities/2`): tags "Post Rock", "Expressive", "Dynamic", "Experimental Indie", "Energetic", "J-Rock"

**Related book** (req 0015, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 My Brother's Husband, All Volumes (Otouto no Otto, #1-4) (affinity 0.9259655914927156; `/results/entities/0`): tags none returned
- #2 Zero at the Bone (affinity 0.84901306849112; `/results/entities/1`): tags none returned
- #3 Hedy Lamarr: An Incredible Life (affinity 0.8466754223337736; `/results/entities/2`): tags none returned

**Related person** (req 0016, 10 returned; top 3; shown: `urn:tag:occupation:person` tags)

- #1 SunShine Ikezaki (affinity 0.9727169771233962; `/results/entities/0`): tags "Owarai Tarento"
- #2 Tsuyoshi Muro (affinity 0.9657757526269163; `/results/entities/1`): tags "Actor"
- #3 Asami Miura (affinity 0.9645222869532596; `/results/entities/2`): tags "Announcer"

**Related place** (req 0017, 10 returned; top 3; shown: `urn:tag:ambience:qloo` tags + `urn:tag:decor:qloo` tags)

- #1 上七軒 億 (affinity 0.9691608861241814; `/results/entities/0`): tags "Relaxing", "Minimalist", "Modern", "Charming", "Japanese modern", "Traditional"
- #2 Shiretoko Villa Hotel Freeze (affinity 0.9677718791352675; `/results/entities/1`): tags "Quiet", "Casual", "Traditional", "Relaxing", "Rustic", "Log cabin style"
- #3 ONE@Tokyo (affinity 0.9664694067985252; `/results/entities/2`): tags "Quiet", "Minimalist", "Modern", "Stylish", "Modern", "Industrial"

**Tag insights** (req 0018, `filter.type=urn:tag`, no namespace filter; top 10 of 20)

| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |
|---|---|---|---|---|
| 1 | Moderately expensive | urn:tag:cost_description:place | 1 | `/results/tags/0` |
| 2 | japanese drama | urn:tag:keyword:media | 1 | `/results/tags/1` |
| 3 | Five Star | urn:tag:hotel_rating:place | 1 | `/results/tags/2` |
| 4 | Cafe | urn:tag:genre:place | 1 | `/results/tags/3` |
| 5 | Manga | urn:tag:genre:media | 1 | `/results/tags/4` |
| 6 | Animation | urn:tag:genre:media | 1 | `/results/tags/5` |
| 7 | JCB | urn:tag:credit_card:place | 1 | `/results/tags/6` |
| 8 | Identifies as women-owned | urn:tag:inclusivity:place | 1 | `/results/tags/7` |
| 9 | based on manga | urn:tag:keyword:media | 0.999750583183099 | `/results/tags/8` |
| 10 | anime animation | urn:tag:keyword:media | 0.9996772979273467 | `/results/tags/9` |

## Seed `cdg` (Comme des Garçons)

- `properties.short_description` (req 0020 `/results/0/properties/short_description`): "Comme des Garçons is a Japanese fashion label founded by Rei Kawakubo, known for avant-garde clothing, accessories, and collaborations."
- Own tags by namespace (req 0020 `/results/0/tags`):
  - `urn:tag:aesthetic_property:qloo`: "Deconstructed Silhouettes", "Asymmetry", "Dark Palette", "Conceptual Graphics", "Raw Edges"
  - `urn:tag:personal_style:qloo`: "Avant-Garde", "Minimalist", "Androgynous", "Edgy", "Conceptual"
  - `urn:tag:emotional_tone:qloo`: "Provocative", "Intellectual", "Mysterious", "Subversive", "Sophisticated"
  - `urn:tag:core_value:qloo`: "Innovation", "Non-Conformity", "Creativity", "Artistry", "Independence"
  - `urn:tag:market_archetype:qloo`: "Avant-Garde", "Niche", "Heritage", "Cult"
  - `urn:tag:keyword:qloo`: "Deconstruction", "Avant-Garde", "Conceptual", "Japanese Design", "Subversion"
  - `urn:tag:cultural_relevance:qloo`: "Punk Aesthetic", "Minimalism", "Modern Art", "Streetwear Culture"
  - other namespaces (count only): `urn:tag:brand_subtype:qloo` 1, `urn:tag:brand_type:qloo` 1, `urn:tag:business_model:qloo` 3, `urn:tag:collection_cadence:qloo` 3, `urn:tag:competitor_brand:qloo` 5, `urn:tag:customer_segment:qloo` 3, `urn:tag:design_inspiration:qloo` 4, `urn:tag:fashion_segment:qloo` 5, `urn:tag:genre:brand` 3, `urn:tag:industry:qloo` 4, `urn:tag:influencer_appeal:qloo` 5, `urn:tag:interest_adjacency:qloo` 5, `urn:tag:key_market:qloo` 4, `urn:tag:lifestyle:qloo` 6, `urn:tag:material:qloo` 5, `urn:tag:partnership:qloo` 5, `urn:tag:price_level:qloo` 1, `urn:tag:product_category:qloo` 5, `urn:tag:product_service:qloo` 5, `urn:tag:retail_channel:qloo` 4, `urn:tag:signature_piece:qloo` 5, `urn:tag:similar_brand:qloo` 5, `urn:tag:subsidiary:qloo` 4, `urn:tag:sustainability_initiative:qloo` 1, `urn:tag:target_age_group:qloo` 2, `urn:tag:target_gender:qloo` 3, `urn:tag:target_income_level:qloo` 2

**Related brand** (req 0021, 10 returned; top 3; shown: `urn:tag:aesthetic_property:qloo` tags + `properties.emotional_tone`)

- #1 Vetements (affinity 0.9711303709876457; `/results/entities/0`): tags "Deconstructed Silhouettes", "Oversized Proportions", "Distressed Finishes", "Graphic Prints", "Exaggerated Volumes"; emotional_tone "Subversive", "Ironic", "Provocative", "Bold", "Edgy"
- #2 Sacai (affinity 0.9647281311264283; `/results/entities/1`): tags "Layered Construction", "Asymmetrical Silhouettes", "Hybridized Fabrics", "Technical Detailing", "Structured Volumes"; emotional_tone "Experimental", "Sophisticated", "Intellectual", "Unexpected", "Bold"
- #3 Rick Owens (affinity 0.9646909733468192; `/results/entities/2`): tags "Monochromatic Palette", "Asymmetrical Cuts", "Draped Fabrics", "Architectural Silhouettes", "Aggressive Footwear"; emotional_tone "Provocative", "Serious", "Intense", "Sophisticated", "Rebellious"

**Related movie** (req 0022, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Lady Bird (affinity 0.9087999901579679; `/results/entities/0`): tags "Quiet deadpan humor", "Handmade mirror motifs", "Naturalistic", "Warm", "Intimate", "Colorful"
- #2 Phantom Thread (affinity 0.9070344548456003; `/results/entities/1`): tags "Needle sharp", "Elegant", "Period accurate", "Atmospheric", "Operatic restraint", "Quietly erotic"
- #3 The Favourite (affinity 0.9056661540062159; `/results/entities/2`): tags "Intimate", "Lush", "Fisheye distortion", "Textured color palette", "Deadpan framing", "Baroque composition"

**Related artist** (req 0023, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Tyler, the Creator (affinity 0.9662260222769556; `/results/entities/0`): tags "Dynamic", "Theatrical", "Neo Soul", "Psychedelic Rap", "Experimental Hip Hop", "Energetic"
- #2 KAYTRANADA (affinity 0.9613786076228861; `/results/entities/1`): tags "Alternative R&B", "Hip Hop Soul", "Electronic Funk", "Future House", "Dynamic", "Dancefloor Grooves"
- #3 Blood Orange (affinity 0.9609904815042196; `/results/entities/2`): tags "Electro Funk", "Indie Pop", "Alternative R&B", "Intimate", "Synthpop", "Expressive"

**Related book** (req 0024, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 The Other Hollywood: The Uncensored Oral History of the Porn Film Industry (affinity 0.8507392487299815; `/results/entities/0`): tags none returned
- #2 Norma Jean (affinity 0.8433291690602489; `/results/entities/1`): tags "Insightful", "Thorough", "Engaging", "Tragic", "Revealing"
- #3 Letters of Note: An Eclectic Collection of Correspondence Deserving of a Wider Audience (affinity 0.8362765902246105; `/results/entities/2`): tags none returned

**Related person** (req 0025, 10 returned; top 3; shown: `urn:tag:occupation:person` tags)

- #1 Kim Jones (affinity 0.9681568501199025; `/results/entities/0`): tags "Personal Stylist"
- #2 Haider Ackermann (affinity 0.9642464221622589; `/results/entities/1`): tags "Artist", "Fashion Designer"
- #3 Kris Van Assche (affinity 0.9615937045755109; `/results/entities/2`): tags "Fashion Designer", "Model", "Art Director"

**Related place** (req 0026, 10 returned; top 3; shown: `urn:tag:ambience:qloo` tags + `urn:tag:decor:qloo` tags)

- #1 Vivienne Westwood Worlds End (affinity 0.9554818679989344; `/results/entities/0`): tags "Quirky", "Stylish", "Unique", "Charming", "Eclectic", "Historic"
- #2 Caviar Kaspia (affinity 0.9469074101421815; `/results/entities/1`): tags "Classic", "Luxurious", "Gastronomic", "Historic", "Romantic", "Classic"
- #3 Burberry (affinity 0.9464858949825657; `/results/entities/2`): tags "Elegant", "Stylish", "Contemporary", "British luxury", "Modern", "Luxurious"

**Tag insights** (req 0027, `filter.type=urn:tag`, no namespace filter; top 10 of 20)

| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |
|---|---|---|---|---|
| 1 | JCB | urn:tag:credit_card:place | 1 | `/results/tags/0` |
| 2 |  electronic | urn:tag:genre:music | 1 | `/results/tags/1` |
| 3 | Deconstruction | urn:tag:keyword:qloo | 1 | `/results/tags/2` |
| 4 | Identifies as women-owned | urn:tag:inclusivity:place | 1 | `/results/tags/3` |
| 5 | Oyster Platter | urn:tag:specialty_dish:place | 1 | `/results/tags/4` |
| 6 | Expensive | urn:tag:cost_description:place | 1 | `/results/tags/5` |
| 7 | japanese drama | urn:tag:keyword:media | 1 | `/results/tags/6` |
| 8 | Five Star | urn:tag:hotel_rating:place | 1 | `/results/tags/7` |
| 9 | Art gallery | urn:tag:genre:place | 1 | `/results/tags/8` |
| 10 | Deconstructed | urn:tag:aesthetic_property:qloo | 0.9999131039277025 | `/results/tags/9` |

## Seed `nike` (Nike)

- `properties.short_description` (req 0029 `/results/0/properties/short_description`): "Nike is a global brand specializing in athletic footwear, apparel, equipment, and accessories for men, women, and kids."
- Own tags by namespace (req 0029 `/results/0/tags`):
  - `urn:tag:aesthetic_property:qloo`: "Minimalist Logo Design", "Technological Aesthetics", "Performance-Driven Silhouettes", "Dynamic Motion Lines"
  - `urn:tag:personal_style:qloo`: "Sporty", "Minimalist", "Functional", "Urban"
  - `urn:tag:emotional_tone:qloo`: "Bold", "Motivating", "Energetic", "Empowering", "Confident"
  - `urn:tag:core_value:qloo`: "Innovation", "Excellence", "Inclusivity", "Performance", "Equality"
  - `urn:tag:market_archetype:qloo`: "Mainstream", "Heritage", "Challenger"
  - `urn:tag:keyword:qloo`: "Innovation", "Sport", "Performance", "Movement", "Empowerment"
  - `urn:tag:cultural_relevance:qloo`: "Global Sports Culture", "Hip-Hop", "Streetwear Movement", "Social Justice Advocacy"
  - other namespaces (count only): `urn:tag:brand_subtype:qloo` 1, `urn:tag:brand_type:qloo` 1, `urn:tag:business_model:qloo` 2, `urn:tag:collection_cadence:qloo` 3, `urn:tag:competitor_brand:qloo` 5, `urn:tag:customer_segment:qloo` 4, `urn:tag:design_inspiration:qloo` 4, `urn:tag:fashion_segment:qloo` 4, `urn:tag:genre:brand` 7, `urn:tag:industry:qloo` 5, `urn:tag:influencer_appeal:qloo` 5, `urn:tag:interest_adjacency:qloo` 5, `urn:tag:key_market:qloo` 5, `urn:tag:lifestyle:qloo` 8, `urn:tag:material:qloo` 5, `urn:tag:partnership:qloo` 5, `urn:tag:price_level:qloo` 1, `urn:tag:product_category:qloo` 5, `urn:tag:product_service:qloo` 5, `urn:tag:retail_channel:qloo` 5, `urn:tag:signature_piece:qloo` 5, `urn:tag:similar_brand:qloo` 5, `urn:tag:subsidiary:qloo` 2, `urn:tag:sustainability_initiative:qloo` 9, `urn:tag:target_age_group:qloo` 6, `urn:tag:target_gender:qloo` 4, `urn:tag:target_income_level:qloo` 4, `urn:tag:wikipedia_category` 22

**Related brand** (req 0030, 10 returned; top 3; shown: `urn:tag:aesthetic_property:qloo` tags + `properties.emotional_tone`)

- #1 Air Jordan Product Line (affinity 0.969972417154696; `/results/entities/0`): tags "Bold Branding", "Dynamic Silhouettes", "High-Contrast Colorways", "Performance-Oriented Design"; emotional_tone "Bold", "Confident", "Ambitious", "Electrifying"
- #2 Real Madrid CF (affinity 0.9690527331926435; `/results/entities/1`): tags "White And Gold Color Palette", "Minimalist Crest Design", "Modern Stadium Infrastructure", "Dynamic Promotional Imagery"; emotional_tone "Passionate", "Proud", "Exhilarating", "Determined", "Prestigious"
- #3 National Basketball Association (affinity 0.9648099103224258; `/results/entities/2`): tags "Bold Typography", "High-Contrast Branding", "Dynamic Photography", "Iconic Color Palettes"; emotional_tone "Competitive", "Energetic", "Exciting", "Inspiring"

**Related movie** (req 0031, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Creed (affinity 0.9372771980908613; `/results/entities/0`): tags "Realistic", "Intimate", "Montage driven", "Kinetic", "Sweat drenched", "Handheld intimacy"
- #2 Creed II (affinity 0.9368145539762308; `/results/entities/1`): tags "Gritty", "Intimate", "Cinematic", "Nostalgic homage", "Visceral", "Close up intimacy"
- #3 John Wick: Chapter 2 (affinity 0.9046402814649322; `/results/entities/2`): tags "Neon noir lighting", "Gritty", "Hyper choreographed gunplay", "Kinetic", "Clinical close quarter combat", "Elegant weaponry framing"

**Related artist** (req 0032, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Wiz Khalifa (affinity 0.9789124253791885; `/results/entities/0`): tags "Pop-Influenced Hip Hop", "Marijuana-Themed", "Laid Back", "Melodic Rap", "Engaging", "Laid-Back Flow"
- #2 Jay-Z (affinity 0.9766692852135209; `/results/entities/1`): tags "Dynamic", "Engaging", "Gangsta Rap", "Charismatic", "Boom Bap", "East Coast Hip Hop"
- #3 DJ Khaled (affinity 0.9764786784079703; `/results/entities/2`): tags "Showmanlike", "Anthemic", "Engaging", "Charismatic", "Radio Friendly", "Energetic"

**Related book** (req 0033, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 Showtime: Magic, Kareem, Riley, and the Los Angeles Lakers Dynasty of the 1980s (affinity 0.9102194282429557; `/results/entities/0`): tags "Vivid", "Engaging", "Comprehensive", "Dynamic", "Informative"
- #2 A Season on the Brink: A Year with Bob Knight and the Indiana Hoosiers (affinity 0.9092650663003289; `/results/entities/1`): tags "In-depth", "Journalistic", "Candid", "Unfiltered", "Engaging"
- #3 The Boys of Dunbar: A Story of Love, Hope, and Basketball (affinity 0.9049981840976431; `/results/entities/2`): tags none returned

**Related person** (req 0034, 10 returned; top 3; shown: `urn:tag:occupation:person` tags)

- #1 Daniel Alves (affinity 0.97223622587072; `/results/entities/0`): tags "Association Football Player"
- #2 Andrés Iniesta (affinity 0.9716028756911764; `/results/entities/1`): tags "Association Football Player"
- #3 Iker Casillas (affinity 0.9697154515127488; `/results/entities/2`): tags "Association Football Player"

**Related place** (req 0035, 10 returned; top 3; shown: `urn:tag:ambience:qloo` tags + `urn:tag:decor:qloo` tags)

- #1 ZT The Golden Hotel Barcelona (affinity 0.9423525470173761; `/results/entities/0`): tags none returned
- #2 Mercedes Heritage Apartments Barcelona (affinity 0.9389725440634531; `/results/entities/1`): tags "Welcoming", "Modern", "Functional", "Comfortable", "Urban residential", "Modern"
- #3 Meliá Paris La Défense (affinity 0.9387765010871101; `/results/entities/2`): tags "Lively", "Stylish", "Corporate minimalism", "Convenient", "Welcoming", "Sophisticated"

**Tag insights** (req 0036, `filter.type=urn:tag`, no namespace filter; top 10 of 20)

| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |
|---|---|---|---|---|
| 1 | VISA | urn:tag:credit_card:place | 1 | `/results/tags/0` |
| 2 | Tataki Atun | urn:tag:specialty_dish:place | 1 | `/results/tags/1` |
| 3 | Moderately expensive | urn:tag:cost_description:place | 1 | `/results/tags/2` |
| 4 |  Hip Hop | urn:tag:genre:music | 1 | `/results/tags/3` |
| 5 | Identifies as women-owned | urn:tag:inclusivity:place | 1 | `/results/tags/4` |
| 6 | Hotel | urn:tag:genre:place | 1 | `/results/tags/5` |
| 7 | Sports | urn:tag:genre:media | 1 | `/results/tags/6` |
| 8 | Five Star | urn:tag:hotel_rating:place | 1 | `/results/tags/7` |
| 9 | Women Empowerment | urn:tag:cultural_relevance:qloo | 0.9999053060193807 | `/results/tags/8` |
| 10 | Sport | urn:tag:keyword:qloo | 0.9998774659968142 | `/results/tags/9` |

## Seed `ralph_lauren` (Ralph Lauren)

- `properties.short_description` (req 0038 `/results/0/properties/short_description`): "Ralph Lauren is a global fashion brand known for its men's, women's, and kids' clothing, accessories, and home decor, famous for its Polo line."
- Own tags by namespace (req 0038 `/results/0/tags`):
  - `urn:tag:aesthetic_property:qloo`: "Classic Tailoring", "Preppy Patterns", "Neutral Color Palettes", "Signature Polo Logo"
  - `urn:tag:personal_style:qloo`: "Preppy", "Classic", "Sophisticated", "Minimalist"
  - `urn:tag:emotional_tone:qloo`: "Sophisticated", "Nostalgic", "Refined", "Confident"
  - `urn:tag:core_value:qloo`: "Timelessness", "Quality", "Authenticity", "Craftsmanship"
  - `urn:tag:market_archetype:qloo`: "Mainstream", "Heritage"
  - `urn:tag:keyword:qloo`: "Polo", "Americana", "Preppy", "Heritage", "Timeless"
  - `urn:tag:cultural_relevance:qloo`: "Americana", "Ivy League Style", "Old Money Aesthetic"
  - other namespaces (count only): `urn:tag:brand_subtype:qloo` 1, `urn:tag:brand_type:qloo` 1, `urn:tag:business_model:qloo` 3, `urn:tag:collection_cadence:qloo` 3, `urn:tag:competitor_brand:qloo` 5, `urn:tag:customer_segment:qloo` 4, `urn:tag:design_inspiration:qloo` 4, `urn:tag:fashion_segment:qloo` 5, `urn:tag:genre:brand` 10, `urn:tag:industry:qloo` 3, `urn:tag:influencer_appeal:qloo` 4, `urn:tag:interest_adjacency:qloo` 5, `urn:tag:key_market:qloo` 5, `urn:tag:lifestyle:qloo` 8, `urn:tag:material:qloo` 5, `urn:tag:partnership:qloo` 3, `urn:tag:price_level:qloo` 1, `urn:tag:product_category:qloo` 7, `urn:tag:product_service:qloo` 8, `urn:tag:retail_channel:qloo` 3, `urn:tag:signature_piece:qloo` 4, `urn:tag:similar_brand:qloo` 4, `urn:tag:subsidiary:qloo` 4, `urn:tag:sustainability_initiative:qloo` 3, `urn:tag:target_age_group:qloo` 6, `urn:tag:target_gender:qloo` 3, `urn:tag:target_income_level:qloo` 3, `urn:tag:wikipedia_category` 24

**Related brand** (req 0039, 10 returned; top 3; shown: `urn:tag:aesthetic_property:qloo` tags + `properties.emotional_tone`)

- #1 Armani Exchange (affinity 0.9707017742679687; `/results/entities/0`): tags "Minimalist Logo Branding", "Monochromatic Palettes", "Clean Lines", "Urban-Casual Silhouette", "Sleek Hardware"; emotional_tone "Confident", "Dynamic", "Urban", "Accessible", "Modern"
- #2 Louis Vuitton (affinity 0.9703935832640984; `/results/entities/1`): tags "Monogram Canvas", "Minimalist Hardware", "Signature Damier Pattern", "Structured Silhouettes", "Rich Leather Textures"; emotional_tone "Sophisticated", "Prestigious", "Timeless", "Ambitious"
- #3 Versace (affinity 0.9687118470056398; `/results/entities/2`): tags "Medusa Head Motif", "Baroque Prints", "Gold Accents", "Vibrant Colors", "Maximalist Design"; emotional_tone "Bold", "Glamorous", "Provocative", "Confident", "Sophisticated"

**Related movie** (req 0040, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 A Star Is Born (affinity 0.9034127701824036; `/results/entities/0`): tags "Naturalistic", "Moody", "Raw vocal close ups", "Handheld concert intimacy", "Glam to backstage contrast", "Live performance realism"
- #2 Molly's Game (affinity 0.9005838257582333; `/results/entities/1`): tags "Cinematic", "Dynamic", "Wardrobe focused", "Dialogue driven", "Nonlinear narrative", "Tight close ups"
- #3 Crazy Rich Asians (affinity 0.8955242595612203; `/results/entities/2`): tags "Opulent production design", "Cinematic", "Ornate costume spectacle", "Lush", "Colorful", "Polished"

**Related artist** (req 0041, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 DJ Khaled (affinity 0.9738833434786272; `/results/entities/0`): tags "Showmanlike", "Anthemic", "Engaging", "Charismatic", "Radio Friendly", "Energetic"
- #2 50 Cent (affinity 0.9729247389311848; `/results/entities/1`): tags "Gangsta Rap", "Engaging", "Confident", "Energetic", "Hardcore Hip Hop", "Street Rap"
- #3 Drake&Orson (affinity 0.9679236200868998; `/results/entities/2`): tags "Dynamic", "Emotional R&B", "Energetic", "Trap-Influenced Pop", "Charismatic", "Melodic Rap"

**Related book** (req 0042, 10 returned; top 3; shown: `urn:tag:style:qloo` tags)

- #1 And Then It Fell Apart (affinity 0.8937199779392067; `/results/entities/0`): tags "Candid", "Unflinching", "Entertaining", "Introspective", "Raw"
- #2 Powerhouse (affinity 0.866778347655498; `/results/entities/1`): tags none returned
- #3 Norma Jean (affinity 0.8620948996276546; `/results/entities/2`): tags "Insightful", "Thorough", "Engaging", "Tragic", "Revealing"

**Related person** (req 0043, 10 returned; top 3; shown: `urn:tag:occupation:person` tags)

- #1 Christian Louboutin (affinity 0.982404388096383; `/results/entities/0`): tags "Fashion Designer"
- #2 Giorgio Armani (affinity 0.9823275762163705; `/results/entities/1`): tags "Entrepreneur", "Fashion Designer"
- #3 Valentino (affinity 0.9770071620961732; `/results/entities/2`): tags "Businessperson", "Fashion Designer"

**Related place** (req 0044, 10 returned; top 3; shown: `urn:tag:ambience:qloo` tags + `urn:tag:decor:qloo` tags)

- #1 Fairmont Monte Carlo (affinity 0.962102146773483; `/results/entities/0`): tags "Stylish", "Beige and blue coastal", "Comfortable", "Elegant", "Lively", "Prestigious"
- #2 La Bourdonnais (affinity 0.9592905769651418; `/results/entities/1`): tags "Charming", "Elegant", "Romantic", "Elegant", "Stylish", "Comfortable"
- #3 Meliá Paris La Défense (affinity 0.9560873832398683; `/results/entities/2`): tags "Lively", "Stylish", "Corporate minimalism", "Convenient", "Welcoming", "Sophisticated"

**Tag insights** (req 0045, `filter.type=urn:tag`, no namespace filter; top 10 of 20)

| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |
|---|---|---|---|---|
| 1 | Hotel | urn:tag:genre:place | 1 | `/results/tags/0` |
| 2 | Expensive | urn:tag:cost_description:place | 1 | `/results/tags/1` |
| 3 |  Hip Hop | urn:tag:genre:music | 1 | `/results/tags/2` |
| 4 | Fashion | urn:tag:genre:media | 1 | `/results/tags/3` |
| 5 | VISA | urn:tag:credit_card:place | 1 | `/results/tags/4` |
| 6 | Dessert Platter | urn:tag:specialty_dish:place | 1 | `/results/tags/5` |
| 7 | Identifies as women-owned | urn:tag:inclusivity:place | 1 | `/results/tags/6` |
| 8 | Five Star | urn:tag:hotel_rating:place | 1 | `/results/tags/7` |
| 9 | Refined Tailoring | urn:tag:aesthetic_property:qloo | 0.9999344820808491 | `/results/tags/8` |
| 10 | Elegant Fabrics | urn:tag:aesthetic_property:qloo | 0.9998560778331078 | `/results/tags/9` |

## Cross-seed checks (returned IDs only)

Own descriptive tag IDs carried by more than one seed (same ID; similar names under different IDs are not merged):

| Tag ID | Name | Seeds |
|---|---|---|
| `urn:tag:personal_style:qloo:minimalist` | minimalist | cdg, muji, nike, ralph_lauren |
| `urn:tag:core_value:qloo:innovation` | Innovation | a24, cdg, nike |
| `urn:tag:emotional_tone:qloo:sophisticated` | Sophisticated | a24, cdg, ralph_lauren |
| `urn:tag:market_archetype:qloo:heritage` | Heritage | cdg, nike, ralph_lauren |
| `urn:tag:market_archetype:qloo:mainstream` | Mainstream | muji, nike, ralph_lauren |
| `urn:tag:core_value:qloo:creativity` | Creativity | a24, cdg |
| `urn:tag:core_value:qloo:independence` | Independence | a24, cdg |
| `urn:tag:core_value:qloo:quality` | Quality | muji, ralph_lauren |
| `urn:tag:cultural_relevance:qloo:modern_art` | Modern Art | a24, cdg |
| `urn:tag:emotional_tone:qloo:confident` | Confident | nike, ralph_lauren |
| `urn:tag:emotional_tone:qloo:provocative` | Provocative | a24, cdg |
| `urn:tag:market_archetype:qloo:avant_garde` | Avant-Garde | a24, cdg |
| `urn:tag:market_archetype:qloo:challenger` | Challenger | a24, nike |
| `urn:tag:market_archetype:qloo:cult` | Cult | a24, cdg |
| `urn:tag:market_archetype:qloo:niche` | Niche | a24, cdg |
| `urn:tag:personal_style:qloo:functional` | functional | muji, nike |

Related-entity overlap between seeds (pairs with at least one shared returned ID; all other pairs share none):

| Domain request | Seed pair | Shared IDs | Union |
|---|---|---|---|
| urn:entity:movie | a24 / cdg | 2 | 18 |
| urn:entity:artist | a24 / cdg | 1 | 19 |
| urn:entity:artist | nike / ralph_lauren | 7 | 13 |
| urn:entity:book | cdg / ralph_lauren | 2 | 18 |
| urn:entity:place | nike / ralph_lauren | 2 | 18 |
| seed_tags | a24 / cdg | 1 | 39 |
| seed_tags | a24 / muji | 1 | 39 |
| seed_tags | a24 / nike | 1 | 39 |
| seed_tags | a24 / ralph_lauren | 1 | 39 |
| seed_tags | cdg / muji | 6 | 34 |
| seed_tags | cdg / nike | 2 | 38 |
| seed_tags | cdg / ralph_lauren | 3 | 37 |
| seed_tags | muji / nike | 3 | 37 |
| seed_tags | muji / ralph_lauren | 2 | 38 |
| seed_tags | nike / ralph_lauren | 5 | 35 |

## Requests cited

Exact non-secret request of each cited local ID (GET; the credential is added by the environment and never stored).

| Request | Operation | Path | Parameters | Status | Reused from |
|---|---|---|---|---|---|
| req 0001 | search  | `/search` | `query=A24&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0002 | seed_detail  | `/entities` | `entity_ids=7E904879-87BC-4BA6-B4AB-6E380A4C250D` | ok | live-20261006T102530Z-61e1 |
| req 0003 | related_entities brand | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:brand&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0004 | related_entities movie | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:movie&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0005 | related_entities artist | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:artist&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0006 | related_entities book | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:book&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | — |
| req 0007 | related_entities person | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:person&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | — |
| req 0008 | related_entities place | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:place&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=10` | ok | — |
| req 0009 | seed_tags  | `/v2/insights` | `filter.type=urn:tag&signal.interests.entities=7E904879-87BC-4BA6-B4AB-6E380A4C250D&take=20` | ok | live-20261006T102530Z-61e1 |
| req 0010 | search  | `/search` | `query=MUJI&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0011 | seed_detail  | `/entities` | `entity_ids=E12201A5-CC50-40AF-97AE-C54A2CA303F7` | ok | live-20261006T102530Z-61e1 |
| req 0012 | related_entities brand | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:brand&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0013 | related_entities movie | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:movie&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0014 | related_entities artist | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:artist&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | live-20261006T102530Z-61e1 |
| req 0015 | related_entities book | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:book&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | — |
| req 0016 | related_entities person | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:person&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | — |
| req 0017 | related_entities place | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:place&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=10` | ok | — |
| req 0018 | seed_tags  | `/v2/insights` | `filter.type=urn:tag&signal.interests.entities=E12201A5-CC50-40AF-97AE-C54A2CA303F7&take=20` | ok | live-20261006T102530Z-61e1 |
| req 0019 | search  | `/search` | `query=Comme des Garçons&take=10` | ok | — |
| req 0020 | seed_detail  | `/entities` | `entity_ids=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD` | ok | — |
| req 0021 | related_entities brand | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:brand&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0022 | related_entities movie | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:movie&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0023 | related_entities artist | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:artist&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0024 | related_entities book | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:book&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0025 | related_entities person | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:person&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0026 | related_entities place | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:place&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=10` | ok | — |
| req 0027 | seed_tags  | `/v2/insights` | `filter.type=urn:tag&signal.interests.entities=3637BC2E-B2D1-4496-9BD7-938E4FAE81AD&take=20` | ok | — |
| req 0028 | search  | `/search` | `query=Nike&take=10` | ok | — |
| req 0029 | seed_detail  | `/entities` | `entity_ids=C70CE2B8-0AD1-4150-BF18-5A6347F2E860` | ok | — |
| req 0030 | related_entities brand | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:brand&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0031 | related_entities movie | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:movie&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0032 | related_entities artist | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:artist&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0033 | related_entities book | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:book&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0034 | related_entities person | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:person&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0035 | related_entities place | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:place&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=10` | ok | — |
| req 0036 | seed_tags  | `/v2/insights` | `filter.type=urn:tag&signal.interests.entities=C70CE2B8-0AD1-4150-BF18-5A6347F2E860&take=20` | ok | — |
| req 0037 | search  | `/search` | `query=Ralph Lauren&take=10` | ok | — |
| req 0038 | seed_detail  | `/entities` | `entity_ids=2723B38E-C3E2-435F-A77B-A94A92D68D07` | ok | — |
| req 0039 | related_entities brand | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:brand&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0040 | related_entities movie | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:movie&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0041 | related_entities artist | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:artist&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0042 | related_entities book | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:book&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0043 | related_entities person | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:person&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0044 | related_entities place | `/v2/insights` | `feature.explainability=true&filter.type=urn:entity:place&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=10` | ok | — |
| req 0045 | seed_tags  | `/v2/insights` | `filter.type=urn:tag&signal.interests.entities=2723B38E-C3E2-435F-A77B-A94A92D68D07&take=20` | ok | — |

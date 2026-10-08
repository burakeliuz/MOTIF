# Why Adidas and OpenAI leave dimensions open and share one structure

Review of 2026-10-07, prompted by two hosted-demo results.
The hosted sessions are not reachable from the build environment, so both brands
were fetched once through the product's own controller (`LiveQloo`, direct
transport, `https://hackathon.api.qloo.com`): **8 Qloo requests** (search, own
entry, related brands, related films per brand; no failure, no retry), **no LLM
call**. Raw responses: git-ignored `data/motif_sessions/review-20261007T173852Z/`.
Everything below is replayed offline from them with the shipped versions
(`lexicon-0.3`, `scoring-1.0`, `sensory-1.0`, `continuous-params-1.0`,
`olfactory-1.1`). No engine file was changed.

## 1. What Qloo returned and what MOTIF reads

| | Adidas | OpenAI |
|---|---|---|
| Own-entry descriptors | 12 | 8 |
| Related brands / films | 10 / 10 | 10 / 10 |
| Distinct descriptors returned | 139 | 129 |
| Distinct descriptors MOTIF reads as motif support | **3** | **5** |
| Own entry read | "minimalist", "Minimalist Branding" only as a common word (counted lightly) | "Geometric" → precision; "Minimalist" as a common word |
| Own descriptors not read | Bold Graphic Elements, Technological Design, Three-Stripe Motif, Aspirational, Bold, Confident, Energetic, casual, sporty, urban | Clean, Modern, Analytical, Empowering, Intellectual, Visionary |
| Frequent unread related descriptors | Cinematic, Energetic, Gritty, Moody, Confident, Kinetic, Dynamic, Empowering | Atmospheric, Cinematic, Collaborative, Polished (7×), Moody, Professional, Analytical, Technical, Innovative |

Across all 19 recorded brands Qloo returns 122–143 distinct descriptors per
brand; MOTIF reads 1–27 of them.

## 2. Why dimensions stay open

Both results rest on two motifs: **restraint** (cell: weight → light, medium
confidence) and **precision** (texture → smooth-finished, medium; temperature →
cool, low). Neither has a cell for impression, projection, or sweetness, so
those dimensions have no contribution at all (mass 0). Adidas' temperature has
one faint contribution (precision from a single related brand, mass 0.016 against
the threshold 0.05).

| Dimension | Adidas | OpenAI |
|---|---|---|
| Temperature | open: faint cool lean from precision | slightly cool, tentative |
| Weight | light, supported (restraint) | light, supported (restraint) |
| Texture | smooth-finished, tentative (precision from one related brand) | smooth-finished, supported (precision, own entry) |
| Impression, projection, sweetness | open: no read motif speaks to them | open: no read motif speaks to them |

Across the 19 brands, 65 dimensions are open: 25 because no read motif speaks to
them, 23 because motifs pull both ways, 17 because the lean is too weak.

**Answer.** Qloo's data is not the limit: it returns well over a hundred
descriptors per brand. The limit is MOTIF's translation: the lexicon reads a few
percent of them, and the motifs it reads only speak to some dimensions. The
presentation also under-told the result (four separate "Open to the perfumer"
lines, no reason, and a profile that hid most of what carried restraint for
Adidas; section 4).

## 3. Why both reach the same architecture

The architecture is matched by cosine similarity to the resolved commitment
(direction, not size). Both targets point the same way: light weight plus a
smooth texture (Adidas: light −0.23, smooth +0.12; OpenAI: light −0.30, smooth
+0.31, cool +0.06). With that target, the only eligible opening is watery/ozonic,
the best core is transparent floral, and the best drydown is powdery iris, for
both brands (fits: transparent floral 0.84 / 0.79, watery/ozonic 0.59 / 0.51,
powdery iris 0.42 / 0.63; the next eligible drydowns are creamy woods and clean
musk). The structures are identical because what MOTIF can read of the two
brands reduces to the same two motifs; the real differences (Adidas: bold,
energetic, sporty, kinetic; OpenAI: analytical, intellectual, technical) are not
in the lexicon. Making them differ inside the olfactory layer would be forcing.

## 4. "Understated humanism" → restraint (Adidas)

- **Mechanically correct** under `lexicon-0.3`: "understated" is a restraint
  cue, and the context rules only drop film technique nouns.
- **Contextually weak:** the tag describes the narrative tone of a legal drama
  (*Just Mercy*), not a visual or material aesthetic. It is one of ten films Qloo
  relates to Adidas, and Adidas' own descriptors point the other way (Bold,
  Energetic, Confident, Bold Graphic Elements), unread.
- **Not the main source of the score, but the switch.** Restraint's score
  (0.347) is: Adidas' own "minimalist" as a common word 0.18, "Minimalist" in 7
  related brands 0.11, the film tag 0.10. A common word counts only for a motif
  with other support, and the film tag is that support. What-if, not applied:
  without it, restraint becomes common-only, no motif leads, Adidas' outcome
  becomes "insufficient evidence", weight opens, and the structure changes
  (aldehydic, clean / powdery iris / creamy woods from precision alone).
- The page showed only the film tag and "references only", which hid that
  Adidas' own "minimalist" carries the largest part. Now disclosed (section 5).

## 5. Presentation changes (applied; no engine change)

- **Open dimensions told once.** One "Open to the perfumer" block in the
  olfactory direction, grouped by why (no read motif speaks to them / too weak to
  decide, with the faint lean and its motif / motifs pull both ways, with both
  sides), and one line on coverage: how many of the descriptors Qloo returned
  MOTIF's vocabulary reads, quoting up to three of the brand's own unread
  descriptors. The same paragraph in the HTML brief and the PDF. Nothing is
  filled in; the dimensions stay open.
- **The proposal in words.** "In scent:" one sentence from the chosen
  directions (for Adidas: watery and ozonic to open, a transparent floral core, a
  powdery iris and violet drydown), then what the accords themselves bring to the
  open dimensions, from their documented cells in `olfactory-1.1` (for Adidas:
  slightly cool, synthetic-feeling, slightly sweet; projection mixed, diffusive
  in the core and close-wearing in the drydown). Labelled as MOTIF's creative
  proposal; not Qloo evidence. When an accord goes against a lean the evidence
  shows too weakly to decide, the text says so (Coca-Cola: "synthetic-feeling
  (against the faint natural-feeling lean)").
- **Evidence apart from interpretation.** Section labels: Cultural profile =
  Qloo evidence; Olfactory direction = MOTIF's translation; Scent architecture
  and Emphasize and avoid = MOTIF's creative proposal.
- **Common words disclosed.** A profile row says when a common word counts
  lightly and where ("“minimalist”, a word common to many brands, in Adidas' own
  entry and 7 related brands"). The related-only headline line now says the
  motif "leads only with the references".
- **Rows aligned.** Every motif and why row shares one 210 px label column at
  24 px (the longest label word, EXPERIMENTATION, fits); on phones every row
  stacks the same way.

## 6. Engine proposals (not applied; each needs a version bump and a new holdout)

1. **Lexicon coverage (`lexicon-0.4`).** Read frequent descriptors that fit an
   existing motif (for example "Polished" and "Clean" for precision), and decide
   whether energy (bold, energetic, dynamic, kinetic) and intellect or technology
   (analytical, technical, innovative) need motifs of their own. New motifs need
   sensory cells researched like `sensory-1.0`. This is the change that would let
   Adidas and OpenAI differ.
2. **Narrative tone in film tags (`lexicon-0.4`).** Treat restraint or intimacy
   words that qualify a story ("humanism", "storytelling", "performances") as
   context, not support. Effect on Adidas: as in the what-if of section 4.
3. **Unlocking common words (`scoring-1.1`).** Let a common word count only when
   the other support comes from the brand's own entry or from at least two
   related entities. Effect on Adidas: the same as proposal 2.
4. **No change to the olfactory layer for convergence.** Identical structures
   follow identical readable evidence; differentiation should come from proposal 1.

Proposals 2 and 3 make Adidas' result thinner but more honest; proposal 1 is the
one that adds information. None was applied as part of this review.

## 7. Applied after the review (2026-10-07)

Proposals 1 and 2 were applied as `lexicon-0.4` and `sensory-1.1`, limited to
energy, technology, and design words, with no brand exception; proposal 3 was
not. Differences from the proposal text above: "Polished" (the texture pole word
itself), "Clean" (mostly typography and interface words of related brands),
"bold", "kinetic", "analytical", and "innovative" were left out; the new cells
are creative design decisions, not researched (a project decision); the
narrative-tone rule covers look and material motifs only, so intimacy told as a
story still counts. Replayed offline from the same recordings:

| | Adidas | OpenAI |
|---|---|---|
| Leading motifs | energy, technology (own entry), precision (references) | precision (own entry), restraint, technology (references) |
| Resolved | smooth-finished texture; slightly diffusive; slightly synthetic-feeling | slightly cool; light; smooth-finished; slightly synthetic-feeling |
| Open to the perfumer | temperature, weight, sweetness | projection, sweetness |
| Scent idea | aldehydic and clean / powdery iris and violet / creamy woods | watery and ozonic / transparent floral / powdery iris and violet |

"Understated humanism" is now excluded as narrative tone; Adidas' restraint is
context only and its weight is open. The two structures differ because what
MOTIF reads of the two brands differs, not because difference was a target.
Effect on all 19 recorded brands: `docs/REFACTOR_LOG.md`.

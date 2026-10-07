# Devpost submission texts (copy-ready drafts)

Drafts for the owner to paste into Devpost. The project is already submitted;
nothing here has been entered or changed on Devpost by the build agent. Every
claim below matches the implemented product and the reports in this repository
(`reports/trial_6b.md`, `docs/STAGE_6A_DECISIONS.md`).

**Status of these texts: draft for after deployment.** The hosted demo runs `main`
(commit `73e6b64`: the stage 5 interface behind the review password). The texts
below describe the version on the session branch (art direction A with scent
strips, cultural profile, printable brief, one retry, the
LLM budget guard). They become true only after the owner merges the branch into
`main` and redeploys Render. If that does not happen, use the "Current demo
variant" at the end instead of the testing steps and gallery.

Basic fields:

- **Project name:** MOTIF
- **Tagline (≈ 200 characters):** If a brand were a scent: MOTIF reads how culture describes a brand in Qloo and turns it, rule by rule, into a scent direction, verified starting materials, and a one-page perfumer brief.
- **Demo URL:** https://motif-pxh8.onrender.com (behind a reviewer password, see testing instructions)
- **Repository:** https://github.com/burakeliuz/MOTIF (MIT license for the code)

## About the project

### Inspiration

Brand and creative teams who commission a scent (a signature scent for stores, a
first fragrance, a hotel or retail atmosphere) usually brief a perfumer with
mood boards and adjectives. The brief decides a lot, yet it rarely says why a
direction fits the brand. We asked a sharper question: if this brand were a
scent, what would it be, and can every step from culture to scent be shown and
checked? (The need is our working assumption; no brand team or perfumer has
validated MOTIF yet.)

### What it does

You type a brand and, optionally, a one-line purpose for the brief ("a signature
scent for the flagship stores"). MOTIF then shows, step by step:

1. **Qloo, the cultural references.** MOTIF finds the brand in Qloo (and asks you
   when a name is ambiguous: "Le Labo" returns two shops and the brand "Le Labo
   Fragrances"). It reads the descriptors Qloo attaches to the brand itself and to
   the brands and films Qloo relates to it.
2. **MOTIF, the scent direction.** Repeated descriptors become motifs (restraint,
   precision, provocation …). A cultural profile ranks them, the brand's own
   entry first. Five visible, versioned rules translate motifs into directions on
   six sensory dimensions; a dimension the evidence does not decide stays open,
   never a midpoint. Starting materials (top, heart, base) are proposed only from
   properties verified on the supplier's own page, drawn as scent strips.
3. **Claude, the brief.** Claude writes the brief in plain words from the
   result; MOTIF checks it (no new materials, numbers, or audience claims; every
   open dimension named) and falls back to a labelled template otherwise. An
   optional application context ("a hotel lobby", "a product launch") frames
   the brief; it does not change the cultural evidence or the direction. The
   brief prints as one A4 page with clickable sources.

Examples from live runs (2026-10-07):

- **MUJI**: "Restraint, precision and naturalness: a light, smooth-finished and
  natural-feeling scent." Bergamot (top), HEDIONE (heart), HABANOLIDE (base),
  each with the supplier's own words. Temperature, projection, and sweetness stay
  open.
- **Gucci**: "A profile led by provocation." MOTIF has no rule for provocation
  yet, so that is named as the next creative decision; the proposed direction so
  far (dense, smooth-finished) comes only from references Qloo relates to Gucci,
  and says so.
- **Harley-Davidson**: "A profile led by heritage." No direction yet: MOTIF has
  no rule for heritage, and it says so instead of guessing.

### How we built it

- **Qloo Hackathon API**: `/search`, `/entities` (the brand's own entry), and
  `/v2/insights` for related brands and films; at most four requests per brand,
  cached per brand so answering a question, changing the purpose, refreshing, or
  printing repeats nothing.
- **A research controller** (a deterministic state machine, not an LLM) decides
  each step: it resolves the entity or asks you to choose, fetches the own entry
  and related brands, fetches films only when they can still change the result,
  asks you when two motifs pull one dimension both ways, stops on a failed
  request with what it has, and offers one controlled retry (after deployment).
- **The engine** (Python standard library): a lexicon of twelve motifs
  (lexicon-0.3), five draft rules (draft-0.2), and a verified palette
  (palette-0.3: seven of eight materials checked on Givaudan and dsm-firmenich
  pages, the supplier's words kept apart from MOTIF's reading). The same evidence
  and versions always give the same result.
- **Claude (`claude-sonnet-5-5`)** writes prose and optional readings only; it
  chooses no step, rule, material, or score.
- **Web**: a standard-library Python server and a vanilla JavaScript interface (no
  HTML built from data), hosted on Render behind a review password. Keys stay
  server-side; spending is reserved before every paid call, and Claude pauses when
  its counter could not survive a restart (after deployment).

### Challenges we ran into

- Qloo describes culture, not smell: the culture-to-scent step had to be our own
  explicit design rules, honest about what they cannot decide.
- Common adjectives ("minimalist", "sophisticated") appear for most brands, so
  repetition alone is not evidence of a distinctive aesthetic.
- Related entities are relations, not proof of a shared aesthetic: directions
  drawn only from them are labelled and never lead the result.
- Verifying materials on supplier pages: one supplier's site refuses automated
  access, so ISO E SUPER stays unverified and is never used.

### Accomplishments that we're proud of

- An auditable result: every phrase opens its Qloo entity, field, request, and
  date; every material property links to the supplier's page.
- Unknowns stay unknown, and motifs without a rule stay on the page as the next
  creative decision instead of disappearing.
- A measured view of Qloo's contribution with identical rules (own entry only vs.
  with relations) on 13 brands.

### What we learned

In two pre-registered trials (six fresh brands), grounding made every claim
traceable, and Qloo's relations lifted each brand's own leading motif to the
threshold. Our translation layer is the limit: five rules and seven verified
materials make calm brands converge (MUJI and Aesop receive the same direction
and the same three materials; Le Labo gets two of those directions, both only
from related references, and the same materials), and attitude-led brands
(Supreme, Gucci, Harley-Davidson, Sanrio) get a clear profile but a thin or no
direction. A Claude-only brief was more vivid and practical on first read, and
untraceable. No human rating was made, so we claim no winner.

### What's next

Rules for the motifs MOTIF meets most often without one (provocation, heritage,
playfulness), more verified materials per dimension, fresh held-out brands, and a
perfumer's review of real briefs. A first candidate rule (provocation → raw
texture) was measured and not adopted: on the fresh brands it created conflicts,
not directions.

## Current limits (short)

- A creative direction, never a formula: nothing is smelled, balanced, dosed, or
  tested for safety, and nothing predicts who will like a scent.
- Five draft rules, seven verified materials: many brands get a partial direction.
- Directions are MOTIF's design rules, not Qloo's; related entities are relations,
  not audience overlap.
- The demo is password-protected during judging and runs on a free host (first
  load after a quiet period can take about a minute).

## Built with

`python` · `javascript` · `html5` · `css3` · `qloo-api` · `anthropic-claude` ·
`render` · Google Fonts (Archivo, Newsreader)

## Testing instructions (password placeholder)

Paste only into a field the organizers confirm is visible to judges alone.
Never put the password in the public description.

```
MOTIF is behind a reviewer password during judging.

1. Open https://motif-pxh8.onrender.com
   (free hosting: the first load after a quiet period can take about a minute).
2. Sign in with the password: [PASSWORD PLACEHOLDER]
3. Click "MUJI" (or type a brand), then "Explore a scent direction". Optionally
   pick or type an application context (for example "Flagship store").
   Research takes a few seconds and shows its real steps.
4. On the result: read the headline and MOTIF's proposed direction, then select a
   Top/Heart/Base strip for why MOTIF chose it and the supplier's own words.
   Under "Cultural profile", every phrase opens its Qloo source.
5. "Print or save as PDF" gives the one-page brief.

Try also "Le Labo" (ambiguous name: you choose the brand) and "Gucci"
(a profile led by provocation, with a partial direction from related references).
```

## Short summary in Turkish (for the owner, not for Devpost)

MOTIF, bir markanın Qloo'daki kültürel tanımlarını okuyup görünür kurallarla bir
koku yönüne, tedarikçi sayfasında doğrulanmış başlangıç malzemelerine ve tek
sayfalık bir parfümör brief'ine çevirir. Her adımın kaynağı açılabilir; kanıtın
karar vermediği boyutlar açık kalır. Kuralı olmayan motifler (provokasyon, miras,
oyunculuk) sonuçta "sıradaki yaratıcı karar" olarak görünür. Claude yalnızca
metni yazar; araştırmayı belirli kurallı bir denetleyici yönetir.

## Gallery (from real live sessions, 2026-10-07)

Private image files (they show Qloo descriptors; publishing them follows the
same data-sharing decision as the repository excerpts). Captions in English.
The images were taken before the 2026-10-08 presentation pass (section order,
no open decisions, no suggested readings); retake them from a live session once
that pass is approved and deployed.

1. **Cover** (`01-cover-start.png`): "If a brand were a scent. Type a brand; MOTIF shows how Qloo, MOTIF, and Claude each contribute."
2. **Result** (`02-result.png`): "MUJI: the headline, MOTIF's proposed direction, and three starting materials as scent strips. Temperature, projection, and sweetness stay open."
3. **Opened strip** (`03-strip-open.png`): "Why MOTIF chose bergamot, in the supplier's own verified words, kept apart from MOTIF's reading."
4. **Cultural profile** (`04-cultural-profile.png`): "Motifs ranked by evidence, the brand's own entry first; every phrase opens its Qloo source."
5. **One-page brief** (`05-brief.png`, from `05-brief.pdf`): "The printable brief: cultural profile, direction, starting roles, evidence, Claude's wording checked against the result, and clickable sources."
6. **Mobile** (`06-mobile.png`): "The same result on a phone."
7. Optional, **partial result** (`07-gucci-partial.png`): "Gucci: a profile led by provocation; MOTIF names the next creative decision instead of guessing."

## Optional demo narration (about 75 seconds; a video is not required)

"If a brand were a scent, what would it be? MOTIF answers with evidence. I type
MUJI. MOTIF asks Qloo how culture describes MUJI, and which brands and films Qloo
relates to it: four requests, shown as real steps. The result leads with the
brand's own profile: restraint, precision, and naturalness, a light,
smooth-finished, natural-feeling scent. Three starting materials appear as scent
strips: bergamot on top, HEDIONE in the heart, HABANOLIDE at the base, each with
the supplier's own words. Temperature, projection, and sweetness stay open; MOTIF
does not guess them. Every phrase opens its Qloo source. Gucci shows the other
side: its profile is led by provocation, which MOTIF cannot translate yet, so it
says so and names the next creative decision. Claude writes the brief, checked
against the result, and it prints as one page. A direction, not a formula."

## Judging criteria → product evidence

| Criterion (equal weight) | What to show |
|---|---|
| Technological implementation / Qloo use | Own entry vs. related references kept apart and labelled; A/A′/B with identical rules on 13 brands; entity choice from Qloo search; one controlled retry; evidence dialog with entity, field, request, date |
| Design | Art direction A with scent strips; headline and direction first, evidence one tap away; phone layout; one-page brief with sources |
| Potential impact | A brief a brand team can hand to a perfumer: direction, roles, supplier words, evidence, honest limits |
| Quality of the idea | Culture → motif → sensory direction → verified material, with unknowns and untranslated motifs kept visible |

## Current demo variant (only if the branch is not deployed)

The deployed stage 5 interface has no scent strips, no printable brief page, no
cultural profile headline, no application context field, and no
retry; its start page reads "A scent direction, read from culture." Then:

- remove the gallery images (they show the new interface) and the "Opened strip"
  and "One-page brief" sentences;
- testing steps: "Sign in, click MUJI or type a brand, follow the research steps,
  then read the scent direction, the starting materials, and the perfumer brief;
  open any phrase for its Qloo source. 'Download brief (JSON)' gives the full
  trail."

## Before the deadline (suggested check on October 27–28; nothing is scheduled)

- Deadline: October 30, 2026, 11:45 pm EDT = October 31, 06:45 Türkiye. Judging:
  November 2–16 (US Eastern); keep the demo working until at least November 17.
- Re-read the official rules; confirm with the organizers (Discord
  `#qloo-hackathon`) whether a password-protected demo is accepted and where
  judges see testing instructions.
- Check Render: service live, `/healthz` OK, `main` deployed, environment
  variables present (names only: `QLOO_API_KEY`, `MOTIF_ANTHROPIC_API_KEY`,
  `MOTIF_ACCESS_PROTECTION`, `MOTIF_ACCESS_PASSWORD`, `MOTIF_LLM_MAX_CALLS`,
  `MOTIF_LLM_BUDGET_GUARD`, `MOTIF_QLOO_MAX_CALLS_PER_DAY`,
  `MOTIF_WEB_SESSIONS_PER_DAY`, `MOTIF_WEB_SESSIONS_PER_IP_HOUR`).
- Budgets for the judging weeks: decide between the options in
  `docs/STAGE_6A_DECISIONS.md` §0.4 so a judge can always complete MUJI (about four
  Qloo requests and one Claude call).
- Repository: public, MIT license present, README setup steps work from a clean
  clone. The MIT license covers the code, not Qloo data; recorded Qloo data stays
  out of the public demo.

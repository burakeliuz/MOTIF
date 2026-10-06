# Devpost submission texts (copy-ready drafts)

Drafts for the owner to paste into Devpost. Nothing here has been submitted or
edited on Devpost by the build agent. Every claim below is based on the
implemented product and the reports in this repository; adjust wording freely,
but keep the limits.

- **Project name:** MOTIF
- **Tagline (max ~200 characters):** If a brand were a scent: MOTIF reads a brand's cultural footprint in Qloo and turns it, rule by rule, into a scent direction and a perfumer brief you can trace.
- **Demo URL:** https://motif-pxh8.onrender.com
- **Repository:** https://github.com/burakeliuz/MOTIF (MIT license for the code)

## About the project

### Inspiration

Brand and creative teams often brief perfumers with mood boards and adjectives.
We wanted to ask a sharper question: if this brand were a scent, what would it
smell like, and can every step from culture to scent be shown and checked?
(The brief-writing need is our assumption; no customer or perfumer has
validated it yet.)

### What it does

You type a brand (and, optionally, one line of creative intent, such as "a
signature scent for the flagship stores"). MOTIF then:

1. finds the brand in **Qloo** (asking you when the name is ambiguous, for
   example "Le Labo" returns two shops and the brand "Le Labo Fragrances");
2. reads the descriptors Qloo attaches to the brand itself, and to the brands and
   films Qloo relates to it;
3. groups repeated descriptors into motifs (restraint, precision, naturalness…)
   and translates them with versioned, visible rules into directions on six
   sensory dimensions; a dimension the evidence does not decide stays open, never
   a midpoint;
4. proposes starting materials (top, heart, base) whose properties were checked
   on the supplier's own pages, drawn as scent strips;
5. writes a brief (with Claude, checked against the result, or with a fixed
   template), printable as one A4 page.

Every direction says where it comes from: the brand's own descriptors, the same
motif in references Qloo relates to the brand, or only those references (then it
is labelled a creative suggestion). Motifs MOTIF cannot translate yet, such as
Comme des Garçons' experimentation, stay visible as open design questions. On
request, Claude can suggest readings for descriptors MOTIF's lexicon does not
read; they are never applied unless you accept them, and even then they are your
notes, not evidence.

### How we built it

- **Qloo Hackathon API:** `/search`, `/entities`, and `/v2/insights` (related
  brands and films for one brand), at most four requests per brand, cached per
  brand so answering a question or changing the intent repeats nothing.
- **A deterministic engine** in Python (standard library only): lexicon
  (lexicon-0.3), draft translation rules (draft-0.2), and a verified material
  palette (palette-0.3: seven of eight materials checked on Givaudan and
  dsm-firmenich pages, with the supplier's words kept apart from MOTIF's
  reading). The same evidence and versions always give the same result.
- **A research controller** (a state machine, not an LLM) decides each step and
  skips a related domain only when it provably cannot change the result.
- **Claude (`claude-sonnet-5-5`)** writes only prose and optional readings; its
  output is validated (no new materials, numbers, or preference claims) and
  falls back to a labelled template.
- **Web:** a Python standard-library server and a vanilla JavaScript interface
  (no HTML built from data), hosted on Render; keys stay server-side; budget
  counters reserve before every paid call and fail closed.

### Challenges we ran into

- Qloo describes culture, not smell: the cultural-to-scent step had to be our
  own explicit, versioned design rules, honest about what they cannot decide.
- Common adjectives ("minimalist", "sophisticated") appear for most brands, so
  repetition alone is not evidence of a distinctive aesthetic.
- Related entities are relations, not proof of a shared aesthetic; we label
  directions that come only from them.
- One supplier site blocked automated access, so ISO E SUPER stays unverified
  and is never used.

### Accomplishments that we're proud of

- A result you can audit: every phrase opens its Qloo entity, field, request,
  and date; every material property links to the supplier's page.
- Unknowns stay unknown, and motifs without a rule stay on the page.
- A measured view of Qloo's contribution with identical rules (own entry only vs.
  with relations), kept honest about the threshold effect.

### What we learned

In a pre-registered two-brand trial, grounding made every claim traceable, but
our five rules and seven verified materials are too narrow: MUJI, Le Labo, and
Aesop receive the same direction, and attitude-led brands (Supreme) get a thin
result. An LLM-only brief was more vivid and practical on first read, and
untraceable. No human rating was made, so we claim no winner.

### What's next

A small rule package (for example provocation → raw texture), one more verified
material, fresh held-out brands, and a perfumer's review of real briefs.

## Built with

`python` · `javascript` · `html5` · `css3` · `qloo-api` · `anthropic-claude` ·
`render` · Google Fonts (Archivo, Newsreader)

## Testing instructions (draft, password placeholder)

Paste only into a field the organizers confirm is visible to judges alone.
Never put the password in the public description.

```
MOTIF is behind a reviewer password during judging.

1. Open https://motif-pxh8.onrender.com
   (free hosting: the first load after a quiet period can take about a minute).
2. Sign in with the password: [PASSWORD PLACEHOLDER]
3. Click "MUJI" (or type a brand). Optionally add a one-line creative intent.
   Research takes a few seconds and shows its real steps.
4. On the result: read the scent idea, then select a Top/Heart/Base strip to
   see its role and the supplier's own words. Open "How it was made" for the
   evidence; every phrase opens its source.
5. "Print or save as PDF" gives the one-page brief.
6. Optional: under "Notes", "Suggest interpretations" makes one Claude call and
   offers readings you can accept or reject; they never change the result.

Try also "Le Labo" (ambiguous name: you choose the brand) and
"Comme des Garçons" (a partial result with open design questions).
```

## Gallery (from the final screens)

Private image files (they show Qloo descriptors; publishing them follows the
same data-sharing decision as the repository excerpts): 
`data/design_preview/stage6b/`.

1. Start screen, "If a brand / were a / scent." (`start-desktop.png`)
2. Result idea and character for a brand (`aesop-desktop-top.png`)
3. Starting materials as scent strips with one opened (`muji-recorded-desktop-full.png`, section 01)
4. Partial result with an open design question (`cdg-recorded-desktop-full.png`, `supreme-desktop-top.png`)
5. Mobile result (`aesop-mobile-top.png`)
6. One-page brief PDF (`aesop-brief.pdf`, page 1)

Cover suggestion: the start screen (no brand data on it).

## Optional demo narration (about 75 seconds; a video is not required)

"If a brand were a scent, what would it smell like? MOTIF answers with evidence.
I type MUJI. MOTIF asks Qloo how culture describes MUJI, and which brands and
films Qloo relates to it: four requests, shown as real steps. The result leads
with an idea: a light, smooth-finished, natural-feeling scent, built on
restraint, precision, and naturalness. Below are three starting materials as
scent strips: bergamot on top, HEDIONE in the heart, HABANOLIDE at the base,
each with the supplier's own words. Temperature, projection, and sweetness stay
open; MOTIF does not guess them. Every direction says where it comes from, and
every phrase opens its Qloo source. Comme des Garçons shows the other side:
experimentation is clearly there, but MOTIF has no rule for it, so it stays an
open question for the perfumer. The brief prints as one page. A direction, not
a formula."

## Judging criteria → product evidence

| Criterion (equal weight) | What to show |
|---|---|
| Technological implementation / Qloo use | Per-direction basis (own descriptors vs. references Qloo relates to the brand); A/A′/B with identical rules; entity choice from Qloo search; evidence dialog with entity, field, request, date |
| Design | Art direction A with scent strips; idea first, evidence one tap away; mobile layout of its own; one-page brief |
| Potential impact | A brief a brand team can hand to a perfumer: roles, supplier words, open decisions; honest limits |
| Quality of the idea | Culture → motif → sensory direction → verified material, with unknowns and untranslated motifs kept visible |

## Before the deadline (suggested check on October 27–28; nothing is scheduled)

- Deadline: October 30, 2026, 11:45 pm EDT = October 31, 06:45 Türkiye. Judging:
  November 2–16 (US Eastern); keep the demo working until at least November 17.
- Re-read the official rules in full; confirm with the organizers (Discord
  `#qloo-hackathon`) whether a password-protected demo is accepted and where
  judges see testing instructions.
- Check Render: service live, `/healthz` OK, `main` deployed, environment
  variables present (names only: `QLOO_API_KEY`, `MOTIF_ANTHROPIC_API_KEY`,
  `MOTIF_ACCESS_PROTECTION`, `MOTIF_ACCESS_PASSWORD`, `MOTIF_LLM_MAX_CALLS`,
  `MOTIF_QLOO_MAX_CALLS_PER_DAY`, `MOTIF_WEB_SESSIONS_PER_DAY`,
  `MOTIF_WEB_SESSIONS_PER_IP_HOUR`).
- Budgets for the judging weeks: set an Anthropic workspace spend limit in the
  Anthropic Console; consider `MOTIF_LLM_MAX_CALLS` and the Qloo daily cap so a
  judge can always complete MUJI (about 4 Qloo requests and 1 Claude call).
- Repository: public, MIT license present, README setup steps work from a
  clean clone. The MIT license covers the code, not Qloo data; recorded Qloo
  data stays out of the public demo.

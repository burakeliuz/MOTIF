# Devpost submission texts (copy-ready drafts)

Drafts for the owner to paste into Devpost. The project is already submitted;
nothing here has been entered or changed on Devpost by the build agent. Every
claim below matches the implemented product and the reports in this repository
(`docs/VALIDATION.md`, `reports/final_validation.md`, `reports/trial_6b.md`).

**Status of these texts: draft for after deployment.** They describe the
continuous engine and the redesigned brief (engine refactor of 2026-10-07).
They become true for judges only after this version is on `main` and the owner
redeploys Render. If the hosted demo still runs an earlier version, use the
"Earlier demo variant" at the end instead of the testing steps and gallery.

Basic fields:

- **Project name:** MOTIF
- **Tagline (≈ 200 characters):** If a brand were a scent: MOTIF reads how culture describes a brand in Qloo and translates it, step by traceable step, into a scent direction, a scent architecture, and a one-page perfumer brief.
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

You type a brand and, optionally, an application context ("a signature scent
for the flagship stores"). MOTIF then shows, step by step:

1. **Qloo, the cultural evidence.** MOTIF finds the brand in Qloo (and asks you
   when a name is ambiguous: "Le Labo" returns shops and the brand "Le Labo
   Fragrances"). It reads the descriptors Qloo attaches to the brand itself and
   to the brands and films Qloo relates to it.
2. **MOTIF, the translation.** Descriptors become weighted motifs (restraint,
   precision, provocation …), the brand's own entry weighing most. A versioned
   model translates the motifs into six continuous sensory dimensions
   (temperature, weight, texture, impression, projection, sweetness); a
   dimension the evidence does not decide stays "open to the perfumer", and a
   leaning that rests only on MOTIF's design reading is labelled tentative. The
   dimensions select a scent architecture (opening, core, drydown) from 23
   accord-type directions, with what to emphasize and avoid when the evidence
   supports it. Material references are examples of each direction's class,
   named as in the IFRA ingredient glossary, with a trade name only where we
   read the supplier's page.
3. **Claude, the brief.** Claude writes the brief in plain words from the
   finished result; MOTIF checks it (no ingredient outside the architecture, no
   numbers, no audience claims, every open dimension named) and falls back to a
   labelled template otherwise. The application context frames the brief; it
   does not change the evidence or the direction. The brief prints as one A4 page
   with its sources, and every step is shown: Qloo → motif → scent.

Examples (stored live Qloo responses of 2026-10-06/07, current engine):

- **MUJI**: "Restraint, precision and naturalness: a light, natural-feeling and
  slightly smooth-finished direction." Opening aromatic herbs, core transparent
  floral, drydown earthy and mossy. Projection stays open to the perfumer.
- **Gucci**: "Provocation: a slightly diffusive direction." Qloo's related brands
  and films add dense weight and a smooth finish, and the page says they come
  from those references. Core rich white floral, drydown resinous amber; the
  opening stays open.
- **Harley-Davidson**: "Heritage and provocation: a slightly dense and slightly
  dry direction", labelled tentative: every leaning rests on MOTIF's design
  reading, and the page says so. Fresh spice, smoke and incense, leather.

### How we built it

- **Qloo Hackathon API**: `/search`, `/entities` (the brand's own entry), and
  `/v2/insights` for related brands and films; at most four requests per brand,
  cached per brand so choosing an entity, changing the context, refreshing, or
  printing repeats nothing.
- **A research controller** (a deterministic state machine, not an LLM) resolves
  the entity or asks you to choose, fetches the own entry, related brands, and
  related films within a budget, stops on a failed request with what it has, and
  offers one controlled retry.
- **The engine** (Python standard library), every part versioned: a lexicon of
  twelve motifs; saturating motif scores; a motif-to-sensory model built from
  open odor-descriptor datasets (Dravnieks, Keller & Vosshall, Leffingwell, the
  IFRA glossary, via Pyrfume) and labelled design readings; continuous
  aggregation that keeps every contributor; a 23-direction olfactory library.
  The same evidence and versions always give the same result.
- **Claude (`claude-sonnet-5-5`)** writes prose only; it chooses no motif,
  dimension, direction, or material.
- **Web**: a standard-library Python server and a vanilla JavaScript interface (no
  HTML built from data), hosted on Render behind a review password. Keys stay
  server-side; spending is reserved before every paid call.

### Challenges we ran into

- Qloo describes culture, not smell: the culture-to-scent step is our own model,
  and it has to say what it cannot decide.
- Our first engine (five yes/no rules, seven materials) gave 13 brands only 3
  distinct material sets. We rebuilt it as a continuous model and kept the old
  engine as a measured baseline.
- Sensory claims need support: where open odor data exists (warm/cool,
  light/heavy, sweet/dry ratings of odor families) the model cites it; elsewhere
  a cell is a labelled design reading, and three motifs carry no claim at all.
- Related entities are relations, not proof of a shared aesthetic: directions
  drawn only from them are labelled and never lead the result.

### Accomplishments that we're proud of

- An auditable result: every Qloo phrase opens its entity, field, request, and
  date; every dimension shows the motifs and phrases behind it.
- Less collapse, measured: on 13 trial brands, 11 distinct scent architectures
  instead of 3 material sets, deterministic and stable when one descriptor is
  left out (the architecture changes in 4% of 523 such runs).
- Unknowns stay unknown, and tentative leanings say so.

### What we learned

On five pre-registered brands MOTIF had never seen, it resolved four (Qloo's
search returned only IKEA stores) with no structural failure, and misread 8% of
the descriptors it relied on ("industrial design" read as an industrial look).
About a third of the differences between architectures come from MOTIF's
tentative design readings rather than data, and brands whose descriptors fall
outside our lexicon (LEGO, Coca-Cola) get thin, similar results. A Claude-only
brief commits to almost every dimension and agrees with our grounded engine on
most poles where both commit, but nothing in it can be traced. No perfumer has
rated the briefs, so we claim no winner.

### What's next

A perfumer's review of real briefs; wider lexicon coverage; context rules for
the misreads; typed entity search; fresh held-out brands for every model change.

## Current limits (short)

- A creative direction, never a formula: nothing is smelled, balanced, dosed, or
  tested for safety, and nothing predicts who will like a scent.
- Much of the culture-to-scent model is design reading, labelled tentative; only
  some relations rest on open odor data.
- Related entities are relations, not audience overlap.
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
4. On the result: the headline, the cultural profile (every phrase opens its
   Qloo source), the olfactory direction, the scent architecture (opening,
   core, drydown), and "Why": which Qloo phrases led to which motif and
   dimension.
5. "Download brief (PDF)" saves the one-page brief as a PDF file.

Try also "Le Labo" (ambiguous name: you choose the brand) and
"Harley-Davidson" (a tentative direction, labelled as such).
```

## Short summary in Turkish (for the owner, not for Devpost)

MOTIF, bir markanın Qloo'daki kültürel tanımlarını okur; bunları ağırlıklı
motiflere, altı sürekli duyusal boyuta ve açılış, kalp ve dip notalarından
oluşan bir koku mimarisine çevirir; sonunda tek sayfalık bir parfümör brief'i
verir. Her adımın kaynağı açılabilir. Kanıtın karar vermediği boyutlar
"parfümöre açık" kalır. Yalnızca MOTIF'in tasarım okumasına dayanan eğilimler
"tentative" diye işaretlenir. Claude yalnızca metni yazar; araştırmayı belirli
kurallarla çalışan bir denetleyici yönetir.

## Gallery

Retake the images from a live session after this version is deployed (the
previous gallery shows the earlier interface). Private image files: they show
Qloo descriptors, so publishing them follows the same data-sharing decision as
the repository excerpts. Suggested shots and captions:

1. **Cover**: "If a brand were a scent. Type a brand; MOTIF shows how Qloo, MOTIF, and Claude each contribute."
2. **Result**: "MUJI: the headline, the cultural profile, and the olfactory direction; projection stays open to the perfumer."
3. **Scent architecture**: "Opening, core, drydown, each with the dimensions it fits and material references from the IFRA glossary."
4. **Why**: "Qloo phrase → motif → dimension, for every resolved dimension."
5. **One-page brief**: "The printable brief with its sources."
6. **Mobile**: "The same result on a phone."
7. Optional, **tentative result**: "Harley-Davidson: every leaning is MOTIF's design reading, and the page says so."

## Optional demo narration (about 75 seconds; a video is not required)

"If a brand were a scent, what would it be? MOTIF answers with evidence. I type
MUJI. MOTIF asks Qloo how culture describes MUJI, and which brands and films Qloo
relates to it: four requests, shown as real steps. The cultural profile leads
with MUJI's own motifs: restraint, precision, naturalness. MOTIF translates them
into a light, natural-feeling, slightly smooth-finished direction; projection
stays open, because the evidence does not decide it. The scent architecture
follows: aromatic herbs to open, a transparent floral core, an earthy, mossy
drydown. 'Why' shows each step from a Qloo phrase to a motif to a dimension.
Harley-Davidson shows the other side: its leanings rest on MOTIF's design
reading, and the page labels them tentative. Claude writes the brief, checked
against the result, and it prints as one page. A direction, not a formula."

## Judging criteria → product evidence

| Criterion (equal weight) | What to show |
|---|---|
| Technological implementation / Qloo use | Own entry vs. related references weighed and labelled separately; deterministic, versioned engine; legacy vs continuous measured on 13 brands and a pre-registered holdout; entity choice from Qloo search; one controlled retry |
| Design | Headline and direction first, evidence one tap away; scent architecture drawn as strips; phone layout; one-page brief |
| Potential impact | A brief a brand team can hand to a perfumer: direction, structure, what to emphasize and avoid, evidence, honest limits |
| Quality of the idea | Culture → motif → sensory dimension → scent architecture, with unknowns open and tentative leanings labelled |

## Earlier demo variant (only if this version is not deployed)

If Render still runs the earlier rule-engine interface, describe it instead:
the result shows the cultural profile, MOTIF's proposed direction from five
draft rules, and Top/Heart/Base starting materials drawn as scent strips (only
materials verified on the supplier's page), with the printable brief. Remove
the "Scent architecture" and "Why" gallery shots and testing step 4's wording
about them.

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

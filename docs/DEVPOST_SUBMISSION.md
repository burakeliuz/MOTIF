# Devpost submission (final, copy-ready)

Texts and images for the owner to paste and upload on Devpost. The project is
already submitted; nothing here has been entered or changed on Devpost by the
build agent. Every claim matches the product on `main` and the screens in
`docs/devpost/` (MUJI, real MOTIF output; capture note under "Image gallery").

## Basic fields

- **Project name:** MOTIF
- **Tagline (elevator pitch):** If a brand were a scent: MOTIF reads a brand's cultural evidence in Qloo and turns it into a traceable scent direction and a one-page brief for a perfumer.
- **Demo:** https://motif-pxh8.onrender.com
- **Repository:** https://github.com/burakeliuz/MOTIF

## About the project

*(Not part of the text: copy from "### Inspiration" down to the italic line about brands. Each paragraph is one line, so it pastes without stray line breaks; 486 words without the headings.)*

### Inspiration

If a brand were a scent, what would it be? Creative teams shaping a scent idea for a brand's stores, launch or first fragrance usually start from mood boards and adjectives; the perfumer who receives the brief rarely learns why a direction fits. MOTIF is for both: type a brand and get a reasoned scent direction, a scent idea in three parts (opening, core, drydown) and a one-page PDF brief whose every step traces back to its source.

### What it does

Take MUJI. Type the name and, optionally, what the scent is for ("a signature scent for the flagship stores"). MOTIF finds MUJI in Qloo, reads its own entry and the brands and films Qloo relates to it, and shows each research step as it runs. MUJI's own descriptors ("Unpretentious", "Clean Lines", "Natural Materials") and those references ("Muted" on the film Still Walking, "Earthy Color Palette" on the brand studio CLIP) support three motifs: restraint, precision and naturalness. MOTIF reads them as a light, natural-feeling, slightly smooth-finished direction and proposes a scent idea: aromatic herbs to open, a transparent floral core, an earthy, mossy drydown.

Each phrase opens its source: "Natural Materials" comes from MUJI itself; "Earthy Color Palette" is labelled as a reference Qloo relates to MUJI, not proof of a shared aesthetic. Both read as naturalness, which makes the impression natural-feeling, and the opening and drydown are chosen to fit it. Projection stays open to the perfumer: nothing in the evidence decides it. One click saves the PDF brief.

### How we built it

A deterministic research controller, not an LLM, makes four Qloo calls per brand (`/search`, `/entities`, and `/v2/insights` for related brands and films), asks you to choose when a name is ambiguous, and stops on a failed request instead of falling back. MOTIF's versioned engine, in plain Python, weighs descriptors into motifs (the brand's own entry counts most), maps motifs to six sensory dimensions with a model partly built on open odor-descriptor data, and picks the best-fitting opening, core and drydown from 23 accord types. Claude, when switched on, only writes the brief's prose, checked against the result; otherwise MOTIF's template writes it.

### Challenges we ran into

Qloo describes culture, not smell, so the culture-to-scent step had to be ours, and honest about what it cannot decide. Our first rule engine gave 13 brands only three distinct results, so we rebuilt it as a continuous model.

### Accomplishments that we're proud of

Every claim is traceable: a Qloo phrase opens its source entity and fetch date, and every dimension names the motifs behind it.

### What we learned

Related references are evidence, not proof, so MOTIF labels them and never lets them lead the headline. A useful brief also says what the data leaves open. MOTIF offers a creative starting brief, not a formula: nothing is smelled, dosed or predicted to please anyone.

### What's next for MOTIF

A perfumer's review of real briefs, a wider vocabulary, and fresh test brands for every model change.

*Brands appear as examples run on Qloo data; none is affiliated with MOTIF.*

## Built with

`python` · `javascript` · `html5` · `css3` · `qloo` · `claude` · `anthropic` ·
`fpdf2` · `render` · `playwright` · `google-fonts` · `pyrfume`

(Qloo hackathon API; Claude `claude-sonnet-5-5`, optional, prose only; fpdf2
for the PDF; Render free web service; Playwright and Chromium for browser
tests; Archivo and Newsreader fonts; open odor-descriptor data read through
Pyrfume for the sensory model.)

## Try it out

- Demo: https://motif-pxh8.onrender.com
- Code: https://github.com/burakeliuz/MOTIF

## Testing instructions for judges

Paste into the judges-only field. Write the password there only, never in the
public description.

```
1. Open https://motif-pxh8.onrender.com (free hosting: the first load after a
   quiet period can take about a minute).
2. If a sign-in page appears, use the password: [PASSWORD, judges-only field]
3. Click "MUJI" under the brand field (or type any brand), optionally pick
   "Flagship store", then "Explore a scent direction". The research steps run
   for a few seconds.
4. Read the title and the scent idea, then click a Qloo phrase such as
   "Natural Materials" to see where it comes from.
5. Scroll to "Why: Qloo → motif → scent" and click "Download brief (PDF)".
6. Also try "Le Labo" (Qloo may ask which entity you mean) or a brand of your
   own. If the brief shows no Claude badge, its prose came from MOTIF's
   template: Claude is optional and paused on the free host.
```

## Image gallery (upload in this order)

All images are 1500 × 1000 PNG, under 0.4 MB each, in `docs/devpost/`.

| File | Title on the image | Devpost caption |
|---|---|---|
| `00-cover-1500x1000.png` (thumbnail) | If a brand were a scent. | MOTIF: from a brand's cultural evidence in Qloo to a scent idea. The strips are MUJI's proposed opening, core and drydown. |
| `01-brand-to-direction.png` | From a brand name to a scent direction | Type a brand and, optionally, what the scent is for. MOTIF finds it in Qloo, reads its own entry and the brands and films Qloo relates to it, and shows each real research step before the result. |
| `02-scent-idea.png` | MUJI as a scent: opening, core, drydown | MUJI reads as restraint, precision and naturalness: a light, natural-feeling, slightly smooth-finished direction. The scent idea and its opening, core and drydown are MOTIF's creative proposal, labelled as such; nothing has been smelled. |
| `03-qloo-to-scent.png` | From a Qloo phrase to a scent decision | "Natural Materials" comes from MUJI's own Qloo entry; "Earthy Color Palette" from studio CLIP, a brand Qloo relates to MUJI. MOTIF reads both as naturalness, which makes the impression natural-feeling; the opening and drydown are chosen to fit it. Qloo supplies the evidence; MOTIF translates. |
| `04-pdf-brief.png` | A one-page brief to hand to a perfumer | One click saves a real one-page PDF: the direction, the scent architecture with material references, what to emphasize and avoid, why, and the Qloo sources. A creative starting brief, not a formula. |

Sample PDF: `docs/devpost/MOTIF-Muji-Brief.pdf` (the file the download button
saved). Everything is also in `docs/devpost/MOTIF-Devpost-Package.zip`.

**Capture note.** All screens are real MOTIF output for MUJI, captured on 7
October 2026 from a local run of the code on `main` (commit 4975a42) with live
Qloo data (four requests); the hosted demo itself is not reachable from the
build environment. Claude was not called, so the brief text in the PDF comes
from MOTIF's template. The images add titles, numbers, arrows, frames and a
fade at the cut edge of the phone screens; no result was edited.

## Judging criteria → where MOTIF shows it

| Criterion | Feature or example |
|---|---|
| Technological Implementation | Four Qloo calls per brand (`/search`, `/entities`, `/v2/insights` for related brands and films); the brand's own entry and its references weighed and labelled separately; a deterministic controller with entity choice, a request budget and no fallback; a versioned, tested engine; every phrase opens its Qloo source (image 3). |
| Design | Scent idea first, evidence one click away; scent strips for opening, core and drydown; labels that separate Qloo evidence, MOTIF's translation and MOTIF's creative proposal; phone layout (image 1); one-page PDF (image 4). |
| Potential Impact | A creative team goes from a brand name to a reasoned direction and a brief it can hand to a perfumer: MUJI from name to PDF (images 1 to 4). |
| Quality of the Idea | Qloo's cultural descriptors used as evidence for a sensory translation (culture → motif → dimension → accords), with unknowns left open and references never treated as proof (image 3). |

## Current limits (short)

- A creative direction, never a formula: nothing is smelled, balanced, dosed or
  tested for safety, and nothing predicts who will like a scent.
- Much of the culture-to-scent model is MOTIF's design reading, labelled
  tentative; only some relations rest on open odor data.
- Related brands and films are references Qloo relates to a brand, not proof of
  a shared aesthetic or audience.
- Free hosting: the first load after a quiet period can take about a minute.

## Before the deadline (owner checklist)

- Deadline: October 30, 2026, 11:45 pm EDT (October 31, 06:45 Türkiye). Judging:
  November 2–16 (US Eastern); keep the demo working until at least November 17.
- Judge access: the demo is behind the review password. Before judging, either
  give judges the password in a field the organizers confirm is judges-only, or
  open the demo (`MOTIF_ACCESS_PROTECTION=off` on Render).
- Claude on the free host stays paused unless the provider-side spending cap of
  `docs/STAGE_6A_DECISIONS.md` §0.4 is set; the demo works either way.
- Check Render on October 27–28: service live, `/healthz` OK, latest `main`
  deployed.
- The demo video is planned for a separate session.

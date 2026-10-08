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

*(Not part of the text: copy from "### Inspiration" down to the italic line about brands. Each paragraph is one line, so it pastes without stray line breaks; 498 words without the headings.)*

### Inspiration

If a brand were a scent, what would it be? Brand and creative teams developing a scent for stores, a launch or a first fragrance often start from mood boards and adjectives, and the perfumer gets a brief that says what to make but not why. MOTIF gives both sides a shared starting point: type a brand and, in a few seconds, get a reasoned scent direction, a scent idea (opening, core, drydown) and a one-page brief showing where every choice comes from.

### What it does

Take MUJI. Type the name and, optionally, what the scent is for ("a signature scent for the flagship stores"). MOTIF finds MUJI in Qloo, reads its own entry and the brands and films Qloo relates to it, and shows each research step as it runs.

Qloo returns MUJI's own descriptors ("Unpretentious", "Clean Lines", "Natural Materials") and those of related references ("Muted" on the film Still Walking, "Earthy Color Palette" on the brand studio CLIP). MOTIF turns them into three motifs: restraint, precision and naturalness. Naturalness rests on MUJI's own "Natural Materials" and the earthy palettes of related brands; it makes the scent natural-feeling, so MOTIF opens with aromatic herbs and dries down earthy and mossy. Restraint makes it light and precision smooth, which suits the transparent floral core. What the evidence does not decide, such as projection, is left to the perfumer.

One click saves a one-page PDF brief (the direction, the scent architecture with material references, what to emphasize and avoid, and why): a creative starting brief for the perfumer to develop.

### How we built it

A deterministic research controller makes four Qloo calls per brand (`/search`, `/entities`, and `/v2/insights` for related brands and films), asks you to choose when a name is ambiguous, and stops cleanly if a request fails. MOTIF's versioned Python engine weighs descriptors into motifs (the brand's own entry counts most), maps motifs to six sensory dimensions with a model partly built on open odor data, and picks the best-fitting opening, core and drydown from 23 accord types. Claude (`claude-sonnet-5-5`) writes the brief's prose from the finished result; MOTIF checks it before showing it. Claude narrates; MOTIF decides.

### Challenges we ran into

Qloo describes culture, not smell, so the bridge from culture to scent had to be ours, and had to know when to stay silent. Our first rule engine gave 13 brands only three distinct results, so we rebuilt it as a continuous model.

### Accomplishments that we're proud of

A brief you can audit: every Qloo phrase opens its source entity and fetch date, and every dimension names its motifs. The brand's own words lead; references add weight, labelled as references.

### What we learned

Qloo's strongest contribution is context. A brand's own descriptors and the brands and films Qloo relates to it give MOTIF far more than a name, and keeping those sources visible makes a brief easier to trust and discuss with a perfumer.

### What's next for MOTIF

Reviews of real briefs with perfumers, a wider vocabulary, and new test brands for every model change.

*Brands appear as examples run on Qloo data; none is affiliated with MOTIF.*

## Built with

`python` · `javascript` · `html5` · `css3` · `qloo` · `claude` · `anthropic` ·
`fpdf2` · `render` · `playwright` · `google-fonts` · `pyrfume`

(Qloo hackathon API; Claude `claude-sonnet-5-5` for the brief's prose; fpdf2
for the PDF; Render free web service; Playwright and Chromium for browser
tests; Archivo and Newsreader fonts; open odor-descriptor data read through
Pyrfume for the sensory model.)

## Try it out

- Demo: https://motif-pxh8.onrender.com
- Code: https://github.com/burakeliuz/MOTIF

## Testing instructions for judges

Copy-ready steps; judges start directly at the demo address.

```
1. Open https://motif-pxh8.onrender.com (free hosting: the first load after a
   quiet period can take about a minute).
2. Click "MUJI" under the brand field (or type any brand), optionally pick
   "Flagship store", then "Explore a scent direction". The research steps run
   for a few seconds.
3. Read the title and the scent idea, then click a Qloo phrase such as
   "Natural Materials" to see where it comes from.
4. Scroll to "Why: Qloo → motif → scent" and click "Download brief (PDF)".
5. Also try "Le Labo" (Qloo may ask which entity you mean) or a brand of your
   own.
```

## Image gallery (upload in this order)

All images are 1500 × 1000 PNG, under 0.4 MB each, in `docs/devpost/`.

| File | Title on the image | Devpost caption |
|---|---|---|
| `00-cover-1500x1000.png` (thumbnail) | If a brand were a scent. | MOTIF: from a brand's cultural evidence in Qloo to a scent idea. The strips are MUJI's proposed opening, core and drydown. |
| `01-brand-to-direction.png` | From a brand name to a scent direction | Type a brand and, optionally, what the scent is for. MOTIF finds it in Qloo, reads its own entry and the brands and films Qloo relates to it, and shows each real research step before the result. |
| `02-scent-idea.png` | MUJI as a scent: opening, core, drydown | MUJI reads as restraint, precision and naturalness: a light, natural-feeling, slightly smooth-finished direction. The scent idea and its opening, core and drydown are MOTIF's creative proposal, built from that direction. |
| `03-qloo-to-scent.png` | From a Qloo phrase to a scent decision | "Natural Materials" comes from MUJI's own Qloo entry; "Earthy Color Palette" from studio CLIP, a brand Qloo relates to MUJI. MOTIF reads both as naturalness, which makes the impression natural-feeling; the opening and drydown are chosen to fit it. Qloo supplies the evidence; MOTIF translates. |
| `04-pdf-brief.png` | A one-page brief to hand to a perfumer | One click saves a one-page PDF: the direction, the scent architecture with material references, what to emphasize and avoid, why, and the Qloo sources. |

Sample PDF: `docs/devpost/MOTIF-Muji-Brief.pdf` (the file the download button
saved). Everything is also in `docs/devpost/MOTIF-Devpost-Package.zip`.

**Capture note.** All screens are real MOTIF output for MUJI, captured on 7
October 2026 from a local run of the code on `main` (commit 4975a42) with live
Qloo data (four requests); the hosted demo itself is not reachable from the
build environment. Claude was not called in this local capture, so the brief
text in the sample PDF comes from MOTIF's template; on the live site Claude
writes it. The images add titles, numbers, arrows, frames and a fade at the cut
edge of the phone screens; no result was edited.

## Judging criteria → where MOTIF shows it

| Criterion | Feature or example |
|---|---|
| Technological Implementation | Four Qloo calls per brand (`/search`, `/entities`, `/v2/insights` for related brands and films); the brand's own entry and its references weighed and labelled separately; a deterministic controller with entity choice, a request budget and no fallback; a versioned, tested engine; every phrase opens its Qloo source (image 3). |
| Design | Scent idea first, evidence one click away; scent strips for opening, core and drydown; labels that separate Qloo evidence, MOTIF's translation and MOTIF's creative proposal; phone layout (image 1); one-page PDF (image 4). |
| Potential Impact | A creative team goes from a brand name to a reasoned direction and a brief it can hand to a perfumer: MUJI from name to PDF (images 1 to 4). |
| Quality of the Idea | Qloo's cultural descriptors used as evidence for a sensory translation (culture → motif → dimension → accords), with the brand's own words and its references kept apart and unknowns left open (image 3). |

## Current limits (short)

- Much of the culture-to-scent model is MOTIF's design reading, labelled
  tentative; only some relations rest on open odor data.
- Free hosting: the first load after a quiet period can take about a minute.

## Before the deadline (owner checklist)

- Deadline: October 30, 2026, 11:45 pm EDT (October 31, 06:45 Türkiye). Judging:
  November 2–16 (US Eastern); keep the demo working until at least November 17.
- Judge access: the review password stays on for now. Remove it before judging
  starts (`MOTIF_ACCESS_PROTECTION=off` on Render), then open the demo URL in a
  private window to confirm it loads without a sign-in page.
- Check Render on October 27–28: service live, `/healthz` OK, latest `main`
  deployed, and a fresh brief shows the Claude badge.
- The demo video is planned for a separate session.

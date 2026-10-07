/* MOTIF browser client: a thin renderer of the server's session view (art direction A).
 *
 * Every value comes from the server; this file only lays it out. It never builds HTML
 * from data, never invents progress, and only starts work when the person asks: a new
 * search, an answer to a question, or a request for interpretation suggestions.
 * Re-rendering, back/forward, and reload read the existing session with GET.
 */
"use strict";

const view = document.getElementById("view");
const announce = document.getElementById("announce");
const dialog = document.getElementById("evidence");
const dialogBody = document.getElementById("evidence-body");
let config = null;
let pollTimer = null;
let pollFailures = 0;
let posting = false;
let shown = { id: null, mode: null };

// ---------- helpers ----------

function h(tag, attrs, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    node.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return node;
}
const swap = (...nodes) => view.replaceChildren(...nodes);
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const src = (who) => h("span", { class: "src " + who.toLowerCase(), text: who });
function say(text) { announce.textContent = ""; window.setTimeout(() => { announce.textContent = text; }, 60); }
function focusHeading() {
  const h1 = view.querySelector("h1");
  if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
  window.scrollTo({ top: 0 });
}
function when(iso) { return iso ? iso.replace("T", " ").replace(/:\d\dZ$/, " UTC").replace(/Z$/, " UTC") : ""; }

async function api(path, options) {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), 60000);
  try {
    const res = await fetch(path, Object.assign({ signal: ctrl.signal, headers: { "Content-Type": "application/json" } }, options || {}));
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (res.status === 401 && data && data.kind === "auth_required") location.replace("/login");  // review gate
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { error: "The server could not be reached." } };
  } finally {
    window.clearTimeout(timer);
  }
}
function stopPolling() { if (pollTimer) window.clearTimeout(pollTimer); pollTimer = null; }

// ---------- starting work (the only places that can spend) ----------

async function startSearch(reference, extra, errorTarget) {
  if (posting) return;               // a double click never sends twice
  posting = true;
  document.querySelectorAll("[data-starts]").forEach((b) => { b.disabled = true; });
  const res = await api("/api/sessions", { method: "POST", body: JSON.stringify(Object.assign({ reference, type: "brand" }, extra || {})) });
  posting = false;
  document.querySelectorAll("[data-starts]").forEach((b) => { b.disabled = b.hasAttribute("data-never"); });
  if (res.ok && res.data && res.data.id) { location.hash = "#/s/" + res.data.id; return; }
  const msg = (res.data && res.data.error) || "The search could not be started.";
  if (errorTarget) errorTarget.textContent = msg; else renderProblem("The search could not be started", msg);
}

// ---------- start ----------

// Quick picks only fill a field; research starts only from the Explore button.
const CONTEXT_PICKS = [
  ["Flagship store", "A signature scent for the flagship stores"],
  ["Hotel lobby", "An ambient scent for a hotel lobby"],
  ["Fashion show", "A scent direction for a fashion show"],
  ["Product launch", "A scent for a product launch"],
  ["Private event", "An atmospheric scent for a private event"],
  ["Retail pop-up", "An ambient scent for a retail pop-up"],
  ["Exhibition", "A scent direction for a cultural exhibition"],
  ["Brand dinner", "A scent for an intimate brand dinner"],
];

function quickPicks(label, picks, field) {
  const buttons = picks.map(([text, value]) => h("button", { type: "button", "aria-pressed": "false", "data-value": value, onclick: (e) => {
    field.value = value;
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget)));
  } }, text));
  field.addEventListener("input", () => buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.value === field.value))));
  return h("p", { class: "tries", role: "group", "aria-label": label }, h("span", { class: "tries-label", text: label }), buttons);
}

function renderStart() {
  shown = { id: null, mode: "start" };
  const live = !config || config.live_available;
  const err = h("p", { class: "form-error", id: "form-error", role: "alert" });
  const input = h("input", { id: "brand", name: "brand", type: "text", autocomplete: "off", spellcheck: "false", maxlength: "80",
    placeholder: "Name a brand", "aria-describedby": "form-error" });
  const intent = h("input", { id: "intent", name: "intent", type: "text", autocomplete: "off", maxlength: "140",
    placeholder: "What are you designing the scent for?", "aria-describedby": "intent-hint" });
  const brands = (config && config.examples) || ["MUJI", "Ralph Lauren"];
  const form = h("form", { class: "ask", "aria-label": "Explore a brand", onsubmit: (e) => {
      e.preventDefault();
      const name = input.value.trim();
      if (!name) { err.textContent = "Enter a brand name."; input.focus(); return; }
      err.textContent = "";
      startSearch(name, { intent: intent.value.trim() }, err);
    } },
    h("label", { class: "kicker", for: "brand", text: "Brand" }),
    h("div", { class: "askrow" }, input,
      h("button", { class: "btn", type: "submit", "data-starts": true, disabled: !live, "data-never": !live, text: "Explore a scent direction" })),
    err,
    quickPicks("Try", brands.map((b) => [b, b]), input),
    h("div", { class: "intent" },
      h("label", { class: "kicker", for: "intent", text: "Application context (optional)" }), intent,
      quickPicks("For example", CONTEXT_PICKS, intent),
      h("p", { class: "hint", id: "intent-hint", text: "Used to frame the final brief around its intended setting; cultural evidence and scent direction remain unchanged." })));
  const notice = config && !config.live_available
    ? h("p", { class: "notice", role: "status", text: "Live Qloo access is not configured on this server, so searches cannot run. Nothing is replaced with sample data." }) : null;
  swap(h("section", { class: "hero" },
      h("h1", {}, h("span", { text: "If a brand" }), h("span", { text: "were a" }), h("span", { class: "acc", text: "scent." })),
      h("p", { class: "benefit", text: "Turn a brand's cultural references into a scent direction, a scent architecture, and a one-page brief for a perfumer, with every step traceable." }),
      notice, form),
    h("section", { class: "how", "aria-labelledby": "how-title" },
      h("h2", { class: "kicker", id: "how-title", text: "How it works" }),
      h("ol", {},
        h("li", {}, h("b", { text: "01" }), h("span", { class: "st" }, src("Qloo"), " Cultural references"),
          h("span", { text: "How Qloo describes the brand, and the brands and films it relates to it." })),
        h("li", {}, h("b", { text: "02" }), h("span", { class: "st" }, src("MOTIF"), " Scent direction"),
          h("span", { text: "Weighted motifs, translated into six sensory dimensions and an opening, core, and drydown." })),
        h("li", {}, h("b", { text: "03" }), h("span", { class: "st" }, src("MOTIF"), " Brief"),
          h("span", { text: "A one-page brief for a perfumer, every line traceable to the evidence." })))));
  window.scrollTo({ top: 0 });
}

// ---------- research progress ----------

const STATE = { pending: "Waiting", running: "Now", done: "Done", skipped: "Skipped", stopped: "Stopped", waiting: "Needs you", not_run: "Not run" };

function stepList(steps) {
  return h("ol", { "aria-label": "Research steps" }, steps.map((s, i) =>
    h("li", { class: s.status },
      h("span", { class: "n", text: String(i + 1).padStart(2, "0") }),
      h("span", { class: "t" }, s.label, " ", h("span", { class: "st", text: "· " + STATE[s.status] })),
      s.who ? src(s.who) : h("span", {}),
      s.detail ? h("span", { class: "d", text: s.detail }) : null)));
}

function renderProgress(s) {
  const running = s.steps.find((x) => x.status === "running");
  if (shown.id === s.id && shown.mode === "progress") {
    view.querySelector(".toc ol").replaceWith(stepList(s.steps));
  } else {
    shown = { id: s.id, mode: "progress" };
    swap(h("section", { class: "rs" },
      h("h1", { class: "brand" }, s.reference, h("small", { text: "Researching. Each line is a real step on the server; nothing is estimated." })),
      h("div", { class: "toc" }, h("p", { class: "kicker", text: "Steps of this research" }), stepList(s.steps))));
    focusHeading();
  }
  if (running && running.key !== shown.step) { shown.step = running.key; say(running.label + ": in progress"); }
}

// ---------- retry (one controlled retry after a failed Qloo request) ----------

function retryBlock(s) {
  const r = s.retry || {};
  if (r.retried_by) return h("p", {}, h("a", { href: "#/s/" + r.retried_by, text: "See the retried search" }));
  if (r.available) {
    const err = h("p", { class: "form-error", role: "alert" });
    return h("div", { class: "actions" }, h("button", { class: "btn", type: "button", "data-starts": true, onclick: async (e) => {
      if (posting) return;
      posting = true; e.currentTarget.disabled = true;
      const res = await api("/api/sessions/" + encodeURIComponent(s.id) + "/retry", { method: "POST", body: "{}" });
      posting = false;
      if (res.ok && res.data && res.data.id) { location.hash = "#/s/" + res.data.id; return; }
      e.currentTarget.disabled = false;
      err.textContent = (res.data && res.data.error) || "The retry could not be started.";
    } }, "Try the failed step again"), err);
  }
  if (r.used) return h("p", { class: "mute small", text: "This search was already retried once." });
  return null;
}

// ---------- questions ----------

function renderChoose(s) {
  shown = { id: s.id, mode: "choose" };
  const q = s.question;
  const brands = q.options.filter((o) => o.selectable).length;
  swap(h("section", { class: "stage" },
    h("p", { class: "kicker", text: "One question" }),
    h("h1", { text: "Which " + s.reference + "?" }),
    h("p", { class: "lede", text: brands
      ? "Qloo returned more than one entity for this name. MOTIF researches brands, so only brands can be chosen; other kinds are shown with the reason."
      : "Qloo returned entities for this name, but none is a brand. Try the brand's full name." }),
    h("ul", { class: "options" }, q.options.map((o) => h("li", { class: "option" + (o.selectable ? "" : " off") },
      h("div", {}, h("div", { class: "name", text: o.name }),
        h("div", { class: "meta" }, src(o.type_label), " ", o.exact_name ? "Same name" : "Different name from what you typed", o.detail ? " · " + o.detail : ""),
        o.why_not ? h("div", { class: "meta", text: o.why_not }) : null),
      o.selectable ? h("button", { class: "btn", type: "button", "data-starts": true,
        onclick: () => startSearch(s.reference, { choose: o.qloo_id, parent: s.id, intent: s.intent || "" }) }, "Research this brand") : null))),
    h("div", { class: "actions" }, h("a", { class: "btn ghost", href: "#/", text: "Search a different name" }))));
  focusHeading();
}

// ---------- result ----------

// What each part of the result is: Qloo's evidence, MOTIF's translation of it, or MOTIF's creative proposal.
const PROVENANCE = { "Cultural profile": "Qloo evidence", "Olfactory direction": "MOTIF's translation",
  "Scent architecture": "MOTIF's creative proposal", "Emphasize and avoid": "MOTIF's creative proposal" };

function section(num, title, ...body) {
  return h("section", { class: "sec", id: "sec-" + num },
    h("div", { class: "sech" }, h("h2", {}, h("span", { class: "num", text: num }), title),
      PROVENANCE[title] ? h("p", { class: "prov", text: PROVENANCE[title] }) : null),
    h("div", { class: "body" }, body));
}

function supplierLink(url, text) {
  let host = "";
  try { host = new URL(url).hostname; } catch (e) { return null; }
  return h("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: text || host });
}

function phraseButtons(items, motif) {
  return h("span", { class: "phr" }, items.map((e) => h("button", { type: "button", onclick: (ev) => openEvidence(e, motif, "support", ev.currentTarget),
    "aria-label": "Evidence: " + e.tag + " from " + e.entity }, e.tag, h("span", { class: "ent", text: e.entity }))));
}

function profileBlock(r, brand) {
  const byMotif = Object.fromEntries(r.motifs.map((m) => [m.motif, m]));
  const rows = (ps) => h("ul", { class: "basis" }, ps.map((p) => h("li", { class: p.basis.kind === "related_only" ? "rel" : null },
    h("div", { class: "ax" }, p.label, h("small", { text: p.strength_label + " · " + (p.basis.kind === "related_only" ? "references only: " : "") + p.source_short.join(", ") })),
    h("div", {},
      p.translation ? h("p", { class: "tr" + (/^Moves/.test(p.translation) ? "" : " open"), text: p.translation }) : null,
      phraseButtons(p.examples, byMotif[p.motif] || p),
      p.common ? h("p", { class: "common", text: p.common }) : null))));
  const qloo = h("b", { text: "Cultural evidence sourced from Qloo." });
  if (!r.profile.length) return [h("p", { class: "intro" }, qloo, r.minor.length
      ? " The weaker signals MOTIF reads in it; none is strong enough to lead." : " MOTIF reads no motif in it."),
    r.minor.length ? rows(r.minor) : null];
  return [h("p", { class: "intro" }, qloo, " The motifs MOTIF reads in it, strongest evidence first; motifs from " + brand + "'s own entry lead. “References only” marks a motif found only in brands and films Qloo relates to " + brand + "."),
    rows(r.profile)];
}

function dimensionsBlock(r) {
  const resolved = r.dimensions.filter((d) => d.state === "resolved");
  const open = r.dimensions.filter((d) => d.state !== "resolved");
  return h("div", { class: "dir" },
    resolved.length ? h("div", { class: "char" }, resolved.map((d) => h("span", { class: "w" + (d.tentative ? " rel" : "") },
      h("span", { class: "v", text: d.word }), h("small", { text: d.name + " · " + d.confidence_word })))) : h("p", { class: "none", text: "No dimension is resolved yet." }),
    resolved.some((d) => d.tentative) ? h("p", { class: "mute small", text: "Tentative leanings rest on MOTIF's design reading alone; supported ones on the brand's motifs with a medium-confidence translation." }) : null,
    r.open_summary ? h("p", { class: "openline", text: r.open_summary.line }) : null);
}

// Why the open dimensions are open, and how much of Qloo's vocabulary MOTIF reads: method detail, closed by default.
function methodDetail(o) {
  if (!o) return null;
  return h("details", { class: "fold", id: "method" },
    h("summary", {}, "Method detail", h("small", { text: "Why some dimensions stay open, and how much of what Qloo returned MOTIF reads" })),
    h("div", { class: "method" }, o.lines.map((line) => h("p", { text: line.text })), h("p", { class: "mute", text: o.coverage })));
}

function andList(xs) {
  return xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
}

function roleDetail(role) {
  if (!role.materials.length) return h("p", { class: "mute small", text: "No material reference is named for this direction." });
  return h("details", { class: "refs" }, h("summary", { text: "Material references" }),
    h("ul", {}, role.materials.map((m) => h("li", {}, h("b", { text: m.generic }),
      m.example ? [" (e.g. ", m.url ? supplierLink(m.url, m.example) : m.example, ")"] : null,
      m.ifra ? h("span", { class: "mute", text: " · " + m.ifra.join(", ") }) : null,
      h("span", { class: "mute small", text: " · " + m.source })))),
    h("p", { class: "mute small", text: "Examples of the class, not a formula: no doses or proportions. A trade name is given only where MOTIF read the supplier's page." }));
}

function architectureBlock(r) {
  const a = r.architecture;
  if (a.status !== "proposed") return h("p", { class: "intro", text: "No scent architecture is proposed: no dimension is resolved. The structure is open to the perfumer." });
  return [h("p", { class: "intro", text: "MOTIF's creative proposal, built from the olfactory direction above; not Qloo evidence, and nothing has been smelled."
      + (a.tentative ? " Every role here rests on tentative leanings." : "") }),
    h("div", { class: "roles" }, a.roles.map((role) => {
      if (role.open) return h("div", { class: "role open" }, h("p", { class: "kicker", text: role.name }), h("p", { class: "nm", text: "Open to the perfumer" }));
      const strip = h("span", { class: "strip", "aria-hidden": "true" });
      strip.append(MotifStrips.svg(role.props));
      return h("div", { class: "role" }, strip,
        h("div", {}, h("p", { class: "kicker", text: role.name + (role.tentative ? " · tentative" : "") }),
          h("p", { class: "nm", text: role.label }), h("p", { class: "sc", text: role.descriptors.join(", ") }),
          role.works_with.length ? h("p", { class: "mute small", text: "Fits the " + andList(role.works_with) + "." }) : null,
          roleDetail(role)));
    })),
    r.accord_character ? h("p", { class: "character", text: r.accord_character }) : null];
}

function emphasizeBlock(r) {
  const a = r.architecture;
  const list = (items) => h("ul", {}, items.map((x) => h("li", {}, h("b", { text: x.label }), " · " + x.because.join(", "))));
  return h("div", { class: "ea" },
    a.emphasize.length ? h("div", {}, h("h3", { class: "kicker", text: "Emphasize" }), list(a.emphasize)) : null,
    a.avoid.length ? h("div", {}, h("h3", { class: "kicker", text: "Avoid" }), list(a.avoid)) : null);
}

function sourcesList(r) {
  const q = r.sources.qloo;
  return h("div", { class: "sources" },
    h("h3", { class: "kicker", text: "Sources" }),
    h("ul", {},
      h("li", {}, h("b", { text: "Cultural evidence sourced from Qloo" }), " · fetched " + q.dates.join(", ") + " · "
        + [...new Set(q.requests.map((x) => x.what.charAt(0).toLowerCase() + x.what.slice(1)))].join(", ")
        + ". Each phrase above opens its source: entity, field, request, and date."),
      r.sources.suppliers.map((x) => h("li", {}, h("b", { text: x.supplier }), " · " + x.material + " · ", supplierLink(x.url, "supplier page")))));
}

function whyBlock(s, r, brand) {
  const byMotif = Object.fromEntries(r.motifs.map((m) => [m.motif, m]));
  const res = s.resolution || {};
  const motifRow = (m) => h("div", { class: "mrow" },
    h("div", {}, h("h3", { text: m.label }), h("div", { class: "sp", text: m.strength_label + (m.active ? " · leads" : " · minor") + " · " + m.sources.join(", ") })),
    h("div", {}, h("div", {}, src("Qloo"), " ", phraseButtons(m.evidence, m)), m.translation ? h("div", { class: "rl" }, src("MOTIF"), " ", m.translation) : null));
  // Qloo phrases are quoted once on the page: motifs of the cultural profile point back to it
  const quoted = new Set(r.profile.map((p) => p.motif));
  const cite = (c) => {
    if (quoted.has(c.motif)) return null;
    quoted.add(c.motif);
    return [" · ", phraseButtons(c.examples, byMotif[c.motif] || c)];
  };
  return [h("p", { class: "intro", text: "Qloo supplied the descriptors, quoted literally (the phrases of each motif are in the cultural profile above). MOTIF weighs them into motifs and translates the motifs into dimensions; the scent architecture follows from the dimensions." }),
    r.why.length ? h("ul", { class: "why" }, r.why.map((w) => h("li", {},
      h("div", { class: "ax" }, w.name, h("small", { text: w.word + (w.confidence_word ? " · " + w.confidence_word : "") })),
      h("div", {}, w.chain.map((c) => h("p", {}, h("b", { text: c.label }), " → " + c.toward + (c.tentative ? " (tentative)" : ""), cite(c))))))) : h("p", { text: "No dimension to explain yet." }),
    methodDetail(r.open_summary),
    h("details", { class: "fold", id: "how" },
      h("summary", {}, "All motifs and sources", h("small", { text: "Every phrase opens its entity, field, request, and date" })),
      r.motifs.map(motifRow),
      sourcesList(r),
      h("details", { class: "tech" }, h("summary", { text: "Full trace" }),
        h("p", { text: "Qloo entity: " + (res.name || brand) + (s.fetched ? " · fetched " + when(s.fetched[0]) : "") })))];
}

function briefBlock(s) {
  const b = s.brief;
  if (!b) return h("p", { class: "intro", text: "No brief is written for a stopped or incomplete result." });
  return h("div", { class: "brief" },
    s.intent ? h("p", { class: "intentline", text: "Application context: “" + s.intent + "”" }) : null,
    h("p", { class: "text", text: b.text }),
    b.author === "llm" ? h("p", { class: "byline" }, "Prose drafted by ", src("Claude"), " from this result and checked against it.") : null,
    downloadAction(s.id));
}

function downloadAction(id) {
  const status = h("p", { class: "dlstatus", "aria-live": "polite" });
  const button = h("button", { class: "btn", type: "button", id: "download-pdf", text: MotifDownload.LABEL });
  button.addEventListener("click", () => MotifDownload.brief(id, button, status));
  return h("div", { class: "actions" }, button, status);
}

function renderResult(s, opts) {
  const r = s.result;
  const brand = (s.resolution && s.resolution.name) || s.reference;
  const fresh = !(shown.id === s.id && shown.mode === "result");
  const keepOpen = new Set([...(opts && opts.keepOpen ? [opts.keepOpen] : []), ...[...view.querySelectorAll("details[open][id]")].map((d) => d.id)]);
  shown = { id: s.id, mode: "result" };
  const made = [src("Qloo"), src("MOTIF"), s.brief && s.brief.author === "llm" ? src("Claude") : null];
  const banners = [];
  if (s.status === "stopped") banners.push(h("div", { class: "notice", role: "status" },
    h("p", {}, h("b", { text: "Research stopped early. " }), (s.message || "") + " What follows uses only what was fetched before the stop."), retryBlock(s)));
  let n = 0;
  const num = () => String(++n).padStart(2, "0");
  const a = r.architecture;
  swap(h("section", { class: "res" },
    banners,
    h("div", { class: "lead" },
      h("div", { class: "meta" }, h("p", { class: "kicker", text: r.headline.label }),
        h("h1", { class: brand.length > 12 ? "long" : brand.length > 5 ? "mid" : null, text: brand }),
        brand.toLowerCase() !== s.reference.toLowerCase() ? h("div", { class: "facts", text: "You typed: " + s.reference }) : null,
        h("div", { class: "made" }, made)),
      h("div", { class: "main" },
        h("p", { class: "idea", text: r.headline.title }),
        r.headline.lines.map((line) => h("p", { class: "line", text: line })),
        // the scent idea up front, marked as MOTIF's proposal so it never reads as Qloo evidence
        r.scent_story ? h("div", { class: "scentidea" },
          h("p", { class: "kicker" }, "Scent idea", h("span", { class: "prov", text: " · MOTIF's creative proposal" })),
          h("p", { class: "story", text: r.scent_story })) : null)),
    section(num(), "Cultural profile", profileBlock(r, brand)),
    section(num(), "Olfactory direction", dimensionsBlock(r)),
    section(num(), "Scent architecture", architectureBlock(r)),
    a.emphasize.length || a.avoid.length ? section(num(), "Emphasize and avoid", emphasizeBlock(r)) : null,
    section(num(), "Why: Qloo → motif → scent", whyBlock(s, r, brand)),
    section(num(), "The brief", briefBlock(s))));
  keepOpen.forEach((id) => { const d = document.getElementById(id); if (d) d.open = true; });
  if (fresh) { focusHeading(); say("Result ready for " + brand + "."); }
}

// ---------- evidence dialog ----------

function openEvidence(item, motif, kind, opener) {
  const params = item.request_params ? Object.entries(item.request_params).map(([k, v]) => k + "=" + v).join("&") : "";
  dialogBody.replaceChildren(...[
    h("p", { class: "ev-q", text: "“" + item.tag + "”" }),
    h("div", { class: "ev-part" }, h("h3", {}, src("Qloo"), " Returned by Qloo"),
      h("dl", { class: "kv" },
        h("dt", { text: "Entity" }), h("dd", { text: item.entity + " (" + item.entity_role + ")" }),
        h("dt", { text: "Fetched" }), h("dd", { text: when(item.fetched_at) || "unknown" }),
        item.common_in_sample ? [h("dt", { text: "Frequency" }), h("dd", { text: "Common in MOTIF's seven-brand sample (indicative only)" })] : null)),
    item.source_kind !== "own" ? h("p", { class: "mute small", text: "Qloo describes " + item.entity + " here, a reference it relates to the brand, not the brand itself." }) : null,
    h("div", { class: "ev-part" }, h("h3", {}, src("MOTIF"), " MOTIF's reading, not from Qloo"),
      h("dl", { class: "kv" },
        h("dt", { text: "Motif" }), h("dd", { text: motif.label + " · " + motif.strength_label }),
        h("dt", { text: "Translation" }), h("dd", { text: motif.translation || "No sensory claim: open to the perfumer" }))),
    h("details", { class: "tech" }, h("summary", { text: "Technical record" }),
      h("dl", { class: "kv" },
        h("dt", { text: "Field" }), h("dd", {}, h("code", { text: item.tag_type })),
        h("dt", { text: "Position" }), h("dd", {}, h("code", { text: item.json_pointer })),
        h("dt", { text: "Request" }), h("dd", {}, h("code", { text: "GET " + item.request_path + (params ? "?" + params : "") })),
        h("dt", { text: "Matched cue" }), h("dd", { text: item.cue || "" })))].filter(Boolean));
  dialog._opener = opener || null;
  dialog.showModal();
}
document.getElementById("evidence-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
dialog.addEventListener("close", () => { if (dialog._opener && document.contains(dialog._opener)) dialog._opener.focus(); });

// ---------- problems ----------

function renderProblem(title, text, s) {
  shown = { id: s ? s.id : null, mode: "problem" };
  swap(h("section", { class: "state-panel" },
    h("p", { class: "kicker", text: s ? "Research stopped" : "Problem" }), h("h1", { text: title }), h("p", { class: "lede", text }),
    s ? retryBlock(s) : null,
    s && s.steps ? h("div", { class: "toc" }, stepList(s.steps)) : null,
    h("div", { class: "actions" }, h("a", { class: "btn ghost", href: "#/", text: "Back to the start" }))));
  focusHeading();
}

// ---------- loading and routing ----------

async function loadSession(id, opts) {
  stopPolling();
  const res = await api("/api/sessions/" + encodeURIComponent(id));
  if (!location.hash.endsWith("/" + id)) return;
  if (res.status === 404) return renderProblem("This search is no longer on the server", "Searches are kept in memory for a limited time and are lost when the server restarts. Start a new search; nothing was sent to Qloo just now.");
  if (!res.ok || !res.data) {
    pollFailures += 1;
    if (pollFailures <= 5) { pollTimer = window.setTimeout(() => loadSession(id), 1500 * pollFailures); return; }
    return renderProblem("The server stopped answering", "The research may still be running. Reload this page to check again.");
  }
  pollFailures = 0;
  const s = res.data;
  if (s.status === "running") { renderProgress(s); pollTimer = window.setTimeout(() => loadSession(id), 800); }
  else if (s.status === "needs_choice" && s.question && s.question.kind === "choose_entity") renderChoose(s);
  else if ((s.status === "completed" || s.status === "stopped") && s.result) renderResult(s, opts);
  else if (s.status === "stopped") renderProblem(s.outcome === "not_found" ? "Qloo found nothing under this name" : "The research stopped", s.message || "The research stopped.", s);
  else renderProblem("Something went wrong", s.message || "The server reported an error. No result is shown as complete.", s);
}

function route() {
  stopPolling();
  if (dialog.open) dialog.close();
  const m = location.hash.match(/^#\/s\/([A-Za-z0-9_-]{6,20})$/);
  if (m) { if (shown.id !== m[1]) swap(h("p", { class: "loading", text: "Loading…" })); loadSession(m[1]); }
  else { renderStart(); const input = document.getElementById("brand"); if (input && location.hash === "#/") input.focus({ preventScroll: true }); }
}

async function boot() {
  const res = await api("/api/config");
  config = res.ok ? res.data : null;
  const mode = document.getElementById("mode");
  if (config) {
    if (config.mode_label) { mode.textContent = config.mode_label; mode.hidden = false; }  // local development only
  }
  window.addEventListener("hashchange", route);
  route();
}
boot();

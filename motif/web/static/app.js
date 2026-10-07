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
let openMaterial = null;

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

function renderStart() {
  shown = { id: null, mode: "start" };
  const live = !config || config.live_available;
  const err = h("p", { class: "form-error", id: "form-error", role: "alert" });
  const input = h("input", { id: "brand", name: "brand", type: "text", autocomplete: "off", spellcheck: "false", maxlength: "80",
    placeholder: "Name a brand", "aria-describedby": "form-error" });
  const intent = h("input", { id: "intent", name: "intent", type: "text", autocomplete: "off", maxlength: "140",
    placeholder: "e.g. a signature scent for the flagship stores", "aria-describedby": "intent-hint" });
  const go = (name) => { err.textContent = ""; startSearch(name, { intent: intent.value.trim() }, err); };
  const form = h("form", { class: "ask", "aria-label": "Explore a brand", onsubmit: (e) => {
      e.preventDefault();
      const name = input.value.trim();
      if (!name) { err.textContent = "Enter a brand name."; input.focus(); return; }
      go(name);
    } },
    h("label", { class: "kicker", for: "brand", text: "Brand" }),
    h("div", { class: "askrow" }, input,
      h("button", { class: "btn", type: "submit", "data-starts": true, disabled: !live, "data-never": !live, text: "Explore a scent direction" })),
    err,
    h("div", { class: "intent" },
      h("label", { class: "kicker", for: "intent", text: "Brief purpose (optional)" }), intent,
      h("p", { class: "hint", id: "intent-hint", text: "Used in the brief only; it does not change the direction." })),
    h("p", { class: "tries" }, "Or try",
      (config ? config.examples : ["MUJI", "Ralph Lauren"]).map((name) => h("button", { type: "button", "data-starts": true,
        disabled: !live, "data-never": !live, onclick: () => { input.value = name; go(name); } }, name))));
  const llm = config && config.llm === "configured";
  const notice = config && !config.live_available
    ? h("p", { class: "notice", role: "status", text: "Live Qloo access is not configured on this server, so searches cannot run. Nothing is replaced with sample data." }) : null;
  swap(h("section", { class: "hero" },
      h("h1", {}, h("span", { text: "If a brand" }), h("span", { text: "were a" }), h("span", { class: "acc", text: "scent." })),
      h("p", { class: "benefit", text: "Turn a brand's cultural references into a scent direction, starting materials, and a one-page brief for a perfumer, with every step traceable." }),
      notice, form),
    h("section", { class: "how", "aria-labelledby": "how-title" },
      h("h2", { class: "kicker", id: "how-title", text: "How it works" }),
      h("ol", {},
        h("li", {}, h("b", { text: "01" }), h("span", { class: "st" }, src("Qloo"), " Cultural references"),
          h("span", { text: "How Qloo describes the brand, and the brands and films it relates to it." })),
        h("li", {}, h("b", { text: "02" }), h("span", { class: "st" }, src("MOTIF"), " Scent direction"),
          h("span", { text: "Repeated motifs, translated by visible rules into a direction and verified starting materials." })),
        h("li", {}, h("b", { text: "03" }), h("span", { class: "st" }, llm ? src("Claude") : src("MOTIF"), " Brief"),
          h("span", { text: llm ? "Claude writes the brief from the result; MOTIF checks it against the result."
            : "MOTIF writes the brief from the result with a fixed template." })))));
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

function renderConflict(s) {
  shown = { id: s.id, mode: "conflict" };
  const q = s.question;
  const axis = (s.result && s.result.axes.find((a) => a.key === q.axis)) || { name: q.axis, pushes: [] };
  swap(h("section", { class: "stage" },
    h("p", { class: "kicker", text: "One question" }),
    h("h1", { text: "Two ways on " + axis.name.toLowerCase() }),
    h("p", { class: "lede", text: "Different motifs push this dimension toward opposite poles. MOTIF does not average them: choose one, or leave it open." }),
    s.intent ? h("p", { class: "intentline", text: "Your stated purpose: " + s.intent }) : null,
    h("ul", { class: "options" }, (axis.pushes || []).map((p) => {
      const row = ((s.result && s.result.profile) || []).find((x) => x.motif === p.motif);
      return h("li", { class: "option" }, h("div", {}, h("div", { class: "name", text: (row ? row.label : cap(p.motif)) + " → " + p.pole }),
        row ? h("div", { class: "meta", text: row.strength_label + " · " + row.source_short.join(", ") }) : null));
    })),
    h("div", { class: "actions" }, q.options.map((opt) => h("button", { class: opt === "open" ? "btn ghost" : "btn", type: "button", "data-starts": true,
      onclick: () => startSearch(s.reference, { choose: s.choose, parent: s.id, intent: s.intent || "",
        resolve_conflict: Object.assign({}, s.overrides || {}, { [q.axis]: opt }) }) }, opt === "open" ? "Leave it open" : "Toward " + opt)))));
  focusHeading();
}

// ---------- result ----------

function section(num, title, ...body) {
  return h("section", { class: "sec", id: "sec-" + num },
    h("h2", {}, h("span", { class: "num", text: num }), title), h("div", { class: "body" }, body));
}

function supplierLink(url) {
  let host = "";
  try { host = new URL(url).hostname; } catch (e) { return null; }
  return h("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: host });
}

function materialDetail(m, brand) {
  const asked = m.props.filter((p) => p.requested);
  const other = m.props.filter((p) => !p.requested);
  const quote = (p) => h("div", { class: "prop" },
    h("div", { class: "k", text: p.axis + ": " + p.word }),
    h("div", {}, p.supplier_text ? h("q", { text: p.supplier_text }) : null,
      p.source_url ? h("div", { class: "why" }, "Supplier page: ", supplierLink(p.source_url)) : null));
  return h("div", { class: "matdetail", id: "matdetail", tabindex: "-1" },
    h("p", { class: "kicker", text: "Suggested starting role: " + m.slot }),
    h("h3", {}, m.name, h("span", { class: "sc", text: " · " + (m.scent || "") })),
    h("p", { class: "mute", text: (m.plain ? cap(m.plain) + " · " : "") + (m.supplier_short || "") }),
    h("h4", { text: "Why MOTIF chose it" }),
    h("p", { text: "It fits " + brand + "'s proposed direction on " + m.fits.map((f) => f.toLowerCase()).join(" and ")
      + ". A starting point for the perfumer, not a tested formula." }),
    asked.length ? [h("h4", { text: "Supplier's description (verified on the supplier's page)" }), asked.map(quote)] : null,
    other.length ? [h("h4", { text: "Also described by the supplier" }),
      h("p", { class: "mute small", text: "On dimensions still open in this direction: creative choices, not evidence about " + brand + "." }),
      other.map(quote)] : null,
    m.props.some((p) => p.interpretation) ? [h("h4", { text: "MOTIF's reading" }),
      h("ul", { class: "reading" }, m.props.filter((p) => p.interpretation).map((p) => h("li", { text: p.interpretation })))] : null,
    h("p", { class: "patnote", text: MotifStrips.NOTE }));
}

function referenceList(ref) {
  return [h("p", { class: "intro", text: ref.note }),
    h("ul", { class: "candlist" }, ref.items.map((m) => h("li", {},
      h("b", { text: m.name }), " · " + (m.scent || "") + " · fits " + m.fits.map((f) => f.toLowerCase()).join(", ") + " · ",
      m.source ? h("a", { href: m.source.url, target: "_blank", rel: "noopener noreferrer", text: m.source.supplier + " page" }) : m.supplier_short)))];
}

function materialsBlock(r, brand) {
  const mats = r.materials;
  if (!mats.selected.length) {
    return h("div", { class: "nocomp" }, h("p", { text: mats.status_text }), mats.reference ? referenceList(mats.reference) : null);
  }
  const detailHost = h("div", {});
  const buttons = [];
  const select = (m, btn) => {
    const same = openMaterial === m.id;
    openMaterial = same ? null : m.id;
    buttons.forEach((b) => b.setAttribute("aria-expanded", "false"));
    detailHost.replaceChildren();
    if (!same) { btn.setAttribute("aria-expanded", "true"); detailHost.append(materialDetail(m, brand)); }
  };
  const grid = h("div", { class: "strips" }, mats.selected.map((m) => {
    const strip = h("span", { class: "strip", "aria-hidden": "true" });
    strip.append(MotifStrips.svg(m.props));
    const btn = h("button", { type: "button", class: "mat", "aria-expanded": "false", "aria-controls": "matdetail",
      "aria-label": m.slot + ", suggested starting role: " + m.name + ", " + (m.scent || "") + ". Show why and sources." },
      strip,
      h("span", {}, h("span", { class: "slot", text: m.slot }), h("span", { class: "role", text: "suggested starting role" }),
        h("span", { class: "nm", text: m.name }), h("span", { class: "sc", text: m.scent || "" }),
        h("span", { class: "more", text: "Why and sources" })));
    btn.addEventListener("click", () => select(m, btn));
    buttons.push(btn);
    return btn;
  }));
  if (openMaterial) {
    const i = mats.selected.findIndex((x) => x.id === openMaterial);
    if (i >= 0) { buttons[i].setAttribute("aria-expanded", "true"); detailHost.append(materialDetail(mats.selected[i], brand)); }
  }
  return [h("p", { class: "intro", text: mats.status_text + " Select a strip for why and the supplier's own words." }), grid, detailHost,
    mats.empty_slots && mats.empty_slots.length ? h("p", { class: "mute small", text: "No verified material for: " + mats.empty_slots.join(", ") + ". MOTIF leaves it empty rather than inventing one." }) : null];
}

function phraseButtons(items, motif) {
  return h("span", { class: "phr" }, items.map((e) => h("button", { type: "button", onclick: (ev) => openEvidence(e, motif, "support", ev.currentTarget),
    "aria-label": "Evidence: " + e.tag + " from " + e.entity }, e.tag, h("span", { class: "ent", text: e.entity }))));
}

function profileBlock(r, brand) {
  if (!r.profile.length) return h("p", { class: "intro", text: r.headline.lines.join(" ") || r.outcome_text });
  const byMotif = Object.fromEntries(r.motifs.map((m) => [m.motif, m]));
  return [h("p", { class: "intro", text: "Motifs MOTIF found in the descriptors Qloo returned, strongest evidence first. Motifs from " + brand + "'s own entry lead." }),
    h("ul", { class: "basis" }, r.profile.map((p) => h("li", {},
      h("div", { class: "ax" }, p.label, h("small", { text: p.strength_label + " · " + p.source_short.join(", ") })),
      h("div", {},
        h("p", { class: p.basis.kind === "related_only" ? "rel" : null, text: p.basis.text }),
        h("p", { class: "tr" + (p.state === "direction" ? "" : " open"), text: p.translation }),
        phraseButtons(p.examples, byMotif[p.motif] || { label: p.label, strength_label: p.strength_label, rule: null })))))];
}

function decisionsBlock(r, brand) {
  const items = [];
  for (const q of r.design_questions) items.push(h("li", {}, h("div", {}, "How should " + q.label + " be expressed?", h("small", { text: q.text }))));
  for (const a of r.still_open) {
    const leaning = r.materials.selected.flatMap((m) => m.props.filter((p) => p.axis === a.axis).map((p) => m.name + " leans " + p.word));
    items.push(h("li", {}, h("div", {}, a.axis + ": " + a.poles[0] + " or " + a.poles[1] + "?",
      h("small", { text: (a.state === "conflicted" ? "The evidence points both ways." : "Not decided by the evidence; not a midpoint.")
        + (leaning.length ? " Supplier-described: " + leaning.join("; ") + "." : "") }))));
  }
  items.push(h("li", {}, h("div", {}, "Proportions, further materials, and whether it reads as " + brand + ".", h("small", { text: "Only smelling can decide these." }))));
  return h("ol", { class: "dec" }, items);
}

function briefBlock(s) {
  const b = s.brief;
  if (!b) return h("p", { class: "intro", text: "No brief is written for a stopped or incomplete result." });
  const note = b.note || "";
  const byline = b.author === "llm"
    ? ["Written by ", src("Claude"), " " + b.model + " from the result, then checked against it. It chose no motif, direction, or material."]
    : [src("MOTIF"), " " + (/paused/.test(note) ? note
        : /budget/.test(note) ? "The LLM call budget is used up, so this is MOTIF's fixed template."
        : /failed validation/.test(note) ? "The LLM's text did not pass MOTIF's checks, so this is MOTIF's fixed template."
        : /failed/.test(note) ? "The LLM call did not succeed, so this is MOTIF's fixed template, not LLM output."
        : "Written by MOTIF's fixed template; no LLM is configured on this server.")];
  return h("div", { class: "brief" }, h("p", { class: "text", text: b.text }), h("p", { class: "byline" }, byline),
    h("div", { class: "actions" },
      h("a", { class: "btn", href: "/brief/" + encodeURIComponent(s.id), target: "_blank", rel: "noopener", text: "Print or save as PDF" }),
      h("a", { class: "btn ghost", href: "/api/sessions/" + encodeURIComponent(s.id) + "/brief.json", download: "motif-brief.json", text: "Technical JSON" })));
}

function suggestionsBlock(s, r) {
  const sg = s.suggestions || { status: "unavailable", suggestions: [] };
  const body = [h("p", { class: "intro", text: "On request, Claude suggests up to three readings for descriptors MOTIF's lexicon does not read. Nothing is applied: an accepted reading becomes your note in the brief, never Qloo evidence, and changes no direction or material." })];
  if (r.unread && r.unread.length) {
    body.push(h("p", { class: "mute small" }, "Unread here: ", r.unread.slice(0, 6).map((u, i) => [i ? ", " : "", u.descriptor + (u.own ? " (brand's own)" : " (" + u.entities.length + " references)")])));
  }
  if (sg.status === "not_requested") {
    body.push(h("div", { class: "actions" }, h("button", { class: "btn ghost", type: "button", "data-starts": true, onclick: (e) => requestSuggestions(s, e.currentTarget) }, "Suggest interpretations (one Claude call)")));
  } else if (sg.message) {
    body.push(h("p", { class: "notice", text: sg.message }));
  }
  for (const it of sg.suggestions || []) {
    body.push(h("div", { class: "sug" + (it.decision === "accepted" ? " accepted" : "") },
      h("span", { class: "lbl", text: it.decision === "accepted" ? "Accepted by you — your interpretation, not Qloo evidence; no rule applied" : it.decision === "rejected" ? "Rejected" : "Suggested interpretation — not applied" }),
      h("div", { class: "d", text: it.descriptor }),
      h("div", { class: "from", text: (it.from_brand_itself ? "From the brand's own Qloo entry" : "From " + it.source + ": " + it.entities.join(", ")) }),
      it.decision === "rejected" ? null : [h("p", { class: "r", text: it.reading }), h("p", { class: "qq", text: "Open question: " + it.design_question })],
      h("div", { class: "actions" },
        it.decision === null ? [h("button", { class: "btn", type: "button", onclick: () => decide(s, it.id, "accept") }, "Accept as my note"),
          h("button", { class: "btn ghost", type: "button", onclick: () => decide(s, it.id, "reject") }, "Reject")]
          : h("button", { class: "link", type: "button", onclick: () => decide(s, it.id, "undo") }, "Undo"))));
  }
  return h("details", { class: "fold", id: "suggest" }, h("summary", {}, "Suggested interpretations", h("small", { text: "Optional · for descriptors MOTIF does not read · never applied automatically" })), h("div", {}, body));
}

async function requestSuggestions(s, btn) {
  if (posting) return;
  posting = true; btn.disabled = true; btn.textContent = "Asking Claude…";
  await api("/api/sessions/" + encodeURIComponent(s.id) + "/suggestions", { method: "POST", body: "{}" });
  posting = false;
  await loadSession(s.id, { keepOpen: "suggest" });
}

async function decide(s, id, decision) {
  if (posting) return;
  posting = true;
  await api("/api/sessions/" + encodeURIComponent(s.id) + "/suggestions/" + id, { method: "POST", body: JSON.stringify({ decision }) });
  posting = false;
  await loadSession(s.id, { keepOpen: "suggest" });
}

function sourcesList(r) {
  const q = r.sources.qloo;
  return h("div", { class: "sources" },
    h("h3", { class: "kicker", text: "Sources" }),
    h("ul", {},
      h("li", {}, h("b", { text: q.api }), " · fetched " + q.dates.join(", ") + " · "
        + q.requests.map((x) => x.what.toLowerCase() + " (" + x.path + ", " + x.request_id.replace("local:req:", "request ") + ")").join("; ")
        + ". No public page exists for an API response; the literal values are in the technical JSON."),
      r.sources.suppliers.map((x) => h("li", {}, h("b", { text: x.supplier }), " · " + x.material + " · ",
        h("a", { href: x.url, target: "_blank", rel: "noopener noreferrer", text: x.document || x.url }), x.accessed ? " · read " + x.accessed : ""))));
}

function howBlock(s, r, brand) {
  const active = r.motifs.filter((m) => m.active);
  const rest = r.motifs.filter((m) => !m.active);
  const motifRow = (m) => h("div", { class: "mrow" },
    h("div", {}, h("h3", { text: m.label }), h("div", { class: "sp", text: m.strength_label + (m.active ? " · used" : " · not used") + " · " + m.sources.join(", ") })),
    h("div", {},
      h("div", {}, src("Qloo"), " ", phraseButtons(m.evidence.slice(0, 8), m), m.evidence.some((e) => e.common_in_sample) ? h("span", { class: "tag-common", text: "some common in sample" }) : null),
      h("div", { class: "rl" }, src("MOTIF"), " ", m.rule ? "Draft rule: " + m.label.toLowerCase() + " → " + m.rule.text.toLowerCase() + ". " + m.rule.rationale + "." : "No scent rule for this motif."),
      m.excluded.length ? h("div", { class: "rl mute", text: "Set aside by context rules: " + m.excluded.map((e) => e.tag).join(", ") }) : null));
  const res = s.resolution || {};
  return h("details", { class: "fold", id: "how" },
    h("summary", {}, "How it was made", h("small", { text: "Motifs, rules, and sources; technical records inside" })),
    h("p", { class: "intro", text: "Qloo supplied the literal descriptors. MOTIF grouped them into motifs with a versioned lexicon and translated motifs into directions with draft rules. A motif repeated across references is a pattern, not proof of an aesthetic; descriptors marked common appear for at least four of the seven brands in MOTIF's reference sample." }),
    active.length ? active.map(motifRow) : h("p", { text: "No motif reached the threshold for use." }),
    rest.length ? h("details", { class: "tech" }, h("summary", { text: "Seen but not used (" + rest.length + ")" }), rest.map(motifRow)) : null,
    sourcesList(r),
    h("details", { class: "tech" }, h("summary", { text: "Technical record" }),
      h("p", { text: "Qloo entity: " + (res.name || brand) + (s.fetched ? " · fetched " + when(s.fetched[0]) : "") }),
      h("p", { text: "Versions: engine " + r.versions.engine + " · lexicon " + r.versions.lexicon + " · rules " + r.versions.rules + " · palette " + r.versions.palette + " · params " + r.versions.params }),
      h("p", { text: "Steps: " + s.steps.map((x) => x.label + " (" + x.status + ")").join(" · ") }),
      h("p", {}, "Every phrase above opens its entity, field, request, and date. Full trail: ", h("a", { href: "/api/sessions/" + encodeURIComponent(s.id) + "/brief.json", download: "motif-brief.json", text: "technical JSON" }), ".")));
}

function directionBlock(r, brand) {
  const words = r.direction.map((d) => h("span", { class: "w" + (d.relations_only ? " rel" : "") },
    h("span", { class: "v", text: d.word }), h("small", { text: d.axis + (d.relations_only ? " · related references only" : "") })));
  const axes = h("details", { class: "axes" }, h("summary", { text: "All six dimensions" }),
    h("dl", { class: "kv" }, r.axes.map((a) => {
      const d = r.direction.find((x) => x.key === a.key);
      return [h("dt", { text: a.name + " (" + a.poles[0] + " / " + a.poles[1] + ")" }),
        h("dd", { text: d ? d.word + " · " + (d.basis ? d.basis.text : "")
          : a.state === "conflicted" ? "Open: the evidence points both ways." : "Open: not decided by the evidence; not a midpoint." })];
    })));
  return h("div", { class: "dir" },
    h("p", { class: "kicker", text: "MOTIF's proposed direction" }),
    words.length ? h("div", { class: "char" }, words) : h("p", { class: "none", text: "None yet." }),
    r.still_open.length ? h("p", { class: "stillopen", text: "Still open: " + r.still_open.map((a) => a.axis.toLowerCase()).join(", ") + "." }) : null,
    axes);
}

function renderResult(s, opts) {
  const r = s.result;
  const brand = (s.resolution && s.resolution.name) || s.reference;
  const fresh = !(shown.id === s.id && shown.mode === "result");
  if (fresh) openMaterial = null;
  const keepOpen = new Set([...(opts && opts.keepOpen ? [opts.keepOpen] : []), ...[...view.querySelectorAll("details[open][id]")].map((d) => d.id)]);
  shown = { id: s.id, mode: "result" };
  const made = [src("Qloo"), src("MOTIF"), s.brief && s.brief.author === "llm" ? src("Claude") : null];
  const banners = [];
  if (s.status === "stopped") banners.push(h("div", { class: "notice", role: "status" },
    h("p", {}, h("b", { text: "Research stopped early. " }), (s.message || "") + " What follows uses only what was fetched before the stop."), retryBlock(s)));
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
        directionBlock(r, brand),
        s.intent ? h("p", { class: "intentline", text: "Brief purpose: “" + s.intent + "”. " + (s.intent_effect || "") }) : null)),
    section("01", "Starting materials", materialsBlock(r, brand)),
    section("02", "Cultural profile", profileBlock(r, brand)),
    section("03", "Open decisions", decisionsBlock(r, brand)),
    section("04", "The brief", briefBlock(s)),
    section("05", "Notes", suggestionsBlock(s, r)),
    section("06", "Basis", howBlock(s, r, brand))));
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
        h("dt", { text: "Rule" }), h("dd", { text: motif.rule ? "Draft: " + motif.rule.text : "No scent rule for this motif" }))),
    h("details", { class: "tech" }, h("summary", { text: "Technical record" }),
      h("dl", { class: "kv" },
        h("dt", { text: "Field" }), h("dd", {}, h("code", { text: item.tag_type })),
        h("dt", { text: "Position" }), h("dd", {}, h("code", { text: item.json_pointer })),
        h("dt", { text: "Request" }), h("dd", {}, h("code", { text: "GET " + item.request_path + (params ? "?" + params : "") })),
        h("dt", { text: "Lexicon cue" }), h("dd", { text: item.cue || "" })))].filter(Boolean));
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
  else if (s.status === "needs_choice" && s.question && s.question.kind === "conflict") renderConflict(s);
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

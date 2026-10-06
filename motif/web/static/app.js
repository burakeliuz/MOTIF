/* MOTIF browser client: a thin renderer of the server's session view.
 *
 * Every value shown comes from the server; this file only lays it out. It never
 * builds HTML from data (no innerHTML), never invents progress, and only starts a
 * new search when the person submits one. Re-rendering, back/forward, and reload
 * read the existing session with GET and send nothing to Qloo or the LLM.
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

// ---------- small helpers ----------

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

function swap(...nodes) {
  view.replaceChildren(...nodes);
}

function focusHeading() {
  const h1 = view.querySelector("h1");
  if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
  window.scrollTo({ top: 0 });
}

function say(text) {
  announce.textContent = "";
  window.setTimeout(() => { announce.textContent = text; }, 60);
}

function when(iso) {
  if (!iso) return "";
  return iso.replace("T", " ").replace(/:\d\dZ$/, " UTC").replace(/Z$/, " UTC");
}

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

async function api(path, options) {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), 20000);
  try {
    const res = await fetch(path, Object.assign({ signal: ctrl.signal, headers: { "Content-Type": "application/json" } }, options || {}));
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: { error: "The server could not be reached." } };
  } finally {
    window.clearTimeout(timer);
  }
}

function stopPolling() {
  if (pollTimer) window.clearTimeout(pollTimer);
  pollTimer = null;
}

// ---------- starting a search (the only place that creates work) ----------

async function startSearch(reference, extra, errorTarget) {
  if (posting) return;               // a double click never sends twice
  posting = true;
  document.querySelectorAll("[data-starts]").forEach((b) => { b.disabled = true; });
  const body = Object.assign({ reference, type: "brand" }, extra || {});
  const res = await api("/api/sessions", { method: "POST", body: JSON.stringify(body) });
  posting = false;
  document.querySelectorAll("[data-starts]").forEach((b) => { b.disabled = b.hasAttribute("data-never"); });
  if (res.ok && res.data && res.data.id) {
    location.hash = "#/s/" + res.data.id;
    return;
  }
  const msg = (res.data && res.data.error) || "The search could not be started.";
  if (errorTarget) { errorTarget.textContent = msg; }
  else { renderProblem("The search could not be started", msg); }
}

// ---------- start page ----------

function renderStart(prefill) {
  shown = { id: null, mode: "start" };
  const live = !config || config.live_available;
  const err = h("p", { class: "form-error", id: "form-error", role: "alert" });
  const input = h("input", { id: "brand", name: "brand", type: "text", autocomplete: "off", spellcheck: "false",
    maxlength: "80", required: true, placeholder: "e.g. Aesop", value: prefill || null, "aria-describedby": "form-error" });
  const form = h("form", { class: "search", onsubmit: (e) => {
      e.preventDefault();
      const name = input.value.trim();
      if (!name) { err.textContent = "Enter a brand name."; input.focus(); return; }
      err.textContent = "";
      startSearch(name, null, err);
    } },
    h("label", { for: "brand", text: "Brand" }),
    h("div", { class: "search-row" }, input,
      h("button", { class: "btn", type: "submit", "data-starts": true, disabled: !live, "data-never": !live, text: "Research" })),
    err,
    h("div", { class: "examples" }, h("span", { text: "Or start with" }),
      (config ? config.examples : ["MUJI", "Ralph Lauren"]).map((name) => h("button", {
        class: "chip-btn", type: "button", "data-starts": true, disabled: !live, "data-never": !live,
        onclick: () => { input.value = name; err.textContent = ""; startSearch(name, null, err); } }, name))));

  const notices = [];
  if (config && !config.live_available) {
    notices.push(h("div", { class: "notice", role: "status" },
      h("p", { text: "Live Qloo access is not configured on this server, so searches cannot run right now. Nothing is replaced with sample data." })));
  }
  if (config && config.mode === "recorded") {
    notices.push(h("div", { class: "notice" },
      h("p", { text: "Local preview: this server replays stored Qloo responses and sends no live requests. Only brands in the recording can be researched." })));
  }

  swap(
    h("section", { class: "hero" },
      h("p", { class: "kicker", text: "Cultural evidence → scent direction" }),
      h("h1", {}, "A scent direction, ", h("em", { text: "read from culture." })),
      h("p", { class: "lede", text: "Name a brand. MOTIF finds it in Qloo, reads the descriptors Qloo attaches to the brand and to the brands and films its audience also likes, and translates them, rule by rule, into a direction a perfumer can work from." }),
      notices, form,
      h("p", { class: "muted small", text: "A search makes a few live requests to the Qloo API and usually takes under a minute." })),
    h("ol", { class: "how" },
      h("li", {}, h("h3", { text: "Evidence" }), h("p", { text: "Literal descriptors returned by Qloo, each traceable to its entity, field, and date." })),
      h("li", {}, h("h3", { text: "Translation" }), h("p", { text: "Versioned rules turn repeated descriptors into directions on six sensory dimensions. Dimensions without support stay open." })),
      h("li", {}, h("h3", { text: "Materials and brief" }), h("p", { text: "Starting materials whose properties were checked on supplier pages, and a short brief. Never a formula or a dose." }))));
  if (prefill === undefined) window.scrollTo({ top: 0 });
}

// ---------- research progress ----------

const STATE_WORDS = { pending: "Waiting", running: "In progress", done: "Done", skipped: "Skipped", stopped: "Stopped",
  waiting: "Needs your answer", not_run: "Not run" };

function stepList(steps) {
  return h("ol", { class: "steps", "aria-label": "Research steps" }, steps.map((s) =>
    h("li", { class: "step " + s.status },
      h("span", { class: "dot", "aria-hidden": "true" }),
      h("div", {},
        h("div", { class: "label" }, s.label, " ", h("span", { class: "state", text: "· " + STATE_WORDS[s.status] })),
        s.detail ? h("p", { class: "detail", text: s.detail }) : null))));
}

function renderProgress(s) {
  const running = s.steps.find((x) => x.status === "running");
  if (shown.id === s.id && shown.mode === "progress") {
    view.querySelector(".steps").replaceWith(stepList(s.steps));
  } else {
    shown = { id: s.id, mode: "progress" };
    swap(h("section", { class: "stage" },
      h("p", { class: "kicker", text: "Researching" }),
      h("h1", { text: s.reference }),
      h("p", { class: "lede", text: "Each line below is a real step on the server. Steps that cannot change the result are skipped, and the reason is shown." }),
      stepList(s.steps)));
    focusHeading();
  }
  if (running && running.key !== shown.step) { shown.step = running.key; say(running.label + ": in progress"); }
}

// ---------- questions ----------

function renderChoose(s) {
  shown = { id: s.id, mode: "choose" };
  const q = s.question;
  const brands = q.options.filter((o) => o.selectable).length;
  swap(h("section", { class: "stage" },
    h("p", { class: "kicker", text: "One question" }),
    h("h1", {}, "Which ", h("em", { text: "“" + s.reference + "”" }), " do you mean?"),
    h("p", { class: "lede", text: brands
      ? "Qloo returned more than one entity for this name. MOTIF researches brands, so only brand results can be chosen; stores and other kinds of entity are shown so you can see why."
      : "Qloo returned entities for this name, but none of them is a brand, so MOTIF cannot research it. Try the brand's full name." }),
    h("p", { class: "muted small", text: "Engine note: " + q.why + "." }),
    h("ul", { class: "options" }, q.options.map((o) => h("li", { class: "option" + (o.selectable ? "" : " off") },
      h("div", {},
        h("div", { class: "name", text: o.name }),
        h("div", { class: "meta" },
          h("span", { class: "tag" + (o.selectable ? " accent" : ""), text: o.type_label }),
          o.exact_name ? "Same name" : "Different name from what you typed",
          o.detail ? " · " + o.detail : ""),
        o.why_not ? h("p", { class: "meta", text: o.why_not }) : null),
      o.selectable
        ? h("button", { class: "btn", type: "button", "data-starts": true,
            onclick: () => startSearch(s.reference, { choose: o.qloo_id, parent: s.id }) }, "Research this brand")
        : null))),
    h("div", { class: "actions" }, h("a", { class: "btn ghost", href: "#/", text: "Search a different name" }))));
  focusHeading();
}

function renderConflict(s) {
  shown = { id: s.id, mode: "conflict" };
  const q = s.question;
  const axis = (s.result && s.result.axes.find((a) => a.key === q.axis)) || { name: q.axis, poles: [] };
  const pushes = axis.pushes || [];
  swap(h("section", { class: "stage" },
    h("p", { class: "kicker", text: "One question" }),
    h("h1", { text: "The evidence points two ways on " + axis.name.toLowerCase() + "." }),
    h("p", { class: "lede", text: "Different motifs push this dimension toward opposite poles. MOTIF does not average them. Choose one direction, or leave the dimension open." }),
    pushes.length ? h("ul", {}, pushes.map((p) => h("li", { text: cap(p.motif) + " → " + p.pole + (p.rule_id ? " (rule " + p.rule_id + ")" : "") }))) : null,
    h("div", { class: "actions" }, q.options.map((opt) => h("button", {
      class: opt === "open" ? "btn ghost" : "btn", type: "button", "data-starts": true,
      onclick: () => startSearch(s.reference, { choose: s.choose, parent: s.id,
        resolve_conflict: Object.assign({}, s.overrides || {}, { [q.axis]: opt }) }) },
      opt === "open" ? "Leave it open" : "Toward " + opt)))));
  focusHeading();
}

// ---------- result ----------

function section(num, title, intro, ...body) {
  return h("section", { class: "section reveal" },
    h("header", {}, h("p", { class: "kicker" }, h("span", { class: "num", text: num }), title.kicker),
      h("h2", { text: title.heading }), intro ? h("p", { text: intro }) : null),
    body);
}

function axisRow(a, name) {
  const [left, right] = a.poles;
  const side = a.state === "target" ? (a.value === left ? "left" : "right") : null;
  const track = h("div", { class: "track " + a.state, "aria-hidden": "true" },
    side ? h("span", { class: "mark " + side }) : null);
  let text;
  if (a.state === "target") text = name + " toward " + a.value + ".";
  else if (a.state === "conflicted") text = name + ": the evidence points both ways; no direction is set.";
  else text = name + ": not decided by the evidence.";
  const notes = [];
  if (a.state === "target") {
    notes.push(h("p", { class: "note" }, h("strong", { text: a.strength_label }), " · rule " + a.rules.join(", ") + " · " + a.rule_confidence +
      " · from " + a.motifs.map(cap).join(", ")));
    if (a.relations_only) notes.push(h("p", { class: "relonly", text: a.relations_only_text }));
  } else if (a.state === "conflicted") {
    notes.push(h("p", { class: "note", text: "Evidence points both ways: " + (a.pushes || []).map((p) => cap(p.motif) + " → " + p.pole).join("; ") + "." }));
  } else {
    notes.push(h("p", { class: "note", text: "Not decided by the evidence. This is not a midpoint; the dimension is open." }));
  }
  return h("li", { class: "axis " + a.state },
    h("div", { class: "aname", text: a.name }),
    h("div", { class: "scale", role: "img", "aria-label": text },
      h("span", { class: "pole left" + (side === "left" ? " on" : ""), text: left }),
      track,
      h("span", { class: "pole right" + (side === "right" ? " on" : ""), text: right })),
    notes);
}

function phraseButton(item, motif, kind) {
  return h("li", {}, h("button", { type: "button", class: "phrase" + (kind === "excluded" ? " excluded" : ""),
      "aria-label": "Evidence: “" + item.tag + "” from " + item.entity + (kind === "excluded" ? " (set aside)" : ""),
      onclick: (e) => openEvidence(item, motif, kind, e.currentTarget) },
    h("span", { class: "q", text: "“" + item.tag + "”" }),
    h("span", { class: "who", text: item.entity + " · " + item.source })));
}

function phraseList(items, motif, kind, limit) {
  const list = h("ul", { class: "phrases" }, items.slice(0, limit).map((i) => phraseButton(i, motif, kind)));
  if (items.length > limit) {
    const more = h("li", {}, h("button", { type: "button", class: "chip-btn", onclick: () => {
      more.replaceWith(...items.slice(limit).map((i) => phraseButton(i, motif, kind)));
    } }, "Show all " + items.length));
    list.append(more);
  }
  return list;
}

function motifItem(m, name) {
  const rule = m.rule
    ? h("p", { class: "rule" }, h("b", { text: "Rule " + m.rule.id + " (draft): " }), m.rule.text + ". ", h("span", { class: "muted", text: m.rule.rationale + "." }))
    : h("p", { class: "rule muted", text: m.active ? "MOTIF has no scent rule for this motif, so it sets no direction." : "No scent rule." });
  return h("li", { class: "motif" + (m.active ? " active" : "") },
    h("div", {}, h("h3", { text: m.label }), h("p", { class: "strength", text: m.strength_label + (m.active ? " · used" : " · not used") })),
    h("div", { class: "body" },
      m.sources.length ? h("p", { class: "muted small", text: "Found in: " + m.sources.join(", ") }) : null,
      rule,
      m.relations_only && m.active ? h("p", { class: "relonly", text: "Only from related entities: none of these descriptors is on " + name + "'s own Qloo entry." }) : null,
      m.evidence.length ? [h("p", { class: "subhead", text: "Qloo descriptors counted" }), phraseList(m.evidence, m, "support", 8)] : null,
      m.context.length ? [h("p", { class: "subhead", text: "Very common descriptors (shown, not counted)" }), phraseList(m.context, m, "context", 4)] : null,
      m.excluded.length ? [h("p", { class: "subhead", text: "Set aside by context rules" }), phraseList(m.excluded, m, "excluded", 4)] : null));
}

function materialCard(m, showSlot) {
  return h("li", { class: "material" },
    h("div", { class: "top" },
      showSlot && m.slot ? h("span", { class: "slot", text: m.slot }) : null,
      h("h3", { text: m.name })),
    h("p", { class: "kind", text: cap(m.kind) + (m.supplier ? " · " + m.supplier : "") }),
    m.matches.map((x) => h("div", { class: "match" },
      h("p", { class: "why", text: "Matches " + x.axis.toLowerCase() + " → " + x.pole }),
      x.supplier_text ? h("blockquote", { text: "“" + x.supplier_text + "”" }) : null,
      x.interpretation ? h("p", { class: "interp", text: "MOTIF's reading: " + x.interpretation }) : null,
      x.source_url ? h("p", { class: "interp" }, "Supplier page: ",
        h("a", { href: x.source_url, target: "_blank", rel: "noopener noreferrer", text: new URL(x.source_url).hostname }),
        x.accessed ? [", ", h("span", { class: "nowrap", text: "read " + x.accessed })] : "") : null)),
    m.creative_choices.length ? h("p", { class: "creative" },
      h("b", { text: "Creative choice, not evidence: " }),
      m.creative_choices.map((c) => "also brings " + c.pole + " (" + c.axis.toLowerCase() + ")").join("; ") + ".") : null);
}

function templateNote(note) {
  if (/LLM call failed/.test(note || "")) return "The LLM call did not succeed, so this is MOTIF's fixed template, not LLM output.";
  if (/failed validation/.test(note || "")) return "The LLM's text did not pass MOTIF's checks, so this is MOTIF's fixed template instead.";
  return "No LLM is configured on this server; the wording comes from MOTIF's fixed template.";
}

function renderResult(s) {
  const r = s.result;
  const name = (s.resolution && s.resolution.name) || s.reference;
  const fresh = !(shown.id === s.id && shown.mode === "result");
  shown = { id: s.id, mode: "result" };
  const banners = [];
  if (s.status === "stopped") {
    banners.push(h("div", { class: "notice", role: "status" },
      h("p", {}, h("b", { text: "Research stopped early. " }), s.message || ""),
      h("p", { text: "What follows uses only the evidence fetched before the stop. It is incomplete, and no brief is written for it." }),
      h("details", {}, h("summary", { text: "Which steps ran" }), stepList(s.steps))));
  }
  if (s.data_label === "recorded") {
    banners.push(h("div", { class: "notice" }, h("p", { text: "Recorded data: stored Qloo responses (" + (s.recorded_from || []).join(", ") + "), not live requests." })));
  }
  const facts = [
    h("li", { text: "Qloo entity: " + name + (s.resolution && s.resolution.method === "user_choice" ? " (your choice)" : "") }),
    s.fetched ? h("li", { text: "Fetched " + when(s.fetched[0]) + (when(s.fetched[1]) !== when(s.fetched[0]) ? " to " + when(s.fetched[1]) : "") }) : null,
    h("li", { text: s.data_label === "recorded" ? "Recorded data" : "Live data" }),
    name.toLowerCase() !== s.reference.toLowerCase() ? h("li", { text: "You typed: " + s.reference }) : null,
  ];
  const words = r.direction.map((d) => cap(d.value));
  const direction = h("div", { class: "direction" },
    h("p", { class: "kicker", text: "Direction" }),
    words.length
      ? h("p", { class: "words" }, words.flatMap((w, i) => i ? [h("span", { class: "sep", "aria-hidden": "true", text: "·" }), w] : [w]))
      : h("p", { class: "none", text: "No direction is supported yet." }),
    h("p", { class: "muted", text: r.headline + (r.headline_note ? " " + r.headline_note : "") }),
    r.open.length ? h("p", { class: "small muted", text: "Left open by the evidence: " + r.open.join(", ") + "." }) : null);

  const active = r.motifs.filter((m) => m.active);
  const rest = r.motifs.filter((m) => !m.active);
  const mats = r.materials;
  const matList = mats.selected.length ? mats.selected : mats.candidates;

  const brief = s.brief;
  const byline = brief
    ? (brief.author === "llm"
      ? [h("span", { class: "tag accent", text: "LLM prose" }), " Written by " + brief.model + " from the engine result, then checked against it. The model chose no motif, direction, or material."]
      : [h("span", { class: "tag", text: "Template prose" }), " " + templateNote(brief.note)])
    : null;

  swap(
    h("section", { class: "result-head" },
      banners,
      h("p", { class: "kicker", text: s.status === "stopped" ? "Partial result for" : "Scent direction for" }),
      h("h1", { text: name }),
      h("ul", { class: "facts" }, facts),
      direction),
    section("01", { kicker: "Six dimensions", heading: "Where the evidence points" },
      "A mark sits at the pole MOTIF aims for. A dimension without a mark was not decided by the evidence: it is open, not a midpoint.",
      h("ul", { class: "axes" }, r.axes.map((a) => axisRow(a, name)))),
    section("02", { kicker: "Motifs", heading: "What Qloo's descriptors have in common" },
      "MOTIF groups literal Qloo descriptors into motifs with a versioned lexicon. Open any phrase to see the entity, field, request, and date it came from.",
      active.length ? h("ul", { class: "motifs" }, active.map((m) => motifItem(m, name)))
        : h("p", { class: "muted", text: "No motif reached the threshold for use." }),
      r.unmapped_active.length ? h("p", { class: "notice", text: "Supported but without a scent rule: " + r.unmapped_active.join(", ") + ". MOTIF does not invent a translation." }) : null,
      rest.length ? h("details", { class: "weak-list" }, h("summary", { text: "Seen but not used (" + rest.length + ")" }),
        h("ul", { class: "motifs" }, rest.map((m) => motifItem(m, name)))) : null),
    section("03", { kicker: "Starting materials", heading: mats.selected.length ? "Verified materials that fit" : "No composition proposed" },
      mats.status_text,
      mats.verification_mode !== "verified_only" ? h("p", { class: "notice", text: "Design preview: unverified material properties are in use. Not for live matching." }) : null,
      matList.length ? h("ul", { class: "materials" }, matList.map((m) => materialCard(m, mats.selected.length > 0))) : null,
      mats.excluded.length ? h("details", { class: "excluded-mats" }, h("summary", { text: "Not used (" + mats.excluded.length + ")" }),
        h("ul", {}, mats.excluded.map((m) => h("li", { text: m.name + ": " + m.reason })))) : null),
    brief ? section("04", { kicker: "Perfumer brief", heading: "The brief" }, null,
      h("div", { class: "brief" }, h("p", { class: "text", text: brief.text }), h("p", { class: "byline" }, byline)),
      h("div", { class: "actions" },
        h("a", { class: "btn ghost", href: "/api/sessions/" + encodeURIComponent(s.id) + "/brief.json", download: "motif-brief.json", text: "Download brief (JSON)" }),
        h("a", { class: "btn", href: "#/", text: "Research another brand" }))) : null,
    section(brief ? "05" : "04", { kicker: "Provenance", heading: "What Qloo returned, and what MOTIF added" }, null,
      h("div", { class: "ledger" },
        h("div", {}, h("h3", { text: "Returned by Qloo" }), h("ul", {},
          h("li", { text: "The entity match for “" + s.reference + "”." }),
          h("li", { text: "Descriptor tags on the brand's own entry and on related brands" + (r.motifs.some((m) => m.sources.includes("Related films")) ? " and films" : "") + ", copied literally with their position in the response." }),
          h("li", { text: "Which entities are related. Relation means shared audiences, not a shared aesthetic." }))),
        h("div", {}, h("h3", { text: "Added by MOTIF" }), h("ul", {},
          h("li", { text: "Grouping descriptors into motifs (lexicon " + r.versions.lexicon + ") and their strength thresholds." }),
          h("li", { text: "Draft creative rules from motifs to sensory directions (" + r.versions.rules + ")." }),
          h("li", { text: "Material profiles from supplier pages (" + r.versions.palette + "); only verified properties are matched." }),
          h("li", { text: brief && brief.author === "llm" ? "The brief's wording, written by an LLM under MOTIF's checks." : "The brief's wording, from a fixed template." })))),
      h("p", { class: "small muted", text: "Engine " + r.versions.engine + " · lexicon " + r.versions.lexicon + " · rules " + r.versions.rules + " · palette " + r.versions.palette + " · params " + r.versions.params }),
      brief ? null : h("div", { class: "actions" }, h("a", { class: "btn", href: "#/", text: "Research another brand" }))));
  if (fresh) { focusHeading(); say("Result ready for " + name + "."); }
}

// ---------- evidence dialog ----------

function openEvidence(item, motif, kind, opener) {
  const params = item.request_params ? Object.entries(item.request_params).map(([k, v]) => k + "=" + v).join("&") : "";
  const motifSide = [];
  if (kind === "excluded") {
    motifSide.push(h("dt", { text: "Set aside" }), h("dd", { text: item.excluded_reason || "context rule" }));
  } else {
    motifSide.push(h("dt", { text: "Lexicon cue" }), h("dd", { text: item.cue ? "“" + item.cue + "”" : "(cue)" }));
    motifSide.push(h("dt", { text: "Motif" }), h("dd", { text: motif.label + " · " + motif.strength_label }));
    if (kind === "context") motifSide.push(h("dt", { text: "Counted" }), h("dd", { text: "No: a very common descriptor, shown for context only." }));
    motifSide.push(h("dt", { text: "Rule" }), h("dd", { text: motif.rule ? motif.rule.id + " (draft): " + motif.rule.text : "No scent rule for this motif." }));
  }
  dialogBody.replaceChildren(
    h("p", { class: "ev-quote", text: "“" + item.tag + "”" }),
    h("div", { class: "ev-part" },
      h("h3", { text: "Returned by Qloo · " + item.provenance }),
      h("dl", { class: "kv" },
        h("dt", { text: "Entity" }), h("dd", { text: item.entity + " (" + item.entity_role + ")" }),
        h("dt", { text: "Field" }), h("dd", {}, "tag name, type ", h("code", { text: item.tag_type })),
        h("dt", { text: "Position" }), h("dd", {}, h("code", { text: item.json_pointer })),
        h("dt", { text: "Request" }), h("dd", {}, h("code", { text: "GET " + item.request_path + (params ? "?" + params : "") })),
        h("dt", { text: "Fetched" }), h("dd", { text: when(item.fetched_at) || "unknown" }))),
    item.source_kind !== "own" ? h("p", { class: "small muted", text: "Qloo describes " + item.entity + " here, a related entity, not the brand itself." }) : null,
    h("div", { class: "ev-part motif-side" },
      h("h3", { text: "MOTIF's reading · not from Qloo" }),
      h("dl", { class: "kv" }, motifSide)));
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
    h("p", { class: "kicker", text: s ? "Research stopped" : "Problem" }),
    h("h1", { text: title }),
    h("p", { class: "lede", text: text }),
    s && s.steps ? stepList(s.steps) : null,
    h("div", { class: "actions" }, h("a", { class: "btn", href: "#/", text: "Back to the start" }))));
  focusHeading();
}

// ---------- session loading and routing ----------

async function loadSession(id) {
  stopPolling();
  const res = await api("/api/sessions/" + encodeURIComponent(id));
  if (!location.hash.endsWith("/" + id)) return;   // the person navigated away meanwhile
  if (res.status === 404) {
    return renderProblem("This search is no longer on the server",
      "Searches are kept in memory for a limited time and are lost when the server restarts. Start a new search; nothing was sent to Qloo just now.");
  }
  if (!res.ok || !res.data) {
    pollFailures += 1;
    if (pollFailures <= 5) { pollTimer = window.setTimeout(() => loadSession(id), 1500 * pollFailures); return; }
    return renderProblem("The server stopped answering", "The research may still be running on the server. Reload this page to check again.");
  }
  pollFailures = 0;
  const s = res.data;
  if (s.status === "running") {
    renderProgress(s);
    pollTimer = window.setTimeout(() => loadSession(id), 800);
  } else if (s.status === "needs_choice" && s.question && s.question.kind === "choose_entity") {
    renderChoose(s);
  } else if (s.status === "needs_choice" && s.question && s.question.kind === "conflict") {
    renderConflict(s);
  } else if ((s.status === "completed" || s.status === "stopped") && s.result) {
    renderResult(s);
  } else if (s.status === "stopped") {
    renderProblem(s.outcome === "not_found" ? "Qloo found nothing under this name" : "The research stopped", s.message || "The research stopped.", s);
  } else {
    renderProblem("Something went wrong", s.message || "The server reported an error. No result is shown as complete.", s);
  }
}

function route() {
  stopPolling();
  if (dialog.open) dialog.close();
  const m = location.hash.match(/^#\/s\/([A-Za-z0-9_-]{6,20})$/);
  if (m) {
    if (!(shown.id === m[1])) swap(h("p", { class: "loading", text: "Loading…" }));
    loadSession(m[1]);
  } else {
    renderStart();
    const input = document.getElementById("brand");
    if (input && location.hash === "#/") input.focus({ preventScroll: true });
  }
}

async function boot() {
  const res = await api("/api/config");
  config = res.ok ? res.data : null;
  const mode = document.getElementById("mode");
  if (config) {
    mode.textContent = config.mode_label;
    mode.classList.toggle("recorded", config.mode === "recorded");
    mode.hidden = false;
    const v = config.versions || {};
    document.getElementById("versions").textContent = Object.values(v).join(" · ");
  }
  window.addEventListener("hashchange", route);
  route();
}

boot();

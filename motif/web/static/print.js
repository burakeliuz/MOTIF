/* Printable brief: renders the session already on the server into one A4 page.
 * It sends no research request; it reads GET /api/sessions/<id> only. Every value
 * comes from the same session view as the web page, so the two cannot disagree. */
"use strict";

(() => {
  const sheet = document.getElementById("sheet");
  const id = (location.pathname.match(/^\/brief\/([A-Za-z0-9_-]{6,20})$/) || [])[1];
  const download = document.getElementById("download");
  download.addEventListener("click", () => id && MotifDownload.brief(id, download, document.getElementById("dlstatus")));
  document.getElementById("back").href = id ? "/#/s/" + id : "/";

  function h(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") node.className = v; else if (k === "text") node.textContent = v; else node.setAttribute(k, v);
    }
    for (const kid of kids.flat(Infinity)) if (kid !== null && kid !== undefined && kid !== false) node.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
    return node;
  }
  const link = (url, text) => h("a", { href: url, target: "_blank", rel: "noopener noreferrer", text });

  const PROVENANCE = { "Cultural profile": "Qloo evidence", "Olfactory direction": "MOTIF's translation",
    "Scent architecture": "MOTIF's creative proposal", "Emphasize and avoid": "MOTIF's creative proposal" };

  function section(num, title, ...body) {
    return h("div", { class: "grid" }, h("div", {}, h("h2", {}, h("span", { text: num }), title),
      PROVENANCE[title] ? h("p", { class: "prov", text: PROVENANCE[title] }) : null), h("div", {}, body));
  }

  function profile(r) {
    if (!r.profile.length) return h("p", { text: r.minor.length ? "Weaker signals, none strong enough to lead: "
      + r.minor.slice(0, 4).map((p) => p.label.toLowerCase() + " (" + p.source_short.join(", ") + ")").join("; ") + "." : "MOTIF reads no motif in the Qloo descriptors." });
    return h("ul", { class: "basis" }, r.profile.slice(0, 4).map((p) => h("li", {},
      h("b", { text: p.label + " · " }), p.strength_label.toLowerCase() + ", " + (p.basis.kind === "related_only" ? "references only: " : "")
        + p.source_short.join(", ") + "." + (p.translation ? " " + p.translation : "") + " Examples: ",
      p.examples.slice(0, 3).map((e, i) => [i ? ", " : "", h("span", { class: "sc", text: e.tag }), " (" + e.entity + ")"]), ".",
      p.common ? h("span", { class: "cm", text: " " + p.common }) : null)));
  }

  function dimensions(r) {
    const resolved = r.dimensions.filter((d) => d.state === "resolved");
    const o = r.open_summary;
    return [h("p", { class: "dirl" },
      resolved.length ? resolved.map((d, i) => [i ? " · " : "", h("b", { text: d.word.toUpperCase() }), " (" + d.name.toLowerCase() + ", " + d.confidence_word + ")"]) : "No dimension resolved yet",
      "."),
      o ? h("p", { class: "open", text: o.line }) : null];
  }

  // the page's closed "Method detail": why the open dimensions are open, and how much MOTIF reads
  function method(r) {
    const o = r.open_summary;
    return o ? h("p", { class: "method" }, h("b", { text: "Method detail. " }), o.lines.map((line) => line.text).join(" ") + " " + o.coverage) : null;
  }

  function architecture(r) {
    const a = r.architecture;
    if (a.status !== "proposed") return h("p", { text: "No scent architecture is proposed: the structure is open to the perfumer." });
    return [h("div", { class: "mats" }, a.roles.map((role) => {
      if (role.open) return h("div", { class: "mat open" }, h("div", {}, h("div", { class: "s", text: role.name }), h("div", { class: "n", text: "Open to the perfumer" })));
      const strip = h("div", { class: "strip" });
      strip.append(MotifStrips.svg(role.props));
      const refs = role.materials.slice(0, 2);
      return h("div", { class: "mat" }, strip, h("div", {},
        h("div", { class: "s", text: role.name + (role.tentative ? " · tentative" : "") }),
        h("div", { class: "n", text: role.label }),
        h("div", { class: "x", text: role.descriptors.join(", ") }),
        refs.length ? h("div", { class: "q" }, "e.g. ", refs.map((m, i) => [i ? "; " : "", m.generic,
          m.example ? [" (", m.url ? link(m.url, m.example) : m.example, ")"] : null])) : null));
    })),
    r.accord_character ? h("p", { class: "character", text: r.accord_character }) : null];
  }

  function emphasize(r) {
    const a = r.architecture;
    const items = (xs) => xs.map((x) => x.label.toLowerCase()).join("; ");
    return h("p", {}, a.emphasize.length ? [h("b", { text: "Emphasize " }), items(a.emphasize) + ". "] : null,
      a.avoid.length ? [h("b", { text: "Avoid " }), items(a.avoid) + "."] : null);
  }

  function why(r) {
    return h("ul", { class: "basis" }, r.why.filter((w) => w.state === "resolved").slice(0, 3).map((w) => h("li", {},
      h("b", { text: w.name + " → " + w.word + " · " }),
      w.chain.slice(0, 2).map((c, i) => [i ? "; " : "", c.label + (c.tentative ? " (tentative)" : ""), " from ",
        c.examples.slice(0, 2).map((e, j) => [j ? ", " : "", h("span", { class: "sc", text: e.tag })])]), ".")));
  }

  function sources(r) {
    const q = r.sources.qloo;
    return h("ul", { class: "src" },
      h("li", {}, h("b", { text: "Cultural evidence sourced from Qloo" }), " · fetched " + q.dates.join(", ") + " · "
        + [...new Set(q.requests.map((x) => x.what.charAt(0).toLowerCase() + x.what.slice(1)))].join(", ")
        + ". Every phrase traces to its Qloo entity, field, and request in MOTIF's session record."),
      r.sources.suppliers.length ? h("li", {}, h("b", { text: "Supplier pages (identity of the trade-name examples)" }), " · ",
        r.sources.suppliers.map((x, i) => [i ? " · " : "", link(x.url, x.material)])) : null);
  }

  function render(s) {
    const r = s.result;
    const brand = (s.resolution && s.resolution.name) || s.reference;
    document.title = "MOTIF brief · " + brand;
    const date = s.fetched ? s.fetched[0].slice(0, 10) : "";
    const b = s.brief;
    const a = r.architecture;
    let n = 0;
    const num = () => String(++n).padStart(2, "0");
    sheet.replaceChildren(...[
      h("div", { class: "hd" }, h("span", { class: "lg", text: "MOTIF" }),
        h("span", { class: "m" }, "Perfumer brief · scent direction", h("br"),
          (s.data_label === "recorded" ? "Recorded preview · " : "") + "Cultural evidence sourced from Qloo" + (date ? " · " + date : ""))),
      h("h1", { text: brand }),
      h("p", { class: "lbl", text: r.headline.label }),
      h("p", { class: "idea", text: r.headline.title }),
      r.headline.lines.map((line) => h("p", { class: "line", text: line })),
      r.scent_story ? h("div", { class: "scent" }, h("p", { class: "k", text: "Scent idea · MOTIF's creative proposal" }),
        h("p", { class: "st", text: r.scent_story })) : null,
      section(num(), "Cultural profile", profile(r)),
      section(num(), "Olfactory direction", dimensions(r)),
      section(num(), "Scent architecture", architecture(r)),
      a.emphasize.length || a.avoid.length ? section(num(), "Emphasize and avoid", emphasize(r)) : null,
      section(num(), "Why", why(r), method(r), sources(r)),
      b ? section(num(), "The brief",
        s.intent ? h("p", { class: "note", text: "Application context: “" + s.intent + "”" }) : null,
        h("p", { class: "prose", text: b.text.replace(/\n\s*\n+/g, "\n").trim() }),
        b.author === "llm" ? h("p", { class: "note", text: "Prose drafted by Claude from this result and checked against it." }) : null) : null,
      h("div", { class: "ft" },
        h("span", { text: "A creative direction, not a formula: not smelled or balanced, no proportions, no prediction of who will like it." }),
        h("span", { text: "1 / 1" }))].flat(Infinity).filter(Boolean));
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(fit);  // measure with the real fonts
  }

  // Keep the brief on one A4 page: measure an off-screen copy laid out at A4 width and step
  // the type down (never below about 7 pt) until the content fits the printable height.
  function fit() {
    const page = 276 * 96 / 25.4;  // printable height in CSS px: 297 mm minus 21 mm of margins
    const probe = sheet.cloneNode(true);
    probe.removeAttribute("id");
    document.body.append(probe);
    let chosen = "";
    for (const level of ["", "fit1", "fit2", "fit3"]) {
      probe.className = ("sheet measure " + level).trim();
      const style = getComputedStyle(probe);
      const inner = probe.scrollHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
      chosen = level;
      if (inner <= page) break;
    }
    probe.remove();
    sheet.className = ("sheet " + chosen).trim();
  }

  async function load() {
    if (!id) { sheet.textContent = "No brief selected."; return; }
    const res = await fetch("/api/sessions/" + encodeURIComponent(id), { headers: { "Content-Type": "application/json" } });
    if (res.status === 401) { location.replace("/login"); return; }
    const s = res.ok ? await res.json() : null;
    if (!s || !s.result) { sheet.textContent = "This brief is not available: the search is unknown, still running, or has no result."; return; }
    render(s);
  }
  load();
})();

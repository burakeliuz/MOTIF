/* Printable brief: renders the session already on the server into one A4 page.
 * It sends no research request; it reads GET /api/sessions/<id> only. Every value
 * comes from the same session view as the web page, so the two cannot disagree. */
"use strict";

(() => {
  const sheet = document.getElementById("sheet");
  const id = (location.pathname.match(/^\/brief\/([A-Za-z0-9_-]{6,20})$/) || [])[1];
  document.getElementById("print").addEventListener("click", () => window.print());
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
  const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
  // A quote is kept literal; a long one is cut at a word boundary and marked with an ellipsis.
  const short = (text, max) => {
    if (!text || text.length <= max) return text || "";
    const cut = text.slice(0, max);
    return cut.slice(0, cut.lastIndexOf(" ")).replace(/[ ,.;:…]+$/, "") + " …";
  };
  const link = (url, text) => h("a", { href: url, target: "_blank", rel: "noopener noreferrer", text });

  function section(num, title, ...body) {
    return h("div", { class: "grid" }, h("h2", {}, h("span", { text: num }), title), h("div", {}, body));
  }

  function materials(r, brand) {
    const mats = r.materials;
    if (!mats.selected.length) {
      const ref = mats.reference;
      return [h("p", { text: mats.status_text }), ref ? [h("p", { class: "note", text: ref.note }),
        h("ul", { class: "ref" }, ref.items.map((m) => h("li", {}, h("b", { text: m.name }), " · " + (m.scent || "") + " · fits "
          + m.fits.map((f) => f.toLowerCase()).join(", ") + " · ", m.source ? link(m.source.url, m.source.supplier) : m.supplier_short)))] : null];
    }
    return h("div", { class: "mats" }, mats.selected.map((m) => {
      const strip = h("div", { class: "strip" });
      strip.append(MotifStrips.svg(m.props));
      const asked = m.props.filter((p) => p.requested);
      const other = m.props.filter((p) => !p.requested);
      const first = asked.find((p) => p.supplier_text) || asked[0];
      return h("div", { class: "mat" }, strip, h("div", {},
        h("div", { class: "s", text: m.slot }), h("div", { class: "rl", text: "suggested starting role" }),
        h("div", { class: "n" }, m.name, h("span", { class: "sc", text: " · " + (m.scent || "") })),
        h("div", { class: "x", text: "Why: fits " + brand + "'s " + m.fits.map((f) => f.toLowerCase()).join(" and ") + "." }),
        first && first.supplier_text ? h("div", { class: "q" }, "“" + short(first.supplier_text, 90) + "” ",
          first.source_url ? link(first.source_url, m.source ? m.source.supplier : "supplier page") : null) : null,
        other.length ? h("div", { class: "x" }, h("b", { text: "Also" }), " supplier-described: "
          + other.map((p) => p.word + " (" + p.axis.toLowerCase() + " is open)").join(", ") + ".") : null));
    }));
  }

  function profile(r) {
    if (!r.profile.length) return h("p", { text: r.headline.lines.join(" ") || r.outcome_text });
    return h("ul", { class: "basis" }, r.profile.slice(0, 4).map((p) => h("li", {},
      h("b", { text: p.label + " · " }), p.basis.text + " " + p.translation + " Examples: ",
      p.examples.slice(0, 3).map((e, i) => [i ? ", " : "", h("span", { class: "sc", text: e.tag }), " (" + e.entity + ")"]), ".")));
  }

  function sources(r) {
    const q = r.sources.qloo;
    return h("ul", { class: "src" },
      h("li", {}, h("b", { text: q.api }), " · fetched " + q.dates.join(", ") + " · "
        + q.requests.map((x) => x.what.toLowerCase() + " (" + x.path + ", " + x.request_id.replace("local:req:", "request ") + ")").join("; ")
        + ". API responses have no public page; literal values are in the technical JSON."),
      r.sources.suppliers.map((x) => h("li", {}, h("b", { text: x.supplier }), " · " + x.material + " · ",
        link(x.url, x.document || x.url), x.accessed ? " · read " + x.accessed : "")));
  }

  function render(s) {
    const r = s.result;
    const brand = (s.resolution && s.resolution.name) || s.reference;
    document.title = "MOTIF brief · " + brand;
    const date = s.fetched ? s.fetched[0].slice(0, 10) : "";
    const b = s.brief;
    const dir = r.direction.map((d) => d.word.toUpperCase() + " (" + d.axis.toLowerCase() + (d.relations_only ? ", related references only" : "") + ")");
    let n = 0;
    const num = () => String(++n).padStart(2, "0");
    sheet.replaceChildren(...[
      h("div", { class: "hd" }, h("span", { class: "lg", text: "MOTIF" }),
        h("span", { class: "m" }, "Perfumer brief · scent direction", h("br"),
          (s.data_label === "recorded" ? "Recorded preview · " : "") + "Qloo data" + (date ? " fetched " + date : ""))),
      h("h1", { text: brand }),
      h("p", { class: "lbl", text: r.headline.label }),
      h("p", { class: "idea", text: r.headline.title }),
      r.headline.lines.map((line) => h("p", { class: "line", text: line })),
      section(num(), "Cultural profile", profile(r)),
      section(num(), "MOTIF's proposed direction", h("p", { class: "dirl" }, dir.length ? dir.join(" · ") : "None yet",
        r.still_open.length ? ". Still open: " + r.still_open.map((a) => a.axis.toLowerCase()).join(", ") + "." : ".")),
      section(num(), "Starting materials", materials(r, brand)),
      section(num(), "Evidence", sources(r)),
      b ? section(num(), "The brief",
        s.intent ? h("p", { class: "note", text: "Application context: “" + s.intent + "”" }) : null,
        h("p", { class: "prose", text: b.text.replace(/\n\s*\n+/g, "\n").trim() }),
        h("p", { class: "note", text: b.author === "llm" ? "Written by Claude (" + b.model + ") from the result and checked against it; it chose nothing."
          : "Written by MOTIF's fixed template." })) : null,
      h("div", { class: "ft" },
        h("span", { text: "A creative direction, not a formula: not smelled or balanced, no proportions, no prediction of who will like it. "
          + "MOTIF " + r.versions.engine + " · " + r.versions.lexicon + " · rules " + r.versions.rules + " · " + r.versions.palette + "." }),
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

/* Printable brief: renders the session already on the server into one A4 page.
 * It sends no research request; it reads GET /api/sessions/<id> only. */
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

  function render(s) {
    const r = s.result;
    const brand = (s.resolution && s.resolution.name) || s.reference;
    document.title = "MOTIF brief · " + brand;
    const targets = r.axes.filter((a) => a.state === "target");
    const open = r.axes.filter((a) => a.state !== "target");
    const mats = r.materials.selected;
    const accepted = ((s.suggestions || {}).suggestions || []).filter((x) => x.decision === "accepted");
    const domains = [...new Set(mats.flatMap((m) => m.props.map((p) => p.source_url).filter(Boolean)).map((u) => new URL(u).hostname))];
    const date = s.fetched ? s.fetched[0].slice(0, 10) : "";
    const decisions = [];
    for (const a of open) {
      const lean = mats.flatMap((m) => m.props.filter((p) => p.axis === a.name).map((p) => m.name + " leans " + p.pole));
      decisions.push(a.name + ": " + a.poles[0] + " or " + a.poles[1] + "?" + (lean.length ? " (" + lean.join("; ") + ")" : ""));
    }
    for (const q of r.design_questions) decisions.push(cap(q.label) + ": " + q.text);
    decisions.push("Proportions, further materials, and whether it reads as " + brand + ": only smelling can decide.");

    sheet.replaceChildren(
      h("div", { class: "hd" }, h("span", { class: "lg", text: "MOTIF" }),
        h("span", { class: "m" }, "Perfumer brief · scent direction", h("br"), (s.data_label === "recorded" ? "Recorded Qloo data" : "Live Qloo data") + (date ? ", " + date : ""))),
      h("h1", { text: brand }),
      h("p", { class: "idea", text: r.idea }),
      h("div", { class: "char" }, targets.map((a) => h("span", { class: "w", text: a.value })), open.map((a) => h("span", { class: "o", text: a.name }))),
      h("p", { class: "note", text: (targets.length ? "Set by the evidence: " + targets.map((a) => a.name.toLowerCase() + " → " + a.value).join(", ") + ". " : "") + (open.length ? "Outlined dimensions are left open, not midpoints." : "") }),
      s.intent ? h("p", { class: "note", text: "Stated purpose (from the user, not evidence): “" + s.intent + "”. It did not change the direction or the materials." }) : null,

      h("div", { class: "grid" }, h("h2", {}, h("span", { text: "01" }), "Starting materials"),
        mats.length ? h("div", { class: "mats" }, mats.map((m) => {
          const strip = h("div", { class: "strip" }); strip.append(MotifStrips.svg(m.props));
          const asked = m.props.filter((p) => p.requested);
          const other = m.props.filter((p) => !p.requested);
          return h("div", { class: "mat" }, strip, h("div", {},
            h("div", { class: "s", text: m.slot + " · starting role" }), h("div", { class: "n", text: m.name }),
            h("div", { class: "pl", text: cap(m.plain || "") + " · " + (m.supplier_short || "") }),
            h("div", { class: "q", text: "“" + (asked[0] && asked[0].supplier_text || m.scent || "") + "”" }),
            h("div", { class: "x" }, "Serves: " + asked.map((p) => p.axis.toLowerCase() + " → " + p.pole).join(", ") + ".",
              other.length ? [" ", h("b", { text: "Also" }), " supplier-described: " + other.map((p) => p.pole + " (" + p.axis.toLowerCase() + " is open)").join(", ") + "."] : "")));
        })) : h("div", {}, h("p", { text: r.materials.status_text }))),

      h("div", { class: "grid" }, h("h2", {}, h("span", { text: "02" }), "Why " + brand),
        targets.length ? h("ul", { class: "basis" }, targets.map((a) => {
          const ev = r.motifs.filter((m) => a.motifs.includes(m.motif)).flatMap((m) => m.evidence);
          ev.sort((x, y) => (x.source_kind === "own" ? 0 : 1) - (y.source_kind === "own" ? 0 : 1));
          const seen = new Set();
          const picks = ev.filter((e) => (seen.has(e.tag) ? false : seen.add(e.tag))).slice(0, 3);
          return h("li", {}, h("b", { text: a.value + " · " }), (a.basis ? a.basis.text : "") + " Examples: ",
            picks.map((e, i) => [i ? ", " : "", h("span", { class: "sc", text: e.tag }), " (" + e.entity + ")"]), ".");
        })) : h("p", { text: r.headline })),

      h("div", { class: "grid" }, h("h2", {}, h("span", { text: "03" }), "Open decisions"), h("ol", {}, decisions.map((d) => h("li", { text: d })))),

      accepted.length ? h("div", { class: "grid" }, h("h2", {}, h("span", { text: "04" }), "Your notes"),
        h("ol", {}, accepted.map((x) => h("li", { text: x.descriptor + ": " + x.reading + " (accepted by you; not Qloo evidence; no rule applied)" })))) : null,

      h("div", { class: "ft" },
        h("span", {}, "Limits: a creative direction, not a formula: not smelled, not balanced, no proportions, no prediction of who will like it. Sources: Qloo Hackathon API descriptors for " + brand + " and references Qloo relates to it" + (date ? " (" + date + ")" : "") + "; supplier pages (" + domains.join(", ") + "), read 2026-10-06. Direction and materials: MOTIF " + r.versions.engine + ", " + r.versions.lexicon + ", rules " + r.versions.rules + ", " + r.versions.palette + ". " + (s.brief && s.brief.author === "llm" ? "Brief wording by Claude (" + s.brief.model + "), checked against the result. " : "") + "Full evidence trail: technical JSON."),
        h("span", { text: "1 / 1" })));
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

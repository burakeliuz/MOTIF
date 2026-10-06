/* Scent strips: MOTIF's visual shorthand for a material's supplier-described properties.
 *
 * One texture per property pole. A property on a dimension the direction asks for is drawn
 * at full strength; a property on a dimension the evidence leaves open is drawn faint.
 * Both kinds of property are supplier-described and verified on the supplier's page; the
 * faint drawing only says the brand evidence did not ask for it. The texture is MOTIF's
 * interpretation, never a measurement. Everything is built with DOM methods, no HTML strings.
 */
"use strict";

const MotifStrips = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const INK = "#121212";
  let uid = 0;

  function el(name, attrs) {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, String(v));
    return node;
  }

  // Each builder returns [width, height, children] for a userSpaceOnUse pattern tile.
  const TEXTURES = {
    light: (o) => [16, 16, [el("circle", { cx: 8, cy: 8, r: 1.4, fill: INK, "fill-opacity": o })]],
    dense: (o) => [6, 6, [el("circle", { cx: 3, cy: 3, r: 1.3, fill: INK, "fill-opacity": o })]],
    polished: (o) => [10, 7, [el("line", { x1: 0, y1: 3.5, x2: 10, y2: 3.5, stroke: INK, "stroke-width": 0.9, "stroke-opacity": o })]],
    raw: (o) => [14, 14, [el("path", { d: "M1 4 L5 2 M8 9 L12 6 M3 12 L6 10", stroke: INK, "stroke-width": 1.1, "stroke-opacity": o, fill: "none" })]],
    natural: (o) => [26, 16, [el("path", { d: "M0 8 Q6.5 2 13 8 T26 8", stroke: INK, "stroke-width": 1, "stroke-opacity": o, fill: "none" })]],
    synthetic: (o) => [12, 12, [el("path", { d: "M0 0 H12 M0 0 V12", stroke: INK, "stroke-width": 0.8, "stroke-opacity": o, fill: "none" })]],
    warm: (o) => [9, 9, [el("line", { x1: 0, y1: 9, x2: 9, y2: 0, stroke: INK, "stroke-width": 0.9, "stroke-opacity": o })]],
    cool: (o) => [9, 9, [el("line", { x1: 4.5, y1: 0, x2: 4.5, y2: 9, stroke: INK, "stroke-width": 0.8, "stroke-opacity": o })]],
    intimate: (o) => [14, 14, [el("circle", { cx: 7, cy: 7, r: 2, fill: "none", stroke: INK, "stroke-width": 0.9, "stroke-opacity": o })]],
    projecting: (o) => [44, 44, [el("circle", { cx: 22, cy: 22, r: 9, fill: "none", stroke: INK, "stroke-width": 0.8, "stroke-opacity": o }),
      el("circle", { cx: 22, cy: 22, r: 18, fill: "none", stroke: INK, "stroke-width": 0.6, "stroke-opacity": o })]],
    sweet: (o) => [20, 20, [el("circle", { cx: 10, cy: 10, r: 3.4, fill: "none", stroke: INK, "stroke-width": 0.9, "stroke-opacity": o })]],
    dry: (o) => [12, 12, [el("path", { d: "M0 12 L12 0 M0 0 L12 12", stroke: INK, "stroke-width": 0.5, "stroke-opacity": o, fill: "none" })]],
  };

  /** props: [{pole, requested}] → an <svg> filling its parent. */
  function svg(props) {
    const root = el("svg", { "aria-hidden": "true", focusable: "false" });
    const defs = el("defs");
    root.append(defs);
    for (const p of props) {
      const make = TEXTURES[p.pole];
      if (!make) continue;
      const [w, h, kids] = make(p.requested ? 0.95 : 0.3);
      const id = "mp" + (++uid);
      const pat = el("pattern", { id, width: w, height: h, patternUnits: "userSpaceOnUse" });
      pat.append(...kids);
      defs.append(pat);
      root.append(el("rect", { width: "100%", height: "100%", fill: `url(#${id})` }));
    }
    return root;
  }

  const NOTE = "The texture is MOTIF's visual shorthand for the supplier-described properties: darker for the dimensions this direction asks for, lighter for supplier-described properties on dimensions the evidence leaves open. It is an interpretation, not a measurement.";

  return { svg, NOTE };
})();

"""Self-review of a motif-to-sensory model (phase 3): rules, data agreement, coverage, similarity.

  python3 tools/sensory_model_review.py [--model config/candidates/motif_sensory_vectors.v1.json] [--markdown OUT.md]

Checks, all deterministic and offline (problems make the exit code 1; notes are reported):
* every cell's value equals its direction sign x strength value; enums are valid;
* the model's own rules: low confidence -> at most weak; design inference -> at most moderate; an
  imagery route is moderate only when its odor step is replicated (both rated datasets, r >= 0.3,
  pleasantness-robust); 'high' is not used; the forbidden stereotype cells are null;
* imagery-route cells: at least one of the motif's imagery families supports the cell's pole in
  config/candidates/odor_axis_evidence.v1.json; families rated less on that pole, or supporting
  the opposite pole, are noted; design cells whose own imagery points the other way are noted;
* every number quoted after a family word in rationale, uncertainty, or null notes matches a value
  measured for that family (any pole of the cell's dimension, or powdery), within rounding;
* pole coverage, nulls, evidence types; pairwise cosine similarity (null as 0); near-identical
  pairs (>= 0.9) are problems; 'opposite' pairs with a positive similarity are noted.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AXES = ("warm_cool", "light_dense", "raw_polished", "natural_synthetic", "intimate_projecting", "sweet_dry")
POLES = {"warm_cool": ("warm", "cool"), "light_dense": ("light", "dense"), "raw_polished": ("raw", "polished"),
         "natural_synthetic": ("natural", "synthetic"), "intimate_projecting": ("intimate", "projecting"), "sweet_dry": ("sweet", "dry")}
OPPOSITES = [("restrained", "opulent"), ("natural", "industrial"), ("playful", "melancholic"), ("heritage", "experimental"),
             ("intimate", "provocative"), ("precise", "natural")]
FORBIDDEN = [("playful", "sweet_dry", "sweet"), ("melancholic", "warm_cool", "cool"), ("heritage", "warm_cool", "warm"),
             ("industrial", "natural_synthetic", "synthetic")]
FAMILY_WORDS = {"balsamic": "gourmand_balsamic", "gourmand": "gourmand_balsamic", "spicy": "spicy", "floral": "floral",
                "woody": "woody", "burnt": "burnt_tar", "tar": "burnt_tar", "animalic": "animalic", "leathery": "leathery",
                "metallic": "metallic", "earthy": "earthy_musty", "citrus": "citrus", "fruity": "fruity", "musk": "musk",
                "chemical": "chemical_solvent", "green": "green_herbal", "incense": "incense", "soapy": "soapy_aldehydic"}
NEAR_IDENTICAL = 0.9


def vec(model, m):
    return [((model["motifs"][m]["cells"].get(a) or {}).get("value") or 0.0) for a in AXES]


def cosine(u, v):
    nu, nv = math.sqrt(sum(x * x for x in u)), math.sqrt(sum(x * x for x in v))
    return sum(a * b for a, b in zip(u, v)) / (nu * nv) if nu and nv else 0.0


def family_values(evidence, axis, fam):
    vals = []
    for key in [f"{axis}:{p}" for p in POLES[axis]] + ["extra:powdery"]:
        for d in (evidence["measurements"].get(key, {}).get(fam) or {}).values():
            vals += [d.get("r", d.get("phi")), d.get("r_without_top5")]
    return [v for v in vals if isinstance(v, (int, float))]


def check_numbers(text, axis, evidence):
    """Numbers after a family word must match that family's measured values on this axis."""
    bad = []
    words = sorted(FAMILY_WORDS, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(words) + r")\b", re.IGNORECASE)
    marks = [(m.start(), FAMILY_WORDS[m.group(1).lower()]) for m in pattern.finditer(text)]
    for i, (start, fam) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        for num in re.findall(r"(?:D85|KV16|LEF)[^0-9-]{0,12}(-?\d\.\d\d)", text[start:end]):
            known = family_values(evidence, axis, fam)
            if not any(abs(abs(float(num)) - abs(v)) <= 0.005 + 1e-9 for v in known):
                bad.append(f"{fam} {num}")
    return bad


def review(model, evidence):
    problems, notes = [], []
    sv = model["strength_values"]
    summary = evidence["summary"]
    for m, spec in model["motifs"].items():
        for a in AXES:
            cell = spec["cells"].get(a)
            texts = [spec.get("null_notes", {}).get(a, "")]
            if cell is not None:
                texts += [cell["rationale"], cell["uncertainty"]]
                pole = cell["direction"]
                sign = -1 if pole == POLES[a][0] else 1 if pole == POLES[a][1] else 0
                if not sign or cell["strength"] not in sv or abs(cell["value"] - sign * sv[cell["strength"]]) > 1e-9:
                    problems.append(f"{m}.{a}: value {cell['value']} does not match {pole}/{cell['strength']}")
                if cell["confidence"] not in ("low", "medium") or cell["evidence_type"] not in model["evidence_types"]:
                    problems.append(f"{m}.{a}: confidence or evidence type not allowed")
                if cell["confidence"] == "low" and cell["strength"] != "weak":
                    problems.append(f"{m}.{a}: low confidence but strength {cell['strength']}")
                fams = spec.get("imagery", [])
                own = {f: summary.get(f"{a}:{pole}", {}).get(f, {"class": "none", "less": []}) for f in fams}
                other = {f: summary.get(f"{a}:{POLES[a][1] if sign < 0 else POLES[a][0]}", {}).get(f, {"class": "none"}) for f in fams}
                if cell["evidence_type"] == "imagery_route":
                    supporting = [f for f, s in own.items() if s["class"] != "none"]
                    if not supporting:
                        problems.append(f"{m}.{a}: imagery route with no imagery family supporting '{pole}'")
                    strong = [f for f in supporting if own[f]["class"] == "replicated" and not own[f]["weak_effect"] and own[f]["valence_robust"]]
                    if cell["strength"] == "moderate" and not strong:
                        problems.append(f"{m}.{a}: moderate imagery route without a replicated, robust odor step")
                for f, s in own.items():
                    if s.get("less"):
                        notes.append(f"{m}.{a}: imagery family {f} is rated less {pole} ({', '.join(s['less'])})")
                for f, s in other.items():
                    if s["class"] != "none":
                        notes.append(f"{m}.{a}: imagery family {f} supports the opposite pole")
            for t in texts:
                for b in check_numbers(t, a, evidence):
                    problems.append(f"{m}.{a}: quoted value {b} is not measured for that family on {a}")
    for m, a, pole in FORBIDDEN:
        c = model["motifs"][m]["cells"].get(a)
        if c and c["direction"] == pole:
            problems.append(f"{m}.{a}: forbidden stereotype cell ({m} = {pole}) is not null")
    if any(model["motifs"]["romantic"]["cells"].get(a) and model["motifs"]["romantic"]["imagery"] for a in AXES):
        problems.append("romantic: floral imagery is forbidden without an owner decision")
    motifs = list(model["motifs"])
    sims = {(x, y): cosine(vec(model, x), vec(model, y)) for x, y in itertools.combinations(motifs, 2)}
    cells = [(m, a, c) for m in motifs for a, c in model["motifs"][m]["cells"].items() if c]
    coverage = {p: sorted(m for m, a, c in cells if c["direction"] == p) for a in AXES for p in POLES[a]}
    near = sorted([(x, y, round(s, 3)) for (x, y), s in sims.items() if s >= NEAR_IDENTICAL], key=lambda r: -r[2])
    problems += [f"near-identical vectors: {x}–{y} {s}" for x, y, s in near]
    opp = [(x, y, round(sims.get((x, y), sims.get((y, x), 0.0)), 3)) for x, y in OPPOSITES]
    notes += [f"opposite pair {x}–{y} has positive similarity {s:+.2f}" for x, y, s in opp if s > 0]
    return {"problems": problems, "notes": notes, "similarity": sims, "coverage": coverage,
            "non_null": len(cells), "empty_motifs": [m for m in motifs if not any(model["motifs"][m]["cells"].values())],
            "per_axis": {a: sum(1 for x in cells if x[1] == a) for a in AXES},
            "evidence_types": {t: sum(1 for x in cells if x[2]["evidence_type"] == t) for t in model["evidence_types"]},
            "confidence": {c: sum(1 for x in cells if x[2]["confidence"] == c) for c in ("low", "medium", "high")},
            "most_similar": sorted([(x, y, round(s, 3)) for (x, y), s in sims.items()], key=lambda r: -r[2])[:6], "opposites": opp}


def markdown(model, rep):
    motifs = list(model["motifs"])
    L = ["| Motif | " + " | ".join(f"{POLES[a][0]} − / + {POLES[a][1]}" for a in AXES) + " |", "|---|" + "---|" * len(AXES)]
    for m in motifs:
        row = []
        for a in AXES:
            c = model["motifs"][m]["cells"].get(a)
            row.append(f"{c['value']:+.2f} {c['confidence'][0].upper()}{'*' if c['evidence_type'] == 'imagery_route' else ''}" if c else "")
        L.append(f"| {m} | " + " | ".join(row) + " |")
    L += ["", "M/L = medium/low confidence; * = imagery route (motif → odor imagery → pole); blank = null.", "",
          "Pairwise cosine similarity (null as 0):", "", "| | " + " | ".join(m[:5] for m in motifs) + " |", "|---|" + "---|" * len(motifs)]
    for x in motifs:
        L.append(f"| {x} | " + " | ".join("—" if x == y else f"{rep['similarity'].get((x, y), rep['similarity'].get((y, x))):+.2f}" for y in motifs) + " |")
    L += ["", f"Non-null cells: {rep['non_null']} of {len(motifs) * len(AXES)}; motifs with no claim: {', '.join(rep['empty_motifs']) or 'none'}. "
          "Per dimension: " + ", ".join(f"{a} {n}" for a, n in rep["per_axis"].items()) + ".",
          "Evidence types: " + ", ".join(f"{k} {v}" for k, v in rep["evidence_types"].items())
          + ". Confidence: " + ", ".join(f"{k} {v}" for k, v in rep["confidence"].items()) + ".",
          "Pole coverage: " + "; ".join(f"{p} ({len(ms)})" for p, ms in rep["coverage"].items()) + ".",
          "Most similar pairs: " + ", ".join(f"{x}–{y} {s:+.2f}" for x, y, s in rep["most_similar"]) + ".",
          "Opposite pairs: " + ", ".join(f"{x}–{y} {s:+.2f}" for x, y, s in rep["opposites"]) + ".",
          "Notes: " + ("; ".join(rep["notes"]) or "none") + ".",
          "Problems: " + ("; ".join(rep["problems"]) or "none") + "."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default=str(ROOT / "config" / "candidates" / "motif_sensory_vectors.v1.json"))
    ap.add_argument("--evidence", default=str(ROOT / "config" / "candidates" / "odor_axis_evidence.v1.json"))
    ap.add_argument("--markdown")
    args = ap.parse_args(argv)
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    rep = review(model, json.loads(Path(args.evidence).read_text(encoding="utf-8")))
    text = markdown(model, rep)
    if args.markdown:
        Path(args.markdown).write_text(text, encoding="utf-8")
    print(text)
    return 1 if rep["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

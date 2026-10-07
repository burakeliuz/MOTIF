"""Empirical odor-family -> sensory-pole evidence from open olfactory datasets (phase 3).

Reads three datasets from the Pyrfume public data archive (github.com/pyrfume/pyrfume-data,
fetched from raw.githubusercontent.com into the git-ignored data/external/pyrfume/):

* Dravnieks (1985), Atlas of Odor Character Profiles (D85): panel applicability of 146
  descriptors for 160 stimuli; pole descriptors WARM, COOL/COOLING, LIGHT, HEAVY, SWEET.
* Keller & Vosshall (2016), Olfactory perception of chemically diverse molecules (KV16):
  55 subjects rate about 480 molecules at two dilutions (960 stimuli, not independent) on
  20 descriptors incl. WARM, COLD, SWEET (0-100), plus pleasantness.
* Leffingwell odor dataset (LEF): binary expert labels for about 3,500 molecules, incl. warm,
  dry, sweet. Too sparse (warm 40, dry 31 molecules) to decide anything; agreement only.

Each pole is measured by its own descriptor, never by a contrast: in D85, WARM and COOL are
unrelated (r about -0.04) and so are SWEET and DRY/POWDERY, so a contrast would turn
"rated less cool" into "warmer" and "less sweet" into "drier". No dataset has a usable dry
descriptor (D85's "DRY, POWDERY" is reported as powdery only), so the dry pole is never
supported by data here; "rated less sweet" is reported as such.

For each odor family (a fixed group of each dataset's own descriptors) and each pole
descriptor: Pearson r across stimuli (D85, KV16), phi (LEF), a deterministic bootstrap 95%
interval, r with the five stimuli highest on the family removed, and for KV16 the partial r
with pleasantness held constant. Associations between descriptors, not causes; nothing here
is about brands. Only aggregates are written; the datasets stay local.

  python3 tools/sensory_evidence.py [--fetch] [--write config/candidates/odor_axis_evidence.v1.json]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "external" / "pyrfume"
BASE = "https://raw.githubusercontent.com/pyrfume/pyrfume-data/main/"
FILES = ["dravnieks_1985/behavior_1.csv", "dravnieks_1985/manifest.toml", "keller_2016/behavior.csv",
         "keller_2016/manifest.toml", "leffingwell/behavior.csv", "leffingwell/manifest.toml"]
SOURCES = {
    "dravnieks_1985": {"key": "D85", "citation": "A. Dravnieks (1985), Atlas of Odor Character Profiles, ASTM DS61 (doi 10.1520/DS61-EB, as printed in the Pyrfume manifest)",
                       "read": "dataset only (Pyrfume processed behavior_1.csv: applicability averaged across panelists); the book itself was not read",
                       "stimuli": 160},
    "keller_2016": {"key": "KV16", "citation": "A. Keller, L. B. Vosshall (2016), Olfactory perception of chemically diverse molecules, BMC Neuroscience (doi 10.1186/s12868-016-0287-2, as printed in the Pyrfume manifest)",
                    "read": "dataset only (Pyrfume processed behavior.csv); the article was not read",
                    "stimuli": "960 (about 480 molecules x 2 dilutions; not independent)"},
    "leffingwell": {"key": "LEF", "citation": "Leffingwell odor dataset, cleaned by B. Sanchez-Lengeling, J. N. Wei et al. (doi 10.5281/zenodo.4085098, as printed in the Pyrfume manifest)",
                    "read": "dataset only (Pyrfume processed behavior.csv: binary expert labels)",
                    "stimuli": "about 3,500 molecules"},
}
# Odor families as groups of each dataset's own descriptor names (exact column / label names).
FAMILIES = {
    "citrus": {"dravnieks_1985": ["FRUITY,CITRUS", "LEMON", "GRAPEFRUIT", "ORANGE"], "leffingwell": ["citrus", "lemon", "orange", "grapefruit"]},
    "fruity": {"dravnieks_1985": ["FRUITY,OTHER THAN CITRUS", "PINEAPPLE", "STRAWBERRY", "APPLE, FRUIT", "PEAR", "PEACH FRUIT", "BANANA", "CHERRY, BERRY"],
               "keller_2016": ["FRUIT"], "leffingwell": ["fruity", "apple", "pear", "peach", "berry", "banana", "pineapple", "tropical", "plum", "strawberry", "apricot", "melon", "grape"]},
    "floral": {"dravnieks_1985": ["FLORAL", "ROSE", "VIOLETS"], "keller_2016": ["FLOWER"], "leffingwell": ["floral", "rose", "jasmine", "violet", "orris"]},
    "green_herbal": {"dravnieks_1985": ["HERBAL, GREEN,CUTGRASS", "CRUSHED GRASS", "CRUSHED WEEDS", "FRESH GREEN VEGETABLES", "GERANIUM LEAVES", "RAW CUCUMBER"],
                     "keller_2016": ["GRASS"], "leffingwell": ["green", "grassy", "herbal", "leafy", "cucumber"]},
    "woody": {"dravnieks_1985": ["WOODY, RESINOUS", "CEDARWOOD", "OAK WOOD,COGNAC", "BARK,BIRCHBARK"], "keller_2016": ["WOOD"], "leffingwell": ["woody"]},
    "spicy": {"dravnieks_1985": ["SPICY", "CLOVE", "CINNAMON", "BLACK PEPPER"], "keller_2016": ["SPICES"], "leffingwell": ["spicy", "cinnamon"]},
    "gourmand_balsamic": {"dravnieks_1985": ["VANILLA", "CARAMEL", "MAPLE SYRUP", "CHOCOLATE", "HONEY"], "keller_2016": ["BAKERY"],
                          "leffingwell": ["vanilla", "caramellic", "balsamic", "honey", "chocolate", "cocoa"]},
    # perfumery musk and animalic notes behave differently in D85; KV16's lay "MUSKY" tracks SWEATY,
    # so it is grouped with animalic, not with musk
    "musk": {"dravnieks_1985": ["MUSK"], "leffingwell": ["musk"]},
    "animalic": {"dravnieks_1985": ["ANIMAL"], "keller_2016": ["MUSKY"], "leffingwell": ["animal"]},
    # incense reads differently from burnt and tar notes in D85, so the two are kept apart
    "incense": {"dravnieks_1985": ["INCENSE"]},
    "burnt_tar": {"dravnieks_1985": ["BURNT,SMOKY", "FRESH TOBACCO SMOKE", "TAR", "CREOSOTE"], "keller_2016": ["BURNT"],
                  "leffingwell": ["smoky", "burnt", "tobacco", "phenolic"]},
    "leathery": {"dravnieks_1985": ["LEATHER"], "leffingwell": ["leathery"]},
    "earthy_musty": {"dravnieks_1985": ["MUSTY, EARTHY, MOLDY", "MUSHROOM", "RAW POTATO"], "leffingwell": ["earthy", "musty", "mushroom"]},
    "metallic": {"dravnieks_1985": ["METALLIC"], "leffingwell": ["metallic"]},
    "chemical_solvent": {"dravnieks_1985": ["CHEMICAL", "ETHERISH, ANAESTHETIC", "GASOLINE, SOLVENT", "CLEANING FLUID", "NAIL POLISH REMOVER", "PAINT"],
                         "keller_2016": ["CHEMICAL"], "leffingwell": ["solvent", "ethereal", "gasoline"]},
    "minty_camphor": {"dravnieks_1985": ["MINTY, PEPPERMINT", "CAMPHOR", "EUCALYPTUS"], "leffingwell": ["mint", "camphoreous"]},
    "soapy_aldehydic": {"dravnieks_1985": ["SOAPY"], "leffingwell": ["aldehydic", "waxy"]},
}
# Pole descriptors per dataset; a pole without a descriptor in a dataset is not measured there.
POLES = {
    "warm_cool": {"warm": {"dravnieks_1985": ["WARM"], "keller_2016": ["WARM"], "leffingwell": ["warm"]},
                  "cool": {"dravnieks_1985": ["COOL,COOLING"], "keller_2016": ["COLD"]}},
    "light_dense": {"light": {"dravnieks_1985": ["LIGHT"]}, "dense": {"dravnieks_1985": ["HEAVY"]}},
    "sweet_dry": {"sweet": {"dravnieks_1985": ["SWEET"], "keller_2016": ["SWEET"], "leffingwell": ["sweet"]},
                  "dry": {"leffingwell": ["dry"]}},
}
EXTRA = {"powdery": {"dravnieks_1985": ["DRY, POWDERY"]}}  # D85's 'DRY, POWDERY': reported, never the dry pole
STRONG, WEAK, ROBUST = 0.2, 0.1, 0.3
BOOT = 1000


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        dest = _path(f)
        if not dest.exists():
            with urllib.request.urlopen(BASE + f, timeout=120) as r:  # noqa: S310 (fixed https URL)
                dest.write_bytes(r.read())


def _path(f: str) -> Path:
    return CACHE / f.replace("/", "__")


def sha(f: str) -> str:
    return hashlib.sha256(_path(f).read_bytes()).hexdigest()


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def bootstrap(x: Sequence[float], y: Sequence[float], seed: str) -> List[float]:
    rng = random.Random(seed)  # deterministic per (dataset, family, pole)
    n = len(x)
    rs = []
    for _ in range(BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        r = pearson([x[i] for i in idx], [y[i] for i in idx])
        if not math.isnan(r):
            rs.append(r)
    rs.sort()
    return [round(rs[int(0.025 * len(rs))], 3), round(rs[int(0.975 * len(rs)) - 1], 3)]


def drop_top(x: Sequence[float], y: Sequence[float], k: int = 5) -> float:
    keep = sorted(range(len(x)), key=lambda i: -x[i])[k:]
    return pearson([x[i] for i in keep], [y[i] for i in keep])


def load():
    drows = list(csv.DictReader(_path("dravnieks_1985/behavior_1.csv").open(encoding="utf-8")))
    # KV16: per-stimulus mean per descriptor over subjects who smelled something; an unrated (NA)
    # descriptor of such a subject counts as 0 (not applicable). Pleasantness: mean of given ratings.
    wanted = {d for fam in FAMILIES.values() for d in fam.get("keller_2016", [])}
    wanted |= {d for ax in POLES.values() for pole in ax.values() for d in pole.get("keller_2016", [])}
    smelled, ratings, pleasant = set(), {}, defaultdict(list)
    with _path("keller_2016/behavior.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row["Stimulus"], row["Subject"])
            if row["MeasurementValue"] == "CAN OR CAN'T SMELL" and row["Value"] == "I smell something":
                smelled.add(key)
            elif row["MeasurementValue"] == "HOW PLEASANT IS THE SMELL?" and row["Value"] not in ("NA", ""):
                pleasant[row["Stimulus"]].append(float(row["Value"]))
            elif row["MeasurementValue"] in wanted and row["Value"] not in ("NA", ""):
                ratings[key + (row["MeasurementValue"],)] = float(row["Value"])
    sums: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    for stim, subj in sorted(smelled):
        for d in sorted(wanted):
            acc = sums[stim][d]
            acc[0] += ratings.get((stim, subj, d), 0.0)
            acc[1] += 1
    krows = [dict({d: v[0] / v[1] for d, v in ds.items()}, _pleasant=sum(pleasant[s]) / len(pleasant[s]))
             for s, ds in sorted(sums.items()) if pleasant.get(s)]
    lrows = [{k: int(v) for k, v in r.items() if k != "Stimulus"} for r in csv.DictReader(_path("leffingwell/behavior.csv").open(encoding="utf-8"))]
    return drows, krows, lrows


def measure(drows, krows, lrows) -> Dict[str, Dict[str, Dict[str, Dict[str, object]]]]:
    mean_d = lambda r, cols: sum(float(r[c] or 0) for c in cols) / len(cols)  # noqa: E731
    mean_k = lambda r, cols: sum(r[c] for c in cols) / len(cols)  # noqa: E731
    out: Dict[str, Dict[str, Dict[str, Dict[str, object]]]] = defaultdict(dict)
    poles = {f"{axis}:{pole}": per for axis, ps in POLES.items() for pole, per in ps.items()}
    poles.update({f"extra:{k}": v for k, v in EXTRA.items()})
    for pole_key, per in poles.items():
        for fam, cols in FAMILIES.items():
            cell = {}
            if "dravnieks_1985" in per and "dravnieks_1985" in cols:
                x = [mean_d(r, cols["dravnieks_1985"]) for r in drows]
                y = [mean_d(r, per["dravnieks_1985"]) for r in drows]
                top = sorted(range(len(x)), key=lambda i: (-x[i], drows[i]["Stimulus"]))[:5]
                cell["dravnieks_1985"] = {"r": round(pearson(x, y), 3), "ci95": bootstrap(x, y, f"d85|{fam}|{pole_key}"),
                                          "r_without_top5": round(drop_top(x, y), 3), "n": len(drows),
                                          "top_stimuli": [drows[i]["Stimulus"] for i in top]}
            if "keller_2016" in per and "keller_2016" in cols:
                x = [mean_k(r, cols["keller_2016"]) for r in krows]
                y = [mean_k(r, per["keller_2016"]) for r in krows]
                z = [r["_pleasant"] for r in krows]
                rxy, rxz, ryz = pearson(x, y), pearson(x, z), pearson(y, z)
                partial = (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
                cell["keller_2016"] = {"r": round(rxy, 3), "ci95": bootstrap(x, y, f"kv16|{fam}|{pole_key}"),
                                       "r_without_top5": round(drop_top(x, y), 3), "r_pleasantness_controlled": round(partial, 3),
                                       "n": len(krows)}
            if "leffingwell" in per and "leffingwell" in cols:
                fam_on = [int(any(r.get(c, 0) for c in cols["leffingwell"])) for r in lrows]
                pole_on = [int(any(r.get(c, 0) for c in per["leffingwell"])) for r in lrows]
                cell["leffingwell"] = {"phi": round(pearson(fam_on, pole_on), 3), "n": len(lrows),
                                       "family_count": sum(fam_on), "pole_count": sum(pole_on)}
            if cell:
                out[pole_key][fam] = cell
    return out


def classify_pole(cell: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    """Support of one family for one pole.

    supported: a rated dataset (D85, KV16) at r >= 0.2 whose bootstrap interval stays above 0 and
    whose r stays >= 0.1 without the five top stimuli; replicated when both rated datasets support
    it; contradicted (class none) when any dataset (LEF included, |phi| >= 0.1) is at <= -0.1.
    `less`: rated datasets at r <= -0.2 with the interval below 0 (the family is rated LESS on this
    pole; this is never support for the opposite pole). `weak_effect`: the smallest supporting r is
    below 0.3. `valence_robust`: KV16's partial r with pleasantness held constant stays >= 0.1
    (None when KV16 does not support this pole).
    """
    rated = {k: v for k, v in cell.items() if "r" in v and not math.isnan(v["r"])}
    support = {k: v for k, v in rated.items() if v["r"] >= STRONG and v["ci95"][0] > 0 and v["r_without_top5"] >= WEAK}
    against = [k for k, v in cell.items() if v.get("r", v.get("phi", 0)) <= -WEAK]
    less = {k: v for k, v in rated.items() if v["r"] <= -STRONG and v["ci95"][1] < 0}
    cls = ("replicated" if len(support) >= 2 else "single_dataset") if support and not against else "none"
    k = cell.get("keller_2016")
    return {"class": cls, "supporting": [SOURCES[d]["key"] for d in sorted(support)] if cls != "none" else [],
            "less": [SOURCES[d]["key"] for d in sorted(less)],
            "weak_effect": cls != "none" and min(v["r"] for v in support.values()) < ROBUST,
            "valence_robust": (k["r_pleasantness_controlled"] >= WEAK) if (cls != "none" and "keller_2016" in support) else None,
            "values": {SOURCES[d]["key"]: v.get("r", v.get("phi")) for d, v in sorted(cell.items())}}


def summarize(measured) -> Dict[str, Dict[str, Dict[str, object]]]:
    return {pole_key: {fam: classify_pole(cell) for fam, cell in fams.items()} for pole_key, fams in measured.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch", action="store_true", help="download the three datasets into data/external/pyrfume/")
    ap.add_argument("--write", help="write the aggregate evidence JSON here")
    args = ap.parse_args(argv)
    if args.fetch:
        fetch()
    missing = [f for f in FILES if not _path(f).exists()]
    if missing:
        print("missing datasets (run with --fetch): " + ", ".join(missing), file=sys.stderr)
        return 2
    measured = measure(*load())
    doc = {"evidence_version": "odor-axis-evidence-1.0", "provenance_category": "external_dataset_aggregate",
           "notice": "Associations between odor descriptors in published olfactory datasets, one pole descriptor at a time. "
                     "Not about brands; not causal. Supports only the odor-family -> pole step of MOTIF's imagery routes.",
           "sources": SOURCES, "files_sha256": {f: sha(f) for f in FILES}, "families": FAMILIES, "poles": POLES, "extra": EXTRA,
           "rule": classify_pole.__doc__.strip(), "thresholds": {"strong": STRONG, "weak": WEAK, "robust": ROBUST, "bootstrap": BOOT},
           "measurements": measured, "summary": summarize(measured)}
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        Path(args.write).write_text(text, encoding="utf-8")
    for pole_key, fams in doc["summary"].items():
        rows = [(f, s) for f, s in fams.items() if s["class"] != "none" or s["less"]]
        if rows:
            print(pole_key)
        for fam, s in sorted(rows, key=lambda kv: (kv[1]["class"], kv[0])):
            flags = " ".join(x for x in ("weak" if s["weak_effect"] else "",
                                         {True: "valence-robust", False: "NOT-valence-robust"}.get(s["valence_robust"], "")) if x)
            less = f" less:{','.join(s['less'])}" if s["less"] else ""
            print(f"   {fam:18s} {s['class']:15s} {s['values']} {flags}{less}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

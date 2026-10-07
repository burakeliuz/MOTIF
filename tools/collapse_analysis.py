"""Offline collapse diagnostic (reports/collapse_analysis.md).

Replays the stored Qloo responses of the 13 brands of reports/trial_6b.md through
the unchanged engine (RecordedQloo: no network, no LLM) and measures what each
stage keeps: Qloo input -> lexicon cues -> active motifs -> sensory targets ->
eligible materials -> selected materials. It changes no engine behaviour, rule,
lexicon, palette, or parameter; it only reads results and response bodies.

  python3 tools/collapse_analysis.py [--json OUT.json] [--markdown OUT.md]

Needs the git-ignored recordings under data/ (see BRANDS below).
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from motif.agent import Controller  # noqa: E402
from motif.config import AXES, load_config  # noqa: E402
from motif.qloo import RecordedQloo, related_argv  # noqa: E402
from motif_spike.adapter import OP_RELATED, locate_items  # noqa: E402

DATA = ROOT / "data"
STAGE2 = DATA / "raw" / "live-20261006T103307Z-660d"
T1 = sorted((DATA / "motif_sessions").glob("live-*"))
WEB = DATA / "web_sessions"
# brand -> (recording dirs, choose, conflict answer); the same inputs as reports/trial_6b.md
BRANDS = {
    "MUJI": ([STAGE2], None, None),
    "A24": ([STAGE2], None, None),
    "Comme des Garçons": ([STAGE2], None, None),
    "Nike": ([STAGE2], None, None),
    "Ralph Lauren": ([STAGE2], None, None),
    "Le Labo": (T1, "25C88914-2BC2-4E6B-A787-A8DD2DD4F45E", None),
    "Patagonia": (T1, None, None),
    "Aesop": ([WEB / "a1YBurE0Z2Ve"], None, None),
    "Supreme": ([WEB / "hHeC7lbfur3A"], None, None),
    "Gucci": ([WEB / "mp7uYelWeVwq"], None, None),
    "Harley-Davidson": ([WEB / "kf-9VYahIcn6"], None, None),
    "Sanrio": ([WEB / "JHfY12rK4CuE"], None, None),
    "Balenciaga": ([WEB / "YHii7QL_YRzh"], None, {"light_dense": "open"}),
}
DESCRIPTIVE_PROPERTIES = (
    "aesthetic_properties", "emotional_tone", "personal_style", "style_description", "core_values",
    "design_inspiration", "cultural_context_description", "cultural_relevance", "market_positioning",
    "lifestyle", "aspirational_lifestyle", "tagline", "emotional_tone_description", "plot_themes_description",
    "genre_description", "description", "short_description",
)
KIND_OF = {"urn:entity:brand": "brand", "urn:entity:movie": "movie", "urn:entity:artist": "artist"}
PAIRS = [("MUJI", "Aesop"), ("MUJI", "Le Labo"), ("Gucci", "Balenciaga"), ("A24", "Supreme"),
         ("Harley-Davidson", "Sanrio")]


def jaccard(a: frozenset, b: frozenset) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def run_brand(name: str, cfg) -> Dict[str, Any]:
    recs, choose, overrides = BRANDS[name]
    access = RecordedQloo(recs, None, 99)
    bodies: Dict[str, Any] = {}
    original = access.request

    def capture(operation, argv):
        rec = original(operation, argv)
        if rec.get("body") is not None:
            kind = "own" if operation != OP_RELATED else KIND_OF.get(argv[argv.index("--type") + 1], "other")
            if operation in ("seed_detail", OP_RELATED):
                bodies[kind] = rec["body"]
        return rec

    access.request = capture
    ctl = Controller(access, cfg, name, "brand", choose, overrides=overrides)
    out = ctl.run()
    access.request = original
    # recorded but outside the default domains (stage-2 run only); offline replay, never sent
    extra = {}
    entity_id = (out.get("resolution") or {}).get("qloo_id")
    if entity_id:
        rec = access.request(OP_RELATED, related_argv(entity_id, "urn:entity:artist", cfg.params["related_take"]))
        if rec.get("status") in ("ok", "ok_empty") and rec.get("body") is not None:
            extra["artist"] = rec["body"]
    return {"outcome": out, "bodies": bodies, "extra": extra,
            "skipped": [r["action"] for r in ctl.trace if r["decision"] == "skip"]}


def input_stats(result: Dict[str, Any], bodies: Dict[str, Any], extra: Dict[str, Any], namespaces) -> Dict[str, Any]:
    ev = result["evidence"]
    by_kind = Counter(e["source_kind"] for e in ev)
    entities = defaultdict(set)
    affinity = defaultdict(list)
    for e in ev:
        if e["source_kind"] != "own":
            entities[e["source_kind"]].add(e["entity_id"])
            if isinstance(e.get("relation_affinity"), (int, float)):
                affinity[e["source_kind"]].append(e["relation_affinity"])
    returned, tags_total, tags_used, unused_types, props = {}, Counter(), Counter(), Counter(), defaultdict(Counter)
    prop_examples: Dict[str, str] = {}
    dup = Counter()
    for kind, body in list(bodies.items()) + [("artist (recorded, not fetched)", b) for b in extra.values()]:
        base_kind = kind.split(" ")[0]
        allowed = set(namespaces.get(base_kind, []))
        items, _ = locate_items("seed_detail" if kind == "own" else OP_RELATED, body)
        returned[kind] = len(items)
        for _, ent in items:
            if not isinstance(ent, dict):
                continue
            used_names = set()
            for t in ent.get("tags") or []:
                if not isinstance(t, dict):
                    continue
                tags_total[kind] += 1
                if t.get("type") in allowed:
                    tags_used[kind] += 1
                    used_names.add(str(t.get("name", "")).lower())
                else:
                    unused_types[(kind, t.get("type"))] += 1
            p = ent.get("properties") or {}
            for key in DESCRIPTIVE_PROPERTIES:
                v = p.get(key)
                if not v:
                    continue
                n = len(v) if isinstance(v, list) else 1
                props[kind][key] += n
                prop_examples.setdefault(f"{kind}:{key}", (", ".join(map(str, v[:3])) if isinstance(v, list) else str(v))[:110])
                if isinstance(v, list) and key in ("aesthetic_properties", "emotional_tone", "personal_style"):
                    for x in v:
                        dup["already_a_consumed_tag" if str(x).lower() in used_names else "not_a_consumed_tag"] += 1
    return {
        "items": len(ev), "by_kind": dict(by_kind), "distinct_names": len({e["tag_name"].strip().lower() for e in ev}),
        "related_entities": {k: len(v) for k, v in entities.items()},
        "entities_returned": returned,
        "affinity": {k: (round(min(v), 3), round(max(v), 3)) for k, v in affinity.items()},
        "tags_total": dict(tags_total), "tags_used": dict(tags_used),
        "unused_types": {f"{k}|{t}": n for (k, t), n in unused_types.most_common(12)},
        "properties": {k: dict(v) for k, v in props.items()}, "property_examples": prop_examples,
        "property_vs_tags": dict(dup),
    }


def classification_stats(result: Dict[str, Any]) -> Dict[str, Any]:
    ev = {e["evidence_id"]: e for e in result["evidence"]}
    ann = result["annotations"]
    matched = {a["evidence_id"] for a in ann}
    roles = Counter(a["role"] for a in ann)
    motifs = {}
    for m, info in sorted(result["motifs"].items()):
        sup = [ev[i] for i in info["support_evidence_ids"] if i in ev]
        motifs[m] = {
            "strength": info["strength"], "active": info["active"], "source_kinds": info["source_kinds"],
            "support_items": len(sup),
            "distinct_entities": len({(e["source_kind"], e["entity_id"]) for e in sup}),
            "related_entities": len({(e["source_kind"], e["entity_id"]) for e in sup if e["source_kind"] != "own"}),
            "cue_groups": sorted({a["cue_id"] for a in ann if a["motif"] == m and a["role"] == "support"}),
            "counted_units": len(info["source_kinds"]),
            "context_items": len(info["context_evidence_ids"]), "excluded_items": len(info.get("excluded_evidence", [])),
        }
    return {"items": len(ev), "matched": len(matched), "unmatched": result["unclassified_evidence_count"],
            "roles": dict(roles),
            "cues_all": sorted({a["cue_id"] for a in ann}),
            "cues_support": sorted({a["cue_id"] for a in ann if a["role"] == "support"}),
            "motifs": motifs}


def material_stats(result: Dict[str, Any]) -> Dict[str, Any]:
    mats = result["materials"]
    return {"status": mats["status"],
            "targets": {a: v["value"] for a, v in result["axes"].items() if v["state"] == "target"},
            "ranked": [(m["material_id"], m["name"], m["score"], m["matches"]) for m in mats.get("ranked", [])],
            "excluded": [(m["material_id"], m.get("reason")) for m in mats.get("excluded", [])],
            "selected": [(m["material_id"], m.get("slot")) for m in mats.get("selected", [])]}


def stage_sets(result: Dict[str, Any], bodies, namespaces) -> Dict[str, frozenset]:
    own_all = set()
    for kind, body in bodies.items():
        items, _ = locate_items("seed_detail" if kind == "own" else OP_RELATED, body)
        for _, ent in items:
            for t in (ent.get("tags") or []) if isinstance(ent, dict) else []:
                if isinstance(t, dict) and str(t.get("type", "")).endswith(":qloo") and t.get("name"):
                    own_all.add((kind, str(t["name"]).lower()))
    ann = result["annotations"]
    return {
        "A0 Qloo descriptive tags (all :qloo types)": frozenset(n for _, n in own_all),
        "A Qloo evidence MOTIF consumes": frozenset(e["tag_name"].strip().lower() for e in result["evidence"]),
        "B lexicon cue groups matched": frozenset(a["cue_id"] for a in ann),
        "B' cue groups counted as support": frozenset(a["cue_id"] for a in ann if a["role"] == "support"),
        "C active motifs": frozenset(m for m, i in result["motifs"].items() if i["active"]),
        "D sensory targets": frozenset(f"{a}={v['value']}" for a, v in result["axes"].items() if v["state"] == "target"),
        "E eligible materials": frozenset(m["material_id"] for m in result["materials"].get("ranked", [])),
        "F selected materials": frozenset(m["material_id"] for m in result["materials"].get("selected", [])),
    }


def _pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def markdown(rep: Dict[str, Any], stages: List[str]) -> str:
    """Generated tables for reports/collapse_analysis.md (numbers only; the diagnosis is written by hand)."""
    B = rep["brands"]
    L: List[str] = []
    w = L.append
    # pooled totals
    tot = Counter()
    for b in B.values():
        i, c, t = b["input"], b["classification"], b["translation"]
        for k, v in i["tags_total"].items():
            if "artist" not in k:
                tot["tags_returned"] += v
        for k, v in i["tags_used"].items():
            if "artist" not in k:
                tot["tags_consumed"] += v
        tot["items"] += i["items"]
        tot["matched"] += c["matched"]
        tot["support_items"] += c["roles"].get("support", 0)
        tot["active"] += len(t["active"])
        tot["mapped"] += len(t["mapped"])
        for x in c["motifs"].values():
            if x["support_items"]:
                tot["motif_support_items"] += x["support_items"]
                tot["motif_entities"] += x["distinct_entities"]
                tot["motif_units"] += x["counted_units"]
    w("### G.1 Pooled retention (13 brands)\n")
    w("| Measure | Value |\n|---|---|")
    w(f"| Tags returned on the fetched entities (all types) | {tot['tags_returned']} |")
    w(f"| Tags in the namespaces MOTIF reads (evidence items before dedup) | {tot['tags_consumed']} ({_pct(tot['tags_consumed'], tot['tags_returned'])}) |")
    w(f"| Evidence items after dedup | {tot['items']} |")
    w(f"| Items matching any lexicon cue | {tot['matched']} ({_pct(tot['matched'], tot['items'])} of items) |")
    w(f"| Annotations counted as support (non-common, not excluded) | {tot['support_items']} |")
    w(f"| Support items → distinct entities → counted units (source kinds) | {tot['motif_support_items']} → {tot['motif_entities']} → {tot['motif_units']} |")
    w(f"| Active motifs → motifs with a rule | {tot['active']} → {tot['mapped']} ({_pct(tot['mapped'], tot['active'])}) |\n")

    w("### G.2 Per brand: Qloo input\n")
    w("| Brand | Evidence items (own / brand / movie) | Distinct names | Related entities (brand / movie) | Affinity range (report only) | Tags returned → read | Descriptive properties not read (brand entities) |")
    w("|---|---|---|---|---|---|---|")
    for n, b in B.items():
        i = b["input"]
        k = i["by_kind"]
        ret = sum(v for kk, v in i["tags_total"].items() if "artist" not in kk)
        used = sum(v for kk, v in i["tags_used"].items() if "artist" not in kk)
        aff = "; ".join(f"{kk} {a}-{z}" for kk, (a, z) in i["affinity"].items())
        bp = i["properties"].get("brand", {})
        props = ", ".join(f"{kk} {v}" for kk, v in bp.items() if kk in ("style_description", "core_values", "design_inspiration", "cultural_context_description", "personal_style"))
        w(f"| {n} | {i['items']} ({k.get('own', 0)} / {k.get('brand', 0)} / {k.get('movie', 0)}) | {i['distinct_names']} | "
          f"{i['related_entities'].get('brand', 0)} / {i['related_entities'].get('movie', 0)} | {aff or 'n/a'} | {ret} → {used} ({_pct(used, ret)}) | {props or 'none'} |")
    w("")
    w("### G.3 Per brand: classification retention\n")
    w("| Brand | Matched / items | Unmatched | Cue groups (all / support) | Motifs seen (strength) | Active |")
    w("|---|---|---|---|---|---|")
    for n, b in B.items():
        c = b["classification"]
        seen = ", ".join(f"{m} ({x['strength']})" for m, x in c["motifs"].items())
        act = ", ".join(m for m, x in c["motifs"].items() if x["active"]) or "none"
        w(f"| {n} | {c['matched']} / {c['items']} ({_pct(c['matched'], c['items'])}) | {c['unmatched']} | "
          f"{len(c['cues_all'])} / {len(c['cues_support'])} | {seen} | {act} |")
    w("")
    w("### G.4 Per motif: what the support count keeps (active and candidate motifs)\n")
    w("Support items = matching evidence items; entities = distinct entities carrying them; "
      "units = what the strength rule counts (distinct source kinds).\n")
    w("| Brand | Motif | Strength | Source kinds | Support items | Distinct entities (related) | Cue groups | Counted units |")
    w("|---|---|---|---|---|---|---|---|")
    for n, b in B.items():
        for m, x in b["classification"]["motifs"].items():
            if x["support_items"] == 0:
                continue
            w(f"| {n} | {m} | {x['strength']} | {', '.join(x['source_kinds'])} | {x['support_items']} | "
              f"{x['distinct_entities']} ({x['related_entities']}) | {len(x['cue_groups'])} | {x['counted_units']} |")
    w("")
    w("### G.5 Per brand: translation retention\n")
    w("| Brand | Active | Mapped | Unmapped | Targets | Unknown axes | Conflicted | Retention |")
    w("|---|---|---|---|---|---|---|---|")
    for n, b in B.items():
        t = b["translation"]
        tg = ", ".join(f"{a}={v}" for a, v in t["targets"].items()) or "none"
        w(f"| {n} | {', '.join(t['active']) or 'none'} | {', '.join(t['mapped']) or 'none'} | {', '.join(t['unmapped']) or 'none'} | "
          f"{tg} | {len(t['unknown'])} | {', '.join(t['conflicted']) or 'none'}{' (left open)' if n == 'Balenciaga' else ''} | "
          f"{len(t['mapped'])}/{len(t['active'])} |")
    w("")
    w("### G.6 Per brand: material retention (brands with targets)\n")
    w("| Brand | Targets | Eligible (score; matches) | Excluded (reason) | Selected | Status |")
    w("|---|---|---|---|---|---|")
    for n, b in B.items():
        m = b["materials"]
        if not m["targets"]:
            continue
        el = "; ".join(f"{i} {s:.3f} ({', '.join(x.split('_')[0] + '/' + x.split('_')[1] for x in mt)})" for i, _, s, mt in m["ranked"]) or "none"
        ex = "; ".join(f"{i} ({r})" for i, r in m["excluded"])
        sel = ", ".join(f"{i} {s}" for i, s in m["selected"]) or "none"
        tg = ", ".join(f"{a}={v}" for a, v in m["targets"].items())
        w(f"| {n} | {tg} | {el} | {ex} | {sel} | {m['status']} |")
    w("")
    w("### G.7 Cross-brand comparison by stage\n")
    w("Jaccard of two empty sets is counted as 1 (identical); the second mean leaves out pairs where either set is empty.\n")
    w("| Stage | Unique profiles / 13 | Identical groups | Empty sets | Mean pairwise Jaccard | Mean (non-empty pairs) |")
    w("|---|---|---|---|---|---|")
    for st in stages:
        c = rep["cross"][st]
        groups = "; ".join(" = ".join(g) for g, _ in c["identical_groups"]) or "none"
        w(f"| {st} | {c['unique']} | {groups} | {len(c['empty'])} | {c['mean_jaccard']} | {c['mean_jaccard_nonempty']} |")
    w("")
    w("### G.8 Named pairs: Jaccard similarity by stage\n")
    short = [s.split(" ")[0] for s in stages]
    w("| Pair | " + " | ".join(short) + " |")
    w("|---|" + "---|" * len(short))
    for pair, vals in rep["named_pairs"].items():
        w(f"| {pair} | " + " | ".join(f"{vals[s]:.2f}" for s in stages) + " |")
    w("")
    w("Stage keys: " + "; ".join(stages) + ".\n")
    w("### G.9 First stage at which a pair becomes identical\n")
    by_stage = defaultdict(list)
    for pair, st in rep["first_identical"].items():
        by_stage[st].append(pair)
    w("| Stage | Pairs that first become identical here |")
    w("|---|---|")
    for st in stages:
        if by_stage.get(st):
            w(f"| {st} | {'; '.join(by_stage[st])} |")
    w("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--markdown")
    args = ap.parse_args()
    cfg = load_config()
    ns = cfg.lexicon["match"]["namespaces"]
    rules = {r["motif"] for r in cfg.rules["rules"]}
    data, sets = {}, {}
    for name in BRANDS:
        run = run_brand(name, cfg)
        r = run["outcome"]["result"]
        data[name] = {"outcome": r["outcome"], "skipped": run["skipped"],
                      "input": input_stats(r, run["bodies"], run["extra"], ns),
                      "classification": classification_stats(r),
                      "translation": {
                          "active": sorted(m for m, i in r["motifs"].items() if i["active"]),
                          "mapped": sorted(m for m, i in r["motifs"].items() if i["active"] and m in rules),
                          "unmapped": r["unmapped_active_motifs"],
                          "targets": {a: v["value"] for a, v in r["axes"].items() if v["state"] == "target"},
                          "unknown": [a for a in AXES if r["axes"][a]["state"] == "unknown"],
                          "conflicted": [a for a in AXES if r["axes"][a]["state"] == "conflicted"]},
                      "materials": material_stats(r)}
        sets[name] = stage_sets(r, run["bodies"], ns)
    names = list(BRANDS)
    stages = list(next(iter(sets.values())).keys())
    cross = {}
    for st in stages:
        groups = defaultdict(list)
        for n in names:
            groups[sets[n][st]].append(n)
        pairs = list(itertools.combinations(names, 2))
        cross[st] = {
            "unique": len(groups),
            "identical_groups": [(g, sorted(k)[:6]) for k, g in groups.items() if len(g) > 1],
            "empty": [n for n in names if not sets[n][st]],
            "mean_jaccard": round(sum(jaccard(sets[a][st], sets[b][st]) for a, b in pairs) / len(pairs), 3),
            "mean_jaccard_nonempty": (lambda ps: round(sum(jaccard(sets[a][st], sets[b][st]) for a, b in ps) / len(ps), 3) if ps else None)(
                [(a, b) for a, b in pairs if sets[a][st] and sets[b][st]]),
            "sizes": {n: len(sets[n][st]) for n in names},
        }
    first_identical = {}
    for a, b in itertools.combinations(names, 2):
        hit = next((st for st in stages if sets[a][st] == sets[b][st]), None)
        if hit:
            first_identical[f"{a} | {b}"] = hit
    named = {f"{a} vs {b}": {st: round(jaccard(sets[a][st], sets[b][st]), 3) for st in stages} for a, b in PAIRS}
    report = {"brands": data, "cross": cross, "first_identical": first_identical, "named_pairs": named}
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1, ensure_ascii=False, default=list), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(markdown(report, stages), encoding="utf-8")
    print(json.dumps({"cross": cross, "first_identical": first_identical, "named_pairs": named}, indent=1,
                     ensure_ascii=False, default=list))
    return 0


if __name__ == "__main__":
    sys.exit(main())

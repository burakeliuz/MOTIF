"""Factual cross-seed comparisons over normalized observations.

Only identifiers returned by Qloo are compared: two items are "the same" only
when their returned IDs are equal, never because their names look alike.
Scores are summarized per field and never averaged across requests: Qloo
documents affinity as normalized per query. Tag shares are computed inside the
retrieved top-N samples and labelled as such; they are not population lift.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from statistics import median
from typing import Any, Dict, List

from .adapter import OP_RELATED, OP_SEED_TAGS

COMPARISON_NOTES = [
    "Overlap and recurrence use returned Qloo IDs only; display names are never matched or merged.",
    "Only requests with identical comparability parameters (operation, entity type, take, explainability or limit) are compared.",
    "Affinity and popularity are reported as returned; they are not percentages of people, confidence, or scent suitability, and are not averaged across requests.",
    "Sample shares compare tag frequency inside the retrieved top-N results of seeds in the same comparable group. They are not lift: there is no population denominator.",
]


def _unique_items(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [o for o in observations if o.get("duplicate_of") is None and o.get("qloo_id") is not None]


def _popularity(obs: Dict[str, Any]):
    for score in obs.get("scores", []):
        if score["field"] == "popularity":
            return score["value"]
    return None


def _groups(records: List[Dict[str, Any]], observations: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_request = defaultdict(list)
    for obs in observations:
        by_request[obs["request_id"]].append(obs)
    groups: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        if rec["operation"] not in (OP_RELATED, OP_SEED_TAGS) or rec["status"] not in ("ok", "ok_empty"):
            continue
        key = json.dumps(rec.get("comparability", {}), sort_keys=True)
        group = groups.setdefault(key, {"comparability": rec.get("comparability", {}), "seeds": {}})
        group["seeds"][rec["seed_key"]] = _unique_items(by_request[rec["request_id"]])
    return groups


def _overlap(group: Dict[str, Any]) -> Dict[str, Any]:
    seeds = sorted(group["seeds"])
    sets = {s: {o["qloo_id"] for o in group["seeds"][s]} for s in seeds}
    names = {o["qloo_id"]: o.get("name") for s in seeds for o in group["seeds"][s]}
    popularity = {o["qloo_id"]: _popularity(o) for s in seeds for o in group["seeds"][s] if _popularity(o) is not None}

    pairwise = []
    for i, a in enumerate(seeds):
        for b in seeds[i + 1:]:
            union = sets[a] | sets[b]
            inter = sets[a] & sets[b]
            pairwise.append({
                "a": a, "b": b, "intersection": len(inter), "union": len(union),
                "jaccard": round(len(inter) / len(union), 4) if union else None,
            })
    frequency = Counter(i for s in seeds for i in sets[s])
    n = len(seeds)
    shared_all = sorted(i for i, c in frequency.items() if c == n) if n >= 2 else []
    pop_by_k = {}
    for k in sorted(set(frequency.values())):
        values = [popularity[i] for i, c in frequency.items() if c == k and i in popularity]
        pop_by_k[str(k)] = {"ids": sum(1 for c in frequency.values() if c == k), "with_popularity": len(values),
                            "median_popularity": round(median(values), 6) if values else None}
    return {
        "comparability": group["comparability"],
        "seeds": seeds,
        "result_counts": {s: len(sets[s]) for s in seeds},
        "seeds_with_zero_results": [s for s in seeds if not sets[s]],
        "pairwise": pairwise,
        "appearance_distribution": {str(k): v for k, v in sorted(Counter(frequency.values()).items())},
        "shared_by_all_seeds": [{"qloo_id": i, "name": names.get(i)} for i in shared_all],
        "share_of_each_seed_shared_by_all": {
            s: round(len(sets[s] & set(shared_all)) / len(sets[s]), 4) if sets[s] and n >= 2 else None for s in seeds
        },
        "popularity_by_appearance_count": pop_by_k,
    }


def _sample_tag_shares(group: Dict[str, Any], top: int = 8) -> Dict[str, Any]:
    seeds = sorted(group["seeds"])
    # Each seed is counted from its own observations. An entity in the pooled
    # sample carries a tag if any observation of it in this group returned that tag.
    seed_entity_tags: Dict[str, Dict[Any, set]] = {}
    pooled: Dict[Any, set] = {}
    tag_meta: Dict[Any, Dict[str, Any]] = {}
    for s in seeds:
        seed_entity_tags[s] = {}
        for o in group["seeds"][s]:
            tags = {t["id"] for t in o.get("tags", []) or [] if t.get("id") is not None}
            seed_entity_tags[s][o["qloo_id"]] = tags
            pooled.setdefault(o["qloo_id"], set()).update(tags)
            for t in o.get("tags", []) or []:
                if t.get("id") is not None:
                    tag_meta.setdefault(t["id"], {"name": t.get("name"), "type": t.get("type")})
    pooled_n = len(pooled)
    pooled_k = Counter(t for tags in pooled.values() for t in tags)
    per_seed = {}
    for s in seeds:
        n = len(seed_entity_tags[s])
        k = Counter(t for tags in seed_entity_tags[s].values() for t in tags)
        rows = []
        for tag_id, count in k.items():
            seed_share = count / n
            pooled_share = pooled_k[tag_id] / pooled_n
            rows.append({
                "tag_id": tag_id, **tag_meta.get(tag_id, {}), "k": count, "n": n,
                "K_pooled": pooled_k[tag_id], "N_pooled": pooled_n,
                "sample_enrichment": round(seed_share / pooled_share, 3) if pooled_share else None,
            })
        rows.sort(key=lambda r: (-r["k"], -(r["sample_enrichment"] or 0), str(r["tag_id"])))
        per_seed[s] = rows[:top]
    return {"comparability": group["comparability"], "seeds": seeds, "pooled_unique_entities": pooled_n, "per_seed": per_seed}


def _cross_domain_tags(observations: List[Dict[str, Any]], top: int = 12) -> Dict[str, Any]:
    per_seed: Dict[str, Dict[Any, Dict[str, Any]]] = defaultdict(dict)
    domains_seen: Dict[str, set] = defaultdict(set)
    for o in _unique_items([o for o in observations if o["query_context"]["operation"] == OP_RELATED]):
        seed = o["query_context"]["seed_key"]
        domain = o["query_context"]["domain_key"]
        domains_seen[seed].add(domain)
        for tag in o.get("tags", []) or []:
            if tag.get("id") is None:
                continue
            entry = per_seed[seed].setdefault(tag["id"], {"name": tag.get("name"), "type": tag.get("type"), "domains": set(), "entities": set()})
            entry["domains"].add(domain)
            entry["entities"].add(o["qloo_id"])
    out = {}
    for seed, tags in per_seed.items():
        recurring = [
            {"tag_id": tag_id, "name": e["name"], "type": e["type"], "domains": sorted(e["domains"]), "entity_count": len(e["entities"])}
            for tag_id, e in tags.items()
            if len(e["domains"]) >= 2
        ]
        recurring.sort(key=lambda r: (-len(r["domains"]), -r["entity_count"], str(r["tag_id"])))
        out[seed] = {
            "domains_with_results": sorted(domains_seen[seed]),
            "distinct_tag_ids": len(tags),
            "tag_ids_in_two_or_more_domains": len(recurring),
            "top_recurring": recurring[:top],
        }
    return out


def _score_inventory(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    inventory: Dict[tuple, Dict[str, Any]] = {}
    for o in observations:
        for score in o.get("scores", []):
            key = (o["kind"], score["field"])
            entry = inventory.setdefault(key, {"kind": o["kind"], "field": score["field"], "count": 0, "min": None, "max": None, "requests": set()})
            value = score["value"]
            entry["count"] += 1
            entry["min"] = value if entry["min"] is None else min(entry["min"], value)
            entry["max"] = value if entry["max"] is None else max(entry["max"], value)
            entry["requests"].add(o["request_id"])
    rows = []
    for entry in inventory.values():
        entry = dict(entry)
        entry["requests"] = len(entry["requests"])
        rows.append(entry)
    return sorted(rows, key=lambda r: (r["kind"], r["field"]))


def compare(normalized: Dict[str, Any]) -> Dict[str, Any]:
    records = normalized["requests"]
    observations = normalized["observations"]
    groups = _groups(records, observations)
    related = [g for g in groups.values() if g["comparability"].get("operation") == OP_RELATED]
    tags = [g for g in groups.values() if g["comparability"].get("operation") == OP_SEED_TAGS]
    with_results = [g for g in related if sum(1 for items in g["seeds"].values() if items) >= 2]
    return {
        "record_type": "comparison",
        "run_id": normalized["run"]["run_id"],
        "synthetic": bool(normalized["run"].get("synthetic")),
        "notes": COMPARISON_NOTES,
        "related_entity_overlap": [_overlap(g) for g in related],
        "tag_insight_overlap": [_overlap(g) for g in tags],
        "sample_tag_shares": [_sample_tag_shares(g) for g in with_results],
        "cross_domain_tag_recurrence": _cross_domain_tags(observations),
        "score_inventory": _score_inventory(observations),
    }

"""Small, shareable evidence excerpt of one live run (Markdown).

Raw and normalized run data stay in git-ignored `data/`. This excerpt copies a
bounded selection of literal returned values into a file that can be committed
(for example `reports/evidence_excerpt.md`), each with the local request ID and
JSON Pointer it came from. It adds no interpretation, merges nothing by display
name, and never includes credentials (none are stored in the run data).
Synthetic runs are refused: synthetic data is never evidence.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from .util import RunPaths, read_json, read_jsonl

# Namespaces of the seed's own tags that are copied in full (others are counted).
SEED_DESCRIPTOR_TYPES = (
    "urn:tag:aesthetic_property:qloo",
    "urn:tag:personal_style:qloo",
    "urn:tag:emotional_tone:qloo",
    "urn:tag:core_value:qloo",
    "urn:tag:market_archetype:qloo",
    "urn:tag:keyword:qloo",
    "urn:tag:cultural_relevance:qloo",
)
# Per related-entity domain: tag namespaces shown, and literal properties shown.
RELATED_DESCRIPTOR_TAGS = {
    "brand": ("urn:tag:aesthetic_property:qloo",),
    "movie": ("urn:tag:style:qloo",),
    "artist": ("urn:tag:style:qloo",),
    "book": ("urn:tag:style:qloo",),
    "person": ("urn:tag:occupation:person",),
    "place": ("urn:tag:ambience:qloo", "urn:tag:decor:qloo"),
}
RELATED_DESCRIPTOR_PROPERTIES = {"brand": ("emotional_tone",)}
RELATED_PER_DOMAIN = 3
TAGS_PER_ENTITY = 6
TAG_INSIGHTS_SHOWN = 10


def _short(request_id: str) -> str:
    return request_id.replace("local:req:", "req ")


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _affinity(obs: Dict[str, Any]) -> Optional[Any]:
    for score in obs.get("scores", []):
        if score["field"] in ("query.affinity", "affinity"):
            return score["value"]
    return None


def _quote(values: List[Any]) -> str:
    return ", ".join(f'"{_cell(v)}"' for v in values) if values else "none returned"


def render_excerpt(paths: RunPaths) -> str:
    norm = paths.normalized_dir
    run = read_json(norm / "run.json")
    if run.get("synthetic") or run.get("mode") != "live":
        raise ValueError("evidence excerpts are built from live runs only; synthetic data is never evidence")
    resolutions = read_json(norm / "seed_resolutions.json")
    observations = read_jsonl(norm / "observations.jsonl")
    comparison = read_json(norm / "comparison.json")
    requests = {r["request_id"]: r for r in read_jsonl(paths.requests_log)}

    by_request: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        by_request[obs["request_id"]].append(obs)

    plan = run.get("plan", {})
    base_url = (plan.get("harness_env") or {}).get("QLOO_BASE_URL")
    lines = [
        f"# MOTIF evidence excerpt: run `{run['run_id']}`",
        "",
        "Provenance category: `qloo_observation`. Every value below is copied literally from a live Qloo "
        "response; nothing is inferred, translated, or merged by display name. MOTIF adds no motif, axis, "
        "or scent judgment here (see `reports/feasibility.md` for judgments, kept separate).",
        "",
        f"- Run: `{run['run_id']}` (plan `{run.get('plan_name')}`, {run.get('started_at')} to {run.get('finished_at')} UTC)",
        f"- Base URL: {base_url}; transport: {run.get('versions', {}).get('transport')}",
        f"- Parser status at normalization: {(run.get('normalization') or {}).get('parser_status')}",
        f"- Selection: seed resolution; the seed's own tags in {len(SEED_DESCRIPTOR_TYPES)} descriptive namespaces "
        f"(other namespaces counted only); top {RELATED_PER_DOMAIN} related entities per domain with at most "
        f"{TAGS_PER_ENTITY} descriptor tags each; top {TAG_INSIGHTS_SHOWN} tag insights per seed.",
        "- `req NNNN` is the run's local request ID (table at the end). Pointers are JSON Pointers into that "
        "request's saved response, which stays in git-ignored `data/raw/`.",
        "- Affinity and popularity are copied as returned. They are not percentages of people, confidence, "
        "or scent suitability, and are not comparable across requests.",
        "",
    ]

    obs_by_seed_op: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        ctx = obs["query_context"]
        obs_by_seed_op[(ctx.get("seed_key"), ctx["operation"], ctx.get("domain_key"))].append(obs)

    lines += ["## 1. Seed resolution", "",
              "| Seed input | Status | Returned name | Returned ID | Returned types | Source |", "|---|---|---|---|---|---|"]
    for res in resolutions:
        lines.append(f"| {_cell(res.get('input_name'))} | {res.get('status')} | {_cell(res.get('name'))} | "
                     f"`{res.get('qloo_id')}` | {', '.join(res.get('types') or [])} | "
                     f"{_short(res['search_request_id']) if res.get('search_request_id') else '—'} |")
    lines.append("")

    for res in resolutions:
        key = res["seed_key"]
        lines += [f"## Seed `{key}` ({_cell(res.get('input_name'))})", ""]
        detail = obs_by_seed_op.get((key, "seed_detail", None), [])
        if detail:
            seed = detail[0]
            req, ptr = _short(seed["request_id"]), seed["pointer"]
            desc = (seed.get("attributes") or {}).get("short_description")
            if desc is not None:
                lines.append(f"- `properties.short_description` ({req} `{ptr}/properties/short_description`): \"{_cell(desc)}\"")
            grouped: Dict[str, List[str]] = defaultdict(list)
            for tag in seed.get("tags") or []:
                grouped[tag.get("type") or "(no type)"].append(tag.get("name"))
            lines.append(f"- Own tags by namespace ({req} `{ptr}/tags`):")
            for tag_type in SEED_DESCRIPTOR_TYPES:
                lines.append(f"  - `{tag_type}`: {_quote(grouped.get(tag_type, []))}")
            others = sorted((t, len(v)) for t, v in grouped.items() if t not in SEED_DESCRIPTOR_TYPES)
            lines.append("  - other namespaces (count only): " + ", ".join(f"`{t}` {n}" for t, n in others))
        lines.append("")

        for domain in [d["key"] for d in plan.get("domains", [])]:
            related = obs_by_seed_op.get((key, "related_entities", domain), [])
            if not related:
                continue
            tag_types = RELATED_DESCRIPTOR_TAGS.get(domain, ())
            props = RELATED_DESCRIPTOR_PROPERTIES.get(domain, ())
            shown = " + ".join([f"`{t}` tags" for t in tag_types] + [f"`properties.{p}`" for p in props])
            lines.append(f"**Related {domain}** ({_short(related[0]['request_id'])}, {len(related)} returned; "
                         f"top {RELATED_PER_DOMAIN}; shown: {shown})")
            lines.append("")
            for obs in related[:RELATED_PER_DOMAIN]:
                names = [t.get("name") for t in obs.get("tags") or [] if t.get("type") in tag_types][:TAGS_PER_ENTITY]
                parts = [f"tags {_quote(names)}"]
                for prop in props:
                    value = (obs.get("attributes") or {}).get(prop)
                    if value is not None:
                        parts.append(f"{prop} {_quote(value if isinstance(value, list) else [value])}")
                lines.append(f"- #{obs['rank']} {_cell(obs.get('name'))} (affinity {_affinity(obs)}; `{obs['pointer']}`): "
                             + "; ".join(parts))
            lines.append("")

        insights = obs_by_seed_op.get((key, "seed_tags", None), [])
        if insights:
            lines.append(f"**Tag insights** ({_short(insights[0]['request_id'])}, `filter.type=urn:tag`, no namespace "
                         f"filter; top {TAG_INSIGHTS_SHOWN} of {len(insights)})")
            lines.append("")
            lines.append("| Rank | Name | Namespace (`subtype`) | Affinity | Pointer |")
            lines.append("|---|---|---|---|---|")
            for obs in insights[:TAG_INSIGHTS_SHOWN]:
                lines.append(f"| {obs['rank']} | {_cell(obs.get('name'))} | {(obs.get('types') or {}).get('subtype')} | "
                             f"{_affinity(obs)} | `{obs['pointer']}` |")
            lines.append("")

    lines += ["## Cross-seed checks (returned IDs only)", ""]
    own: Dict[str, Dict[str, Any]] = {}
    for obs in observations:
        if obs["kind"] != "seed_entity":
            continue
        for tag in obs.get("tags") or []:
            if tag.get("type") in SEED_DESCRIPTOR_TYPES and tag.get("id"):
                entry = own.setdefault(tag["id"], {"name": tag.get("name"), "seeds": set()})
                entry["seeds"].add(obs["query_context"]["seed_key"])
    shared = sorted(((tid, e) for tid, e in own.items() if len(e["seeds"]) > 1), key=lambda x: (-len(x[1]["seeds"]), x[0]))
    lines.append("Own descriptive tag IDs carried by more than one seed (same ID; similar names under different IDs are not merged):")
    lines.append("")
    if shared:
        lines += ["| Tag ID | Name | Seeds |", "|---|---|---|"]
        lines += [f"| `{tid}` | {_cell(e['name'])} | {', '.join(sorted(e['seeds']))} |" for tid, e in shared]
    else:
        lines.append("None.")
    lines += ["", "Related-entity overlap between seeds (pairs with at least one shared returned ID; all other pairs share none):", ""]
    lines += ["| Domain request | Seed pair | Shared IDs | Union |", "|---|---|---|---|"]
    for group in comparison.get("related_entity_overlap", []) + comparison.get("tag_insight_overlap", []):
        label = group["comparability"].get("entity_type") or group["comparability"]["operation"]
        for pair in group["pairwise"]:
            if pair["intersection"]:
                lines.append(f"| {label} | {pair['a']} / {pair['b']} | {pair['intersection']} | {pair['union']} |")
    lines.append("")

    lines += ["## Requests cited", "",
              "Exact non-secret request of each cited local ID (GET; the credential is added by the environment and never stored).",
              "", "| Request | Operation | Path | Parameters | Status | Reused from |", "|---|---|---|---|---|---|"]
    for rid in sorted(by_request):
        rec = requests.get(rid, {})
        preview = rec.get("api_request_preview") or {}
        url = preview.get("url") or ""
        path = url[len(base_url):] if base_url and url.startswith(base_url) else url
        params = "&".join(f"{k}={v}" for k, v in sorted((preview.get("params") or {}).items()))
        reused = (rec.get("reused_from") or {}).get("run_id") or "—"
        lines.append(f"| {_short(rid)} | {rec.get('operation')} {rec.get('domain_key') or ''} | `{path}` | `{_cell(params)}` | "
                     f"{rec.get('status')} | {reused} |")
    lines.append("")
    return "\n".join(lines)

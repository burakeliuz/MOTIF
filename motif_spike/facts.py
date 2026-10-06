"""Render a run's facts sheet (Markdown). Facts only: no verdict, no interpretation.

Judgments (descriptive sufficiency, differentiation, recommendation) belong in
reports/feasibility.md and are written by a person after reading this sheet.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

from .adapter import OP_RELATED, OP_SEED_DETAIL, OP_SEED_TAGS, PARSER_BASIS, STATUS_MEANINGS

SYNTHETIC_BANNER = (
    "> **SYNTHETIC FIXTURE RUN: NOT QLOO DATA.** Every entity, tag, score, and ID below was invented "
    "locally to exercise the pipeline. It is not evidence about Qloo, the seed identities, or MOTIF feasibility."
)


def _cell(value: Any, limit: int = 60) -> str:
    if value is None:
        return "—"
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _table(headers: List[str], rows: Iterable[List[Any]]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return lines


def _score(obs: Dict[str, Any], field: str) -> Optional[Any]:
    for score in obs.get("scores", []):
        if score["field"] == field:
            return score["value"]
    return None


def _affinity(obs: Dict[str, Any]) -> Optional[Any]:
    value = _score(obs, "query.affinity")
    return value if value is not None else _score(obs, "affinity")


def _ref(obs: Dict[str, Any]) -> str:
    return f"`{obs['raw_ref']['file']}#{obs['raw_ref']['pointer']}`"


def _tags_inline(obs: Dict[str, Any], limit: int = 6) -> str:
    tags = obs.get("tags") or []
    shown = [f"{t.get('name') or t.get('id') or t.get('literal')} [{t.get('type') or 'no type'}]" for t in tags[:limit]]
    more = f" (+{len(tags) - limit} more)" if len(tags) > limit else ""
    return ("; ".join(shown) + more) if shown else "no tags returned"


def render_facts(normalized: Dict[str, Any], comparison: Dict[str, Any]) -> str:
    run = normalized["run"]
    synthetic = bool(run.get("synthetic"))
    versions = run.get("versions", {})
    base_url = (run.get("plan", {}).get("harness_env") or {}).get("QLOO_BASE_URL")
    lines: List[str] = [f"# MOTIF Qloo spike: run facts `{run['run_id']}`", ""]
    if synthetic:
        lines += [SYNTHETIC_BANNER, ""]
    lines += _table(["Field", "Value"], [
        ["Mode", run["mode"] + (f" (scenario: {run.get('scenario')})" if run.get("scenario") else "")],
        ["Plan", run.get("plan_name")],
        ["Run status", run.get("status")],
        ["Live execution status", run.get("live_execution_status")],
        ["Abort reason", run.get("abort_reason")],
        ["Started / finished (UTC)", f"{run.get('started_at')} / {run.get('finished_at')}"],
        ["Transport", versions.get("transport")],
        ["Harness version", versions.get("harness")],
        ["Harness base URL", base_url or ("not applicable" if synthetic else "harness default")],
        ["Adapter / parser status", f"{versions.get('adapter')} / {versions.get('parser_status')}"],
        ["Manifest version", versions.get("manifest")],
        ["Draft rule registry", f"{versions.get('draft_rule_registry')} (inactive draft; not applied by the spike)"],
        ["Feasibility verdict", "not_evaluated (this sheet lists facts only)"],
    ])
    lines += ["", f"Parser basis: {PARSER_BASIS}.", ""]
    if base_url and not synthetic and versions.get("transport") == "harness":
        lines += [f"Requests went to `{base_url}`. The harness's `--dry-run` previews print its configured or default "
                  "base URL instead, so preview URLs in the request log can differ from the address actually used.", ""]

    # 1. seed resolution ---------------------------------------------------
    lines += ["## 1. Seed resolution", ""]
    lines += _table(
        ["Seed", "Input", "Status", "Method", "Returned ID", "Returned name", "Returned types", "Candidates"],
        [[r["seed_key"], r.get("input_name"), r.get("status"), r.get("method"), r.get("qloo_id"), r.get("name"),
          ", ".join(r.get("types") or []) or None, r.get("candidates_returned")] for r in normalized["resolutions"]],
    )
    for r in normalized["resolutions"]:
        for label in ("alternatives", "near_matches"):
            items = r.get(label) or []
            if items:
                listed = "; ".join(f"{_cell(i.get('name'), 40)} ({_cell(i.get('qloo_id'), 40)}, {', '.join(i.get('types') or []) or 'no type'})" for i in items)
                lines.append(f"- `{r['seed_key']}` {label.replace('_', ' ')}: {listed}")
        if r.get("status") != "not_attempted" and r.get("matches_runtime_decision") is False:
            lines.append(f"- `{r['seed_key']}`: re-normalized resolution differs from the decision taken during the run. Inspect before using.")
    lines.append("")

    # 2. requests ----------------------------------------------------------
    records = normalized["requests"]
    lines += ["## 2. Requests", ""]
    counts: Dict[str, int] = defaultdict(int)
    for rec in records:
        counts[rec["status"]] += 1
    lines += _table(["Status", "Count", "Meaning"], [[s, n, STATUS_MEANINGS.get(s, "")] for s, n in sorted(counts.items())])
    reused = sum(1 for r in records if r.get("reused_from"))
    invocations = run.get("counts", {}).get("harness_invocations")
    answered_by = "local fixtures (nothing reached Qloo)" if synthetic else "the Qloo harness"
    lines += ["", f"Invocations answered by {answered_by}, including retries and excluding dry-run previews: {invocations}. "
              f"Responses reused from earlier identical live requests: {reused}.", ""]
    not_ok = normalized["coverage"]["not_ok_requests"]
    if not_ok:
        lines += ["Requests without a usable result:", ""]
        lines += _table(["Request", "Operation", "Seed / domain", "Status", "Code", "Message (redacted)"],
                        [[f["request_id"], f["operation"], "/".join(x for x in (f.get("seed_key"), f.get("domain_key")) if x),
                          f["status"], f.get("error_code"), f.get("message")] for f in not_ok])
        lines.append("")

    # 3. coverage ----------------------------------------------------------
    cov = normalized["coverage"]
    lines += ["## 3. Field coverage by operation and domain", "", cov["expected_fields_basis"], ""]
    lines += _table(
        ["Group", "Request statuses", "Items", "Unique IDs", "With tags", "With description", "With affinity", "With explanation", "Distinct tag IDs", "Top tag types"],
        [[k, ", ".join(f"{s} {n}" for s, n in sorted(g["status_counts"].items())), g["items"], g["unique_ids"], g["items_with_tags"],
          g["items_with_description_text"], g["items_with_affinity"],
          g["items_with_explanation"], g["distinct_tag_ids"],
          ", ".join(f"{t} ({n})" for t, n in list(g["tag_type_counts"].items())[:3]) or None]
         for k, g in sorted(cov["by_operation_domain"].items())],
    )
    absent = [r for r in cov["requests"] if r["requested_but_absent"]]
    if absent:
        lines += ["", "Requested but not returned: " + "; ".join(
            f"{r['request_id']} ({r['seed_key']}/{r['domain_key']}): {', '.join(r['requested_but_absent'])}" for r in absent)]
    missing_rows = [r for r in cov["requests"] if r["missing_field_counts"]]
    if missing_rows:
        lines += ["", "Missing expected fields (count of items): " + "; ".join(
            f"{r['request_id']}: " + ", ".join(f"{k}×{v}" for k, v in sorted(r["missing_field_counts"].items())) for r in missing_rows)]
    for note in cov.get("unrecognized_shapes", []):
        lines.append(f"- {note['request_id']} ({note['operation']}): unrecognized output shape, top level {note['top_level']}; saved raw, not normalized.")
    for check in cov.get("harness_resolution_checks", []):
        if check["consistent"] is False:
            lines.append(f"- {check['request_id']}: the harness resolved {check['harness_resolved_ids']} instead of {check['requested_qloo_id']}.")
    lines.append("")

    # 4. examples ----------------------------------------------------------
    lines += ["## 4. Returned examples with provenance", "",
              "Literal values as returned. `raw` points to the saved harness output and the JSON Pointer of the item.", ""]
    by_seed: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for obs in normalized["observations"]:
        by_seed[obs["query_context"]["seed_key"]].append(obs)
    for seed_key, observations in by_seed.items():
        lines += [f"### `{seed_key}`", ""]
        if all(o["kind"] == "search_candidate" for o in observations):
            lines += ["Search candidates only (see section 1); no dependent request was sent or none returned data.", ""]
            continue
        for obs in observations:
            if obs["query_context"]["operation"] == OP_SEED_DETAIL:
                lines.append(f"- Seed entity **{_cell(obs.get('name'))}**: {_tags_inline(obs, 10)}. Description fields: "
                             f"{', '.join(obs.get('description_fields') or []) or 'none'}. raw {_ref(obs)}")
        tag_obs = [o for o in observations if o["query_context"]["operation"] == OP_SEED_TAGS]
        if tag_obs:
            shown = "; ".join(f"{_cell(o.get('name'), 40)} [{(o.get('types') or {}).get('type') or 'no type'}] affinity={_cell(_affinity(o))}"
                              for o in tag_obs[:10])
            lines.append(f"- Tag insights (top {min(10, len(tag_obs))} of {len(tag_obs)}): {shown}. raw `{tag_obs[0]['raw_ref']['file']}`")
        related = [o for o in observations if o["query_context"]["operation"] == OP_RELATED]
        domains: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for o in related:
            domains[o["query_context"]["domain_key"]].append(o)
        for domain, items in domains.items():
            lines.append(f"- Related **{domain}** ({len(items)} returned):")
            for o in items[:3]:
                dup = f" duplicate of {o['duplicate_of']};" if o.get("duplicate_of") else ""
                lines.append(f"  - #{o['rank']} {_cell(o.get('name'), 50)} (`{_cell(o.get('qloo_id'), 40)}`) affinity={_cell(_affinity(o))}, "
                             f"popularity={_cell(_score(o, 'popularity'))};{dup} tags: {_tags_inline(o)}. raw {_ref(o)}")
        lines.append("")

    # 5. overlap -----------------------------------------------------------
    lines += ["## 5. Overlap between seeds (comparable requests only)", ""]
    groups = comparison["related_entity_overlap"] + comparison["tag_insight_overlap"]
    if not groups:
        lines.append("No comparable successful requests.")
    for group in groups:
        comp = group["comparability"]
        label = comp.get("entity_type") or f"limit {comp.get('limit')}"
        lines.append(f"**{comp.get('operation')} / {label}**. Seeds: {', '.join(group['seeds'])}; unique results per seed: "
                     + ", ".join(f"{s} {n}" for s, n in group["result_counts"].items()))
        if len(group["seeds"]) - len(group["seeds_with_zero_results"]) < 2:
            lines += ["", "Fewer than two seeds returned results in this group; overlap is not informative.", ""]
            continue
        if group["seeds_with_zero_results"]:
            lines += ["", f"Returned no results (pairs with them are trivially 0): {', '.join(group['seeds_with_zero_results'])}."]
        lines.append("")
        lines += _table(["A", "B", "Shared IDs", "Union", "Jaccard"],
                        [[p["a"], p["b"], p["intersection"], p["union"], p["jaccard"]] for p in group["pairwise"]])
        lines += ["", "Returned IDs by number of seeds they appear for: "
                  + ", ".join(f"{k} seed(s): {v}" for k, v in group["appearance_distribution"].items()) + "."]
        if group["shared_by_all_seeds"]:
            lines.append("Returned for every seed: " + ", ".join(_cell(i["name"], 40) for i in group["shared_by_all_seeds"][:10]) + ".")
        pops = [f"{k}: median {v['median_popularity']} (n={v['with_popularity']})" for k, v in group["popularity_by_appearance_count"].items()
                if v["median_popularity"] is not None]
        if pops:
            lines.append("Returned `popularity` by appearance count: " + "; ".join(pops) + ".")
        lines.append("")

    # 6. cross-domain tags -------------------------------------------------
    lines += ["## 6. Tag IDs recurring across domains (per seed)", "",
              "Same tag ID on related entities of different domains for one seed. Different IDs with similar names are not merged.", ""]
    recurrence = comparison["cross_domain_tag_recurrence"]
    if not recurrence:
        lines.append("No related-entity tags returned.")
    for seed_key, info in recurrence.items():
        lines.append(f"- `{seed_key}`: {info['distinct_tag_ids']} distinct tag IDs across {', '.join(info['domains_with_results'])}; "
                     f"{info['tag_ids_in_two_or_more_domains']} appear in two or more domains.")
        for r in info["top_recurring"][:8]:
            lines.append(f"  - {_cell(r['name'], 40)} `{_cell(r['tag_id'], 60)}` [{r['type']}]: {', '.join(r['domains'])}; {r['entity_count']} entities")
    lines.append("")

    # 7. sample shares -----------------------------------------------------
    lines += ["## 7. Sample tag shares (retrieved samples only; not lift)", "",
              "k/n = seed's results carrying the tag; K/N = pooled results of all seeds in the same group. "
              "Ratios from top-N samples are descriptive only and are not population lift.", ""]
    if not comparison["sample_tag_shares"]:
        lines.append("Not computable: needs at least two seeds with comparable related-entity results.")
    for block in comparison["sample_tag_shares"]:
        lines.append(f"**{block['comparability'].get('entity_type')}** (pooled unique entities: {block['pooled_unique_entities']})")
        lines.append("")
        rows = []
        for seed_key, entries in block["per_seed"].items():
            for e in entries[:5]:
                rows.append([seed_key, e.get("name"), e.get("type"), f"{e['k']}/{e['n']}", f"{e['K_pooled']}/{e['N_pooled']}", e["sample_enrichment"]])
        lines += _table(["Seed", "Tag", "Tag type", "k/n", "K/N", "Sample enrichment"], rows)
        lines.append("")

    # 8. quantitative fields -----------------------------------------------
    lines += ["## 8. Quantitative fields returned", ""]
    if comparison["score_inventory"]:
        lines += _table(["Item kind", "Field", "Values", "Min", "Max", "Requests"],
                        [[r["kind"], r["field"], r["count"], r["min"], r["max"], r["requests"]] for r in comparison["score_inventory"]])
    else:
        lines.append("No numeric score fields returned.")
    lines += ["", "## 9. Notes", ""] + [f"- {n}" for n in comparison["notes"]]
    lines += [
        "- This sheet establishes what the harness returned for these requests. It does not establish shared aesthetics, "
        "audience preferences, motif labels, or fragrance suitability.",
        "",
    ]
    return "\n".join(lines)

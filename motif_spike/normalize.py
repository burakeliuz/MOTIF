"""Raw harness output -> normalized observations, seed resolutions, coverage.

Normalization copies literal values only. Each observation points back to its
raw file and JSON Pointer. Nothing is merged by display name, no score is
rescaled, and an absent field is recorded as missing, never filled in.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .adapter import (
    DATA_STATUSES,
    OBSERVATION_KIND,
    OP_RELATED,
    OP_SEARCH,
    OP_SEED_TAGS,
    PARSER_BASIS,
    PARSER_STATUS,
    field_coverage,
    item_view,
    locate_items,
)
from .manifest import Seed
from .resolve import resolve_seed
from .util import RunPaths, evidence_id, get_path, iso, read_json, read_jsonl, utc_now, write_json, write_jsonl

PROVENANCE_LIVE = "qloo_observation"
PROVENANCE_SYNTHETIC = "synthetic_fixture"


def provenance_category(synthetic: bool) -> str:
    return PROVENANCE_SYNTHETIC if synthetic else PROVENANCE_LIVE


def observations_for(record: Dict[str, Any], doc: Any, run_id: str, synthetic: bool) -> Tuple[List[Dict[str, Any]], str]:
    operation = record["operation"]
    kind = OBSERVATION_KIND[operation]
    items, shape = locate_items(operation, doc)
    explainability_requested = bool(record.get("explainability_requested"))
    preview = record.get("api_request_preview")
    context = {
        "operation": operation,
        "seed_key": record.get("seed_key"),
        "seed_input_name": record.get("seed_input_name"),
        "seed_qloo_id": record.get("seed_qloo_id"),
        "domain_key": record.get("domain_key"),
        "requested_entity_type": record.get("requested_entity_type"),
        "harness_command": record.get("harness_command"),
        "api_params": preview.get("params") if isinstance(preview, dict) else None,
    }
    first_seen: Dict[Any, str] = {}
    out = []
    for index, (pointer, item) in enumerate(items):
        view = item_view(kind, item, pointer)
        missing, empty = field_coverage(kind, item, explainability_requested)
        eid = evidence_id(record["seq"], index)
        qloo_id = view.get("qloo_id")
        duplicate_of = None
        if qloo_id is not None:
            duplicate_of = first_seen.get(qloo_id)
            first_seen.setdefault(qloo_id, eid)
        out.append({
            "record_type": "observation",
            "evidence_id": eid,
            "provenance_category": provenance_category(synthetic),
            "synthetic": synthetic,
            "run_id": run_id,
            "request_id": record["request_id"],
            "kind": kind,
            "query_context": context,
            "rank": index + 1,
            "result_set_size": len(items),
            **view,
            "pointer": pointer,
            "missing_fields": missing,
            "empty_fields": empty,
            "duplicate_of": duplicate_of,
            "raw_ref": {"file": record["response_ref"], "pointer": pointer},
        })
    return out, shape


def load_doc(paths: RunPaths, record: Dict[str, Any]) -> Any:
    ref = record.get("response_ref")
    if not ref or record.get("status") not in DATA_STATUSES or not ref.endswith(".json"):
        return None
    return read_json(paths.root / ref)


def _seed_from_snapshot(snapshot: Dict[str, Any]) -> Seed:
    return Seed(**{k: snapshot.get(k) for k in ("key", "input_name", "expected_types", "search_type", "override", "note")})


def _coverage(records: List[Dict[str, Any]], observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_request: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        by_request[obs["request_id"]].append(obs)

    request_rows = []
    groups: Dict[str, Dict[str, Any]] = {}
    failures = []
    for rec in records:
        obs = by_request.get(rec["request_id"], [])
        missing = Counter(f for o in obs for f in o["missing_fields"])
        empty = Counter(f for o in obs for f in o["empty_fields"])
        requested_but_absent = []
        if rec.get("explainability_requested") and obs and all(o.get("explanation") is None for o in obs):
            requested_but_absent.append("explainability")
        request_rows.append({
            "request_id": rec["request_id"],
            "operation": rec["operation"],
            "seed_key": rec.get("seed_key"),
            "domain_key": rec.get("domain_key"),
            "status": rec["status"],
            "output_shape": rec.get("output_shape"),
            "result_count": len(obs) if rec.get("response_ref") else None,
            "missing_field_counts": dict(missing),
            "empty_field_counts": dict(empty),
            "requested_but_absent": requested_but_absent,
        })
        if rec["status"] not in ("ok", "ok_empty"):
            failures.append({
                "request_id": rec["request_id"],
                "operation": rec["operation"],
                "seed_key": rec.get("seed_key"),
                "domain_key": rec.get("domain_key"),
                "status": rec["status"],
                "error_code": (rec.get("error") or {}).get("code"),
                "message": (rec.get("error") or {}).get("message_redacted") or rec.get("skip_reason"),
            })

        group_key = rec["operation"] + (":" + rec["domain_key"] if rec.get("domain_key") else "")
        group = groups.setdefault(group_key, {
            "requests": 0, "status_counts": Counter(), "items": 0, "unique_ids": set(), "with_tags": 0,
            "with_description": 0, "with_affinity": 0, "with_explanation": 0, "tag_ids": set(), "tag_types": Counter(),
        })
        group["requests"] += 1
        group["status_counts"][rec["status"]] += 1
        for o in obs:
            group["items"] += 1
            if o.get("qloo_id") is not None:
                group["unique_ids"].add(o["qloo_id"])
            if o.get("tags"):
                group["with_tags"] += 1
            if o.get("description_fields"):
                group["with_description"] += 1
            if any(s["field"] in ("query.affinity", "affinity") for s in o.get("scores", [])):
                group["with_affinity"] += 1
            if o.get("explanation") is not None:
                group["with_explanation"] += 1
            for tag in o.get("tags", []) or []:
                if tag.get("id") is not None:
                    group["tag_ids"].add(tag["id"])
                group["tag_types"][tag.get("type") or "(no type)"] += 1
            if o["kind"] == "tag_insight":
                if o.get("qloo_id") is not None:
                    group["tag_ids"].add(o["qloo_id"])
                group["tag_types"][(o.get("types") or {}).get("type") or (o.get("types") or {}).get("subtype") or "(no type)"] += 1

    return {
        "record_type": "coverage",
        "expected_fields_basis": "Expected fields come from documentation; 'missing' means not returned, never a negative value.",
        "status_counts": dict(Counter(r["status"] for r in records)),
        "requests": request_rows,
        "by_operation_domain": {
            key: {
                "requests": g["requests"],
                "status_counts": dict(g["status_counts"]),
                "items": g["items"],
                "unique_ids": len(g["unique_ids"]),
                "items_with_tags": g["with_tags"],
                "items_with_description_text": g["with_description"],
                "items_with_affinity": g["with_affinity"],
                "items_with_explanation": g["with_explanation"],
                "distinct_tag_ids": len(g["tag_ids"]),
                "tag_type_counts": dict(g["tag_types"].most_common()),
            }
            for key, g in groups.items()
        },
        "not_ok_requests": failures,
    }


def normalize_run(paths: RunPaths) -> Dict[str, Any]:
    run = read_json(paths.run_record)
    records = read_jsonl(paths.requests_log)
    synthetic = bool(run.get("synthetic"))
    run_id = run["run_id"]

    observations: List[Dict[str, Any]] = []
    shape_notes = []
    harness_resolution_checks = []
    # Response-level fields outside the located items (direct transport bodies only).
    response_level = []
    for rec in records:
        doc = load_doc(paths, rec)
        if doc is None:
            continue
        obs, shape = observations_for(rec, doc, run_id, synthetic)
        observations.extend(obs)
        if shape == "unrecognized":
            keys = sorted(doc) if isinstance(doc, dict) else type(doc).__name__
            shape_notes.append({"request_id": rec["request_id"], "operation": rec["operation"], "top_level": keys})
        aggregate = get_path(doc, ("query", "explainability")) if isinstance(doc, dict) else None
        if aggregate is not None:
            response_level.append({
                "request_id": rec["request_id"],
                "seed_key": rec.get("seed_key"),
                "domain_key": rec.get("domain_key"),
                "field": "query.explainability",
                "value": aggregate,
                "raw_ref": {"file": rec["response_ref"], "pointer": "/query/explainability"},
            })
        if rec["operation"] == OP_SEED_TAGS and isinstance(doc, dict):
            interpreted = get_path(doc, ("interpretation", "entities"))
            ids = [e.get("entityId") for e in interpreted] if isinstance(interpreted, list) else None
            harness_resolution_checks.append({
                "request_id": rec["request_id"],
                "seed_key": rec.get("seed_key"),
                "requested_qloo_id": rec.get("seed_qloo_id"),
                "harness_resolved_ids": ids,
                "consistent": ids == [rec.get("seed_qloo_id")] if ids is not None else None,
            })

    seeds = {s["key"]: _seed_from_snapshot(s) for s in run["plan"]["seeds"]}
    resolutions = []
    for rec in records:
        if rec["operation"] != OP_SEARCH:
            continue
        seed = seeds[rec["seed_key"]]
        candidates = [o for o in observations if o["request_id"] == rec["request_id"]]
        res = resolve_seed(seed, candidates, rec["status"])
        runtime = rec.get("runtime_resolution") or {}
        resolutions.append({
            "record_type": "seed_resolution",
            "resolution_id": f"local:seed:{seed.key}",
            "provenance_category": provenance_category(synthetic),
            "synthetic": synthetic,
            "seed_key": seed.key,
            "input_name": seed.input_name,
            "expected_types": seed.expected_types,
            "search_request_id": rec["request_id"],
            "raw_ref": {"file": rec.get("response_ref"), "pointer": ""} if rec.get("response_ref") else None,
            **res,
            "matches_runtime_decision": (runtime.get("status") == res["status"] and runtime.get("qloo_id") == res["qloo_id"]),
        })
    for seed_key in seeds:
        if not any(r["seed_key"] == seed_key for r in resolutions):
            resolutions.append({
                "record_type": "seed_resolution",
                "resolution_id": f"local:seed:{seed_key}",
                "synthetic": synthetic,
                "seed_key": seed_key,
                "input_name": seeds[seed_key].input_name,
                "status": "not_attempted",
                "method": "no search request was sent (run aborted or budget exhausted)",
            })

    coverage = _coverage(records, observations)
    coverage.update(run_id=run_id, synthetic=synthetic, unrecognized_shapes=shape_notes,
                    harness_resolution_checks=harness_resolution_checks, response_level_fields=response_level)

    normalized_run = dict(run)
    normalized_run["normalization"] = {
        "normalized_at": iso(utc_now()),
        "parser_status": PARSER_STATUS,
        "parser_basis": PARSER_BASIS,
        "observation_count": len(observations),
    }
    out = paths.normalized_dir
    write_json(out / "run.json", normalized_run)
    write_json(out / "seed_resolutions.json", resolutions)
    write_jsonl(out / "observations.jsonl", observations)
    write_json(out / "coverage.json", coverage)
    return {"run": normalized_run, "resolutions": resolutions, "observations": observations, "coverage": coverage, "requests": records}


def candidate_views(record: Dict[str, Any], doc: Any, run_id: str, synthetic: bool) -> List[Dict[str, Any]]:
    """Search candidates for runtime resolution; same IDs normalization will produce."""
    if doc is None:
        return []
    obs, _ = observations_for(record, doc, run_id, synthetic)
    return obs


def related_observations(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [o for o in observations if o["query_context"]["operation"] == OP_RELATED]

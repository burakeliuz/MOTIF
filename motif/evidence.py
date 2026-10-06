"""Normalized evidence items from Qloo response bodies.

An evidence item is one returned tag on one entity, copied literally with the
request it came from and its JSON Pointer. Only the namespaces the lexicon
reads are kept (config/motif_lexicon.json -> match.namespaces). The item ID is
derived from (source kind, entity ID, tag ID), so the same tag on the same
entity returned twice is one item. The relation score (`query.affinity`) is
kept beside the item as rank context only; it never feeds classification.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from motif_spike.adapter import OP_RELATED, OP_SEED_DETAIL, locate_items
from motif_spike.util import get_path, join_pointer

SOURCE_ORDER = ("own", "brand", "movie", "artist")


def _tag_id(tag: Dict[str, Any]) -> Optional[str]:
    return tag.get("tag_id") or tag.get("id")


def items_from_body(source_kind: str, body: Any, request: Dict[str, Any], namespaces: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Evidence items of one saved response body.

    `request` carries `request_id`, `fetched_at`, `path`, and `params` (non-secret).
    """
    operation = OP_SEED_DETAIL if source_kind == "own" else OP_RELATED
    allowed = set(namespaces.get(source_kind, []))
    out: List[Dict[str, Any]] = []
    entities, _shape = locate_items(operation, body)
    for rank, (pointer, entity) in enumerate(entities, start=1):
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("entity_id") or entity.get("id")
        affinity = get_path(entity, ("query", "affinity"))
        for index, tag in enumerate(entity.get("tags") or []):
            if not isinstance(tag, dict) or tag.get("type") not in allowed:
                continue
            tag_id = _tag_id(tag)
            name = tag.get("name")
            if not tag_id or not isinstance(name, str):
                continue
            out.append({
                "evidence_id": f"ev:{source_kind}:{entity_id}:{tag_id}",
                "provenance_category": "qloo_observation",
                "source_kind": source_kind,
                "entity_id": entity_id,
                "entity_name": entity.get("name"),
                "entity_rank": rank,
                "relation_affinity": affinity if source_kind != "own" else None,
                "tag_id": tag_id,
                "tag_name": name,
                "tag_type": tag.get("type"),
                "request_id": request.get("request_id"),
                "request": {"path": request.get("path"), "params": request.get("params")},
                "fetched_at": request.get("fetched_at"),
                "json_pointer": join_pointer(pointer, "tags", index),
            })
    return out


def normalize_evidence(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by evidence ID (first occurrence in canonical order wins) and sort canonically."""
    def key(item: Dict[str, Any]):
        return (SOURCE_ORDER.index(item["source_kind"]), str(item["entity_id"]), item["tag_id"],
                str(item.get("request_id")), item["json_pointer"])

    unique: Dict[str, Dict[str, Any]] = {}
    for item in sorted(items, key=key):
        unique.setdefault(item["evidence_id"], item)
    return sorted(unique.values(), key=key)

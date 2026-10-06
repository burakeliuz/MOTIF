"""SYNTHETIC test helpers for the motif engine: invented Qloo-shaped bodies and a fake transport.

Nothing here is Qloo data. Names and IDs are invented and prefixed SYN-.
"""

import json
import random

from motif_spike.transport import ProcessResult
from motif.config import load_config

AESTHETIC = "urn:tag:aesthetic_property:qloo"
TONE = "urn:tag:emotional_tone:qloo"
STYLE = "urn:tag:style:qloo"


def tag(name, ttype, key="tag_id"):
    return {key: f"{ttype}:{name.lower().replace(' ', '_')}", "name": name, "type": ttype}


def entities_body(entity_id, name, tags):
    return {"results": [{"entity_id": entity_id, "name": name, "types": ["urn:entity:brand"],
                         "tags": [tag(n, t) for n, t in tags]}]}


def insights_body(entities):
    """entities: [(entity_id, name, [(tag name, tag type)])]"""
    return {"success": True, "results": {"entities": [
        {"entity_id": eid, "name": name, "query": {"affinity": 0.9 - i / 100},
         "tags": [tag(n, t, key="id") for n, t in tags]} for i, (eid, name, tags) in enumerate(entities)]}}


def search_body(candidates):
    """candidates: [(entity_id, name, type)]"""
    return {"results": [{"entity_id": eid, "name": name, "types": [t], "disambiguation": ""} for eid, name, t in candidates]}


def evidence_item(kind, entity_id, tag_name, ttype, request_id="local:req:0001"):
    tag_id = f"{ttype}:{tag_name.lower().replace(' ', '_')}"
    return {"evidence_id": f"ev:{kind}:{entity_id}:{tag_id}", "provenance_category": "synthetic_fixture",
            "source_kind": kind, "entity_id": entity_id, "entity_name": f"SYN {entity_id}", "entity_rank": 1,
            "relation_affinity": None, "tag_id": tag_id, "tag_name": tag_name, "tag_type": ttype,
            "request_id": request_id, "request": {}, "fetched_at": None, "json_pointer": "/results/0/tags/0"}


def ok(body):
    return ProcessResult(0, json.dumps(body), "", 1)


def http_error(status):
    return ProcessResult(5, json.dumps({"error": True, "code": f"HTTP_{status}", "message": f"HTTP {status}"}), "", 1)


class FakeTransport:
    """Answers by request kind; records every call. `script` maps a key to a list of results (consumed in order)."""

    name = "direct"

    def __init__(self, routes):
        self.routes = routes  # function(argv) -> ProcessResult
        self.calls = []

    def supports_preview(self, operation):
        return False

    def execute(self, argv, timeout_s=None):
        self.calls.append(list(argv))
        return self.routes(list(argv))


def verified_palette(config, verify):
    """A copy of the palette where ONLY the listed (material_id, axis) properties are verified (test only)."""
    palette = json.loads(json.dumps(config.palette))
    for m in palette["materials"]:
        for axis in m["motif_profile"]:
            ok = (m["material_id"], axis) in verify or (m["material_id"], "*") in verify
            m.setdefault("property_verification", {})[axis] = {"status": "verified_full_page" if ok else "unverified_excerpt"}
    return type(config)(config.lexicon, config.rules, palette, config.params)


def shuffled(items, seed=7):
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


CONFIG = load_config()

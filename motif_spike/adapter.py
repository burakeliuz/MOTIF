"""Boundary between MOTIF and the Qloo API.

Requests are described as harness-style commands (`qloo api ...`,
`qloo exec ...`). A transport then either runs them with the official harness
(`@qloo/qloo-harness`) or, by default, sends the equivalent HTTPS request
itself (`http_request` below; see transport.DirectTransport).

With the harness, what is saved is a projection of the API response, not the
HTTP body (read from harness 0.1.26 source, see docs/QLOO_ACCESS_NOTES.md):

* `qloo api search --json`   -> the `results` list
* `qloo api entity --json`   -> one entity object
* `qloo api insights --json` -> the `results.entities` list (tag results are
  not printed, which is why tag insights use `qloo exec entity_tags`)
* `qloo exec entity_tags`    -> a workflow envelope with compact tags

The direct transport saves the full HTTP body instead. The parsers below
accept both kinds of documented shapes, record the shape actually
seen, and report anything else as `unrecognized_shape` instead of guessing.
They have not been checked against live output yet.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .util import get_path, has_path, is_number, join_pointer

ADAPTER_VERSION = "0.1.0"
# Flip to "verified" only after comparing these parsers with real harness output.
PARSER_STATUS = "unverified"
PARSER_BASIS = (
    "Qloo docs-public reference and @qloo/qloo-harness 0.1.26 source, read 2026-10-04; "
    "no live harness output inspected yet"
)
MIN_HARNESS_VERSION = (0, 1, 26)

OP_SEARCH = "search"
OP_SEED_DETAIL = "seed_detail"
OP_RELATED = "related_entities"
OP_SEED_TAGS = "seed_tags"
OPERATIONS = (OP_SEARCH, OP_SEED_DETAIL, OP_RELATED, OP_SEED_TAGS)

OBSERVATION_KIND = {
    OP_SEARCH: "search_candidate",
    OP_SEED_DETAIL: "seed_entity",
    OP_RELATED: "related_entity",
    OP_SEED_TAGS: "tag_insight",
}

# `qloo api tags` and `qloo exec` have no --dry-run; everything else does.
DRY_RUN_SUPPORTED = frozenset({OP_SEARCH, OP_SEED_DETAIL, OP_RELATED})

# --- request statuses -------------------------------------------------------

SUCCESS_STATUSES = frozenset({"ok", "ok_empty"})
# Statuses whose stdout is a usable document and is saved as a raw response.
DATA_STATUSES = frozenset({"ok", "ok_empty", "partial", "needs_input", "unrecognized_shape"})
RETRYABLE_STATUSES = frozenset({"rate_limited", "server_error", "timeout", "network_error", "transient_error"})
# Credential problems stop the run: no other credential or endpoint is tried.
ABORT_STATUSES = frozenset({"auth_error"})

STATUS_MEANINGS = {
    "ok": "Harness returned a recognized document with at least one result.",
    "ok_empty": "Harness returned a recognized document with zero results.",
    "partial": "Workflow reported partial/degraded results; data kept and flagged.",
    "needs_input": "Workflow could not resolve its input (harness-side resolution).",
    "unrecognized_shape": "Output was JSON but not a documented shape; saved, not normalized.",
    "unparseable_output": "Output was not JSON.",
    "auth_error": "Credential missing or rejected; the run stops here.",
    "forbidden": "HTTP 403 after other requests succeeded: this operation is not permitted.",
    "rate_limited": "HTTP 429 / rate limit; retried within the bounded retry budget.",
    "server_error": "HTTP 5xx; retried within the bounded retry budget.",
    "transient_error": "Harness flagged a retryable failure; retried within the budget.",
    "network_error": "Network failure reported by the harness; retried within the budget.",
    "timeout": "No harness response within the timeout; retried within the budget.",
    "rejected_request": "HTTP 400/422: parameters rejected (possibly unsupported).",
    "not_found": "Entity not found / HTTP 404.",
    "bad_usage": "Harness rejected the command line (adapter bug).",
    "config_error": "Harness configuration error.",
    "api_error": "Other API error; see the redacted message.",
    "harness_error": "Non-zero exit without a structured error.",
    "harness_missing": "The `qloo` binary was not found.",
    "fixture_missing": "Synthetic mode only: no fixture matches this command.",
    "skipped_unresolved_seed": "Not sent: the seed did not resolve to exactly one entity.",
    "skipped_after_auth_error": "Not sent: an earlier credential failure stopped the run.",
    "skipped_budget": "Not sent: the run's request budget was exhausted.",
}


# --- command builders --------------------------------------------------------


def search_argv(query: str, take: int, type_hint: Optional[str] = None) -> List[str]:
    argv = ["api", "search", "--query", query, "--take", str(take), "--json"]
    if type_hint:
        argv[4:4] = ["--type", type_hint]
    return argv


def seed_detail_argv(entity_id: str) -> List[str]:
    return ["api", "entity", "--id", entity_id, "--json"]


def related_argv(entity_id: str, entity_type: str, take: int, explainability: bool) -> List[str]:
    argv = ["api", "insights", "--type", entity_type, "--signal-entities", entity_id, "--take", str(take), "--json"]
    if explainability:
        argv += ["--params", json.dumps({"feature.explainability": True}, sort_keys=True)]
    return argv


def seed_tags_argv(entity_id: str, limit: int) -> List[str]:
    payload = json.dumps({"entities": [entity_id], "limit": limit}, sort_keys=True)
    return ["exec", "entity_tags", "--input", payload]


def display_command(argv: Sequence[str]) -> str:
    return "qloo " + " ".join(shlex.quote(a) for a in argv)


def parse_flags(argv: Sequence[str]) -> Dict[str, str]:
    """`--flag value` pairs of an adapter command (bare flags such as --json are skipped)."""
    flags: Dict[str, str] = {}
    for i, token in enumerate(argv):
        if token.startswith("--") and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            flags[token] = argv[i + 1]
    return flags


def _param_value(value: Any) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def http_request(argv: Sequence[str]) -> Tuple[str, Dict[str, str]]:
    """The Qloo HTTP request (path, query params) an adapter command stands for.

    Used by the direct transport. Parameters mirror what the harness sends:
    search, entity and insights were checked with `--dry-run` against harness
    0.1.26; entity_tags (no dry-run) follows the harness source, minus the
    identifier lookup the harness adds first.
    """
    argv = [a for a in argv if a != "--dry-run"]
    command = tuple(argv[:2])
    flags = parse_flags(argv)
    if command == ("api", "search"):
        params = {"query": flags["--query"], "take": flags["--take"]}
        if "--type" in flags:
            params["types"] = flags["--type"]
        return "/search", params
    if command == ("api", "entity"):
        return "/entities", {"entity_ids": flags["--id"]}
    if command == ("api", "insights"):
        params = {
            "filter.type": flags["--type"],
            "signal.interests.entities": flags["--signal-entities"],
            "take": flags["--take"],
        }
        if "--params" in flags:
            params.update({k: _param_value(v) for k, v in json.loads(flags["--params"]).items()})
        return "/v2/insights", params
    if command == ("exec", "entity_tags"):
        payload = json.loads(flags["--input"])
        return "/v2/insights", {
            "filter.type": "urn:tag",
            "signal.interests.entities": ",".join(payload["entities"]),
            "take": str(payload.get("limit", 10)),
        }
    raise ValueError(f"no HTTP mapping for command {' '.join(argv[:2])!r}")


# --- outcome classification ------------------------------------------------


@dataclass
class Outcome:
    status: str
    doc: Any = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False
    shape: Optional[str] = None
    item_count: Optional[int] = None
    workflow_status: Optional[str] = None
    notes: List[str] = field(default_factory=list)


_NOT_JSON = object()


def _parse(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        return _NOT_JSON
    try:
        return json.loads(text)
    except ValueError:
        return _NOT_JSON


def _structured_error(doc: Any) -> Optional[Tuple[str, str, Optional[bool]]]:
    """Return (code, message, retryable_hint) when the harness reported an error."""
    if not isinstance(doc, dict):
        return None
    if doc.get("error") is True:  # `qloo api`: {"error": true, "code": ..., "message": ...}
        return str(doc.get("code") or "UNKNOWN"), str(doc.get("message") or ""), None
    err = doc.get("error")
    if isinstance(err, dict) and ("status" not in doc or doc.get("status") == "error"):
        # `qloo exec`: {"error": {"code", "layer", "retryable", "recovery", ...}, ...}
        message = err.get("message") or err.get("recovery") or ""
        retryable = err.get("retryable") if isinstance(err.get("retryable"), bool) else None
        return str(err.get("code") or "UNKNOWN"), str(message), retryable
    return None


def error_status(code: str, message: str, retryable_hint: Optional[bool] = None) -> str:
    code_u = (code or "").upper()
    msg = (message or "").lower()
    if code_u == "SYNTHETIC_FIXTURE_MISSING":
        return "fixture_missing"
    if code_u == "NETWORK_ERROR":
        return "network_error"
    if code_u.startswith("HTTP_") and code_u[5:].isdigit():
        status = int(code_u[5:])
        if status == 401:
            return "auth_error"
        if status == 403:
            return "forbidden"
        if status == 404:
            return "not_found"
        if status == 429:
            return "rate_limited"
        if status >= 500:
            return "server_error"
        if 400 <= status < 500:
            return "rejected_request"
        return "api_error"
    if code_u == "AUTH_FAILED" or "AUTH" in code_u or re.search(r"\b401\b", msg) or "unauthorized" in msg:
        return "auth_error"
    if re.search(r"\b403\b", msg) or "forbidden" in msg:
        return "forbidden"
    if code_u == "NOT_FOUND":
        return "not_found"
    if code_u == "BAD_USAGE":
        return "bad_usage"
    if code_u == "CONFIG_ERROR":
        return "config_error"
    if re.search(r"\b429\b", msg) or "rate limit" in msg or "too many requests" in msg or "RATE" in code_u:
        return "rate_limited"
    if re.search(r"\b5\d\d\b", msg):
        return "server_error"
    if re.search(r"\b(400|422)\b", msg) or "bad request" in msg:
        return "rejected_request"
    if re.search(r"\b404\b", msg):
        return "not_found"
    if any(s in msg for s in ("fetch failed", "econnreset", "econnrefused", "enotfound", "etimedout", "network")):
        return "network_error"
    if retryable_hint:
        return "transient_error"
    return "api_error"


def classify(operation: str, result: Any) -> Outcome:
    """Turn one harness invocation (a transport ProcessResult) into an Outcome."""
    if result.missing_binary:
        return Outcome("harness_missing", error_message="qloo binary not found")
    if result.timed_out:
        return Outcome("timeout", retryable=True, error_message="no harness response within the timeout")

    doc = _parse(result.stdout)
    if doc is _NOT_JSON:
        detail = (result.stdout or "").strip() or (result.stderr or "").strip() or "empty output"
        return Outcome("unparseable_output", error_message=detail, notes=[f"exit code {result.exit_code}"])

    err = _structured_error(doc)
    if err:
        code, message, hint = err
        status = error_status(code, message, hint)
        return Outcome(status, doc=doc, error_code=code, error_message=message, retryable=status in RETRYABLE_STATUSES)

    if result.exit_code not in (0, None):
        return Outcome("harness_error", doc=doc, error_message=f"exit code {result.exit_code} without a structured error")

    items, shape = locate_items(operation, doc)
    if shape == "unrecognized":
        return Outcome("unrecognized_shape", doc=doc, shape=shape, item_count=0)

    workflow_status = doc.get("status") if operation == OP_SEED_TAGS and isinstance(doc, dict) else None
    if workflow_status == "needs_input":
        status = "needs_input"
    elif workflow_status in ("partial", "degraded"):
        status = "partial"
    elif workflow_status not in (None, "ok", "empty"):
        status = "unrecognized_shape"
    else:
        status = "ok" if items else "ok_empty"
    return Outcome(status, doc=doc, shape=shape, item_count=len(items), workflow_status=workflow_status)


# --- locating result items ----------------------------------------------------


def locate_items(operation: str, doc: Any) -> Tuple[List[Tuple[str, Any]], str]:
    """Return [(json_pointer, item), ...] and a label for the shape that matched."""
    if operation == OP_SEED_TAGS:
        if isinstance(doc, dict) and isinstance(doc.get("results"), list):
            return [(join_pointer("/results", i), it) for i, it in enumerate(doc["results"])], "workflow_envelope.results"
        # Direct API body: {"results": {"tags": [...]}} (taste-analysis reference).
        tags = get_path(doc, ("results", "tags"))
        if isinstance(tags, list):
            return [(join_pointer("/results/tags", i), it) for i, it in enumerate(tags)], "results.tags"
        return [], "unrecognized"

    if operation == OP_SEED_DETAIL and isinstance(doc, dict) and any(k in doc for k in ("entity_id", "id", "name")):
        return [("", doc)], "root_object"

    if isinstance(doc, list):
        return [(join_pointer("", i), it) for i, it in enumerate(doc)], "root_array"
    if isinstance(doc, dict):
        for path in (("entities",), ("results",), ("results", "entities")):
            node = get_path(doc, path)
            if isinstance(node, list):
                base = join_pointer("", *path)
                return [(join_pointer(base, i), it) for i, it in enumerate(node)], ".".join(path)
    return [], "unrecognized"


# --- literal views of returned items -------------------------------------------

# For each observation kind: (label, alternative key paths). A field counts as
# present when any alternative exists with a non-null value. These lists come
# from documentation, so "missing" means "not returned", never "false".
EXPECTED_FIELDS: Dict[str, List[Tuple[str, List[Tuple[str, ...]]]]] = {
    "search_candidate": [
        ("id", [("entity_id",), ("id",)]),
        ("name", [("name",)]),
        ("type", [("types",), ("subtype",), ("type",)]),
        ("properties", [("properties",)]),
        ("tags", [("tags",)]),
        ("popularity", [("popularity",)]),
    ],
    "related_entity": [
        ("id", [("entity_id",), ("id",)]),
        ("name", [("name",)]),
        ("type", [("subtype",), ("type",), ("types",)]),
        ("properties", [("properties",)]),
        ("tags", [("tags",)]),
        ("affinity", [("query", "affinity"), ("affinity",)]),
        ("popularity", [("popularity",)]),
    ],
    "tag_insight": [
        ("id", [("id",), ("tag_id",)]),
        ("name", [("name",)]),
        ("type", [("type",), ("subtype",)]),
        ("affinity", [("affinity",), ("query", "affinity")]),
        ("popularity", [("popularity",)]),
    ],
}
EXPECTED_FIELDS["seed_entity"] = EXPECTED_FIELDS["search_candidate"]

DESCRIPTION_PATHS = (("properties", "description"), ("properties", "short_description"), ("properties", "short_descriptions"))
SCORE_PATHS = (("query", "affinity"), ("affinity",), ("popularity",))


def _first_present(item: Dict[str, Any], paths: Sequence[Tuple[str, ...]]) -> Optional[Tuple[str, ...]]:
    for path in paths:
        if has_path(item, path) and get_path(item, path) is not None:
            return path
    return None


def field_coverage(kind: str, item: Any, explainability_requested: bool = False) -> Tuple[List[str], List[str]]:
    """Return (missing_fields, empty_fields) for one returned item."""
    if not isinstance(item, dict):
        return [label for label, _ in EXPECTED_FIELDS[kind]], []
    expected = list(EXPECTED_FIELDS[kind])
    if kind == "related_entity" and explainability_requested:
        expected.append(("explainability", [("query", "explainability")]))
    missing, empty = [], []
    for label, paths in expected:
        path = _first_present(item, paths)
        if path is None:
            missing.append(label)
        elif get_path(item, path) in ([], {}, ""):
            empty.append(label)
    return missing, empty


def _first_key(item: Dict[str, Any], *keys: str) -> Tuple[Optional[str], Any]:
    for key in keys:
        if key in item and item[key] is not None:
            return key, item[key]
    return None, None


def item_view(kind: str, item: Any, pointer: str) -> Dict[str, Any]:
    """Literal fields of one returned item, each traceable to `pointer`."""
    if not isinstance(item, dict):
        return {"literal": item, "qloo_id": None, "qloo_id_field": None, "name": None}

    id_field, qloo_id = _first_key(item, "entity_id", "id", "tag_id")
    view: Dict[str, Any] = {
        "qloo_id": qloo_id,
        "qloo_id_field": id_field,
        "name": item.get("name"),
        "types": {k: item[k] for k in ("type", "subtype", "types") if k in item},
        "scores": [
            {"field": ".".join(path), "value": get_path(item, path), "pointer": join_pointer(pointer, *path)}
            for path in SCORE_PATHS
            if is_number(get_path(item, path))
        ],
    }
    if kind == "tag_insight":
        return view

    properties = item.get("properties")
    view["attributes"] = properties if isinstance(properties, dict) else None
    view["description_fields"] = [".".join(p) for p in DESCRIPTION_PATHS if get_path(item, p) not in (None, "", [], {})]
    tags = []
    if isinstance(item.get("tags"), list):
        for i, tag in enumerate(item["tags"]):
            tag_pointer = join_pointer(pointer, "tags", i)
            if isinstance(tag, dict):
                tags.append({
                    "id": _first_key(tag, "id", "tag_id")[1],
                    "name": tag.get("name"),
                    "type": _first_key(tag, "type", "subtype")[1],
                    "pointer": tag_pointer,
                    **({"value": tag["value"]} if "value" in tag else {}),
                })
            else:
                tags.append({"literal": tag, "pointer": tag_pointer})
    view["tags"] = tags
    explanation = get_path(item, ("query", "explainability"))
    view["explanation"] = (
        {"value": explanation, "pointer": join_pointer(pointer, "query", "explainability")} if explanation is not None else None
    )
    known = {"entity_id", "id", "tag_id", "name", "type", "subtype", "types", "properties", "tags", "popularity", "query", "affinity"}
    view["other_top_level_keys"] = sorted(k for k in item if k not in known)
    return view


def item_types(view: Dict[str, Any]) -> List[str]:
    """Flatten the literal type fields of a view into a list of strings."""
    out: List[str] = []
    for value in view.get("types", {}).values():
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(v for v in value if isinstance(v, str))
    return out

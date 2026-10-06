"""Outcome classification, shape detection, field coverage, and redaction."""

try:
    from . import _netguard  # noqa: F401
except ImportError:  # started as a top-level module (discover -s tests)
    import _netguard  # noqa: F401
import json
import os
import unittest
from unittest import mock

from motif_spike import adapter
from motif_spike.adapter import classify, field_coverage, item_view, locate_items
from motif_spike.redact import REDACTED, redact
from motif_spike.transport import ProcessResult


def api_error(message, code="API_ERROR", exit_code=5):
    return ProcessResult(exit_code, json.dumps({"error": True, "code": code, "message": message}), "", 1)


class Classify(unittest.TestCase):
    def test_distinct_error_states(self):
        cases = {
            "API request failed: 401 Unauthorized": "auth_error",
            "API request failed: 403 Forbidden": "forbidden",
            "API request failed: 429 Too Many Requests": "rate_limited",
            "API request failed: 503 Service Unavailable": "server_error",
            "API request failed: 400 Bad Request": "rejected_request",
            "API request failed: 404 Not Found": "not_found",
            "fetch failed": "network_error",
            "something else": "api_error",
        }
        for message, status in cases.items():
            with self.subTest(message=message):
                self.assertEqual(classify(adapter.OP_RELATED, api_error(message)).status, status)
        self.assertEqual(classify(adapter.OP_SEARCH, api_error("No API key found.", "AUTH_FAILED", 3)).status, "auth_error")
        self.assertEqual(classify(adapter.OP_SEED_DETAIL, api_error("Entity not found.", "NOT_FOUND", 4)).status, "not_found")

    def test_empty_result_is_not_an_error(self):
        outcome = classify(adapter.OP_RELATED, ProcessResult(0, "[]", "", 1))
        self.assertEqual((outcome.status, outcome.item_count), ("ok_empty", 0))

    def test_unexpected_output_is_reported_not_guessed(self):
        self.assertEqual(classify(adapter.OP_RELATED, ProcessResult(0, "not json", "", 1)).status, "unparseable_output")
        self.assertEqual(classify(adapter.OP_RELATED, ProcessResult(0, '{"surprise": 1}', "", 1)).status, "unrecognized_shape")
        self.assertEqual(classify(adapter.OP_RELATED, ProcessResult(None, "", "", 1, timed_out=True)).status, "timeout")
        self.assertEqual(classify(adapter.OP_RELATED, ProcessResult(None, "", "", 0, missing_binary=True)).status, "harness_missing")

    def test_workflow_envelope_states(self):
        def envelope(status, results):
            return ProcessResult(0, json.dumps({"status": status, "results": results}), "", 1)
        self.assertEqual(classify(adapter.OP_SEED_TAGS, envelope("ok", [{"id": "t"}])).status, "ok")
        self.assertEqual(classify(adapter.OP_SEED_TAGS, envelope("empty", [])).status, "ok_empty")
        self.assertEqual(classify(adapter.OP_SEED_TAGS, envelope("needs_input", [])).status, "needs_input")
        self.assertEqual(classify(adapter.OP_SEED_TAGS, envelope("degraded", [{"id": "t"}])).status, "partial")
        failed = ProcessResult(4, json.dumps({"error": {"code": "QLOO_AUTH", "retryable": False}}), "", 1)
        self.assertEqual(classify(adapter.OP_SEED_TAGS, failed).status, "auth_error")
        retryable = ProcessResult(1, json.dumps({"error": {"code": "QLOO_UPSTREAM", "retryable": True}}), "", 1)
        self.assertTrue(classify(adapter.OP_SEED_TAGS, retryable).retryable)


class ShapesAndFields(unittest.TestCase):
    def test_locate_items_reports_the_shape_used(self):
        self.assertEqual(locate_items(adapter.OP_SEARCH, [{"name": "a"}])[1], "root_array")
        self.assertEqual(locate_items(adapter.OP_SEARCH, {"entities": [{"name": "a"}]})[1], "entities")
        self.assertEqual(locate_items(adapter.OP_SEARCH, {"results": {"entities": [{"name": "a"}]}})[1], "results.entities")
        items, shape = locate_items(adapter.OP_RELATED, [{"name": "a"}, {"name": "b"}])
        self.assertEqual([p for p, _ in items], ["/0", "/1"])

    def test_missing_fields_are_listed_and_not_filled(self):
        item = {"entity_id": "X", "name": "Only a name", "query": {}}
        missing, empty = field_coverage("related_entity", item, explainability_requested=True)
        self.assertEqual(set(missing), {"type", "properties", "tags", "affinity", "popularity", "explainability"})
        view = item_view("related_entity", item, "/0")
        self.assertEqual(view["scores"], [])
        self.assertEqual(view["tags"], [])
        self.assertIsNone(view["attributes"])
        self.assertIsNone(view["explanation"])

    def test_scores_and_tags_keep_their_pointers_and_values(self):
        item = {"entity_id": "X", "query": {"affinity": 0.7}, "popularity": 0.2,
                "tags": [{"id": "urn:tag:keyword:media:a", "name": "A", "type": "urn:tag:keyword:media"}]}
        view = item_view("related_entity", item, "/3")
        self.assertIn({"field": "query.affinity", "value": 0.7, "pointer": "/3/query/affinity"}, view["scores"])
        self.assertEqual(view["tags"][0]["pointer"], "/3/tags/0")
        self.assertEqual(view["tags"][0]["type"], "urn:tag:keyword:media")


class LiveBodyShapes(unittest.TestCase):
    """Shapes seen in direct-transport bodies on 2026-10-06; values here are invented."""

    def test_entities_endpoint_wraps_the_entity_in_results(self):
        doc = {"results": [{"entity_id": "E1", "name": "N", "types": ["urn:entity:brand"],
                            "tags": [{"tag_id": "urn:tag:x:qloo:y", "name": "Y", "type": "urn:tag:x:qloo"}]}]}
        items, shape = locate_items(adapter.OP_SEED_DETAIL, doc)
        self.assertEqual((shape, [p for p, _ in items]), ("results", ["/results/0"]))
        view = item_view("seed_entity", items[0][1], items[0][0])
        self.assertEqual(view["tags"][0]["id"], "urn:tag:x:qloo:y")

    def test_insights_entities_keep_measurements_and_explainability(self):
        doc = {"success": True, "results": {"entities": [{
            "entity_id": "E2", "name": "N", "type": "urn:entity", "subtype": "urn:entity:movie",
            "tags": [{"id": "urn:tag:style:qloo:a", "name": "A", "type": "urn:tag:style:qloo"}],
            "query": {"affinity": 0.5, "measurements": {"audience_growth": 0},
                      "explainability": {"signal.interests.entities": [{"entity_id": "E1", "score": 1}]}}}]},
            "query": {"explainability": {}}}
        outcome = classify(adapter.OP_RELATED, ProcessResult(0, json.dumps(doc), "", 1))
        self.assertEqual((outcome.status, outcome.shape), ("ok", "results.entities"))
        view = item_view("related_entity", doc["results"]["entities"][0], "/results/entities/0")
        self.assertIn({"field": "query.measurements.audience_growth", "value": 0,
                       "pointer": "/results/entities/0/query/measurements/audience_growth"}, view["scores"])
        self.assertEqual(view["explanation"]["pointer"], "/results/entities/0/query/explainability")

    def test_tag_insights_keep_namespace_and_tag_value(self):
        doc = {"success": True, "results": {"tags": [{
            "tag_id": "urn:tag:genre:place:bar", "name": "Bar", "types": ["urn:entity:place"],
            "subtype": "urn:tag:genre:place", "tag_value": "urn:tag:genre:place:bar",
            "popularity": 0.9, "query": {"affinity": 1}}]}}
        outcome = classify(adapter.OP_SEED_TAGS, ProcessResult(0, json.dumps(doc), "", 1))
        self.assertEqual((outcome.status, outcome.shape), ("ok", "results.tags"))
        view = item_view("tag_insight", doc["results"]["tags"][0], "/results/tags/0")
        self.assertEqual(view["types"]["subtype"], "urn:tag:genre:place")
        self.assertEqual(view["tag_value"], "urn:tag:genre:place:bar")
        self.assertEqual(field_coverage("tag_insight", doc["results"]["tags"][0]), ([], []))


class Redaction(unittest.TestCase):
    def test_secret_value_and_header_patterns_are_removed(self):
        with mock.patch.dict(os.environ, {"QLOO_API_KEY": "sk-test-SHOULD-NOT-APPEAR"}):
            text = redact("failed for sk-test-SHOULD-NOT-APPEAR; header X-Api-Key: abcdef123456")
        self.assertNotIn("SHOULD-NOT-APPEAR", text)
        self.assertNotIn("abcdef123456", text)
        self.assertIn(REDACTED, text)

    def test_ordinary_error_text_survives(self):
        self.assertEqual(redact("authorization failed"), "authorization failed")


if __name__ == "__main__":
    unittest.main()

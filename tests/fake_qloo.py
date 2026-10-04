"""Test double for the `qloo` harness CLI. Used only by tests, never by the tool.

Behaviour is selected with FAKE_QLOO_MODE:
  ok      -> plausible-shaped invented answers (search echoes the query as the name)
  reject  -> every API command fails with HTTP 403 and echoes the key (redaction test)
Each non-dry-run invocation is appended to $FAKE_QLOO_LOG when set.
"""

import json
import os
import sys


def main() -> int:
    argv = sys.argv[1:]
    mode = os.environ.get("FAKE_QLOO_MODE", "ok")
    key = os.environ.get("QLOO_API_KEY", "")

    if argv == ["--version"]:
        print("0.1.26")
        return 0
    if argv[:2] == ["setup", "--status"]:
        print(json.dumps({"schemaVersion": "1.0", "qloo": {"ready": bool(key), "source": "environment" if key else "missing"}}))
        return 0
    if "--dry-run" in argv:
        print(json.dumps({"method": "GET", "url": "https://fake.invalid/" + "/".join(argv[:2]), "params": {"argv": argv[2:]}}))
        return 0

    log = os.environ.get("FAKE_QLOO_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(argv) + "\n")

    if mode == "reject":
        print(json.dumps({"error": True, "code": "API_ERROR", "message": f"API request failed: 403 Forbidden (key {key})"}))
        return 5

    flags = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    if argv[:2] == ["api", "search"]:
        print(json.dumps([{"entity_id": "FAKE-ENT-1", "name": flags["--query"], "types": ["urn:entity:brand"]}]))
    elif argv[:2] == ["api", "entity"]:
        print(json.dumps({"entity_id": flags["--id"], "name": "Fake Entity", "tags": []}))
    elif argv[:2] == ["api", "insights"]:
        print(json.dumps([{"entity_id": "FAKE-REL-1", "name": "Fake Related", "subtype": flags["--type"],
                           "query": {"affinity": 0.5}, "tags": [{"id": "fake:tag:1", "name": "Fake Tag", "type": "fake:tag"}]}]))
    elif argv[:2] == ["exec", "entity_tags"]:
        print(json.dumps({"status": "ok", "results": [{"id": "fake:tag:1", "name": "Fake Tag", "type": "fake:tag", "affinity": 0.4}]}))
    else:
        print(json.dumps({"error": True, "code": "BAD_USAGE", "message": "unknown command"}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

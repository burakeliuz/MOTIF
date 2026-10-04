"""Small shared helpers: time, local IDs, JSON files, JSON Pointers, paths."""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
FIXTURES_DIR = REPO_ROOT / "fixtures" / "synthetic"

# Every identifier minted by this tool starts with this prefix so it can never
# be mistaken for a Qloo identifier.
LOCAL_PREFIX = "local:"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id(mode: str, now: Optional[datetime] = None) -> str:
    now = now or utc_now()
    return f"{mode}-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(2)}"


def request_id(seq: int) -> str:
    return f"{LOCAL_PREFIX}req:{seq:04d}"


def evidence_id(request_seq: int, item_index: int) -> str:
    return f"{LOCAL_PREFIX}obs:{request_seq:04d}-{item_index:03d}"


def data_root(override: Optional[str] = None) -> Path:
    if override:
        return Path(override)
    env = os.environ.get("MOTIF_DATA_DIR")
    return Path(env) if env else REPO_ROOT / "data"


class RunPaths:
    """Where one run's raw and normalized outputs live (kept in separate trees)."""

    def __init__(self, root: Path, run_id: str):
        self.root = root
        self.run_id = run_id
        self.raw_dir = root / "raw" / run_id
        self.responses_dir = self.raw_dir / "responses"
        self.normalized_dir = root / "normalized" / run_id

    @property
    def run_record(self) -> Path:
        return self.raw_dir / "run.json"

    @property
    def requests_log(self) -> Path:
        return self.raw_dir / "requests.jsonl"

    def response_file(self, seq: int, suffix: str = "json") -> Path:
        return self.responses_dir / f"{seq:04d}.{suffix}"

    def rel(self, path: Path) -> str:
        """Path relative to the data root, used in provenance references."""
        return path.relative_to(self.root).as_posix()


# --- JSON files -----------------------------------------------------------


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def append_jsonl(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> List[Any]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# --- JSON Pointer (RFC 6901) ------------------------------------------------


def _escape(token: Any) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def join_pointer(base: str, *tokens: Any) -> str:
    return base + "".join("/" + _escape(t) for t in tokens)


def split_pointer(pointer: str) -> List[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def resolve_pointer(doc: Any, pointer: str) -> Any:
    node = doc
    for token in split_pointer(pointer):
        if isinstance(node, list):
            node = node[int(token)]
        elif isinstance(node, dict):
            node = node[token]
        else:
            raise KeyError(pointer)
    return node


def get_path(obj: Any, path: Sequence[str]) -> Any:
    """Return obj[path[0]][path[1]]... or None when any step is absent."""
    node = obj
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def has_path(obj: Any, path: Sequence[str]) -> bool:
    node = obj
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return False
        node = node[key]
    return True


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def iter_unique(items: Iterable[Any]) -> Iterator[Any]:
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            yield item

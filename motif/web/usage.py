"""Daily usage counters that survive a process restart and concurrent requests.

Counters live in one JSON file under the data directory and are changed only
under an exclusive file lock with an atomic replace, so two threads or two
processes cannot both pass a cap. Spending is reserved before the call and the
unused part is released afterwards. If the file cannot be read or written, the
reservation fails: MOTIF then makes no new paid call (fail-closed).

Limit: the counters persist as long as the data directory does. On a host whose
disk is reset on restart or redeploy (for example a free Render instance), they
reset too; provider-side limits (the Anthropic workspace spend limit, the Qloo
key's own quota) remain the outer guard.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional

from motif_spike.util import iso, utc_now


class UsageError(RuntimeError):
    """The counters could not be read or written; callers must not spend."""


class UsageStore:
    def __init__(self, path: Path, clock=None):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.clock = clock or (lambda: iso(utc_now())[:10])
        self._thread_lock = threading.Lock()

    @contextmanager
    def _locked(self) -> Iterator[Dict[str, Dict[str, int]]]:
        with self._thread_lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.lock_path, "a+") as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    try:
                        data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
                        if not isinstance(data, dict):
                            raise ValueError("usage file is not an object")
                        yield data
                        tmp = self.path.with_suffix(".tmp")
                        tmp.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
                        os.replace(tmp, self.path)
                    finally:
                        fcntl.flock(lock, fcntl.LOCK_UN)
            except (OSError, ValueError) as exc:
                raise UsageError(f"usage counters unavailable ({type(exc).__name__})") from exc

    def reserve(self, kind: str, amount: int, cap: int) -> bool:
        """Add `amount` to today's `kind` if the total stays within `cap`. False when it would not."""
        with self._locked() as data:
            day = data.setdefault(self.clock(), {})
            if day.get(kind, 0) + amount > cap:
                return False
            day[kind] = day.get(kind, 0) + amount
            for old in [d for d in data if d < self.clock()][:-7]:  # keep a week of history
                del data[old]
            return True

    def release(self, kind: str, amount: int, day: Optional[str] = None) -> None:
        if amount <= 0:
            return
        with self._locked() as data:
            bucket = data.setdefault(day or self.clock(), {})
            bucket[kind] = max(0, bucket.get(kind, 0) - amount)

    def today(self) -> Dict[str, int]:
        with self._locked() as data:
            return dict(data.get(self.clock(), {}))

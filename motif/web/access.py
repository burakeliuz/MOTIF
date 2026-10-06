"""Temporary access gate for the review period: one shared password, checked server-side.

  MOTIF_ACCESS_PROTECTION  "on" (default) or "off". On is fail-closed: without a
                           password nothing behind the gate can be reached.
  MOTIF_ACCESS_PASSWORD    the password. Read from the environment only; never
                           printed, logged, stored, or sent to the browser.

A correct password creates a random session token kept in server memory and
sent as a Secure, HttpOnly, SameSite=Strict cookie. Failed attempts are limited
per client address and globally (the global limit also holds when the client
address can be spoofed through X-Forwarded-For).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Dict, Mapping, Optional

COOKIE = "motif_access"
SESSION_TTL_S = 12 * 3600
FAIL_WINDOW_S = 15 * 60
FAILS_PER_IP = 5
FAILS_GLOBAL = 30


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


class AccessGate:
    def __init__(self, enabled: bool, password: Optional[str], clock=time.time):
        self.enabled = enabled
        self._password = _digest(password) if password else None
        self.clock = clock
        self.tokens: Dict[str, float] = {}
        self.fails: Dict[str, deque] = defaultdict(deque)
        self.global_fails: deque = deque()
        self.lock = threading.Lock()

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "AccessGate":
        flag = env.get("MOTIF_ACCESS_PROTECTION", "on").strip().lower()
        return cls(flag not in ("off", "0", "false", "no"), env.get("MOTIF_ACCESS_PASSWORD") or None)

    @property
    def configured(self) -> bool:
        return self._password is not None

    def describe(self) -> str:
        if not self.enabled:
            return "access protection off"
        return "access protection on" + ("" if self.configured else " (no password set: access closed)")

    # -- checks --------------------------------------------------------------------

    def allowed(self, cookie_header: Optional[str]) -> bool:
        if not self.enabled:
            return True
        token = _cookie_value(cookie_header or "", COOKIE)
        if not token or not self.configured:
            return False
        with self.lock:
            expiry = self.tokens.get(token)
            if expiry is None:
                return False
            if expiry < self.clock():
                del self.tokens[token]
                return False
            return True

    def login(self, password: object, ip: str) -> (int, Dict[str, str], Optional[str]):
        """Return (http status, JSON body, new token or None)."""
        if not self.enabled:
            return 400, {"error": "Access protection is off."}, None
        if not self.configured:
            return 503, {"error": "Access is closed: no password is configured on the server.", "kind": "access_closed"}, None
        now = self.clock()
        with self.lock:
            for q in (self.fails[ip], self.global_fails):
                while q and now - q[0] > FAIL_WINDOW_S:
                    q.popleft()
            if len(self.fails[ip]) >= FAILS_PER_IP or len(self.global_fails) >= FAILS_GLOBAL:
                return 429, {"error": "Too many wrong attempts. Try again in 15 minutes.", "kind": "locked"}, None
            ok = isinstance(password, str) and hmac.compare_digest(_digest(password), self._password)
            if not ok:
                self.fails[ip].append(now)
                self.global_fails.append(now)
                return 401, {"error": "Wrong password.", "kind": "wrong_password"}, None
            self.fails.pop(ip, None)
            for t in [t for t, exp in self.tokens.items() if exp < now]:
                del self.tokens[t]
            token = secrets.token_urlsafe(32)
            self.tokens[token] = now + SESSION_TTL_S
            return 200, {"ok": True}, token

    @staticmethod
    def cookie(token: str) -> str:
        return f"{COOKIE}={token}; Path=/; Max-Age={SESSION_TTL_S}; HttpOnly; Secure; SameSite=Strict"


def _cookie_value(header: str, name: str) -> Optional[str]:
    for part in header.split(";"):
        key, _, value = part.strip().partition("=")
        if key == name and value:
            return value
    return None

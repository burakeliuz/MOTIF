"""Keep credentials out of every record, log line, and saved file.

The key normally lives only in the harness's private config, where MOTIF never
looks. If QLOO_API_KEY is set in the environment, its value is used in memory
for one purpose: replacing any occurrence in text with [REDACTED].
"""

from __future__ import annotations

import os
import re
from typing import Iterable, List, Mapping, Optional

# Environment variables whose values are secret. Only their presence is ever reported.
SECRET_ENV_VARS = ("QLOO_API_KEY",)

REDACTED = "[REDACTED]"

# "X-Api-Key: abc...", "api_key=abc...", "Authorization: Bearer abc..."
_HEADER_PATTERN = re.compile(
    r"(?i)(\b(?:x-api-key|api[_-]?key|authorization)[\"']?\s*[:=]\s*[\"']?(?:bearer\s+)?)([A-Za-z0-9._\-+/=]{6,})"
)
_BEARER_PATTERN = re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._\-+/=]{12,})")
_FLAG_PATTERN = re.compile(r"(--api-key[= ])(\S+)")


def secret_values(env: Optional[Mapping[str, str]] = None) -> List[str]:
    env = os.environ if env is None else env
    values = []
    for name in SECRET_ENV_VARS:
        value = env.get(name)
        if value and len(value.strip()) >= 4:
            values.append(value.strip())
    return values


def redact(text: str, extra_secrets: Iterable[str] = (), env: Optional[Mapping[str, str]] = None) -> str:
    if not text:
        return text
    for value in list(secret_values(env)) + [s for s in extra_secrets if s and len(s) >= 4]:
        text = text.replace(value, REDACTED)
    for pattern in (_FLAG_PATTERN, _HEADER_PATTERN, _BEARER_PATTERN):
        text = pattern.sub(lambda m: m.group(1) + REDACTED, text)
    return text


def contains_secret(text: str, env: Optional[Mapping[str, str]] = None) -> bool:
    return any(value in text for value in secret_values(env))


def truncate(text: str, limit: int = 2000) -> str:
    return text if len(text) <= limit else text[:limit] + f"... [truncated {len(text) - limit} chars]"

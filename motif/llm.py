"""Optional LLM prose writer. It never classifies, scores, or selects.

Configuration (environment only; the key is never printed, logged, or stored):
  MOTIF_ANTHROPIC_API_KEY  Anthropic key read explicitly by MOTIF (not the SDK's default variable)
  MOTIF_LLM_MODEL          model ID, default "claude-sonnet-5-5"; MOTIF never switches models on its own
  MOTIF_LLM_EFFORT         optional output effort (default "low")
  MOTIF_LLM_TIMEOUT_S      request timeout in seconds (default 30)
  MOTIF_LLM_MAX_CALLS      cap on API calls per UTC day, counted in the call ledger (default 20)
  MOTIF_LLM_PROVIDER       optional; "anthropic" is the only provider implemented, "off" disables

Every real API call (model check or generation, retries included) is appended to
a call ledger (data/llm_calls.jsonl, git-ignored) with its usage and an estimated
cost. Without a key, the SDK, or remaining budget, MOTIF uses labelled template prose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from motif_spike.util import iso, utc_now

from .brief import AXIS_LABELS, open_axes, template_prose, validate_prose

PROMPT_VERSION = "prose-0.3"
DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_OUTPUT_TOKENS = 1500
# USD per million tokens (input, output), from https://platform.claude.com/docs/en/about-claude/pricing (read 2026-10-06).
PRICES = {"claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}
PRICE_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing (read 2026-10-06)"
SYSTEM = (
    "You write a short perfumer brief from a structured result produced by a deterministic engine. "
    "Use only facts in the JSON. Qloo supplied only the literal descriptors (example_qloo_descriptors); grouping them into motifs, "
    "the sensory targets, and the materials are MOTIF's creative translation, so never say that Qloo returned motifs or groups. "
    "Do not add materials, notes, numbers, percentages, sensory targets, or claims about "
    "how the scent will be received. Name every axis listed under open_axes as open, using its label. Keep the "
    "difference between what Qloo returned (cultural descriptors) and MOTIF's creative translation visible. "
    "Plain English, at most 160 words, no headings."
)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    price = PRICES.get(model)
    if not price:
        return None
    return round(input_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1], 6)


class CallLedger:
    """Counts and records real API calls. Never stores prompts, responses, or keys."""

    def __init__(self, path: Optional[Path], max_calls_per_day: int):
        self.path = Path(path) if path else None
        self.max_calls = max_calls_per_day
        self.memory: list = []

    def _rows(self):
        if self.path and self.path.exists():
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return list(self.memory)

    def calls_today(self) -> int:
        today = iso(utc_now())[:10]
        return sum(1 for r in self._rows() if r.get("at", "")[:10] == today)

    def allow(self) -> bool:
        return self.calls_today() < self.max_calls

    def record(self, row: Dict[str, Any]) -> None:
        row = dict(row, at=iso(utc_now()))
        self.memory.append(row)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, sort_keys=True) + "\n")


class BudgetExhausted(RuntimeError):
    pass


class AnthropicProseWriter:
    def __init__(self, api_key: str, model: str, effort: str = "low", timeout_s: float = 30.0,
                 ledger: Optional[CallLedger] = None, client: Any = None):
        self.model = model
        self.effort = effort
        self.ledger = ledger or CallLedger(None, 20)
        if client is None:
            import anthropic  # optional dependency, imported only when configured
            client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=0)
        self.client = client

    def describe(self) -> Dict[str, Any]:
        return {"provider": "anthropic", "model": self.model, "effort": self.effort, "prompt_version": PROMPT_VERSION}

    def _guard(self) -> None:
        if not self.ledger.allow():
            raise BudgetExhausted(f"LLM call budget reached ({self.ledger.max_calls} per day)")

    def check_model(self) -> Dict[str, Any]:
        """One real API call: confirm the configured model is available to this key."""
        self._guard()
        try:
            info = self.client.models.retrieve(self.model)
        except Exception as exc:
            self.ledger.record({"kind": "models.retrieve", "model": self.model, "status": "error", "error": type(exc).__name__})
            raise
        self.ledger.record({"kind": "models.retrieve", "model": self.model, "status": "ok"})
        return {"id": getattr(info, "id", self.model), "display_name": getattr(info, "display_name", None)}

    def write(self, payload: Dict[str, Any], feedback: Optional[str] = None) -> str:
        self._guard()
        content = "Engine result:\n" + json.dumps(payload, indent=1, sort_keys=True)
        if feedback:
            content += "\n\nYour previous text was rejected: " + feedback + "\nWrite it again without these problems."
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=SYSTEM,
                output_config={"effort": self.effort},
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:
            self.ledger.record({"kind": "messages.create", "model": self.model, "status": "error", "error": type(exc).__name__})
            raise
        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "input_tokens", 0) or 0
        tokens_out = getattr(usage, "output_tokens", 0) or 0
        stop = getattr(response, "stop_reason", None)
        self.ledger.record({"kind": "messages.create", "model": getattr(response, "model", self.model), "status": "ok",
                            "stop_reason": stop, "input_tokens": tokens_in, "output_tokens": tokens_out,
                            "estimated_cost_usd": estimate_cost(self.model, tokens_in, tokens_out),
                            "price_source": PRICE_SOURCE})
        self.last_usage = {"input_tokens": tokens_in, "output_tokens": tokens_out, "stop_reason": stop,
                           "estimated_cost_usd": estimate_cost(self.model, tokens_in, tokens_out)}
        if stop in ("refusal", "max_tokens"):
            raise RuntimeError(f"no usable text (stop_reason={stop})")
        return "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()


def writer_from_env(env: Mapping[str, str], ledger_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return {'writer': obj or None, 'status': text}. Never raises for missing configuration."""
    provider = env.get("MOTIF_LLM_PROVIDER", "anthropic").strip().lower() or "anthropic"
    if provider == "off":
        return {"writer": None, "status": "LLM disabled (MOTIF_LLM_PROVIDER=off): template prose"}
    if provider != "anthropic":
        return {"writer": None, "status": f"provider {provider!r} not implemented: template prose"}
    key = env.get("MOTIF_ANTHROPIC_API_KEY", "")
    if not key:
        return {"writer": None, "status": "MOTIF_ANTHROPIC_API_KEY unset: template prose"}
    model = env.get("MOTIF_LLM_MODEL", "").strip() or DEFAULT_MODEL
    try:
        max_calls = int(env.get("MOTIF_LLM_MAX_CALLS", "20"))
        timeout = float(env.get("MOTIF_LLM_TIMEOUT_S", "30"))
    except ValueError:
        return {"writer": None, "status": "invalid MOTIF_LLM_MAX_CALLS or MOTIF_LLM_TIMEOUT_S: template prose"}
    ledger = CallLedger(ledger_path, max_calls)
    try:
        writer = AnthropicProseWriter(key, model, env.get("MOTIF_LLM_EFFORT", "low"), timeout, ledger)
    except ImportError:
        return {"writer": None, "status": "the 'anthropic' package is not installed: template prose"}
    return {"writer": writer, "status": f"LLM prose enabled ({model})"}


def prose_payload(seed_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Only what the prose needs: no raw Qloo bodies, no IDs, no scores."""
    axes = result["axes"]
    evidence = {e["evidence_id"]: e for e in result["evidence"]}
    motifs = []
    for name, info in sorted(result["motifs"].items()):
        if not info["active"]:
            continue
        examples = sorted({evidence[i]["tag_name"] for i in info["support_evidence_ids"] if i in evidence})[:4]
        motifs.append({"motif": name, "strength": info["strength"], "sources": info["source_kinds"],
                       "example_qloo_descriptors": examples,
                       "has_translation_rule": name not in result["unmapped_active_motifs"]})
    return {
        "reference": seed_name,
        "outcome": result["outcome_meaning"],
        "active_motifs": motifs,
        "targets": {a: {"pole": v["value"], "label": AXIS_LABELS[a], "evidence_strength": v["evidence_strength"],
                        "only_from_related_entities": v.get("relations_only", False)}
                    for a, v in axes.items() if v["state"] == "target"},
        "open_axes": [AXIS_LABELS[a] for a in open_axes(result)],
        "materials": [{"name": m["name"], "slot": m["slot"],
                       "creative_choices_not_from_evidence": [AXIS_LABELS[u["axis"]] + ": " + u["pole"]
                                                              for u in m["unrequested_properties"]]}
                      for m in result["materials"].get("selected", [])],
        "material_status": result["materials"]["status"],
    }


def write_prose(seed_name: str, result: Dict[str, Any], writer: Any = None, max_attempts: int = 2) -> Dict[str, Any]:
    template = template_prose(seed_name, result)
    if writer is None:
        return {"author": "template", "text": template, "llm": None, "note": "template prose (no LLM configured)"}
    payload = prose_payload(seed_name, result)
    feedback = None
    attempts = []
    for _ in range(max_attempts):
        try:
            text = writer.write(payload, feedback)
        except Exception as exc:  # API error, refusal, budget: template prose, labelled, never shown as LLM output
            attempts.append({"error": type(exc).__name__, "detail": str(exc)[:160] if isinstance(exc, (BudgetExhausted, RuntimeError)) else None})
            break
        problems = validate_prose(text, result)
        attempts.append({"problems": problems, "usage": getattr(writer, "last_usage", None)})
        if not problems:
            return {"author": "llm", "text": text, "llm": dict(writer.describe(), attempts=attempts), "note": None}
        feedback = "; ".join(problems)
    failed_call = any("error" in a for a in attempts)
    return {"author": "template", "text": template, "llm": dict(writer.describe(), attempts=attempts),
            "note": ("LLM call failed; template prose shown instead" if failed_call
                     else "LLM text failed validation; template prose shown instead")}

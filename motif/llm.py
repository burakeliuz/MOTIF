"""Optional LLM prose writer. It never classifies, scores, or selects.

Configuration (environment only; keys are never read from files or printed):
  MOTIF_LLM_PROVIDER   "anthropic" (the only provider implemented)
  MOTIF_LLM_MODEL      model ID, required: no model is chosen implicitly
  MOTIF_LLM_EFFORT     optional output effort (default "low")
  ANTHROPIC_API_KEY    read by the official SDK itself

Without a provider, model, key, or the `anthropic` package, MOTIF uses
template prose and labels it so.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional

from .brief import AXIS_LABELS, open_axes, template_prose, validate_prose

PROMPT_VERSION = "prose-0.1"
SYSTEM = (
    "You write a short perfumer brief from a structured result produced by a deterministic engine. "
    "Use only facts in the JSON. Do not add materials, notes, numbers, percentages, or sensory targets. "
    "Name every axis listed under open_axes as open, using its label. Do not claim that anyone will like "
    "the scent or that anything is proven. Plain English, at most 160 words, no headings."
)


class AnthropicProseWriter:
    def __init__(self, model: str, effort: str = "low", client: Any = None):
        self.model = model
        self.effort = effort
        if client is None:
            import anthropic  # optional dependency, imported only when configured
            client = anthropic.Anthropic()
        self.client = client

    def describe(self) -> Dict[str, Any]:
        return {"provider": "anthropic", "model": self.model, "effort": self.effort, "prompt_version": PROMPT_VERSION}

    def write(self, payload: Dict[str, Any], feedback: Optional[str] = None) -> str:
        content = "Engine result:\n" + json.dumps(payload, indent=1, sort_keys=True)
        if feedback:
            content += "\n\nYour previous text was rejected: " + feedback + "\nWrite it again without these problems."
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM,
            output_config={"effort": self.effort},
            messages=[{"role": "user", "content": content}],
        )
        if getattr(response, "stop_reason", None) == "refusal":
            raise RuntimeError("model refused")
        return "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()


def writer_from_env(env: Mapping[str, str]) -> Dict[str, Any]:
    """Return {'writer': obj or None, 'status': text}. Never raises for missing configuration."""
    provider = env.get("MOTIF_LLM_PROVIDER", "").strip().lower()
    model = env.get("MOTIF_LLM_MODEL", "").strip()
    if not provider:
        return {"writer": None, "status": "no LLM configured (MOTIF_LLM_PROVIDER unset): template prose"}
    if provider != "anthropic":
        return {"writer": None, "status": f"provider {provider!r} not implemented: template prose"}
    if not model:
        return {"writer": None, "status": "MOTIF_LLM_MODEL unset: template prose (no model is chosen implicitly)"}
    if not env.get("ANTHROPIC_API_KEY"):
        return {"writer": None, "status": "ANTHROPIC_API_KEY unset: template prose"}
    try:
        writer = AnthropicProseWriter(model, env.get("MOTIF_LLM_EFFORT", "low"))
    except ImportError:
        return {"writer": None, "status": "the 'anthropic' package is not installed: template prose"}
    return {"writer": writer, "status": "LLM prose enabled"}


def prose_payload(seed_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    axes = result["axes"]
    evidence = {e["evidence_id"]: e for e in result["evidence"]}
    motifs = []
    for name, info in sorted(result["motifs"].items()):
        if not info["active"]:
            continue
        examples = sorted({evidence[i]["tag_name"] for i in info["support_evidence_ids"] if i in evidence})[:4]
        motifs.append({"motif": name, "strength": info["strength"], "sources": info["source_kinds"],
                       "example_descriptors": examples, "has_translation_rule": name not in result["unmapped_active_motifs"]})
    return {
        "reference": seed_name,
        "outcome": result["outcome_meaning"],
        "active_motifs": motifs,
        "targets": {a: {"pole": v["value"], "label": AXIS_LABELS[a], "evidence_strength": v["evidence_strength"],
                        "relations_only": v.get("relations_only", False)}
                    for a, v in axes.items() if v["state"] == "target"},
        "open_axes": [AXIS_LABELS[a] for a in open_axes(result)],
        "materials": [{"name": m["name"], "slot": m["slot"],
                       "creative_choices": [AXIS_LABELS[u["axis"]] + ": " + u["pole"] for u in m["unrequested_properties"]]}
                      for m in result["materials"].get("selected", [])],
        "material_status": result["materials"]["status"],
    }


def write_prose(seed_name: str, result: Dict[str, Any], writer: Any = None, max_attempts: int = 2) -> Dict[str, Any]:
    template = template_prose(seed_name, result)
    if writer is None:
        return {"author": "template", "text": template, "llm": None, "note": "template prose (no LLM)"}
    payload = prose_payload(seed_name, result)
    feedback = None
    attempts = []
    for _ in range(max_attempts):
        try:
            text = writer.write(payload, feedback)
        except Exception as exc:  # network, refusal, SDK errors: fall back to the template, labelled
            attempts.append({"error": type(exc).__name__})
            break
        problems = validate_prose(text, result)
        attempts.append({"problems": problems})
        if not problems:
            return {"author": "llm", "text": text, "llm": dict(writer.describe(), attempts=attempts), "note": None}
        feedback = "; ".join(problems)
    return {"author": "template", "text": template, "llm": dict(writer.describe(), attempts=attempts),
            "note": "LLM text failed validation or the call failed; template prose used"}

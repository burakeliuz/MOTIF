"""Whether the web server may make paid LLM calls, given where its call counter lives.

MOTIF's LLM cap is a counter on disk (`llm_calls.jsonl` in the data directory).
A cap only protects spending if the counter survives a restart. On a host whose
disk is reset on restart, redeploy, or idle spin-down (a free Render web service
has no persistent disk), the counter would start again at zero, so the cap would
not hold. MOTIF_LLM_BUDGET_GUARD decides what happens then:

  auto      (default) On Render (the RENDER variable is set), LLM calls are allowed
            only when MOTIF_DATA_DIR is set and the data directory is on its own
            persistent mount (a Render disk). Elsewhere, the local disk is trusted.
            Otherwise Claude is paused: briefs use MOTIF's labelled template and
            interpretation suggestions are unavailable.
  provider  The owner confirms that a spend limit is set on the Anthropic side (a
            workspace spend limit in the Claude Console). Calls are allowed; the
            local counter still applies but may reset on restart.
  off       No LLM calls.

Nothing here reads or prints a key; it only looks at variable names and mounts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

EPHEMERAL_FS = {"tmpfs", "ramfs", "overlay", "aufs", "squashfs"}
PAUSED_NOTE = ("Claude is paused on this server because its call counter would not survive a restart, "
               "so MOTIF's fixed template wrote this brief.")


def mount_of(path: Path, mounts_text: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """(mount point, filesystem type) of the deepest mount that contains `path`, from /proc/self/mounts."""
    if mounts_text is None:
        try:
            mounts_text = Path("/proc/self/mounts").read_text(encoding="utf-8")
        except OSError:
            return None
    target = str(Path(path).resolve()) if Path(path).exists() else str(Path(path).absolute())
    best = None
    for line in mounts_text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        point = parts[1].replace("\\040", " ")
        inside = target == point or target.startswith(point.rstrip("/") + "/")
        if inside and (best is None or len(point) > len(best[0])):
            best = (point, parts[2])
    return best


def llm_guard(env: Mapping[str, str], data_dir: Path, mounts_text: Optional[str] = None) -> Dict[str, object]:
    """{'mode', 'allowed', 'durable', 'reason'}; never raises."""
    mode = (env.get("MOTIF_LLM_BUDGET_GUARD") or "auto").strip().lower()
    if mode not in ("auto", "provider", "off"):
        return {"mode": mode, "allowed": False, "durable": False,
                "reason": "MOTIF_LLM_BUDGET_GUARD has an unknown value, so Claude is paused (fail-closed)."}
    if mode == "off":
        return {"mode": mode, "allowed": False, "durable": False, "reason": "Claude is switched off on this server."}
    on_render = bool(env.get("RENDER"))
    durable = True
    reason = "local data directory"
    if on_render:
        durable = False
        reason = "on Render without a persistent disk for the data directory"
        if env.get("MOTIF_DATA_DIR"):
            found = mount_of(data_dir, mounts_text)
            if found and found[0] != "/" and found[1] not in EPHEMERAL_FS:
                durable, reason = True, f"data directory on its own mount ({found[1]})"
    if mode == "provider":
        return {"mode": mode, "allowed": True, "durable": durable,
                "reason": "the owner confirmed a provider-side spend limit" + ("" if durable else "; local counters may reset on restart")}
    return {"mode": mode, "allowed": durable, "durable": durable, "reason": reason}

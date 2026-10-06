"""Versioned design configuration (lexicon, rules, palette, engine parameters)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from motif_spike.util import CONFIG_DIR, read_json

AXES = ("warm_cool", "light_dense", "raw_polished", "natural_synthetic", "intimate_projecting", "sweet_dry")


@dataclass(frozen=True)
class EngineConfig:
    lexicon: Dict[str, Any]
    rules: Dict[str, Any]
    palette: Dict[str, Any]
    params: Dict[str, Any]

    @property
    def versions(self) -> Dict[str, str]:
        return {
            "lexicon": self.lexicon["lexicon_version"],
            "rules": self.rules["registry_version"],
            "palette": self.palette["palette_version"],
            "params": self.params["params_version"],
        }

    def poles(self) -> Dict[str, tuple]:
        return {a["key"]: (a["first_pole"], a["second_pole"]) for a in self.rules["axes"]}


def load_config(config_dir: Optional[Path] = None) -> EngineConfig:
    base = Path(config_dir) if config_dir else CONFIG_DIR
    config = EngineConfig(
        lexicon=read_json(base / "motif_lexicon.json"),
        rules=read_json(base / "draft_rules.json"),
        palette=read_json(base / "material_palette.json"),
        params=read_json(base / "engine_params.json"),
    )
    axes = tuple(a["key"] for a in config.rules["axes"])
    if axes != AXES:
        raise ValueError(f"draft_rules.json axes changed: {axes}")
    return config

"""Versioned design configuration: the legacy rule engine (lexicon, rules, palette, parameters) and the
continuous engine (lexicon, motif scoring, motif-to-sensory model, aggregation parameters)."""

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


@dataclass(frozen=True)
class ContinuousConfig:
    lexicon: Dict[str, Any]
    scoring: Dict[str, Any]
    vectors: Dict[str, Any]
    params: Dict[str, Any]
    library: Optional[Dict[str, Any]] = None  # olfactory directions (scent architecture)

    @property
    def versions(self) -> Dict[str, str]:
        out = {
            "lexicon": self.lexicon["lexicon_version"],
            "scoring": self.scoring["scoring_version"],
            "sensory_model": self.vectors["model_version"],
            "params": self.params["params_version"],
        }
        if self.library:
            out["olfactory"] = self.library["library_version"]
        return out


def load_continuous_config(config_dir: Optional[Path] = None) -> ContinuousConfig:
    base = Path(config_dir) if config_dir else CONFIG_DIR
    config = ContinuousConfig(
        lexicon=read_json(base / "motif_lexicon.json"),
        scoring=read_json(base / "motif_scoring.v1.json"),
        vectors=read_json(base / "motif_sensory_vectors.v1.json"),
        params=read_json(base / "continuous_params.v1.json"),
        library=read_json(base / "olfactory_directions.v1.json"),
    )
    if tuple(config.vectors["encoding"]) != AXES:
        raise ValueError(f"motif_sensory_vectors axes changed: {tuple(config.vectors['encoding'])}")
    unknown = set(config.vectors["motifs"]) - set(config.lexicon["cue_groups"])
    if unknown:
        raise ValueError(f"sensory model names motifs the lexicon does not define: {sorted(unknown)}")
    return config

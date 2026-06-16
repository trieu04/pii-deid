import os
import re
from pathlib import Path
from typing import Any

import yaml


class Config:
    def __init__(self, data: dict[str, Any]):
        self.salt: str = data.get("salt", "default-salt-change-me")
        self.field_mapping: dict[str, str] = data.get("field_mapping", {})
        self.processing: dict[str, Any] = data.get("processing", {})
        self.pseudonym: dict[str, Any] = data.get("pseudonym", {})
        self.api: dict[str, Any] = data.get("api", {})

    @property
    def ner_enabled(self) -> bool:
        return self.processing.get("ner_enabled", True)

    @property
    def ner_min_confidence(self) -> float:
        return self.processing.get("ner_min_confidence", 0.6)

    @property
    def max_depth(self) -> int:
        return self.processing.get("max_depth", 20)

    @property
    def upstream_url(self) -> str:
        return self.api.get("upstream_url", "")

    @property
    def upstream_timeout(self) -> int:
        return self.api.get("upstream_timeout", 30)


def _resolve_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        pattern = re.compile(r"\$\{(\w+)\}")
        matches = pattern.findall(value)
        for var in matches:
            value = value.replace(f"${{{var}}}", os.environ.get(var, ""))
        return value
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


_config: Config | None = None


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    resolved = _resolve_env_vars(raw)
    return Config(resolved)


def get_config() -> Config:
    global _config
    if _config is None:
        cfg_path = os.environ.get("CONFIG_PATH", "config.yaml")
        _config = load_config(cfg_path)
    return _config

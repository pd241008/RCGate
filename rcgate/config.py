"""YAML config loading with single-parent inheritance and dot access (constraint C4).

Every hyperparameter in this project lives in ``configs/*.yaml``. Nothing is a module
constant that affects a trained number.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import yaml

from .paths import CONFIGS_DIR

_MISSING = object()


class Config(Mapping):
    """Read-only nested mapping with ``cfg.a.b`` and ``cfg.get("a.b", default)``."""

    __slots__ = ("_data", "_source")

    def __init__(self, data: Mapping[str, Any] | None = None, source: Path | None = None):
        self._data = dict(data or {})
        self._source = source

    # -- Mapping protocol -------------------------------------------------
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, key: str) -> Any:
        try:
            value = object.__getattribute__(self, "_data")[key]
        except (AttributeError, KeyError) as exc:
            raise AttributeError(f"no config key {key!r} in {self.source or '<inline>'}") from exc
        return Config(value, self.source) if isinstance(value, dict) else value

    def __repr__(self) -> str:
        return f"Config({self._data!r})"

    # -- lookup -----------------------------------------------------------
    def get(self, dotted: str, default: Any = _MISSING) -> Any:  # type: ignore[override]
        """Look up ``"train.lr"``. Raises if absent and no default is given."""
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if default is _MISSING:
                    raise KeyError(f"missing config key {dotted!r} in {self._source or '<inline>'}")
                return default
            node = node[part]
        return Config(node, self._source) if isinstance(node, dict) else node

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

    @property
    def source(self) -> Path | None:
        return self._source


def _no_duplicate_keys(loader: yaml.SafeLoader, node, deep: bool = False):
    """Reject duplicate YAML keys.

    PyYAML silently keeps the last value for a repeated key, which once made a config
    declare 900 questions and silently use 1400. A duplicate key is always a mistake.
    """
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


yaml.SafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_keys
)


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: str | Path) -> Config:
    """Load a YAML config, resolving a single ``extends:`` parent relative to itself."""
    path = Path(path)
    with path.open() as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"config {path} must be a mapping, got {type(raw).__name__}")

    parent_ref = raw.pop("extends", None)
    if parent_ref is None:
        return Config(raw, path)

    parent_path = (path.parent / parent_ref).resolve()
    parent = load_config(parent_path)
    return Config(_deep_merge(parent.to_dict(), raw), path)


def load_named(name: str) -> Config:
    """Load ``configs/<name>.yaml``."""
    path = CONFIGS_DIR / (name if name.endswith(".yaml") else f"{name}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"no such config: {path}")
    return load_config(path)


def available_configs() -> list[str]:
    return sorted(p.stem for p in CONFIGS_DIR.glob("*.yaml"))


def write_config(path: str | Path, cfg: Config | Mapping) -> Path:
    """Persist a resolved config next to a run's results (constraint C4)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = cfg.to_dict() if isinstance(cfg, Config) else dict(cfg)
    header = "# resolved config, written by rcgate at run time\n"
    path.write_text(header + yaml.safe_dump(payload, sort_keys=True))
    return path

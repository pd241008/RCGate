"""Disk cache and budget guard for every outbound API call (constraint C3).

Nothing in this project calls a network endpoint directly. Every LLM or search call goes
through :class:`DiskCache.call`, which is keyed by a hash of
``(provider, model, prompt, params)`` and honours the ``--dry-run`` flag and the
``max_usd`` / ``max_calls`` caps from ``configs/budget.yaml``.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..paths import CACHE_DIR


class DryRunMiss(RuntimeError):
    """Raised in ``--dry-run`` when a call is not already cached."""


class BudgetExceeded(RuntimeError):
    """Raised when ``max_calls`` or ``max_usd`` would be exceeded."""


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    blocked: int = 0
    calls_made: int = 0
    usd_spent: float = 0.0
    api_seconds: float = 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "blocked": self.blocked,
            "calls_made": self.calls_made,
            "usd_spent": round(self.usd_spent, 6),
            "api_seconds": round(self.api_seconds, 3),
        }


@dataclass
class Budget:
    max_usd: float | None = None
    max_calls: int | None = None
    dry_run: bool = False

    @classmethod
    def from_config(cls, cfg) -> Budget:
        budget = cfg.get("budget", {}) if cfg is not None else {}
        return cls(
            max_usd=budget.get("max_usd"),
            max_calls=budget.get("max_calls"),
            dry_run=bool(budget.get("dry_run", False)),
        )


def make_key(provider: str, model: str, prompt: str, params: Mapping | None = None) -> str:
    """Stable content hash. ``params`` is sorted so dict ordering cannot change the key."""
    blob = json.dumps(
        {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "params": dict(sorted((params or {}).items())),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class DiskCache:
    """Sharded JSON cache. Payload shape is ``{"key", "meta", "value"}``."""

    root: Path = field(default_factory=lambda: CACHE_DIR)
    budget: Budget = field(default_factory=Budget)
    stats: CacheStats = field(default_factory=CacheStats)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- paths ------------------------------------------------------------
    def path_for(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    # -- raw io -----------------------------------------------------------
    def get(self, key: str) -> dict | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None

    def put(self, key: str, value: Any, meta: Mapping | None = None) -> None:
        path = self.path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"key": key, "meta": dict(meta or {}), "value": value}, ensure_ascii=False)
        )

    def has(self, key: str) -> bool:
        return self.path_for(key).exists()

    # -- guarded call -----------------------------------------------------
    def call(
        self,
        provider: str,
        model: str,
        prompt: str,
        fn,
        *,
        params: Mapping | None = None,
        cost_usd: float = 0.0,
        max_tokens: int = 512,
    ) -> Any:
        """Return the cached value for this call, or invoke ``fn`` once and cache it.

        ``fn`` receives a single ``prompt: str`` argument. Tests inject a fake ``fn``
        instead of a network client, which is why no test ever touches the network.
        """
        key = make_key(provider, model, prompt, params)
        record = self.get(key)
        if record is not None:
            self.stats.hits += 1
            return record["value"]

        self.stats.misses += 1

        if self.budget.dry_run:
            self.stats.blocked += 1
            raise DryRunMiss(
                f"dry-run: {provider}/{model} call is not cached (key={key[:12]}); "
                "rerun without --dry-run to spend budget"
            )

        if self.budget.max_calls is not None and self.stats.calls_made + 1 > self.budget.max_calls:
            self.stats.blocked += 1
            raise BudgetExceeded(f"max_calls={self.budget.max_calls} reached")
        if self.budget.max_usd is not None and self.stats.usd_spent + cost_usd > self.budget.max_usd:
            self.stats.blocked += 1
            raise BudgetExceeded(f"max_usd={self.budget.max_usd} would be exceeded")

        started = time.perf_counter()
        value = fn(prompt)
        self.stats.api_seconds += time.perf_counter() - started

        self.stats.calls_made += 1
        self.stats.usd_spent += cost_usd
        self.put(
            key,
            value,
            meta={
                "provider": provider,
                "model": model,
                "params": dict(params or {}),
                "max_tokens": max_tokens,
                "cost_usd": cost_usd,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        return value

    def report(self) -> dict[str, float | int]:
        return self.stats.as_dict()


def cache_from_config(cfg=None, root: Path | None = None, dry_run: bool | None = None) -> DiskCache:
    budget = Budget.from_config(cfg)
    if dry_run is not None:
        budget.dry_run = dry_run
    return DiskCache(root=root or CACHE_DIR, budget=budget)

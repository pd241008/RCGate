"""Seeding, parameter counting, timing, and git provenance (constraint C4)."""

from __future__ import annotations

import json
import os
import random
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch


def set_seed(seed: int) -> None:
    """Seed Python, NumPy and torch. Called once at the top of every run."""
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def count_parameters(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def device() -> torch.device:
    return torch.device("cpu")


def git_hash(repo: str | Path | None = None) -> str:
    """Short git hash of HEAD, or ``unknown`` outside a repo. Recorded next to results."""
    cwd = str(repo) if repo is not None else None
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd,
            check=True,
        )
        return out.stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


@dataclass
class Timing:
    """Wall-clock accounting. Every run reports these (reviewer attack 3)."""

    wall_s: float = 0.0
    train_s: float = 0.0
    predict_s: float = 0.0
    api_calls: int = 0
    api_usd: float = 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {
            "wall_s": round(self.wall_s, 3),
            "train_s": round(self.train_s, 3),
            "predict_s": round(self.predict_s, 3),
            "api_calls": self.api_calls,
            "api_usd": round(self.api_usd, 4),
        }


@contextmanager
def timed(target: str = "wall") -> Iterator[dict[str, float]]:
    """Context manager returning ``{name: elapsed_seconds}``."""
    acc: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield acc
    finally:
        acc[target] = time.perf_counter() - start


def dump_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))

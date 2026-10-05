"""Shared run pipeline: build splits, fit one variant, evaluate, persist artefacts.

Kept separate from the CLI so ``train.py``, ``evaluate.py`` and the tests all drive the
same code path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config, write_config
from .utils import Timing, git_hash, set_seed


@dataclass
class RunContext:
    """Everything a training run needs, resolved once from a config."""

    cfg: Config
    variant: str
    seed: int
    table: Path
    out_dir: Path
    git: str = "unknown"
    timing: Timing | None = None

    @classmethod
    def build(cls, cfg: Config, variant: str, seed: int, table: Path | None = None) -> RunContext:
        from .paths import PROJECT_ROOT

        base = cfg.get("report.out_dir", "results/summary")
        out_dir = PROJECT_ROOT / base / str(cfg.get("report.tag", "run")) / f"{variant}_seed{seed}"
        return cls(
            cfg=cfg,
            variant=variant,
            seed=seed,
            table=Path(table) if table else PROJECT_ROOT / str(cfg.get("data.table")),
            out_dir=out_dir,
            git=git_hash(PROJECT_ROOT),
            timing=Timing(),
        )

    def start(self) -> None:
        set_seed(self.seed)

    def provenance(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "seed": self.seed,
            "git": self.git,
            "config": self.cfg.source.name if self.cfg.source else "inline",
            "table": str(self.table),
        }

    def persist_config(self) -> Path:
        """Constraint C4: the run's resolved config lands next to its results."""
        path = self.out_dir / "config.yaml"
        write_config(path, self.cfg)
        return path


def load_table(path: str | Path):
    """Read a parquet signal table and validate it against the data contract."""
    import pandas as pd

    from .data.schema import validate

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"signal table not found: {path} (build it first)")
    df = pd.read_parquet(path)
    validate(df).raise_if_failed()
    return df


def train_variant(ctx: RunContext) -> Any:
    """Fit one variant. Implemented in M3; kept as a single entry point."""
    raise NotImplementedError("train_variant is wired up in milestone M3")


def load_config_or_die(name_or_path: str) -> Config:
    from .config import load_config, load_named

    if name_or_path.endswith(".yaml") or "/" in name_or_path:
        return load_config(name_or_path)
    return load_named(name_or_path)

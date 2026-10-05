"""Shared run pipeline: build splits, fit one variant, evaluate, persist artefacts.

Kept separate from the CLI so ``train.py``, ``evaluate.py`` and the tests all drive the
same code path. Every artefact written here carries the config and the git hash
(constraint C4) and every metric carries wall-clock and API accounting (reviewer attack 3).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import Config, write_config
from .metrics import SliceMetrics, auroc, slice_metrics, tune_threshold
from .utils import Timing, dump_json, git_hash, set_seed


@dataclass
class RunContext:
    """Everything a training run needs, resolved once from a config."""

    cfg: Config
    variant: str
    seed: int
    table: Path
    out_dir: Path
    git: str = "unknown"
    timing: Timing = field(default_factory=Timing)
    split_seed: int | None = None

    @classmethod
    def build(
        cls,
        cfg: Config,
        variant: str,
        seed: int,
        table: Path | None = None,
        split_seed: int | None = None,
    ) -> RunContext:
        from .data.build import table_path
        from .paths import PROJECT_ROOT

        base = cfg.get("report.out_dir", "results/summary")
        out_dir = PROJECT_ROOT / base / str(cfg.get("report.tag", "run")) / f"{variant}_seed{seed}"
        return cls(
            cfg=cfg,
            variant=variant,
            seed=seed,
            table=Path(table) if table else table_path(cfg, seed),
            out_dir=out_dir,
            git=git_hash(PROJECT_ROOT),
            split_seed=seed if split_seed is None else split_seed,
        )

    def ensure_table(self) -> Path:
        """Build this run's table if it is missing, so a config never runs on absent data."""
        from .data.build import ensure_table

        return ensure_table(self.cfg, self.seed)

    def start(self) -> None:
        set_seed(self.seed)

    def provenance(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "seed": self.seed,
            "split_seed": self.split_seed,
            "git": self.git,
            "config": self.cfg.source.name if self.cfg.source else "inline",
            "table": str(self.table),
        }

    def persist_config(self) -> Path:
        """Constraint C4: the run's resolved config lands next to its results."""
        path = self.out_dir / "config.yaml"
        write_config(path, self.cfg)
        return path


@dataclass
class RunResult:
    """What one (variant, seed) run produces."""

    variant: str
    seed: int
    model: Any
    fit_info: dict
    threshold: float
    test: SliceMetrics
    val_auroc: float
    y_test: np.ndarray
    p_test: np.ndarray
    test_frame: pd.DataFrame
    out_dir: Path
    timing: Timing
    gate_weights: pd.DataFrame | None = None
    skipped: str | None = None

    def to_dict(self) -> dict:
        return {
            "variant": self.variant,
            "seed": self.seed,
            "threshold": round(self.threshold, 6),
            "val_auroc": None if np.isnan(self.val_auroc) else round(self.val_auroc, 4),
            "test": self.test.as_dict(),
            "fit_info": self.fit_info,
            "timing": self.timing.as_dict(),
            "skipped": self.skipped,
        }


def load_table(path: str | Path) -> pd.DataFrame:
    """Read a parquet signal table and validate it against the data contract."""
    from .data.schema import validate

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"signal table not found: {path} (build it first)")
    df = pd.read_parquet(path)
    validate(df).raise_if_failed()
    return df


def make_split(df: pd.DataFrame, ctx: RunContext):
    """Grouped split by ``question_id``. The split seed varies, the model seed varies."""
    from .data.splits import grouped_split

    return grouped_split(df, seed=int(ctx.split_seed or ctx.seed))


def fit_variant(ctx: RunContext, df: pd.DataFrame | None = None, split=None) -> RunResult:
    """Fit one variant end to end and score it on the held-out test questions."""
    from .data.splits import assert_disjoint
    from .models import build_model
    from .variants import is_runnable

    ctx.start()
    ctx.ensure_table()
    wall_start = time.perf_counter()

    df = load_table(ctx.table) if df is None else df
    split = make_split(df, ctx) if split is None else split
    assert_disjoint(split)

    runnable, reason = is_runnable(ctx.variant, df)
    if not runnable:
        return RunResult(
            variant=ctx.variant,
            seed=ctx.seed,
            model=None,
            fit_info={},
            threshold=0.5,
            test=SliceMetrics(ctx.variant, 0, float("nan"), float("nan")),
            val_auroc=float("nan"),
            y_test=np.array([]),
            p_test=np.array([]),
            test_frame=split.test,
            out_dir=ctx.out_dir,
            timing=ctx.timing,
            skipped=reason,
        )

    model = build_model(ctx.variant, ctx.cfg, seed=ctx.seed)

    train_start = time.perf_counter()
    fit_info = model.fit(split.train, split.val, ctx.cfg) or {}
    ctx.timing.train_s = time.perf_counter() - train_start

    threshold = tune_threshold(
        split.val["label"].to_numpy(),
        model.predict_proba(split.val),
        quantile=float(ctx.cfg.get("eval.threshold_quantile", 0.5)),
    )

    predict_start = time.perf_counter()
    p_test = np.asarray(model.predict_proba(split.test), dtype="float64")
    ctx.timing.predict_s = time.perf_counter() - predict_start

    y_test = split.test["label"].to_numpy()
    ctx.timing.wall_s = time.perf_counter() - wall_start

    test_metrics = slice_metrics(
        y_test,
        p_test,
        name=f"{ctx.variant}:test",
        threshold=threshold,
        n_bins=int(ctx.cfg.get("eval.ece_bins", 15)),
        extra={"variant": ctx.variant, "seed": ctx.seed},
    )

    return RunResult(
        variant=ctx.variant,
        seed=ctx.seed,
        model=model,
        fit_info=fit_info,
        threshold=threshold,
        test=test_metrics,
        val_auroc=auroc(split.val["label"].to_numpy(), model.predict_proba(split.val)),
        y_test=y_test,
        p_test=p_test,
        test_frame=split.test,
        out_dir=ctx.out_dir,
        timing=ctx.timing,
        gate_weights=getattr(model, "gate_weight_frame", lambda: None)(),
    )


def persist(ctx: RunContext, result: RunResult) -> dict[str, Path]:
    """Write metrics JSON and a checkpoint next to the run's config."""
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    written = {"config": ctx.persist_config()}

    payload = {**ctx.provenance(), **result.to_dict()}
    metrics_path = ctx.out_dir / "metrics.json"
    dump_json(metrics_path, payload)
    written["metrics"] = metrics_path

    if result.model is not None and ctx.cfg.get("report.save_checkpoint", True):
        written["checkpoint"] = save_model(result.model, ctx.out_dir / "model.joblib")
    return written


def save_model(model, path: Path) -> Path:
    """Persist a fitted variant. Torch modules use torch.save, everything else joblib."""
    import joblib

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import torch

        if isinstance(model, torch.nn.Module):
            torch.save(model, path.with_suffix(".pt"))
            return path.with_suffix(".pt")
    except ImportError:  # pragma: no cover - torch is a hard dependency
        pass
    joblib.dump(model, path)
    return path


def train_variant(ctx: RunContext) -> str:
    """Fit and persist one (variant, seed). Returns a one-line summary for the CLI."""
    result = fit_variant(ctx)
    if result.skipped:
        return f"skipped: {result.skipped}"
    written = persist(ctx, result)
    metrics = result.test.as_dict()
    return (
        f"test_auroc={metrics['auroc']} f1={metrics['f1']} ece={metrics['ece']} "
        f"val_auroc={None if np.isnan(result.val_auroc) else round(result.val_auroc, 4)} "
        f"-> {written['metrics']}"
    )


def load_config_or_die(name_or_path: str) -> Config:
    from .config import load_config, load_named

    if name_or_path.endswith(".yaml") or "/" in name_or_path:
        return load_config(name_or_path)
    return load_named(name_or_path)

"""Build the signal table a config asks for, and keep config and data from disagreeing.

``configs/*.yaml`` declares ``data.table`` (which may contain ``{seed}``), ``n_questions``
and ``n_generators``. This module is the only place a table is created, so a config can
never claim 4 generators over a 5-generator table again.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..config import Config, load_config
from ..paths import PROJECT_ROOT


def table_path(cfg: Config, seed: int) -> Path:
    """Resolve ``data.table`` for a seed. ``{seed}`` is filled in if present."""
    raw = str(cfg.get("data.table"))
    return PROJECT_ROOT / raw.format(seed=seed)


def table_seeds(cfg: Config) -> list[int]:
    seeds = cfg.get("data.table_seeds", None)
    if not seeds:
        return [int(cfg.get("seed", 0))]
    return [int(s) for s in seeds]


def ensure_table(cfg: Config, seed: int, force: bool = False) -> Path:
    """Generate the table for one seed if it is not already on disk."""
    from .synthetic import generate, load_planted, save

    path = table_path(cfg, seed)
    if path.exists() and not force:
        return path

    benchmark = str(cfg.get("data.benchmark", "synthetic"))
    if benchmark != "synthetic":
        raise NotImplementedError(
            f"benchmark {benchmark!r} is built by its own loader, not by the synthetic generator"
        )

    df = generate(
        load_planted(cfg.get("data.planted_config", None)),
        seed=seed,
        n_questions=int(cfg.get("data.n_questions", 900)),
        n_generators=int(cfg.get("data.n_generators", 5)),
    )
    save(df, path)
    return path


def ensure_tables(cfg: Config, force: bool = False) -> list[Path]:
    return [ensure_table(cfg, seed, force=force) for seed in table_seeds(cfg)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m rcgate.data.build",
        description="Build every signal table a config declares.",
    )
    p.add_argument("--config", default="synthetic", help="config name in configs/ or a path")
    p.add_argument("--force", action="store_true", help="regenerate even if present")
    p.add_argument("--seed", type=int, default=None, help="build only this table seed")
    args = p.parse_args(argv)

    cfg = load_config(args.config) if ("/" in args.config or args.config.endswith(".yaml")) else load_config(
        PROJECT_ROOT / "configs" / f"{args.config}.yaml"
    )

    seeds = [args.seed] if args.seed is not None else table_seeds(cfg)
    for seed in seeds:
        path = ensure_table(cfg, seed, force=args.force)
        print(f"seed={seed} table={path} rows={_rows(path)}")
    return 0


def _rows(path: Path) -> str:
    import pandas as pd

    return str(len(pd.read_parquet(path, columns=["claim_id"])))


if __name__ == "__main__":
    raise SystemExit(main())

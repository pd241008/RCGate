"""Build the signal table a config asks for, and keep config and data from disagreeing.

``configs/*.yaml`` declares ``data.table`` (which may contain ``{seed}``), ``n_questions``
and ``n_generators``. This module is the only place a table is created, so a config can
never claim 4 generators over a 5-generator table again.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ..config import Config, load_config
from ..paths import PROJECT_ROOT
from ..utils import dump_json
from .synthetic import save


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
    """Generate the table for one seed if it is not already on disk.

    The benchmark named in the config decides which builder runs, so a config cannot claim
    one benchmark's numbers over another benchmark's data.
    """
    path = table_path(cfg, seed)
    if path.exists() and not force:
        return path

    benchmark = str(cfg.get("data.benchmark", "synthetic"))
    builder = BUILDERS.get(benchmark)
    if builder is None:
        raise NotImplementedError(
            f"no builder for benchmark {benchmark!r}; known: {sorted(BUILDERS)}"
        )
    df = builder(cfg, seed)
    save(df, path)
    return path


def _build_synthetic(cfg: Config, seed: int) -> pd.DataFrame:
    from .synthetic import generate, load_planted

    return generate(
        load_planted(cfg.get("data.planted_config", None)),
        seed=seed,
        n_questions=int(cfg.get("data.n_questions", 900)),
        n_generators=int(cfg.get("data.n_generators", 5)),
    )


def _build_ragtruth(cfg: Config, seed: int) -> pd.DataFrame:
    """Load RAGTruth and run the real extractors over it."""
    from ..claims.dealias import ANTECEDENT_VERSION
    from ..signals.extract import extract_signals
    from ..utils import git_hash
    from .ragtruth import ALIGNMENT_VERSION, FILES, build_slice, write_schema_record

    sl = build_slice(cfg, seed=seed)
    frame, report = extract_signals(sl.frame, cfg, sl.answers_by_question)

    explicit = cfg.get("data.schema_record", None)
    if explicit:
        schema_path = PROJECT_ROOT / str(explicit)
    else:
        schema_path = (
            PROJECT_ROOT / str(cfg.get("paths.benchmarks_dir", "data/benchmarks"))
            / f"{cfg.get('data.benchmark', 'ragtruth')}.json"
        )
    benchmark_record = write_schema_record(schema_path, sl.stats)
    build_log = {
        "benchmark": "ragtruth",
        "seed": seed,
        "pipeline_version": str(cfg.get("data.pipeline_version", "historical")),
        "alignment_version": ALIGNMENT_VERSION,
        "antecedent_version": ANTECEDENT_VERSION,
        "git": git_hash(PROJECT_ROOT),
        "config": cfg.source.name if cfg.source else "inline",
        "roster": sl.roster,
        "slice": sl.stats,
        "extraction": report.as_dict(),
        "benchmark_record": str(benchmark_record),
        "raw_files": [{"name": name, "sha256": digest} for name, digest in FILES.items()],
    }
    dump_json(PROJECT_ROOT / str(cfg.get("report.out_dir", "results/summary")) /
              str(cfg.get("report.tag", "run")) / f"build_seed{seed}.json", build_log)
    print(f"[ragtruth] {sl.stats['n_claims_written']} claims from "
          f"{sl.stats['n_sources_written']} sources, "
          f"{sl.stats['n_hallucinated']} hallucinated "
          f"({sl.stats.get('positive_rate', 0):.1%}), backend={report.backend}, "
          f"{report.cache_hits} cached / {report.cache_misses} computed NLI calls, "
          f"{report.seconds:.1f}s")
    return frame


BUILDERS = {"synthetic": _build_synthetic, "ragtruth": _build_ragtruth}


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

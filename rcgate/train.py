"""CLI: train any variant from a config.

Built on stdlib argparse because ``typer`` is not installable in this environment
(see DECISIONS.md). Flag names match the spec.

Examples
--------
    python -m rcgate.train --config configs/synthetic.yaml --variant A7
    python -m rcgate.train --config configs/synthetic.yaml --all-variants --seeds 5
    python -m rcgate.train --config configs/smoke.yaml
"""

from __future__ import annotations

import argparse
import sys

from .config import available_configs
from .pipeline import load_config_or_die
from .variants import ALL_VARIANTS, DEFAULT_VARIANTS, describe_variants


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m rcgate.train",
        description="Train an RC-Gate variant or a baseline from a YAML config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "variants:\n"
            "  A0 flat logistic on 6 signals        A1 cross-model only\n"
            "  A2 evidence only                    A3 static scalar alpha blend\n"
            "  A4 flat GBM + metadata (control)   A5 gate on claim type\n"
            "  A6 gate on generator               A7 full RC-Gate\n"
            "  A8 naive majority vote (needs judge_votes in the table)\n"
        ),
    )
    p.add_argument("--config", default="synthetic", help="config name in configs/ or a path")
    p.add_argument(
        "--variant",
        default=None,
        choices=ALL_VARIANTS,
        help="single variant to train (default: A7, the proposed method)",
    )
    p.add_argument("--all-variants", action="store_true", help="train every runnable variant")
    p.add_argument(
        "--seeds", type=int, default=None, help="number of seeds (default: eval.n_seeds)"
    )
    p.add_argument("--seed", type=int, default=None, help="a single explicit seed")
    p.add_argument("--list-variants", action="store_true", help="print variants and exit")
    p.add_argument("--list-configs", action="store_true", help="print configs and exit")
    return p


def resolve_seeds(args, cfg) -> list[int]:
    if args.seed is not None:
        return [args.seed]
    n = args.seeds if args.seeds is not None else int(cfg.get("eval.n_seeds", 5))
    return list(range(n))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_configs:
        print("\n".join(available_configs()))
        return 0
    if args.list_variants:
        print(describe_variants())
        return 0

    cfg = load_config_or_die(args.config)
    if args.all_variants:
        variants = ALL_VARIANTS
    elif args.variant:
        variants = [args.variant]
    else:
        variants = list(DEFAULT_VARIANTS)
    seeds = resolve_seeds(args, cfg)

    from .pipeline import RunContext, train_variant

    failures: list[str] = []
    for variant in variants:
        for seed in seeds:
            ctx = RunContext.build(cfg, variant=variant, seed=seed)
            try:
                result = train_variant(ctx)
            except NotImplementedError as exc:
                print(f"[skip] {variant} seed={seed}: {exc}")
                failures.append(f"{variant}: {exc}")
                continue
            print(f"[done] {variant} seed={seed} -> {result}")
    return 1 if failures and len(failures) == len(variants) * len(seeds) else 0


if __name__ == "__main__":
    sys.exit(main())

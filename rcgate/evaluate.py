"""Evaluation harness (milestone M4).

One command produces: per-benchmark and per-claim-type AUROC / F1 / precision / recall /
ECE, bootstrap 95% CIs, mean +/- std across seeds, a leave-one-generator-out run through
the ``UNK`` path, and the gate-weight heatmap.

Example
-------
    python -m rcgate.evaluate --config synthetic --bootstrap 1000 \\
        --out results/summary/synthetic.md
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config
from .data.build import table_path
from .data.schema import CLAIM_TYPE_NAMES, UNK_GENERATOR
from .data.splits import leave_one_generator_out
from .metrics import (
    auroc,
    bootstrap_auroc_ci,
    paired_bootstrap_delta,
    slice_metrics,
)
from .pipeline import RunContext, fit_variant, load_table, persist
from .utils import git_hash
from .variants import ALL_VARIANTS, VARIANTS

#: Slices that get a bootstrap CI. Cell-level (type x generator) tables are point
#: estimates only, because there are 20 of them and each CI costs 1000 resamples.
CI_SLICES = ("all", "benchmark", "claim_type", "generator_id")


# ---------------------------------------------------------------------------
# slice construction
# ---------------------------------------------------------------------------


def slice_masks(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Every slice the report shows, as boolean masks over the test rows."""
    masks: dict[str, np.ndarray] = {"all": np.ones(len(df), dtype=bool)}
    if "benchmark" in df.columns:
        for value in sorted(df["benchmark"].astype(str).unique()):
            masks[f"benchmark={value}"] = df["benchmark"].astype(str).to_numpy() == value
    for value in sorted(df["claim_type"].unique()):
        masks[f"claim_type={value}"] = df["claim_type"].to_numpy() == value
    for value in sorted(df["generator_id"].unique()):
        masks[f"generator_id={value}"] = df["generator_id"].to_numpy() == value
    for t in sorted(df["claim_type"].unique()):
        for g in sorted(df["generator_id"].unique()):
            m = (df["claim_type"].to_numpy() == t) & (df["generator_id"].to_numpy() == g)
            masks[f"cell={CLAIM_TYPE_NAMES[int(t)]}|{int(g)}"] = m
    return masks


# ---------------------------------------------------------------------------
# per-run scoring
# ---------------------------------------------------------------------------


@dataclass
class SeedRun:
    variant: str
    seed: int
    rows: list[dict] = field(default_factory=list)
    y: dict[str, np.ndarray] = field(default_factory=dict)
    p: dict[str, np.ndarray] = field(default_factory=dict)
    threshold: float = 0.5
    val_auroc: float = float("nan")
    timing: dict = field(default_factory=dict)
    gate_weights: pd.DataFrame | None = None
    skipped: str | None = None


def score_run(result, cfg: Config, seed: int, n_bootstrap: int, n_bins: int) -> SeedRun:
    """Score every slice of one test split, with CIs where they are affordable."""
    run = SeedRun(variant=result.variant, seed=seed, threshold=result.threshold)
    run.val_auroc = result.val_auroc
    run.timing = result.timing.as_dict()
    run.skipped = result.skipped
    run.gate_weights = result.gate_weights

    if result.skipped:
        return run

    df = result.test_frame
    y, p = result.y_test, result.p_test
    masks = slice_masks(df)
    n_bins = int(cfg.get("eval.ece_bins", n_bins))

    for name, mask in masks.items():
        if mask.sum() < 2:
            continue
        ys, ps = y[mask], p[mask]
        ci = None
        if name in CI_SLICES or name.startswith("benchmark"):
            ci = bootstrap_auroc_ci(ys, ps, n_resamples=n_bootstrap, seed=seed)
        m = slice_metrics(
            ys, ps, name=name, threshold=result.threshold, n_bins=n_bins, ci=ci,
            extra={"variant": result.variant, "seed": seed, "n_questions": int(df.loc[mask, "question_id"].nunique())},
        )
        run.rows.append(m.as_dict())
        run.y[name] = ys
        run.p[name] = ps
    return run


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def aggregate(runs: dict[str, list[SeedRun]], cfg: Config, n_bootstrap: int) -> pd.DataFrame:
    """Mean and sample sd across seeds, one row per (variant, slice).

    Interval endpoints are averaged with the other columns. That average is not a
    confidence interval. Stage 5 inference does not use it; see ``stats_protocol``.
    """
    frames = [pd.DataFrame(r.rows) for seed_runs in runs.values() for r in seed_runs if r.rows]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    numeric = ["auroc", "f1", "precision", "recall", "ece", "auroc_ci_lo", "auroc_ci_hi", "mean_prob"]
    present = [c for c in numeric if c in df.columns]
    grouped = df.groupby(["variant", "slice"], dropna=False)
    agg = grouped[present].mean().add_suffix("_mean")
    std = grouped[present].std(ddof=1).add_suffix("_std")
    agg = agg.join(std)
    agg = agg.join(grouped["n"].mean().rename("n"))
    return agg.reset_index()


# ---------------------------------------------------------------------------
# leave-one-generator-out through the UNK path
# ---------------------------------------------------------------------------


def logo_runs(cfg: Config, variants: list[str], df: pd.DataFrame, n_generators: int) -> pd.DataFrame:
    """Hold out each generator, relabel it UNK in test, and score only the UNK rows."""
    rows = []
    for g in range(n_generators):
        if g not in set(df["generator_id"].unique()):
            continue
        split = leave_one_generator_out(df, generator_id=g, seed=0)
        for variant in variants:
            ctx = RunContext.build(cfg, variant=variant, seed=0)
            started = time.perf_counter()
            result = fit_variant(ctx, df=df, split=split)
            unk = split.test["generator_id"].to_numpy() == UNK_GENERATOR
            if unk.sum() < 2 or result.skipped:
                rows.append({"held_out_generator": g, "variant": variant, "n_unk": int(unk.sum())})
                continue
            y, p = result.y_test[unk], result.p_test[unk]
            ci = bootstrap_auroc_ci(y, p, n_resamples=200, seed=g)
            rows.append(
                {
                    "held_out_generator": g,
                    "variant": variant,
                    "n_unk": int(unk.sum()),
                    "unk_auroc": round(auroc(y, p), 4),
                    "unk_ci_lo": round(ci.lo, 4) if np.isfinite(ci.lo) else None,
                    "unk_ci_hi": round(ci.hi, 4) if np.isfinite(ci.hi) else None,
                    "seen_auroc": round(auroc(result.y_test[~unk], result.p_test[~unk]), 4),
                    "train_contains_generator": bool((split.train["generator_id"] == g).any()),
                    "seconds": round(time.perf_counter() - started, 1),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# report rendering
# ---------------------------------------------------------------------------


def _fmt(v, digits: int = 3) -> str:
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "-"
    return f"{v:.{digits}f}"


def _pm(mean, std) -> str:
    if mean is None or (isinstance(mean, float) and np.isnan(mean)):
        return "-"
    return f"{mean:.3f}" + (f" ± {std:.3f}" if std is not None and not np.isnan(std) else "")


def markdown_report(
    cfg: Config,
    agg: pd.DataFrame,
    runs: dict[str, list[SeedRun]],
    logo: pd.DataFrame | None,
    deltas: pd.DataFrame | None,
    gate_summary: pd.DataFrame | None,
    table_path: Path,
    n_bootstrap: int,
    seconds: float,
) -> str:
    benchmark = str(cfg.get("data.benchmark", "?"))
    synthetic = benchmark == "synthetic"
    stamp = time.strftime("%Y-%m-%d %H:%M")
    n_seeds = max((len(v) for v in runs.values()), default=0)

    lines: list[str] = []
    lines.append(f"# RC-Gate results -- {benchmark}")
    lines.append("")
    if synthetic:
        lines.append(
            "> **SYNTHETIC DATA.** These numbers validate the machinery on data with known "
            "planted signal reliability. They are not evidence for or against H1-H3, which "
            "are claims about real model outputs. Every table and plot from this run must be "
            "labelled synthetic (constraint C8)."
        )
        lines.append("")
    lines.append(f"- generated: {stamp}")
    lines.append(f"- git: `{git_hash()}`")
    lines.append(f"- config: `{cfg.source.name if cfg.source else 'inline'}`")
    lines.append(f"- signal table: `{table_path}`")
    lines.append(f"- seeds: {n_seeds}; bootstrap resamples: {n_bootstrap} per slice per seed")
    lines.append(f"- total wall clock: {seconds:.0f}s")
    lines.append("")

    def table_for(slice_prefix: str, title: str, note: str = "") -> list[str]:
        sub = agg[agg["slice"].str.startswith(slice_prefix)] if len(agg) else agg
        if sub.empty:
            return []
        out = [f"## {title}", ""]
        if note:
            out += [note, ""]
        out.append("| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |")
        out.append("|---|---|---:|---|---|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            ci = ""
            if pd.notna(r.get("auroc_ci_lo")) and pd.notna(r.get("auroc_ci_hi")):
                ci = f" [{r['auroc_ci_lo']:.3f}, {r['auroc_ci_hi']:.3f}]"
            out.append(
                f"| {r['variant']} | `{r['slice']}` | {int(r['n'])} | {_fmt(r.get('auroc_mean'))}{ci} | "
                f"{_pm(r.get('auroc_mean'), r.get('auroc_std'))} | {_fmt(r.get('f1_mean'))} | "
                f"{_fmt(r.get('precision_mean'))} | {_fmt(r.get('recall_mean'))} | {_fmt(r.get('ece_mean'))} |"
            )
        out.append("")
        return out

    lines += table_for("all", "Overall")
    lines += table_for("benchmark=", "Per benchmark")
    lines += table_for("claim_type=", "Per claim type",
                       "Claim types: 0 numeric, 1 entity, 2 extractive, 3 abstractive. "
                       "The proposal's \"numeric/extractive\" reporting group is types 0 and 2.")

    gen = agg[agg["slice"].str.startswith("generator_id=")] if len(agg) else pd.DataFrame()
    if not gen.empty:
        lines += ["## Per generator", "",
                  "`UNK` (-1) only appears in the leave-one-generator-out table below.", "",
                  "| variant | generator | n | AUROC (95% CI) | AUROC mean ± sd | F1 | ECE |",
                  "|---|---|---:|---|---|---:|---:|"]
        for _, r in gen.iterrows():
            ci = ""
            if pd.notna(r.get("auroc_ci_lo")) and pd.notna(r.get("auroc_ci_hi")):
                ci = f" [{r['auroc_ci_lo']:.3f}, {r['auroc_ci_hi']:.3f}]"
            lines.append(
                f"| {r['variant']} | {r['slice'].split('=')[1]} | {int(r['n'])} | "
                f"{_fmt(r.get('auroc_mean'))}{ci} | {_pm(r.get('auroc_mean'), r.get('auroc_std'))} | "
                f"{_fmt(r.get('f1_mean'))} | {_fmt(r.get('ece_mean'))} |"
            )
        lines.append("")

    cells = agg[agg["slice"].str.startswith("cell=")] if len(agg) else pd.DataFrame()
    if not cells.empty:
        lines += ["## Per (claim type, generator) cell", "",
                  "Point estimates only; bootstrap CIs are not computed for 20 cells x "
                  f"{n_seeds} seeds.", "",
                  "| variant | cell | n | AUROC mean ± sd |", "|---|---|---:|---|"]
        for _, r in cells.iterrows():
            lines.append(
                f"| {r['variant']} | `{r['slice'][5:]}` | {int(r['n'])} | "
                f"{_pm(r.get('auroc_mean'), r.get('auroc_std'))} |"
            )
        lines.append("")

    if deltas is not None and not deltas.empty:
        lines += ["## H2 test: A7 minus baseline, paired bootstrap", "",
                  "Both models are scored on the *same* test rows, so this is a paired "
                  "comparison and much tighter than differencing two separate CIs. "
                  "`p_gt_0` is the bootstrap fraction of resamples favouring A7.", "",
                  "| slice | comparison | ΔAUROC | 95% CI | p_gt_0 |", "|---|---|---:|---|---:|"]
        for _, r in deltas.iterrows():
            lines.append(
                f"| `{r['slice']}` | {r['variant']} - {r['baseline']} | {_fmt(r['delta'])} | "
                f"[{_fmt(r.get('lo'))}, {_fmt(r.get('hi'))}] | {_fmt(r.get('p_gt_0'))} |"
            )
        lines.append("")

    if gate_summary is not None and not gate_summary.empty:
        lines += ["## Gate weights (A7)", "",
                  "Mean softmax weights over the test split, by claim type and by generator. "
                  "Both columns should sum to 1 per cell.", "",
                  "| claim type | " + " | ".join(f"w_cross g{g}" for g in sorted(gate_summary.columns))
                  + " |", "|---|" + "---|" * len(gate_summary.columns)]
        for tname, row in gate_summary.iterrows():
            lines.append(f"| {tname} | " + " | ".join(f"{v:.3f}" for v in row.to_numpy()) + " |")
        lines.append("")

    if logo is not None and not logo.empty:
        lines += ["## Leave-one-generator-out (UNK cold start)", "",
                  "Each generator is removed from train and val, relabelled `UNK` in test, and "
                  "scored on the UNK rows only. `seen_auroc` is the rest of the test set.", "",
                  "| held out | variant | n UNK | UNK AUROC | 95% CI | seen AUROC | in train? |",
                  "|---|---|---:|---:|---|---:|---|"]
        for _, r in logo.iterrows():
            ci = ""
            if r.get("unk_ci_lo") is not None and pd.notna(r.get("unk_ci_lo")):
                ci = f" [{r['unk_ci_lo']:.3f}, {r['unk_ci_hi']:.3f}]"
            lines.append(
                f"| {r['held_out_generator']} | {r['variant']} | {int(r['n_unk'])} | "
                f"{_fmt(r.get('unk_auroc'))}{ci} | {_fmt(r.get('seen_auroc'))} | "
                f"{r.get('train_contains_generator', False)} |"
            )
        lines.append("")

    lines += ["## Cost and latency", "",
              "Wall clock per run, and API accounting. API calls are zero for every table that "
              "was already built; they are non-zero only for tables whose signals came from a "
              "live extractor.", "",
              "| variant | mean train s | mean predict s | API calls | API USD |",
              "|---|---:|---:|---:|---:|"]
    for variant, rs in runs.items():
        if not rs or rs[0].timing is None:
            continue
        tr = np.mean([r.timing.get("train_s", 0.0) for r in rs])
        pr = np.mean([r.timing.get("predict_s", 0.0) for r in rs])
        calls = sum(r.timing.get("api_calls", 0) for r in rs)
        usd = sum(r.timing.get("api_usd", 0.0) for r in rs)
        lines.append(f"| {variant} | {tr:.2f} | {pr:.3f} | {calls} | {usd:.4f} |")
    lines.append("")

    lines += ["## Variant glossary", "", "| id | name | purpose |", "|---|---|---|"]
    for vid in ALL_VARIANTS:
        v = VARIANTS[vid]
        lines.append(f"| {vid} | {v.name} | {v.purpose} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def run(
    cfg: Config,
    variants: list[str],
    seeds: list[int],
    n_bootstrap: int,
    out_path: Path,
    with_logo: bool = True,
    logo_variants: tuple[str, ...] = ("A0", "A7"),
) -> Path:
    started = time.perf_counter()
    tables = {seed: load_table(table_path(cfg, seed)) for seed in seeds}

    runs: dict[str, list[SeedRun]] = {}
    for variant in variants:
        rs: list[SeedRun] = []
        for seed in seeds:
            ctx = RunContext.build(cfg, variant=variant, seed=seed)
            result = fit_variant(ctx, df=tables[seed])
            persist(ctx, result)
            rs.append(score_run(result, cfg, seed, n_bootstrap, int(cfg.get("eval.ece_bins", 15))))
            print(f"  scored {variant} seed={seed}", flush=True)
        runs[variant] = rs

    agg = aggregate(runs, cfg, n_bootstrap)

    deltas = _deltas(runs, "A7", ("A0", "A4", "A3", "A1", "A2"), n_bootstrap)

    gate_summary = None
    if "A7" in runs:
        gate_summary = _gate_heatmap(runs["A7"])

    logo = None
    if with_logo:
        df0 = tables[seeds[0]]
        n_gen = int(cfg.get("model.n_generators", df0["generator_id"].nunique()))
        print(f"  leave-one-generator-out over {n_gen} generators", flush=True)
        logo = logo_runs(cfg, list(logo_variants), df0, n_gen)

    seconds = time.perf_counter() - started
    source_table = table_path(cfg, seeds[0])
    report = markdown_report(
        cfg, agg, runs, logo, deltas, gate_summary, source_table, n_bootstrap, seconds
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)

    json_path = out_path.with_suffix(".json")
    import json

    json_path.write_text(
        json.dumps(
            {
                "config": cfg.to_dict(),
                "git": git_hash(),
                "aggregated": agg.to_dict(orient="records"),
                "deltas": None if deltas is None else deltas.to_dict(orient="records"),
                "logo": None if logo is None else logo.to_dict(orient="records"),
                "gate_weights": None if gate_summary is None else gate_summary.to_dict(),
            },
            indent=2,
            default=str,
        )
    )

    if gate_summary is not None:
        _write_heatmap(gate_summary, out_path.with_suffix(".gate_weights.png"))

    print(f"\nwrote {out_path}\nwrote {json_path}")
    return out_path


def _deltas(runs, target: str, baselines: tuple[str, ...], n_bootstrap: int) -> pd.DataFrame:
    """Paired A7-minus-baseline AUROC deltas, per slice, on shared test rows."""
    if target not in runs:
        return pd.DataFrame()
    rows = []
    slices = set(runs[target][0].y.keys()) if runs[target] else set()
    for baseline in baselines:
        if baseline not in runs or len(runs[baseline]) != len(runs[target]):
            continue
        for a, b in zip(runs[target], runs[baseline], strict=True):
            for slice_name in sorted(slices):
                if slice_name not in a.y or slice_name not in b.y or len(a.y[slice_name]) != len(b.y[slice_name]):
                    continue
                if slice_name.startswith("cell="):
                    continue
                # Stage 4 cap. Reproduced on purpose so the published paired intervals
                # stay traceable. Corrected intervals live in rcgate.stats_protocol
                # and use the requested resample count without this cap.
                d = paired_bootstrap_delta(
                    a.y[slice_name],
                    a.p[slice_name],
                    b.p[slice_name],
                    n_resamples=min(n_bootstrap, 500),
                    seed=a.seed,
                )
                rows.append({"variant": target, "baseline": baseline, "slice": slice_name, "seed": a.seed, **d})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    num = [c for c in ("delta", "lo", "hi", "p_gt_0") if c in frame.columns]
    return frame.groupby(["variant", "baseline", "slice"])[num].mean().reset_index()


def _gate_heatmap(runs_a7: list[SeedRun]) -> pd.DataFrame | None:
    """Mean w_cross per (claim type, generator), stacked across seeds."""
    frames = [r.gate_weights for r in runs_a7 if r.gate_weights is not None]
    if not frames:
        return None
    g = pd.concat(frames, ignore_index=True)
    piv = g.pivot_table(index="claim_type", columns="generator_id", values="w_cross", aggfunc="mean")
    piv.index = [CLAIM_TYPE_NAMES[int(t)] for t in piv.index]
    return piv.sort_index()


def _write_heatmap(summary: pd.DataFrame, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(1.6 * len(summary.columns) + 3, 0.9 * len(summary) + 2))
    im = ax.imshow(summary.to_numpy(dtype=float), cmap="RdBu_r", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(summary.columns)), [f"g{c}" for c in summary.columns])
    ax.set_yticks(range(len(summary.index)), list(summary.index))
    for i in range(summary.shape[0]):
        for j in range(summary.shape[1]):
            value = summary.to_numpy(dtype=float)[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                    color="white" if abs(value - 0.5) > 0.28 else "black")
    ax.set_xlabel("generator_id")
    ax.set_ylabel("claim type")
    ax.set_title("A7 gate weight w_cross  (blue = trusts cross-model, red = trusts evidence)")
    fig.colorbar(im, ax=ax, label="w_cross")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m rcgate.evaluate",
        description="Full evaluation: per-slice metrics, bootstrap CIs, LOGO, gate heatmap.",
    )
    p.add_argument("--config", default="synthetic")
    p.add_argument("--variants", nargs="+", default=None, help="default: every runnable variant")
    p.add_argument("--seeds", type=int, default=None, help="default: eval.n_seeds")
    p.add_argument("--bootstrap", type=int, default=None, help="default: eval.n_bootstrap")
    p.add_argument("--out", default=None, help="markdown path (default: results/summary/<tag>.md)")
    p.add_argument("--no-logo", action="store_true", help="skip leave-one-generator-out")
    p.add_argument("--logo-variants", nargs="+", default=["A0", "A7"])
    return p


def main(argv: list[str] | None = None) -> int:
    from .paths import PROJECT_ROOT, SUMMARY_DIR
    from .pipeline import load_config_or_die

    args = build_parser().parse_args(argv)
    cfg = load_config_or_die(args.config)
    seeds = list(range(args.seeds if args.seeds is not None else int(cfg.get("eval.n_seeds", 5))))
    n_bootstrap = args.bootstrap if args.bootstrap is not None else int(cfg.get("eval.n_bootstrap", 1000))
    variants = args.variants or list(ALL_VARIANTS)

    out = Path(args.out) if args.out else PROJECT_ROOT / str(cfg.get("report.out_dir", "results/summary")) / f"{cfg.get('report.tag', 'run')}.md"
    if not out.is_absolute():
        out = PROJECT_ROOT / out

    run(cfg, variants, seeds, n_bootstrap, out, with_logo=not args.no_logo,
        logo_variants=tuple(args.logo_variants))
    _ = SUMMARY_DIR
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

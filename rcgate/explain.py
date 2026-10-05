"""Gate-weight explanations (milestone M4, and the H3 evidence).

Constraint C5: the weights are not decoration on top of a probability, they are the
explanation. This module turns them into the two artefacts a reviewer asks for:

1. a (claim type x generator) heatmap, and
2. a one-line explanation per claim, e.g.
   "numeric claim; cross-model agreement down-weighted (w_evid 0.81)"

It works from a fitted checkpoint when one exists, and otherwise fits on a config, so the
demo and the report cannot drift apart.

Examples
--------
    python -m rcgate.explain --config synthetic --variant A7
    python -m rcgate.explain --config synthetic --variant A7 \\
        --checkpoint results/summary/synthetic/A7_seed0/model.pt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .config import Config
from .data.build import table_path
from .data.schema import CLAIM_TYPE_NAMES, UNK_GENERATOR
from .data.splits import grouped_split
from .models.rcgate import RCGateModel, build_gate_variant
from .pipeline import load_config_or_die, load_table
from .utils import git_hash

GENERATOR_LABELS = {UNK_GENERATOR: "UNK (unseen generator)"}


def load_or_fit(cfg: Config, variant: str, seed: int, checkpoint: Path | None) -> RCGateModel:
    """Prefer a serialized checkpoint; fall back to fitting so this always works."""
    model = build_gate_variant(variant, cfg, seed=seed)
    if checkpoint is not None and Path(checkpoint).exists():
        import torch

        state = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if isinstance(state, RCGateModel):
            return state
        if isinstance(state, torch.nn.Module):
            model.model.load_state_dict(state.state_dict())
            return model
        raise ValueError(f"{checkpoint} is not an RC-Gate checkpoint")
    df = load_table(table_path(cfg, seed))
    split = grouped_split(df, seed=seed)
    model.fit(split.train, split.val, cfg)
    return model


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------


def weight_table(weights: pd.DataFrame, value: str = "w_cross") -> pd.DataFrame:
    """Mean weight per (claim type, generator), with the claim type as a row label."""
    piv = weights.pivot_table(index="claim_type", columns="generator_id", values=value, aggfunc="mean")
    piv.index = [CLAIM_TYPE_NAMES[int(t)] for t in piv.index]
    piv.columns = [GENERATOR_LABELS.get(int(c), f"g{c}") for c in piv.columns]
    return piv.sort_index()


def generator_table(weights: pd.DataFrame, value: str = "w_cross") -> pd.DataFrame:
    """Mean weight per generator, plus the claim-type spread it induces."""
    out = weights.groupby("generator_id")[value].agg(["mean", "std", "min", "max"])
    out.index = [GENERATOR_LABELS.get(int(i), f"g{i}") for i in out.index]
    out.columns = [f"{value}_{c}" for c in out.columns]
    return out


def collapse_report(weights: pd.DataFrame, value: str = "w_cross") -> dict:
    """Detect gate collapse (spec section 11: a collapse is a finding, not a bug).

    A gate has collapsed when every (claim type, generator) cell receives the same weight.
    ``spread`` is the standard deviation of the cell means; near zero means no conditioning.
    """
    cell_means = weights.groupby(["claim_type", "generator_id"])[value].mean()
    spread = float(cell_means.std())
    collapsed = spread < 0.02
    return {
        "spread_of_cell_means": round(spread, 4),
        "range": [round(float(cell_means.min()), 4), round(float(cell_means.max()), 4)],
        "collapsed": collapsed,
        "verdict": (
            "gate collapsed: metadata carries no signal in this dataset"
            if collapsed
            else "gate is conditioning on metadata"
        ),
        "n_cells": int(cell_means.size),
    }


def explain_claims(model: RCGateModel, df: pd.DataFrame, top_k: int = 12) -> pd.DataFrame:
    """Per-claim verdicts with the gate weights and a one-line reason."""
    preds = model.predict(df)
    rows = []
    for i, p in enumerate(preds):
        claim_type = int(df["claim_type"].iloc[i])
        gen = int(df["generator_id"].iloc[i])
        rows.append(
            {
                "claim_id": df["claim_id"].iloc[i],
                "claim_text": str(df["claim_text"].iloc[i])[:120],
                "claim_type": CLAIM_TYPE_NAMES[claim_type],
                "generator": GENERATOR_LABELS.get(gen, f"g{gen}"),
                "prob": round(p.prob, 4),
                "w_cross": round(p.w_cross, 4),
                "w_evid": round(p.w_evid, 4),
                "z_cross": round(p.z_cross, 4),
                "z_evid": round(p.z_evid, 4),
                "explanation": one_line(p.prob, p.w_cross, CLAIM_TYPE_NAMES[claim_type], p.z_cross, p.z_evid),
            }
        )
    out = pd.DataFrame(rows).sort_values("prob", ascending=False)
    return out.head(top_k).reset_index(drop=True)


def one_line(prob: float, w_evid: float, claim_type_name: str, z_cross: float, z_evid: float) -> str:
    """The sentence the demo shows under each claim.

    Kept deliberately dull: the reviewer should be able to check it against the numbers in
    the same row.
    """
    trusted = "evidence" if w_evid >= 0.5 else "cross-model"
    other = "cross-model" if trusted == "evidence" else "evidence"
    down = "down-weighted" if (w_evid >= 0.5) == (abs(z_evid) < abs(z_cross)) else "up-weighted"
    verdict = "likely hallucinated" if prob >= 0.5 else "likely supported"
    return (
        f"{claim_type_name} claim; {verdict} ({prob:.2f}); {other} {down} "
        f"(w_evid {w_evid:.2f})"
    )


# ---------------------------------------------------------------------------
# plots
# ---------------------------------------------------------------------------


def plot_heatmap(pivots: dict[str, pd.DataFrame], path: Path, title_suffix: str = "") -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(pivots)
    fig, axes = plt.subplots(1, n, figsize=(1.7 * max(len(p.columns) for p in pivots.values()) + 2.5,
                                                0.8 * max(len(p.index) for p in pivots.values()) + 2.5),
                             squeeze=False)
    for ax, (name, piv) in zip(axes[0], pivots.items(), strict=False):
        data = piv.to_numpy(dtype=float)
        im = ax.imshow(data, cmap="RdBu_r", vmin=0.0, vmax=1.0, aspect="auto")
        ax.set_xticks(range(data.shape[1]), list(piv.columns), rotation=45, ha="right")
        ax.set_yticks(range(data.shape[0]), list(piv.index))
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                v = data[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white" if abs(v - 0.5) > 0.28 else "black")
        ax.set_title(f"w_cross -- {name}{title_suffix}", fontsize=10)
        ax.set_xlabel("generator")
        fig.colorbar(im, ax=ax, fraction=0.046, label="w_cross")
    fig.suptitle(
        "RC-Gate weights: blue = trusts cross-model signals, red = trusts evidence\n"
        "(columns sum to 1 per cell; see results markdown for the numbers)",
        fontsize=10,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_generator_shift(weights: pd.DataFrame, path: Path) -> Path:
    """Bar chart of w_cross per generator, one bar per claim type."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    piv = weights.pivot_table(index="generator_id", columns="claim_type", values="w_cross", aggfunc="mean")
    piv.columns = [CLAIM_TYPE_NAMES[int(c)] for c in piv.columns]
    ax = piv.plot(kind="bar", figsize=(8, 4), width=0.8)
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1, label="equal trust")
    ax.set_ylabel("w_cross")
    ax.set_xlabel("generator_id")
    ax.set_ylim(0, 1)
    ax.set_title("Gate weight by generator and claim type (H3: is conditioning visible?)")
    ax.legend(fontsize=8, ncol=3)
    fig = ax.figure
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def build_report(
    cfg: Config,
    variant: str = "A7",
    seed: int = 0,
    checkpoint: Path | None = None,
    out_dir: Path | None = None,
) -> dict:
    from .paths import PROJECT_ROOT

    out_dir = out_dir or PROJECT_ROOT / str(cfg.get("report.out_dir", "results/summary"))
    out_dir.mkdir(parents=True, exist_ok=True)

    model = load_or_fit(cfg, variant, seed, checkpoint)
    df = load_table(table_path(cfg, seed))
    split = grouped_split(df, seed=seed)
    model.predict_proba(split.test)  # populates the cached frame

    weights = model.gate_weight_frame()
    if weights is None:
        raise RuntimeError("no gate weights available")

    w_cross = weight_table(weights, "w_cross")
    w_evid = weight_table(weights, "w_evid")
    gen = generator_table(weights, "w_cross")
    collapse = collapse_report(weights, "w_cross")
    claims = explain_claims(model, split.test)

    stem = out_dir / f"{cfg.get('report.tag', 'run')}_{variant}_explain"
    plot_heatmap({"w_cross": w_cross, "w_evid": w_evid}, stem.with_suffix(".heatmap.png"))
    plot_generator_shift(weights, stem.with_suffix(".by_generator.png"))

    payload = {
        "variant": variant,
        "seed": seed,
        "git": git_hash(),
        "w_cross_by_type_generator": w_cross.round(4).to_dict(),
        "w_evid_by_type_generator": w_evid.round(4).to_dict(),
        "w_cross_by_generator": gen.round(4).reset_index().to_dict(orient="records"),
        "collapse_report": collapse,
        "n_parameters": model.model.n_parameters,
        "gate_input_dim": model.model.encoder.output_dim,
        "top_claims": claims.to_dict(orient="records"),
    }
    stem.with_suffix(".json").write_text(json.dumps(payload, indent=2, default=str))
    stem.with_suffix(".md").write_text(_markdown(payload))
    return payload


def _markdown(p: dict) -> str:
    lines = [f"# Gate weights -- {p['variant']} (seed {p['seed']})", ""]
    if str(p.get("git")) == "unknown":
        lines.append("")
    lines += [
        f"- git: `{p['git']}`",
        f"- trainable parameters: {p['n_parameters']}",
        f"- gate input dimension: {p['gate_input_dim']} "
        f"(claim-type embedding ‖ generator embedding)",
        "",
        "## Collapse check (spec section 11)",
        "",
        f"- spread of cell means: **{p['collapse_report']['spread_of_cell_means']}**",
        f"- range: {p['collapse_report']['range']}",
        f"- verdict: {p['collapse_report']['verdict']}",
        "",
        "## w_cross by claim type and generator",
        "",
        "Blue in the heatmap is cross-model; the two tables below are the same numbers.",
        "",
    ]
    lines += _md_table(p["w_cross_by_type_generator"], "claim type \\ generator", "w_cross")
    lines.append("")
    lines += _md_table(p["w_evid_by_type_generator"], "claim type \\ generator", "w_evid")
    lines += ["", "## w_cross by generator", "",
              "| generator | mean | std | min | max |", "|---|---:|---:|---:|---:|"]
    for row in p["w_cross_by_generator"]:
        gen = row.get("generator_id", row.get("index", "?"))
        lines.append(
            f"| {gen} | {row['w_cross_mean']:.3f} | {row['w_cross_std']:.3f} | "
            f"{row['w_cross_min']:.3f} | {row['w_cross_max']:.3f} |"
        )
    lines += ["", "## Most-flagged claims", "",
              "| claim | type | prob | w_evid | z_cross | z_evid | explanation |",
              "|---|---|---:|---:|---:|---:|---|"]
    for c in p["top_claims"]:
        lines.append(
            f"| {c['claim_text'][:70]} | {c['claim_type']} | {c['prob']:.3f} | "
            f"{c['w_evid']:.3f} | {c['z_cross']:+.2f} | {c['z_evid']:+.2f} | {c['explanation']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _md_table(data: dict, index_name: str, value_name: str) -> list[str]:
    frame = pd.DataFrame(data)
    frame.index.name = index_name
    frame = frame.reset_index()
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in frame.iterrows():
        lines.append("| " + " | ".join(
            str(r[c]) if c == index_name else f"{float(r[c]):.3f}" for c in cols
        ) + " |")
    return lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m rcgate.explain",
        description="Gate-weight tables, heatmaps, and per-claim explanations.",
    )
    p.add_argument("--config", default="synthetic")
    p.add_argument("--variant", default="A7")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--checkpoint", default=None, help="path to a fitted A7/A5/A6 checkpoint")
    p.add_argument("--out-dir", default=None)
    args = p.parse_args(argv)

    cfg = load_config_or_die(args.config)
    payload = build_report(
        cfg,
        variant=args.variant,
        seed=args.seed,
        checkpoint=Path(args.checkpoint) if args.checkpoint else None,
        out_dir=Path(args.out_dir) if args.out_dir else None,
    )
    print(json.dumps({k: v for k, v in payload.items() if k != "top_claims"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

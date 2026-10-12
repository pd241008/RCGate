"""Stage 6: sensitivity of the corrected RAGTruth run to split construction.

The frozen signal tables, labels, signals, variants, hyperparameters, and the
Stage 5 uncertainty procedure stay as they are. The one change is the splitter:
``grouped_split(..., stratify=True)`` is the historical sort-then-permute, and
``group_stratified_split`` assigns whole ``question_id`` groups inside
positive-count strata.

Balance is judged before any model number is interpreted. A drop in mean
absolute positive-rate deviation of at least 0.01 is reported as a real
reduction. A smaller drop is not called material. Nothing in this module
retunes a threshold or a model after seeing A7.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_named
from .data.ragtruth import schema_record
from .data.splits import (
    SPLIT_GROUP_STRATIFIED,
    assert_disjoint,
    group_stratified_split,
    grouped_split,
    split_balance,
)
from .metrics import slice_metrics
from .paths import PROJECT_ROOT, SUMMARY_DIR
from .pipeline import RunContext, fit_variant, load_table, persist
from .stats_protocol import (
    N_RESAMPLES,
    PAIRED_BASELINES,
    SEEDS,
    VARIANTS,
    across_seed_dispersion,
    classify_interval,
    format_interval,
    format_point,
    paired_question_delta,
    within_seed_auroc_interval,
)
from .utils import git_hash
from .variants import ALL_VARIANTS

STAGE5_DIR = SUMMARY_DIR / "ragtruth_corrected_stats_v1"
STAGE6_DIR = SUMMARY_DIR / "ragtruth_split_corrected_v1"
CONFIG_NAME = "ragtruth_split_corrected_v1"
TABLES = [
    PROJECT_ROOT / f"data/signal_tables/ragtruth_corrected_integrity_v1_s{seed}.parquet"
    for seed in SEEDS
]
# A reduction smaller than one percentage point is not described as material.
MATERIAL_MAD_DROP = 0.01
PROTECTED = [
    PROJECT_ROOT / "results/summary/ragtruth_corrected_integrity_v1/report.json",
    PROJECT_ROOT / "results/summary/ragtruth_corrected_integrity_v1/report.md",
    PROJECT_ROOT / "results/summary/ragtruth_corrected_integrity_v1/VERDICT.md",
    PROJECT_ROOT / "results/summary/ragtruth_corrected_stats_v1/report.json",
    PROJECT_ROOT / "results/summary/ragtruth_corrected_stats_v1/report.md",
    PROJECT_ROOT / "results/summary/ragtruth_corrected_stats_v1/provenance.json",
    PROJECT_ROOT / "results/summary/ragtruth/build_seed0.json",
    PROJECT_ROOT / "results/summary/ragtruth_historical_freeze/MANIFEST.json",
]
PARTITIONS = ("train", "val", "test")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(paths: list[Path]) -> dict[str, tuple[int, int]]:
    out = {}
    for path in paths:
        stat = path.stat()
        out[str(path)] = (stat.st_mtime_ns, stat.st_size)
    return out


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (np.floating, np.integer)):
        native = value.item()
        if isinstance(native, float) and not np.isfinite(native):
            return None
        return native
    if isinstance(value, Path):
        return str(value)
    return value


def _md(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _mean_key(block: dict) -> float:
    return float(block["mean_of_rounded_seed_statistics"])


def _attach_rounded_mean(values: list[float]) -> dict:
    summary = across_seed_dispersion(values)
    summary["mean_of_rounded_seed_statistics"] = float(np.mean(np.asarray(values, dtype="float64")))
    return summary


# ---------------------------------------------------------------------------
# splits
# ---------------------------------------------------------------------------


def _question_sets(split) -> dict[str, list[str]]:
    return {
        name: sorted(getattr(split, name)[split.group_column].astype(str).unique())
        for name in PARTITIONS
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return float(len(a & b) / len(union)) if union else float("nan")


def diagnose_splits(tables: dict[int, pd.DataFrame]) -> dict:
    """Old sort-then-permute versus positive-count stratification, seeds 0–2."""
    rows = []
    for seed, frame in tables.items():
        for method, splitter in (
            ("legacy_sort_then_permute", lambda df, s: grouped_split(df, seed=s, stratify=True)),
            ("group_stratified", lambda df, s: group_stratified_split(df, seed=s)),
        ):
            split = splitter(frame, seed)
            assert_disjoint(split)
            balance = split_balance(frame, split)
            balance["method"] = method
            balance["question_ids"] = _question_sets(split)
            claim_sets = [set(getattr(split, name)["claim_id"].astype(str)) for name in PARTITIONS]
            balance["claim_id_disjoint"] = (
                claim_sets[0].isdisjoint(claim_sets[1])
                and claim_sets[0].isdisjoint(claim_sets[2])
                and claim_sets[1].isdisjoint(claim_sets[2])
            )
            balance["question_id_disjoint"] = True
            rows.append(balance)
    paired = []
    for seed in tables:
        legacy = next(row for row in rows if row["seed"] == seed and row["method"] == "legacy_sort_then_permute")
        corrected = next(row for row in rows if row["seed"] == seed and row["method"] == "group_stratified")
        paired.append(
            {
                "seed": seed,
                "test_question_jaccard": _jaccard(
                    set(legacy["question_ids"]["test"]),
                    set(corrected["question_ids"]["test"]),
                ),
                "legacy_mad": legacy["mean_absolute_deviation"],
                "stratified_mad": corrected["mean_absolute_deviation"],
            }
        )
    by_method = {}
    for method in ("legacy_sort_then_permute", "group_stratified"):
        subset = [row for row in rows if row["method"] == method]
        mad = [row["mean_absolute_deviation"] for row in subset]
        by_method[method] = {
            "mean_mad": float(np.mean(mad)),
            "per_seed_mad": mad,
            "test_positives": [row["partitions"]["test"]["positives"] for row in subset],
            "test_rate_deviation": [row["partitions"]["test"]["positive_rate_deviation"] for row in subset],
        }
    drop = by_method["legacy_sort_then_permute"]["mean_mad"] - by_method["group_stratified"]["mean_mad"]
    return {
        "per_split": rows,
        "old_versus_new_test_overlap": paired,
        "summary": by_method,
        "mad_drop": float(drop),
        "mad_drop_threshold": MATERIAL_MAD_DROP,
        "mad_reduction_meets_threshold": bool(drop >= MATERIAL_MAD_DROP),
    }


def _text_duplication(frame: pd.DataFrame, split) -> dict:
    text = frame["claim_text"].astype(str)
    sizes = text.value_counts()
    duplicated = sizes[sizes > 1]
    same_question = 0
    cross_question = []
    for value, n_rows in duplicated.items():
        rows = frame[text == value]
        n_questions = int(rows["question_id"].nunique())
        if n_questions == 1:
            same_question += 1
            continue
        shown = value if len(value) <= 120 else value[:117] + "..."
        cross_question.append(
            {
                "text": shown,
                "length": int(len(value)),
                "rows": int(n_rows),
                "questions": n_questions,
                "generators": int(rows["generator_id"].nunique()),
                "positives": int(rows["label"].sum()),
            }
        )
    sets = {name: set(getattr(split, name)["claim_text"].astype(str)) for name in PARTITIONS}
    overlaps = {}
    for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
        shared = sets[left] & sets[right]
        overlaps[f"{left}_{right}"] = {
            "n_texts": len(shared),
            "texts": [
                {
                    "text": value if len(value) <= 120 else value[:117] + "...",
                    "length": len(value),
                    "positives": int(frame.loc[text == value, "label"].sum()),
                }
                for value in sorted(shared, key=len)
            ],
        }
    prefix = frame["claim_id"].astype(str).str.split("#").str[0]
    questions_per_response = frame.assign(_response=prefix).groupby("_response")["question_id"].nunique()
    assigned = {}
    for name in PARTITIONS:
        for question_id in getattr(split, name)["question_id"].astype(str):
            assigned[question_id] = name
    response_parts = (
        frame.assign(_response=prefix, _part=frame["question_id"].astype(str).map(assigned))
        .groupby("_response")["_part"]
        .nunique()
    )
    return {
        "duplicate_texts": int(len(duplicated)),
        "extra_duplicate_rows": int(duplicated.sum() - len(duplicated)),
        "same_question_duplicate_texts": int(same_question),
        "cross_question_duplicate_texts": cross_question,
        "exact_text_overlap_across_partitions": overlaps,
        "max_questions_per_response_prefix": int(questions_per_response.max()),
        "max_partitions_per_response_prefix": int(response_parts.max()),
    }


def leakage_report(tables: dict[int, pd.DataFrame]) -> dict:
    """What the columns support. No extra grouping key is introduced here."""
    columns = schema_record()["columns"]
    per_seed = []
    for seed, frame in tables.items():
        split = group_stratified_split(frame, seed=seed)
        small = frame.groupby(frame["question_id"].astype(str)).size()
        small = small[small < 6]
        truncated = []
        assigned = {}
        for name in PARTITIONS:
            for question_id in getattr(split, name)["question_id"].astype(str).unique():
                assigned[question_id] = name
        for question_id, n_rows in small.items():
            rows = frame[frame["question_id"].astype(str) == question_id]
            truncated.append(
                {
                    "question_id": str(question_id),
                    "claims": int(n_rows),
                    "generators": sorted(int(g) for g in rows["generator_id"].unique()),
                    "positives": int(rows["label"].sum()),
                    "partition": assigned[str(question_id)],
                }
            )
        per_seed.append(
            {
                "seed": seed,
                "question_id_disjoint": True,
                "generators_in_every_partition": {
                    name: sorted(int(g) for g in getattr(split, name)["generator_id"].unique())
                    for name in PARTITIONS
                },
                "positives": {
                    name: int(getattr(split, name)["label"].sum()) for name in PARTITIONS
                },
                "duplication": _text_duplication(frame, split),
                "truncated_groups": truncated,
                "cross_n_others": {
                    "min": int(frame["cross_n_others"].min()),
                    "max": int(frame["cross_n_others"].max()),
                },
                "evidence_source_nunique": int(frame["evidence_source"].nunique()),
                "source_nunique": int(frame["source"].nunique()),
                "task_type_nunique": int(frame["task_type"].nunique()),
                "tasks_per_question_max": int(frame.groupby("question_id")["task_type"].nunique().max()),
                "context_column_present": "context" in frame.columns,
            }
        )
    question_sets = [set(frame["question_id"].astype(str)) for frame in tables.values()]
    claim_sets = [set(frame["claim_id"].astype(str)) for frame in tables.values()]
    return {
        "question_id_meaning": columns["question_id"],
        "claim_id_meaning": columns["claim_id"],
        "repository_split_policy": schema_record()["split_policy"],
        "within_question_dependence": (
            "agree, contra, and sem_dist are scored against the other generators' "
            "answers for the same source. On these tables cross_n_others is 5 for "
            "every claim, so each row uses the other five answers. Those answers "
            "belong to the same question_id, and the split keeps that question in "
            "one partition."
        ),
        "per_seed": per_seed,
        "across_seed_question_overlap": {
            f"{a}_{b}": len(question_sets[a] & question_sets[b]) for a, b in ((0, 1), (0, 2), (1, 2))
        },
        "across_seed_claim_overlap": {
            f"{a}_{b}": len(claim_sets[a] & claim_sets[b]) for a, b in ((0, 1), (0, 2), (1, 2))
        },
        "additional_grouping_key": None,
    }


# ---------------------------------------------------------------------------
# fit and score
# ---------------------------------------------------------------------------


def fit_all(cfg, tables: dict[int, pd.DataFrame]) -> list[dict]:
    notes = []
    for variant in ALL_VARIANTS:
        for seed in SEEDS:
            ctx = RunContext.build(cfg, variant=variant, seed=seed)
            if STAGE6_DIR.resolve() not in ctx.out_dir.resolve().parents:
                raise RuntimeError(f"refusing to write outside {STAGE6_DIR}: {ctx.out_dir}")
            result = fit_variant(ctx, df=tables[seed])
            persist(ctx, result)
            notes.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "skipped": result.skipped,
                    "auroc": None if result.skipped else result.test.auroc,
                }
            )
            print(f"  fit {variant} seed={seed} skipped={result.skipped}", flush=True)
    return notes


def _metrics_path(variant: str, seed: int) -> Path:
    return STAGE6_DIR / f"{variant}_seed{seed}" / "metrics.json"


def _checkpoint_path(variant: str, seed: int) -> Path:
    return STAGE6_DIR / f"{variant}_seed{seed}" / "model.joblib"


def score_checkpoints(tables: dict[int, pd.DataFrame], n_resamples: int) -> dict:
    """Reload the new checkpoints and apply the Stage 5 grouped protocol."""
    import joblib

    bundles = {}
    checks = []
    for seed in SEEDS:
        frame = tables[seed]
        split = group_stratified_split(frame, seed=seed)
        test = split.test
        y = test["label"].to_numpy()
        groups = test["question_id"].astype(str).to_numpy()
        scores = {}
        thresholds = {}
        for variant in VARIANTS:
            meta = json.loads(_metrics_path(variant, seed).read_text())
            if meta.get("skipped"):
                checks.append({"variant": variant, "seed": seed, "skipped": meta["skipped"]})
                continue
            if meta.get("split_method") != SPLIT_GROUP_STRATIFIED or int(meta["split_seed"]) != seed:
                raise RuntimeError(f"{variant} seed {seed} was not fit with the stratified split")
            model = joblib.load(_checkpoint_path(variant, seed))
            score = np.asarray(model.predict_proba(test), dtype="float64")
            threshold = float(meta["threshold"])
            metrics = slice_metrics(y, score, name="all", threshold=threshold, n_bins=15)
            got = metrics.as_dict()
            expected = meta["test"]
            for key in ("auroc", "f1", "precision", "recall", "ece", "n"):
                if got[key] != expected[key]:
                    raise RuntimeError(
                        f"reloaded {variant} seed {seed} {key}={got[key]} "
                        f"does not match metrics.json {expected[key]}"
                    )
            scores[variant] = score
            thresholds[variant] = threshold
            checks.append({"variant": variant, "seed": seed, "matched_metrics_json": True, "n": int(y.size)})
        bundles[seed] = {
            "y": y,
            "groups": groups,
            "scores": scores,
            "thresholds": thresholds,
            "n_questions": int(np.unique(groups).size),
        }
    variants = []
    for variant in VARIANTS:
        per_seed = []
        for seed in SEEDS:
            bundle = bundles[seed]
            y = bundle["y"]
            score = bundle["scores"][variant]
            groups = bundle["groups"]
            threshold = bundle["thresholds"][variant]
            rounded = slice_metrics(y, score, name="all", threshold=threshold, n_bins=15).as_dict()
            interval = within_seed_auroc_interval(y, score, groups, n_resamples=n_resamples, seed=seed)
            per_seed.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "n_claims": int(y.size),
                    "n_questions": int(np.unique(groups).size),
                    "n_positive": int(np.asarray(y).sum()),
                    "threshold": threshold,
                    "auroc": rounded["auroc"],
                    "f1": rounded["f1"],
                    "precision": rounded["precision"],
                    "recall": rounded["recall"],
                    "ece": rounded["ece"],
                    "grouped_interval": interval,
                }
            )
        summary = {"variant": variant, "per_seed": per_seed}
        for name in ("auroc", "f1", "precision", "recall", "ece"):
            summary[name] = _attach_rounded_mean([row[name] for row in per_seed])
        variants.append(summary)

    paired = {}
    for baseline in PAIRED_BASELINES:
        per_seed = []
        for seed in SEEDS:
            bundle = bundles[seed]
            corrected = paired_question_delta(
                bundle["y"],
                bundle["scores"]["A7"],
                bundle["scores"][baseline],
                bundle["groups"],
                n_resamples=n_resamples,
                seed=seed,
            )
            per_seed.append(
                {
                    "comparison": f"A7 - {baseline}",
                    "baseline": baseline,
                    "seed": seed,
                    "n_claims": int(bundle["y"].size),
                    "n_questions": int(np.unique(bundle["groups"]).size),
                    "delta_auroc": None if corrected["delta"] is None else round(float(corrected["delta"]), 4),
                    "grouped_interval": {
                        "lo": corrected["lo"],
                        "hi": corrected["hi"],
                        "n_requested": corrected["n_requested"],
                        "n_finite": corrected["n_finite"],
                        "position_vs_0": classify_interval(corrected["lo"], corrected["hi"]),
                    },
                    "bootstrap_frac_delta_gt_0": corrected["bootstrap_frac_delta_gt_0"],
                }
            )
        deltas = [row["delta_auroc"] for row in per_seed]
        paired[baseline] = {
            "comparison": f"A7 - {baseline}",
            "per_seed": per_seed,
            "delta": _attach_rounded_mean(deltas),
            "seed_interval_positions": [row["grouped_interval"]["position_vs_0"] for row in per_seed],
        }
    return {"variants": variants, "paired": paired, "checks": checks}


def _index_stage5(payload: dict) -> dict:
    return {
        "variants": {item["variant"]: item for item in payload["variants"]},
        "paired": payload["paired"],
    }


# ---------------------------------------------------------------------------
# conclusion
# ---------------------------------------------------------------------------


def judge(diagnostics: dict, stage5: dict, stage6: dict) -> dict:
    """Qualitative reading. The label is about the Stage 5 claim, not a p-value.

    The Stage 5 claim is that A7 is not supported as better than A0 or A4.
    ``materially_sensitive`` means that claim reverses. ``weakened`` means A7
    moves toward a baseline by more than that comparison's across-seed SD, or
    a mean ordering flips, while every paired interval still fails to lie
    entirely above 0. ``strengthened`` means the evidence against an A7
    advantage gets sharper by the same scale, or an interval moves entirely
    below 0. Otherwise the claim is ``unchanged``.
    """

    def mean(block: dict, variant: str) -> float:
        return _mean_key(block["variants"][variant]["auroc"])

    def sd(block: dict, variant: str) -> float:
        return float(block["variants"][variant]["auroc"]["sd_across_seeds"])

    shifts = {
        variant: mean(stage6, variant) - mean(stage5, variant) for variant in VARIANTS
    }
    positions = {
        baseline: {
            "stage5": stage5["paired"][baseline]["seed_interval_positions"],
            "stage6": stage6["paired"][baseline]["seed_interval_positions"],
        }
        for baseline in ("A0", "A4")
    }
    delta_shift = {
        baseline: _mean_key(stage6["paired"][baseline]["delta"]) - _mean_key(stage5["paired"][baseline]["delta"])
        for baseline in ("A0", "A4")
    }
    delta_sd = {
        baseline: float(stage5["paired"][baseline]["delta"]["sd_across_seeds"])
        for baseline in ("A0", "A4")
    }
    new_above = {
        baseline: mean(stage6, "A7") > mean(stage6, baseline) for baseline in ("A0", "A4")
    }
    old_above = {
        baseline: mean(stage5, "A7") > mean(stage5, baseline) for baseline in ("A0", "A4")
    }
    any_above_zero = any(
        pos == "entirely_above_0"
        for baseline in ("A0", "A4")
        for pos in positions[baseline]["stage6"]
    )
    any_new_below = any(
        new == "entirely_below_0" and old != "entirely_below_0"
        for baseline in ("A0", "A4")
        for old, new in zip(
            positions[baseline]["stage5"],
            positions[baseline]["stage6"],
            strict=True,
        )
    )
    moved_toward_a7 = any(delta_shift[baseline] > delta_sd[baseline] for baseline in ("A0", "A4"))
    moved_against_a7 = any(-delta_shift[baseline] > delta_sd[baseline] for baseline in ("A0", "A4"))
    ordering_flip = any(new_above[baseline] != old_above[baseline] for baseline in ("A0", "A4"))

    if any_above_zero or (moved_toward_a7 and moved_against_a7):
        label = "materially_sensitive"
    elif ordering_flip or moved_toward_a7:
        label = "weakened"
    elif any_new_below or moved_against_a7:
        label = "strengthened"
    else:
        label = "unchanged"

    return {
        "stage5_claim": "A7 is not supported as better than A0 or A4",
        "label": label,
        "auroc_mean_shift_stage6_minus_stage5": shifts,
        "a7_mean_above_baseline": {"stage5": old_above, "stage6": new_above},
        "paired_interval_positions": positions,
        "paired_delta_mean_shift": delta_shift,
        "stage5_paired_delta_sd": delta_sd,
        "any_stage6_paired_interval_entirely_above_0": any_above_zero,
        "a7_auroc_sd_stage5": sd(stage5, "A7"),
        "a7_auroc_sd_stage6": sd(stage6, "A7"),
        "balance_mad_reduction_meets_0_01": diagnostics["mad_reduction_meets_threshold"],
        "three_seeds_are_not_a_robustness_proof": True,
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _variant_table(block: dict, title: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        _md(
            [
                "variant",
                "mean AUROC (point estimate)",
                "sd of AUROC across seeds (not a confidence interval)",
                "mean F1 (point estimate)",
                "sd of F1 across seeds (not a confidence interval)",
                "mean precision (point estimate)",
                "sd of precision across seeds (not a confidence interval)",
                "mean recall (point estimate)",
                "sd of recall across seeds (not a confidence interval)",
                "mean ECE (point estimate)",
                "sd of ECE across seeds (not a confidence interval)",
            ]
        ),
        _md(["---"] * 11),
    ]
    for variant in VARIANTS:
        item = block["variants"][variant]
        cells = [variant]
        for name in ("auroc", "f1", "precision", "recall", "ece"):
            cells.append(format_point(_mean_key(item[name])))
            cells.append(format_point(item[name]["sd_across_seeds"]))
        lines.append(_md(cells))
    lines.append("")
    return lines


def _per_seed_table(block: dict, title: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "Each bracket is that seed's interval. Endpoints are not averaged.",
        "",
        _md(
            [
                "variant",
                "seed",
                "n claims",
                "n questions",
                "n positive",
                "AUROC (point estimate)",
                "within-seed 95% question-grouped percentile bootstrap interval",
                "resamples requested",
                "resamples finite",
                "F1",
                "precision",
                "recall",
                "ECE",
            ]
        ),
        _md(["---"] * 13),
    ]
    for variant in VARIANTS:
        for row in block["variants"][variant]["per_seed"]:
            interval = row["grouped_interval"]
            lines.append(
                _md(
                    [
                        variant,
                        str(row["seed"]),
                        str(row["n_claims"]),
                        str(row["n_questions"]),
                        str(row["n_positive"]),
                        format_point(row["auroc"]),
                        format_interval(interval["lo"], interval["hi"]),
                        str(interval["n_requested"]),
                        str(interval["n_finite"]),
                        format_point(row["f1"]),
                        format_point(row["precision"]),
                        format_point(row["recall"]),
                        format_point(row["ece"]),
                    ]
                )
            )
    lines.append("")
    return lines


def _paired_table(block: dict, title: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "Delta is AUROC(A7) minus AUROC(baseline) on the same test claims.",
        "One resample draws question ids once and scores both models on those claims.",
        "The bootstrap fraction is not a p-value. Interval endpoints are not averaged.",
        "",
        _md(
            [
                "comparison",
                "seed",
                "delta AUROC (point estimate)",
                "per-seed 95% paired question-grouped percentile bootstrap interval",
                "interval vs 0",
                "resamples finite",
                "bootstrap fraction delta > 0 (not a p-value)",
            ]
        ),
        _md(["---"] * 7),
    ]
    for baseline in ("A0", "A4"):
        for row in block["paired"][baseline]["per_seed"]:
            interval = row["grouped_interval"]
            lines.append(
                _md(
                    [
                        row["comparison"],
                        str(row["seed"]),
                        format_point(row["delta_auroc"]),
                        format_interval(interval["lo"], interval["hi"]),
                        interval["position_vs_0"],
                        f"{interval['n_finite']}/{interval['n_requested']}",
                        format_point(row["bootstrap_frac_delta_gt_0"]),
                    ]
                )
            )
    lines += [
        "",
        _md(
            [
                "comparison",
                "mean delta AUROC (point estimate)",
                "sd of delta across seeds (not a confidence interval)",
                "per-seed interval positions",
            ]
        ),
        _md(["---"] * 4),
    ]
    for baseline in ("A0", "A4"):
        item = block["paired"][baseline]
        lines.append(
            _md(
                [
                    item["comparison"],
                    format_point(_mean_key(item["delta"])),
                    format_point(item["delta"]["sd_across_seeds"]),
                    ", ".join(item["seed_interval_positions"]),
                ]
            )
        )
    lines.append("")
    return lines


def _balance_lines(diagnostics: dict) -> list[str]:
    lines = [
        "## Split balance",
        "",
        "Deviation is the partition positive rate minus the full-table positive rate (0.07125, 57/800).",
        f"A mean-absolute-deviation reduction of at least {MATERIAL_MAD_DROP:.2f} was specified as the "
        "bar for calling the balance change real. Smaller movements are not called material.",
        "",
        _md(
            [
                "method",
                "seed",
                "part",
                "groups",
                "claims",
                "positives",
                "positive rate",
                "deviation from full table",
            ]
        ),
        _md(["---"] * 8),
    ]
    for row in diagnostics["per_split"]:
        for name in PARTITIONS:
            part = row["partitions"][name]
            lines.append(
                _md(
                    [
                        row["method"],
                        str(row["seed"]),
                        name,
                        str(part["groups"]),
                        str(part["claims"]),
                        str(part["positives"]),
                        format_point(part["positive_rate"]),
                        format_point(part["positive_rate_deviation"]),
                    ]
                )
            )
    summary = diagnostics["summary"]
    lines += [
        "",
        f"- Legacy mean MAD: {format_point(summary['legacy_sort_then_permute']['mean_mad'])}.",
        f"- Group-stratified mean MAD: {format_point(summary['group_stratified']['mean_mad'])}.",
        f"- MAD drop (legacy minus stratified): {format_point(diagnostics['mad_drop'])}.",
        f"- Meets the {MATERIAL_MAD_DROP:.2f} bar: {diagnostics['mad_reduction_meets_threshold']}.",
        "- Legacy test positive counts: "
        + ", ".join(str(v) for v in summary["legacy_sort_then_permute"]["test_positives"])
        + ".",
        "- Stratified test positive counts: "
        + ", ".join(str(v) for v in summary["group_stratified"]["test_positives"])
        + ".",
        "",
        "Test-question Jaccard between the legacy split and the stratified split, by seed:",
        "",
    ]
    for row in diagnostics["old_versus_new_test_overlap"]:
        lines.append(f"- seed {row['seed']}: {format_point(row['test_question_jaccard'])}")
    lines.append("")
    return lines


def _leakage_lines(leakage: dict) -> list[str]:
    lines = [
        "## Leakage and duplication",
        "",
        f"- `question_id` in this repository: {leakage['question_id_meaning']}.",
        f"- `claim_id`: {leakage['claim_id_meaning']}.",
        f"- Split policy recorded with the loader: {leakage['repository_split_policy']}.",
        f"- Within-question dependence: {leakage['within_question_dependence']}",
        "- No additional grouping key is introduced. `source` has two corpus names and "
        "`task_type` has two task names; both are coarse labels, and each question has one task. "
        "`evidence_source` is a constant. The response prefix of `claim_id` maps to one question.",
        f"- Question overlap across the three frozen tables: {leakage['across_seed_question_overlap']}.",
        f"- Claim overlap across the three frozen tables: {leakage['across_seed_claim_overlap']}.",
        "",
    ]
    for seed_row in leakage["per_seed"]:
        dup = seed_row["duplication"]
        lines.append(f"### Seed {seed_row['seed']}")
        lines.append("")
        lines.append(
            f"Generators present: {seed_row['generators_in_every_partition']}. "
            f"Positive counts: {seed_row['positives']}. "
            f"Truncated groups: {seed_row['truncated_groups']}. "
            f"`cross_n_others` range: {seed_row['cross_n_others']}."
        )
        lines.append("")
        lines.append(
            f"Duplicate exact texts: {dup['duplicate_texts']} "
            f"({dup['same_question_duplicate_texts']} confined to one question, "
            f"{len(dup['cross_question_duplicate_texts'])} spanning questions). "
            f"Max questions per response prefix: {dup['max_questions_per_response_prefix']}. "
            f"Max partitions per response prefix: {dup['max_partitions_per_response_prefix']}."
        )
        lines.append("")
        if dup["cross_question_duplicate_texts"]:
            lines.append("Cross-question repeated strings:")
            lines.append("")
            for item in dup["cross_question_duplicate_texts"]:
                lines.append(
                    f"- `{item['text']}` length {item['length']}, rows {item['rows']}, "
                    f"questions {item['questions']}, positives {item['positives']}."
                )
            lines.append("")
        for key, overlap in dup["exact_text_overlap_across_partitions"].items():
            shown = ", ".join(f"`{item['text']}`" for item in overlap["texts"]) or "none"
            lines.append(f"- Exact text overlap {key}: {overlap['n_texts']} ({shown}).")
        lines.append("")
    return lines


def _paper_paragraph(conclusion: dict, stage5: dict, stage6: dict) -> str:
    def mean(block, variant):
        return format_point(_mean_key(block["variants"][variant]["auroc"]))

    def sd(block, variant):
        return format_point(block["variants"][variant]["auroc"]["sd_across_seeds"])

    a0_pos = ", ".join(conclusion["paired_interval_positions"]["A0"]["stage6"])
    a4_pos = ", ".join(conclusion["paired_interval_positions"]["A4"]["stage6"])
    return (
        f"On the frozen corrected RAGTruth tables, refitting A0–A7 with positive-count "
        f"group stratification in place of the sort-then-permute split gives mean test "
        f"AUROC {mean(stage6, 'A7')} for RC-Gate (A7), {mean(stage6, 'A0')} for flat "
        f"logistic regression (A0), and {mean(stage6, 'A4')} for the metadata "
        f"gradient-boosting control (A4). Under the previous split those means were "
        f"{mean(stage5, 'A7')}, {mean(stage5, 'A0')}, and {mean(stage5, 'A4')}. "
        f"The A7 mean is lower after the change; it remains below A0 and below A4. "
        f"Across-seed standard deviations on the new split are {sd(stage6, 'A7')} for A7, "
        f"{sd(stage6, 'A0')} for A0, and {sd(stage6, 'A4')} for A4, and are not confidence "
        f"intervals. Within each seed the uncertainty is a 95% percentile bootstrap on "
        f"the test question ids (1000 resamples). The paired A7−A0 intervals are {a0_pos}; "
        f"the paired A7−A4 intervals are {a4_pos}. No paired interval lies entirely above 0. "
        f"The Stage 5 statement that A7 is not supported as better than A0 or A4 still "
        f"holds, and the point estimates sit further from an A7 advantage. The three seeds "
        f"reuse nearly the same claims, so this rerun does not show that the result is "
        f"robust to split construction in general, and it does not show that the earlier "
        f"negative conclusion was produced by the sort-then-permute split."
    )


def render_markdown(result: dict) -> str:
    conclusion = result["conclusion"]
    lines = [
        "# RC-Gate Stage 6 — group-stratified split sensitivity",
        "",
        "This file changes the split and nothing else. Architecture, variant definitions,",
        "signals, labels, claim text, and the Stage 5 uncertainty procedure are unchanged.",
        "Historical result directories were not rewritten.",
        "Three seeds are three seeds. They are not a robustness proof.",
        "",
        "## What the old splitter does",
        "",
        "`grouped_split(..., stratify=True)` sorts `question_id` groups by their mean label,",
        "draws one permutation of that sorted list with `numpy.random.default_rng(seed)`,",
        "and cuts the permuted list into blocks of about 60/20/20 groups.",
        "The permutation removes the sort. The flag does not stratify.",
        "Question ids are still disjoint across train, validation, and test.",
        "",
        "## Corrected split",
        "",
        "What is stratified: the group's positive-claim count, not the claim.",
        "What is grouped: `question_id` (RAGTruth `source_id`). Every claim of a source stays together.",
        "Proportions: inside each count stratum, `round(0.6 n)` train groups, `round(0.2 n)` validation groups, remainder test.",
        "Seed: `numpy.random.default_rng(SeedSequence([seed, stratum]))` shuffles the sorted group ids of that stratum.",
        "The same seed repeats. A different seed can reshuffle a stratum that has more than one group.",
        "The shuffle does not depend on row order or on which other strata exist.",
        "Limit: a stratum of size 2 contributes 1 train group, 0 validation groups, and 1 test group.",
        "On these tables the counts 3 and 4 each have two groups, so validation receives none of those 7 positive claims.",
        "The resulting positive totals are 33 train, 9 validation, and 15 test, on every seed.",
        "The method does not search for a closer rate.",
        "",
        "## Protocol",
        "",
        "- Tables: `ragtruth_corrected_integrity_v1_s{0,1,2}.parquet` (800 claims, not rebuilt).",
        "- Variants A0–A7 refit. A8 skipped because the tables have no judge votes.",
        "- Seeds 0, 1, and 2 are both the model seed and the split seed.",
        "- Thresholds are the validation F1 quantile rule from the training code, applied to the new validation split.",
        "- Point estimate: unweighted mean of the three seed statistics after 4-decimal rounding.",
        "- Across-seed dispersion: sample standard deviation, ddof=1. Not a confidence interval.",
        "- Within-seed interval: 95% question-grouped percentile bootstrap, 1000 resamples.",
        "- Paired interval: the same question draw scores both models. Not an average of endpoints.",
        "- No classical p-value.",
        "",
        *_balance_lines(result["diagnostics"]),
        *_leakage_lines(result["leakage"]),
        "## Stage 5 canonical result (previous split)",
        "",
        *_variant_table(result["stage5"], "Means"),
        *_per_seed_table(result["stage5"], "Per seed"),
        *_paired_table(result["stage5"], "Paired A7 minus A0 and A7 minus A4"),
        "## Stage 6 group-stratified result",
        "",
        *_variant_table(result["stage6"], "Means"),
        *_per_seed_table(result["stage6"], "Per seed"),
        *_paired_table(result["stage6"], "Paired A7 minus A0 and A7 minus A4"),
        "## Mean shifts (Stage 6 minus Stage 5)",
        "",
        "A shift is a difference of point estimates. It is not a confidence interval.",
        "",
        _md(["variant", "mean AUROC shift", "Stage 5 sd of AUROC", "Stage 6 sd of AUROC"]),
        _md(["---"] * 4),
    ]
    for variant in VARIANTS:
        lines.append(
            _md(
                [
                    variant,
                    format_point(conclusion["auroc_mean_shift_stage6_minus_stage5"][variant]),
                    format_point(result["stage5"]["variants"][variant]["auroc"]["sd_across_seeds"]),
                    format_point(result["stage6"]["variants"][variant]["auroc"]["sd_across_seeds"]),
                ]
            )
        )
    lines += [
        "",
        _md(
            [
                "comparison",
                "mean delta shift",
                "Stage 5 sd of delta",
                "Stage 6 mean delta",
                "Stage 6 sd of delta",
            ]
        ),
        _md(["---"] * 5),
    ]
    for baseline in ("A0", "A4"):
        lines.append(
            _md(
                [
                    f"A7 - {baseline}",
                    format_point(conclusion["paired_delta_mean_shift"][baseline]),
                    format_point(conclusion["stage5_paired_delta_sd"][baseline]),
                    format_point(_mean_key(result["stage6"]["paired"][baseline]["delta"])),
                    format_point(result["stage6"]["paired"][baseline]["delta"]["sd_across_seeds"]),
                ]
            )
        )
    lines += [
        "",
        "## Verdict",
        "",
        f"Label for the Stage 5 claim: **{conclusion['label']}**.",
        "",
        f"- A7 mean above A0: Stage 5 {conclusion['a7_mean_above_baseline']['stage5']['A0']}, "
        f"Stage 6 {conclusion['a7_mean_above_baseline']['stage6']['A0']}.",
        f"- A7 mean above A4: Stage 5 {conclusion['a7_mean_above_baseline']['stage5']['A4']}, "
        f"Stage 6 {conclusion['a7_mean_above_baseline']['stage6']['A4']}.",
        f"- Any Stage 6 paired A7−A0 or A7−A4 interval entirely above 0: "
        f"{conclusion['any_stage6_paired_interval_entirely_above_0']}.",
        f"- Balance MAD reduction meets 0.01: {conclusion['balance_mad_reduction_meets_0_01']}.",
        "- The label uses the across-seed SD of the paired delta as the scale for a mean shift.",
        "  A shift inside that SD, with the same ordering and intervals that still cover 0, is not a new conclusion.",
        "- This label is not a hypothesis test, and three seeds do not prove robustness.",
        "",
        "### Paper-safe paragraph",
        "",
        _paper_paragraph(conclusion, result["stage5"], result["stage6"]),
        "",
        "### Limitations",
        "",
        "- Three seeds, and the frozen tables share almost all of their claims, so the seed SD mixes split assignment with fitting on one pool.",
        "- Validation has 9 positive claims and 26 questions. Test has 15 positive claims and 28 questions. The grouped intervals are wide.",
        "- Strata with two groups cannot enter all three partitions. Test stays a few positive claims above the 20% share.",
        "- Claims inside a question share cross-model features. The split keeps the question together; the bootstrap treats it as one group.",
        "- A few short repeated strings appear in more than one partition. They were not removed.",
        "- F1, precision, recall, and ECE have an across-seed SD only.",
        "- Leave-one-generator-out was not refit. It still calls the legacy splitter.",
        "- A8 remains skipped.",
        "",
    ]
    return "\n".join(lines)


def write_results(result: dict) -> Path:
    STAGE6_DIR.mkdir(parents=True, exist_ok=True)
    payload = _jsonable(result)
    (STAGE6_DIR / "report.json").write_text(json.dumps(payload, indent=2))
    report = render_markdown(result)
    (STAGE6_DIR / "report.md").write_text(report)
    provenance = {
        "stage": "ragtruth_split_corrected_v1",
        "git_head": git_hash(PROJECT_ROOT),
        "git_head_does_not_include_uncommitted_stage6_edits": True,
        "split_method": SPLIT_GROUP_STRATIFIED,
        "split_definition": (
            "Within each question_id positive-count stratum, shuffle sorted group ids "
            "with Generator(SeedSequence([seed, stratum])) and cut with round(0.6 n), "
            "round(0.2 n), remainder test."
        ),
        "signal_tables": [str(path) for path in TABLES],
        "signal_table_sha256": result["table_sha256"],
        "stage5_dir": str(STAGE5_DIR),
        "stage4_dir": str(SUMMARY_DIR / "ragtruth_corrected_integrity_v1"),
        "historical_directories_unchanged": result["protected_unchanged"],
        "models": "refit with the same fit_variant path; hyperparameters from the Stage 4 config",
        "thresholds": "tune_threshold on the new validation split; not chosen from test A7",
        "statistics": "Stage 5 question-grouped percentile bootstrap, 1000 resamples",
        "interval_endpoints_averaged": False,
        "formal_p_value_reported": False,
        "a8": "skipped; no judge votes",
        "logo": "not rerun",
        "n_resamples": result["n_resamples"],
        "numpy": result["numpy"],
        "conclusion_label": result["conclusion"]["label"],
    }
    (STAGE6_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2))
    return STAGE6_DIR / "report.md"


def evaluate(fit: bool = True) -> dict:
    if any(not path.exists() for path in TABLES):
        raise FileNotFoundError("frozen corrected signal tables are missing; refusing to rebuild them")
    if any(not path.exists() for path in PROTECTED):
        raise FileNotFoundError("a historical result file is missing; refusing to run")
    protected_before = _snapshot(PROTECTED)
    table_before = {str(path): _sha256(path) for path in TABLES}
    cfg = load_named(CONFIG_NAME)
    if cfg.get("data.split_method") != SPLIT_GROUP_STRATIFIED:
        raise RuntimeError("Stage 6 config is not group_stratified")
    if cfg.get("report.tag") != STAGE6_DIR.name:
        raise RuntimeError("Stage 6 config would write outside its namespace")
    tables = {seed: load_table(path) for seed, path in zip(SEEDS, TABLES, strict=True)}
    diagnostics = diagnose_splits(tables)
    leakage = leakage_report(tables)
    if fit:
        fit_all(cfg, tables)
    scored = score_checkpoints(tables, N_RESAMPLES)
    stage6 = {
        "variants": {item["variant"]: item for item in scored["variants"]},
        "paired": scored["paired"],
    }
    stage5_payload = json.loads((STAGE5_DIR / "report.json").read_text())
    stage5 = _index_stage5(stage5_payload)
    conclusion = judge(diagnostics, stage5, stage6)
    protected_after = _snapshot(PROTECTED)
    table_after = {str(path): _sha256(path) for path in TABLES}
    if protected_before != protected_after:
        raise RuntimeError("a historical result file changed during Stage 6")
    if table_before != table_after:
        raise RuntimeError("a frozen signal table changed during Stage 6")
    a8 = json.loads(_metrics_path("A8", 0).read_text())
    if not a8.get("skipped"):
        raise RuntimeError("A8 was not skipped")
    return {
        "n_resamples": N_RESAMPLES,
        "numpy": np.__version__,
        "table_sha256": table_before,
        "protected_unchanged": True,
        "diagnostics": diagnostics,
        "leakage": leakage,
        "stage5": stage5,
        "stage6": stage6,
        "conclusion": conclusion,
        "a8_skipped": a8["skipped"],
        "checkpoint_checks": scored["checks"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 6 group-stratified split sensitivity")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Rewrite report.md from report.json without refitting.",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Rescore existing Stage 6 checkpoints without refitting.",
    )
    args = parser.parse_args(argv)
    if args.render_only:
        payload = json.loads((STAGE6_DIR / "report.json").read_text())
        (STAGE6_DIR / "report.md").write_text(render_markdown(payload))
        print(f"rewrote {STAGE6_DIR / 'report.md'}")
        return 0
    result = evaluate(fit=not args.score_only)
    path = write_results(result)
    print(f"wrote {path}")
    print(f"conclusion {result['conclusion']['label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

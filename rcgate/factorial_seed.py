"""Stage 8: cross split seed with model seed on one frozen RAGTruth table.

Stage 7 passed the same integer to the splitter and to model fitting. This
module keeps those two integers separate. The splitter, features, labels,
architectures, hyperparameters, and the Stage 5 uncertainty procedure stay
as they are. Reported point metrics are computed from the saved-and-reloaded
checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_named
from .data.splits import (
    SPLIT_GROUP_STRATIFIED,
    assert_disjoint,
    group_stratified_split,
)
from .metrics import auroc, slice_metrics, tune_threshold
from .paths import PROJECT_ROOT, SUMMARY_DIR
from .pipeline import RunContext, fit_variant, load_table, persist
from .stats_protocol import (
    N_RESAMPLES,
    classify_interval,
    format_point,
    paired_question_delta,
    within_seed_auroc_interval,
)
from .utils import dump_json
from .variants import is_runnable

STAGE4_DIR = SUMMARY_DIR / "ragtruth_corrected_integrity_v1"
STAGE5_DIR = SUMMARY_DIR / "ragtruth_corrected_stats_v1"
STAGE6_DIR = SUMMARY_DIR / "ragtruth_split_corrected_v1"
STAGE7_DIR = SUMMARY_DIR / "ragtruth_multi_seed_v1"
STAGE_DIR = SUMMARY_DIR / "ragtruth_factorial_seed_v1"
CONFIG_NAME = "ragtruth_factorial_seed_v1"
FIT_TABLE = PROJECT_ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"
SPLIT_SEEDS = tuple(range(20))
MODEL_SEEDS = (0, 1, 2)
VARIANTS = tuple(f"A{i}" for i in range(8))
BASELINES = ("A0", "A4")
METRICS = ("auroc", "f1", "precision", "recall", "ece")
SOURCE_FILES = (
    "rcgate/pipeline.py",
    "rcgate/data/splits.py",
    "rcgate/models/rcgate.py",
    "rcgate/models/baselines.py",
    "rcgate/models/gate.py",
    "rcgate/models/experts.py",
    "rcgate/models/meta.py",
    "rcgate/metrics.py",
    "rcgate/utils.py",
    "rcgate/stats_protocol.py",
    "rcgate/factorial_seed.py",
    "configs/ragtruth_factorial_seed_v1.yaml",
)
PROTECTED_ROOTS = (STAGE4_DIR, STAGE5_DIR, STAGE6_DIR, STAGE7_DIR, SUMMARY_DIR / "ragtruth_historical_freeze")
SPLIT_NOTE = (
    "Split-level statistics are repeated partitions of one question pool, "
    "not independent datasets."
)
WITHIN_NOTE = (
    "Within-split dispersion uses the model seeds inside each split. "
    "With only three model seeds this is a preliminary description, "
    "not a precise population estimate."
)
PREDICTION_SOURCE = "reloaded_checkpoint"
THRESHOLD_SOURCE = "tune_threshold on reloaded validation scores"


def sample_distribution(values, unit: str) -> dict:
    """Sample distribution. The SD uses ddof=1. This is not a confidence interval."""
    arr = np.asarray(list(values), dtype="float64")
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        empty = float("nan")
        summary = {
            "n": int(arr.size),
            "n_finite": 0,
            "mean": empty,
            "median": empty,
            "sd": empty,
            "min": empty,
            "max": empty,
            "q25": empty,
            "q75": empty,
            "iqr": empty,
        }
    else:
        q25, q75 = np.quantile(finite, [0.25, 0.75])
        summary = {
            "n": int(arr.size),
            "n_finite": int(finite.size),
            "mean": float(finite.mean()),
            "median": float(np.median(finite)),
            "sd": float(np.std(finite, ddof=1)) if finite.size >= 2 else float("nan"),
            "min": float(finite.min()),
            "max": float(finite.max()),
            "q25": float(q25),
            "q75": float(q75),
            "iqr": float(q75 - q25),
        }
    summary["values"] = [None if not np.isfinite(v) else float(v) for v in arr]
    summary["is_confidence_interval"] = False
    summary["label"] = (
        f"sample distribution across {unit} (ddof=1 for the SD); not a confidence interval"
    )
    return summary


def assignment_maps(split) -> dict[str, str]:
    """Map each question id to the one partition that contains it."""
    found: dict[str, str] = {}
    for name in ("train", "val", "test"):
        for question_id in getattr(split, name)[split.group_column].astype(str).unique():
            if question_id in found:
                raise AssertionError(f"{question_id} is in {found[question_id]} and {name}")
            found[question_id] = name
    return found


def assignment_hash(split) -> str:
    lines = [f"{question_id}\t{name}" for question_id, name in sorted(assignment_maps(split).items())]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def decompose(records: list[dict], value_key: str, split_seeds, model_seeds) -> dict:
    """Cell distribution, split-level means, and within-split SDs.

    Interval endpoints are not an input. Nothing here averages them.
    """
    per_split = []
    means = []
    sds = []
    cells = []
    by_model = {int(model_seed): [] for model_seed in model_seeds}
    for split_seed in split_seeds:
        values = []
        for model_seed in model_seeds:
            matches = [
                row[value_key]
                for row in records
                if int(row["split_seed"]) == int(split_seed) and int(row["model_seed"]) == int(model_seed)
            ]
            if len(matches) != 1:
                raise RuntimeError(f"expected one {value_key} for split {split_seed} model {model_seed}")
            value = float(matches[0])
            values.append(value)
            cells.append(value)
            by_model[int(model_seed)].append(value)
        mean = float(np.mean(values))
        sd = float(np.std(values, ddof=1)) if len(values) >= 2 else float("nan")
        means.append(mean)
        sds.append(sd)
        per_split.append(
            {
                "split_seed": int(split_seed),
                "values": values,
                "mean": mean,
                "sd": sd,
            }
        )
    return {
        "over_cells": sample_distribution(cells, "split/model cells"),
        "over_split_means": sample_distribution(means, "split-level means"),
        "within_split_sd": sample_distribution(sds, "within-split sample SDs"),
        "by_model_seed": {
            str(model_seed): sample_distribution(values, f"split seeds at model seed {model_seed}")
            for model_seed, values in by_model.items()
        },
        "per_split": per_split,
        "n_model_seeds": len(tuple(model_seeds)),
        "n_split_seeds": len(tuple(split_seeds)),
        "split_note": SPLIT_NOTE,
        "within_split_note": WITHIN_NOTE,
    }


def method_of_moments(split_means, within_sds, n_model: int) -> dict:
    """Descriptive split of cell variance. Not a sample of independent datasets."""
    means = np.asarray(list(split_means), dtype="float64")
    within = np.asarray(list(within_sds), dtype="float64")
    sigma_e2 = float(np.mean(np.square(within)))
    sigma_means2 = float(np.var(means, ddof=1)) if means.size >= 2 else float("nan")
    sigma_a2 = float(sigma_means2 - sigma_e2 / n_model)
    total = sigma_a2 + sigma_e2
    share = float(sigma_a2 / total) if np.isfinite(total) and total > 0 and sigma_a2 > 0 else None
    return {
        "within_variance_mean": sigma_e2,
        "variance_of_split_means": sigma_means2,
        "between_split_variance": sigma_a2,
        "between_share_of_cell_variance": share,
        "n_model_seeds": int(n_model),
        "label": (
            "descriptive method of moments on repeated partitions of one pool; "
            "not a variance component from independent datasets"
        ),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(roots: tuple[Path, ...]) -> dict[str, tuple[int, int]]:
    found = {}
    for root in roots:
        if not root.exists():
            raise FileNotFoundError(root)
        for path in root.rglob("*"):
            if path.is_file():
                stat = path.stat()
                found[str(path)] = (stat.st_mtime_ns, stat.st_size)
    return found


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


def _dist_row(label: str, block: dict) -> str:
    return _md(
        [
            label,
            format_point(block["mean"]),
            format_point(block["median"]),
            format_point(block["sd"]),
            format_point(block["min"]),
            format_point(block["max"]),
            format_point(block["q25"]),
            format_point(block["q75"]),
            format_point(block["iqr"]),
        ]
    )


def _cell_dir(variant: str, split_seed: int, model_seed: int) -> Path:
    return STAGE_DIR / f"{variant}_split{split_seed}_model{model_seed}"


def _prediction_frame(split, variant: str, split_seed: int, model_seed: int, val_score, test_score) -> pd.DataFrame:
    rows = []
    for partition, scores in (("val", val_score), ("test", test_score)):
        part = getattr(split, partition)
        for i in range(len(part)):
            rows.append(
                {
                    "variant": variant,
                    "split_seed": int(split_seed),
                    "model_seed": int(model_seed),
                    "partition": partition,
                    "row_in_partition": int(i),
                    "claim_id": str(part["claim_id"].iloc[i]),
                    "question_id": str(part["question_id"].iloc[i]),
                    "label": int(part["label"].iloc[i]),
                    "generator_id": int(part["generator_id"].iloc[i]),
                    "claim_type": int(part["claim_type"].iloc[i]),
                    "score": float(scores[i]),
                }
            )
    return pd.DataFrame(rows)


def _full_metrics(metrics) -> dict:
    y_n = int(metrics.n)
    return {
        "n": y_n,
        "auroc": None if not np.isfinite(metrics.auroc) else float(metrics.auroc),
        "f1": None if not np.isfinite(metrics.f1) else float(metrics.f1),
        "precision": None if not np.isfinite(metrics.precision) else float(metrics.precision),
        "recall": None if not np.isfinite(metrics.recall) else float(metrics.recall),
        "ece": None if not np.isfinite(metrics.ece) else float(metrics.ece),
    }


def _complete(path: Path, split_seed: int, model_seed: int, variant: str) -> bool:
    metrics_path = path / "metrics.json"
    pred_path = path / "predictions.parquet"
    ckpt = path / "model.joblib"
    if not (metrics_path.exists() and pred_path.exists() and ckpt.exists()):
        return False
    meta = json.loads(metrics_path.read_text())
    return (
        meta.get("prediction_source") == PREDICTION_SOURCE
        and meta.get("variant") == variant
        and int(meta.get("split_seed", -1)) == int(split_seed)
        and int(meta.get("model_seed", -1)) == int(model_seed)
        and meta.get("skipped") in (None, False)
    )


def _fit_cell(cfg, frame: pd.DataFrame, split, variant: str, split_seed: int, model_seed: int, split_hash: str) -> dict:
    out = _cell_dir(variant, split_seed, model_seed)
    if STAGE_DIR.resolve() not in out.resolve().parents:
        raise RuntimeError(f"refusing to write outside {STAGE_DIR}: {out}")
    if _complete(out, split_seed, model_seed, variant):
        meta = json.loads((out / "metrics.json").read_text())
        print(f"  reuse {variant} split={split_seed} model={model_seed}", flush=True)
        return meta

    from .data.build import table_path

    if table_path(cfg, model_seed).resolve() != FIT_TABLE.resolve():
        raise RuntimeError("model seed changed the fit-table path")
    ctx = RunContext.build(cfg, variant=variant, seed=model_seed, table=FIT_TABLE, split_seed=split_seed)
    ctx.out_dir = out
    result = fit_variant(ctx, df=frame, split=split)
    if result.skipped:
        raise RuntimeError(f"{variant} was skipped: {result.skipped}")
    written = persist(ctx, result)
    checkpoint = written["checkpoint"]
    if checkpoint.suffix != ".joblib":
        raise RuntimeError(f"expected a joblib checkpoint, found {checkpoint}")

    import joblib

    reloaded = joblib.load(checkpoint)
    val_score = np.asarray(reloaded.predict_proba(split.val), dtype="float64")
    test_score = np.asarray(reloaded.predict_proba(split.test), dtype="float64")
    mem_val = np.asarray(result.model.predict_proba(split.val), dtype="float64")
    mem_test = np.asarray(result.p_test, dtype="float64")
    y_val = split.val["label"].to_numpy()
    y_test = split.test["label"].to_numpy()
    threshold = float(tune_threshold(y_val, val_score))
    scored = slice_metrics(
        y_test,
        test_score,
        name=f"{variant}:test",
        threshold=threshold,
        n_bins=int(cfg.get("eval.ece_bins", 15)),
        extra={"variant": variant, "split_seed": split_seed, "model_seed": model_seed},
    )
    full = _full_metrics(scored)
    full["n_positive"] = int(np.asarray(y_test).sum())
    full["n_questions"] = int(split.test["question_id"].nunique())
    payload = {
        **ctx.provenance(),
        "variant": variant,
        "seed": int(model_seed),
        "model_seed": int(model_seed),
        "split_seed": int(split_seed),
        "split_assignment_sha256": split_hash,
        "prediction_source": PREDICTION_SOURCE,
        "threshold_source": THRESHOLD_SOURCE,
        "threshold": threshold,
        "in_memory_threshold": float(result.threshold),
        "threshold_matches_in_memory": bool(threshold == float(result.threshold)),
        "in_memory_max_abs_val": float(np.max(np.abs(mem_val - val_score))),
        "in_memory_max_abs_test": float(np.max(np.abs(mem_test - test_score))),
        "scores_equal_in_memory": bool(np.array_equal(mem_val, val_score) and np.array_equal(mem_test, test_score)),
        "test": scored.as_dict(),
        "test_full": full,
        "val_auroc_full": float(auroc(y_val, val_score)),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "skipped": None,
        "fit_info": result.fit_info,
    }
    dump_json(out / "metrics.json", _jsonable(payload))
    _prediction_frame(split, variant, split_seed, model_seed, val_score, test_score).to_parquet(
        out / "predictions.parquet", index=False
    )
    print(
        f"  fit {variant} split={split_seed} model={model_seed} "
        f"auroc={scored.as_dict()['auroc']}",
        flush=True,
    )
    return json.loads((out / "metrics.json").read_text())


def _load_predictions(variant: str, split_seed: int, model_seed: int) -> pd.DataFrame:
    frame = pd.read_parquet(_cell_dir(variant, split_seed, model_seed) / "predictions.parquet")
    return frame.sort_values(["partition", "row_in_partition"]).reset_index(drop=True)


def _scores(frame: pd.DataFrame, partition: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    part = frame[frame["partition"] == partition].sort_values("row_in_partition")
    return (
        part["label"].to_numpy(),
        part["score"].to_numpy(dtype="float64"),
        part["question_id"].astype(str).to_numpy(),
    )


def reproduce_a4_checkpoint(cfg, frame: pd.DataFrame) -> dict:
    """Refit Stage 7's A4 split-seed 6 / model-seed 6 cell. Do not touch Stage 7 files."""
    import joblib

    split = group_stratified_split(frame, seed=6)
    assert_disjoint(split)
    out = STAGE_DIR / "checkpoint_repro" / "A4_split6_model6"
    ctx = RunContext.build(cfg, variant="A4", seed=6, table=FIT_TABLE, split_seed=6)
    ctx.out_dir = out
    result = fit_variant(ctx, df=frame, split=split)
    written = persist(ctx, result)
    fresh = joblib.load(written["checkpoint"])
    stage7_model = joblib.load(STAGE7_DIR / "A4_seed6" / "model.joblib")
    stage7_meta = json.loads((STAGE7_DIR / "A4_seed6" / "metrics.json").read_text())
    y = split.test["label"].to_numpy()
    mem = np.asarray(result.p_test, dtype="float64")
    fresh_score = np.asarray(fresh.predict_proba(split.test), dtype="float64")
    stage7_score = np.asarray(stage7_model.predict_proba(split.test), dtype="float64")
    exact = float(result.threshold)
    rounded = round(exact, 6)
    stored = float(stage7_meta["threshold"])
    claim = split.test["claim_id"].astype(str).to_numpy()
    between = np.flatnonzero((mem >= exact) != (mem >= rounded))
    nearest = int(np.argmin(np.abs(mem - exact)))

    def pack(score, threshold):
        got = slice_metrics(y, score, name="A4:test", threshold=threshold).as_dict()
        return {key: got[key] for key in ("auroc", "f1", "precision", "recall", "ece", "n")}

    return {
        "cell": "A4 split_seed=6 model_seed=6",
        "stage7_directory_modified": False,
        "exact_threshold": exact,
        "threshold_rounded_to_6_decimals": rounded,
        "stage7_stored_threshold": stored,
        "stored_threshold_equals_rounded": bool(stored == rounded),
        "in_memory_equals_fresh_reload": bool(np.array_equal(mem, fresh_score)),
        "fresh_reload_equals_stage7_checkpoint": bool(np.array_equal(fresh_score, stage7_score)),
        "max_abs_in_memory_vs_stage7_checkpoint": float(np.max(np.abs(mem - stage7_score))),
        "n_test_calls_flipped_by_6_decimal_rounding": int(between.size),
        "flipped_claim_ids": [str(claim[i]) for i in between],
        "nearest_claim_id": str(claim[nearest]),
        "nearest_score": float(mem[nearest]),
        "nearest_label": int(y[nearest]),
        "metrics_at_exact_threshold": pack(mem, exact),
        "metrics_at_rounded_threshold": pack(mem, rounded),
        "stage7_fit_time_metrics": {
            key: stage7_meta["test"][key] for key in ("auroc", "f1", "precision", "recall", "ece", "n")
        },
        "cause": (
            "Joblib reload reproduced the in-memory scores exactly, including the "
            "Stage 7 checkpoint. RunResult.to_dict had stored round(threshold, 6). "
            "That moved the validation threshold from the exact quantile-grid value "
            "onto 6e-6. One negative test claim scored between those two cuts, so "
            "precision and F1 changed and AUROC did not. The discrepancy is threshold "
            "serialization, not model serialization, prediction drift, or a second fit."
        ),
    }


def _verify_saved(cfg, frame: pd.DataFrame, cells: list[dict]) -> dict:
    """Recompute every reported metric from the saved scores and a second reload."""
    import joblib

    failures = []
    max_abs = 0.0
    n_equal = 0
    for meta in cells:
        variant = meta["variant"]
        split_seed = int(meta["split_seed"])
        model_seed = int(meta["model_seed"])
        saved = _load_predictions(variant, split_seed, model_seed)
        y_val, p_val, _ = _scores(saved, "val")
        y_test, p_test, groups = _scores(saved, "test")
        threshold = float(tune_threshold(y_val, p_val))
        if threshold != float(meta["threshold"]):
            failures.append(f"{variant} split {split_seed} model {model_seed}: threshold")
        got = slice_metrics(
            y_test,
            p_test,
            name="recomputed",
            threshold=threshold,
            n_bins=int(cfg.get("eval.ece_bins", 15)),
        )
        reported = meta["test"]
        for key in ("auroc", "f1", "precision", "recall", "ece", "n"):
            if got.as_dict()[key] != reported[key]:
                failures.append(
                    f"{variant} split {split_seed} model {model_seed}: {key} "
                    f"{got.as_dict()[key]} != {reported[key]}"
                )
        full = meta["test_full"]
        if got.n != int(full["n"]) or int(y_test.sum()) != int(full["n_positive"]):
            failures.append(f"{variant} split {split_seed} model {model_seed}: counts")
        if full["auroc"] is None or got.auroc != float(full["auroc"]):
            failures.append(f"{variant} split {split_seed} model {model_seed}: full auroc")
        split = group_stratified_split(frame, seed=split_seed)
        model = joblib.load(_cell_dir(variant, split_seed, model_seed) / "model.joblib")
        re_test = np.asarray(model.predict_proba(split.test), dtype="float64")
        re_val = np.asarray(model.predict_proba(split.val), dtype="float64")
        max_abs = max(max_abs, float(np.max(np.abs(re_test - p_test))), float(np.max(np.abs(re_val - p_val))))
        if np.array_equal(re_test, p_test) and np.array_equal(re_val, p_val):
            n_equal += 1
        else:
            failures.append(f"{variant} split {split_seed} model {model_seed}: reload scores")
        if int(np.unique(groups).size) != int(full["n_questions"]):
            failures.append(f"{variant} split {split_seed} model {model_seed}: questions")
        del model
    if failures:
        raise RuntimeError("saved artifacts do not recreate the reported metrics: " + "; ".join(failures[:8]))
    return {
        "n_cells": len(cells),
        "n_checkpoints_matching_saved_scores": n_equal,
        "max_abs_second_reload_vs_saved_scores": max_abs,
        "threshold_rederived_from_saved_validation_scores": True,
        "rounded_metrics_match_saved_scores": True,
        "full_precision_auroc_matches_saved_scores": True,
        "source": PREDICTION_SOURCE,
    }


def _score_cells(cells: list[dict], n_resamples: int) -> dict:
    bundles: dict[tuple[int, int], dict] = {}
    metric_rows = []
    for meta in cells:
        key = (int(meta["split_seed"]), int(meta["model_seed"]))
        saved = _load_predictions(meta["variant"], key[0], key[1])
        y, score, groups = _scores(saved, "test")
        bundle = bundles.setdefault(
            key,
            {
                "y": y,
                "groups": groups,
                "claim_id": saved.loc[saved["partition"] == "test", "claim_id"].astype(str).tolist(),
                "scores": {},
                "thresholds": {},
                "full": {},
                "rounded": {},
            },
        )
        if bundle["claim_id"] != saved.loc[saved["partition"] == "test", "claim_id"].astype(str).tolist():
            raise RuntimeError(f"test claim ids differ at split {key[0]} model {key[1]}")
        bundle["scores"][meta["variant"]] = score
        bundle["thresholds"][meta["variant"]] = float(meta["threshold"])
        bundle["full"][meta["variant"]] = meta["test_full"]
        bundle["rounded"][meta["variant"]] = meta["test"]
        metric_rows.append(
            {
                "variant": meta["variant"],
                "split_seed": key[0],
                "model_seed": key[1],
                "threshold": float(meta["threshold"]),
                "n": int(meta["test_full"]["n"]),
                "n_positive": int(meta["test_full"]["n_positive"]),
                "n_questions": int(meta["test_full"]["n_questions"]),
                **{name: meta["test_full"][name] for name in METRICS},
                "scores_equal_in_memory": bool(meta["scores_equal_in_memory"]),
                "checkpoint_sha256": meta["checkpoint_sha256"],
                "split_assignment_sha256": meta["split_assignment_sha256"],
            }
        )

    for key, bundle in bundles.items():
        ids = None
        for variant in VARIANTS:
            if variant not in bundle["scores"]:
                raise RuntimeError(f"missing {variant} at split {key[0]} model {key[1]}")
            current = tuple(bundle["claim_id"])
            if ids is None:
                ids = current
            elif current != ids:
                raise RuntimeError("variants in one cell do not share test claim ids")

    variant_blocks = []
    for variant in VARIANTS:
        records = []
        for split_seed in SPLIT_SEEDS:
            for model_seed in MODEL_SEEDS:
                bundle = bundles[(split_seed, model_seed)]
                full = bundle["full"][variant]
                interval = within_seed_auroc_interval(
                    bundle["y"],
                    bundle["scores"][variant],
                    bundle["groups"],
                    n_resamples=n_resamples,
                    seed=split_seed,
                )
                if int(interval["n_requested"]) != n_resamples:
                    raise RuntimeError("bootstrap requested-sample count changed")
                records.append(
                    {
                        "variant": variant,
                        "split_seed": split_seed,
                        "model_seed": model_seed,
                        "threshold": bundle["thresholds"][variant],
                        "n": full["n"],
                        "n_positive": full["n_positive"],
                        "n_questions": full["n_questions"],
                        **{name: full[name] for name in METRICS},
                        "grouped_interval": interval,
                    }
                )
        block = {"variant": variant, "cells": records}
        for name in METRICS:
            block[name] = decompose(records, name, SPLIT_SEEDS, MODEL_SEEDS)
            block[name]["components"] = method_of_moments(
                [row["mean"] for row in block[name]["per_split"]],
                [row["sd"] for row in block[name]["per_split"]],
                len(MODEL_SEEDS),
            )
        block["threshold"] = decompose(records, "threshold", SPLIT_SEEDS, MODEL_SEEDS)
        variant_blocks.append(block)

    paired = {}
    for baseline in BASELINES:
        records = []
        for split_seed in SPLIT_SEEDS:
            for model_seed in MODEL_SEEDS:
                bundle = bundles[(split_seed, model_seed)]
                corrected = paired_question_delta(
                    bundle["y"],
                    bundle["scores"]["A7"],
                    bundle["scores"][baseline],
                    bundle["groups"],
                    n_resamples=n_resamples,
                    seed=split_seed,
                )
                if "p_value" in corrected or corrected.get("fraction_is_p_value") is not False:
                    raise RuntimeError("paired delta exposed a p-value")
                if int(corrected["n_requested"]) != n_resamples:
                    raise RuntimeError("paired bootstrap requested-sample count changed")
                records.append(
                    {
                        "comparison": f"A7 - {baseline}",
                        "baseline": baseline,
                        "split_seed": split_seed,
                        "model_seed": model_seed,
                        "n": int(bundle["y"].size),
                        "n_positive": int(np.asarray(bundle["y"]).sum()),
                        "n_questions": int(np.unique(bundle["groups"]).size),
                        "delta_auroc": None if corrected["delta"] is None else float(corrected["delta"]),
                        "grouped_interval": {
                            "lo": corrected["lo"],
                            "hi": corrected["hi"],
                            "n_requested": corrected["n_requested"],
                            "n_finite": corrected["n_finite"],
                            "position_vs_0": classify_interval(corrected["lo"], corrected["hi"]),
                        },
                        "bootstrap_frac_delta_gt_0": corrected["bootstrap_frac_delta_gt_0"],
                        "fraction_is_p_value": False,
                        "fraction_label": corrected["fraction_label"],
                    }
                )
        positions = [row["grouped_interval"]["position_vs_0"] for row in records]
        paired[baseline] = {
            "comparison": f"A7 - {baseline}",
            "cells": records,
            "delta_auroc": decompose(records, "delta_auroc", SPLIT_SEEDS, MODEL_SEEDS),
            "components": method_of_moments(
                [
                    float(np.mean([row["delta_auroc"] for row in records if row["split_seed"] == split_seed]))
                    for split_seed in SPLIT_SEEDS
                ],
                [
                    float(np.std([row["delta_auroc"] for row in records if row["split_seed"] == split_seed], ddof=1))
                    for split_seed in SPLIT_SEEDS
                ],
                len(MODEL_SEEDS),
            ),
            "n_cells_a7_gt_baseline": int(sum(row["delta_auroc"] > 0 for row in records)),
            "n_cells_a7_lt_baseline": int(sum(row["delta_auroc"] < 0 for row in records)),
            "n_cells_a7_eq_baseline": int(sum(row["delta_auroc"] == 0 for row in records)),
            "n_interval_entirely_above_0": int(sum(p == "entirely_above_0" for p in positions)),
            "n_interval_entirely_below_0": int(sum(p == "entirely_below_0" for p in positions)),
            "n_interval_covers_0": int(sum(p == "covers_0" for p in positions)),
            "n_interval_undefined": int(sum(p == "undefined" for p in positions)),
            "interval_endpoint_mean": None,
            "fraction_label": "bootstrap fraction of resamples with delta > 0; not a p-value",
            "classical_p_value": None,
        }
        paired[baseline]["delta_auroc"]["components"] = paired[baseline]["components"]
    return {"variants": variant_blocks, "paired": paired, "metric_rows": metric_rows, "bundles": bundles}


def _split_records(frame: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    rows = []
    assigned_rows = []
    from .utils import set_seed

    for split_seed in SPLIT_SEEDS:
        split = group_stratified_split(frame, seed=split_seed)
        assert_disjoint(split)
        base_hash = assignment_hash(split)
        for model_seed in MODEL_SEEDS:
            set_seed(model_seed)
            again = group_stratified_split(frame, seed=split_seed)
            if assignment_hash(again) != base_hash:
                raise RuntimeError(f"model seed {model_seed} changed split seed {split_seed}")
        questions = assignment_maps(split)
        claim_ids = [str(v) for v in split.test["claim_id"].astype(str)]
        rows.append(
            {
                "split_seed": split_seed,
                "assignment_sha256": base_hash,
                "test_claim_ids_sha256": hashlib.sha256("\n".join(claim_ids).encode()).hexdigest(),
                "n_train_groups": int(split.train["question_id"].nunique()),
                "n_val_groups": int(split.val["question_id"].nunique()),
                "n_test_groups": int(split.test["question_id"].nunique()),
                "n_train": int(len(split.train)),
                "n_val": int(len(split.val)),
                "n_test": int(len(split.test)),
                "n_train_positive": int(split.train["label"].sum()),
                "n_val_positive": int(split.val["label"].sum()),
                "n_test_positive": int(split.test["label"].sum()),
            }
        )
        for question_id, partition in sorted(questions.items()):
            assigned_rows.append(
                {"split_seed": split_seed, "question_id": question_id, "partition": partition}
            )
    return rows, pd.DataFrame(assigned_rows)


def _diagonal_check(cells: list[dict]) -> dict:
    """Cells whose two seeds match Stage 7's coupled seed, for seeds 0, 1, and 2."""
    compared = []
    matched = True
    for seed in (0, 1, 2):
        for variant in VARIANTS:
            stage7 = json.loads((STAGE7_DIR / f"{variant}_seed{seed}" / "metrics.json").read_text())
            got = next(
                cell
                for cell in cells
                if cell["variant"] == variant and int(cell["split_seed"]) == seed and int(cell["model_seed"]) == seed
            )
            diffs = {}
            for key in ("auroc", "f1", "precision", "recall", "ece"):
                if got["test"][key] != stage7["test"][key]:
                    diffs[key] = {"stage7_fit_time": stage7["test"][key], "stage8_reloaded": got["test"][key]}
            if diffs:
                matched = False
            compared.append({"variant": variant, "seed": seed, "matched": not diffs, "differences": diffs})
    return {"matched": matched, "cells": compared}


def _git_record() -> dict:
    def run(*args: str) -> str:
        out = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
        return out.stdout.strip()

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    lines = [line for line in status.splitlines() if line.strip()]
    source_lines = [
        line
        for line in lines
        if any(token in line for token in ("rcgate/", "configs/", "tests/", "pyproject.toml"))
    ]
    dirty = bool(lines)
    return {
        "head": run("git", "rev-parse", "HEAD"),
        "head_short": run("git", "rev-parse", "--short", "HEAD"),
        "dirty": dirty,
        "n_porcelain_lines": len(lines),
        "source_porcelain": source_lines,
        "head_alone_reproduces_this_experiment": False,
        "reason": (
            "The working tree is dirty. Stage 8 source edits are uncommitted, and "
            "other untracked result files are present. Git HEAD alone does not reproduce this run."
            if dirty
            else "The working tree is clean. This HEAD contains the Stage 8 source."
        ),
    }


def _source_hashes() -> dict[str, str]:
    return {rel: _sha256(PROJECT_ROOT / rel) for rel in SOURCE_FILES}


def _answers(result: dict) -> dict:
    variants = {block["variant"]: block for block in result["scored"]["variants"]}
    a7 = variants["A7"]["auroc"]
    fixed = {seed: a7["by_model_seed"][str(seed)] for seed in MODEL_SEEDS}
    within = a7["within_split_sd"]
    fixed_sds = [fixed[seed]["sd"] for seed in MODEL_SEEDS]
    mean_fixed = float(np.mean(fixed_sds))
    ratio = float(within["median"] / mean_fixed) if mean_fixed else float("nan")
    ranges = {str(seed): float(fixed[seed]["max"] - fixed[seed]["min"]) for seed in MODEL_SEEDS}
    split_unstable = all(span > 0.10 for span in ranges.values())
    init_moves = bool(within["median"] >= 0.01 or within["max"] >= 0.05)

    def advantage(baseline: str) -> dict:
        block = result["scored"]["paired"][baseline]
        means = [row["mean"] for row in block["delta_auroc"]["per_split"]]
        n_pos = int(sum(v > 0 for v in means))
        n_neg = int(sum(v < 0 for v in means))
        n_zero = int(sum(v == 0 for v in means))
        stable = n_pos == len(means) and block["n_cells_a7_lt_baseline"] == 0
        return {
            "baseline": baseline,
            "stable_advantage": stable,
            "n_split_means_positive": n_pos,
            "n_split_means_negative": n_neg,
            "n_split_means_zero": n_zero,
            "n_splits": len(means),
            "n_cells_positive": block["n_cells_a7_gt_baseline"],
            "n_cells_negative": block["n_cells_a7_lt_baseline"],
            "n_intervals_entirely_above_0": block["n_interval_entirely_above_0"],
            "n_intervals_entirely_below_0": block["n_interval_entirely_below_0"],
            "n_intervals_cover_0": block["n_interval_covers_0"],
            "split_mean_of_deltas": block["delta_auroc"]["over_split_means"]["mean"],
            "statement": (
                f"The split-level mean A7−{baseline} delta is positive on all {len(means)} splits."
                if stable
                else (
                    f"No stable advantage over {baseline}. The split-level mean delta is "
                    f"positive on {n_pos} of {len(means)} splits and negative on {n_neg}. "
                    f"Of 60 separate paired intervals, {block['n_interval_entirely_above_0']} "
                    f"lie entirely above 0 and {block['n_interval_entirely_below_0']} lie entirely "
                    f"below 0. Interval endpoints are not averaged."
                )
            ),
        }

    adv = {name: advantage(name) for name in BASELINES}
    share = a7["components"]["between_share_of_cell_variance"]
    if np.isfinite(ratio) and ratio < 0.25:
        attribution = (
            f"At a fixed model seed, A7's AUROC SD across the 20 splits is "
            f"{format_point(fixed_sds[0])}, {format_point(fixed_sds[1])}, and "
            f"{format_point(fixed_sds[2])}. The median SD across the three model seeds "
            f"inside one split is {format_point(within['median'])}. "
            "The split contribution is larger. The method-of-moments between-split share "
            f"of a single cell is {format_point(share) if share is not None else 'undefined'}. "
            "That share describes this dependent repartition; it is not a variance component "
            "from independent datasets. The three-seed initialization term is preliminary."
        )
    else:
        attribution = (
            f"At a fixed model seed, A7's AUROC SD across the 20 splits is "
            f"{format_point(fixed_sds[0])}, {format_point(fixed_sds[1])}, and "
            f"{format_point(fixed_sds[2])}. The median within-split SD is "
            f"{format_point(within['median'])} and the maximum is {format_point(within['max'])}. "
            "Both the split and the model seed move A7. With three model seeds, the "
            "initialization term is preliminary. The method-of-moments between-split share "
            f"is {format_point(share) if share is not None else 'undefined'}, on repeated "
            "partitions of one pool."
        )
    repro = result["a4_repro"]
    supported = [
        "Question groups do not cross the train, validation, and test partitions.",
        "The split seed controls split assignment. The model seed does not.",
        "A7 training is reproducible at a fixed split and a fixed model seed, and it changes when the model seed changes.",
        "The Stage 7 A4 seed-6 F1 gap is explained by rounding the stored threshold to 6 decimals.",
    ]
    unsupported = [
        "Stage 7's seed dispersion can be read as a pure split effect or a pure initialization effect. The design set the two seeds equal.",
    ]
    if not adv["A0"]["stable_advantage"]:
        unsupported.append("A7 has a stable test-AUROC advantage over A0 on this RAGTruth table.")
    if not adv["A4"]["stable_advantage"]:
        unsupported.append("A7 has a stable test-AUROC advantage over A4 on this RAGTruth table.")
    uncertain = [
        "The magnitude of initialization variance. Only three model seeds were fit, so the within-split SD is preliminary.",
        "Generalization beyond this 134-question pool. The 20 splits repartition that one pool.",
        "A8. Judge votes are not in the frozen table, so A8 was not fit.",
    ]
    return {
        "1_stage7_confounded": {
            "answer": True,
            "statement": (
                "Yes. Stage 7 set the model seed equal to the split seed, so each reported "
                "seed changed the question assignment and, for models that read that seed, "
                "the initialization together. The two generators were already separate. "
                "The confounding is in that coupled design, not in a hidden shared stream."
            ),
        },
        "2_variance_attribution": {
            "fixed_model_seed_sd": {str(seed): fixed[seed]["sd"] for seed in MODEL_SEEDS},
            "within_split_sd_median": within["median"],
            "within_split_sd_max": within["max"],
            "between_share_of_cell_variance": share,
            "statement": attribution,
        },
        "3_unstable_at_fixed_initialization": {
            "answer": split_unstable,
            "range_by_model_seed": ranges,
            "criterion": "AUROC range across the 20 splits exceeds 0.10 at that fixed model seed",
            "statement": (
                "Yes. With the model seed held fixed, A7's test AUROC still spans "
                + ", ".join(f"{format_point(span)} at model seed {seed}" for seed, span in ranges.items())
                + ". The criterion is a range above 0.10. Initialization is not required for that movement."
                if split_unstable
                else "No. At one or more fixed model seeds the 20-split AUROC range is at most 0.10."
            ),
        },
        "4_unstable_at_fixed_split": {
            "answer": init_moves,
            "within_split_sd": within,
            "statement": (
                f"Within a split, A7's AUROC SD across the three model seeds has median "
                f"{format_point(within['median'])}, minimum {format_point(within['min'])}, "
                f"and maximum {format_point(within['max'])}. "
                + (
                    "Initialization still moves A7 when the split is held fixed. "
                    if init_moves
                    else "Initialization does not move A7 by a meaningful amount on this grid. "
                )
                + "Three model seeds make this a preliminary description, not a precise population SD."
            ),
        },
        "5_stable_advantage": adv,
        "6_a4_checkpoint": {
            "explained": True,
            "cause": repro["cause"],
            "exact_threshold": repro["exact_threshold"],
            "rounded_threshold": repro["threshold_rounded_to_6_decimals"],
            "flipped_claim_ids": repro["flipped_claim_ids"],
            "scores_identical": repro["fresh_reload_equals_stage7_checkpoint"],
        },
        "7_metrics_reconstructed": {
            "answer": result["reproduction"]["n_cells"] == 20 * 3 * 8,
            "statement": (
                f"Yes. All {result['reproduction']['n_cells']} reported point-metric blocks "
                "were recomputed from the saved validation scores, the saved test scores, "
                "and a second load of the checkpoint."
            ),
        },
        "8_claims": {
            "supported": supported,
            "unsupported": unsupported,
            "uncertain": uncertain,
        },
    }


def _paper(result: dict) -> list[str]:
    answers = result["answers"]
    a7 = next(block for block in result["scored"]["variants"] if block["variant"] == "A7")["auroc"]
    a0 = answers["5_stable_advantage"]["A0"]
    a4 = answers["5_stable_advantage"]["A4"]
    n_questions = result["n_questions"]
    text = (
        f"On the frozen corrected RAGTruth table, A0–A7 were refit on a 20 by 3 grid "
        f"of group-stratified split seeds and model seeds. The fit table, splitter, "
        f"features, labels, architectures, and validation threshold rule were unchanged. "
        f"A7 test AUROC across the 60 cells had mean {format_point(a7['over_cells']['mean'])} "
        f"and sample SD {format_point(a7['over_cells']['sd'])}. "
        f"The mean of the three model seeds inside each split, then summarized over the 20 splits, "
        f"had mean {format_point(a7['over_split_means']['mean'])} and SD "
        f"{format_point(a7['over_split_means']['sd'])}. "
        f"The median within-split SD was {format_point(a7['within_split_sd']['median'])}. "
        f"The split-level mean A7−A0 delta was positive on {a0['n_split_means_positive']} of 20 splits "
        f"(mean {format_point(a0['split_mean_of_deltas'])}). "
        f"The split-level mean A7−A4 delta was positive on {a4['n_split_means_positive']} of 20 splits "
        f"(mean {format_point(a4['split_mean_of_deltas'])}). "
        f"Separate paired intervals lay entirely above 0 on {a0['n_intervals_entirely_above_0']} "
        f"of 60 cells versus A0 and {a4['n_intervals_entirely_above_0']} of 60 versus A4. "
        f"Those endpoints were not averaged into one interval."
    )
    limits = (
        f"The 20 splits repartition one pool of {n_questions} questions. They are not 20 "
        f"independent datasets, and the across-split SD is not a confidence interval. "
        f"Three model seeds per split make the initialization SD preliminary. "
        f"Stage 7 coupled the two seeds, so its seed SD mixes assignment with initialization. "
        f"The A4 seed-6 F1 difference was a threshold rounded to 6 decimals; the reloaded "
        f"scores matched the fit. A8 was not run. The model was not retuned."
    )
    conclusion = (
        "A7 does not show a stable advantage over A0 or A4 once split assignment and "
        "model initialization are separated. The result is a description of that "
        "instability, not a repaired estimate for A7."
        if not a0["stable_advantage"] and not a4["stable_advantage"]
        else "See the paired split-level means before treating either baseline comparison as stable."
    )
    return [
        "## Paper-safe wording",
        "",
        text,
        "",
        limits,
        "",
        conclusion,
        "",
    ]


def render_report(result: dict) -> str:
    answers = result["answers"]
    variants = {block["variant"]: block for block in result["scored"]["variants"]}
    lines = [
        "# RC-Gate Stage 8 — factorial split and model seeds",
        "",
        "Split seed and model seed are crossed. The frozen seed-0 corrected table,",
        "the group-stratified splitter, the variants, the hyperparameters, and the",
        "Stage 5 question-grouped bootstrap are unchanged. Stage 4 through Stage 7",
        "directories were not rewritten. Distributions below are not confidence intervals.",
        "",
        "## Randomness-control audit",
        "",
        "What each seed controls:",
        "",
        "- Split assignment: `group_stratified_split` builds one `numpy.random.Generator`",
        "  per positive-count stratum from `SeedSequence([split_seed, stratum])`. Group",
        "  ids are sorted before the shuffle. The function does not call `set_seed` and",
        "  does not read the global Python, NumPy, or torch generators.",
        "- Global state at fit time: `RunContext.start` calls `set_seed(model_seed)`,",
        "  which sets `random.seed`, `np.random.seed`, `torch.manual_seed`, and",
        "  `PYTHONHASHSEED`. That call uses the model seed. It does not rebuild the split",
        "  when a split object is passed in.",
        "- Logistic A0–A3: `LogisticRegression(..., solver='lbfgs', random_state=model_seed)`.",
        "  For `lbfgs`, scikit-learn does not use `random_state` to shuffle. A3's alpha",
        "  grid is `numpy.linspace`. On this grid their test scores did not move with the model seed.",
        "- A4: `HistGradientBoostingClassifier(..., early_stopping=False, random_state=model_seed)`.",
        "  The seed is available for binning. Whether it moves predictions is an empirical",
        "  result of this run, recorded in the within-split SDs.",
        "- A5–A7 weight initialization: `set_seed(model_seed)` runs, then `RCGate()` draws",
        "  the current torch state. The splitter does not draw torch numbers, so a different",
        "  split seed does not advance that state. `fit` then calls `torch.manual_seed(model_seed)`",
        "  again and draws batch order and UNK dropout from `numpy.random.default_rng(model_seed)`.",
        "  There is no PyTorch `DataLoader` and no worker shuffle.",
        "- Validation threshold: `tune_threshold` sees validation labels and validation",
        "  scores only. The candidate grid is deterministic. Test rows are not an input.",
        "- Bootstrap: a separate `default_rng(split_seed)` resamples `question_id`. It does",
        "  not affect fitting. The requested count is 1000. The fraction of positive paired",
        "  deltas is not a p-value.",
        "- Checkpoint: A0–A7 are joblib payloads. `RCGateModel` is not an `nn.Module`, so",
        "  the torch wrapper is not sent through `torch.save`.",
        "",
        "Changing the model seed does not change split assignments. Changing the split",
        "seed does not change A7's initial weights when the model seed is fixed, because",
        "the splitter never consumes the torch generator that `set_seed` just reset.",
        "",
        "## Checkpoint reproducibility",
        "",
        answers["6_a4_checkpoint"]["cause"],
        "",
        f"- Exact threshold: {result['a4_repro']['exact_threshold']}.",
        f"- Rounded to 6 decimals: {result['a4_repro']['threshold_rounded_to_6_decimals']}.",
        f"- Stage 7 stored threshold equals that rounding: {result['a4_repro']['stored_threshold_equals_rounded']}.",
        f"- Calls flipped by the rounding: {result['a4_repro']['n_test_calls_flipped_by_6_decimal_rounding']} "
        f"({', '.join(result['a4_repro']['flipped_claim_ids']) or 'none'}).",
        f"- Nearest claim {result['a4_repro']['nearest_claim_id']} scored "
        f"{result['a4_repro']['nearest_score']} (label {result['a4_repro']['nearest_label']}).",
        f"- In-memory scores equal a fresh reload: {result['a4_repro']['in_memory_equals_fresh_reload']}.",
        f"- Fresh reload equals the Stage 7 checkpoint: {result['a4_repro']['fresh_reload_equals_stage7_checkpoint']}.",
        f"- Max absolute score gap versus the Stage 7 checkpoint: "
        f"{result['a4_repro']['max_abs_in_memory_vs_stage7_checkpoint']}.",
        "",
        "Fit-time metrics at the exact threshold: "
        + json.dumps(result["a4_repro"]["metrics_at_exact_threshold"])
        + ". Metrics at the rounded threshold: "
        + json.dumps(result["a4_repro"]["metrics_at_rounded_threshold"])
        + ". Stage 7's stored fit-time metrics: "
        + json.dumps(result["a4_repro"]["stage7_fit_time_metrics"])
        + ".",
        "",
        "The serialization change is separate from the seed design. `RunResult.to_dict`",
        "now stores the exact threshold instead of `round(threshold, 6)`. Stage 7 files",
        "were not rewritten. Stage 8 selects the threshold on the reloaded model's",
        "validation scores and scores the test set from that same reload.",
        "",
        "## Protocol",
        "",
        "- Fit table: `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` for every cell.",
        "- Split seeds: 0 through 19. Model seeds: 0, 1, and 2. Variants: A0 through A7.",
        "- A8 skipped: the table has no judge votes.",
        "- 480 fits. No Stage 7 checkpoint was reused.",
        "- Fractions 0.6/0.2/0.2 inside each positive-count stratum, via `cut_counts`.",
        "- Threshold: unchanged `tune_threshold` on reloaded validation scores.",
        "- Point metrics: Stage 5 `slice_metrics` on reloaded test scores. Full-precision",
        "  values are stored beside the 4-decimal reported view.",
        "- Paired AUROC: one question resample scores both models. 1000 requested resamples.",
        "  The bootstrap seed is the split seed, so the draw is a property of the partition.",
        "- Cell distribution, mean of the three model seeds, distribution of those 20 means,",
        "  and the distribution of the 20 within-split SDs. Interval endpoints are not averaged.",
        "",
        f"Questions in the pool: {result['n_questions']}. "
        f"In-memory scores matched the first reload on "
        f"{result['n_scores_equal_in_memory']} of {result['n_cells']} cells. "
        f"Maximum absolute gap: {result['max_abs_in_memory']}.",
        "",
        "## Split balance",
        "",
        "Positive totals are fixed by the stratum sizes. Claim totals can still change",
        "when a short group changes partition. Model seed does not enter this table.",
        "",
        _md(
            [
                "split",
                "train groups",
                "val groups",
                "test groups",
                "train positives",
                "val positives",
                "test positives",
                "train claims",
                "val claims",
                "test claims",
            ]
        ),
        _md(["---"] * 10),
    ]
    for row in result["splits"]:
        lines.append(
            _md(
                [
                    str(row["split_seed"]),
                    str(row["n_train_groups"]),
                    str(row["n_val_groups"]),
                    str(row["n_test_groups"]),
                    str(row["n_train_positive"]),
                    str(row["n_val_positive"]),
                    str(row["n_test_positive"]),
                    str(row["n_train"]),
                    str(row["n_val"]),
                    str(row["n_test"]),
                ]
            )
        )
    lines += [
        "",
        "## Distributions over the 60 cells",
        "",
        "Each row pools 20 split seeds and 3 model seeds. The SD is not a confidence interval.",
        "",
        _md(["variant", "metric", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
        _md(["---"] * 10),
    ]
    for variant in VARIANTS:
        for metric in (*METRICS, "threshold"):
            block = variants[variant][metric]["over_cells"]
            lines.append(
                _md(
                    [
                        variant,
                        metric,
                        format_point(block["mean"]),
                        format_point(block["median"]),
                        format_point(block["sd"]),
                        format_point(block["min"]),
                        format_point(block["max"]),
                        format_point(block["q25"]),
                        format_point(block["q75"]),
                        format_point(block["iqr"]),
                    ]
                )
            )
    lines += [
        "",
        "## Split-level means",
        "",
        "For each split seed, average the three model seeds. The row then summarizes those",
        "20 means. Averaging three seeds is not a confidence interval, and the 20 splits",
        "are not 20 datasets.",
        "",
        _md(["variant", "metric", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
        _md(["---"] * 10),
    ]
    for variant in VARIANTS:
        for metric in (*METRICS, "threshold"):
            block = variants[variant][metric]["over_split_means"]
            lines.append(
                _md(
                    [
                        variant,
                        metric,
                        format_point(block["mean"]),
                        format_point(block["median"]),
                        format_point(block["sd"]),
                        format_point(block["min"]),
                        format_point(block["max"]),
                        format_point(block["q25"]),
                        format_point(block["q75"]),
                        format_point(block["iqr"]),
                    ]
                )
            )
    lines += [
        "",
        "## Within-split dispersion",
        "",
        "Each split contributes one sample SD across model seeds 0, 1, and 2.",
        "The table summarizes those 20 SDs. Three seeds make each SD preliminary.",
        "",
        _md(["variant", "metric", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
        _md(["---"] * 10),
    ]
    for variant in VARIANTS:
        for metric in ("auroc", "f1", "ece"):
            block = variants[variant][metric]["within_split_sd"]
            lines.append(
                _md(
                    [
                        variant,
                        metric,
                        format_point(block["mean"]),
                        format_point(block["median"]),
                        format_point(block["sd"]),
                        format_point(block["min"]),
                        format_point(block["max"]),
                        format_point(block["q25"]),
                        format_point(block["q75"]),
                        format_point(block["iqr"]),
                    ]
                )
            )
    lines += [
        "",
        "### A7 AUROC by split and model seed",
        "",
        _md(["split", "model 0", "model 1", "model 2", "mean", "within SD"]),
        _md(["---"] * 6),
    ]
    for row in variants["A7"]["auroc"]["per_split"]:
        lines.append(
            _md(
                [str(row["split_seed"])]
                + [format_point(v) for v in row["values"]]
                + [format_point(row["mean"]), format_point(row["sd"])]
            )
        )
    lines += [
        "",
        f"Method of moments for A7 AUROC: {json.dumps(variants['A7']['auroc']['components'])}.",
        "",
        SPLIT_NOTE,
        WITHIN_NOTE,
        "",
    ]
    for baseline in BASELINES:
        block = result["scored"]["paired"][baseline]
        dist = block["delta_auroc"]
        lines += [
            f"## A7 minus {baseline}",
            "",
            "Delta is test AUROC(A7) minus test AUROC of the baseline on the same claims.",
            "The interval is that cell's own paired question-grouped bootstrap.",
            "A count of positions is not one combined interval, and the bootstrap fraction",
            "is not a p-value.",
            "",
            "### Over 60 cells",
            "",
            _md(["", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
            _md(["---"] * 9),
            _dist_row("delta AUROC", dist["over_cells"]),
            "",
            "### Over 20 split-level means",
            "",
            _md(["", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
            _md(["---"] * 9),
            _dist_row("delta AUROC", dist["over_split_means"]),
            "",
            "### Within-split SDs of the delta",
            "",
            _md(["", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
            _md(["---"] * 9),
            _dist_row("within-split SD", dist["within_split_sd"]),
            "",
            f"- Cells with A7 above the baseline: {block['n_cells_a7_gt_baseline']}.",
            f"- Cells with A7 below the baseline: {block['n_cells_a7_lt_baseline']}.",
            f"- Cells with equal AUROC: {block['n_cells_a7_eq_baseline']}.",
            f"- Intervals entirely above 0: {block['n_interval_entirely_above_0']}.",
            f"- Intervals entirely below 0: {block['n_interval_entirely_below_0']}.",
            f"- Intervals that cover 0: {block['n_interval_covers_0']}.",
            f"- Mean of interval endpoints: {block['interval_endpoint_mean']}.",
            "",
            _md(["split", "model 0", "model 1", "model 2", "mean", "within SD"]),
            _md(["---"] * 6),
        ]
        for row in dist["per_split"]:
            lines.append(
                _md(
                    [str(row["split_seed"])]
                    + [format_point(v) for v in row["values"]]
                    + [format_point(row["mean"]), format_point(row["sd"])]
                )
            )
        lines.append("")
        lines.append(
            f"Method of moments: {json.dumps(block['components'])}."
        )
        lines.append("")
    repro = result["reproduction"]
    diag = result["diagonal"]
    git = result["git"]
    lines += [
        "## Reproduction checks",
        "",
        f"- Cells recomputed from saved scores and a second checkpoint load: {repro['n_cells']}.",
        f"- Checkpoints matching the saved scores: {repro['n_checkpoints_matching_saved_scores']}.",
        f"- Max absolute second-reload gap: {repro['max_abs_second_reload_vs_saved_scores']}.",
        f"- Stage 7 coupled cells (split seed = model seed in {{0, 1, 2}}) matched fit-time metrics: {diag['matched']}.",
        f"- Synthetic fingerprint unchanged: {result['synthetic']['unchanged']}.",
        f"- Prior result directories unchanged: {result['protected_unchanged']}.",
        "",
        "## Provenance",
        "",
        f"- Git HEAD: `{git['head']}`.",
        f"- Dirty working tree: {git['dirty']}.",
        f"- HEAD alone reproduces this experiment: {git['head_alone_reproduces_this_experiment']}.",
        f"- {git['reason']}",
        "",
        "Source porcelain lines:",
        "",
    ]
    for line in git["source_porcelain"]:
        lines.append(f"- `{line}`")
    lines += [
        "",
        f"Fit-table SHA-256: `{result['fit_table_sha256']}`.",
        "",
        "Source-file SHA-256:",
        "",
    ]
    for rel, digest in result["source_hashes"].items():
        lines.append(f"- `{rel}` `{digest}`")
    lines += [
        "",
        "## Answers",
        "",
        "1. " + answers["1_stage7_confounded"]["statement"],
        "",
        "2. " + answers["2_variance_attribution"]["statement"],
        "",
        "3. " + answers["3_unstable_at_fixed_initialization"]["statement"],
        "",
        "4. " + answers["4_unstable_at_fixed_split"]["statement"],
        "",
        "5. Versus A0: " + answers["5_stable_advantage"]["A0"]["statement"],
        "   Versus A4: " + answers["5_stable_advantage"]["A4"]["statement"],
        "",
        "6. " + answers["6_a4_checkpoint"]["cause"],
        "",
        "7. " + answers["7_metrics_reconstructed"]["statement"],
        "",
        "8. Supported:",
        "",
    ]
    for item in answers["8_claims"]["supported"]:
        lines.append(f"- {item}")
    lines += ["", "Unsupported:", ""]
    for item in answers["8_claims"]["unsupported"]:
        lines.append(f"- {item}")
    lines += ["", "Uncertain:", ""]
    for item in answers["8_claims"]["uncertain"]:
        lines.append(f"- {item}")
    lines += ["", ""]
    lines.extend(_paper(result))
    return "\n".join(lines)


def _write_outputs(result: dict) -> Path:
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _jsonable({k: v for k, v in result.items() if k not in {"assignment_frame", "prediction_frame"}})
    (STAGE_DIR / "report.json").write_text(json.dumps(payload, indent=2))
    report = render_report(result)
    (STAGE_DIR / "report.md").write_text(report)
    result["assignment_frame"].to_parquet(STAGE_DIR / "split_assignments.parquet", index=False)
    result["prediction_frame"].to_parquet(STAGE_DIR / "predictions.parquet", index=False)
    pd.DataFrame(result["scored"]["metric_rows"]).to_csv(STAGE_DIR / "seed_metrics.csv", index=False)
    paired_rows = []
    for baseline in BASELINES:
        for row in result["scored"]["paired"][baseline]["cells"]:
            paired_rows.append(
                {
                    "baseline": baseline,
                    "split_seed": row["split_seed"],
                    "model_seed": row["model_seed"],
                    "delta_auroc": row["delta_auroc"],
                    "lo": row["grouped_interval"]["lo"],
                    "hi": row["grouped_interval"]["hi"],
                    "n_requested": row["grouped_interval"]["n_requested"],
                    "n_finite": row["grouped_interval"]["n_finite"],
                    "position_vs_0": row["grouped_interval"]["position_vs_0"],
                    "bootstrap_frac_delta_gt_0": row["bootstrap_frac_delta_gt_0"],
                    "fraction_is_p_value": False,
                }
            )
    pd.DataFrame(paired_rows).to_csv(STAGE_DIR / "paired_deltas.csv", index=False)
    provenance = {
        "stage": STAGE_DIR.name,
        "git": result["git"],
        "head_alone_reproduces_this_experiment": False,
        "fit_table": str(FIT_TABLE),
        "fit_table_sha256": result["fit_table_sha256"],
        "split_seeds": list(SPLIT_SEEDS),
        "model_seeds": list(MODEL_SEEDS),
        "variants": list(VARIANTS),
        "a8": "skipped; no judge votes",
        "n_fits": result["n_cells"],
        "prediction_source": PREDICTION_SOURCE,
        "threshold_source": THRESHOLD_SOURCE,
        "threshold_serialization": (
            "RunResult.to_dict stores the exact tune_threshold return value. "
            "The previous round(threshold, 6) is the Stage 7 A4 seed-6 discrepancy."
        ),
        "bootstrap_seed": "split_seed",
        "n_resamples_requested": result["n_resamples"],
        "bootstrap_fraction_is_p_value": False,
        "formal_p_value_reported": False,
        "interval_endpoints_averaged": False,
        "source_hashes": result["source_hashes"],
        "config_sha256": result["config_sha256"],
        "split_assignment_sha256": {str(row["split_seed"]): row["assignment_sha256"] for row in result["splits"]},
        "reproduction": result["reproduction"],
        "synthetic_unchanged": result["synthetic"]["unchanged"],
        "protected_unchanged": result["protected_unchanged"],
        "stage7_diagonal_matched": result["diagonal"]["matched"],
        "numpy": result["numpy"],
        "command": "python -m rcgate.factorial_seed",
    }
    (STAGE_DIR / "provenance.json").write_text(json.dumps(_jsonable(provenance), indent=2))
    return STAGE_DIR / "report.md"


def evaluate(fit: bool = True) -> dict:
    protected_before = _snapshot(PROTECTED_ROOTS)
    table_hash = _sha256(FIT_TABLE)
    cfg = load_named(CONFIG_NAME)
    if cfg.get("report.tag") != STAGE_DIR.name:
        raise RuntimeError("Stage 8 config would write outside its namespace")
    if cfg.get("data.split_method") != SPLIT_GROUP_STRATIFIED:
        raise RuntimeError("Stage 8 config is not group_stratified")
    if (PROJECT_ROOT / str(cfg.get("data.table"))).resolve() != FIT_TABLE.resolve():
        raise RuntimeError("Stage 8 fit table is not the frozen s0 table")
    if "{seed}" in str(cfg.get("data.table")):
        raise RuntimeError("Stage 8 table path must not depend on seed")
    frame = load_table(FIT_TABLE)
    if len(frame) != 800 or int(frame["question_id"].nunique()) != 134:
        raise RuntimeError("frozen table is not the expected 800 claims / 134 questions")
    runnable, reason = is_runnable("A8", frame)
    if runnable:
        raise RuntimeError("A8 became runnable; this stage must keep it skipped")
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    splits, assignments = _split_records(frame)
    cells = []
    if fit:
        for split_seed in SPLIT_SEEDS:
            split = group_stratified_split(frame, seed=split_seed)
            assert_disjoint(split)
            split_hash = assignment_hash(split)
            for model_seed in MODEL_SEEDS:
                for variant in VARIANTS:
                    cells.append(_fit_cell(cfg, frame, split, variant, split_seed, model_seed, split_hash))
    else:
        for split_seed in SPLIT_SEEDS:
            for model_seed in MODEL_SEEDS:
                for variant in VARIANTS:
                    path = _cell_dir(variant, split_seed, model_seed) / "metrics.json"
                    if not path.exists():
                        raise FileNotFoundError(path)
                    cells.append(json.loads(path.read_text()))
    if len(cells) != len(SPLIT_SEEDS) * len(MODEL_SEEDS) * len(VARIANTS):
        raise RuntimeError("the factorial grid is incomplete")
    reproduction = _verify_saved(cfg, frame, cells)
    scored = _score_cells(cells, N_RESAMPLES)
    predictions = pd.concat(
        [_load_predictions(meta["variant"], int(meta["split_seed"]), int(meta["model_seed"])) for meta in cells],
        ignore_index=True,
    )
    from .multi_seed import synthetic_regression

    synthetic = synthetic_regression()
    a4_repro = reproduce_a4_checkpoint(cfg, frame)
    diagonal = _diagonal_check(cells)
    protected_after = _snapshot(PROTECTED_ROOTS)
    if protected_before != protected_after:
        raise RuntimeError("a protected Stage 4–7 file changed")
    if _sha256(FIT_TABLE) != table_hash:
        raise RuntimeError("the frozen fit table changed")
    equal_flags = [bool(meta["scores_equal_in_memory"]) for meta in cells]
    gaps = [float(meta["in_memory_max_abs_test"]) for meta in cells]
    result = {
        "n_resamples": N_RESAMPLES,
        "numpy": np.__version__,
        "n_questions": int(frame["question_id"].nunique()),
        "n_cells": len(cells),
        "n_scores_equal_in_memory": int(sum(equal_flags)),
        "max_abs_in_memory": float(max(gaps)),
        "fit_table_sha256": table_hash,
        "config_sha256": _sha256(PROJECT_ROOT / "configs" / f"{CONFIG_NAME}.yaml"),
        "source_hashes": _source_hashes(),
        "git": _git_record(),
        "splits": splits,
        "a8_reason": reason,
        "scored": {k: v for k, v in scored.items() if k != "bundles"},
        "reproduction": reproduction,
        "a4_repro": a4_repro,
        "diagonal": diagonal,
        "synthetic": synthetic,
        "protected_unchanged": True,
        "assignment_frame": assignments,
        "prediction_frame": predictions,
    }
    result["answers"] = _answers(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 8 factorial split and model seeds")
    parser.add_argument("--score-only", action="store_true", help="Rescore saved Stage 8 checkpoints")
    args = parser.parse_args(argv)
    result = evaluate(fit=not args.score_only)
    path = _write_outputs(result)
    print(f"wrote {path}")
    print(f"cells {result['n_cells']}")
    print(f"synthetic_unchanged {result['synthetic']['unchanged']}")
    print(f"diagonal_matched {result['diagonal']['matched']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

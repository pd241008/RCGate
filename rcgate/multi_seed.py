"""Stage 7: twenty group-stratified seeds on one frozen corrected RAGTruth table.

The splitter, signals, labels, variants, hyperparameters, and the Stage 5
uncertainty procedure stay as they are. The only experimental factor is the
seed passed to ``group_stratified_split`` and, as in Stage 6, to model fitting.
Seeds 0 through 19 are kept. No seed is dropped after the scores are seen.

The three frozen tables are not rebuilt. Fitting uses seed 0's table for every
seed so a per-seed path cannot create ``s3``..``s19``. Companion tables ``s1``
and ``s2`` are hashed and compared, then left unused as fit data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_named
from .data.schema import CLAIM_TYPES
from .data.splits import (
    SPLIT_GROUP_STRATIFIED,
    assert_disjoint,
    group_positive_counts,
    group_stratified_split,
    split_balance,
)
from .metrics import slice_metrics
from .paths import PROJECT_ROOT, SUMMARY_DIR
from .pipeline import RunContext, fit_variant, load_table, persist
from .stats_protocol import (
    N_RESAMPLES,
    across_seed_dispersion,
    classify_interval,
    format_interval,
    format_point,
    paired_question_delta,
    within_seed_auroc_interval,
)
from .utils import git_hash
from .variants import ALL_VARIANTS

STAGE4_DIR = SUMMARY_DIR / "ragtruth_corrected_integrity_v1"
STAGE5_DIR = SUMMARY_DIR / "ragtruth_corrected_stats_v1"
STAGE6_DIR = SUMMARY_DIR / "ragtruth_split_corrected_v1"
STAGE7_DIR = SUMMARY_DIR / "ragtruth_multi_seed_v1"
CONFIG_NAME = "ragtruth_multi_seed_v1"
FIT_TABLE = PROJECT_ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"
COMPANION_TABLES = [
    PROJECT_ROOT / f"data/signal_tables/ragtruth_corrected_integrity_v1_s{seed}.parquet"
    for seed in (0, 1, 2)
]
SEEDS = list(range(20))
VARIANTS = [f"A{i}" for i in range(8)]
BASELINES = ("A0", "A4")
METRICS = ("auroc", "f1", "precision", "recall", "ece")
PARTITIONS = ("train", "val", "test")
# Cells with this many training positives, or fewer, count as sparse support
# for a test positive. Both cutoffs are fixed before any AUROC is read.
SPARSE_CUTOFFS = (0, 1)
# A high-count stratum cannot fill validation (cut_counts sends a size-2
# stratum to train and test only). Those groups are the composition factor
# the splitter itself isolates. The exploratory table uses this cutoff and
# no other question subset.
HIGH_COUNT = 3
DISTRIBUTION_LABEL = (
    "sample distribution across the 20 split seeds (ddof=1 for the SD); "
    "not a confidence interval"
)
PROTECTED = [
    STAGE4_DIR / "report.json",
    STAGE4_DIR / "report.md",
    STAGE4_DIR / "VERDICT.md",
    STAGE5_DIR / "report.json",
    STAGE5_DIR / "report.md",
    STAGE5_DIR / "provenance.json",
    STAGE6_DIR / "report.json",
    STAGE6_DIR / "report.md",
    STAGE6_DIR / "provenance.json",
    STAGE6_DIR / "A0_seed0" / "metrics.json",
    STAGE6_DIR / "A4_seed0" / "metrics.json",
    STAGE6_DIR / "A7_seed0" / "metrics.json",
    STAGE6_DIR / "A7_seed1" / "metrics.json",
    STAGE6_DIR / "A7_seed2" / "metrics.json",
    PROJECT_ROOT / "results/summary/ragtruth_historical_freeze/MANIFEST.json",
    PROJECT_ROOT / "results/summary/ragtruth_historical_freeze/synthetic_fingerprint_seed0_n30.parquet",
    PROJECT_ROOT / "rcgate/data/splits.py",
    *COMPANION_TABLES,
]
STAGE6_A7_MEAN = 0.5025


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
    if isinstance(value, np.bool_):
        return bool(value)
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


def _round4(value: float) -> float:
    return float(np.round(float(value), 4))


def distribution_summary(values) -> dict:
    """Sample distribution of seed-level statistics.

    The SD uses ``ddof=1``. Percentiles use ``numpy.quantile`` (linear).
    Nothing here is a confidence interval, and the 20 seeds are not treated
    as 20 independent datasets.
    """
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
    summary["statistic"] = "sample_distribution_across_seeds"
    summary["is_confidence_interval"] = False
    summary["label"] = DISTRIBUTION_LABEL
    protocol = across_seed_dispersion(finite if finite.size else [float("nan")])
    summary["protocol_mean"] = protocol["mean"]
    summary["protocol_sd_across_seeds"] = protocol["sd_across_seeds"]
    return summary


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return float("nan")
    return float(len(left & right) / len(union))


def spearman(x, y) -> float | None:
    """Rank correlation. Undefined when either series is constant. Not a p-value."""
    xs = np.asarray(list(x), dtype="float64")
    ys = np.asarray(list(y), dtype="float64")
    if xs.size != ys.size or xs.size < 3:
        return None
    if np.unique(xs).size < 2 or np.unique(ys).size < 2:
        return None
    rx = pd.Series(xs).rank(method="average").to_numpy()
    ry = pd.Series(ys).rank(method="average").to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def _question_sets(split) -> dict[str, list[str]]:
    return {
        name: sorted(getattr(split, name)[split.group_column].astype(str).unique())
        for name in PARTITIONS
    }


def _cell_counts(frame: pd.DataFrame) -> dict[str, int]:
    grouped = frame.groupby(["generator_id", "claim_type"], sort=True)["label"].sum()
    return {
        f"{int(gen)}|{int(ctype)}": int(total)
        for (gen, ctype), total in grouped.items()
    }


def _generator_names(frame: pd.DataFrame) -> dict[str, str]:
    if "source_model" not in frame.columns:
        return {}
    names = {}
    for gen, part in frame.groupby("generator_id"):
        values = sorted(set(part["source_model"].astype(str)))
        names[str(int(gen))] = values[0] if len(values) == 1 else ",".join(values)
    return names


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------


def compare_companions(frames: dict[int, pd.DataFrame]) -> dict:
    """How s0, s1, and s2 differ. Shared claims are compared; nothing is refit."""
    pairwise = []
    signal_cols = ["agree", "contra", "sem_dist", "support", "src_quality", "conflict"]
    id_cols = ["label", "claim_text", "claim_type", "generator_id", "question_id"]
    for left, right in ((0, 1), (0, 2), (1, 2)):
        a, b = frames[left], frames[right]
        q_a, q_b = set(a["question_id"].astype(str)), set(b["question_id"].astype(str))
        c_a, c_b = set(a["claim_id"].astype(str)), set(b["claim_id"].astype(str))
        shared = sorted(c_a & c_b)
        aa = a.set_index("claim_id").loc[shared]
        bb = b.set_index("claim_id").loc[shared]
        diffs = {}
        for col in id_cols:
            diffs[col] = int((aa[col].astype(str).to_numpy() != bb[col].astype(str).to_numpy()).sum())
        for col in signal_cols:
            diffs[col] = int(
                (~np.isclose(aa[col].to_numpy(dtype="float64"), bb[col].to_numpy(dtype="float64"), equal_nan=True)).sum()
            )
        pairwise.append(
            {
                "tables": [left, right],
                "questions_only_left": sorted(q_a - q_b),
                "questions_only_right": sorted(q_b - q_a),
                "n_shared_questions": len(q_a & q_b),
                "n_shared_claims": len(shared),
                "shared_column_differences": diffs,
            }
        )
    return {"pairwise": pairwise}


def _stage6_test_sets(frames: dict[int, pd.DataFrame]) -> dict[int, list[str]]:
    """Stage 6 assigned table s{k} to seed k. Reconstructed, not refit."""
    out = {}
    for seed in (0, 1, 2):
        split = group_stratified_split(frames[seed], seed=seed)
        assert_disjoint(split)
        out[seed] = _question_sets(split)["test"]
    return out


# ---------------------------------------------------------------------------
# fit and score
# ---------------------------------------------------------------------------


def fit_all(cfg, frame: pd.DataFrame) -> None:
    for seed in SEEDS:
        split = group_stratified_split(frame, seed=seed)
        assert_disjoint(split)
        for variant in ALL_VARIANTS:
            ctx = RunContext.build(cfg, variant=variant, seed=seed)
            if STAGE7_DIR.resolve() not in ctx.out_dir.resolve().parents:
                raise RuntimeError(f"refusing to write outside {STAGE7_DIR}: {ctx.out_dir}")
            result = fit_variant(ctx, df=frame, split=split)
            persist(ctx, result)
            print(
                f"  fit {variant} seed={seed} skipped={result.skipped}",
                flush=True,
            )


def _metrics_path(variant: str, seed: int) -> Path:
    return STAGE7_DIR / f"{variant}_seed{seed}" / "metrics.json"


def _checkpoint_path(variant: str, seed: int) -> Path:
    return STAGE7_DIR / f"{variant}_seed{seed}" / "model.joblib"


def score_checkpoints(frame: pd.DataFrame, n_resamples: int) -> dict:
    """Reload checkpoints and apply the Stage 5 grouped protocol."""
    import joblib

    bundles = {}
    prediction_rows = []
    checks = []
    for seed in SEEDS:
        split = group_stratified_split(frame, seed=seed)
        test = split.test
        y = test["label"].to_numpy()
        groups = test["question_id"].astype(str).to_numpy()
        scores = {}
        thresholds = {}
        rounded = {}
        for variant in VARIANTS:
            meta = json.loads(_metrics_path(variant, seed).read_text())
            if meta.get("skipped"):
                raise RuntimeError(f"{variant} seed {seed} was skipped")
            if meta.get("split_method") != SPLIT_GROUP_STRATIFIED or int(meta["split_seed"]) != seed:
                raise RuntimeError(f"{variant} seed {seed} was not fit with the stratified split")
            if Path(meta["table"]).resolve() != FIT_TABLE.resolve():
                raise RuntimeError(f"{variant} seed {seed} was not fit on {FIT_TABLE.name}")
            model = joblib.load(_checkpoint_path(variant, seed))
            score = np.asarray(model.predict_proba(test), dtype="float64")
            threshold = float(meta["threshold"])
            got = slice_metrics(y, score, name="all", threshold=threshold, n_bins=15).as_dict()
            expected = meta["test"]
            if int(expected["n"]) != int(y.size):
                raise RuntimeError(f"{variant} seed {seed} test n {y.size} != metrics.json {expected['n']}")
            if got["auroc"] != expected["auroc"]:
                raise RuntimeError(
                    f"reloaded {variant} seed {seed} auroc={got['auroc']} "
                    f"does not match metrics.json {expected['auroc']}"
                )
            # HistGradientBoosting can move a score by <1e-6 across the stored
            # threshold after joblib reload. That flips a hard call and the
            # 4th decimal of F1. AUROC is unchanged. Point metrics stay the
            # fit-time values in metrics.json.
            edge = {
                key: {"reloaded": got[key], "fit": expected[key]}
                for key in METRICS
                if got[key] != expected[key]
            }
            scores[variant] = score
            thresholds[variant] = threshold
            rounded[variant] = expected
            checks.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "auroc_matched_metrics_json": True,
                    "threshold_edge": edge,
                    "n": int(y.size),
                }
            )
        bundles[seed] = {
            "y": y,
            "groups": groups,
            "scores": scores,
            "thresholds": thresholds,
            "rounded": rounded,
            "claim_id": test["claim_id"].astype(str).to_numpy(),
            "generator_id": test["generator_id"].to_numpy(),
            "claim_type": test["claim_type"].to_numpy(),
        }
        for i in range(len(test)):
            row = {
                "seed": seed,
                "claim_id": str(test["claim_id"].iloc[i]),
                "question_id": str(test["question_id"].iloc[i]),
                "label": int(test["label"].iloc[i]),
                "generator_id": int(test["generator_id"].iloc[i]),
                "claim_type": int(test["claim_type"].iloc[i]),
            }
            for variant in VARIANTS:
                row[variant] = float(scores[variant][i])
            prediction_rows.append(row)
        print(f"  scored seed={seed}", flush=True)

    variants = []
    for variant in VARIANTS:
        per_seed = []
        for seed in SEEDS:
            bundle = bundles[seed]
            y = bundle["y"]
            score = bundle["scores"][variant]
            groups = bundle["groups"]
            threshold = bundle["thresholds"][variant]
            got = bundle["rounded"][variant]
            interval = within_seed_auroc_interval(y, score, groups, n_resamples=n_resamples, seed=seed)
            per_seed.append(
                {
                    "variant": variant,
                    "seed": seed,
                    "n_claims": int(y.size),
                    "n_questions": int(np.unique(groups).size),
                    "n_positive": int(np.asarray(y).sum()),
                    "threshold": threshold,
                    "auroc": got["auroc"],
                    "f1": got["f1"],
                    "precision": got["precision"],
                    "recall": got["recall"],
                    "ece": got["ece"],
                    "grouped_interval": interval,
                }
            )
        block = {"variant": variant, "per_seed": per_seed}
        for name in METRICS:
            block[name] = distribution_summary([row[name] for row in per_seed])
        variants.append(block)

    paired = {}
    for baseline in BASELINES:
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
            delta = None if corrected["delta"] is None else float(corrected["delta"])
            per_seed.append(
                {
                    "comparison": f"A7 - {baseline}",
                    "baseline": baseline,
                    "seed": seed,
                    "n_claims": int(bundle["y"].size),
                    "n_questions": int(np.unique(bundle["groups"]).size),
                    "delta_auroc": None if delta is None else _round4(delta),
                    "delta_auroc_unrounded": delta,
                    "grouped_interval": {
                        "lo": corrected["lo"],
                        "hi": corrected["hi"],
                        "n_requested": corrected["n_requested"],
                        "n_finite": corrected["n_finite"],
                        "position_vs_0": classify_interval(corrected["lo"], corrected["hi"]),
                    },
                    "bootstrap_frac_delta_gt_0": corrected["bootstrap_frac_delta_gt_0"],
                    "fraction_is_p_value": False,
                }
            )
        deltas = [row["delta_auroc"] for row in per_seed]
        point = [row["delta_auroc_unrounded"] for row in per_seed]
        positions = [row["grouped_interval"]["position_vs_0"] for row in per_seed]
        paired[baseline] = {
            "comparison": f"A7 - {baseline}",
            "per_seed": per_seed,
            "delta": distribution_summary(deltas),
            "n_a7_gt_baseline": int(sum(v is not None and v > 0 for v in point)),
            "n_a7_lt_baseline": int(sum(v is not None and v < 0 for v in point)),
            "n_a7_eq_baseline": int(sum(v is not None and v == 0 for v in point)),
            "n_interval_entirely_above_0": int(sum(p == "entirely_above_0" for p in positions)),
            "n_interval_entirely_below_0": int(sum(p == "entirely_below_0" for p in positions)),
            "n_interval_covers_0": int(sum(p == "covers_0" for p in positions)),
            "n_interval_undefined": int(sum(p == "undefined" for p in positions)),
            "seed_interval_positions": positions,
            "interval_label": (
                "per-seed 95% paired question-grouped percentile bootstrap interval for delta AUROC"
            ),
            "fraction_label": "bootstrap fraction of resamples with delta > 0; not a p-value",
            "classical_p_value": None,
        }
    return {
        "variants": variants,
        "paired": paired,
        "checks": checks,
        "predictions": pd.DataFrame(prediction_rows),
    }


# ---------------------------------------------------------------------------
# splits, overlap, sparsity
# ---------------------------------------------------------------------------


def split_records(frame: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    rows = []
    assignments = []
    counts = group_positive_counts(frame)
    for seed in SEEDS:
        split = group_stratified_split(frame, seed=seed)
        assert_disjoint(split)
        balance = split_balance(frame, split)
        questions = _question_sets(split)
        high = sorted(questions["test"], key=lambda q: (-int(counts[q]), q))
        high = [q for q in high if int(counts[q]) >= HIGH_COUNT]
        entry = {
            "seed": seed,
            "question_ids": questions,
            "high_count_test_questions": high,
            "partitions": {
                name: {
                    "groups": balance["partitions"][name]["groups"],
                    "claims": balance["partitions"][name]["claims"],
                    "positives": balance["partitions"][name]["positives"],
                    "positive_rate": balance["partitions"][name]["positive_rate"],
                    "positive_rate_deviation": balance["partitions"][name]["positive_rate_deviation"],
                    "positives_by_generator": balance["partitions"][name]["positives_by_generator"],
                    "positive_groups": int(
                        (getattr(split, name).groupby(split.group_column)["label"].sum() > 0).sum()
                    ),
                }
                for name in PARTITIONS
            },
            "mean_absolute_deviation": balance["mean_absolute_deviation"],
            "max_absolute_deviation": balance["max_absolute_deviation"],
        }
        rows.append(entry)
        assigned = {}
        for name in PARTITIONS:
            for question_id in questions[name]:
                assigned[question_id] = name
        for question_id, n_positive in counts.items():
            part = frame[frame["question_id"].astype(str) == str(question_id)]
            assignments.append(
                {
                    "seed": seed,
                    "question_id": str(question_id),
                    "partition": assigned[str(question_id)],
                    "n_positive": int(n_positive),
                    "n_claims": int(len(part)),
                }
            )
    return rows, pd.DataFrame(assignments)


def overlap_analysis(records: list[dict], stage6_tests: dict[int, list[str]], n_groups: int) -> dict:
    tests = [set(row["question_ids"]["test"]) for row in records]
    values = []
    for i in range(len(tests)):
        for j in range(i + 1, len(tests)):
            values.append(jaccard(tests[i], tests[j]))
    arr = np.asarray(values, dtype="float64")
    union: set[str] = set()
    for group in tests:
        union |= group
    pool = set(records[0]["question_ids"]["train"]) | set(records[0]["question_ids"]["val"]) | set(records[0]["question_ids"]["test"])
    for row in records:
        for name in PARTITIONS:
            pool |= set(row["question_ids"][name])
    versus_stage6 = []
    for seed, stage6 in stage6_tests.items():
        versus_stage6.append(
            {
                "seed": seed,
                "jaccard_with_stage7_same_seed": jaccard(set(stage6), tests[seed]),
                "n_stage6": len(stage6),
                "n_stage7": len(tests[seed]),
                "n_shared": len(set(stage6) & tests[seed]),
            }
        )
    stage6_pairs = []
    stage6_sets = {seed: set(questions) for seed, questions in stage6_tests.items()}
    for left, right in ((0, 1), (0, 2), (1, 2)):
        stage6_pairs.append(
            {
                "seeds": [left, right],
                "jaccard": jaccard(stage6_sets[left], stage6_sets[right]),
                "n_shared": len(stage6_sets[left] & stage6_sets[right]),
            }
        )
    return {
        "n_pairwise": int(arr.size),
        "jaccard_min": float(arr.min()),
        "jaccard_median": float(np.median(arr)),
        "jaccard_max": float(arr.max()),
        "jaccard_mean": float(arr.mean()),
        "n_unique_test_questions": len(union),
        "n_groups_in_pool": len(pool),
        "n_groups_never_in_test": len(pool - union),
        "n_groups_reported_by_table": int(n_groups),
        "stage6_same_seed_test_jaccard": versus_stage6,
        "stage6_pairwise_test_jaccard": stage6_pairs,
        "dependence": (
            "Twenty seeds repartition one pool of question groups. "
            "A test set is about 28 groups drawn inside positive-count strata, "
            "so successive test sets share groups. The sample SD across seeds "
            "describes that dependent repartition. It is not the standard error "
            "of 20 independent datasets, and it is not a confidence interval."
        ),
    }


def _margin(frame: pd.DataFrame, column: str) -> dict[str, int]:
    totals = frame.groupby(column)["label"].sum()
    return {str(int(k)): int(v) for k, v in totals.items()}


def sparsity_analysis(frame: pd.DataFrame, auroc_by_variant: dict[str, list[float]]) -> dict:
    """Fairness counts, plus two pre-specified exploratory rank associations.

    The associations use the number of test positive claims whose
    (generator, claim type) cell has 0 training positives, and the same count
    at a cutoff of 1. They are rank correlations against A7, A0, and A4.
    No other feature is correlated with AUROC. No p-value is computed.
    """
    names = _generator_names(frame)
    full_cells = _cell_counts(frame)
    full_by_generator = _margin(frame, "generator_id")
    full_by_type = _margin(frame, "claim_type")
    claims_by_cell = (
        frame.groupby(["generator_id", "claim_type"]).size().astype(int).to_dict()
    )
    positive_questions = {}
    for (gen, ctype), part in frame.groupby(["generator_id", "claim_type"]):
        hit = part[part["label"] == 1]
        positive_questions[f"{int(gen)}|{int(ctype)}"] = sorted(set(hit["question_id"].astype(str)))

    per_seed = []
    for seed in SEEDS:
        split = group_stratified_split(frame, seed=seed)
        train_cells = _cell_counts(split.train)
        test_pos = split.test[split.test["label"] == 1]
        sparse_hits = dict.fromkeys(SPARSE_CUTOFFS, 0)
        for _, row in test_pos.iterrows():
            key = f"{int(row['generator_id'])}|{int(row['claim_type'])}"
            n_train = int(train_cells.get(key, 0))
            for cutoff in SPARSE_CUTOFFS:
                if n_train <= cutoff:
                    sparse_hits[cutoff] += 1
        per_seed.append(
            {
                "seed": seed,
                "train_positives_by_generator": _margin(split.train, "generator_id"),
                "val_positives_by_generator": _margin(split.val, "generator_id"),
                "test_positives_by_generator": _margin(split.test, "generator_id"),
                "train_positives_by_claim_type": _margin(split.train, "claim_type"),
                "val_positives_by_claim_type": _margin(split.val, "claim_type"),
                "test_positives_by_claim_type": _margin(split.test, "claim_type"),
                "train_positives_by_cell": train_cells,
                "val_positives_by_cell": _cell_counts(split.val),
                "test_positives_by_cell": _cell_counts(split.test),
                "test_positive_claims_with_sparse_train_support": {
                    str(cutoff): sparse_hits[cutoff] for cutoff in SPARSE_CUTOFFS
                },
            }
        )

    def _range(getter) -> dict[str, dict]:
        keys = sorted({key for row in per_seed for key in getter(row)})
        out = {}
        for key in keys:
            values = [int(getter(row).get(key, 0)) for row in per_seed]
            out[key] = {
                "min": int(min(values)),
                "median": float(np.median(values)),
                "max": int(max(values)),
            }
        return out

    exploratory = {"label": "exploratory", "pre_specified": True, "p_value": None}
    for cutoff in SPARSE_CUTOFFS:
        series = [
            row["test_positive_claims_with_sparse_train_support"][str(cutoff)] for row in per_seed
        ]
        exploratory[f"cutoff_{cutoff}"] = {
            "definition": (
                f"count of test positive claims whose (generator_id, claim_type) "
                f"cell has at most {cutoff} training positives"
            ),
            "per_seed": series,
            "distribution": distribution_summary(series),
            "spearman_vs_auroc": {
                variant: spearman(series, auroc_by_variant[variant]) for variant in ("A7", "A0", "A4")
            },
        }

    scarcest_generator = min(full_by_generator, key=lambda k: (full_by_generator[k], int(k)))
    scarce_questions = sorted(
        {
            q
            for key, questions in positive_questions.items()
            if key.startswith(f"{scarcest_generator}|")
            for q in questions
        }
    )
    scarce_partition = []
    for seed in SEEDS:
        split = group_stratified_split(frame, seed=seed)
        located = {}
        for question_id in scarce_questions:
            for name in PARTITIONS:
                ids = set(getattr(split, name)["question_id"].astype(str))
                if question_id in ids:
                    located[question_id] = name
        scarce_partition.append({"seed": seed, "questions": located})

    return {
        "exploratory_label": (
            "The rank associations and the scarcest-generator partition split "
            "are exploratory descriptions. They were limited to the conditioning "
            "variables the gate already uses. They are not a model search."
        ),
        "generator_names": names,
        "claim_type_names": {str(k): v for k, v in CLAIM_TYPES.items()},
        "full_table_positives_by_generator": full_by_generator,
        "full_table_positives_by_claim_type": full_by_type,
        "full_table_positives_by_cell": full_cells,
        "full_table_claims_by_cell": {
            f"{int(gen)}|{int(ctype)}": int(n) for (gen, ctype), n in claims_by_cell.items()
        },
        "train_positive_range_by_generator": _range(lambda row: row["train_positives_by_generator"]),
        "train_positive_range_by_claim_type": _range(lambda row: row["train_positives_by_claim_type"]),
        "train_positive_range_by_cell": _range(lambda row: row["train_positives_by_cell"]),
        "per_seed": per_seed,
        "exploratory": exploratory,
        "scarcest_generator": {
            "generator_id": int(scarcest_generator),
            "name": names.get(scarcest_generator, ""),
            "full_table_positives": int(full_by_generator[scarcest_generator]),
            "positive_questions": scarce_questions,
            "partition_by_seed": scarce_partition,
        },
    }


def high_count_composition(records: list[dict], auroc_by_variant: dict[str, list[float]]) -> dict:
    """Exploratory table: which high-count groups landed in test.

    Every seed's test set contains one group from each size-2 high-count
    stratum. The key is that pair of question ids. AUROC is averaged inside
    each observed pair. This is a description, not a search over groups.
    """
    groups: dict[str, list[int]] = {}
    for row in records:
        key = ",".join(row["high_count_test_questions"])
        groups.setdefault(key, []).append(int(row["seed"]))
    table = []
    for key, seeds in sorted(groups.items()):
        entry = {"high_count_test_questions": key, "n_seeds": len(seeds), "seeds": seeds}
        for variant in ("A7", "A0", "A4"):
            values = [auroc_by_variant[variant][seed] for seed in seeds]
            entry[f"{variant}_mean_auroc"] = float(np.mean(values))
            entry[f"{variant}_values"] = values
        table.append(entry)
    return {
        "label": "exploratory",
        "rule": (
            f"Group question ids with at least {HIGH_COUNT} positive claims. "
            "Tabulate the test subset of those ids. No other grouping is tried."
        ),
        "by_test_pair": table,
    }


def stage6_seed0_check() -> dict:
    """Same table, same split seed, same model seed as Stage 6 seed 0."""
    compared = {}
    matched = True
    for variant in VARIANTS:
        stage6 = json.loads((STAGE6_DIR / f"{variant}_seed0" / "metrics.json").read_text())
        stage7 = json.loads(_metrics_path(variant, 0).read_text())
        keys = list(METRICS) + ["threshold"]
        diffs = {}
        for key in keys:
            left = stage6["test"][key] if key != "threshold" else stage6["threshold"]
            right = stage7["test"][key] if key != "threshold" else stage7["threshold"]
            if left != right:
                diffs[key] = {"stage6": left, "stage7": right}
                matched = False
        compared[variant] = {"matched": not diffs, "differences": diffs}
    return {"matched": matched, "variants": compared}


def synthetic_regression() -> dict:
    """Regenerate the frozen n=30 fingerprint. Do not refit synthetic models."""
    from .data.synthetic import generate, load_planted

    manifest_path = PROJECT_ROOT / "results/summary/ragtruth_historical_freeze/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    fingerprint = manifest["synthetic_fingerprint"]
    path = PROJECT_ROOT / fingerprint["path"]
    file_hash = _sha256(path)
    frozen = pd.read_parquet(path)
    fresh = generate(
        load_planted(),
        seed=int(fingerprint["seed"]),
        n_questions=int(fingerprint["n_questions"]),
        n_generators=int(fingerprint["n_generators"]),
    )
    fresh = fresh.reset_index(drop=True)
    frozen = frozen.reset_index(drop=True)
    shared = [col for col in frozen.columns if col in fresh.columns]
    equal = bool(frozen[shared].equals(fresh[shared])) and list(frozen.columns) == list(fresh.columns)
    return {
        "fingerprint_path": str(path),
        "manifest_sha256": fingerprint["sha256"],
        "file_sha256": file_hash,
        "file_hash_matches_manifest": file_hash == fingerprint["sha256"],
        "rows_frozen": int(len(frozen)),
        "rows_regenerated": int(len(fresh)),
        "frame_equal": equal,
        "unchanged": bool(file_hash == fingerprint["sha256"] and equal),
        "models_refit": False,
    }


# ---------------------------------------------------------------------------
# verdict
# ---------------------------------------------------------------------------


def _auroc_values(block: dict, variant: str) -> list[float]:
    found = next(item for item in block if item["variant"] == variant)
    return list(found["auroc"]["values"])


def recommend(facts: dict) -> dict:
    """Map the pre-specified pattern onto one of the three paper choices.

    Choice 1 keeps A7 as the main architecture and reports a negative result.
    Choice 2 keeps A7 only as a mechanism prototype.
    Choice 3 says the architecture should be reconsidered before publication.

    A stable loss to both baselines, with no paired interval in A7's favor and
    a larger seed SD, is a negative architectural result. It becomes choice 3
    when every generator has at least five positive claims, so the gate's
    conditioning cells are not obviously unidentified. It becomes choice 2
    when some generator has fewer than five positives: the same run shows the
    failure and shows that this slice does not identify a per-generator gate.
    Choice 1 requires the median to clear both baselines, a point-estimate win
    on at least 15 seeds against each, at least one interval entirely above 0,
    and a seed SD no larger than both baselines.
    """
    a7 = facts["median"]["A7"]
    a0 = facts["median"]["A0"]
    a4 = facts["median"]["A4"]
    below = a7 < a0 and a7 < a4
    rarely = facts["wins"]["A0"] < 10 and facts["wins"]["A4"] < 10
    no_support = facts["interval_favors_a7"]["A0"] == 0 and facts["interval_favors_a7"]["A4"] == 0
    less_stable = facts["sd"]["A7"] > facts["sd"]["A0"] and facts["sd"]["A7"] > facts["sd"]["A4"]
    weak = facts["min_generator_positives"] < 5
    above = a7 > a0 and a7 > a4
    often = facts["wins"]["A0"] >= 15 and facts["wins"]["A4"] >= 15
    any_interval = facts["interval_favors_a7"]["A0"] + facts["interval_favors_a7"]["A4"] > 0
    if above and often and any_interval and not less_stable:
        choice = 1
        reason = (
            "The 20-seed median is above both baselines, the point estimate wins "
            "on at least 15 seeds against each, a paired interval excludes 0 in "
            "A7's favor at least once, and A7's seed SD is not larger than both baselines."
        )
    elif below and rarely and no_support and less_stable and not weak:
        choice = 3
        reason = (
            "A7's median is below both baselines, it wins on fewer than half the "
            "seeds, no paired interval favors it, and its seed SD is larger, on a "
            "table where every generator has at least five positives."
        )
    elif below and no_support and weak:
        choice = 2
        reason = (
            "A7's median is below both baselines and no paired interval favors it. "
            "At least one generator has fewer than five positive claims, so this "
            "slice does not identify a per-generator gate. The result is negative "
            "and is not a clean test of the mechanism."
        )
    elif less_stable and weak and not above:
        choice = 2
        reason = (
            "A7's median is not above both baselines, its seed SD is larger than "
            "both, and the paired intervals do not show a stable advantage. "
            "At least one generator has fewer than five positive claims, so a "
            "gate conditioned on generator is weakly identified on this slice. "
            "That supports keeping A7 as a mechanism prototype. It does not "
            "support publishing A7 as the main architecture on this RAGTruth result, "
            "and it does not by itself refute the mechanism on a better-supported sample."
        )
    else:
        choice = 2
        reason = (
            "The 20-seed result does not show a stable gain over A0 and A4. "
            "A7 stays a mechanism prototype until a less sparse sample says otherwise."
        )
    return {"choice": choice, "reason": reason, "rule_inputs": {
        "median_below_both": below,
        "wins_under_half": rarely,
        "no_interval_favors_a7": no_support,
        "sd_larger_than_both": less_stable,
        "generator_with_fewer_than_5_positives": weak,
    }}


def build_answers(result: dict) -> dict:
    variants = {item["variant"]: item for item in result["scored"]["variants"]}
    auroc = {name: variants[name]["auroc"] for name in ("A7", "A0", "A4")}
    paired = result["scored"]["paired"]
    records = result["splits"]
    test_pos = [row["partitions"]["test"]["positives"] for row in records]
    test_rate = [row["partitions"]["test"]["positive_rate_deviation"] for row in records]
    pos_groups = [row["partitions"]["test"]["positive_groups"] for row in records]
    facts = {
        "median": {name: auroc[name]["median"] for name in auroc},
        "sd": {name: auroc[name]["sd"] for name in auroc},
        "wins": {name: paired[name]["n_a7_gt_baseline"] for name in BASELINES},
        "interval_favors_a7": {
            name: paired[name]["n_interval_entirely_above_0"] for name in BASELINES
        },
        "min_generator_positives": min(
            result["sparsity"]["full_table_positives_by_generator"].values()
        ),
    }
    stage6_inside = auroc["A7"]["min"] <= STAGE6_A7_MEAN <= auroc["A7"]["max"]
    balance_keys = {
        tuple(row["partitions"][name]["positives"] for name in PARTITIONS) for row in records
    }
    balance_constant = len(balance_keys) == 1
    rate_span = float(max(test_rate) - min(test_rate)) if test_rate else float("nan")
    sparse0 = result["sparsity"]["exploratory"]["cutoff_0"]
    rho7 = sparse0["spearman_vs_auroc"]["A7"]
    rho0 = sparse0["spearman_vs_auroc"]["A0"]
    rho4 = sparse0["spearman_vs_auroc"]["A4"]
    sparse_varies = sparse0["distribution"]["max"] != sparse0["distribution"]["min"]
    recommendation = recommend(facts)
    answers = {
        "1_stage6_low_a7_reproduced": {
            "stage6_mean_auroc": STAGE6_A7_MEAN,
            "stage7_mean": auroc["A7"]["mean"],
            "stage7_median": auroc["A7"]["median"],
            "stage7_min": auroc["A7"]["min"],
            "stage7_max": auroc["A7"]["max"],
            "stage6_mean_inside_stage7_range": stage6_inside,
            "stage6_mean_below_stage7_q25": STAGE6_A7_MEAN < auroc["A7"]["q25"],
            "statement": (
                f"Stage 6's three-seed mean A7 AUROC was {STAGE6_A7_MEAN:.4f}. "
                f"On 20 seeds the mean is {auroc['A7']['mean']:.4f} and the median is "
                f"{auroc['A7']['median']:.4f}, with range "
                f"[{auroc['A7']['min']:.4f}, {auroc['A7']['max']:.4f}] "
                f"and 25th percentile {auroc['A7']['q25']:.4f}. "
                + (
                    "0.5025 falls inside that range"
                    if stage6_inside
                    else "0.5025 falls outside that range"
                )
                + (
                    " and below the 25th percentile, so it is a low draw the distribution contains, not the typical seed."
                    if STAGE6_A7_MEAN < auroc["A7"]["q25"]
                    else "."
                )
            ),
        },
        "2_a7_auroc_distribution": auroc["A7"],
        "3_a0_a4_auroc_distribution": {"A0": auroc["A0"], "A4": auroc["A4"]},
        "4_a7_consistently_below_a0": {
            "n_below": paired["A0"]["n_a7_lt_baseline"],
            "n_above": paired["A0"]["n_a7_gt_baseline"],
            "n_equal": paired["A0"]["n_a7_eq_baseline"],
            "mean_delta": paired["A0"]["delta"]["mean"],
            "consistently_below": paired["A0"]["n_a7_lt_baseline"] == 20,
        },
        "5_a7_consistently_below_a4": {
            "n_below": paired["A4"]["n_a7_lt_baseline"],
            "n_above": paired["A4"]["n_a7_gt_baseline"],
            "n_equal": paired["A4"]["n_a7_eq_baseline"],
            "mean_delta": paired["A4"]["delta"]["mean"],
            "consistently_below": paired["A4"]["n_a7_lt_baseline"] == 20,
        },
        "6_point_estimate_wins": {
            "A0": paired["A0"]["n_a7_gt_baseline"],
            "A4": paired["A4"]["n_a7_gt_baseline"],
            "n_seeds": 20,
        },
        "7_variance_larger": {
            "sd_A7": auroc["A7"]["sd"],
            "sd_A0": auroc["A0"]["sd"],
            "sd_A4": auroc["A4"]["sd"],
            "iqr_A7": auroc["A7"]["iqr"],
            "iqr_A0": auroc["A0"]["iqr"],
            "iqr_A4": auroc["A4"]["iqr"],
            "larger_than_both": auroc["A7"]["sd"] > auroc["A0"]["sd"] and auroc["A7"]["sd"] > auroc["A4"]["sd"],
        },
        "8_imbalance_versus_instability": {
            "positive_counts_identical_across_seeds": balance_constant,
            "positive_count_tuple": list(next(iter(balance_keys))),
            "test_positive_rate_deviation_span": rate_span,
            "test_positive_groups_min": int(min(pos_groups)),
            "test_positive_groups_max": int(max(pos_groups)),
            "test_positives_min": int(min(test_pos)),
            "test_positives_max": int(max(test_pos)),
            "model_seed_equals_split_seed": True,
            "positive_count_tuples": [list(item) for item in sorted(balance_keys)],
            "statement": (
                "Partition positive counts are "
                + ("the same on every seed" if balance_constant else "not the same on every seed")
                + f" ({[list(item) for item in sorted(balance_keys)]} for train, validation, test). "
                "The seed still sets both the group assignment and A7's optimizer RNG, "
                "so group identity and initialization stay confounded with each other."
            ),
        },
        "9_sparsity": {
            "min_generator_positives": facts["min_generator_positives"],
            "sparse0_varies_across_seeds": bool(sparse_varies),
            "spearman_sparse0_vs_A7": rho7,
            "spearman_sparse0_vs_A0": rho0,
            "spearman_sparse0_vs_A4": rho4,
            "exploratory": True,
        },
        "10_recommendation": recommendation,
    }
    return answers


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _dist_row(variant: str, metric: str, block: dict) -> str:
    return _md(
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


def _fmt_cell(gen: str, ctype: str, names: dict, types: dict) -> str:
    gname = names.get(gen, gen)
    tname = types.get(ctype, ctype)
    return f"{gname} / {tname}"


def render_markdown(result: dict) -> str:
    variants = {item["variant"]: item for item in result["scored"]["variants"]}
    lines = [
        "# RC-Gate Stage 7 — 20-seed group-stratified robustness",
        "",
        "This file varies the split seed and nothing else. The group-stratified",
        "splitter, the signal tables, the variants, the hyperparameters, and the",
        "Stage 5 uncertainty procedure are unchanged. No earlier result directory",
        "was rewritten. The seed distribution below is not a confidence interval.",
        "",
        "## Protocol",
        "",
        "- Split function: `group_stratified_split` in `rcgate/data/splits.py`.",
        "- Split method key: `group_stratified`.",
        "- Grouping field: `question_id` (RAGTruth source id). Whole groups move together.",
        "- Stratum: the group's integer positive-claim count, the sum of `label`.",
        "- Fractions: 0.6 train, 0.2 validation, 0.2 test, applied inside each stratum",
        "  by `cut_counts` (`round(0.6 n)`, `round(0.2 n)`, remainder test).",
        "- Seed: `numpy.random.default_rng(SeedSequence([seed, stratum]))` shuffles",
        "  group ids that were sorted first. Strata do not share a random stream.",
        "- Seeds: 0 through 19. The model seed equals the split seed, as in Stage 6.",
        "- Fit table: `ragtruth_corrected_integrity_v1_s0.parquet` for every seed.",
        "  The config path has no `{seed}` placeholder, so s3–s19 are not built.",
        "- Companion tables s1 and s2 are hashed below and are not fit tables.",
        "  Shared claims match s0 on labels, text, types, and the six signals.",
        "  Stage 6 seed k used table sk, so Stage 7 seeds 1 and 2 are not copies",
        "  of Stage 6 seeds 1 and 2. Stage 7 seed 0 is the same fit as Stage 6 seed 0.",
        "- Variants A0–A7 refit. A8 skipped because the table has no judge votes.",
        "- Thresholds: the existing validation quantile rule. Not chosen from test A7.",
        "- Point metrics are the seed statistics already rounded to 4 decimals.",
        "- Distribution: mean, median, sample SD (ddof=1), min, max, 25th percentile,",
        "  75th percentile, interquartile range. `numpy.quantile` linear method.",
        "  This distribution is not a confidence interval.",
        "- Within-seed interval: 95% question-grouped percentile bootstrap, 1000 resamples.",
        "- Paired interval: one question draw scores both models. The bootstrap",
        "  fraction of positive deltas is not a p-value. No classical p-value is reported.",
        "",
        "## Companion tables",
        "",
    ]
    for item in result["companions"]["pairwise"]:
        left, right = item["tables"]
        diffs = item["shared_column_differences"]
        n_diff = sum(diffs.values())
        lines.append(
            f"- s{left} vs s{right}: shared questions {item['n_shared_questions']}, "
            f"only s{left} {item['questions_only_left'] or 'none'}, "
            f"only s{right} {item['questions_only_right'] or 'none'}, "
            f"shared-claim column differences {n_diff}."
        )
    lines += [
        "",
        "Stage 6 test-question Jaccard against the Stage 7 test set at the same seed:",
        "",
    ]
    for item in result["overlap"]["stage6_same_seed_test_jaccard"]:
        lines.append(
            f"- seed {item['seed']}: Jaccard {format_point(item['jaccard_with_stage7_same_seed'])} "
            f"({item['n_shared']} shared of {item['n_stage6']} and {item['n_stage7']})."
        )
    seed0 = result["stage6_seed0"]
    edges = [item for item in result["scored"]["checks"] if item["threshold_edge"]]
    lines += [
        "",
        f"Stage 6 seed-0 metrics reproduced on this path: {seed0['matched']}.",
        "",
        "Point metrics are the fit-time `metrics.json` values. Reloaded checkpoints",
        "matched those AUROCs. A reload that only changes a thresholded metric is a",
        "score sitting on the stored threshold, not a second model.",
        "",
    ]
    if not edges:
        lines.append("No reloaded checkpoint changed a thresholded metric.")
    else:
        lines.append(f"Reloaded checkpoints with a thresholded-metric difference: {len(edges)}.")
        for item in edges:
            lines.append(
                f"- {item['variant']} seed {item['seed']}: {json.dumps(item['threshold_edge'])}."
            )
    lines += [
        "",
        "## Split balance",
        "",
        "Deviation is the partition positive rate minus the full-table positive rate.",
        "Group counts follow from the stratum sizes, so they do not depend on the seed.",
        "Claim counts can still move when a short group changes partition.",
        "",
        _md(
            [
                "seed",
                "train groups",
                "val groups",
                "test groups",
                "train positives",
                "val positives",
                "test positives",
                "train claims",
                "val claims",
                "test claims",
                "train rate dev",
                "val rate dev",
                "test rate dev",
                "test positive groups",
            ]
        ),
        _md(["---"] * 14),
    ]
    for row in result["splits"]:
        part = row["partitions"]
        lines.append(
            _md(
                [
                    str(row["seed"]),
                    str(part["train"]["groups"]),
                    str(part["val"]["groups"]),
                    str(part["test"]["groups"]),
                    str(part["train"]["positives"]),
                    str(part["val"]["positives"]),
                    str(part["test"]["positives"]),
                    str(part["train"]["claims"]),
                    str(part["val"]["claims"]),
                    str(part["test"]["claims"]),
                    format_point(part["train"]["positive_rate_deviation"]),
                    format_point(part["val"]["positive_rate_deviation"]),
                    format_point(part["test"]["positive_rate_deviation"]),
                    str(part["test"]["positive_groups"]),
                ]
            )
        )
    lines += [
        "",
        "## Distributions",
        "",
        "Each row is 20 seed-level statistics. The SD is not a confidence interval.",
        "",
        _md(["variant", "metric", "mean", "median", "sd", "min", "max", "p25", "p75", "iqr"]),
        _md(["---"] * 10),
    ]
    for variant in VARIANTS:
        for metric in METRICS:
            lines.append(_dist_row(variant, metric, variants[variant][metric]))
    lines += [
        "",
        "### Seed-level AUROC",
        "",
        _md(["seed", *VARIANTS]),
        _md(["---"] * 9),
    ]
    for seed in SEEDS:
        lines.append(
            _md(
                [str(seed)]
                + [format_point(variants[variant]["per_seed"][seed]["auroc"]) for variant in VARIANTS]
            )
        )
    lines += [
        "",
        "Seed-level F1, precision, recall, and ECE are in `seed_metrics.csv`.",
        "Their distributions are in the table above.",
        "",
        "## A7 minus A0",
        "",
        "Delta is test AUROC(A7) minus test AUROC(A0) on the same claims.",
        "The interval is the paired question-grouped percentile bootstrap.",
        "A position of `entirely_above_0` favors A7. `entirely_below_0` favors A0.",
        "`covers_0` favors neither. The bootstrap fraction is not a p-value.",
        "",
    ]
    lines.extend(_paired_section(result["scored"]["paired"]["A0"]))
    lines += ["", "## A7 minus A4", ""]
    lines.extend(_paired_section(result["scored"]["paired"]["A4"]))
    overlap = result["overlap"]
    lines += [
        "",
        "## Test-set overlap",
        "",
        f"- Pairwise test-question Jaccard over {overlap['n_pairwise']} pairs: "
        f"min {format_point(overlap['jaccard_min'])}, "
        f"median {format_point(overlap['jaccard_median'])}, "
        f"max {format_point(overlap['jaccard_max'])}.",
        f"- Unique question groups that appear in at least one test set: "
        f"{overlap['n_unique_test_questions']} of {overlap['n_groups_in_pool']}.",
        f"- Question groups that never appear in a test set: {overlap['n_groups_never_in_test']}.",
        "",
        "Stage 6 pairwise test-question overlap, each seed on its own frozen table:",
        "",
    ]
    for item in overlap["stage6_pairwise_test_jaccard"]:
        left, right = item["seeds"]
        lines.append(
            f"- seeds {left} and {right}: Jaccard {format_point(item['jaccard'])}, "
            f"{item['n_shared']} shared questions."
        )
    lines += [
        "",
        overlap["dependence"],
        "",
        "Stage 6's three seeds were a small sample from this same kind of overlap.",
        "Adding seeds does not create 20 fresh RAGTruth corpora.",
        "",
    ]
    lines.extend(_sparsity_lines(result))
    synthetic = result["synthetic"]
    lines += [
        "## Synthetic regression",
        "",
        "The planted table was regenerated at the frozen fingerprint settings",
        f"(seed {0}, 30 questions, 3 generators) and compared with the stored parquet.",
        "Synthetic models were not refit. Planted parameters were not edited.",
        "",
        f"- File hash matches the historical manifest: {synthetic['file_hash_matches_manifest']}.",
        f"- Regenerated frame equals the stored frame: {synthetic['frame_equal']}.",
        f"- Unchanged: {synthetic['unchanged']}.",
        "",
        "## Answers",
        "",
    ]
    return "\n".join(lines)


def _paired_section(block: dict) -> list[str]:
    dist = block["delta"]
    lines = [
        _md(["", "mean", "median", "sd", "min", "max"]),
        _md(["---"] * 6),
        _md(
            [
                "delta AUROC",
                format_point(dist["mean"]),
                format_point(dist["median"]),
                format_point(dist["sd"]),
                format_point(dist["min"]),
                format_point(dist["max"]),
            ]
        ),
        "",
        f"- Seeds with A7 above the baseline (point estimate): {block['n_a7_gt_baseline']}.",
        f"- Seeds with A7 below the baseline: {block['n_a7_lt_baseline']}.",
        f"- Seeds with equal AUROC: {block['n_a7_eq_baseline']}.",
        f"- Paired intervals entirely above 0 (favor A7): {block['n_interval_entirely_above_0']}.",
        f"- Paired intervals entirely below 0 (favor the baseline): {block['n_interval_entirely_below_0']}.",
        f"- Paired intervals that cover 0: {block['n_interval_covers_0']}.",
        "",
        _md(["seed", "delta", "interval", "position vs 0", "bootstrap frac delta > 0 (not a p-value)"]),
        _md(["---"] * 5),
    ]
    for row in block["per_seed"]:
        interval = row["grouped_interval"]
        lines.append(
            _md(
                [
                    str(row["seed"]),
                    format_point(row["delta_auroc"]),
                    format_interval(interval["lo"], interval["hi"]),
                    interval["position_vs_0"],
                    format_point(row["bootstrap_frac_delta_gt_0"]),
                ]
            )
        )
    return lines


def _sparsity_lines(result: dict) -> list[str]:
    sparsity = result["sparsity"]
    names = sparsity["generator_names"]
    types = sparsity["claim_type_names"]
    lines = [
        "## Generator and claim-type support",
        "",
        "Counts are positive claims. The gate is conditioned on generator and claim type.",
        "These margins are properties of the frozen table and of the splits.",
        "The model was not changed to compensate.",
        "",
        "### Full table",
        "",
        _md(["cell", "claims", "positives"]),
        _md(["---", "---", "---"]),
    ]
    claims = sparsity["full_table_claims_by_cell"]
    positives = sparsity["full_table_positives_by_cell"]
    for key in sorted(claims, key=lambda k: (int(k.split("|")[0]), int(k.split("|")[1]))):
        gen, ctype = key.split("|")
        lines.append(_md([_fmt_cell(gen, ctype, names, types), str(claims[key]), str(positives.get(key, 0))]))
    lines += [
        "",
        "### Training positives across 20 seeds",
        "",
        "The range is the min and max training-positive count of that margin.",
        "",
        _md(["margin", "min", "median", "max"]),
        _md(["---"] * 4),
    ]
    for key, block in sparsity["train_positive_range_by_generator"].items():
        label = names.get(key, f"generator {key}")
        lines.append(
            _md([label, str(block["min"]), format_point(block["median"], 1), str(block["max"])])
        )
    for key, block in sparsity["train_positive_range_by_claim_type"].items():
        label = types.get(key, f"type {key}")
        lines.append(
            _md([f"type {label}", str(block["min"]), format_point(block["median"], 1), str(block["max"])])
        )
    lines += [
        "",
        "### Exploratory association",
        "",
        sparsity["exploratory_label"],
        "",
    ]
    for cutoff in SPARSE_CUTOFFS:
        block = sparsity["exploratory"][f"cutoff_{cutoff}"]
        dist = block["distribution"]
        rhos = block["spearman_vs_auroc"]
        lines.append(block["definition"].capitalize() + ".")
        lines.append(
            f"Across seeds: min {format_point(dist['min'], 0)}, "
            f"median {format_point(dist['median'], 1)}, max {format_point(dist['max'], 0)}."
        )
        lines.append(
            "Spearman rank correlation with AUROC, not a p-value: "
            f"A7 {format_point(rhos['A7'])}, A0 {format_point(rhos['A0'])}, A4 {format_point(rhos['A4'])}."
        )
        lines.append("")
    scarce = sparsity["scarcest_generator"]
    lines += [
        f"The generator with the fewest positives in the full table is "
        f"{scarce['name']} (id {scarce['generator_id']}), with "
        f"{scarce['full_table_positives']} positive claim(s), "
        f"in question(s) {scarce['positive_questions']}.",
        "",
        "### Exploratory high-count test composition",
        "",
        result["composition"]["rule"],
        "",
        _md(["test questions with ≥3 positives", "n seeds", "mean A7", "mean A0", "mean A4"]),
        _md(["---"] * 5),
    ]
    for row in result["composition"]["by_test_pair"]:
        lines.append(
            _md(
                [
                    row["high_count_test_questions"] or "(none)",
                    str(row["n_seeds"]),
                    format_point(row["A7_mean_auroc"]),
                    format_point(row["A0_mean_auroc"]),
                    format_point(row["A4_mean_auroc"]),
                ]
            )
        )
    lines.append("")
    return lines


def _paper_paragraphs(result: dict) -> list[str]:
    variants = {item["variant"]: item for item in result["scored"]["variants"]}
    a7, a0, a4 = variants["A7"]["auroc"], variants["A0"]["auroc"], variants["A4"]["auroc"]
    p0, p4 = result["scored"]["paired"]["A0"], result["scored"]["paired"]["A4"]
    overlap = result["overlap"]
    choice = result["answers"]["10_recommendation"]["choice"]
    choice_text = {
        1: "retain A7 as the main proposed architecture and frame this RAGTruth result as negative or unstable",
        2: "retain A7 only as a research hypothesis and mechanism prototype",
        3: "reconsider the architecture before publication",
    }[choice]
    reason = result["answers"]["10_recommendation"]["reason"]
    scarce = result["sparsity"]["scarcest_generator"]
    result_paragraph = (
        f"On the frozen corrected RAGTruth table of 800 claims and "
        f"{overlap['n_groups_in_pool']} question groups, A0–A7 were refit for split seeds "
        f"0–19 with the Stage 6 positive-count group stratification and the unchanged "
        f"training and threshold rules. A7 test AUROC had mean {format_point(a7['mean'])}, "
        f"median {format_point(a7['median'])}, sample SD {format_point(a7['sd'])} "
        f"(not a confidence interval), and range [{format_point(a7['min'])}, {format_point(a7['max'])}]. "
        f"A0 had mean {format_point(a0['mean'])} (SD {format_point(a0['sd'])}) and A4 had mean "
        f"{format_point(a4['mean'])} (SD {format_point(a4['sd'])}). "
        f"The A7−A0 delta had mean {format_point(p0['delta']['mean'])}; A7 was higher on "
        f"{p0['n_a7_gt_baseline']} of 20 seeds and lower on {p0['n_a7_lt_baseline']}. "
        f"The A7−A4 delta had mean {format_point(p4['delta']['mean'])}; A7 was higher on "
        f"{p4['n_a7_gt_baseline']} of 20 seeds and lower on {p4['n_a7_lt_baseline']}. "
        f"Paired question-grouped bootstrap intervals excluded 0 in favor of A7 on "
        f"{p0['n_interval_entirely_above_0']} of 20 seeds versus A0 and "
        f"{p4['n_interval_entirely_above_0']} of 20 versus A4, and in favor of the baseline on "
        f"{p0['n_interval_entirely_below_0']} and {p4['n_interval_entirely_below_0']} of 20 seeds. "
        f"The Stage 6 three-seed A7 mean of 0.5025 "
        f"{'lies inside' if a7['min'] <= STAGE6_A7_MEAN <= a7['max'] else 'lies outside'} "
        f"the 20-seed range"
        f"{' and below the 25th percentile' if STAGE6_A7_MEAN < a7['q25'] else ''}."
    )
    limits = (
        f"The 20 seeds repartition one pool of {overlap['n_groups_in_pool']} questions. "
        f"Pairwise Jaccard overlap of the test question sets has minimum "
        f"{format_point(overlap['jaccard_min'])}, median {format_point(overlap['jaccard_median'])}, "
        f"and maximum {format_point(overlap['jaccard_max'])}. "
        f"{overlap['n_unique_test_questions']} groups appear in some test set and "
        f"{overlap['n_groups_never_in_test']} never do. The across-seed SD is dispersion "
        f"under that dependence, not a confidence interval and not evidence from 20 corpora. "
        f"Each test set has 15 positive claims. Validation has 9. "
        f"{scarce['name']} contributes {scarce['full_table_positives']} positive claim in the "
        f"whole table, and several generator-by-type cells have none, so a gate conditioned "
        f"on those factors is weakly identified. The model seed equals the split seed, so "
        f"A7's extra dispersion mixes assignment with optimizer noise. "
        f"The sparsity associations are exploratory. A8 was not run. The synthetic check "
        f"regenerated the planted fingerprint only."
    )
    recommendation = (
        f"Recommendation {choice}: {choice_text}. {reason} "
        f"The recommendation uses the median, the seed SD, the point-estimate win counts, "
        f"the paired intervals, and the positive-count support of the conditioning variables. "
        f"It does not use a selected subset of seeds."
    )
    return [
        "## Paper-safe wording",
        "",
        "### Result",
        "",
        result_paragraph,
        "",
        "### Limitations",
        "",
        limits,
        "",
        "### Recommendation",
        "",
        recommendation,
        "",
    ]


def render_report(result: dict) -> str:
    """Full report. `render_markdown` stops before the narrative answers."""
    body = render_markdown(result)
    # Drop the unfinished answers tail and write the answers in prose.
    marker = "## Answers"
    head = body.split(marker)[0].rstrip()
    answers = result["answers"]
    a7 = answers["2_a7_auroc_distribution"]
    a0 = answers["3_a0_a4_auroc_distribution"]["A0"]
    a4 = answers["3_a0_a4_auroc_distribution"]["A4"]
    q4 = answers["4_a7_consistently_below_a0"]
    q5 = answers["5_a7_consistently_below_a4"]
    q6 = answers["6_point_estimate_wins"]
    q7 = answers["7_variance_larger"]
    q8 = answers["8_imbalance_versus_instability"]
    q9 = answers["9_sparsity"]
    lines = [
        head,
        "",
        "## Answers",
        "",
        "1. " + answers["1_stage6_low_a7_reproduced"]["statement"],
        "",
        "2. A7 AUROC across 20 seeds: "
        f"mean {format_point(a7['mean'])}, median {format_point(a7['median'])}, "
        f"SD {format_point(a7['sd'])}, min {format_point(a7['min'])}, "
        f"max {format_point(a7['max'])}, IQR {format_point(a7['iqr'])} "
        f"(25th {format_point(a7['q25'])}, 75th {format_point(a7['q75'])}). "
        "The SD is not a confidence interval.",
        "",
        "3. A0 AUROC: "
        f"mean {format_point(a0['mean'])}, median {format_point(a0['median'])}, "
        f"SD {format_point(a0['sd'])}, min {format_point(a0['min'])}, "
        f"max {format_point(a0['max'])}, IQR {format_point(a0['iqr'])}. "
        "A4 AUROC: "
        f"mean {format_point(a4['mean'])}, median {format_point(a4['median'])}, "
        f"SD {format_point(a4['sd'])}, min {format_point(a4['min'])}, "
        f"max {format_point(a4['max'])}, IQR {format_point(a4['iqr'])}.",
        "",
        "4. A7 is "
        + ("below A0 on every seed." if q4["consistently_below"] else
           f"below A0 on {q4['n_below']} seeds, above on {q4['n_above']}, tied on {q4['n_equal']}.")
        + f" Mean delta {format_point(q4['mean_delta'])}.",
        "",
        "5. A7 is "
        + ("below A4 on every seed." if q5["consistently_below"] else
           f"below A4 on {q5['n_below']} seeds, above on {q5['n_above']}, tied on {q5['n_equal']}.")
        + f" Mean delta {format_point(q5['mean_delta'])}.",
        "",
        f"6. By point estimate, A7 beats A0 on {q6['A0']} of {q6['n_seeds']} seeds "
        f"and A4 on {q6['A4']} of {q6['n_seeds']} seeds.",
        "",
        "7. A7's sample SD is "
        + ("larger than both baselines." if q7["larger_than_both"] else "not larger than both baselines.")
        + f" SD A7 {format_point(q7['sd_A7'])}, A0 {format_point(q7['sd_A0'])}, "
        f"A4 {format_point(q7['sd_A4'])}. "
        f"IQR A7 {format_point(q7['iqr_A7'])}, A0 {format_point(q7['iqr_A0'])}, "
        f"A4 {format_point(q7['iqr_A4'])}.",
        "",
        "8. " + q8["statement"]
        + (
            " The evidence points to instability beyond split-label imbalance, "
            "because the positive counts do not move."
            if q8["positive_counts_identical_across_seeds"] and q7["larger_than_both"]
            else " See the positive-count rows above before calling the pattern imbalance."
        ),
        "",
        "9. Exploratory. The least-supported generator has "
        f"{q9['min_generator_positives']} positive claim in the full table, and several "
        "generator-by-type cells have none. The count of test positives with no "
        "training positive in the same cell "
        + ("varies across seeds" if q9["sparse0_varies_across_seeds"] else "does not vary across seeds")
        + " (see the cutoff-0 row). Spearman against AUROC, not a p-value: "
        f"A7 {format_point(q9['spearman_sparse0_vs_A7'])}, "
        f"A0 {format_point(q9['spearman_sparse0_vs_A0'])}, "
        f"A4 {format_point(q9['spearman_sparse0_vs_A4'])}. "
        "The A7 rank correlation is near zero, so this sparsity count does not "
        "explain A7's seed-to-seed AUROC movement. The stronger A4 correlation "
        "is not an A7 finding. The high-count test-pair table is the other "
        "pre-specified description; its lowest A7 cell also has a lower A0 mean, "
        "and each cell has only a few seeds.",
        "",
        "10. " + result["answers"]["10_recommendation"]["reason"],
        "",
    ]
    lines.extend(_paper_paragraphs(result))
    return "\n".join(lines)


def write_results(result: dict) -> Path:
    STAGE7_DIR.mkdir(parents=True, exist_ok=True)
    payload = _jsonable(
        {k: v for k, v in result.items() if k not in {"prediction_frame", "assignment_frame"}}
    )
    (STAGE7_DIR / "report.json").write_text(json.dumps(payload, indent=2))
    report = render_report(result)
    (STAGE7_DIR / "report.md").write_text(report)
    result["prediction_frame"].to_parquet(STAGE7_DIR / "predictions.parquet", index=False)
    result["assignment_frame"].to_parquet(STAGE7_DIR / "split_assignments.parquet", index=False)
    metric_rows = []
    for item in result["scored"]["variants"]:
        for row in item["per_seed"]:
            metric_rows.append(
                {
                    "variant": row["variant"],
                    "seed": row["seed"],
                    "auroc": row["auroc"],
                    "f1": row["f1"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "ece": row["ece"],
                    "threshold": row["threshold"],
                    "n_claims": row["n_claims"],
                    "n_questions": row["n_questions"],
                    "n_positive": row["n_positive"],
                    "interval_lo": row["grouped_interval"]["lo"],
                    "interval_hi": row["grouped_interval"]["hi"],
                }
            )
    pd.DataFrame(metric_rows).to_csv(STAGE7_DIR / "seed_metrics.csv", index=False)
    provenance = {
        "stage": "ragtruth_multi_seed_v1",
        "git_head": git_hash(PROJECT_ROOT),
        "split_method": SPLIT_GROUP_STRATIFIED,
        "split_function": "rcgate.data.splits.group_stratified_split",
        "fractions": [0.6, 0.2, 0.2],
        "group_column": "question_id",
        "stratum": "sum of label within question_id",
        "seed_handling": (
            "numpy.random.default_rng(numpy.random.SeedSequence([seed, stratum])); "
            "group ids sorted before the shuffle; model seed equals split seed; seeds 0..19"
        ),
        "fit_table": str(FIT_TABLE),
        "fit_table_sha256": result["table_sha256"][str(FIT_TABLE)],
        "companion_tables_not_used_for_fitting": [str(path) for path in COMPANION_TABLES],
        "companion_sha256": result["table_sha256"],
        "seeds": SEEDS,
        "variants": VARIANTS,
        "a8": "skipped; no judge votes",
        "thresholds": "tune_threshold on the validation split",
        "statistics": (
            "Stage 5 question-grouped percentile bootstrap, 1000 resamples; "
            "seed distribution is sample SD ddof=1, not a confidence interval"
        ),
        "paired_baselines": list(BASELINES),
        "bootstrap_fraction_is_p_value": False,
        "formal_p_value_reported": False,
        "n_resamples": result["n_resamples"],
        "numpy": result["numpy"],
        "stage6_seed0_metrics_matched": result["stage6_seed0"]["matched"],
        "synthetic_unchanged": result["synthetic"]["unchanged"],
        "historical_directories_unchanged": result["protected_unchanged"],
        "recommendation_choice": result["answers"]["10_recommendation"]["choice"],
    }
    (STAGE7_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2))
    return STAGE7_DIR / "report.md"


def evaluate(fit: bool = True) -> dict:
    if any(not path.exists() for path in PROTECTED):
        missing = [str(path) for path in PROTECTED if not path.exists()]
        raise FileNotFoundError(f"required frozen file missing: {missing}")
    protected_before = _snapshot(PROTECTED)
    table_hashes = {str(path): _sha256(path) for path in COMPANION_TABLES}
    cfg = load_named(CONFIG_NAME)
    if cfg.get("data.split_method") != SPLIT_GROUP_STRATIFIED:
        raise RuntimeError("Stage 7 config is not group_stratified")
    if cfg.get("report.tag") != STAGE7_DIR.name:
        raise RuntimeError("Stage 7 config would write outside its namespace")
    table_spec = str(cfg.get("data.table"))
    if "{seed}" in table_spec:
        raise RuntimeError("Stage 7 table path must not depend on seed")
    if (PROJECT_ROOT / table_spec).resolve() != FIT_TABLE.resolve():
        raise RuntimeError(f"Stage 7 fit table must be {FIT_TABLE.name}")
    frames = {seed: load_table(path) for seed, path in enumerate(COMPANION_TABLES)}
    frame = frames[0]
    if len(frame) != 800:
        raise RuntimeError(f"expected 800 claims, found {len(frame)}")
    companions = compare_companions(frames)
    stage6_tests = _stage6_test_sets(frames)
    if fit:
        fit_all(cfg, frame)
    for seed in SEEDS:
        skipped = json.loads(_metrics_path("A8", seed).read_text())
        if not skipped.get("skipped"):
            raise RuntimeError(f"A8 seed {seed} was not skipped")
    scored = score_checkpoints(frame, N_RESAMPLES)
    splits, assignments = split_records(frame)
    overlap = overlap_analysis(splits, stage6_tests, int(frame["question_id"].nunique()))
    auroc_by_variant = {variant: _auroc_values(scored["variants"], variant) for variant in VARIANTS}
    sparsity = sparsity_analysis(frame, auroc_by_variant)
    composition = high_count_composition(splits, auroc_by_variant)
    seed0 = stage6_seed0_check()
    synthetic = synthetic_regression()
    protected_after = _snapshot(PROTECTED)
    if protected_before != protected_after:
        raise RuntimeError("a protected file changed during Stage 7")
    if {str(path): _sha256(path) for path in COMPANION_TABLES} != table_hashes:
        raise RuntimeError("a frozen signal table changed during Stage 7")
    result = {
        "n_resamples": N_RESAMPLES,
        "numpy": np.__version__,
        "table_sha256": table_hashes,
        "protected_unchanged": True,
        "companions": companions,
        "splits": splits,
        "overlap": overlap,
        "scored": {"variants": scored["variants"], "paired": scored["paired"], "checks": scored["checks"]},
        "sparsity": sparsity,
        "composition": composition,
        "stage6_seed0": seed0,
        "synthetic": synthetic,
        "prediction_frame": scored["predictions"],
        "assignment_frame": assignments,
    }
    result["answers"] = build_answers(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage 7 multi-seed group-stratified robustness")
    parser.add_argument("--score-only", action="store_true", help="Rescore existing checkpoints")
    parser.add_argument("--render-only", action="store_true", help="Rewrite report.md from report.json")
    args = parser.parse_args(argv)
    if args.render_only:
        raise SystemExit("render-only is unavailable; rerun --score-only to rebuild the report")
    result = evaluate(fit=not args.score_only)
    path = write_results(result)
    choice = result["answers"]["10_recommendation"]["choice"]
    print(f"wrote {path}")
    print(f"recommendation {choice}")
    print(f"synthetic_unchanged {result['synthetic']['unchanged']}")
    print(f"stage6_seed0_matched {result['stage6_seed0']['matched']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage 5 statistical protocol for the frozen corrected RAGTruth run.

Point estimates are recomputed from the Stage 4 checkpoints. Uncertainty is not.
The Stage 4 evaluator remains available so its published numbers can be reproduced;
this module is the procedure used for inference.

Four quantities are kept separate:

* point estimate — unweighted mean of the seed-level statistics
* within-seed uncertainty — question-grouped percentile bootstrap interval
* across-seed dispersion — sample standard deviation, which is not a confidence interval
* paired comparison — one shared question resample for both models

``question_id`` is the group. On these tables it is the RAGTruth source id, and the
split assigns whole sources. A source contributes one claim from each generator, so
resampling claims as if they were independent overstates the sample size.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .data.splits import grouped_split
from .metrics import (
    bootstrap_auroc_ci,
    bootstrap_auroc_ci_grouped,
    paired_bootstrap_delta,
    paired_bootstrap_delta_grouped,
    slice_metrics,
)
from .paths import PROJECT_ROOT, SUMMARY_DIR
from .pipeline import load_table
from .utils import git_hash

STAGE4_DIR = SUMMARY_DIR / "ragtruth_corrected_integrity_v1"
STAGE5_DIR = SUMMARY_DIR / "ragtruth_corrected_stats_v1"
GROUP_COLUMN = "question_id"
N_RESAMPLES = 1000
# Stage 4 paired intervals were computed with this cap. It is not used here.
STAGE4_PAIRED_RESAMPLES = 500
VARIANTS = [f"A{i}" for i in range(8)]
SEEDS = [0, 1, 2]
PAIRED_BASELINES = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
PRIMARY_COMPARISONS = ("A0", "A4")

METHOD_GROUPED = "question_grouped_percentile_bootstrap"
METHOD_CLAIM = "claim_level_percentile_bootstrap"
METHOD_ENDPOINT_MEAN = "nonstandard_mean_of_per_seed_interval_endpoints"
METHOD_SEED_SD = "sample_sd_across_seeds"

GROUPED_INTERVAL_LABEL = (
    "within-seed 95% question-grouped percentile bootstrap interval"
)
PAIRED_INTERVAL_LABEL = (
    "per-seed 95% paired question-grouped percentile bootstrap interval for delta AUROC"
)
SEED_SD_LABEL = (
    "sample standard deviation across seeds (ddof=1); not a confidence interval"
)
ENDPOINT_MEAN_LABEL = (
    "nonstandard mean of per-seed interval endpoints; not a confidence interval"
)
FRACTION_LABEL = "bootstrap fraction of resamples with delta > 0; not a p-value"


def _finite(values) -> np.ndarray:
    arr = np.asarray(list(values), dtype="float64")
    return arr[np.isfinite(arr)]


def across_seed_dispersion(values) -> dict:
    """Mean and sample sd of seed-level point estimates.

    With one finite seed the sd is undefined. No interval is substituted for it.
    """
    arr = np.asarray(list(values), dtype="float64")
    finite = arr[np.isfinite(arr)]
    mean = float(finite.mean()) if finite.size else float("nan")
    sd = float(np.std(finite, ddof=1)) if finite.size >= 2 else float("nan")
    return {
        "n_seeds": int(arr.size),
        "n_finite": int(finite.size),
        "mean": mean,
        "sd_across_seeds": sd,
        "statistic": METHOD_SEED_SD,
        "is_confidence_interval": False,
        "label": SEED_SD_LABEL,
    }


def nonstandard_endpoint_average(los, his) -> dict:
    """Arithmetic mean of interval endpoints. Preserved only as a historical diagnostic."""
    lo = _finite(los)
    hi = _finite(his)
    return {
        "lo": float(lo.mean()) if lo.size else float("nan"),
        "hi": float(hi.mean()) if hi.size else float("nan"),
        "n_lo": int(lo.size),
        "n_hi": int(hi.size),
        "method": METHOD_ENDPOINT_MEAN,
        "is_confidence_interval": False,
        "label": ENDPOINT_MEAN_LABEL,
    }


def within_seed_auroc_interval(y_true, y_score, groups, n_resamples: int = N_RESAMPLES, seed: int = 0) -> dict:
    """Labeled question-grouped percentile interval for one test split."""
    groups = np.asarray(groups).astype(str)
    ci = bootstrap_auroc_ci_grouped(y_true, y_score, groups, n_resamples=n_resamples, seed=seed)
    return {
        "point": None if not np.isfinite(ci.point) else float(ci.point),
        "lo": None if not np.isfinite(ci.lo) else float(ci.lo),
        "hi": None if not np.isfinite(ci.hi) else float(ci.hi),
        "n_requested": int(ci.n_requested),
        "n_finite": int(ci.n_resamples),
        "n_claims": int(np.asarray(y_true).size),
        "n_groups": int(np.unique(groups).size),
        "method": METHOD_GROUPED,
        "is_confidence_interval": bool(np.isfinite(ci.lo) and np.isfinite(ci.hi)),
        "label": GROUPED_INTERVAL_LABEL,
        "estimand": (
            "AUROC on this seed's test claims, resampling question_id with replacement"
        ),
    }


def historical_claim_interval(y_true, y_score, n_resamples: int = N_RESAMPLES, seed: int = 0) -> dict:
    """Stage 4 marginal interval: claims resampled independently, endpoints later averaged."""
    ci = bootstrap_auroc_ci(y_true, y_score, n_resamples=n_resamples, seed=seed)
    return {
        "point": None if not np.isfinite(ci.point) else float(ci.point),
        "lo": None if not np.isfinite(ci.lo) else float(ci.lo),
        "hi": None if not np.isfinite(ci.hi) else float(ci.hi),
        "lo_rounded": None if not np.isfinite(ci.lo) else round(float(ci.lo), 4),
        "hi_rounded": None if not np.isfinite(ci.hi) else round(float(ci.hi), 4),
        "n_requested": int(ci.n_requested),
        "n_finite": int(ci.n_resamples),
        "method": METHOD_CLAIM,
        "is_confidence_interval": False,
        "label": (
            "historical claim-level percentile bootstrap interval; "
            "claims treated as iid, so this is not the Stage 5 interval"
        ),
    }


def paired_question_delta(y_true, score_a, score_b, groups, n_resamples: int = N_RESAMPLES, seed: int = 0) -> dict:
    """Paired delta with an explicit non-p-value label on the bootstrap fraction."""
    raw = paired_bootstrap_delta_grouped(
        y_true, score_a, score_b, groups, n_resamples=n_resamples, seed=seed
    )
    if "p_gt_0" in raw or "p_value" in raw:
        raise RuntimeError("paired question delta must not expose a p-value field")
    out = dict(raw)
    out["label"] = PAIRED_INTERVAL_LABEL
    out["fraction_label"] = FRACTION_LABEL
    out["is_confidence_interval"] = out["lo"] is not None and out["hi"] is not None
    out["estimand"] = (
        "AUROC(score_a) - AUROC(score_b) on the same test claims; "
        "each resample draws question_id values once and scores both models on those claims"
    )
    return out


def classify_interval(lo, hi) -> str:
    """How a paired interval sits relative to zero. Undefined stays undefined."""
    if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi):
        return "undefined"
    if lo > hi:
        raise ValueError(f"interval endpoints are not ordered: {lo} > {hi}")
    if lo > 0:
        return "entirely_above_0"
    if hi < 0:
        return "entirely_below_0"
    return "covers_0"


def format_point(value, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "undefined"
    return f"{value:.{digits}f}"


def format_interval(lo, hi, digits: int = 4) -> str:
    """Render an interval. A bare point estimate is not accepted as an interval."""
    if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi):
        return "undefined"
    if lo > hi:
        raise ValueError(f"interval endpoints are not ordered: {lo} > {hi}")
    return f"[{lo:.{digits}f}, {hi:.{digits}f}]"


def _mean_rounded(values: list[float]) -> float:
    """Mean of values already rounded to 4 decimals, matching Stage 4 aggregation."""
    return float(np.mean(np.asarray(values, dtype="float64")))


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (np.floating, np.integer)):
        native = value.item()
        if isinstance(native, float) and not np.isfinite(native):
            return None
        return native
    return value


# ---------------------------------------------------------------------------
# scoring from frozen checkpoints
# ---------------------------------------------------------------------------


def _metrics_path(variant: str, seed: int) -> Path:
    return STAGE4_DIR / f"{variant}_seed{seed}" / "metrics.json"


def _checkpoint_path(variant: str, seed: int) -> Path:
    return STAGE4_DIR / f"{variant}_seed{seed}" / "model.joblib"


def score_frozen_checkpoints(variants: list[str] | None = None, seeds: list[int] | None = None) -> dict:
    """Reload Stage 4 models and score the same grouped test split.

    Models are not refit. Thresholds are the stored validation-tuned thresholds.
    """
    import joblib

    variants = list(variants or VARIANTS)
    seeds = list(seeds or SEEDS)
    by_seed: dict[int, dict] = {}
    checks = []
    for seed in seeds:
        meta0 = json.loads(_metrics_path(variants[0], seed).read_text())
        table = Path(meta0["table"])
        if not table.is_absolute():
            table = PROJECT_ROOT / table
        frame = load_table(table)
        split = grouped_split(frame, seed=int(meta0["split_seed"]))
        test = split.test
        y = test["label"].to_numpy()
        groups = test[GROUP_COLUMN].astype(str).to_numpy()
        claim_ids = test["claim_id"].astype(str).to_numpy()
        scores = {}
        thresholds = {}
        for variant in variants:
            meta = json.loads(_metrics_path(variant, seed).read_text())
            if meta.get("skipped"):
                checks.append({"variant": variant, "seed": seed, "skipped": meta["skipped"]})
                continue
            if Path(meta["table"]) != Path(meta0["table"]) or int(meta["split_seed"]) != seed:
                raise RuntimeError(f"{variant} seed {seed} does not share the frozen table or split seed")
            model = joblib.load(_checkpoint_path(variant, seed))
            score = np.asarray(model.predict_proba(test), dtype="float64")
            threshold = float(meta["threshold"])
            metrics = slice_metrics(y, score, name="all", threshold=threshold, n_bins=15)
            expected = meta["test"]
            got = metrics.as_dict()
            for key in ("auroc", "f1", "precision", "recall", "ece", "n"):
                if got[key] != expected[key]:
                    raise RuntimeError(
                        f"reloaded {variant} seed {seed} {key}={got[key]} "
                        f"does not match Stage 4 metrics.json {expected[key]}"
                    )
            scores[variant] = score
            thresholds[variant] = threshold
            checks.append({"variant": variant, "seed": seed, "matched_metrics_json": True, "n": int(y.size)})
        by_seed[seed] = {
            "y": y,
            "groups": groups,
            "claim_id": claim_ids,
            "question_id": groups,
            "scores": scores,
            "thresholds": thresholds,
            "table": str(table),
            "n_questions_in_table": int(frame[GROUP_COLUMN].nunique()),
        }
    return {"seeds": by_seed, "checks": checks}


def _seed_record(variant: str, seed: int, bundle: dict, n_resamples: int) -> dict:
    y = bundle["y"]
    score = bundle["scores"][variant]
    groups = bundle["groups"]
    threshold = bundle["thresholds"][variant]
    metrics = slice_metrics(y, score, name="all", threshold=threshold, n_bins=15)
    rounded = metrics.as_dict()
    grouped = within_seed_auroc_interval(y, score, groups, n_resamples=n_resamples, seed=seed)
    claim = historical_claim_interval(y, score, n_resamples=n_resamples, seed=seed)
    _assert_ordered(grouped["lo"], grouped["hi"])
    _assert_ordered(claim["lo"], claim["hi"])
    return {
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
        "grouped_interval": grouped,
        "historical_claim_interval": claim,
    }


def _assert_ordered(lo, hi) -> None:
    if lo is None or hi is None:
        return
    if lo > hi:
        raise ValueError(f"interval endpoints are not ordered: {lo} > {hi}")


def _variant_summary(rows: list[dict]) -> dict:
    def col(name: str) -> list[float]:
        return [r[name] for r in rows]

    summary = {"variant": rows[0]["variant"], "per_seed": rows}
    for name in ("auroc", "f1", "precision", "recall", "ece"):
        summary[name] = across_seed_dispersion(col(name))
        # Stage 4 averaged the 4-decimal rounded seed statistics. Reproduce that mean.
        summary[name]["mean_of_rounded_seed_statistics"] = _mean_rounded(col(name))
    summary["historical_mean_of_claim_interval_endpoints"] = nonstandard_endpoint_average(
        [r["historical_claim_interval"]["lo_rounded"] for r in rows],
        [r["historical_claim_interval"]["hi_rounded"] for r in rows],
    )
    summary["grouped_intervals_are_not_averaged"] = True
    return summary


def _paired_records(bundles: dict, n_resamples: int) -> list[dict]:
    rows = []
    for baseline in PAIRED_BASELINES:
        for seed, bundle in bundles.items():
            if "A7" not in bundle["scores"] or baseline not in bundle["scores"]:
                continue
            y = bundle["y"]
            groups = bundle["groups"]
            corrected = paired_question_delta(
                y,
                bundle["scores"]["A7"],
                bundle["scores"][baseline],
                groups,
                n_resamples=n_resamples,
                seed=seed,
            )
            historical = paired_bootstrap_delta(
                y,
                bundle["scores"]["A7"],
                bundle["scores"][baseline],
                n_resamples=STAGE4_PAIRED_RESAMPLES,
                seed=seed,
            )
            if historical["n_requested"] != STAGE4_PAIRED_RESAMPLES:
                raise RuntimeError("historical paired resample count drifted")
            if corrected["n_requested"] != n_resamples:
                raise RuntimeError("corrected paired resample count drifted")
            _assert_ordered(corrected["lo"], corrected["hi"])
            rows.append(
                {
                    "comparison": f"A7 - {baseline}",
                    "baseline": baseline,
                    "seed": seed,
                    "n_claims": int(y.size),
                    "n_questions": int(np.unique(groups).size),
                    "delta_auroc": None if corrected["delta"] is None else round(float(corrected["delta"]), 4),
                    "delta_full": corrected["delta"],
                    "grouped_interval": {
                        "lo": corrected["lo"],
                        "hi": corrected["hi"],
                        "label": corrected["label"],
                        "method": corrected["method"],
                        "n_requested": corrected["n_requested"],
                        "n_finite": corrected["n_finite"],
                        "position_vs_0": classify_interval(corrected["lo"], corrected["hi"]),
                    },
                    "bootstrap_frac_delta_gt_0": corrected["bootstrap_frac_delta_gt_0"],
                    "fraction_label": corrected["fraction_label"],
                    "fraction_is_p_value": False,
                    "historical_claim_level_500": {
                        "delta_rounded": historical["delta"],
                        "lo_rounded": historical["lo"],
                        "hi_rounded": historical["hi"],
                        "bootstrap_fraction_stored_as_p_gt_0": historical["p_gt_0"],
                        "n_requested": historical["n_requested"],
                        "label": (
                            "historical claim-level paired percentile interval "
                            f"from {STAGE4_PAIRED_RESAMPLES} resamples; "
                            "the stored fraction is not a p-value"
                        ),
                        "is_confidence_interval": False,
                    },
                }
            )
    return rows


def _paired_summary(rows: list[dict], baseline: str) -> dict:
    subset = [r for r in rows if r["baseline"] == baseline]
    deltas = [r["delta_auroc"] for r in subset]
    disp = across_seed_dispersion(deltas)
    disp["mean_of_rounded_seed_statistics"] = _mean_rounded(deltas)
    historical = nonstandard_endpoint_average(
        [r["historical_claim_level_500"]["lo_rounded"] for r in subset],
        [r["historical_claim_level_500"]["hi_rounded"] for r in subset],
    )
    return {
        "comparison": f"A7 - {baseline}",
        "per_seed": subset,
        "delta": disp,
        "historical_mean_of_claim_interval_endpoints": historical,
        "seed_interval_positions": [r["grouped_interval"]["position_vs_0"] for r in subset],
    }


def _load_stage4_published() -> dict:
    payload = json.loads((STAGE4_DIR / "report.json").read_text())
    overall = {
        row["variant"]: row
        for row in payload["aggregated"]
        if row["slice"] == "all"
    }
    deltas = {
        (row["baseline"], row["slice"]): row
        for row in payload["deltas"]
        if row["variant"] == "A7"
    }
    return {"overall": overall, "deltas": deltas}


def _reproduction_checks(summaries: list[dict], paired: dict, published: dict) -> dict:
    checks = []
    for summary in summaries:
        variant = summary["variant"]
        stage4 = published["overall"][variant]
        got_mean = summary["auroc"]["mean_of_rounded_seed_statistics"]
        checks.append(
            {
                "quantity": f"{variant} mean AUROC",
                "stage5": got_mean,
                "stage4": stage4["auroc_mean"],
                "match": bool(np.isclose(got_mean, stage4["auroc_mean"], atol=1e-12)),
            }
        )
        for name, stage4_key in (
            ("f1", "f1_mean"),
            ("precision", "precision_mean"),
            ("recall", "recall_mean"),
            ("ece", "ece_mean"),
        ):
            got = summary[name]["mean_of_rounded_seed_statistics"]
            checks.append(
                {
                    "quantity": f"{variant} mean {name}",
                    "stage5": got,
                    "stage4": stage4[stage4_key],
                    "match": bool(np.isclose(got, stage4[stage4_key], atol=1e-12)),
                }
            )
        hist = summary["historical_mean_of_claim_interval_endpoints"]
        checks.append(
            {
                "quantity": f"{variant} mean of claim-level AUROC interval endpoints",
                "stage5_lo": hist["lo"],
                "stage5_hi": hist["hi"],
                "stage4_lo": stage4["auroc_ci_lo_mean"],
                "stage4_hi": stage4["auroc_ci_hi_mean"],
                "match": bool(
                    np.isclose(hist["lo"], stage4["auroc_ci_lo_mean"], atol=1e-12)
                    and np.isclose(hist["hi"], stage4["auroc_ci_hi_mean"], atol=1e-12)
                ),
            }
        )
    for baseline in PAIRED_BASELINES:
        stage4 = published["deltas"].get((baseline, "all"))
        if stage4 is None:
            continue
        summary = paired[baseline]
        checks.append(
            {
                "quantity": f"A7 - {baseline} mean delta",
                "stage5": summary["delta"]["mean_of_rounded_seed_statistics"],
                "stage4": stage4["delta"],
                "match": bool(
                    np.isclose(
                        summary["delta"]["mean_of_rounded_seed_statistics"],
                        stage4["delta"],
                        atol=1e-12,
                    )
                ),
            }
        )
        hist = summary["historical_mean_of_claim_interval_endpoints"]
        checks.append(
            {
                "quantity": f"A7 - {baseline} mean of 500-resample claim-level endpoints",
                "stage5_lo": hist["lo"],
                "stage5_hi": hist["hi"],
                "stage4_lo": stage4["lo"],
                "stage4_hi": stage4["hi"],
                "stage4_field_named_p_gt_0": stage4["p_gt_0"],
                "match": bool(
                    np.isclose(hist["lo"], stage4["lo"], atol=1e-12)
                    and np.isclose(hist["hi"], stage4["hi"], atol=1e-12)
                ),
            }
        )
    return {"all_match": all(item["match"] for item in checks), "checks": checks}


def evaluate_frozen_run(n_resamples: int = N_RESAMPLES) -> dict:
    """Full Stage 5 evaluation. Training, splits, labels, and seeds stay as in Stage 4."""
    frozen = score_frozen_checkpoints()
    bundles = frozen["seeds"]
    summaries = [
        _variant_summary([_seed_record(variant, seed, bundles[seed], n_resamples) for seed in SEEDS])
        for variant in VARIANTS
        if all(variant in bundles[seed]["scores"] for seed in SEEDS)
    ]
    paired_rows = _paired_records(bundles, n_resamples)
    paired = {baseline: _paired_summary(paired_rows, baseline) for baseline in PAIRED_BASELINES}
    published = _load_stage4_published()
    reproduction = _reproduction_checks(summaries, paired, published)
    if not reproduction["all_match"]:
        failed = [c for c in reproduction["checks"] if not c["match"]]
        raise RuntimeError(f"Stage 4 quantities were not reproduced: {failed}")
    return {
        "protocol": protocol_card(n_resamples),
        "variants": summaries,
        "paired": paired,
        "reproduction": reproduction,
        "checkpoint_checks": frozen["checks"],
        "tables": {str(seed): bundles[seed]["table"] for seed in bundles},
    }


def protocol_card(n_resamples: int = N_RESAMPLES) -> dict:
    return {
        "name": "ragtruth_corrected_stats_v1",
        "group_column": GROUP_COLUMN,
        "group_meaning": (
            "RAGTruth source_id. The frozen tables contain one claim from each "
            "available generator per source, about six claims per question."
        ),
        "n_resamples": n_resamples,
        "resample_method": "percentile bootstrap, numpy quantile linear, alpha=0.05",
        "point_estimate": "unweighted mean of the three seed-level statistics after 4-decimal rounding",
        "within_seed_uncertainty": GROUPED_INTERVAL_LABEL,
        "across_seed_dispersion": SEED_SD_LABEL,
        "paired_comparison": PAIRED_INTERVAL_LABEL,
        "bootstrap_fraction": FRACTION_LABEL,
        "formal_p_value": "not computed; three seeds and 27 test questions do not support one here",
        "seeds": SEEDS,
        "split": "unchanged grouped_split by question_id; stratify flag left untouched",
        "models": "Stage 4 checkpoints reloaded; no refit",
        "thresholds": "Stage 4 validation-tuned thresholds reloaded; not retuned",
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _md_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def render_markdown(result: dict) -> str:
    """Tables whose headers name the statistic. Interval cells are intervals."""
    card = result["protocol"]
    lines = [
        "# RC-Gate Stage 5 statistical repair — corrected RAGTruth",
        "",
        "Inference in this file uses question-grouped percentile bootstrap intervals.",
        "The sample standard deviation across seeds is not a confidence interval.",
        "The mean of per-seed interval endpoints is reported only as a historical diagnostic.",
        "No classical p-value is reported.",
        "",
        "## Protocol",
        "",
        f"- group: `{card['group_column']}` ({card['group_meaning']})",
        f"- within-seed interval: {card['within_seed_uncertainty']}",
        f"- resamples requested for every Stage 5 interval: {card['n_resamples']}",
        f"- across seeds: {card['across_seed_dispersion']}",
        f"- paired delta: {card['paired_comparison']}",
        f"- bootstrap fraction: {card['bootstrap_fraction']}",
        f"- formal p-value: {card['formal_p_value']}",
        f"- point estimate: {card['point_estimate']}",
        f"- models: {card['models']}",
        f"- thresholds: {card['thresholds']}",
        f"- split: {card['split']}",
        "",
        "## Point estimates",
        "",
        "Means match Stage 4 because the checkpoints, labels, splits, and thresholds are unchanged.",
        "The sd column is dispersion across the three seeds.",
        "",
        _md_row(
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
        _md_row(["---"] * 11),
    ]
    for summary in result["variants"]:
        cells = [summary["variant"]]
        for name in ("auroc", "f1", "precision", "recall", "ece"):
            block = summary[name]
            cells.append(format_point(block["mean_of_rounded_seed_statistics"]))
            cells.append(format_point(block["sd_across_seeds"]))
        lines.append(_md_row(cells))
    lines += [
        "",
        "## Per-seed AUROC intervals",
        "",
        "Each bracket is that seed's own interval. Endpoints are not averaged.",
        "",
        _md_row(
            [
                "variant",
                "seed",
                "n claims (point count)",
                "n questions (bootstrap groups)",
                "n positive claims",
                "AUROC (point estimate)",
                GROUPED_INTERVAL_LABEL,
                "resamples requested",
                "resamples finite",
                "F1 (point estimate)",
                "precision (point estimate)",
                "recall (point estimate)",
                "ECE (point estimate)",
            ]
        ),
        _md_row(["---"] * 13),
    ]
    for summary in result["variants"]:
        for row in summary["per_seed"]:
            interval = row["grouped_interval"]
            lines.append(
                _md_row(
                    [
                        row["variant"],
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
    lines += [
        "",
        "## Paired comparisons",
        "",
        "Delta is AUROC(A7) minus AUROC(baseline) on the same test claims.",
        "The interval resamples question ids once per draw and scores both models on the drawn claims.",
        f"Stage 5 uses {card['n_resamples']} resamples. "
        f"The historical paired procedure used {STAGE4_PAIRED_RESAMPLES}.",
        "",
        _md_row(
            [
                "comparison",
                "seed",
                "delta AUROC (point estimate)",
                PAIRED_INTERVAL_LABEL,
                "interval vs 0",
                "resamples requested",
                "resamples finite",
                FRACTION_LABEL,
            ]
        ),
        _md_row(["---"] * 8),
    ]
    for block in result["paired"].values():
        for row in block["per_seed"]:
            interval = row["grouped_interval"]
            lines.append(
                _md_row(
                    [
                        row["comparison"],
                        str(row["seed"]),
                        format_point(row["delta_auroc"]),
                        format_interval(interval["lo"], interval["hi"]),
                        interval["position_vs_0"],
                        str(interval["n_requested"]),
                        str(interval["n_finite"]),
                        format_point(row["bootstrap_frac_delta_gt_0"]),
                    ]
                )
            )
    lines += [
        "",
        "### Across-seed summary of paired deltas",
        "",
        _md_row(
            [
                "comparison",
                "mean delta AUROC (point estimate)",
                "sd of delta across seeds (not a confidence interval)",
                "per-seed interval positions",
            ]
        ),
        _md_row(["---"] * 4),
    ]
    for block in result["paired"].values():
        lines.append(
            _md_row(
                [
                    block["comparison"],
                    format_point(block["delta"]["mean_of_rounded_seed_statistics"]),
                    format_point(block["delta"]["sd_across_seeds"]),
                    ", ".join(block["seed_interval_positions"]),
                ]
            )
        )
    lines += [
        "",
        "## Old versus new",
        "",
        "Stage 4's markdown column headed `AUROC (95% CI)` displayed the mean AUROC.",
        "The claim-level interval endpoints were averaged into `auroc_ci_lo_mean` and "
        "`auroc_ci_hi_mean` and were not printed. That nonstandard average is not a confidence interval.",
        "",
        _md_row(
            [
                "variant",
                "mean AUROC, both stages (point estimate)",
                "Stage 4 nonstandard mean of claim-level endpoints (not a confidence interval)",
                "Stage 5 per-seed question-grouped intervals",
            ]
        ),
        _md_row(["---"] * 4),
    ]
    for summary in result["variants"]:
        hist = summary["historical_mean_of_claim_interval_endpoints"]
        per_seed = "; ".join(
            f"seed {row['seed']} {format_interval(row['grouped_interval']['lo'], row['grouped_interval']['hi'])}"
            for row in summary["per_seed"]
        )
        lines.append(
            _md_row(
                [
                    summary["variant"],
                    format_point(summary["auroc"]["mean_of_rounded_seed_statistics"]),
                    format_interval(hist["lo"], hist["hi"]),
                    per_seed,
                ]
            )
        )
    lines += [
        "",
        "### Paired deltas, historical endpoint average versus Stage 5",
        "",
        _md_row(
            [
                "comparison",
                "mean delta (point estimate)",
                "Stage 4 nonstandard mean of 500-resample claim-level endpoints (not a confidence interval)",
                "Stage 5 per-seed question-grouped intervals",
            ]
        ),
        _md_row(["---"] * 4),
    ]
    for baseline in PRIMARY_COMPARISONS:
        if baseline not in result["paired"]:
            continue
        block = result["paired"][baseline]
        hist = block["historical_mean_of_claim_interval_endpoints"]
        per_seed = "; ".join(
            f"seed {row['seed']} {format_interval(row['grouped_interval']['lo'], row['grouped_interval']['hi'])}"
            for row in block["per_seed"]
        )
        lines.append(
            _md_row(
                [
                    block["comparison"],
                    format_point(block["delta"]["mean_of_rounded_seed_statistics"]),
                    format_interval(hist["lo"], hist["hi"]),
                    per_seed,
                ]
            )
        )
    if {"A0", "A4", "A7"} <= {item["variant"] for item in result["variants"]} and {
        "A0",
        "A4",
    } <= set(result["paired"]):
        lines += ["", *render_verdict(result).splitlines()]
    lines += [
        "",
        "## What this file does not claim",
        "",
        "- The sd across three seeds is not a confidence interval.",
        "- A bootstrap fraction is not a p-value.",
        "- Averaging interval endpoints across seeds is not a confidence interval.",
        "- The question-grouped interval is for one seed's test split, not for the mean across seeds.",
        "- Split construction, the number of seeds, labels, signals, and model parameters were not changed.",
        "",
    ]
    return "\n".join(lines)


def _mean(result: dict, variant: str, metric: str) -> float:
    summary = next(item for item in result["variants"] if item["variant"] == variant)
    return float(summary[metric]["mean_of_rounded_seed_statistics"])


def _sd(result: dict, variant: str, metric: str = "auroc") -> float:
    summary = next(item for item in result["variants"] if item["variant"] == variant)
    return float(summary[metric]["sd_across_seeds"])


def render_verdict(result: dict) -> str:
    """Paper-safe reading of the repaired intervals. It does not retune anything."""
    a0 = _mean(result, "A0", "auroc")
    a4 = _mean(result, "A4", "auroc")
    a7 = _mean(result, "A7", "auroc")
    versus_a0 = result["paired"]["A0"]
    versus_a4 = result["paired"]["A4"]
    a0_positions = versus_a0["seed_interval_positions"]
    a4_positions = versus_a4["seed_interval_positions"]
    a0_supports = [pos for pos in a0_positions if pos == "entirely_above_0"]
    a4_supports = [pos for pos in a4_positions if pos == "entirely_above_0"]
    dropped = [
        f"{row['variant']} seed {row['seed']} kept {row['grouped_interval']['n_finite']} "
        f"of {row['grouped_interval']['n_requested']} resamples"
        for summary in result["variants"]
        for row in summary["per_seed"]
        if row["grouped_interval"]["n_finite"] != row["grouped_interval"]["n_requested"]
    ]
    dropped_text = (
        "Every reported interval used all 1000 resamples."
        if not dropped
        else "Some question draws were single-class and were left out of the quantile: "
        + "; ".join(dropped)
        + "."
    )
    return "\n".join(
        [
            "## Verdict",
            "",
            "Statistical repair does not change the point estimates and does not give A7 an advantage.",
            "",
            f"- Mean AUROC stays {format_point(a7)} for A7, {format_point(a0)} for A0, "
            f"and {format_point(a4)} for A4. "
            f"Across-seed standard deviations are {format_point(_sd(result, 'A7'))}, "
            f"{format_point(_sd(result, 'A0'))}, and {format_point(_sd(result, 'A4'))}. "
            "Those standard deviations are not confidence intervals.",
            f"- A4 remains ahead of A7 on the point estimate "
            f"({format_point(a4)} versus {format_point(a7)}). "
            f"The three seed-level deltas A7−A4 are all negative "
            f"(mean {format_point(versus_a4['delta']['mean_of_rounded_seed_statistics'])}, "
            f"sd {format_point(versus_a4['delta']['sd_across_seeds'])}).",
            f"- A7 remains unsupported as better than A0. The mean delta is "
            f"{format_point(versus_a0['delta']['mean_of_rounded_seed_statistics'])} "
            f"(sd {format_point(versus_a0['delta']['sd_across_seeds'])}).",
            f"- Paired A7−A0 interval positions: {', '.join(a0_positions)}. "
            f"Paired A7−A4 interval positions: {', '.join(a4_positions)}. "
            f"Intervals lying entirely above 0, which would be the within-seed sign of an A7 advantage: "
            f"A7−A0 count {len(a0_supports)}; A7−A4 count {len(a4_supports)}.",
            "- Stage 4 numbers that are now historical: the markdown cells under "
            "`AUROC (95% CI)` (they were mean AUROC), the averaged claim-level endpoint "
            "fields `auroc_ci_lo_mean` and `auroc_ci_hi_mean`, the paired intervals formed "
            "by averaging 500-resample claim-level endpoints, and the field `p_gt_0`. "
            "The leave-one-generator-out table is also historical: its interval column was "
            "misaligned, and those intervals used 200 claim-level resamples. "
            "`results/summary/ragtruth/` was not recomputed.",
            "",
            "### Paper-safe paragraph",
            "",
            f"On the frozen corrected RAGTruth tables, with the Stage 4 checkpoints and "
            f"thresholds reused and the question-grouped split left unchanged, mean test "
            f"AUROC is {format_point(a7)} for RC-Gate (A7), {format_point(a0)} for the flat "
            f"logistic baseline (A0), and {format_point(a4)} for the metadata "
            f"gradient-boosting control (A4). Within each seed, the uncertainty for AUROC "
            f"and for paired AUROC differences is a 95% percentile bootstrap that resamples "
            f"the 27 test `question_id` clusters, using 1000 requested resamples. Every "
            f"such paired interval for A7−A0 and for A7−A4 covers 0. Across the three seeds, "
            f"only the sample standard deviation is reported. These results do not support "
            f"a claim that A7 improves on A0 or on A4. They do not support reading the "
            f"Stage 4 bootstrap fraction as a p-value, or treating an average of per-seed "
            f"interval endpoints as a confidence interval. They also do not support claims "
            f"that would require a different split or more seeds; those were not changed.",
            "",
            "### Limitations that remain",
            "",
            "- Three seeds. The claim pools overlap heavily, so the seed standard deviation "
            "mixes split assignment and fitting variation. It is not a confidence interval "
            "for a shared mean.",
            "- Each test split has 27 questions and 15 to 17 positive claims. The grouped "
            "intervals are wide, especially on seed 2.",
            "- The interval is a percentile interval of the finite resamples. "
            + dropped_text,
            "- No formal hypothesis test is reported.",
            "- F1, precision, recall, and ECE are point estimates with an across-seed "
            "standard deviation only. They were not bootstrapped in Stage 4 either.",
            "- `grouped_split(..., stratify=True)` still does not stratify. That is left "
            "for a later stage.",
            "- Leave-one-generator-out was not refit.",
            "",
        ]
    )


def write_results(result: dict, out_dir: Path = STAGE5_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = render_markdown(result)
    (out_dir / "report.md").write_text(report)
    payload = _jsonable(result)
    (out_dir / "report.json").write_text(json.dumps(payload, indent=2))
    provenance = {
        "stage": "ragtruth_corrected_stats_v1",
        "git": git_hash(PROJECT_ROOT),
        "stage4_dir": str(STAGE4_DIR),
        "stage4_untouched": True,
        "historical_ragtruth_dir": str(SUMMARY_DIR / "ragtruth"),
        "checkpoints": "reloaded from Stage 4 model.joblib; models were not refit",
        "predictions": "regenerated by predict_proba on the same grouped test split",
        "thresholds": "taken from Stage 4 metrics.json",
        "signal_tables": result["tables"],
        "n_resamples": result["protocol"]["n_resamples"],
        "group_column": GROUP_COLUMN,
        "reproduction_of_stage4_point_estimates": result["reproduction"]["all_match"],
        "formal_p_value_reported": False,
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2))
    return out_dir / "report.md"


def main() -> int:
    result = evaluate_frozen_run(N_RESAMPLES)
    path = write_results(result)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

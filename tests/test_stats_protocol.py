"""Stage 5 statistical protocol: grouping, labels, and degenerate samples."""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from rcgate.evaluate import _deltas
from rcgate.metrics import (
    auroc,
    auroc_fast,
    bootstrap_auroc_ci_grouped,
    paired_bootstrap_delta_grouped,
)
from rcgate.stats_protocol import (
    FRACTION_LABEL,
    GROUPED_INTERVAL_LABEL,
    N_RESAMPLES,
    PAIRED_INTERVAL_LABEL,
    SEED_SD_LABEL,
    STAGE4_PAIRED_RESAMPLES,
    across_seed_dispersion,
    classify_interval,
    format_interval,
    historical_claim_interval,
    nonstandard_endpoint_average,
    paired_question_delta,
    render_markdown,
    within_seed_auroc_interval,
)


def _clustered(seed: int = 0):
    """Every question contains both classes, so a group draw stays two-class."""
    rng = np.random.default_rng(seed)
    groups = np.repeat([f"q{i}" for i in range(8)], 4)
    y = np.tile(np.array([0, 0, 1, 1]), 8)
    score = y.astype(float) * 0.15 + rng.random(y.size) * 0.85
    return y, score, groups


def test_grouped_interval_reproducible_and_requests_the_full_resample_count():
    y, score, groups = _clustered()
    first = within_seed_auroc_interval(y, score, groups, n_resamples=N_RESAMPLES, seed=11)
    second = within_seed_auroc_interval(y, score, groups, n_resamples=N_RESAMPLES, seed=11)
    assert first == second
    assert first["n_requested"] == N_RESAMPLES
    assert first["n_finite"] == N_RESAMPLES
    assert first["n_requested"] != STAGE4_PAIRED_RESAMPLES
    assert first["lo"] <= first["hi"]


def test_grouped_bootstrap_draws_whole_questions_not_claims():
    y = np.array([0, 0, 0, 1, 1, 1, 0, 1])
    score = np.array([0.1, 0.2, 0.15, 0.9, 0.8, 0.7, 0.4, 0.95])
    groups = np.array(["q0", "q0", "q0", "q1", "q1", "q1", "q2", "q2"])
    out = bootstrap_auroc_ci_grouped(y, score, groups, n_resamples=1, seed=0)
    rng = np.random.default_rng(0)
    unique = np.unique(groups)
    picks = rng.integers(0, unique.size, unique.size)
    idx = np.concatenate([np.flatnonzero(groups == unique[p]) for p in picks])
    expected = auroc_fast(y[idx], score[idx])
    assert len(idx) == sum(int((groups == unique[p]).sum()) for p in picks)
    assert out.lo == pytest.approx(expected)
    assert out.hi == pytest.approx(expected)
    assert out.n_requested == 1
    # A claim resample of size 1 is not what this draw does.
    assert len(idx) != 1


def test_grouped_interval_is_invariant_to_row_order_and_claim_interval_is_not():
    y, score, groups = _clustered(seed=2)
    perm = np.random.default_rng(1).permutation(y.size)
    grouped = within_seed_auroc_interval(y, score, groups, n_resamples=40, seed=3)
    grouped_perm = within_seed_auroc_interval(
        y[perm], score[perm], groups[perm], n_resamples=40, seed=3
    )
    assert grouped["lo"] == pytest.approx(grouped_perm["lo"])
    assert grouped["hi"] == pytest.approx(grouped_perm["hi"])

    claim = historical_claim_interval(y, score, n_resamples=40, seed=3)
    claim_perm = historical_claim_interval(y[perm], score[perm], n_resamples=40, seed=3)
    assert (claim["lo"], claim["hi"]) != (claim_perm["lo"], claim_perm["hi"])


def test_paired_bootstrap_uses_the_same_rows_for_both_models():
    y, score_a, groups = _clustered(seed=4)
    score_b = np.clip(score_a - 0.15, 0, 1)
    out = paired_bootstrap_delta_grouped(y, score_a, score_b, groups, n_resamples=1, seed=5)
    rng = np.random.default_rng(5)
    unique = np.unique(groups)
    picks = rng.integers(0, unique.size, unique.size)
    idx = np.concatenate([np.flatnonzero(groups == unique[p]) for p in picks])
    expected = auroc_fast(y[idx], score_a[idx]) - auroc_fast(y[idx], score_b[idx])
    assert out["lo"] == pytest.approx(expected)
    assert out["hi"] == pytest.approx(expected)
    assert out["n_requested"] == 1

    swapped = score_b.copy()
    swapped[0], swapped[-1] = swapped[-1], swapped[0]
    misaligned = paired_bootstrap_delta_grouped(y, score_a, swapped, groups, n_resamples=1, seed=5)
    assert misaligned["lo"] != pytest.approx(expected)


def test_paired_question_delta_requests_1000_and_hides_p_gt_0():
    y, score_a, groups = _clustered(seed=6)
    score_b = np.clip(score_a - 0.1, 0, 1)
    out = paired_question_delta(y, score_a, score_b, groups, n_resamples=N_RESAMPLES, seed=0)
    assert out["n_requested"] == N_RESAMPLES
    assert out["n_finite"] == N_RESAMPLES
    assert out["lo"] <= out["hi"]
    assert "p_gt_0" not in out
    assert "p_value" not in out
    assert out["fraction_is_p_value"] is False
    assert out["fraction_label"] == FRACTION_LABEL
    assert "not a p-value" in out["fraction_label"]
    assert out["method"] == "question_grouped_percentile_bootstrap"
    assert "question-grouped" in out["label"]


def test_labels_match_the_calculation_they_describe():
    y, score, groups = _clustered()
    grouped = within_seed_auroc_interval(y, score, groups, n_resamples=25, seed=0)
    claim = historical_claim_interval(y, score, n_resamples=25, seed=0)
    assert grouped["method"] == "question_grouped_percentile_bootstrap"
    assert grouped["label"] == GROUPED_INTERVAL_LABEL
    assert "question-grouped" in grouped["label"]
    assert claim["method"] == "claim_level_percentile_bootstrap"
    assert "claim-level" in claim["label"]
    assert "question-grouped" not in claim["label"]
    assert claim["is_confidence_interval"] is False


def test_endpoint_average_is_marked_nonstandard_and_ordered():
    diagnostic = nonstandard_endpoint_average([0.10, 0.30], [0.20, 0.50])
    assert diagnostic["lo"] == pytest.approx(0.20)
    assert diagnostic["hi"] == pytest.approx(0.35)
    assert diagnostic["lo"] <= diagnostic["hi"]
    assert diagnostic["is_confidence_interval"] is False
    assert "nonstandard" in diagnostic["label"]
    assert "not a confidence interval" in diagnostic["label"]


def test_single_seed_dispersion_has_no_interval():
    summary = across_seed_dispersion([0.62])
    assert summary["n_finite"] == 1
    assert summary["mean"] == pytest.approx(0.62)
    assert np.isnan(summary["sd_across_seeds"])
    assert summary["is_confidence_interval"] is False
    assert summary["label"] == SEED_SD_LABEL
    assert "not a confidence interval" in summary["label"]


def test_single_group_and_single_class_intervals_are_undefined():
    y = np.array([0, 1, 0, 1, 1, 0])
    score = np.array([0.2, 0.8, 0.1, 0.7, 0.9, 0.3])
    one_group = np.array(["only"] * y.size)
    grouped = within_seed_auroc_interval(y, score, one_group, n_resamples=30, seed=0)
    assert grouped["point"] == pytest.approx(auroc(y, score))
    assert grouped["lo"] is None and grouped["hi"] is None
    assert grouped["n_finite"] == 0
    assert grouped["n_groups"] == 1
    assert grouped["is_confidence_interval"] is False

    y0 = np.zeros(12, dtype=int)
    groups = np.repeat(["a", "b", "c"], 4)
    empty = within_seed_auroc_interval(y0, np.linspace(0, 1, 12), groups, n_resamples=30, seed=0)
    assert empty["point"] is None
    assert empty["lo"] is None and empty["hi"] is None
    assert empty["n_finite"] == 0

    paired = paired_question_delta(y0, np.linspace(0, 1, 12), np.linspace(1, 0, 12), groups, n_resamples=30, seed=1)
    assert paired["delta"] is None
    assert paired["lo"] is None and paired["hi"] is None
    assert paired["bootstrap_frac_delta_gt_0"] is None
    assert "p_gt_0" not in paired


def test_format_interval_rejects_reversed_endpoints_and_classify_covers_zero():
    assert format_interval(0.1, 0.4) == "[0.1000, 0.4000]"
    with pytest.raises(ValueError):
        format_interval(0.4, 0.1)
    assert classify_interval(0.1, 0.2) == "entirely_above_0"
    assert classify_interval(-0.3, -0.1) == "entirely_below_0"
    assert classify_interval(-0.2, 0.1) == "covers_0"
    assert classify_interval(None, 0.1) == "undefined"


def test_markdown_uncertainty_columns_are_labeled_and_are_not_point_estimates():
    y, score, groups = _clustered(seed=8)
    interval = within_seed_auroc_interval(y, score, groups, n_resamples=40, seed=1)
    paired = paired_question_delta(y, score, np.clip(score - 0.2, 0, 1), groups, n_resamples=40, seed=1)
    seed_row = {
        "variant": "A7",
        "seed": 0,
        "n_claims": int(y.size),
        "n_questions": int(np.unique(groups).size),
        "n_positive": int(y.sum()),
        "threshold": 0.5,
        "auroc": 0.7,
        "f1": 0.4,
        "precision": 0.3,
        "recall": 0.6,
        "ece": 0.05,
        "grouped_interval": interval,
        "historical_claim_interval": historical_claim_interval(y, score, n_resamples=40, seed=1),
    }
    summary = {
        "variant": "A7",
        "per_seed": [seed_row],
        "auroc": {**across_seed_dispersion([0.7, 0.6, 0.5]), "mean_of_rounded_seed_statistics": 0.6},
        "f1": {**across_seed_dispersion([0.4, 0.4, 0.4]), "mean_of_rounded_seed_statistics": 0.4},
        "precision": {**across_seed_dispersion([0.3, 0.3, 0.3]), "mean_of_rounded_seed_statistics": 0.3},
        "recall": {**across_seed_dispersion([0.6, 0.6, 0.6]), "mean_of_rounded_seed_statistics": 0.6},
        "ece": {**across_seed_dispersion([0.05, 0.05, 0.05]), "mean_of_rounded_seed_statistics": 0.05},
        "historical_mean_of_claim_interval_endpoints": nonstandard_endpoint_average([0.4], [0.8]),
    }
    paired_row = {
        "comparison": "A7 - A0",
        "baseline": "A0",
        "seed": 0,
        "delta_auroc": round(paired["delta"], 4),
        "grouped_interval": {
            "lo": paired["lo"],
            "hi": paired["hi"],
            "label": paired["label"],
            "method": paired["method"],
            "n_requested": paired["n_requested"],
            "n_finite": paired["n_finite"],
            "position_vs_0": classify_interval(paired["lo"], paired["hi"]),
        },
        "bootstrap_frac_delta_gt_0": paired["bootstrap_frac_delta_gt_0"],
        "fraction_label": paired["fraction_label"],
    }
    text = render_markdown(
        {
            "protocol": {
                "group_column": "question_id",
                "group_meaning": "source",
                "within_seed_uncertainty": GROUPED_INTERVAL_LABEL,
                "n_resamples": 40,
                "across_seed_dispersion": SEED_SD_LABEL,
                "paired_comparison": PAIRED_INTERVAL_LABEL,
                "bootstrap_fraction": FRACTION_LABEL,
                "formal_p_value": "not computed",
                "point_estimate": "mean of seed statistics",
                "models": "reloaded",
                "thresholds": "stored",
                "split": "unchanged",
            },
            "variants": [summary],
            "paired": {
                "A0": {
                    "comparison": "A7 - A0",
                    "per_seed": [paired_row],
                    "delta": {
                        **across_seed_dispersion([paired_row["delta_auroc"]]),
                        "mean_of_rounded_seed_statistics": paired_row["delta_auroc"],
                    },
                    "historical_mean_of_claim_interval_endpoints": nonstandard_endpoint_average(
                        [-0.2], [0.1]
                    ),
                    "seed_interval_positions": [paired_row["grouped_interval"]["position_vs_0"]],
                }
            },
        }
    )
    assert "p_gt_0" not in text
    assert "not a p-value" in text
    assert "not a confidence interval" in text
    assert "nonstandard" in text
    assert "question-grouped percentile bootstrap interval" in text
    assert "| p-value |" not in text
    assert "| 95% CI |" not in text
    # The interval cell is a bracketed range, not the bare point estimate.
    rendered_interval = format_interval(interval["lo"], interval["hi"])
    assert rendered_interval in text
    assert rendered_interval != format_point_guard(interval["point"])


def format_point_guard(value: float) -> str:
    return f"{value:.4f}"


def test_historical_evaluator_still_caps_paired_resamples_at_500():
    """The Stage 4 path is unchanged so its published intervals stay reproducible."""
    assert "min(n_bootstrap, 500)" in inspect.getsource(_deltas)


def test_mismatched_paired_inputs_raise():
    y = np.array([0, 1, 0, 1])
    with pytest.raises(ValueError):
        paired_bootstrap_delta_grouped(y, np.array([0.1, 0.2]), np.array([0.2, 0.3, 0.4, 0.5]), np.array(["a", "a", "b", "b"]))

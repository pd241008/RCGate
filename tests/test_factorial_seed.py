"""Stage 8 randomness separation. The 480-fit experiment is not run here."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rcgate.config import load_named
from rcgate.data.splits import assert_disjoint, group_stratified_split
from rcgate.factorial_seed import (
    MODEL_SEEDS,
    assignment_hash,
    assignment_maps,
    decompose,
    sample_distribution,
)
from rcgate.metrics import SliceMetrics, tune_threshold
from rcgate.models import build_model
from rcgate.pipeline import RunContext, RunResult, fit_variant, load_table, make_split, save_model
from rcgate.stats_protocol import N_RESAMPLES, paired_question_delta, within_seed_auroc_interval
from rcgate.utils import Timing, set_seed

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"


def _frame() -> pd.DataFrame:
    if not TABLE.exists():
        pytest.skip("frozen corrected signal table is not on disk")
    return load_table(TABLE)


def _ids(split, name: str) -> tuple[str, ...]:
    return tuple(sorted(getattr(split, name)["question_id"].astype(str).unique()))


def test_sample_distribution_is_not_a_confidence_interval():
    summary = sample_distribution([1.0, 3.0, 5.0, 7.0], "toy values")
    assert summary["is_confidence_interval"] is False
    assert summary["n"] == 4
    assert summary["sd"] == pytest.approx(np.std([1.0, 3.0, 5.0, 7.0], ddof=1))
    assert "not a confidence interval" in summary["label"]
    assert "endpoint" not in summary


def test_decompose_separates_split_means_from_within_split_sds():
    records = []
    for split_seed, values in ((0, (1.0, 3.0, 5.0)), (1, (2.0, 2.0, 2.0))):
        for model_seed, value in zip((0, 1, 2), values, strict=True):
            records.append({"split_seed": split_seed, "model_seed": model_seed, "auroc": value})
    out = decompose(records, "auroc", split_seeds=(0, 1), model_seeds=(0, 1, 2))
    assert out["over_split_means"]["values"] == pytest.approx([3.0, 2.0])
    assert out["within_split_sd"]["values"] == pytest.approx([2.0, 0.0])
    assert "mean_of_interval_endpoints" not in out
    assert out["n_model_seeds"] == 3
    assert "not a precise population estimate" in out["within_split_note"]
    assert "not 20 independent datasets" in out["split_note"] or "not independent datasets" in out["split_note"]


def test_identical_split_seeds_ignore_the_model_seed():
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    reference = None
    for model_seed in (0, 1, 2, 99):
        set_seed(model_seed)
        split = group_stratified_split(frame, seed=4)
        assert_disjoint(split)
        ctx = RunContext.build(cfg, variant="A0", seed=model_seed, table=TABLE, split_seed=4)
        ctx.start()
        via_pipeline = make_split(frame, ctx)
        got = assignment_hash(split)
        assert got == assignment_hash(via_pipeline)
        if reference is None:
            reference = got
        assert got == reference
        assert _ids(split, "train") == _ids(via_pipeline, "train")
        assert _ids(split, "val") == _ids(via_pipeline, "val")
        assert _ids(split, "test") == _ids(via_pipeline, "test")


def test_changing_the_split_seed_changes_assignments():
    frame = _frame()
    left = group_stratified_split(frame, seed=0)
    right = group_stratified_split(frame, seed=1)
    assert assignment_hash(left) != assignment_hash(right)
    assert _ids(left, "test") != _ids(right, "test")


def test_model_seed_does_not_change_initialization_or_the_split():
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    states = []
    hashes = []
    for split_seed in (0, 1, 7):
        set_seed(2)
        split = group_stratified_split(frame, seed=split_seed)
        hashes.append(assignment_hash(split))
        model = build_model("A7", cfg, seed=2)
        states.append({k: v.detach().clone() for k, v in model.model.state_dict().items()})
    assert len(set(hashes)) == 3
    for key in states[0]:
        assert torch_equal(states[0][key], states[1][key])
        assert torch_equal(states[0][key], states[2][key])


def torch_equal(left, right) -> bool:
    import torch

    return bool(torch.equal(left, right))


def test_question_groups_stay_inside_one_partition():
    frame = _frame()
    pool = set(frame["question_id"].astype(str))
    for seed in (0, 6, 19):
        split = group_stratified_split(frame, seed=seed)
        assert_disjoint(split)
        maps = assignment_maps(split)
        assert set(maps) == pool
        assert set(maps.values()) <= {"train", "val", "test"}
        for name in ("train", "val", "test"):
            part = getattr(split, name)
            assert set(part["question_id"].astype(str)) == {q for q, p in maps.items() if p == name}


def test_same_model_seed_reproduces_training_and_a_different_seed_moves_a7(tmp_path: Path):
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    split = group_stratified_split(frame, seed=0)

    def predict(variant: str, model_seed: int) -> np.ndarray:
        ctx = RunContext.build(cfg, variant=variant, seed=model_seed, table=TABLE, split_seed=0)
        ctx.out_dir = tmp_path / f"{variant}_m{model_seed}_{predict.n}"
        predict.n += 1
        result = fit_variant(ctx, df=frame, split=split)
        assert result.skipped is None
        return np.asarray(result.p_test, dtype="float64")

    predict.n = 0
    a7_a = predict("A7", 0)
    a7_b = predict("A7", 0)
    a7_c = predict("A7", 1)
    assert np.array_equal(a7_a, a7_b)
    assert not np.array_equal(a7_a, a7_c)
    a0_a = predict("A0", 0)
    a0_b = predict("A0", 1)
    assert np.array_equal(a0_a, a0_b)


def test_threshold_uses_validation_scores_only(tmp_path: Path):
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    split = group_stratified_split(frame, seed=3)
    ctx = RunContext.build(cfg, variant="A0", seed=1, table=TABLE, split_seed=3)
    ctx.out_dir = tmp_path / "A0"
    result = fit_variant(ctx, df=frame, split=split)
    val_score = np.asarray(result.model.predict_proba(split.val), dtype="float64")
    expected = tune_threshold(split.val["label"].to_numpy(), val_score)
    assert result.threshold == expected
    assert len(split.val) != len(split.test)


def test_reloaded_checkpoint_recreates_metrics_and_full_threshold(tmp_path: Path):
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    split = group_stratified_split(frame, seed=6)
    ctx = RunContext.build(cfg, variant="A4", seed=6, table=TABLE, split_seed=6)
    ctx.out_dir = tmp_path / "A4"
    result = fit_variant(ctx, df=frame, split=split)
    import joblib

    path = save_model(result.model, tmp_path / "A4" / "model.joblib")
    reloaded = joblib.load(path)
    test_score = np.asarray(reloaded.predict_proba(split.test), dtype="float64")
    val_score = np.asarray(reloaded.predict_proba(split.val), dtype="float64")
    assert np.array_equal(test_score, np.asarray(result.p_test, dtype="float64"))
    threshold = float(tune_threshold(split.val["label"].to_numpy(), val_score))
    assert threshold == result.threshold
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["threshold"] == result.threshold
    rounded = round(result.threshold, 6)
    boundary = np.asarray(result.p_test, dtype="float64")
    # The published A4 seed-6 failure was a score between these two cuts.
    if threshold != rounded:
        assert int(((boundary >= threshold) != (boundary >= rounded)).sum()) >= 1
    stored = json.loads(json.dumps({"threshold": threshold}))["threshold"]
    assert np.array_equal(boundary >= stored, boundary >= threshold)


def test_json_threshold_preserves_the_stage7_boundary_call():
    exact = 6.453252374040946e-06
    score = 6.420037727803235e-06
    rounded = round(exact, 6)
    assert (score >= exact) != (score >= rounded)
    result = RunResult(
        variant="A4",
        seed=6,
        model=None,
        fit_info={},
        threshold=exact,
        test=SliceMetrics("A4:test", 1, 0.0, 0.5),
        val_auroc=0.4,
        y_test=np.array([0]),
        p_test=np.array([score]),
        test_frame=pd.DataFrame({"claim_id": ["1592#0"]}),
        out_dir=Path("."),
        timing=Timing(),
    )
    payload = json.loads(json.dumps(result.to_dict()))
    assert payload["threshold"] == exact
    assert (score >= payload["threshold"]) == (score >= exact)


def test_matched_variants_share_test_claim_ids(tmp_path: Path):
    frame = _frame()
    cfg = load_named("ragtruth_factorial_seed_v1")
    split = group_stratified_split(frame, seed=4)
    expected = tuple(split.test["claim_id"].astype(str))
    got = []
    for variant in ("A0", "A7"):
        ctx = RunContext.build(cfg, variant=variant, seed=2, table=TABLE, split_seed=4)
        ctx.out_dir = tmp_path / variant
        result = fit_variant(ctx, df=frame, split=split)
        got.append(tuple(result.test_frame["claim_id"].astype(str)))
    assert got[0] == got[1] == expected


def test_bootstrap_labels_and_requested_sample_count():
    y = np.array([0, 1, 0, 1, 0, 1])
    groups = np.array(["q1", "q1", "q2", "q2", "q3", "q3"])
    score_a = np.array([0.1, 0.8, 0.2, 0.7, 0.3, 0.9])
    score_b = np.array([0.2, 0.7, 0.4, 0.6, 0.5, 0.55])
    interval = within_seed_auroc_interval(y, score_a, groups, n_resamples=N_RESAMPLES, seed=0)
    paired = paired_question_delta(y, score_a, score_b, groups, n_resamples=N_RESAMPLES, seed=0)
    assert interval["n_requested"] == 1000
    assert paired["n_requested"] == 1000
    assert paired["fraction_is_p_value"] is False
    assert "p_value" not in paired
    assert "not a p-value" in paired["fraction_label"]
    assert interval["label"].startswith("within-seed")
    assert MODEL_SEEDS == (0, 1, 2)


def test_stage8_config_freezes_the_stage7_table_and_hyperparameters():
    old = load_named("ragtruth_multi_seed_v1")
    new = load_named("ragtruth_factorial_seed_v1")
    assert new.get("report.tag") == "ragtruth_factorial_seed_v1"
    assert new.get("data.split_method") == "group_stratified"
    table = str(new.get("data.table"))
    assert "{seed}" not in table
    assert table.endswith("ragtruth_corrected_integrity_v1_s0.parquet")
    for section in ("train", "model", "baselines", "eval", "signals"):
        assert new.to_dict()[section] == old.to_dict()[section]

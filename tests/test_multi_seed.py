"""Stage 7 helpers. The 20-seed fit is not run here."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from rcgate.config import load_named
from rcgate.data.splits import assert_disjoint, group_stratified_split
from rcgate.multi_seed import distribution_summary, jaccard, spearman

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"


def test_distribution_is_not_a_confidence_interval():
    summary = distribution_summary([0.1, 0.2, 0.3, 0.4])
    assert summary["is_confidence_interval"] is False
    assert summary["n"] == 4
    assert summary["min"] == 0.1
    assert summary["max"] == 0.4
    assert summary["median"] == 0.25
    assert summary["iqr"] == summary["q75"] - summary["q25"]
    assert "not a confidence interval" in summary["label"]


def test_jaccard_and_constant_spearman():
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert jaccard({"a"}, {"a"}) == 1.0
    assert math.isnan(jaccard(set(), set()))
    assert spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None
    rho = spearman([1, 2, 3, 4], [1, 2, 3, 4])
    assert rho is not None and abs(rho - 1.0) < 1e-12


def test_stage7_config_cannot_build_a_new_table():
    cfg = load_named("ragtruth_multi_seed_v1")
    assert cfg.get("report.tag") == "ragtruth_multi_seed_v1"
    assert cfg.get("data.split_method") == "group_stratified"
    table = str(cfg.get("data.table"))
    assert "{seed}" not in table
    assert table.endswith("ragtruth_corrected_integrity_v1_s0.parquet")
    assert (ROOT / table).exists()


def test_group_stratified_positive_counts_do_not_depend_on_seed():
    frame = pd.read_parquet(TABLE)
    totals = []
    for seed in (0, 1, 7, 19):
        split = group_stratified_split(frame, seed=seed)
        assert_disjoint(split)
        totals.append(
            (
                int(split.train["label"].sum()),
                int(split.val["label"].sum()),
                int(split.test["label"].sum()),
            )
        )
    assert len(set(totals)) == 1
    assert totals[0] == (33, 9, 15)

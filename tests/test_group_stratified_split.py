"""Stage 6 split tests: legacy permutation versus group stratification.

The legacy ``stratify=True`` path is pinned to the historical algorithm. The new
splitter is pinned to group-level positive counts, not to a claim-level draw.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rcgate.config import Config, load_named
from rcgate.data.splits import (
    assert_disjoint,
    cut_counts,
    group_positive_counts,
    group_stratified_split,
    grouped_split,
)
from rcgate.pipeline import make_split


def _rows(spec: list[tuple[str, list[int]]]) -> pd.DataFrame:
    """``spec`` is (question_id, labels). One row per label, generators in order."""
    rows = []
    for question_id, labels in spec:
        for index, label in enumerate(labels):
            rows.append(
                {
                    "question_id": question_id,
                    "claim_id": f"{question_id}#{index}",
                    "label": int(label),
                    "generator_id": index % 6,
                }
            )
    return pd.DataFrame(rows)


def skewed_frame() -> pd.DataFrame:
    """25 all-negative groups and 5 all-positive groups, equal size."""
    spec = []
    for q in range(25):
        spec.append((f"q{q:02d}", [0, 0, 0, 0]))
    for q in range(25, 30):
        spec.append((f"q{q:02d}", [1, 1, 1, 1]))
    return _rows(spec)


def mixed_frame() -> pd.DataFrame:
    """Eight groups carry a single positive claim; the rest are negative."""
    spec = []
    for q in range(20):
        labels = [1, 0, 0, 0] if q < 8 else [0, 0, 0, 0]
        spec.append((f"q{q:02d}", labels))
    return _rows(spec)


def distinct_rate_frame() -> pd.DataFrame:
    """Twelve groups with twelve different positive counts, so a sort is visible."""
    spec = [(f"q{q:02d}", [1] * q + [0] * (12 - q)) for q in range(12)]
    return _rows(spec)


def legacy_shuffled_groups(df: pd.DataFrame, seed: int, stratify: bool = True) -> np.ndarray:
    """Reimplementation of the historical body of ``grouped_split``.

    Sort by group mean label, then replace that order with one permutation.
    """
    groups = df["question_id"].astype(str).unique()
    rng = np.random.default_rng(seed)
    if stratify:
        key = df["question_id"].astype(str)
        rates = {g: float(df.loc[key == g, "label"].mean()) for g in groups}
        order = np.array(sorted(rates, key=lambda g: rates[g]))
    else:
        order = np.array(sorted(groups.astype(str)))
    return order[rng.permutation(len(order))]


def _ids(part: pd.DataFrame) -> list[str]:
    return part["question_id"].astype(str).tolist()


def _assigned(split) -> dict[str, str]:
    out = {}
    for name in ("train", "val", "test"):
        for question_id in getattr(split, name)["question_id"].astype(str):
            out[question_id] = name
    return out


# -- legacy mechanism --------------------------------------------------------


def test_legacy_stratify_is_a_full_permutation_of_the_rate_sorted_groups():
    df = distinct_rate_frame()
    shuffled = legacy_shuffled_groups(df, seed=0, stratify=True)
    key = df["question_id"].astype(str)
    rates = {g: float(df.loc[key == g, "label"].mean()) for g in df["question_id"].astype(str).unique()}
    along = [rates[g] for g in shuffled]
    assert along != sorted(along)

    split = grouped_split(df, seed=0, stratify=True)
    n_train, n_val, _ = cut_counts(len(shuffled))
    assert _ids(split.train) == [str(g) for g in shuffled[:n_train]] or set(_ids(split.train)) == set(
        map(str, shuffled[:n_train])
    )
    # Row order inside a part follows the input frame, so compare membership.
    assert set(_ids(split.train)) == set(map(str, shuffled[:n_train]))
    assert set(_ids(split.val)) == set(map(str, shuffled[n_train : n_train + n_val]))
    assert set(_ids(split.test)) == set(map(str, shuffled[n_train + n_val :]))


def test_legacy_positive_counts_move_with_the_seed_and_stratified_counts_do_not():
    df = skewed_frame()
    new_counts = []
    old_counts = []
    for seed in range(20):
        new = group_stratified_split(df, seed=seed)
        old = grouped_split(df, seed=seed, stratify=True)
        new_counts.append(tuple(int(getattr(new, name)["label"].sum()) for name in ("train", "val", "test")))
        old_counts.append(tuple(int(getattr(old, name)["label"].sum()) for name in ("train", "val", "test")))
    assert len(set(new_counts)) == 1
    assert new_counts[0] == (12, 4, 4)
    assert len(set(old_counts)) > 1


# -- group integrity and reproducibility -------------------------------------


def test_every_group_stays_inside_one_partition():
    df = mixed_frame()
    for seed in range(5):
        split = group_stratified_split(df, seed=seed)
        assert_disjoint(split)
        seen = []
        for name in ("train", "val", "test"):
            seen.extend(getattr(split, name)["question_id"].astype(str).unique())
        assert sorted(seen) == sorted(df["question_id"].astype(str).unique())
        assert len(seen) == len(set(seen))
        assigned = _assigned(split)
        for question_id, part in df.groupby(df["question_id"].astype(str)):
            assert part["question_id"].astype(str).map(assigned).nunique() == 1


def test_split_is_deterministic_for_a_fixed_seed_and_ignores_row_order():
    df = skewed_frame()
    first = group_stratified_split(df, seed=2)
    second = group_stratified_split(df, seed=2)
    for name in ("train", "val", "test"):
        assert _ids(getattr(first, name)) == _ids(getattr(second, name))
        assert getattr(first, name)["claim_id"].tolist() == getattr(second, name)["claim_id"].tolist()

    shuffled = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    moved = group_stratified_split(shuffled, seed=2)
    assert _assigned(first) == _assigned(moved)


def test_different_seeds_can_produce_different_valid_partitions():
    df = skewed_frame()
    test_sets = [
        frozenset(group_stratified_split(df, seed=seed).test["question_id"].astype(str))
        for seed in range(8)
    ]
    assert len(set(test_sets)) > 1
    for seed in range(8):
        assert_disjoint(group_stratified_split(df, seed=seed))


def test_stratification_uses_the_group_positive_count_not_the_claim_row():
    df = mixed_frame()
    moved = df.copy()
    for q in range(8):
        question_id = f"q{q:02d}"
        idx = moved.index[moved["question_id"] == question_id]
        moved.loc[idx, "label"] = np.roll(moved.loc[idx, "label"].to_numpy(), 1)
        assert int(moved.loc[idx, "label"].sum()) == 1
        assert int(moved.loc[idx[0], "label"]) == 0

    original = group_stratified_split(df, seed=1)
    rotated = group_stratified_split(moved, seed=1)
    assert _assigned(original) == _assigned(rotated)

    # The positive claim and the negative claims of that source share a partition.
    assigned = _assigned(original)
    for q in range(8):
        question_id = f"q{q:02d}"
        part_name = assigned[question_id]
        part = getattr(original, part_name)
        labels = set(part.loc[part["question_id"] == question_id, "label"])
        assert labels == {0, 1}

    counts = group_positive_counts(df)
    assert int(counts["q00"]) == 1
    assert int(counts["q08"]) == 0


def test_stratum_shuffle_does_not_depend_on_the_other_strata():
    df = skewed_frame()
    full = _assigned(group_stratified_split(df, seed=0))
    positive_ids = {f"q{q:02d}" for q in range(25, 30)}
    only = df[df["question_id"].isin(positive_ids)].reset_index(drop=True)
    reduced = _assigned(group_stratified_split(only, seed=0))
    assert {qid: full[qid] for qid in positive_ids} == reduced


def test_partition_sizes_follow_the_stratum_rounding_rule():
    df = skewed_frame()
    counts = group_positive_counts(df)
    expected = {"train": 0, "val": 0, "test": 0}
    for stratum, n in counts.value_counts().items():
        n_train, n_val, n_test = cut_counts(int(n))
        expected["train"] += n_train
        expected["val"] += n_val
        expected["test"] += n_test
    split = group_stratified_split(df, seed=4)
    assert split.sizes()["train_groups"] == expected["train"] == 18
    assert split.sizes()["val_groups"] == expected["val"] == 6
    assert split.sizes()["test_groups"] == expected["test"] == 6
    # 30 equal groups, 60/20/20, and both strata are large enough to hit it.
    assert expected["train"] / 30 == pytest.approx(0.6)
    assert expected["val"] / 30 == pytest.approx(0.2)


def test_small_stratum_is_not_spread_past_the_rounding_limit():
    spec = [(f"n{i:02d}", [0, 0, 0]) for i in range(10)]
    spec += [("p0", [1, 1, 1]), ("p1", [1, 1, 1])]
    df = _rows(spec)
    split = group_stratified_split(df, seed=0)
    positive = {"p0", "p1"}
    val_ids = set(split.val["question_id"].astype(str))
    assert positive.isdisjoint(val_ids)
    assert cut_counts(2) == (1, 0, 1)
    # Both positive groups are assigned, one to train and one to test.
    train_pos = positive & set(split.train["question_id"].astype(str))
    test_pos = positive & set(split.test["question_id"].astype(str))
    assert len(train_pos) == 1
    assert len(test_pos) == 1


def test_positive_rate_matches_when_strata_can_fill_every_partition():
    df = skewed_frame()
    full = float(df["label"].mean())
    for seed in range(5):
        split = group_stratified_split(df, seed=seed)
        for name in ("train", "val", "test"):
            assert float(getattr(split, name)["label"].mean()) == pytest.approx(full)


def test_cut_counts_matches_historical_rounding_on_the_experiment_fractions():
    for n in range(0, 300):
        raw_train, raw_val = int(round(n * 0.6)), int(round(n * 0.2))
        assert raw_train + raw_val <= n
        assert cut_counts(n) == (raw_train, raw_val, n - raw_train - raw_val)


def test_new_split_rejects_bad_fractions_missing_columns_and_negative_seeds():
    df = skewed_frame()
    with pytest.raises(ValueError):
        group_stratified_split(df, fractions=(0.5, 0.2, 0.2))
    with pytest.raises(KeyError):
        group_stratified_split(df.drop(columns=["question_id"]))
    with pytest.raises(KeyError):
        group_stratified_split(df.drop(columns=["label"]))
    with pytest.raises(ValueError):
        group_stratified_split(df, seed=-1)


# -- wiring ------------------------------------------------------------------


def test_make_split_defaults_to_the_legacy_method():
    df = skewed_frame()
    ctx = type("Ctx", (), {})()
    ctx.cfg = Config({"data": {}})
    ctx.split_seed = 3
    ctx.seed = 3
    got = make_split(df, ctx)
    legacy = grouped_split(df, seed=3, stratify=True)
    assert _assigned(got) == _assigned(legacy)


def test_make_split_selects_group_stratification_from_the_config():
    df = skewed_frame()
    ctx = type("Ctx", (), {})()
    ctx.cfg = Config({"data": {"split_method": "group_stratified"}})
    ctx.split_seed = 3
    ctx.seed = 99
    got = make_split(df, ctx)
    expect = group_stratified_split(df, seed=3)
    assert _assigned(got) == _assigned(expect)
    assert _assigned(got) != _assigned(grouped_split(df, seed=3, stratify=True))


def test_unknown_split_method_is_rejected():
    df = skewed_frame()
    ctx = type("Ctx", (), {})()
    ctx.cfg = Config({"data": {"split_method": "claim_stratified"}})
    ctx.split_seed = 0
    ctx.seed = 0
    with pytest.raises(ValueError):
        make_split(df, ctx)


def test_stage6_config_changes_only_the_split_method_and_the_output_tag():
    old = load_named("ragtruth_corrected_integrity_v1")
    new = load_named("ragtruth_split_corrected_v1")
    assert new.get("data.split_method") == "group_stratified"
    assert old.get("data.split_method", "grouped") == "grouped"
    assert new.get("report.tag") == "ragtruth_split_corrected_v1"
    assert new.get("data.table") == old.get("data.table")
    for section in ("train", "model", "signals", "eval"):
        assert new.to_dict()[section] == old.to_dict()[section]
    old_data = old.to_dict()["data"]
    new_data = new.to_dict()["data"]
    assert set(new_data) - set(old_data) == {"split_method"}
    for key, value in old_data.items():
        assert new_data[key] == value


def _stratum_allocation(counts: pd.Series) -> dict[str, dict[str, int]]:
    """Positive claims and groups each partition receives under ``cut_counts``."""
    out = {
        name: {"groups": 0, "positives": 0}
        for name in ("train", "val", "test")
    }
    for stratum, n_groups in counts.value_counts().sort_index().items():
        n_train, n_val, n_test = cut_counts(int(n_groups))
        for name, n_part in (("train", n_train), ("val", n_val), ("test", n_test)):
            out[name]["groups"] += n_part
            out[name]["positives"] += int(stratum) * n_part
    return out


def test_frozen_corrected_tables_are_split_on_groups_not_claims():
    """The canonical Stage 4 tables, not a toy frame.

    Positive totals are fixed by the stratum sizes. The seed only chooses which
    groups land in each block. ``stratify=True`` does not have that property.
    """
    root = Path("data/signal_tables")
    paths = [root / f"ragtruth_corrected_integrity_v1_s{seed}.parquet" for seed in range(3)]
    if not all(path.exists() for path in paths):
        pytest.skip("frozen corrected signal tables are not on disk")

    new_test_sets = []
    old_test_sets = []
    for seed, path in enumerate(paths):
        df = pd.read_parquet(path)
        assert len(df) == 800
        assert int(df["question_id"].nunique()) == 134
        assert int(df["label"].sum()) == 57
        counts = group_positive_counts(df)
        assert counts.value_counts().sort_index().to_dict() == {0: 97, 1: 23, 2: 10, 3: 2, 4: 2}
        expected = _stratum_allocation(counts)

        new = group_stratified_split(df, seed=seed)
        old = grouped_split(df, seed=seed, stratify=True)
        assert_disjoint(new)
        assert_disjoint(old)
        for name in ("train", "val", "test"):
            part = getattr(new, name)
            assert part["question_id"].nunique() == expected[name]["groups"]
            assert int(part["label"].sum()) == expected[name]["positives"]
            assert set(part["generator_id"]) == {0, 1, 2, 3, 4, 5}
            claim_ids = part["claim_id"].astype(str)
            assert claim_ids.is_unique
        claim_sets = [set(getattr(new, name)["claim_id"].astype(str)) for name in ("train", "val", "test")]
        assert claim_sets[0].isdisjoint(claim_sets[1])
        assert claim_sets[0].isdisjoint(claim_sets[2])
        assert claim_sets[1].isdisjoint(claim_sets[2])
        # A mixed-label source is not split claim by claim.
        mixed = counts[counts.between(1, 5)].index
        assigned = _assigned(new)
        assert len({assigned[qid] for qid in mixed}) >= 1
        for question_id in mixed:
            rows = df[df["question_id"].astype(str) == question_id]
            assert rows["label"].nunique() > 1 or int(rows["label"].sum()) == len(rows)
            assert rows["question_id"].astype(str).map(assigned).nunique() == 1

        new_test_sets.append(frozenset(new.test["question_id"].astype(str)))
        old_test_sets.append(frozenset(old.test["question_id"].astype(str)))
        assert new_test_sets[-1] != old_test_sets[-1]
        # Strata of size 2 (positive counts 3 and 4) contribute no validation groups.
        assert expected["train"]["positives"] == 33
        assert expected["val"]["positives"] == 9
        assert expected["test"]["positives"] == 15

    assert len(set(new_test_sets)) == 3

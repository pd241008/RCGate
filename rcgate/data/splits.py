"""Grouped train/val/test splits by ``question_id`` (constraint C6).

Every model in this repo is fit on these splits and evaluated on the test rows of the
same split object, so no question can appear on both sides of a boundary.

Two constructions live here:

* ``grouped_split`` — the historical splitter. ``stratify=True`` sorts groups by
  positive rate and then draws a full permutation, so the sort is not a stratifier.
  Published checkpoints use this function and it is left unchanged.
* ``group_stratified_split`` — whole groups are shuffled inside their positive-count
  stratum and cut to the requested fractions. This is the Stage 6 splitter.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..utils import set_seed
from .schema import LABEL_COL

#: ``data.split_method`` values. ``grouped`` is the historical default.
SPLIT_GROUPED = "grouped"
SPLIT_GROUP_STRATIFIED = "group_stratified"


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    seed: int
    group_column: str = "question_id"
    held_out_generator: int | None = None

    def sizes(self) -> dict[str, int]:
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
            "train_groups": self.train[self.group_column].nunique(),
            "val_groups": self.val[self.group_column].nunique(),
            "test_groups": self.test[self.group_column].nunique(),
        }

    def unk_rows(self) -> pd.DataFrame:
        """Test rows that went through the ``UNK`` cold-start path."""
        from .schema import UNK_GENERATOR

        return self.test[self.test["generator_id"] == UNK_GENERATOR].reset_index(drop=True)


def grouped_split(
    df: pd.DataFrame,
    seed: int = 0,
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
    group_column: str = "question_id",
    stratify: bool = True,
) -> Split:
    """Split whole questions into train/val/test.

    ``stratify=True`` does not stratify. Groups are sorted by mean label, then a full
    permutation of that list is drawn with ``numpy.random.default_rng(seed)`` and cut
    into contiguous blocks. The permutation removes the sort, so partition positive
    rates are not matched to the table. The body below is the historical algorithm
    and stays byte-for-byte in its assignments so existing checkpoints can be rescored.
    Use ``group_stratified_split`` when the positive rate should be matched at group level.
    """
    if group_column not in df.columns:
        raise KeyError(f"{group_column} not in frame; cannot guarantee leakage-free splits")
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions must sum to 1.0, got {fractions}")

    groups = df[group_column].astype(str).unique()
    rng = np.random.default_rng(seed)

    if stratify:
        key = df[group_column].astype(str)
        rates = {g: float(df.loc[key == g, LABEL_COL].mean()) for g in groups}
        order = np.array(sorted(rates, key=lambda g: rates[g]))
    else:
        order = np.array(sorted(groups.astype(str)))
    shuffled = order[rng.permutation(len(order))]
    n = len(shuffled)
    n_train, n_val = int(round(n * fractions[0])), int(round(n * fractions[1]))
    parts = [shuffled[:n_train], shuffled[n_train : n_train + n_val], shuffled[n_train + n_val :]]

    assigned = {}
    for name, part in zip(("train", "val", "test"), parts, strict=True):
        for g in part:
            assigned[str(g)] = name

    part_of_row = df[group_column].astype(str).map(assigned)
    if part_of_row.isna().any():
        raise RuntimeError("some rows were not assigned to a split")
    frames = {
        name: df.loc[part_of_row == name].reset_index(drop=True) for name in ("train", "val", "test")
    }
    split = Split(seed=seed, group_column=group_column, **frames)
    assert_disjoint(split)
    return split


def cut_counts(n: int, fractions: tuple[float, float, float] = (0.6, 0.2, 0.2)) -> tuple[int, int, int]:
    """Group counts for one stratum, using the same rounding as ``grouped_split``.

    The remainder goes to test. A stratum of size 2 therefore contributes
    ``round(1.2)=1`` train group, ``round(0.4)=0`` validation groups, and 1 test
    group. Validation can miss a rare stratum. That is the method's limit, not a
    second pass that moves groups to chase the positive rate.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    n_train = int(round(n * fractions[0]))
    n_val = int(round(n * fractions[1]))
    if n_train + n_val > n:
        overflow = n_train + n_val - n
        take = min(overflow, n_val)
        n_val -= take
        n_train -= overflow - take
    n_test = n - n_train - n_val
    return n_train, n_val, n_test


def group_positive_counts(
    df: pd.DataFrame,
    group_column: str = "question_id",
    label_column: str = LABEL_COL,
) -> pd.Series:
    """Positive-claim count of each group. This is the stratification key.

    The count is a property of the whole group. Two claims in the same group
    never receive different keys, even when their labels differ.
    """
    if group_column not in df.columns:
        raise KeyError(f"{group_column} not in frame; cannot group the split")
    if label_column not in df.columns:
        raise KeyError(f"{label_column} not in frame; cannot stratify groups")
    key = df[group_column].astype(str)
    totals = df.groupby(key, sort=False)[label_column].sum()
    values = totals.to_numpy(dtype="float64")
    if values.size and not np.all(np.isclose(values, np.rint(values))):
        raise ValueError("group stratification requires an integer positive count per group")
    counts = pd.Series(np.rint(values).astype(int), index=totals.index.astype(str), name="n_positive")
    return counts


def group_stratified_split(
    df: pd.DataFrame,
    seed: int = 0,
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
    group_column: str = "question_id",
    label_column: str = LABEL_COL,
) -> Split:
    """Assign each ``question_id`` wholly to one partition, stratified by positive count.

    What is stratified
        The group's positive-claim count (sum of ``label``), not the claim row.
        Groups with the same count form one stratum. A source whose generators
        disagree stays in one stratum and in one partition.

    What is grouped
        ``group_column``, default ``question_id``. On the RAGTruth tables that
        column is the source id. Every claim of a source moves together.

    Partition proportions
        Inside each stratum the group counts are ``cut_counts``: about 60% train,
        20% validation, 20% test, with the historical ``round`` rule and the
        remainder in test. Global counts are the sums of those stratum cuts.
        They match 60/20/20 when every stratum is large enough for the rounding
        to fill all three partitions, and they miss a partition when a stratum
        has only one or two groups.

    Seed
        Each stratum is shuffled by ``numpy.random.default_rng`` seeded with
        ``SeedSequence([seed, stratum])``. The same seed reproduces the same
        assignment. A different seed reshuffles strata that contain more than
        one group. The stream for one stratum does not depend on the other strata.
        Group ids are sorted before the shuffle, so the result does not depend
        on row order. Seeds must be non-negative, matching ``SeedSequence``.

    Limits
        With few groups at a high positive count, validation can receive none of
        them, and the test positive rate stays a little above the table rate.
        The method does not search for a better assignment.
    """
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions must sum to 1.0, got {fractions}")
    if int(seed) < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")

    counts = group_positive_counts(df, group_column=group_column, label_column=label_column)
    assigned: dict[str, str] = {}
    for stratum in sorted(int(v) for v in counts.unique()):
        members = np.array(sorted(counts.index[counts.to_numpy() == stratum].astype(str)))
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), int(stratum)]))
        order = members[rng.permutation(len(members))]
        n_train, n_val, _n_test = cut_counts(len(order), fractions)
        parts = {
            "train": order[:n_train],
            "val": order[n_train : n_train + n_val],
            "test": order[n_train + n_val :],
        }
        for name, part in parts.items():
            for group_id in part:
                assigned[str(group_id)] = name

    part_of_row = df[group_column].astype(str).map(assigned)
    if part_of_row.isna().any():
        raise RuntimeError("some rows were not assigned to a split")
    frames = {
        name: df.loc[part_of_row == name].reset_index(drop=True) for name in ("train", "val", "test")
    }
    split = Split(seed=seed, group_column=group_column, **frames)
    assert_disjoint(split)
    return split


def split_balance(
    df: pd.DataFrame,
    split: Split,
    label_column: str = LABEL_COL,
) -> dict:
    """Positive-rate balance of one split against the full table."""
    full_n = int(len(df))
    full_pos = int(df[label_column].sum()) if full_n else 0
    full_rate = float(df[label_column].mean()) if full_n else float("nan")
    parts: dict[str, dict] = {}
    for name in ("train", "val", "test"):
        part = getattr(split, name)
        n = int(len(part))
        pos = int(part[label_column].sum()) if n else 0
        rate = float(part[label_column].mean()) if n else float("nan")
        groups = int(part[split.group_column].nunique()) if n else 0
        entry = {
            "groups": groups,
            "claims": n,
            "positives": pos,
            "positive_rate": rate,
            "positive_rate_deviation": (rate - full_rate) if n else float("nan"),
        }
        if "generator_id" in part.columns and n:
            entry["generators"] = sorted(int(g) for g in part["generator_id"].unique())
            entry["generator_counts"] = {
                int(k): int(v) for k, v in part["generator_id"].value_counts().sort_index().items()
            }
            entry["positives_by_generator"] = {
                int(k): int(v) for k, v in part.groupby("generator_id")[label_column].sum().sort_index().items()
            }
        parts[name] = entry
    deviations = np.array([parts[name]["positive_rate_deviation"] for name in ("train", "val", "test")], dtype="float64")
    finite = deviations[np.isfinite(deviations)]
    return {
        "seed": int(split.seed),
        "full_claims": full_n,
        "full_groups": int(df[split.group_column].nunique()) if full_n else 0,
        "full_positives": full_pos,
        "full_positive_rate": full_rate,
        "partitions": parts,
        "mean_absolute_deviation": float(np.mean(np.abs(finite))) if finite.size else float("nan"),
        "max_absolute_deviation": float(np.max(np.abs(finite))) if finite.size else float("nan"),
    }


def assert_disjoint(split: Split) -> None:
    """Fail loudly if any question id appears in more than one split."""
    sets = {
        name: set(getattr(split, name)[split.group_column].astype(str))
        for name in ("train", "val", "test")
    }
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        overlap = sets[a] & sets[b]
        if overlap:
            raise AssertionError(f"{a}/{b} share {len(overlap)} {split.group_column} values")


def leave_one_generator_out(df: pd.DataFrame, generator_id: int, seed: int = 0) -> Split:
    """Hold one generator out of training entirely, to exercise the ``UNK`` path.

    The question split is made first and every split stays question-disjoint; only
    *then* is the held-out generator deleted from train/val and relabelled ``UNK`` in
    test. Splitting by generator before the question split would put sibling claims from
    one question on both sides of the boundary, which is exactly the leak C6 forbids.
    """
    from .schema import UNK_GENERATOR

    if (df["generator_id"] == generator_id).sum() == 0:
        raise ValueError(f"generator_id {generator_id} not present")

    base = grouped_split(df, seed=seed)
    kept = base.train["generator_id"] != generator_id
    kept_val = base.val["generator_id"] != generator_id
    test = base.test.copy()
    test["generator_id"] = np.where(
        test["generator_id"] == generator_id, UNK_GENERATOR, test["generator_id"]
    )

    split = Split(
        train=base.train.loc[kept].reset_index(drop=True),
        val=base.val.loc[kept_val].reset_index(drop=True),
        test=test.reset_index(drop=True),
        seed=seed,
        held_out_generator=generator_id,
    )
    assert_disjoint(split)
    if split.unk_rows().empty:
        raise ValueError(f"generator {generator_id} had no rows in the test split; use another seed")
    return split


def subsample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """Take about ``n`` rows, keeping question groups intact. Used by smoke tests."""
    set_seed(seed)
    if len(df) <= n:
        return df.reset_index(drop=True)
    rng = np.random.default_rng(seed)
    groups = rng.permutation(df["question_id"].astype(str).unique())
    chosen: list[str] = []
    taken = 0
    for g in groups:
        if taken >= n:
            break
        chosen.append(g)
        taken += int((df["question_id"].astype(str) == g).sum())
    return df[df["question_id"].astype(str).isin(set(chosen))].head(n).reset_index(drop=True)

"""Grouped train/val/test splits by ``question_id`` (constraint C6).

Every model in this repo is fit on these splits and evaluated on the test rows of the
same split object, so no question can appear on both sides of a boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..utils import set_seed
from .schema import LABEL_COL


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

    With ``stratify=True`` the *positive rate* of each part is matched to the full table,
    because hallucination rates vary a lot between benchmarks and a plain random split
    can leave the test set single-class.
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

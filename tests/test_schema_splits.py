"""Signal-table contract and leakage-free grouped splits."""

from __future__ import annotations

import pytest

from rcgate.data.schema import (
    SIGNALS,
    UNK_GENERATOR,
    onehot_meta,
    signal_frame,
    split_xy,
    validate,
)
from rcgate.data.splits import assert_disjoint, grouped_split, leave_one_generator_out


def make_frame(n_questions=60, n_generators=4, per_question=4, seed=0):
    rows = []
    for q in range(n_questions):
        for g in range(n_generators):
            for c in range(per_question):
                rows.append(
                    {
                        "question_id": f"q{q}",
                        "claim_id": f"q{q}_g{g}_c{c}",
                        "claim_text": f"claim {c} of question {q}",
                        "benchmark": "synthetic",
                        "claim_type": c % 4,
                        "generator_id": g,
                        "agree": 0.2 + 0.1 * c,
                        "contra": 0.1 * c,
                        "sem_dist": 0.5,
                        "support": 0.3 + 0.1 * c,
                        "src_quality": 0.7,
                        "conflict": 0.05 * c,
                        "label": (q + c) % 2,
                    }
                )
    return signal_frame(rows)


# -- schema ------------------------------------------------------------------


def test_signals_are_within_unit_interval():
    df = make_frame()
    for col in SIGNALS:
        assert df[col].between(0.0, 1.0).all(), col


def test_out_of_range_signal_is_reported():
    df = make_frame()
    df.loc[0, "agree"] = 1.4
    report = validate(df)
    assert not report.ok
    assert any("agree" in p for p in report.problems)


def test_duplicate_claim_id_is_reported():
    df = make_frame()
    df.loc[1, "claim_id"] = df.loc[0, "claim_id"]
    assert any("unique" in p for p in validate(df).problems)


def test_unknown_claim_type_is_reported():
    df = make_frame()
    df.loc[0, "claim_type"] = 9
    assert any("claim_type" in p for p in validate(df).problems)


def test_valid_frame_passes():
    assert validate(make_frame()).ok


def test_split_xy_shapes():
    df = make_frame()
    x, m, y = split_xy(df)
    assert len(x) == len(m) == len(y) == len(df)
    assert len(x[0]) == 6
    assert len(m[0]) == 2


def test_onehot_meta_folds_unknown_generator_into_last_slot():
    n_generators = 4
    df = make_frame(n_generators=n_generators)
    df.loc[0, "generator_id"] = UNK_GENERATOR
    vec = onehot_meta(df, n_generators=n_generators)
    # claim-type block is 4 wide, generator block is G+1 wide with UNK last
    assert len(vec[0]) == 4 + n_generators + 1
    assert sum(vec[0][:4]) == 1.0
    assert vec[0][-1] == 1.0
    assert sum(vec[0][4:]) == 1.0


def test_onehot_meta_rejects_out_of_range_generator():
    df = make_frame(n_generators=4)
    df.loc[0, "generator_id"] = 99
    with pytest.raises(ValueError):
        onehot_meta(df, n_generators=4)


# -- splits ------------------------------------------------------------------


def test_no_question_id_appears_in_two_splits():
    for seed in range(5):
        split = grouped_split(make_frame(), seed=seed)
        assert_disjoint(split)


def test_split_partitions_every_row_exactly_once():
    split = grouped_split(make_frame(), seed=3)
    total = len(split.train) + len(split.val) + len(split.test)
    assert total == len(make_frame())


def test_split_fractions_are_roughly_respected():
    split = grouped_split(make_frame(n_questions=200), seed=0)
    assert split.sizes()["train_groups"] / 200 == pytest.approx(0.6, abs=0.05)


def test_stratified_split_keeps_positive_rate_close():
    df = make_frame(n_questions=200)
    full_rate = df["label"].mean()
    for seed in range(3):
        split = grouped_split(df, seed=seed, stratify=True)
        for part in (split.train, split.val, split.test):
            assert part["label"].mean() == pytest.approx(full_rate, abs=0.05)


def test_unstratified_split_still_disjoint():
    split = grouped_split(make_frame(), seed=1, stratify=False)
    assert_disjoint(split)


def test_leave_one_generator_out_relabels_to_unk():
    df = make_frame(n_generators=4)
    split = leave_one_generator_out(df, generator_id=2)

    # the held-out generator survives only in test, wearing the UNK sentinel
    assert not split.unk_rows().empty
    assert int(split.train["generator_id"].eq(UNK_GENERATOR).sum()) == 0
    assert int(split.val["generator_id"].eq(UNK_GENERATOR).sum()) == 0

    # no trace of generator 2 anywhere in train/val
    assert 2 not in set(split.train["generator_id"])
    assert 2 not in set(split.val["generator_id"])
    assert split.held_out_generator == 2

    # the other generators keep their real ids
    assert set(split.train["generator_id"]) == {0, 1, 3}
    assert_disjoint(split)


def test_leave_one_generator_out_does_not_leak_sibling_claims():
    """A held-out generator's questions must not also appear in train (constraint C6).

    Splitting by generator first would put sibling claims of the same question on both
    sides of the boundary. Dropping generator 2 from train/val and relabelling it in test
    avoids that, so the UNK rows come only from questions absent from train/val.
    """
    df = make_frame(n_generators=4)
    split = leave_one_generator_out(df, generator_id=2)
    seen = set(split.train["question_id"].astype(str)) | set(split.val["question_id"].astype(str))
    unk_questions = set(split.unk_rows()["question_id"].astype(str))
    assert not (seen & unk_questions)
    assert (split.train["generator_id"] != 2).all()


def test_leave_one_generator_out_rejects_unknown_generator():
    with pytest.raises(ValueError):
        leave_one_generator_out(make_frame(), generator_id=42)


def test_fractions_must_sum_to_one():
    with pytest.raises(ValueError):
        grouped_split(make_frame(), fractions=(0.5, 0.2, 0.2))


def test_missing_group_column_is_rejected():
    df = make_frame().drop(columns=["question_id"])
    with pytest.raises(KeyError):
        grouped_split(df)

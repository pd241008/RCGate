"""M1 acceptance: the planted correlations must have the intended signs.

These tests read ``configs/planted.yaml`` and assert the realised table matches what the
config claims. If someone edits the emission tables, these fail loudly, which is the
point: the synthetic table is only useful as a benchmark if its ground truth is known.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from rcgate.data.schema import CLAIM_TYPE_NAMES, SIGNALS, validate
from rcgate.data.synthetic import generate, load_planted

NUMERIC, ENTITY, EXTRACTIVE, ABSTRACTIVE = 0, 1, 2, 3


@pytest.fixture(scope="module")
def table():
    return generate(load_planted(), seed=0, n_questions=400)


def single_signal_auroc(df, signal: str, claim_type: int | None = None, generator: int | None = None):
    """AUROC of one signal against the label. 0.5 = no information, <0.5 = anti-informative."""
    sub = df
    if claim_type is not None:
        sub = sub[sub["claim_type"] == claim_type]
    if generator is not None:
        sub = sub[sub["generator_id"] == generator]
    if sub["label"].nunique() < 2:
        pytest.skip("single-class slice")
    return float(roc_auc_score(sub["label"], sub[signal]))


# -- shape and contract ------------------------------------------------------


def test_table_meets_the_size_floor(table):
    assert len(table) >= 4000, f"only {len(table)} claims; spec floor is 4000"
    assert table["generator_id"].nunique() >= 3
    assert set(table["claim_type"]) == {0, 1, 2, 3}
    assert table["benchmark"].eq("synthetic").all()


def test_full_scale_table_meets_the_size_floor():
    full = generate(load_planted(), seed=0)
    assert len(full) >= 4000


def test_table_satisfies_the_signal_contract(table):
    validate(table).raise_if_failed()
    for col in SIGNALS:
        assert table[col].between(0.0, 1.0).all(), col


def test_generation_is_deterministic():
    a = generate(load_planted(), seed=7, n_questions=60)
    b = generate(load_planted(), seed=7, n_questions=60)
    pd.testing.assert_frame_equal(a, b)


def test_different_seeds_give_different_tables():
    a = generate(load_planted(), seed=1, n_questions=60)
    b = generate(load_planted(), seed=2, n_questions=60)
    assert not a["agree"].equals(b["agree"])


# -- planted structure: the two conflict cells ------------------------------
#
# The design (see the header table in configs/planted.yaml) is:
#   numeric      - evidence trustworthy, cross-model family ANTI-informative
#   entity /     - cross-model family trustworthy, evidence weak
#   extractive /
#   abstractive  -
# These tests assert both directions, because a table where either family works
# everywhere makes flat fusion succeed and the gate untestable.


def test_numeric_agree_carries_no_information(table):
    """Spec M1: for numeric claims `agree` is high regardless of the label."""
    auc = single_signal_auroc(table, "agree", NUMERIC)
    assert 0.40 < auc < 0.60, f"agree should be uninformative on numeric claims, got {auc:.3f}"


def test_numeric_cross_family_is_anti_informative(table):
    """Correlated-error mechanism: all generators copy the same wrong number, so
    cross-model contradiction is *lower* when the claim is wrong."""
    contra = single_signal_auroc(table, "contra", NUMERIC)
    assert contra < 0.20, f"contra should be strongly anti-informative for numeric, got {contra:.3f}"


def test_numeric_evidence_family_is_informative(table):
    """The arithmetic check makes numeric claims verifiable, so evidence works."""
    support = single_signal_auroc(table, "support", NUMERIC)
    conflict = single_signal_auroc(table, "conflict", NUMERIC)
    assert support < 0.28, f"support should carry the numeric cell, got {support:.3f}"
    assert conflict > 0.62, f"conflict should carry the numeric cell, got {conflict:.3f}"


def test_numeric_has_no_usable_cross_signal_but_does_have_usable_evidence(table):
    """The asymmetry that makes the gate worth building.

    On numeric claims, no cross-model signal points the right way, while the evidence
    family does. A gate that down-weights cross for numeric claims therefore gains a lot,
    and a flat model cannot get there because it must carry cross weight for the other
    three claim types.
    """
    best_cross = max(single_signal_auroc(table, s, NUMERIC) for s in ("agree", "contra", "sem_dist"))
    best_evid = max(
        single_signal_auroc(table, s, NUMERIC) for s in ("support", "src_quality", "conflict")
    )
    assert best_cross < 0.52, f"some cross signal still helps on numeric: {best_cross:.3f}"
    assert best_evid > 0.60, f"no evidence signal helps on numeric: {best_evid:.3f}"


@pytest.mark.parametrize("claim_type", [ENTITY, EXTRACTIVE, ABSTRACTIVE])
def test_cross_family_carries_the_non_numeric_types(table, claim_type):
    contra = single_signal_auroc(table, "contra", claim_type)
    assert contra > 0.80, f"contra should be strong on type {claim_type}, got {contra:.3f}"


def test_evidence_family_is_weak_off_numeric(table):
    """If evidence worked everywhere, a flat model would ignore cross-model signals and
    score ~0.91 on numeric. The M2 gate depends on this being true."""
    for claim_type in (ENTITY, EXTRACTIVE, ABSTRACTIVE):
        auc = single_signal_auroc(table, "support", claim_type)
        assert 0.30 < auc < 0.48, f"support should be weak on type {claim_type}, got {auc:.3f}"


def test_extractive_agree_is_weaker_than_entity_agree(table):
    """Spec M1: `agree` is weak for extractive claims and strong for entity claims."""
    entity = single_signal_auroc(table, "agree", ENTITY)
    extractive = single_signal_auroc(table, "agree", EXTRACTIVE)
    assert entity < 0.45
    assert abs(0.5 - extractive) < abs(0.5 - entity), (
        f"agree is not weaker on extractive ({extractive:.3f}) than entity ({entity:.3f})"
    )


# -- planted structure: the inverted generator family -----------------------


def test_inverted_generator_flips_the_sign_of_agree(table):
    """Spec M1: one generator family where `agree` correlates *positively* with hallucination."""
    inverted = int(load_planted().get("inverted_generators", [4])[0])
    for claim_type in range(4):
        auc = single_signal_auroc(table, "agree", claim_type, generator=inverted)
        assert auc > 0.70, (
            f"claim type {CLAIM_TYPE_NAMES[claim_type]}: agree should rise with hallucination "
            f"for the inverted generator, got {auc:.3f}"
        )


def test_inverted_generator_is_opposite_to_the_standard_ones(table):
    inverted = int(load_planted().get("inverted_generators", [4])[0])
    for generator in [g for g in sorted(table["generator_id"].unique()) if g != inverted]:
        for claim_type in range(4):
            standard = single_signal_auroc(table, "agree", claim_type, generator=generator)
            flipped = single_signal_auroc(table, "agree", claim_type, generator=inverted)
            assert standard < 0.50 < flipped, (
                f"generator {generator} vs inverted {inverted}, type {claim_type}: "
                f"{standard:.3f} / {flipped:.3f}"
            )


def test_inversion_does_not_touch_the_evidence_family(table):
    """The inverted decoder hurts agreement only; evidence keeps its planted sign."""
    inverted = int(load_planted().get("inverted_generators", [4])[0])
    for claim_type in (NUMERIC, EXTRACTIVE):
        plain = single_signal_auroc(table, "support", claim_type)
        flipped = single_signal_auroc(table, "support", claim_type, generator=inverted)
        # both directions preserved: numeric stays informative, the rest stays weak
        if claim_type == NUMERIC:
            assert flipped < 0.30, f"numeric support should stay informative, got {flipped:.3f}"
        else:
            assert flipped > 0.30, f"extractive support should stay weak, got {flipped:.3f}"
        assert (plain < 0.30) == (flipped < 0.30)


# -- label-free signals and clustering --------------------------------------


def test_src_quality_is_label_free_by_construction(table):
    for claim_type in range(4):
        auc = single_signal_auroc(table, "src_quality", claim_type)
        assert abs(auc - 0.5) < 0.06, f"src_quality leaked the label on type {claim_type}: {auc:.3f}"


def test_sibling_claims_of_one_answer_are_clustered(table):
    """Random effects make questions non-i.i.d., which is why splits group by question."""
    grouped = table.groupby(["question_id", "generator_id"])["label"]
    mean_size = grouped.size().mean()
    observed_var = grouped.mean().var()
    binomial_var = table["label"].var() / mean_size
    assert observed_var > binomial_var * 1.25, (
        f"answer-level clustering is too weak: {observed_var:.4f} vs {binomial_var:.4f}"
    )


def test_label_noise_leaves_a_ceiling_below_perfect_separation(table):
    best = max(single_signal_auroc(table, s) for s in SIGNALS)
    assert best < 0.98, "noise should stop any single signal from being perfect"


def test_signal_means_match_the_planted_tables():
    """Direct check that emission means land where planted.yaml says they should.

    Beta emission is unbiased, so the observed mean of a signal on a claim type must
    equal ``(1 - p) * m_faithful + p * m_hallucinated`` for the realised rate ``p``.
    """
    cfg = load_planted()
    df = generate(cfg, seed=3, n_questions=600)
    for signal in ("agree", "contra", "support", "conflict"):
        for claim_type in range(4):
            name = CLAIM_TYPE_NAMES[claim_type]
            planted = cfg.signals[signal][name]
            rows = df[df["claim_type"] == claim_type]
            p = float(rows["label"].mean())
            expected = (1 - p) * planted["faithful"] + p * planted["hallucinated"]
            realised = float(rows[signal].mean())
            assert abs(realised - expected) < 0.08, (
                f"{signal}/{name}: realised {realised:.3f} vs planted {expected:.3f} at rate {p:.3f}"
            )
    assert np.isfinite(df[SIGNALS].to_numpy()).all()


def test_planted_tables_are_well_formed():
    """Guard the config itself: every entry is a probability in [0, 1]."""
    cfg = load_planted()
    for signal, by_type in cfg.signals.items():
        assert set(by_type.keys()) == set(CLAIM_TYPE_NAMES), signal
        for name, entry in by_type.items():
            for key in ("faithful", "hallucinated"):
                assert 0.0 <= float(entry[key]) <= 1.0, f"{signal}/{name}/{key}"
    for rate in cfg.base_rate.values():
        assert 0.0 < float(rate) < 1.0

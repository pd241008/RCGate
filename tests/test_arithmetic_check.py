"""Arithmetic verification tests (milestone M5).

The point of this module is that a refuted computation is not a matter of opinion, so the
tests pin exact numbers rather than ranges.
"""

from __future__ import annotations

import pandas as pd
import pytest

from rcgate.signals.arithmetic_check import (
    REFUTED,
    UNVERIFIABLE,
    VERIFIED,
    ArithmeticResult,
    check_against_context,
    check_claim,
    fold_into_support,
    summarise,
    verify_frame,
)

# -- the spec's own example -------------------------------------------------


def test_the_examples_from_the_proposal_are_checked():
    assert check_claim("847 x 12 = 10164").verdict == VERIFIED
    assert check_claim("847 x 12 = 10,164 units").verdict == VERIFIED
    assert check_claim("847 × 12 = 10164").verdict == VERIFIED


def test_a_wrong_product_is_refuted():
    r = check_claim("847 x 12 = 10165")
    assert r.verdict == REFUTED
    assert r.computed == 10164.0
    assert r.stated == 10165.0


# -- operators and formatting ----------------------------------------------


@pytest.mark.parametrize(
    "text,computed",
    [
        ("120 + 30 = 150", 150.0),
        ("120 - 30 = 90", 90.0),
        ("120 * 3 = 360", 360.0),
        ("120 / 4 = 30", 30.0),
        ("1,200 + 800 = 2,000", 2000.0),
        ("$1,200 + $800 = $2,000", 2000.0),
        ("12.5 * 4 = 50", 50.0),
        ("2 * 3 * 4 = 24", 24.0),
        ("(2 + 3) * 4 = 20", 20.0),
        ("100 / 8 = 12.5", 12.5),
    ],
)
def test_arithmetic_is_exact(text, computed):
    r = check_claim(text)
    assert r.computed == pytest.approx(computed), (text, r.as_dict())


@pytest.mark.parametrize("text", ["100 / 0 = 5", "0 / 0 = 1"])
def test_division_by_zero_is_unverifiable_not_a_crash(text):
    assert check_claim(text).verdict == UNVERIFIABLE


# -- honest refusals --------------------------------------------------------


@pytest.mark.parametrize(
    "text,why",
    [
        ("Output reached 847 tonnes.", "numbers but no expression"),
        ("The company was founded in 1998.", "a bare year"),
        ("Revenue rose to $3.8 billion.", "no expression to evaluate"),
        ("Costs fell by 12% year on year.", "no expression"),
    ],
)
def test_non_checkable_claims_are_left_alone(text, why):
    """Never guess. Folding a guess into support would be worse than folding nothing."""
    r = check_claim(text)
    assert r.verdict == UNVERIFIABLE, (why, r.as_dict())
    assert r.reason


def test_expression_without_a_stated_result_is_unverifiable():
    r = check_claim("Total output reached 847 x 12 units")
    assert r.verdict == UNVERIFIABLE
    assert r.computed == pytest.approx(10164.0)
    assert "no stated result" in r.reason


def test_unverifiable_leaves_support_untouched():
    assert fold_into_support(0.4, ArithmeticResult(UNVERIFIABLE)) == 0.4


# -- folding into the evidence signals --------------------------------------


def test_refutation_drives_support_down_hard():
    out = fold_into_support(0.9, ArithmeticResult(REFUTED))
    assert out < 0.15, out


def test_verification_only_nudges_support_up():
    """Proving one fragment right says little about the rest of the claim."""
    out = fold_into_support(0.30, ArithmeticResult(VERIFIED))
    assert 0.30 < out < 0.40, out


def test_folded_support_stays_in_the_unit_interval():
    for support in (0.0, 0.5, 1.0):
        for verdict in (VERIFIED, REFUTED, UNVERIFIABLE):
            assert 0.0 <= fold_into_support(support, ArithmeticResult(verdict)) <= 1.0


# -- context corroboration --------------------------------------------------


def test_operands_found_in_the_context_are_corroborated():
    ctx = "Output reached 847 tonnes and the plant ran 12 shifts."
    assert check_against_context("847 x 12 = 10164", ctx).verdict == VERIFIED


def test_operands_absent_from_the_context_downgrade_to_unverifiable():
    """Catches a product that is arithmetically fine but cites the wrong operands."""
    ctx = "Output reached 300 tonnes and the plant ran 9 shifts."
    r = check_against_context("847 x 12 = 10164", ctx)
    assert r.verdict == UNVERIFIABLE
    assert "context" in r.reason


def test_no_context_still_allows_a_plain_check():
    assert check_against_context("847 x 12 = 10164", None).verdict == VERIFIED


# -- frame integration ------------------------------------------------------


def _frame(rows):
    return pd.DataFrame(rows)


def test_verify_frame_only_touches_numeric_claims():
    df = _frame(
        [
            {"claim_text": "847 x 12 = 10164 units", "claim_type": 0, "support": 0.4, "conflict": 0.1},
            {"claim_text": "847 x 12 = 99999 units", "claim_type": 0, "support": 0.4, "conflict": 0.1},
            {"claim_text": "The headquarters is in Rotterdam.", "claim_type": 1,
             "support": 0.7, "conflict": 0.2},
        ]
    )
    out = verify_frame(df)
    assert list(out["arithmetic_verdict"]) == [VERIFIED, REFUTED, UNVERIFIABLE]
    assert list(out["arithmetic_verified"]) == [True, False, False]
    assert out.loc[0, "support"] < out.loc[2, "support"]
    assert out.loc[1, "conflict"] >= 0.9, "a refuted computation is strong conflict"


def test_verify_frame_leaves_non_numeric_signals_exactly_as_they_were():
    df = _frame(
        [{"claim_text": "847 x 12 = 10164", "claim_type": 3, "support": 0.55, "conflict": 0.2}]
    )
    out = verify_frame(df)
    assert out.loc[0, "support"] == 0.55
    assert out.loc[0, "conflict"] == 0.2


def test_verify_frame_keeps_signals_in_range():
    df = _frame(
        [
            {"claim_text": "10 x 10 = 1000", "claim_type": 0, "support": 0.0, "conflict": 0.0},
            {"claim_text": "10 x 10 = 100", "claim_type": 0, "support": 1.0, "conflict": 0.0},
        ]
    )
    out = verify_frame(df)
    assert out["support"].between(0, 1).all()
    assert out["conflict"].between(0, 1).all()


def test_summarise_reports_verdict_counts():
    df = _frame(
        [
            {"claim_text": "2 x 2 = 4", "claim_type": 0, "support": 0.5, "conflict": 0.0},
            {"claim_text": "2 x 2 = 5", "claim_type": 0, "support": 0.5, "conflict": 0.0},
            {"claim_text": "Nothing numeric.", "claim_type": 1, "support": 0.5, "conflict": 0.0},
        ]
    )
    report = summarise(verify_frame(df))
    assert report["counts"][VERIFIED] == 1
    assert report["counts"][REFUTED] == 1
    assert report["n_numeric_claims"] == 2
    assert summarise(df) == {}

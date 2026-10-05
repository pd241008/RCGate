"""Claim-type rule tests and the hand-labelled accuracy measurement (M5).

The accuracy report here is the evidence for the M5 decision: the spec says not to reach
for an LLM claim classifier "unless the rule-based version is clearly inadequate", and this
is what decides it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rcgate.claims.claim_type import (
    DEFAULT_RULE_ORDER,
    accuracy_report,
    classify,
    numeric_evidence,
    proper_nouns,
    span_overlap,
)
from rcgate.data.schema import ABSTRACTIVE, ENTITY, EXTRACTIVE, NUMERIC

FIXTURE = Path(__file__).parent / "fixtures" / "claim_type_labels.jsonl"


def load_labels() -> list[dict]:
    return [json.loads(line) for line in FIXTURE.read_text().splitlines() if line.strip()]


# -- the individual rules ---------------------------------------------------


@pytest.mark.parametrize(
    "text,expected_hit",
    [
        ("Total output reached 847 tonnes.", "digit"),
        ("Revenue rose by 12.4% year over year.", "percentage"),
        ("The average is 42.50 dollars.", "digit"),
        ("Margins improved to 18.2%.", "percentage"),
    ],
)
def test_numeric_rule_detects_quantities(text, expected_hit):
    hits = numeric_evidence(text)["hits"]
    assert any(h.startswith(expected_hit) for h in hits), hits


def test_numeric_rule_is_weak_on_a_bare_year():
    """'The policy was updated in 2019' is not a numeric claim."""
    weak = numeric_evidence("The policy was updated in 2019.")["strength"]
    strong = numeric_evidence("Output reached 240,000 ounces of silver in 2019.")["strength"]
    assert weak < strong
    assert weak < 1.5


def test_numeric_rule_detects_a_bare_expression():
    hits = numeric_evidence("The check gives 847 x 12 = 10164.")["hits"]
    assert "expression" in hits


def test_numeric_rule_detects_units_and_ratio_words():
    hits = numeric_evidence("Headcount fell by 8% to 3,760 employees.")["hits"]
    assert any(h.startswith("unit") for h in hits)
    assert any(h.startswith("ratio") for h in hits)


def test_proper_nouns_ignore_the_first_word_of_a_sentence():
    found = proper_nouns("The headquarters is located in Rotterdam.")
    assert "Rotterdam" in found


def test_proper_nouns_ignore_ordinary_sentence_starters():
    assert proper_nouns("Costs were contained even as volumes fell sharply.") == []


def test_proper_nouns_pick_up_acronyms():
    assert "NLI" in proper_nouns("The model relies on an NLI cross-encoder.")


def test_span_overlap_finds_a_lifted_run():
    claim = "The report states total output of 847 tonnes across all sites."
    context = "According to the annual report, total output reached 847 tonnes across all sites."
    span = span_overlap(claim, context)
    assert span["longest_run"] >= 4
    assert span["coverage"] > 0.7


def test_span_overlap_is_zero_without_context():
    assert span_overlap("Anything at all.", None)["longest_run"] == 0


# -- the classifier ---------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Total output reached 847 tonnes in 2019, up from 612 tonnes.", NUMERIC),
        ("The headquarters is located in Rotterdam.", ENTITY),
        ("The company's financial position weakened considerably over the period.", ABSTRACTIVE),
    ],
)
def test_classification_without_context(text, expected):
    assert classify(text).claim_type == expected


def test_classification_reports_the_rule_that_decided():
    c = classify("Total output reached 847 tonnes.")
    assert c.rule == "numeric"
    assert c.evidence["numeric"]["strength"] > 0
    assert set(c.evidence["scores"]) == {"numeric", "entity", "extractive", "abstractive"}


def test_classification_uses_the_context_for_extractive():
    claim = "The report states total output of 847 tonnes across all sites."
    context = "According to the annual report, total output reached 847 tonnes across all sites."
    assert classify(claim, context).claim_type == EXTRACTIVE


def test_a_lifted_claim_with_a_proper_noun_is_still_extractive():
    """Provenance should beat content: a name lifted from context is extractive."""
    claim = "The bridge spans the River Kelvin near Dunmore."
    context = "The bridge spans the River Kelvin near Dunmore and carries two lanes."
    assert classify(claim, context).claim_type == EXTRACTIVE


# -- the accuracy measurement ----------------------------------------------


def test_fixture_meets_the_spec_size_requirement():
    labels = load_labels()
    assert len(labels) >= 100, f"the hand-labelled sample must have >=100 claims, got {len(labels)}"
    kinds = {row["type"] for row in labels}
    assert kinds == {NUMERIC, ENTITY, EXTRACTIVE, ABSTRACTIVE}


def rule_based_accuracy_on_the_hand_labelled_sample():
    labels = load_labels()
    return accuracy_report(
        [row["type"] for row in labels],
        [classify(row["claim"], row.get("context")).claim_type for row in labels],
    )


def test_rule_based_accuracy_on_the_hand_labelled_sample():
    report = rule_based_accuracy_on_the_hand_labelled_sample()
    print("\nrule order:", DEFAULT_RULE_ORDER)
    print(f"accuracy: {report['accuracy']:.3f} on {report['n']} hand-labelled claims")
    print("recall:", report["recall"])
    print("confusion:")
    for truth, row in report["confusion"].items():
        print(f"  {truth:12s} -> {row}")
    # The M5 bar for keeping the rules rather than reaching for an LLM.
    #
    # CAVEAT ON THIS NUMBER: the fixture is author-written, not drawn from a real
    # benchmark, so 0.98 is an optimistic estimate of accuracy on TruthfulQA or RAGTruth
    # claims. Treat it as evidence that the rules are adequate in principle, not as a
    # measured benchmark score. See DECISIONS.md.
    assert report["accuracy"] >= 0.95, f"rule-based accuracy {report['accuracy']:.3f} is too low"


def test_only_the_two_debatable_hand_labels_are_wrong():
    """Pin the known failures so a regression elsewhere is visible.

    Both remaining errors are labelling judgement calls rather than rule bugs:
    "Ironbridge employs about 900 people" is a quantity and "another two years" is a
    duration, so numeric is defensible for each.
    """
    labels = load_labels()
    names = ["numeric", "entity", "extractive", "abstractive"]
    wrong = [
        (row["id"], names[row["type"]], names[classify(row["claim"], row.get("context")).claim_type])
        for row in labels
        if classify(row["claim"], row.get("context")).claim_type != row["type"]
    ]
    assert wrong == [("e018", "entity", "numeric"), ("a012", "abstractive", "numeric")]


def test_extractive_recall_is_high_after_the_provenance_fix():
    report = rule_based_accuracy_on_the_hand_labelled_sample()
    assert report["recall"]["extractive"] >= 0.90
    assert report["recall"]["abstractive"] >= 0.90
    assert report["recall"]["entity"] >= 0.90


def test_accuracy_is_reported_for_the_alternative_rule_order():
    """Provenance-vs-content precedence is a judgement call, so both are measured."""
    labels = load_labels()
    alternative = ("numeric", "entity", "extractive", "abstractive")
    report = accuracy_report(
        [row["type"] for row in labels],
        [classify(row["claim"], row.get("context"), rule_order=alternative).claim_type
         for row in labels],
    )
    print(f"\nalternative rule order {alternative}: accuracy {report['accuracy']:.3f}")
    print("recall:", report["recall"])
    assert report["accuracy"] >= 0.70


def test_confusion_matrix_rows_sum_to_the_class_support():
    labels = load_labels()
    report = accuracy_report(
        [row["type"] for row in labels],
        [classify(row["claim"], row.get("context")).claim_type for row in labels],
    )
    names = ["numeric", "entity", "extractive", "abstractive"]
    for name in names:
        assert sum(report["confusion"][name].values()) == report["support"][name]

"""Tests for the real signal extractors and their disk cache (milestone M5).

Everything here runs on the lexical fallback scorer, so the suite stays offline and
sub-second. What is pinned is the contract: the cached wrapper must compute once and return
identical values, the extractors must write six in-range signals, and the cached premises
must be claim-specific.
"""

from __future__ import annotations

import pandas as pd
import pytest

from rcgate.data.schema import SIGNAL_COLUMNS
from rcgate.signals.arithmetic_check import REFUTED, UNVERIFIABLE, VERIFIED, verify_frame
from rcgate.signals.cross_model import NEUTRAL_AGREE, NEUTRAL_CONTRA, score_claim
from rcgate.signals.evidence import (
    SOURCE_CONTEXT,
    SOURCE_NONE,
    gather_evidence,
    source_quality,
)
from rcgate.signals.evidence import (
    score_claim as evidence_score,
)
from rcgate.signals.extract import contract, extract_signals, premise_builder
from rcgate.signals.nli import CachedEmbedder, CachedScorer, Embedder, LexicalScorer

# -- cached scorer -------------------------------------------------------------


class CountingScorer(LexicalScorer):
    """A scorer that records how many times the underlying model was actually consulted."""

    name = "counting"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def score(self, premise: str, hypothesis: str):
        self.calls += 1
        return super().score(premise, hypothesis)


def test_cached_scorer_computes_each_pair_once(tiny_cache):
    inner = CountingScorer()
    scorer = CachedScorer(inner, tiny_cache)

    first = scorer.score("a dozen eggs cost 20 dollars", "A dozen eggs cost $20.")
    second = scorer.score("a dozen eggs cost 20 dollars", "A dozen eggs cost $20.")

    assert inner.calls == 1, "the second identical pair must come off disk"
    assert first.as_tuple() == second.as_tuple()
    assert tiny_cache.stats.hits == 1
    assert tiny_cache.stats.misses == 1


def test_cached_scorer_separates_different_pairs(tiny_cache):
    inner = CountingScorer()
    scorer = CachedScorer(inner, tiny_cache)
    entail = scorer.score("the stock rose 5 percent", "the stock rose 5 percent")
    contra = scorer.score("the stock rose 5 percent", "the stock fell 5 percent")

    assert inner.calls == 2
    assert entail.entailment > entail.contradiction
    assert contra.contradiction > contra.entailment


def test_cached_scorer_reports_the_backend_it_wraps(tiny_cache):
    scorer = CachedScorer(LexicalScorer(), tiny_cache)
    assert scorer.name == "lexical+disk"


def test_cached_embedder_stores_one_vector_per_text(tiny_cache):
    inner = Embedder(LexicalScorer())
    embedder = CachedEmbedder(inner, tiny_cache)

    first = embedder.embed(["profit rose", "profit rose", "costs fell"])
    second = embedder.embed(["profit rose", "costs fell"])

    assert first.shape == (3, embedder.dim)
    assert tiny_cache.stats.misses == 3, "one vector per distinct text, not per position"
    assert tiny_cache.stats.hits == 2
    # Repeated texts must map to the same row.
    assert first[0] == pytest.approx(first[1])
    assert second[0] == pytest.approx(first[0])


def test_cached_embedder_similarity_is_empty_safe(tiny_cache):
    embedder = CachedEmbedder(Embedder(LexicalScorer()), tiny_cache)
    assert embedder.best_sentence_similarity("a claim", []) == 0.0


def test_cached_values_survive_a_new_process_view_of_the_cache(tiny_cache):
    inner = CountingScorer()
    CachedScorer(inner, tiny_cache).score("a", "b")
    reopened = CachedScorer(CountingScorer(), tiny_cache)
    reopened.score("a", "b")
    assert reopened.inner.calls == 0


# -- premise selection ---------------------------------------------------------


def test_premise_builder_keeps_the_sentences_about_the_claim():
    text = (
        "The bank opened in 1904. Revenue rose 12 percent in 2019. "
        "The CEO resigned in March. Costs fell by 4 percent."
    )
    builder = premise_builder(top_k=2)
    premise = builder(text, "What happened to revenue in 2019?")

    assert "Revenue rose 12 percent in 2019." in premise
    assert len(premise.split(". ")) <= 3, premise


def test_premise_builder_falls_back_to_the_leading_sentences():
    builder = premise_builder(top_k=2)
    premise = builder("Alpha. Beta. Gamma.", "a query with no shared words at all")
    assert premise == "Alpha. Beta."


# -- cross-model signals -------------------------------------------------------


def test_a_claim_with_no_other_generator_is_left_neutral():
    scorer = LexicalScorer()
    signals = score_claim("Revenue rose 12 percent.", {}, 0, scorer, Embedder(scorer))
    assert signals.agree == NEUTRAL_AGREE
    assert signals.contra == NEUTRAL_CONTRA
    assert signals.n_others == 0
    assert signals.as_row()["sem_dist"] == 1.0


def test_agree_and_contra_stay_inside_the_unit_interval():
    scorer = LexicalScorer()
    answers = {
        0: "Revenue rose 12 percent in 2019.",
        1: "Revenue rose 12 percent in 2019.",
        2: "Revenue fell by 12 percent in 2019.",
    }
    row = score_claim(
        "Revenue rose 12 percent in 2019.", answers, 0, scorer, Embedder(scorer)
    ).as_row()
    for key in ("agree", "contra", "sem_dist"):
        assert 0.0 <= row[key] <= 1.0
    assert row["cross_n_others"] == 2
    # One generator denies the claim outright, so contra has to rise.
    assert row["contra"] > 0.3


def test_contra_is_a_max_over_generators_not_a_mean():
    scorer = LexicalScorer()
    answers = {
        0: "The figure was 40 percent.",
        1: "The figure was 40 percent.",
        2: "The figure was 40 percent.",
        3: "The figure was not 40 percent at all, it was 90 percent.",
    }
    signals = score_claim("The figure was 40 percent.", answers, 0, scorer, Embedder(scorer))
    mean_all = sum(p["contradiction"] for p in signals.per_generator) / len(
        signals.per_generator
    )
    assert signals.contra >= mean_all - 1e-9


# -- evidence signals ----------------------------------------------------------


def test_context_is_the_evidence_corpus_and_none_is_admitted():
    with_context = gather_evidence(
        "Revenue rose 12 percent in 2019.", "The bank reported revenue growth. " * 5
    )
    assert with_context.source == SOURCE_CONTEXT
    assert with_context.sentences
    assert with_context.src_quality == pytest.approx(0.90)

    without = gather_evidence("Revenue rose 12 percent in 2019.", None)
    assert without.source == SOURCE_NONE
    assert without.sentences == []
    assert without.src_quality == pytest.approx(0.10)


def test_no_evidence_leaves_the_signals_neutral_rather_than_confident():
    scorer = LexicalScorer()
    signals = evidence_score("Revenue rose 12 percent.", None, scorer, Embedder(scorer))
    row = signals.as_row()
    assert row["support"] == pytest.approx(0.5)
    assert row["conflict"] == pytest.approx(0.0)
    assert row["evidence_n_passages"] == 0


def test_src_quality_depends_on_the_source_not_the_claim():
    """The same claim must score the same from the same source, hallucinated or not."""
    assert source_quality(SOURCE_CONTEXT) == source_quality(SOURCE_CONTEXT)
    assert source_quality("web", "en.wikipedia.org") > source_quality("web", "some-blog.xyz")
    assert source_quality("none") < source_quality("web", "some-blog.xyz")


def test_support_rises_when_the_evidence_actually_states_the_claim():
    scorer = LexicalScorer()
    supported = evidence_score(
        "Revenue rose 12 percent in 2019.",
        "The bank reported that revenue rose 12 percent in 2019, its best year.",
        scorer,
        Embedder(scorer),
    )
    unsupported = evidence_score(
        "Revenue rose 12 percent in 2019.",
        "The bank reported a small profit in 2019 and closed two branches.",
        scorer,
        Embedder(scorer),
    )
    assert supported.support > unsupported.support
    for row in (supported.as_row(), unsupported.as_row()):
        for key in ("support", "src_quality", "conflict"):
            assert 0.0 <= row[key] <= 1.0


# -- arithmetic folding into the evidence family --------------------------------


def test_a_refuted_expression_lifts_conflict_and_drops_support():
    frame = pd.DataFrame(
        {
            "claim_text": ["847 x 12 = 10165", "847 x 12 = 10164"],
            "claim_type": [0, 0],
            "context": ["", ""],
            "support": [0.5, 0.5],
            "conflict": [0.1, 0.1],
        }
    )
    out = verify_frame(frame)
    assert out["arithmetic_verdict"].tolist() == [REFUTED, VERIFIED]
    assert out["support"][0] < out["support"][1]
    assert out["conflict"][0] > out["conflict"][1]
    assert 0.0 <= out["support"].min() and out["conflict"].max() <= 1.0


def test_non_numeric_claims_are_left_alone_by_the_verifier():
    frame = pd.DataFrame(
        {"claim_text": ["The bank opened in 1904."], "claim_type": [1],
         "context": [""], "support": [0.4], "conflict": [0.2]}
    )
    out = verify_frame(frame)
    assert out["support"][0] == pytest.approx(0.4)
    assert out["conflict"][0] == pytest.approx(0.2)


# -- the assembled extractor ---------------------------------------------------


def _frame_and_answers() -> tuple[pd.DataFrame, dict]:
    claims = pd.DataFrame(
        {
            "question_id": ["q1", "q1", "q1"],
            "claim_id": ["c1", "c2", "c3"],
            "claim_text": [
                "Revenue rose 12 percent in 2019.",
                "The bank opened in 1904 in Manchester.",
                "847 x 12 = 10165 units.",
            ],
            "benchmark": ["ragtruth"] * 3,
            "context": [
                "The bank reported that revenue rose 12 percent in 2019.",
                "Founded in 1904, the bank traded as the Northern Union Bank of Manchester.",
                "The site shipped 847 units in each of 12 months.",
            ],
            "claim_type": [3, 2, 0],
            "generator_id": [0, 1, 2],
            "label": [0, 0, 1],
        }
    )
    answers = {
        "q1": {
            0: "Revenue rose 12 percent in 2019.",
            1: "The bank opened in 1904 in Manchester.",
            2: "847 x 12 = 10164 units.",
        }
    }
    return claims, answers


def test_extract_signals_fills_six_signals_and_reports(tmp_path):
    from rcgate.config import Config

    cfg = Config({"signals": {"evidence_top_k": 2, "premise_top_k": 2, "arithmetic": True}})
    claims, answers = _frame_and_answers()
    scorer = LexicalScorer()

    frame, report = extract_signals(
        claims, cfg, answers, scorer=scorer, embedder=Embedder(scorer)
    )

    for column in ("agree", "contra", "sem_dist", "support", "src_quality", "conflict"):
        assert frame[column].between(0.0, 1.0).all(), column
    assert report.n_claims == 3
    assert report.backend == "lexical"
    assert report.sections["cross_model"]["mean_others"] == pytest.approx(2.0)
    assert report.sections["arithmetic"]["counts"] == {UNVERIFIABLE: 2, REFUTED: 1}


def test_extract_signals_is_reproducible(tmp_path):
    from rcgate.config import Config

    cfg = Config({"signals": {"evidence_top_k": 2, "arithmetic": True}})
    claims, answers = _frame_and_answers()
    scorer = LexicalScorer()
    a, _ = extract_signals(claims, cfg, answers, scorer=scorer, embedder=Embedder(scorer))
    b, _ = extract_signals(claims, cfg, answers, scorer=scorer, embedder=Embedder(scorer))
    pd.testing.assert_frame_equal(a, b)


def test_contract_drops_the_context_column_and_keeps_provenance():
    claims, _ = _frame_and_answers()
    contracted = contract(claims.assign(src_quality=0.9, support=0.5, conflict=0.1,
                                       agree=0.5, contra=0.5, sem_dist=0.5, label=0))
    assert list(contracted.columns[: len(SIGNAL_COLUMNS)]) == SIGNAL_COLUMNS
    assert "context" not in contracted.columns


def test_extraction_through_the_cache_returns_the_same_numbers(tiny_cache):
    from rcgate.config import Config

    cfg = Config({"signals": {"evidence_top_k": 2, "arithmetic": True}})
    claims, answers = _frame_and_answers()

    plain = LexicalScorer()
    direct, _ = extract_signals(claims, cfg, answers, scorer=plain, embedder=Embedder(plain))

    cached_scorer = CachedScorer(plain, tiny_cache)
    cached, report = extract_signals(
        claims, cfg, answers, scorer=cached_scorer,
        embedder=CachedEmbedder(Embedder(plain), tiny_cache), cache=tiny_cache,
    )

    assert report.cache_misses > 0
    assert direct[["agree", "contra", "sem_dist", "support", "conflict"]].round(9).equals(
        cached[["agree", "contra", "sem_dist", "support", "conflict"]].round(9)
    )


def test_a_second_purely_cached_extraction_computes_nothing(tiny_cache):
    from rcgate.config import Config

    cfg = Config({"signals": {"evidence_top_k": 2, "arithmetic": True}})
    claims, answers = _frame_and_answers()
    plain = LexicalScorer()

    for _ in range(2):
        _, report = extract_signals(
            claims, cfg, answers,
            scorer=CachedScorer(plain, tiny_cache),
            embedder=CachedEmbedder(Embedder(plain), tiny_cache),
            cache=tiny_cache,
        )
    assert report.cache_misses == 0
    assert report.cache_hits > 0


def test_the_compute_cache_ignores_the_api_budget_and_dry_run(tmp_path):
    """Local CPU scorers must not be blocked by ``budget.dry_run`` or capped by ``max_calls``."""
    from rcgate.config import Config
    from rcgate.signals.nli import compute_cache

    cfg = Config({"budget": {"dry_run": True, "max_calls": 1}, "signals": {}})
    cache = compute_cache(cfg, root=tmp_path / "compute")
    assert cache.budget.dry_run is False
    assert cache.budget.max_calls is None

    scorer = CachedScorer(LexicalScorer(), cache)
    scorer.score("a", "b")
    scorer.score("c", "d")
    assert cache.stats.calls_made == 2

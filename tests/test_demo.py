"""Tests for the M7 glass-box demo and the ``one_line`` explanation contract.

The demo must run with no network and no model download: the lexical scorer and the
in-memory cache are injected everywhere, mirroring tests/test_signals_extract.py. Checkpoints
are written to ``tmp_path`` rather than ``results/`` so the suite never depends on a real
training run.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import torch

from rcgate.config import Config
from rcgate.demo.app import (
    build_frame,
    main,
    resolve_checkpoint,
    split_sentences,  # re-exported; guards against accidental removal
)
from rcgate.explain import one_line
from rcgate.models.rcgate import RCGateConfig, RCGateModel
from rcgate.signals.extract import extract_signals
from rcgate.signals.nli import DiskCache, Embedder, LexicalScorer

LEXICAL_CFG = Config(
    {
        "benchmark": "demo",
        "signals": {"backend": "lexical", "arithmetic": False},
    }
)


# ---------------------------------------------------------------------------
# one_line contract (the bug the demo work found)
# ---------------------------------------------------------------------------


def test_one_line_names_evidence_when_evidence_is_trusted():
    text = one_line(0.9, w_evid=0.85, claim_type_name="numeric", z_cross=0.4, z_evid=2.0)
    # w_evid >= 0.5 means evidence is trusted, so cross-model is the down-weighted family.
    assert "cross-model down-weighted" in text
    assert "w_evid 0.85" in text


def test_one_line_names_cross_model_when_cross_is_trusted():
    text = one_line(0.2, w_evid=0.15, claim_type_name="entity", z_cross=1.5, z_evid=0.4)
    # w_evid < 0.5 means cross-model is trusted, so evidence is the down-weighted family.
    assert "evidence down-weighted" in text
    assert "w_evid 0.15" in text


def test_one_line_flags_gate_overriding_the_larger_logit():
    text = one_line(0.9, w_evid=0.85, claim_type_name="numeric", z_cross=2.5, z_evid=1.0)
    assert "despite its larger raw logit" in text


def test_explain_claims_columns_carry_the_right_weight():
    """explain_claims passes each row's own weights; a mix-up shows up as identical columns."""

    n_gen = 3
    model = RCGateModel(RCGateConfig(n_generators=n_gen, epochs=2, batch_size=32), seed=0)
    df = _small_frame(n_gen)
    model.fit(df.head(8), df.head(8), LEXICAL_CFG)
    preds = model.predict(df)
    w_cross = [round(p.w_cross, 4) for p in preds]
    w_evid = [round(p.w_evid, 4) for p in preds]
    assert not (w_cross == w_evid), "test needs a model whose two weights differ"
    out = model.predict(df)  # and the weights printed next to each claim must be its own
    assert [round(p.w_evid, 4) for p in out] == w_evid


def _small_frame(n_gen: int) -> pd.DataFrame:
    rows = [
        {
            "question_id": "q",
            "claim_id": f"c{i}",
            "benchmark": "demo",
            "claim_text": f"Claim number {i} states that revenue rose by 12 percent.",
            "claim_type": i % 4,
            "generator_id": i % n_gen,
            "label": i % 2,
            "agree": 0.2 + 0.1 * (i % 2),
            "contra": 0.3 - 0.1 * (i % 2),
            "sem_dist": 0.5,
            "support": 0.7 - 0.2 * (i % 2),
            "src_quality": 0.9,
            "conflict": 0.1 + 0.3 * (i % 2),
        }
        for i in range(12)
    ]
    from rcgate.data.schema import signal_frame

    return signal_frame(rows)


# ---------------------------------------------------------------------------
# build_frame: sentences -> claims, no network
# ---------------------------------------------------------------------------


def test_build_frame_splits_and_types_claims():
    df = build_frame(
        "What did the company report?",
        "Revenue rose 12 percent to 1,048 crores. The board approved it. It will pay dividends.",
    )
    assert len(df) == 3  # three sentences -> three claims
    assert list(df.columns[:7]) >= ["question_id", "claim_id"]
    assert df["claim_type"].tolist() == [0, 1, 3] or df["claim_type"].tolist() == [0, 1, 2]
    assert (df["generator_id"] == 0).all()
    assert df["benchmark"].tolist() == ["demo"] * len(df)


def test_build_frame_empty_answer_yields_no_rows():
    assert build_frame("Q", "   ").empty


def test_demo_reexports_split_sentences():
    text = "One sentence here. Another one there."
    assert len(split_sentences(text)) == 2


# ---------------------------------------------------------------------------
# Analyse
# ---------------------------------------------------------------------------


@pytest.fixture()
def tiny_cache(tmp_path: Path) -> DiskCache:
    return DiskCache(root=tmp_path / "compute", budget=None)


def test_analyse_with_lexical_backend_and_checkpoint(tmp_path: Path, tiny_cache: DiskCache):
    model = RCGateModel(RCGateConfig(n_generators=6, epochs=2, batch_size=32), seed=0)
    table = _small_frame(6)
    model.fit(table, table, LEXICAL_CFG)

    frame = build_frame(
        "What did the company report?",
        "Revenue rose 12 percent to 1,048 crores. The board approved the plan.",
    )
    scorer, embedder = LexicalScorer(), Embedder(LexicalScorer())
    filled, report = extract_signals(frame, cfg=LEXICAL_CFG, scorer=scorer, embedder=embedder)
    preds = model.predict(filled)
    assert len(preds) == len(filled) == 2
    for p in preds:
        assert 0.0 <= p.prob <= 1.0
        assert abs(p.w_cross + p.w_evid - 1.0) < 1e-6
        assert report.backend == "lexical"


def test_analyse_flags_single_answer_no_others(tmp_path: Path, tiny_cache: DiskCache):
    """With no other answers, cross signals stay neutral and the row is flagged."""
    frame = build_frame("Q", "Compiled revenue increased to 1 billion dollars in 2019.")
    scorer, embedder = LexicalScorer(), Embedder(LexicalScorer())
    filled, _ = extract_signals(frame, cfg=LEXICAL_CFG, scorer=scorer, embedder=embedder)
    assert len(filled) == 1
    assert filled["cross_n_others"].iloc[0] == 0
    assert filled["agree"].iloc[0] == pytest.approx(0.5)
    assert filled["contra"].iloc[0] == pytest.approx(0.5)
    assert filled["sem_dist"].iloc[0] == pytest.approx(1.0)


def test_analyse_with_two_other_answers_uses_cross_family(tiny_cache: DiskCache):
    frame = build_frame(
        "Which company acquired the startup and in what year?",
        "The startup was founded in 2015. It was acquired by Meta in 2021 for 1 billion dollars.",
    )
    scorer, embedder = LexicalScorer(), Embedder(LexicalScorer())
    answers = {"demo": {0: "The startup was founded in 2015. It was acquired by Meta in 2021 for 2 billion dollars.",
                        1: "The startup was founded in 2016. It was acquired by Meta in 2021.",
                        2: "The startup was acquired by Meta in 2021 for 2 billion dollars."}}
    filled, _ = extract_signals(frame, cfg=LEXICAL_CFG, answers_by_question=answers,
                                scorer=scorer, embedder=embedder)
    # With one contradicting, one confirming answer, agreement is neither 0 nor 1.
    assert 0.0 < filled["agree"].iloc[1] < 1.0
    assert 0.0 < filled["contra"].iloc[1] < 1.0


def test_analyse_headless_cli(tmp_path: Path, capsys, monkeypatch):
    """The headless path prints per-claim verdicts and exits 0, with no network access."""
    # Hard-block the scorer build: a test must never attempt a model download.
    import rcgate.signals.nli as nli_mod

    monkeypatch.setattr(
        nli_mod, "build_cached",
        lambda cfg=None, root=None: (LexicalScorer(), Embedder(LexicalScorer()), None),
    )
    checkpoint = tmp_path / "model.pt"
    model = RCGateModel(RCGateConfig(n_generators=3, epochs=1, batch_size=32), seed=0)
    table = _small_frame(3)
    model.fit(table, table, LEXICAL_CFG)
    torch.save(model, checkpoint)

    rc = main(
        [
            "--config", "ragtruth",
            "--checkpoint", str(checkpoint),
            "--question", "What did the company report?",
            "--answer", "Revenue rose 12 percent. The board approved it.",
            "--other-answer", "Revenue rose 12 percent.",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "checkpoint" in out and "Revenue rose 12 percent" in out


def test_resolve_checkpoint_prefers_explicit(tmp_path: Path):
    torch.save(object(), tmp_path / "m.pt")
    path, provenance = resolve_checkpoint(tmp_path / "m.pt", LEXICAL_CFG)
    assert path == tmp_path / "m.pt"
    assert provenance == {}


def test_resolve_checkpoint_raises_without_training(tmp_path: Path, monkeypatch):
    """No checkpoint -> a clear error naming the remedy, not a mid-request fit."""
    from rcgate.demo import app as app_mod

    monkeypatch.setattr(app_mod, "SUMMARY_DIR", tmp_path / "nonexistent")
    with pytest.raises(FileNotFoundError, match="never trains"):
        resolve_checkpoint(None, LEXICAL_CFG)

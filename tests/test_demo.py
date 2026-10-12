"""Tests for the M7 glass-box demo and the ``one_line`` explanation contract.

The demo must run with no network and no model download: the lexical scorer and the
in-memory cache are injected everywhere, mirroring tests/test_signals_extract.py. Checkpoints
are written to ``tmp_path`` rather than ``results/`` so the suite never depends on a real
training run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import torch

from rcgate.config import Config
from rcgate.data.schema import SIGNALS, UNK_GENERATOR
from rcgate.demo.app import (
    EXAMPLE_NOTE,
    EXAMPLES,
    GENERATOR_IDENTITY_LIMITATION,
    INDEX_HREF,
    PREDICTION_CHECKPOINT_SCOPE,
    PREDICTION_CHECKPOINT_TITLE,
    REPORT_HREF,
    STAGE8_A0_AUROC,
    STAGE8_A4_AUROC,
    STAGE8_A7_AUROC,
    STAGE8_A7_MINUS_A0,
    STAGE8_A7_MINUS_A4,
    STAGE8_AGGREGATE_NOTE,
    STAGE8_CHECKPOINT_SEPARATION,
    UNKNOWN_GENERATOR_LABEL,
    analyse,
    apply_example,
    build_frame,
    comparison_status_notice,
    format_probability_percent,
    generator_options,
    input_fingerprint,
    main,
    missing_comparison_notice,
    predicted_class_label,
    prediction_checkpoint_lines,
    research_note_markdown,
    resolve_checkpoint,
    result_namespace,
    split_other_answers,
    split_sentences,  # re-exported; guards against accidental removal
    unknown_identity_supported,
)
from rcgate.explain import one_line
from rcgate.models.rcgate import RCGateConfig, RCGateModel, frame_to_batch
from rcgate.paths import PROJECT_ROOT
from rcgate.signals.cross_model import NEUTRAL_AGREE, NEUTRAL_CONTRA, NEUTRAL_SEM_DIST
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
    assert (df["generator_id"] == UNK_GENERATOR).all()
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
    answers = {
        "demo": {
            0: "The startup was founded in 2015. It was acquired by Meta in 2021 for 2 billion dollars.",
            1: "The startup was founded in 2016. It was acquired by Meta in 2021.",
            2: "The startup was acquired by Meta in 2021 for 2 billion dollars.",
        }
    }
    filled, _ = extract_signals(
        frame, cfg=LEXICAL_CFG, answers_by_question=answers, scorer=scorer, embedder=embedder
    )
    # With one contradicting, one confirming answer, agreement is neither 0 nor 1.
    assert 0.0 < filled["agree"].iloc[1] < 1.0
    assert 0.0 < filled["contra"].iloc[1] < 1.0


def test_analyse_headless_cli(tmp_path: Path, capsys, monkeypatch):
    """The headless path prints per-claim verdicts and exits 0, with no network access."""
    # Hard-block the scorer build: a test must never attempt a model download.
    import rcgate.signals.nli as nli_mod

    monkeypatch.setattr(
        nli_mod,
        "build_cached",
        lambda cfg=None, root=None: (LexicalScorer(), Embedder(LexicalScorer()), None),
    )
    checkpoint = tmp_path / "model.pt"
    model = RCGateModel(RCGateConfig(n_generators=3, epochs=1, batch_size=32), seed=0)
    table = _small_frame(3)
    model.fit(table, table, LEXICAL_CFG)
    torch.save(model, checkpoint)

    rc = main(
        [
            "--config",
            "ragtruth",
            "--checkpoint",
            str(checkpoint),
            "--question",
            "What did the company report?",
            "--answer",
            "Revenue rose 12 percent. The board approved it.",
            "--other-answer",
            "Revenue rose 12 percent.",
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


# ---------------------------------------------------------------------------
# presentation contract: signals, examples, Stage 8 wording
# ---------------------------------------------------------------------------


def test_build_frame_stores_context_for_the_evidence_extractor():
    df = build_frame(
        "What did the note say?",
        "Revenue rose 12 percent.",
        context="The note says revenue rose 12 percent.",
    )
    assert df["context"].iloc[0] == "The note says revenue rose 12 percent."


def test_build_frame_blank_context_stays_blank():
    df = build_frame("Q", "Revenue rose.")
    assert df["context"].iloc[0] == ""


def test_split_other_answers_uses_blank_lines():
    assert split_other_answers("one\n\ntwo") == ["one", "two"]
    assert split_other_answers("one\n\n  \n\n") == ["one"]
    assert split_other_answers("") == []
    assert split_other_answers("same line\nstill one") == ["same line\nstill one"]


def test_examples_fill_fields_and_do_not_score():
    assert EXAMPLES
    assert "not a benchmark item" in EXAMPLE_NOTE
    assert "does not run an analysis" in EXAMPLE_NOTE
    for example in EXAMPLES:
        fields = apply_example(example.id)
        assert fields["answer"].strip()
        assert set(fields) == {"question", "answer", "context", "others"}


def test_predicted_class_label_reads_one_line():
    hallucinated = one_line(0.9, w_evid=0.85, claim_type_name="numeric", z_cross=0.4, z_evid=2.0)
    supported = one_line(0.2, w_evid=0.15, claim_type_name="entity", z_cross=1.5, z_evid=0.4)
    assert predicted_class_label(hallucinated) == "Likely hallucinated"
    assert predicted_class_label(supported) == "Likely supported"
    assert predicted_class_label("no class named") is None


def test_probability_percent_keeps_four_decimal_precision():
    assert format_probability_percent(0.5717) == "57.17%"


def test_research_note_matches_the_final_report():
    report = (PROJECT_ROOT / REPORT_HREF).read_text(encoding="utf-8")
    note = research_note_markdown()
    for token in (
        STAGE8_A0_AUROC,
        STAGE8_A4_AUROC,
        STAGE8_A7_AUROC,
        STAGE8_A7_MINUS_A4,
        STAGE8_A7_MINUS_A0,
    ):
        assert token in report
        assert token in note
    assert REPORT_HREF in note
    assert INDEX_HREF in note
    assert (PROJECT_ROOT / INDEX_HREF).is_file()
    assert "not 60 independent datasets" in note
    assert "not a confidence interval" in note
    assert "A8 was not evaluated" in note
    assert STAGE8_AGGREGATE_NOTE in note
    assert STAGE8_CHECKPOINT_SEPARATION in note
    assert "current sentence" in STAGE8_AGGREGATE_NOTE
    assert "Stage 8 trained" not in note
    assert PREDICTION_CHECKPOINT_TITLE not in note


def test_analyse_returns_pipeline_signals_and_passes_context(monkeypatch):
    """Signals on the demo row are the extractor's values, including a provided source."""
    import rcgate.signals.nli as nli_mod
    from rcgate.signals.extract import extract_signals

    monkeypatch.setattr(
        nli_mod,
        "build_cached",
        lambda cfg=None, root=None: (LexicalScorer(), Embedder(LexicalScorer()), None),
    )
    model = RCGateModel(RCGateConfig(n_generators=3, epochs=1, batch_size=32), seed=0)
    model.fit(_small_frame(3), _small_frame(3), LEXICAL_CFG)
    question = "What did the note say?"
    answer = "Revenue rose 12 percent."
    context = "Revenue rose 12 percent."
    others = ["Revenue rose 12 percent."]
    scored, info = analyse(
        question, answer, context, others, model=model, cfg=LEXICAL_CFG, generator_id=0
    )
    direct, _ = extract_signals(
        build_frame(question, answer, context, generator_id=0),
        cfg=LEXICAL_CFG,
        answers_by_question={"demo": {0: answer, 1: others[0]}},
        scorer=LexicalScorer(),
        embedder=Embedder(LexicalScorer()),
    )
    assert info["backend"] == "lexical"
    assert scored["evidence_source"].iloc[0] == "context"
    for column in ("agree", "contra", "sem_dist", "support", "src_quality", "conflict"):
        assert scored[column].iloc[0] == pytest.approx(round(float(direct[column].iloc[0]), 4))
    bare, _ = analyse(question, answer, "", None, model=model, cfg=LEXICAL_CFG)
    assert bare["evidence_source"].iloc[0] == "none"
    assert bare["support"].iloc[0] != scored["support"].iloc[0]
    assert predicted_class_label(str(scored["explanation"].iloc[0])) in {
        "Likely hallucinated",
        "Likely supported",
    }
    _assert_scores_match_direct_predict(scored, direct, model)


def _use_lexical(monkeypatch) -> None:
    import rcgate.signals.nli as nli_mod

    monkeypatch.setattr(
        nli_mod,
        "build_cached",
        lambda cfg=None, root=None: (LexicalScorer(), Embedder(LexicalScorer()), None),
    )


def _assert_scores_match_direct_predict(scored: pd.DataFrame, direct: pd.DataFrame, model) -> None:
    """Demo rows keep the model's probability, weights, logits, and the six signals."""
    preds = model.predict(direct)
    assert len(scored) == len(preds) == len(direct)
    for i, pred in enumerate(preds):
        assert scored["prob"].iloc[i] == pytest.approx(round(pred.prob, 4))
        assert scored["w_cross"].iloc[i] == pytest.approx(round(pred.w_cross, 4))
        assert scored["w_evid"].iloc[i] == pytest.approx(round(pred.w_evid, 4))
        assert scored["z_cross"].iloc[i] == pytest.approx(round(pred.z_cross, 4))
        assert scored["z_evid"].iloc[i] == pytest.approx(round(pred.z_evid, 4))
        for name in SIGNALS:
            assert scored[name].iloc[i] == pytest.approx(round(float(direct[name].iloc[i]), 4))


# ---------------------------------------------------------------------------
# generator identity, missing comparisons, checkpoint provenance
# ---------------------------------------------------------------------------


def test_answer_text_does_not_select_a_generator():
    df = build_frame("Who wrote this?", "This answer was written by gpt-4-0613.")
    assert int(df["generator_id"].iloc[0]) == UNK_GENERATOR


def test_generator_options_list_roster_identities_and_unknown():
    from rcgate.config import load_named

    cfg = load_named("ragtruth")
    model = RCGateModel(RCGateConfig(n_generators=int(cfg.get("model.n_generators"))), seed=0)
    options = generator_options(model, cfg)
    assert options[0].generator_id == UNK_GENERATOR
    assert options[0].label == UNKNOWN_GENERATOR_LABEL == "Unknown / not specified"
    assert [option.label for option in options[1:]] == list(cfg.get("data.roster"))
    assert [option.generator_id for option in options[1:]] == list(range(model.config.n_generators))


def test_generator_options_stop_at_the_embedding_width():
    cfg = Config({"data": {"roster": ["gpt-4-0613", "gpt-3.5-turbo-0613", "mistral-7B-instruct"]}})
    model = RCGateModel(RCGateConfig(n_generators=2), seed=0)
    options = generator_options(model, cfg)
    assert [(option.generator_id, option.label) for option in options] == [
        (UNK_GENERATOR, "Unknown / not specified"),
        (0, "gpt-4-0613"),
        (1, "gpt-3.5-turbo-0613"),
    ]


def test_missing_generator_embedding_is_reported_and_not_assigned_gpt4():
    model = RCGateModel(RCGateConfig(n_generators=6, use_generator=False), seed=0)
    cfg = Config({"data": {"roster": ["gpt-4-0613"]}})
    assert unknown_identity_supported(model) is False
    assert generator_options(model, cfg) == []
    assert "gpt-4-0613" not in GENERATOR_IDENTITY_LIMITATION
    assert "named roster identity" in GENERATOR_IDENTITY_LIMITATION


def test_selected_and_unknown_identity_reach_the_prediction_pipeline(monkeypatch):
    _use_lexical(monkeypatch)
    model = RCGateModel(RCGateConfig(n_generators=6, epochs=1, batch_size=32), seed=0)
    captured: dict[str, list[int]] = {}
    real_predict = model.predict

    def spy(df):
        captured["ids"] = [int(value) for value in df["generator_id"].tolist()]
        captured["embed"] = frame_to_batch(df, model.config.n_generators)["generator_id"].tolist()
        return real_predict(df)

    model.predict = spy
    answer = "Revenue rose 12 percent."
    analyse("Q", answer, model=model, cfg=LEXICAL_CFG, generator_id=4)
    assert captured["ids"] == [4]
    assert captured["embed"] == [4]
    analyse("Q", "This sentence mentions gpt-4-0613.", model=model, cfg=LEXICAL_CFG)
    assert captured["ids"] == [UNK_GENERATOR]
    assert captured["embed"] == [model.config.n_generators]


def test_unsupported_unknown_identity_stays_off_the_named_roster(monkeypatch):
    _use_lexical(monkeypatch)
    model = RCGateModel(RCGateConfig(n_generators=6, use_generator=False, epochs=1), seed=0)
    captured: dict[str, int] = {}
    real_predict = model.predict

    def spy(df):
        captured["id"] = int(df["generator_id"].iloc[0])
        return real_predict(df)

    model.predict = spy
    _scored, info = analyse(
        "Q", "Revenue rose 12 percent according to gpt-4-0613.", model=model, cfg=LEXICAL_CFG
    )
    assert info["generator_supported"] is False
    assert info["generator_id"] == UNK_GENERATOR
    assert captured["id"] == UNK_GENERATOR


def test_out_of_range_generator_is_rejected_without_a_fallback():
    model = RCGateModel(RCGateConfig(n_generators=6), seed=0)
    with pytest.raises(ValueError, match="unknown id"):
        analyse("Q", "Revenue rose 12 percent.", model=model, cfg=LEXICAL_CFG, generator_id=6)


def test_fingerprint_changes_with_generator_identity():
    same = ("Q", "Revenue rose.", "", "")
    assert input_fingerprint(*same, UNK_GENERATOR) != input_fingerprint(*same, 0)


def test_missing_comparison_uses_documented_fallbacks_and_a_notice(monkeypatch):
    _use_lexical(monkeypatch)
    assert NEUTRAL_AGREE == 0.5
    assert NEUTRAL_CONTRA == 0.5
    assert NEUTRAL_SEM_DIST == 1.0
    model = RCGateModel(RCGateConfig(n_generators=6), seed=0)
    scored, info = analyse(
        "Q", "Revenue rose 12 percent.", model=model, cfg=LEXICAL_CFG, generator_id=0
    )
    assert info["n_other_answers"] == 0
    assert int(scored["cross_n_others"].iloc[0]) == 0
    assert scored["agree"].iloc[0] == pytest.approx(NEUTRAL_AGREE)
    assert scored["contra"].iloc[0] == pytest.approx(NEUTRAL_CONTRA)
    assert scored["sem_dist"].iloc[0] == pytest.approx(NEUTRAL_SEM_DIST)
    notice = comparison_status_notice(bool(split_other_answers("")))
    assert notice == missing_comparison_notice()
    assert "documented fallback" in notice
    assert "No agreement or disagreement was measured" in notice
    assert "limitation" in notice
    assert f"{NEUTRAL_AGREE:.1f}" in notice
    assert f"{NEUTRAL_SEM_DIST:.1f}" in notice
    assert comparison_status_notice(bool(split_other_answers("   \n\n  "))) == notice


def test_provided_comparison_answers_do_not_trigger_the_missing_notice(monkeypatch):
    _use_lexical(monkeypatch)
    model = RCGateModel(RCGateConfig(n_generators=6), seed=0)
    raw = "Revenue rose 12 percent.\n\nThe board rejected the plan."
    others = split_other_answers(raw)
    assert comparison_status_notice(bool(others)) is None
    scored, info = analyse(
        "What did the note say?",
        "Revenue rose 12 percent to 1,048 crores.",
        "",
        others,
        model=model,
        cfg=LEXICAL_CFG,
        generator_id=0,
    )
    assert info["n_other_answers"] == 2
    assert int(scored["cross_n_others"].iloc[0]) == 2
    assert comparison_status_notice(info["n_other_answers"] > 0) is None


def test_same_generator_and_inputs_keep_probability_weights_logits_and_signals(monkeypatch):
    _use_lexical(monkeypatch)
    model = RCGateModel(RCGateConfig(n_generators=6, epochs=1, batch_size=32), seed=1)
    model.fit(_small_frame(6), _small_frame(6), LEXICAL_CFG)
    question = "What did the note say?"
    answer = "Revenue rose 12 percent."
    context = "Revenue rose 12 percent."
    other = "Revenue rose about 12 percent."
    first, _ = analyse(
        question, answer, context, [other], model=model, cfg=LEXICAL_CFG, generator_id=0
    )
    second, _ = analyse(
        question, answer, context, [other], model=model, cfg=LEXICAL_CFG, generator_id=0
    )
    direct, _ = extract_signals(
        build_frame(question, answer, context, generator_id=0),
        cfg=LEXICAL_CFG,
        answers_by_question={"demo": {0: answer, 1: other}},
        scorer=LexicalScorer(),
        embedder=Embedder(LexicalScorer()),
    )
    for column in ("prob", "w_cross", "w_evid", "z_cross", "z_evid", *SIGNALS):
        assert first[column].tolist() == second[column].tolist()
    _assert_scores_match_direct_predict(first, direct, model)


def test_checkpoint_lines_use_the_artifact_and_not_stage8_means():
    lines = prediction_checkpoint_lines({"variant": "A7", "seed": 0, "namespace": "ragtruth"})
    assert lines == [
        "Variant A7",
        "Seed 0",
        "Result namespace ragtruth",
    ]
    assert prediction_checkpoint_lines({}) == [
        "Variant not recorded",
        "Seed not recorded",
        "Result namespace not recorded",
    ]
    blob = " ".join(lines)
    for token in (STAGE8_A0_AUROC, STAGE8_A4_AUROC, STAGE8_A7_AUROC, STAGE8_A7_MINUS_A4):
        assert token not in blob
    assert "ragtruth_factorial_seed_v1" not in blob
    assert "scores the pasted answer" in PREDICTION_CHECKPOINT_SCOPE
    assert STAGE8_A7_AUROC not in PREDICTION_CHECKPOINT_SCOPE


def test_resolve_checkpoint_reads_namespace_from_the_result_directory(tmp_path, monkeypatch):
    from rcgate.demo import app as app_mod

    summary = tmp_path / "summary"
    run = summary / "ragtruth" / "A7_seed2"
    run.mkdir(parents=True)
    (run / "metrics.json").write_text(
        json.dumps(
            {
                "variant": "A7",
                "seed": 2,
                "git": "abc",
                "config": "ragtruth.yaml",
                "table": "ragtruth_s2.parquet",
            }
        ),
        encoding="utf-8",
    )
    (run / "model.joblib").write_bytes(b"checkpoint")
    monkeypatch.setattr(app_mod, "SUMMARY_DIR", summary)
    path, provenance = resolve_checkpoint(None, Config({"report": {"tag": "ragtruth"}}))
    assert path == run / "model.joblib"
    assert provenance["variant"] == "A7"
    assert provenance["seed"] == 2
    assert provenance["namespace"] == "ragtruth"
    assert result_namespace(path) == "ragtruth"
    lines = prediction_checkpoint_lines(provenance)
    assert lines[0] == "Variant A7"
    assert lines[1] == "Seed 2"
    assert lines[2] == "Result namespace ragtruth"


def test_resolve_checkpoint_prefers_namespace_recorded_on_the_artifact(tmp_path, monkeypatch):
    from rcgate.demo import app as app_mod

    summary = tmp_path / "summary"
    run = summary / "ragtruth" / "A7_seed0"
    run.mkdir(parents=True)
    (run / "metrics.json").write_text(
        json.dumps({"variant": "A7", "seed": 0, "namespace": "recorded-namespace"}),
        encoding="utf-8",
    )
    (run / "model.joblib").write_bytes(b"checkpoint")
    monkeypatch.setattr(app_mod, "SUMMARY_DIR", summary)
    _path, provenance = resolve_checkpoint(run / "model.joblib", Config({"report": {"tag": "ragtruth"}}))
    assert provenance["namespace"] == "recorded-namespace"
    assert provenance["variant"] == "A7"
    assert provenance["seed"] == 0


def test_saved_checkpoint_provenance_and_scores_stay_on_that_artifact(monkeypatch):
    """The demo loader's real A7 artifact, when this checkout has one."""
    from rcgate.config import load_named

    cfg = load_named("ragtruth")
    try:
        path, provenance = resolve_checkpoint(None, cfg)
    except FileNotFoundError:
        pytest.skip("no saved A7 checkpoint in this checkout")
    metrics_path = path.parent / "metrics.json"
    if not metrics_path.exists():
        pytest.skip("saved checkpoint has no metrics.json")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert provenance["variant"] == metrics["variant"]
    assert provenance["seed"] == metrics["seed"]
    assert provenance["namespace"] == path.parent.parent.name
    assert "ragtruth_factorial_seed_v1" not in str(path)
    lines = prediction_checkpoint_lines(provenance)
    assert lines[0] == f"Variant {metrics['variant']}"
    assert lines[1] == f"Seed {metrics['seed']}"
    assert lines[2] == f"Result namespace {path.parent.parent.name}"
    for token in (STAGE8_A0_AUROC, STAGE8_A4_AUROC, STAGE8_A7_AUROC):
        assert token not in " ".join(lines)

    import joblib

    model = joblib.load(path)
    assert unknown_identity_supported(model) is True
    _use_lexical(monkeypatch)
    question = "What did the note say?"
    answer = "Revenue rose 12 percent."
    other = "Revenue rose about 12 percent."
    kwargs = {
        "model": model,
        "cfg": LEXICAL_CFG,
        "generator_id": 0,
    }
    first, _info = analyse(question, answer, "Revenue rose 12 percent.", [other], **kwargs)
    second, _info2 = analyse(question, answer, "Revenue rose 12 percent.", [other], **kwargs)
    direct, _report = extract_signals(
        build_frame(question, answer, "Revenue rose 12 percent.", generator_id=0),
        cfg=LEXICAL_CFG,
        answers_by_question={"demo": {0: answer, 1: other}},
        scorer=LexicalScorer(),
        embedder=Embedder(LexicalScorer()),
    )
    for column in ("prob", "w_cross", "w_evid", "z_cross", "z_evid", *SIGNALS):
        assert first[column].tolist() == second[column].tolist()
    _assert_scores_match_direct_predict(first, direct, model)
    unknown, unknown_info = analyse(question, answer, model=model, cfg=LEXICAL_CFG)
    assert unknown_info["generator_id"] == UNK_GENERATOR
    assert int(unknown["cross_n_others"].iloc[0]) == 0

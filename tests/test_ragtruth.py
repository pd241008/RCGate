"""RAGTruth loader tests (milestone M5).

No network and no model download: the raw JSONL is faked in-memory and the extractors are
given the lexical scorer. What is being pinned here is the *mapping* -- response spans to
sentences to labels -- because that mapping is where a real benchmark silently turns into a
wrong dataset.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from rcgate.claims.dealias import split_sentences
from rcgate.data.ragtruth import (
    DEFAULT_ROSTER,
    HALLUCINATION_LABEL_TYPES,
    Claim,
    SentenceAlignmentError,
    build_slice,
    claims_from_response,
    dealias_labelled_claims,
    interleave_by_task,
    require_sentence_alignment,
    schema_record,
    sentence_spans,
    write_schema_record,
)

# -- sentence splitting --------------------------------------------------------


def test_sentence_spans_offsets_index_the_original_string():
    text = "Revenue rose 5 percent. Costs fell. Margins held at 12 percent."
    spans = sentence_spans(text)
    assert [s[2] for s in spans] == [
        "Revenue rose 5 percent.",
        "Costs fell.",
        "Margins held at 12 percent.",
    ]
    for start, end, sentence in spans:
        assert text[start:end] == sentence


def test_sentence_spans_keep_abbreviations_and_quotes_intact():
    text = 'The firm said profit rose 3%. "That is a record," the chief said. Then it fell.'
    sentences = [s[2] for s in sentence_spans(text)]
    assert sentences[0] == "The firm said profit rose 3%."
    assert sentences[1].endswith('the chief said.')


def test_sentence_spans_on_empty_and_whitespace_text():
    assert sentence_spans("") == []
    assert sentence_spans("   \n  ") == []


# -- span-to-sentence labelling ------------------------------------------------


def _response(text: str, spans: list[tuple[int, int, str]], model: str = "gpt-4-0613") -> dict:
    return {
        "id": "7",
        "source_id": "100",
        "model": model,
        "quality": "good",
        "split": "train",
        "response": text,
        "labels": [
            {"start": s, "end": e, "text": t, "label_type": lt}
            for (s, e, t, lt) in spans
        ],
    }


def test_a_span_overlapping_a_sentence_labels_that_sentence():
    response = _response(
        "Revenue rose 5 percent. Costs fell sharply.",
        [(0, 16, "Revenue rose 5 percent.", "Evident Conflict")],
    )
    claims = claims_from_response(response, generator_id=0)
    assert [c.label for c in claims] == [1, 0]
    assert claims[0].label_types == ["Evident Conflict"]


def test_a_span_smaller_than_the_sentence_still_labels_it():
    """Partial overlap counts: part of a hallucinated sentence is still hallucinated."""
    response = _response(
        "The summit was held in Geneva last June.",
        [(23, 29, "Geneva", "Evident Baseless Info")],
    )
    claims = claims_from_response(response, generator_id=0)
    assert [c.label for c in claims] == [1]


def test_all_four_annotation_types_count_as_hallucination():
    text = "A. B. C. D."
    spans = [
        (0, 2, "A.", label_type) for label_type in HALLUCINATION_LABEL_TYPES
    ]
    claims = claims_from_response(_response(text, spans), generator_id=1)
    assert [c.label for c in claims] == [1, 0, 0, 0]
    assert all(c.model == "gpt-4-0613" and c.generator_id == 1 for c in claims)


def test_an_unrecognised_label_type_is_not_counted():
    response = _response("A. B.", [(0, 2, "A.", "Style Issue")])
    assert [c.label for c in claims_from_response(response, 0)] == [0, 0]


def test_a_response_with_no_annotations_is_all_negative():
    claims = claims_from_response(_response("A. B.", []), 0)
    assert [c.label for c in claims] == [0, 0]
    assert all(c.label_types == [] for c in claims)


def test_claim_ids_are_unique_per_response_sentence():
    claims = claims_from_response(_response("A. B. C.", []), 0)
    keys = {(c.response_id, c.index) for c in claims}
    assert len(keys) == len(claims) == 3


# -- source ordering -----------------------------------------------------------


def test_interleave_by_task_alternates_task_types():
    usable = {"1": {}, "2": {}, "3": {}, "4": {}}
    sources = {"1": {"task_type": "QA"}, "2": {"task_type": "Summary"},
               "3": {"task_type": "QA"}, "4": {"task_type": "Summary"}}
    ordered = interleave_by_task(usable, sources)
    tasks = [sources[s]["task_type"] for s in ordered]
    assert tasks[0] != tasks[1], tasks


# -- the assembled slice -------------------------------------------------------


def _responses_for(source_id: str, task: str) -> list[dict]:
    out = []
    for index, model in enumerate(DEFAULT_ROSTER):
        text = f"Model {index} says the figure was 40 percent. It held in {source_id}."
        labelled = index == 0
        out.append(
            {
                "id": f"{source_id}-{index}",
                "source_id": source_id,
                "model": model,
                "quality": "good",
                "split": "train",
                "response": text,
                "labels": (
                    [{"start": 0, "end": 27, "text": text[:27],
                      "label_type": "Evident Conflict"}]
                    if labelled
                    else []
                ),
            }
        )
    return out


@pytest.fixture
def slice_cfg(tmp_path):
    from rcgate.config import Config

    return Config(
        {
            "data": {
                "roster": DEFAULT_ROSTER,
                "task_types": ["QA"],
                "min_generators": 3,
                "n_claims": 24,
                # One claim per generator per source, so the slice carries all six.
                "claims_per_source": 6,
            }
        }
    )


def _cfg_with(**overrides):
    from rcgate.config import Config

    base = {
        "roster": DEFAULT_ROSTER,
        "task_types": ["QA"],
        "min_generators": 3,
        "n_claims": 24,
        "claims_per_source": 6,
    }
    base.update(overrides)
    return Config({"data": base})


def test_build_slice_produces_a_well_formed_claim_frame(tmp_path, slice_cfg, monkeypatch):
    monkeypatch.setattr(
        "rcgate.data.ragtruth.fetch",
        lambda *a, **k: {
            "response.jsonl": tmp_path / "response.jsonl",
            "source_info.jsonl": tmp_path / "source_info.jsonl",
        },
    )
    rows = []
    for n in range(4):
        rows += _responses_for(f"{100 + n}", "QA")
    sources = [
        {"source_id": f"{100 + n}", "task_type": "QA", "source": "CNN/DM",
         "source_info": "The report said the figure was 40 percent.",
         "prompt": "What was the figure?"}
        for n in range(4)
    ]
    (tmp_path / "source_info.jsonl").write_text(
        "\n".join(json.dumps(s) for s in sources)
    )

    sl = build_slice(slice_cfg, seed=0, claim_texts=rows)

    # The signal columns do not exist yet -- they are the extractor's job, not the
    # loader's -- but everything the extractors read must already be present and sound.
    assert len(sl.frame) == 24
    for column in ("question_id", "claim_id", "claim_text", "benchmark", "context",
                   "claim_type", "generator_id", "label"):
        assert column in sl.frame.columns, column
    assert sl.frame["claim_id"].is_unique
    assert sl.frame["label"].isin([0, 1]).all()
    assert sl.stats["n_sources_usable"] == 4
    assert sl.roster["gpt-4-0613"] == 0
    # Every source carries all six generators, so the cross-model family is never empty.
    assert set(sl.frame["generator_id"]) == set(range(6))
    for answers in sl.answers_by_question.values():
        assert set(answers) == set(range(6))
    assert isinstance(sl.frame, pd.DataFrame)


def test_build_slice_respects_the_claim_cap_and_label_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "rcgate.data.ragtruth.fetch",
        lambda *a, **k: {
            "response.jsonl": tmp_path / "response.jsonl",
            "source_info.jsonl": tmp_path / "source_info.jsonl",
        },
    )
    rows = []
    for n in range(6):
        rows += _responses_for(f"{200 + n}", "QA")
    (tmp_path / "source_info.jsonl").write_text(
        "\n".join(
            json.dumps(
                {"source_id": f"{200 + n}", "task_type": "QA", "source": "CNN/DM",
                 "source_info": "The report said 40 percent.", "prompt": "What was it?"}
            )
            for n in range(6)
        )
    )

    cfg = _cfg_with(n_claims=20)
    sl = build_slice(cfg, seed=0, claim_texts=rows)

    assert len(sl.frame) == cfg.get("data.n_claims")
    assert sl.frame["claim_id"].is_unique
    # Only generator 0's first sentence is annotated, and the round-robin writes generator
    # 0 first, so the positives are exactly the first claim of each source in the slice.
    positives = sl.frame[sl.frame["label"] == 1]
    assert len(positives) == sl.frame["question_id"].nunique() == 4
    assert set(positives["generator_id"]) == {0}
    assert set(positives["claim_id"].str.rsplit("#", n=1).str[1]) == {"0"}
    assert sl.stats["n_sources_written"] == 4
    assert sl.stats["positive_rate"] == pytest.approx(
        len(positives) / len(sl.frame), abs=1e-3
    )


def test_the_per_source_cap_keeps_every_generator_represented(tmp_path, monkeypatch):
    """A cap below the roster size would leave the later generators with no rows at all."""
    monkeypatch.setattr(
        "rcgate.data.ragtruth.fetch",
        lambda *a, **k: {
            "response.jsonl": tmp_path / "response.jsonl",
            "source_info.jsonl": tmp_path / "source_info.jsonl",
        },
    )
    rows = []
    for n in range(3):
        rows += _responses_for(f"{400 + n}", "QA")
    (tmp_path / "source_info.jsonl").write_text(
        "\n".join(
            json.dumps(
                {"source_id": f"{400 + n}", "task_type": "QA", "source": "CNN/DM",
                 "source_info": "The report said 40 percent.", "prompt": "What was it?"}
            )
            for n in range(3)
        )
    )

    sl = build_slice(_cfg_with(n_claims=100), seed=0, claim_texts=rows)

    assert len(sl.frame) == 3 * 6
    assert set(sl.frame["generator_id"]) == set(range(6))
    assert sl.frame.groupby("generator_id").size().eq(3).all()
    # The per-source cap is what keeps three questions from swallowing the whole slice.
    assert sl.stats["n_sources_written"] == 3


def test_build_slice_drops_sources_without_enough_generators(tmp_path, slice_cfg, monkeypatch):
    monkeypatch.setattr(
        "rcgate.data.ragtruth.fetch",
        lambda *a, **k: {
            "response.jsonl": tmp_path / "response.jsonl",
            "source_info.jsonl": tmp_path / "source_info.jsonl",
        },
    )
    rows = _responses_for("300", "QA")[:2]  # only two generators, below min_generators=3
    (tmp_path / "source_info.jsonl").write_text(
        json.dumps({"source_id": "300", "task_type": "QA", "source": "x",
                    "source_info": "text", "prompt": "q"})
    )

    sl = build_slice(slice_cfg, seed=0, claim_texts=rows)
    assert len(sl.frame) == 0
    assert sl.stats["n_sources_usable"] == 0


# -- provenance ----------------------------------------------------------------


def test_schema_record_states_license_hashes_and_mapping():
    record = schema_record()
    assert record["license"] == "MIT"
    assert {f["name"] for f in record["files"]} == {"response.jsonl", "source_info.jsonl"}
    assert all(len(f["sha256"]) == 64 for f in record["files"])
    assert record["label_schema"]["mapping"].startswith("label = 1")
    assert record["generator_roster"] == DEFAULT_ROSTER
    assert "question_id" in record["split_policy"]


def test_write_schema_record_round_trips(tmp_path):
    path = write_schema_record(tmp_path / "benchmarks" / "ragtruth.json", {"n_claims_written": 20})
    written = json.loads(path.read_text())
    assert written["slice"]["n_claims_written"] == 20
    assert written["license"] == "MIT"


# -- sentence alignment: one span, one label, one de-aliased sentence -------


def _labelled(text: str, spans: list[tuple[int, int, str]]) -> list:
    return dealias_labelled_claims(claims_from_response(_response(text, spans), 0), question="")


def test_normal_period_and_whitespace_stays_one_to_one():
    text = "Revenue rose 5 percent. Costs fell."
    paired = _labelled(text, [(0, 24, "Revenue rose 5 percent.", "Evident Conflict")])
    assert [c.text for c, _ in paired] == ["Revenue rose 5 percent.", "Costs fell."]
    assert [d.text for _, d in paired] == ["Revenue rose 5 percent.", "Costs fell."]
    assert [c.label for c, _ in paired] == [1, 0]
    assert len(paired) == len(sentence_spans(text)) == len(split_sentences(text))


def test_period_plus_closing_quote_keeps_the_labelled_boundary():
    text = 'He replied "Done." She agreed.'
    paired = _labelled(text, [])
    assert [c.text for c, _ in paired] == ['He replied "Done."', "She agreed."]
    assert [d.text for _, d in paired] == [c.text for c, _ in paired]
    assert len(split_sentences(text)) == 1
    assert len(paired) == 2


def test_period_plus_closing_parenthesis_keeps_the_labelled_boundary():
    text = "Costs fell (see note.) Margins held."
    paired = _labelled(text, [(0, 22, "Costs fell (see note.)", "Subtle Conflict")])
    assert [c.text for c, _ in paired] == ["Costs fell (see note.)", "Margins held."]
    assert [c.label for c, _ in paired] == [1, 0]
    assert [d.text for _, d in paired] == [c.text for c, _ in paired]
    assert len(split_sentences(text)) == 1


def test_multiple_quoted_sentences_are_not_merged():
    text = '"Alpha rose." "Beta fell." Gamma held.'
    paired = _labelled(text, [])
    assert [c.text for c, _ in paired] == ['"Alpha rose."', '"Beta fell."', "Gamma held."]
    assert [d.text for _, d in paired] == [c.text for c, _ in paired]
    assert len(paired) == 3
    assert len(split_sentences(text)) == 1


def test_multiple_labels_stay_on_their_own_sentences():
    text = 'Alpha said "Go." Beta left. Gamma stayed.'
    first = 'Alpha said "Go."'
    third = "Gamma stayed."
    start_third = text.index(third)
    paired = _labelled(
        text,
        [
            (0, len(first), first, "Evident Conflict"),
            (start_third, start_third + len(third), third, "Subtle Baseless Info"),
        ],
    )
    assert [c.label for c, _ in paired] == [1, 0, 1]
    assert [c.label_types for c, _ in paired] == [
        ["Evident Conflict"],
        [],
        ["Subtle Baseless Info"],
    ]
    assert [d.text for _, d in paired] == [c.text for c, _ in paired]


def test_merged_sentence_failure_case_is_not_emitted():
    """The independent splitter glues the quoted sentence onto the next one."""
    text = 'He replied "Done." She agreed. They left.'
    paired = _labelled(text, [(0, 18, 'He replied "Done."', "Evident Conflict")])
    assert [c.text for c, _ in paired] == ['He replied "Done."', "She agreed.", "They left."]
    assert paired[0][1].text == 'He replied "Done."'
    assert "She agreed" not in paired[0][1].text
    merged = split_sentences(text)[0]
    assert "She agreed" in merged
    assert paired[0][1].text != merged


def test_dropped_tail_failure_case_keeps_the_last_labelled_sentence():
    text = 'He replied "Done." She agreed. They left.'
    last = "They left."
    start = text.index(last)
    paired = _labelled(text, [(start, start + len(last), last, "Evident Baseless Info")])
    assert len(paired) == len(sentence_spans(text)) == 3
    assert len(split_sentences(text)) == 2
    assert paired[-1][0].text == last
    assert paired[-1][0].label == 1
    assert paired[-1][1].text == last


def test_ordering_shift_failure_case_does_not_move_a_label_onto_the_next_sentence():
    text = 'Alpha said "Go." Beta left. Gamma stayed.'
    beta = "Beta left."
    gamma = "Gamma stayed."
    paired = _labelled(
        text,
        [(text.index(beta), text.index(beta) + len(beta), beta, "Evident Conflict")],
    )
    by_text = {claim.text: claim.label for claim, _ in paired}
    assert by_text == {'Alpha said "Go."': 0, beta: 1, gamma: 0}
    # The old zip paired Beta's label with Gamma's sentence and dropped Gamma's claim.
    defective = list(zip(
        [c.text for c, _ in paired],
        split_sentences(text),
        strict=False,
    ))
    assert len(defective) == 2
    assert defective[1] == (beta, gamma)


def test_dealiasing_rewrites_the_sentence_the_label_belongs_to(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "rcgate.data.ragtruth.fetch",
        lambda *a, **k: {
            "response.jsonl": tmp_path / "response.jsonl",
            "source_info.jsonl": tmp_path / "source_info.jsonl",
        },
    )
    text = 'The reply was "Go." It left. Gamma stayed.'
    (tmp_path / "source_info.jsonl").write_text(json.dumps({
        "source_id": "1", "task_type": "QA", "source": "x",
        "source_info": "Alpha left.",
        "prompt": "What did Aurora Systems report?",
    }))
    rows = [{
        "id": "9", "source_id": "1", "model": "gpt-4-0613", "quality": "good",
        "split": "train", "response": text,
        "labels": [{"start": text.index("It left."), "end": text.index("It left.") + len("It left."),
                    "text": "It left.", "label_type": "Evident Conflict"}],
    }]
    sl = build_slice(
        _cfg_with(n_claims=10, claims_per_source=3, min_generators=1, roster=["gpt-4-0613"]),
        seed=0, claim_texts=rows,
    )
    texts = sl.frame.sort_values("claim_id")["claim_text"].tolist()
    labels = sl.frame.sort_values("claim_id")["label"].tolist()
    assert texts == ['The reply was "Go."', "Aurora Systems left.", "Gamma stayed."]
    assert labels == [0, 1, 0]


def test_alignment_mismatch_fails_loudly():
    with pytest.raises(SentenceAlignmentError, match="drop or shift"):
        require_sentence_alignment(["a", "b", "c"], ["a"])


def test_claims_carry_the_generator_and_response_provenance():
    claim = Claim(
        response_id="9", source_id="100", model="llama-2-7b-chat", generator_id=3,
        index=1, start=0, end=5, text="Hello", label=1, label_types=["Subtle Conflict"],
    )
    assert claim.generator_id == 3 and claim.model == "llama-2-7b-chat"
    assert claim.label == 1

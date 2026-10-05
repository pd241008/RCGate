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

from rcgate.data.ragtruth import (
    DEFAULT_ROSTER,
    HALLUCINATION_LABEL_TYPES,
    Claim,
    build_slice,
    claims_from_response,
    interleave_by_task,
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


def test_claims_carry_the_generator_and_response_provenance():
    claim = Claim(
        response_id="9", source_id="100", model="llama-2-7b-chat", generator_id=3,
        index=1, start=0, end=5, text="Hello", label=1, label_types=["Subtle Conflict"],
    )
    assert claim.generator_id == 3 and claim.model == "llama-2-7b-chat"
    assert claim.label == 1

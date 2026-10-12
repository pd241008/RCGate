"""Recorded demo fixtures stay tied to stored RAGTruth rows and one checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from rcgate.data.schema import SIGNALS
from rcgate.demo.fixtures import (
    DEFAULT_CHECKPOINT,
    DEFAULT_OUT,
    DEFAULT_RESPONSES,
    DEFAULT_SOURCES,
    DEFAULT_TABLE,
    MODEL_NAMES,
    PLAYBACK_LABEL,
    RESEARCH,
    build_library,
)
from rcgate.paths import PROJECT_ROOT

REPORT = PROJECT_ROOT / "docs/RC-Gate_Final_Research_Report_v1.md"
REQUIRED_SCENARIO = {
    "id",
    "topic",
    "summary",
    "provenance_label",
    "question",
    "source_id",
    "task_type",
    "dataset_source",
    "scored_claim_id",
    "claim_scope",
    "responses",
    "sources",
    "additional_references",
    "prediction",
}
REQUIRED_PREDICTION = {
    "claim_id",
    "claim_text",
    "sentence_index",
    "claim_type",
    "claim_type_name",
    "generator_id",
    "model_id",
    "model_name",
    "prob",
    "predicted_class",
    "w_cross",
    "w_evid",
    "z_cross",
    "z_evid",
    "signals",
    "generation_method",
}


@pytest.fixture(scope="module")
def library() -> dict:
    if not DEFAULT_OUT.exists():
        pytest.skip("demo fixture library has not been built")
    return json.loads(DEFAULT_OUT.read_text(encoding="utf-8"))


def test_library_matches_a_fresh_build(library: dict):
    fresh = build_library()
    assert fresh == library


def test_schema_and_three_real_scenarios(library: dict):
    assert library["kind"] == "recorded_demo"
    assert library["official_benchmark_result"] is False
    assert library["live_provider_calls"] is False
    assert library["playback_label"] == PLAYBACK_LABEL
    assert len(library["scenarios"]) == 3
    ids = [item["id"] for item in library["scenarios"]]
    assert len(set(ids)) == 3
    for scenario in library["scenarios"]:
        missing = REQUIRED_SCENARIO - set(scenario)
        assert not missing, missing
        assert scenario["question"].strip()
        assert scenario["claim_scope"] == "first_sentence"
        pred = scenario["prediction"]
        assert REQUIRED_PREDICTION <= set(pred)
        assert set(pred["signals"]) == set(SIGNALS)


def test_response_models_are_stored_roster_identities(library: dict):
    recorded = {}
    for row in _jsonl(DEFAULT_RESPONSES):
        recorded[str(row["id"])] = row
    for scenario in library["scenarios"]:
        assert len(scenario["responses"]) == 6
        scored = [card for card in scenario["responses"] if card["scored"]]
        assert len(scored) == 1
        assert scored[0]["claim_id"] == scenario["scored_claim_id"]
        for card in scenario["responses"]:
            raw = recorded[card["response_id"]]
            assert str(raw["source_id"]) == scenario["source_id"]
            assert card["model_id"] == str(raw["model"])
            assert card["model_id"] in MODEL_NAMES
            assert card["model_name"] == MODEL_NAMES[card["model_id"]]
            assert card["text"] == str(raw["response"])
            assert "claude" not in card["model_id"].lower()
            assert card["provenance"].endswith(card["response_id"])


def test_scores_belong_to_the_named_claim(library: dict):
    table = pd.read_parquet(DEFAULT_TABLE)
    seen: dict[str, str] = {}
    for scenario in library["scenarios"]:
        pred = scenario["prediction"]
        assert pred["claim_id"] == scenario["scored_claim_id"]
        assert pred["sentence_index"] == 0
        row = table.loc[table["claim_id"].astype(str) == pred["claim_id"]]
        assert len(row) == 1
        stored = row.iloc[0]
        assert str(stored["question_id"]) == scenario["source_id"]
        assert pred["claim_text"] == str(stored["claim_text"])
        assert pred["generator_id"] == int(stored["generator_id"])
        assert pred["model_id"] == str(stored["source_model"])
        for name in SIGNALS:
            assert pred["signals"][name] == round(float(stored[name]), 4)
        assert seen.get(pred["claim_id"]) is None
        seen[pred["claim_id"]] = scenario["id"]
        other_ids = {card["claim_id"] for card in scenario["responses"] if not card["scored"]}
        assert pred["claim_id"] not in other_ids
    assert len(seen) == 3


def test_source_urls_are_absent_because_the_records_have_none(library: dict):
    raw_sources = {str(row["source_id"]): row for row in _jsonl(DEFAULT_SOURCES)}
    for scenario in library["scenarios"]:
        raw = raw_sources[scenario["source_id"]]
        assert "url" not in raw
        assert scenario["additional_references"] == []
        assert scenario["sources"]
        for source in scenario["sources"]:
            assert source["url"] is None
            assert source["kind"] == "supplied_context"
            assert source["used_in_scoring"] is True
            assert source["excerpt"].strip()
            info = raw["source_info"]
            haystack = info["passages"] if isinstance(info, dict) else str(info)
            assert source["excerpt"] in haystack


def test_playback_copy_does_not_claim_a_live_provider_call(library: dict):
    blob = json.dumps(library).lower()
    assert library["playback_label"] == "Recorded demo · precomputed responses"
    for phrase in (
        "querying gpt",
        "calling claude",
        "contacting wikipedia",
        "currently being queried",
        "live provider",
    ):
        assert phrase not in blob
    assert "claude" not in blob


def test_research_figures_match_the_final_report(library: dict):
    report = REPORT.read_text(encoding="utf-8")
    research = library["research"]
    assert research == RESEARCH
    for key in (
        "a0_mean_auroc",
        "a4_mean_auroc",
        "a7_mean_auroc",
        "mean_a7_minus_a4",
        "mean_a7_minus_a0",
    ):
        assert research[key] in report
    assert research["n_group_splits"] == 20
    assert research["n_model_initialisations"] == 3
    assert research["independent_datasets"] is False
    assert research["evaluates_demo_claim"] is False
    assert "60 independent" not in report or "not 60 independent" in report.lower() or "not 20 datasets" in report


def test_checkpoint_file_was_not_rewritten(library: dict):
    recorded = library["checkpoint"]["sha256"]
    assert recorded == _sha256(DEFAULT_CHECKPOINT)
    assert library["signal_table"]["sha256"] == _sha256(DEFAULT_TABLE)


def _jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()

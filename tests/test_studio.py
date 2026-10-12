"""Offline studio: local RAGTruth inventory, search, and checkpoint scoring."""

from __future__ import annotations

import json
import threading
from io import BytesIO
from pathlib import Path

import pytest

from rcgate.data.ragtruth import DEFAULT_ROSTER, FILES
from rcgate.data.schema import SIGNALS
from rcgate.demo.fixtures import RESEARCH
from rcgate.paths import PROJECT_ROOT
from rcgate.studio.catalog import CHECKPOINT_PATH, TABLE_PATH, Catalog
from rcgate.studio.references import EMPTY_NOTE, load_references
from rcgate.studio.scoring import StudioScorer
from rcgate.studio.server import make_handler

REPORT = PROJECT_ROOT / "docs" / "RC-Gate_Final_Research_Report_v1.md"


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return Catalog.load()


@pytest.fixture(scope="module")
def scorer(catalog: Catalog) -> StudioScorer:
    return StudioScorer(catalog)


def test_inventory_matches_pinned_ragtruth_files(catalog: Catalog):
    inventory = catalog.inventory(checkpoint_ready=True, local_ready=True)
    assert inventory["n_sources"] == 2965
    assert inventory["n_responses"] == 17790
    assert inventory["tasks"] == {"QA": 989, "Summary": 943, "Data2txt": 1033}
    assert sum(item["count"] for item in inventory["topics"]) == 2965
    assert inventory["signal_table"]["n_claims"] == 800
    assert inventory["signal_table"]["n_sources"] == 134
    assert all(item["match"] for item in inventory["files"].values())
    for name, expected in FILES.items():
        assert inventory["files"][name]["sha256"] == expected
    assert {item["id"] for item in inventory["generators"]} == set(DEFAULT_ROSTER)
    partial = {item["source_id"]: item["n_claims"] for item in inventory["signal_table"]["partial_sources"]}
    assert partial == {"11775": 2}


def test_every_source_has_six_roster_answers_and_no_duplicates(catalog: Catalog):
    assert len(catalog.sources) == len(set(catalog.sources))
    for source in catalog.sources.values():
        models = [response.model_id for response in source.responses]
        assert models == list(DEFAULT_ROSTER)
        assert len({response.response_id for response in source.responses}) == 6
        assert source.topic_id


def test_unclassified_records_stay_searchable(catalog: Catalog):
    page = catalog.search(topic="other", page_size=5, local_ready=True)
    assert page["total"] > 0
    bare = catalog.search(q=page["results"][0]["title"][:24], page_size=5, local_ready=True)
    assert bare["total"] >= 1
    assert sum(item["count"] for item in catalog.inventory(checkpoint_ready=True, local_ready=True)["topics"]) == 2965


def test_search_filters_sort_and_pagination(catalog: Catalog):
    flight = catalog.search(q="how long would it take to fly 370 miles", local_ready=True)
    assert flight["total"] == 1
    assert flight["results"][0]["source_id"] == "12226"
    qa = catalog.search(task="QA", page_size=1, local_ready=True)
    assert qa["total"] == 989
    llama = catalog.search(generator="llama-2-70b-chat", page_size=1, sort="source", local_ready=True)
    assert llama["results"][0]["excerpt_model_name"] == "Llama-2-70B-chat"
    ordered = catalog.search(sort="source", page_size=3, local_ready=True)
    ids = [int(row["source_id"]) for row in ordered["results"]]
    assert ids == sorted(ids)

    seen: set[str] = set()
    page = 1
    while True:
        batch = catalog.search(page=page, page_size=50, sort="source", local_ready=True)
        found = [row["source_id"] for row in batch["results"]]
        assert not (seen & set(found))
        seen.update(found)
        if page >= batch["n_pages"]:
            break
        page += 1
    assert seen == set(catalog.sources)


def test_record_keeps_task_answers_context_and_references_apart(catalog: Catalog):
    qa = catalog.record("12226", checkpoint_ready=True, local_ready=True)
    assert qa is not None
    assert qa["task"]["question"] == "how long would it take to fly 370 miles while flying at 100 mph"
    assert qa["task"]["kind"] == "qa"
    assert qa["passages"]
    assert all(item["kind"] == "supplied_context" and item["evidence_input"] is True for item in qa["passages"])
    assert qa["independent_references"] == []
    assert qa["independent_reference_note"] == EMPTY_NOTE
    assert [item["model_id"] for item in qa["responses"]] == list(DEFAULT_ROSTER)
    assert len({item["response_id"] for item in qa["responses"]}) == 6

    summary = next(source for source in catalog.sources.values() if source.task_type == "Summary")
    summary_record = catalog.record(summary.source_id, checkpoint_ready=True, local_ready=True)
    assert summary_record is not None
    assert summary_record["task"]["question"] is None
    assert summary_record["task"]["kind"] == "summary"

    referenced = catalog.record("12180", checkpoint_ready=True, local_ready=True)
    assert referenced is not None
    assert referenced["independent_references"][0]["used_in_rcgate_score"] is False
    assert referenced["independent_references"][0]["url"].startswith("https://")
    passage_text = "\n".join(item["text"] for item in referenced["passages"])
    assert referenced["independent_references"][0]["url"] not in passage_text


def test_reference_manifest_never_claims_to_score():
    rows = load_references()
    assert rows
    seen = set()
    for row in rows:
        assert row["used_in_rcgate_score"] is False
        assert row["url"].startswith("https://")
        assert row["title"] and row["publisher"] and row["excerpt"] and row["verified_on"]
        assert row["id"] not in seen
        seen.add(row["id"])


def test_precomputed_rows_match_the_dealiased_sentences(catalog: Catalog):
    assert catalog.alignment_problems() == []
    assert set(catalog.partitions) == {
        row["question_id"] for row in catalog.precomputed_rows.values()
    }
    assert set(catalog.partitions.values()) == {"train", "val", "test"}


def test_precomputed_score_uses_the_checkpoint_row(scorer: StudioScorer):
    before = _mtimes()
    result = scorer.score("12226", "16406", 0)
    assert _mtimes() == before
    assert result["status"] == "complete"
    assert result["feature_source"] == "precomputed_row"
    assert result["benchmark_evaluation"] is False
    assert result["partition"] == "train"
    assert "not an independent test result" in result["partition_note"]
    assert "not a benchmark score" in result["partition_note"]
    row = scorer.catalog.precomputed_rows["16406#0"]
    assert result["claim"]["claim_text"] == row["claim_text"]
    assert result["claim"]["claim_id"] == "16406#0"
    assert result["prediction"]["signals"] == row["signals"]
    assert set(result["prediction"]["signals"]) == set(SIGNALS)
    assert result["worked"]["matches_model"] is True
    assert result["checkpoint"]["path"].endswith("A7_split0_model0/model.joblib")
    assert result["checkpoint"]["sha256"]
    assert "0.6280" in REPORT.read_text(encoding="utf-8")
    assert RESEARCH["a7_mean_auroc"] == "0.5717"


def test_score_does_not_train_or_open_urls(monkeypatch, catalog: Catalog):
    def boom(*_args, **_kwargs):
        raise AssertionError("training was called")

    monkeypatch.setattr("rcgate.models.rcgate.RCGateModel.fit", boom)
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network")),
    )
    result = StudioScorer(catalog).score("12226", "16406", 0)
    assert result["status"] == "complete"
    assert result["prediction"]["prob"] > 0


def test_missing_weights_do_not_invent_features(monkeypatch, catalog: Catalog):
    monkeypatch.setattr("rcgate.studio.scoring.local_weights_present", lambda: False)
    calls = {"n": 0}

    def extracted(*_args, **_kwargs):
        calls["n"] += 1
        raise AssertionError("extractor ran")

    monkeypatch.setattr("rcgate.signals.extract.extract_signals", extracted)
    source = next(item for item in catalog.sources.values() if not item.precomputed_claim_ids)
    result = StudioScorer(catalog).score(source.source_id, source.responses[0].response_id, 0)
    assert result["status"] == "unavailable"
    assert result["prediction"] is None
    assert result["feature_source"] is None
    assert calls["n"] == 0


def test_local_extraction_uses_the_canonical_pipeline(catalog: Catalog, tmp_path: Path):
    source = catalog.sources["12229"]
    result = StudioScorer(catalog, cache_dir=tmp_path).score(
        source.source_id, source.responses[0].response_id, 0
    )
    assert result["status"] == "complete"
    assert result["feature_source"] == "local_extraction"
    assert result["benchmark_evaluation"] is False
    assert result["prediction"]["evidence_source"] == "context"
    assert result["prediction"]["arithmetic_verdict"] == "unverifiable"
    assert result["worked"]["matches_model"] is True
    assert "results" not in Path(result["cache_path"]).parts
    cached = StudioScorer(catalog, cache_dir=tmp_path).score(
        source.source_id, source.responses[0].response_id, 0
    )
    assert cached["feature_source"] == "cached_local_extraction"


def test_http_library_and_health(catalog: Catalog):
    state = {
        "catalog": catalog,
        "scorer": StudioScorer(catalog),
        "jobs": {},
        "jobs_lock": threading.Lock(),
    }
    handler = make_handler(state)
    status, health = _http(handler, "GET", "/api/health")
    assert status == 200
    assert health["ok"] is True
    assert health["live_provider_calls"] is False
    assert health["inventory"]["n_sources"] == 2965
    status, library = _http(handler, "GET", "/api/library?q=nash+equilibrium&page_size=5")
    assert status == 200
    assert library["results"][0]["source_id"] == "12180"
    status, missing = _http(handler, "GET", "/api/library/not-a-source")
    assert status == 404
    assert "unknown source" in missing["error"]


def test_stage8_figures_are_the_report_figures():
    text = REPORT.read_text(encoding="utf-8")
    for value in ("0.6280", "0.6839", "0.5717", "−0.1122", "−0.0563"):
        assert value in text
        assert RESEARCH[
            {
                "0.6280": "a0_mean_auroc",
                "0.6839": "a4_mean_auroc",
                "0.5717": "a7_mean_auroc",
                "−0.1122": "mean_a7_minus_a4",
                "−0.0563": "mean_a7_minus_a0",
            }[value]
        ] == value


def _http(handler_cls, method: str, path: str, body: bytes = b"") -> tuple[int, dict]:
    raw = (
        f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: {len(body)}\r\n\r\n"
    ).encode() + body

    class Sock:
        def __init__(self) -> None:
            self.reader = BytesIO(raw)
            self.writer = BytesIO()

        def makefile(self, mode: str = "r", *args, **kwargs):
            return self.reader if "r" in mode else self.writer

        def sendall(self, data: bytes) -> None:
            self.writer.write(data)

    sock = Sock()
    handler_cls(sock, ("127.0.0.1", 0), None)
    head, _, payload = sock.writer.getvalue().partition(b"\r\n\r\n")
    status = int(head.split()[1])
    return status, json.loads(payload.decode("utf-8"))


def _mtimes() -> dict[str, int]:
    paths = [CHECKPOINT_PATH, TABLE_PATH, REPORT]
    return {str(path): path.stat().st_mtime_ns for path in paths}

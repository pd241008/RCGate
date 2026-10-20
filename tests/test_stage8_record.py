"""Agreement checks for the recorded Stage 8 grid.

The 480-fit experiment is not run here. Tracked summary files are required.
Local tables, checkpoints, and raw JSONL are checked when they are on disk
and skipped, with the missing path named, when they are not.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rcgate.data.ragtruth import FILES
from rcgate.factorial_seed import assignment_hash
from rcgate.stats_protocol import format_point

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "results/summary/ragtruth_factorial_seed_v1"
METRICS_CSV = STAGE / "seed_metrics.csv"
PAIRED_CSV = STAGE / "paired_deltas.csv"
REPORT_JSON = STAGE / "report.json"
REPORT_MD = STAGE / "report.md"
PROVENANCE = STAGE / "provenance.json"
TABLE = ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"
ASSIGNMENTS = STAGE / "split_assignments.parquet"
PREDICTIONS = STAGE / "predictions.parquet"
RAW = ROOT / "data/raw/ragtruth"
CELL_METRICS = ("auroc", "f1", "precision", "recall", "ece", "threshold")
HEADLINE_AUROC = {"A0": "0.6280", "A4": "0.6839", "A7": "0.5717"}

_REQUIRED = (METRICS_CSV, PAIRED_CSV, REPORT_JSON, REPORT_MD, PROVENANCE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load():
    missing = [str(path.relative_to(ROOT)) for path in _REQUIRED if not path.is_file()]
    if missing:
        pytest.fail("tracked Stage 8 summary files are missing: " + ", ".join(missing))
    metrics = pd.read_csv(METRICS_CSV)
    paired = pd.read_csv(PAIRED_CSV)
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    return metrics, paired, report, provenance, REPORT_MD.read_text(encoding="utf-8")


def _distribution(markdown: str) -> dict[tuple[str, str], dict[str, str]]:
    start = markdown.index("## Distributions over the 60 cells")
    end = markdown.index("## Split-level means", start)
    rows = {}
    for line in markdown[start:end].splitlines():
        if not line.startswith("| A"):
            continue
        cells = [part.strip() for part in line.strip("|").split("|")]
        variant, metric, mean, _median, sd = cells[:5]
        rows[(variant, metric)] = {"mean": mean, "sd": sd, "min": cells[5], "max": cells[6]}
    return rows


def _cell_summary(metrics: pd.DataFrame, variant: str, column: str) -> tuple[float, float, float, float]:
    values = metrics.loc[metrics["variant"] == variant, column].to_numpy(dtype="float64")
    return (
        float(values.mean()),
        float(np.std(values, ddof=1)),
        float(values.min()),
        float(values.max()),
    )


def _variants(report: dict) -> dict[str, dict]:
    return {block["variant"]: block for block in report["scored"]["variants"]}


def test_stage8_summaries_agree_across_csv_json_and_markdown():
    metrics, paired, report, _provenance, markdown = _load()
    assert len(metrics) == 480
    assert set(metrics["variant"]) == {f"A{i}" for i in range(8)}
    assert set(metrics["split_seed"]) == set(range(20))
    assert set(metrics["model_seed"]) == {0, 1, 2}
    assert int(metrics["n_positive"].nunique()) == 1
    assert int(metrics["n_positive"].iloc[0]) == 15
    assert int(metrics["n_questions"].nunique()) == 1
    assert int(metrics["n_questions"].iloc[0]) == 28
    assert bool(metrics["scores_equal_in_memory"].all())

    published = _distribution(markdown)
    blocks = _variants(report)
    for variant in (f"A{i}" for i in range(8)):
        for column in CELL_METRICS:
            mean, sd, low, high = _cell_summary(metrics, variant, column)
            over_cells = blocks[variant][column]["over_cells"]
            assert over_cells["n"] == 60
            assert over_cells["is_confidence_interval"] is False
            assert over_cells["mean"] == pytest.approx(mean, abs=1e-9)
            assert over_cells["sd"] == pytest.approx(sd, abs=1e-9)
            row = published[(variant, column)]
            assert row["mean"] == format_point(mean)
            assert row["sd"] == format_point(sd)
            assert row["min"] == format_point(low)
            assert row["max"] == format_point(high)

    for variant, expected in HEADLINE_AUROC.items():
        mean, sd, low, high = _cell_summary(metrics, variant, "auroc")
        assert format_point(mean) == expected
        assert published[(variant, "auroc")]["mean"] == expected
    _, a7_sd, a7_min, a7_max = _cell_summary(metrics, "A7", "auroc")
    assert format_point(a7_sd) == "0.1247"
    assert format_point(a7_min) == "0.3072"
    assert format_point(a7_max) == "0.7983"
    assert "A7 test AUROC across the 60 cells had mean 0.5717 and sample SD 0.1247" in markdown

    for baseline, expected in (("A0", "-0.0563"), ("A4", "-0.1122")):
        values = paired.loc[paired["baseline"] == baseline, "delta_auroc"].to_numpy(dtype="float64")
        assert len(values) == 60
        recorded = report["scored"]["paired"][baseline]["delta_auroc"]["over_split_means"]["mean"]
        assert recorded == pytest.approx(float(values.mean()), abs=1e-9)
        assert format_point(float(values.mean())) == expected
        above = int((paired.loc[paired["baseline"] == baseline, "position_vs_0"] == "entirely_above_0").sum())
        assert report["scored"]["paired"][baseline]["n_interval_entirely_above_0"] == above
    assert "mean -0.0563" in markdown
    assert "mean -0.1122" in markdown
    assert "3 of 60 cells versus A0 and 2 of 60 versus A4" in markdown

    for variant in ("A0", "A4"):
        spread = metrics.loc[metrics["variant"] == variant].groupby("split_seed")["auroc"].agg(lambda s: s.max() - s.min())
        assert float(spread.max()) == 0.0


def test_stage8_provenance_matches_committed_hashed_sources():
    _metrics, _paired, report, provenance, _markdown = _load()
    assert provenance["git"]["head"] == "47090018414f657bca8e5a43e97663feba2e5a7d"
    assert provenance["git"]["dirty"] is True
    assert provenance["head_alone_reproduces_this_experiment"] is False
    assert provenance["command"] == "python -m rcgate.factorial_seed"
    assert provenance["numpy"] == "2.5.3"
    assert provenance["n_fits"] == 480
    assert provenance["fit_table_sha256"] == report["fit_table_sha256"]
    assert provenance["config_sha256"] == _sha256(ROOT / "configs/ragtruth_factorial_seed_v1.yaml")
    assert report["source_hashes"] == provenance["source_hashes"]
    for rel, expected in provenance["source_hashes"].items():
        path = ROOT / rel
        assert path.is_file(), rel
        assert _sha256(path) == expected
    for row in report["splits"]:
        assert row["n_test_positive"] == 15
        assert row["n_test_groups"] == 28
        assert row["assignment_sha256"] == provenance["split_assignment_sha256"][str(row["split_seed"])]


def test_stage8_signal_table_and_recomputed_splits_match_provenance():
    if not TABLE.is_file():
        pytest.skip("missing data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet")
    _metrics, _paired, _report, provenance, _markdown = _load()
    assert _sha256(TABLE) == provenance["fit_table_sha256"]
    frame = pd.read_parquet(TABLE)
    assert len(frame) == 800
    assert frame["question_id"].nunique() == 134
    assert int(frame["label"].sum()) == 57
    suffixes = frame["claim_id"].astype(str).str.rsplit("#", n=1).str[-1]
    assert set(suffixes) == {"0"}
    assert frame["task_type"].value_counts().to_dict() == {"QA": 402, "Summary": 398}
    assert np.allclose(frame["src_quality"].to_numpy(dtype="float64"), 0.9)
    assert set(frame["arithmetic_verdict"].astype(str)) == {"unverifiable"}

    from rcgate.data.splits import assert_disjoint, group_stratified_split

    for seed in range(20):
        split = group_stratified_split(frame, seed=seed)
        assert_disjoint(split)
        assert assignment_hash(split) == provenance["split_assignment_sha256"][str(seed)]
        assert split.test["question_id"].nunique() == 28
        assert int(split.test["label"].sum()) == 15


def test_stage8_split_assignment_file_is_separated_by_question():
    if not ASSIGNMENTS.is_file():
        pytest.skip("missing results/summary/ragtruth_factorial_seed_v1/split_assignments.parquet")
    _metrics, _paired, _report, provenance, _markdown = _load()
    assigned = pd.read_parquet(ASSIGNMENTS)
    assert list(assigned.columns) == ["split_seed", "question_id", "partition"]
    assert len(assigned) == 20 * 134
    assert set(assigned["partition"]) == {"train", "val", "test"}
    for seed, group in assigned.groupby("split_seed"):
        questions = group["question_id"].astype(str)
        assert questions.nunique() == len(group) == 134
        counts = group["partition"].value_counts().to_dict()
        assert counts == {"train": 80, "val": 26, "test": 28}
        pairs = sorted(
            (str(question_id), str(partition))
            for question_id, partition in zip(
                group["question_id"].tolist(),
                group["partition"].tolist(),
                strict=True,
            )
        )
        lines = [f"{question_id}\t{partition}" for question_id, partition in pairs]
        digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()
        assert digest == provenance["split_assignment_sha256"][str(int(seed))]


def test_stage8_checkpoint_hashes_match_seed_metrics():
    metrics, _paired, _report, _provenance, _markdown = _load()
    expected = []
    for row in metrics.itertuples(index=False):
        cell = STAGE / f"{row.variant}_split{int(row.split_seed)}_model{int(row.model_seed)}"
        expected.append((cell, row.checkpoint_sha256))
    present = [cell for cell, _digest in expected if (cell / "model.joblib").is_file()]
    if not present:
        pytest.skip(
            "Stage 8 cell checkpoints are not on disk. "
            "Expected 480 model.joblib files under results/summary/ragtruth_factorial_seed_v1/."
        )
    missing = []
    for cell, digest in expected:
        for name in ("model.joblib", "metrics.json", "predictions.parquet", "config.yaml"):
            if not (cell / name).is_file():
                missing.append(f"{cell.relative_to(ROOT)}/{name}")
        if (cell / "model.joblib").is_file() and _sha256(cell / "model.joblib") != digest:
            missing.append(f"{cell.relative_to(ROOT)}/model.joblib sha256 != seed_metrics.csv")
    assert not missing, "incomplete Stage 8 cell archive:\n" + "\n".join(missing[:12])


def test_stage8_prediction_rows_follow_the_recorded_partitions():
    if not PREDICTIONS.is_file() or not ASSIGNMENTS.is_file():
        missing = [
            str(path.relative_to(ROOT))
            for path in (PREDICTIONS, ASSIGNMENTS)
            if not path.is_file()
        ]
        pytest.skip("missing " + ", ".join(missing))
    metrics, _paired, _report, _provenance, _markdown = _load()
    predicted = pd.read_parquet(PREDICTIONS)
    assigned = pd.read_parquet(ASSIGNMENTS)
    assert set(predicted["partition"]) <= {"val", "test"}
    counted = (
        predicted.loc[predicted["partition"] == "test"]
        .groupby(["variant", "split_seed", "model_seed"])
        .size()
        .rename("n_pred")
        .reset_index()
    )
    merged = metrics.merge(counted, on=["variant", "split_seed", "model_seed"], how="left")
    assert int(merged["n_pred"].isna().sum()) == 0
    assert int((merged["n"] != merged["n_pred"]).sum()) == 0
    membership = predicted[["split_seed", "question_id", "partition"]].drop_duplicates()
    crossed = membership.groupby(["split_seed", "question_id"])["partition"].nunique()
    assert int(crossed.max()) == 1
    train = assigned.loc[assigned["partition"] == "train", ["split_seed", "question_id"]]
    leaked = predicted.merge(train, on=["split_seed", "question_id"])
    assert leaked.empty
    comparable = predicted.merge(
        assigned,
        on=["split_seed", "question_id"],
        suffixes=("_predicted", "_assigned"),
    )
    assert (comparable["partition_predicted"] == comparable["partition_assigned"]).all()


def test_pinned_ragtruth_jsonl_counts_when_present():
    response = RAW / "response.jsonl"
    sources = RAW / "source_info.jsonl"
    if not response.is_file() or not sources.is_file():
        missing = [str(path.relative_to(ROOT)) for path in (response, sources) if not path.is_file()]
        pytest.skip("missing " + ", ".join(missing))
    assert _sha256(response) == FILES["response.jsonl"]
    assert _sha256(sources) == FILES["source_info.jsonl"]

    def rows(path: Path) -> list[dict]:
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    source_rows = rows(sources)
    response_rows = rows(response)
    assert len(source_rows) == 2965
    assert len(response_rows) == 17790
    tasks = pd.Series([row["task_type"] for row in source_rows]).value_counts().to_dict()
    assert tasks == {"QA": 989, "Summary": 943, "Data2txt": 1033}
    models = pd.Series([row["model"] for row in response_rows]).value_counts().to_dict()
    assert models == {
        "gpt-4-0613": 2965,
        "gpt-3.5-turbo-0613": 2965,
        "mistral-7B-instruct": 2965,
        "llama-2-7b-chat": 2965,
        "llama-2-13b-chat": 2965,
        "llama-2-70b-chat": 2965,
    }
    splits = pd.Series([row["split"] for row in response_rows]).value_counts().to_dict()
    assert splits == {"train": 15090, "test": 2700}

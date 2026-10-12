"""Recorded demo fixtures for the verification studio.

This module reads stored RAGTruth rows and one saved A7 checkpoint, then writes a
self-contained library under ``demo_fixtures/``. It does not train, and it does not
write into ``results/``. The probabilities are demo inferences on stored signal rows.
They are not Stage 8 benchmark scores.

Run::

    python -m rcgate.demo.fixtures
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from ..data.ragtruth import DEFAULT_ROSTER, load_jsonl
from ..data.schema import CLAIM_TYPE_NAMES, SIGNALS
from ..explain import one_line
from ..paths import PROJECT_ROOT

DEFAULT_TABLE = PROJECT_ROOT / "data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet"
DEFAULT_CHECKPOINT = (
    PROJECT_ROOT
    / "results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib"
)
DEFAULT_RESPONSES = PROJECT_ROOT / "data/raw/ragtruth/response.jsonl"
DEFAULT_SOURCES = PROJECT_ROOT / "data/raw/ragtruth/source_info.jsonl"
DEFAULT_OUT = PROJECT_ROOT / "demo_fixtures" / "scenarios.json"

PLAYBACK_LABEL = "Recorded demo · precomputed responses"

#: Display names for roster ids that are actually stored. No other providers.
MODEL_NAMES = {
    "gpt-4-0613": "GPT-4-0613",
    "gpt-3.5-turbo-0613": "GPT-3.5-turbo-0613",
    "mistral-7B-instruct": "Mistral-7B-Instruct",
    "llama-2-7b-chat": "Llama-2-7B-chat",
    "llama-2-13b-chat": "Llama-2-13B-chat",
    "llama-2-70b-chat": "Llama-2-70B-chat",
}

# Stage 8 Table 7 and Table 8 of the final research report. Strings keep the printed
# decimals. These figures describe the repeated-fit grid, not a demo claim.
RESEARCH = {
    "a0_mean_auroc": "0.6280",
    "a4_mean_auroc": "0.6839",
    "a7_mean_auroc": "0.5717",
    "mean_a7_minus_a4": "−0.1122",
    "mean_a7_minus_a0": "−0.0563",
    "slice": "one corrected 800-sentence RAGTruth slice",
    "n_sentences": 800,
    "n_questions": 134,
    "n_group_splits": 20,
    "n_model_initialisations": 3,
    "independent_datasets": False,
    "evaluates_demo_claim": False,
    "report_path": "docs/RC-Gate_Final_Research_Report_v1.md",
    "index_path": "docs/RC-Gate_Experiment_Index.md",
}

# Real source ids and first-sentence claim ids from the corrected seed-0 table.
SCENARIO_SPECS: tuple[dict, ...] = (
    {
        "id": "flight-time",
        "topic": "Numbers & calculations",
        "summary": (
            "A stored question asks how long a 370-mile flight takes at 100 mph. "
            "The six recorded answers do not state the same duration."
        ),
        "source_id": "12226",
        "scored_claim_id": "16406#0",
    },
    {
        "id": "civil-war-court",
        "topic": "History & facts",
        "summary": (
            "A stored question asks about the Supreme Court during the Civil War. "
            "The supplied passages mention the appeal process and the Dred Scott decision."
        ),
        "source_id": "12172",
        "scored_claim_id": "16091#0",
    },
    {
        "id": "nash-equilibrium",
        "topic": "Logic & reasoning",
        "summary": (
            "A stored question asks how a Nash equilibrium differs from a maximin solution. "
            "The recorded answers define the two ideas in different words."
        ),
        "source_id": "12180",
        "scored_claim_id": "16135#0",
    },
)

_PASSAGE_MARK = re.compile(r"passage\s+(\d+)\s*:", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _r4(value: float) -> float:
    return round(float(value), 4)


def _vector(tensor) -> list[float]:
    flat = tensor.detach().cpu().flatten().tolist()
    return [round(float(item), 6) for item in flat]


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _question_text(source: dict) -> str:
    info = source.get("source_info")
    if isinstance(info, dict) and str(info.get("question", "")).strip():
        return str(info["question"]).strip()
    prompt = str(source.get("prompt", "")).strip()
    lowered = prompt.lower()
    if "question:" in lowered:
        rest = prompt[lowered.index("question:") + len("question:") :]
        cut = re.split(r"bear in mind|passage\s*1\s*:", rest, maxsplit=1, flags=re.IGNORECASE)[0]
        return cut.strip()
    return ""


def _passages(source: dict) -> list[dict]:
    """Context passages actually stored on the source. URLs are copied only if present."""
    info = source.get("source_info")
    stored_url = source.get("url") if isinstance(source.get("url"), str) else None
    if isinstance(info, dict):
        raw = str(info.get("passages") or "")
        marks = list(_PASSAGE_MARK.finditer(raw))
        passages: list[dict] = []
        if not marks and raw.strip():
            passages.append(_passage_record(1, raw.strip(), stored_url))
        for index, mark in enumerate(marks):
            end = marks[index + 1].start() if index + 1 < len(marks) else len(raw)
            text = raw[mark.end() : end].strip()
            if text:
                passages.append(_passage_record(int(mark.group(1)), text, None))
        return passages
    text = str(info or "").strip()
    if not text:
        return []
    return [_passage_record(1, text, stored_url)]


def _passage_record(number: int, text: str, url: str | None) -> dict:
    return {
        "id": f"passage-{number}",
        "title": f"Supplied context passage {number}",
        "collection": None,
        "excerpt": text,
        "url": url if url else None,
        "used_in_scoring": True,
        "kind": "supplied_context",
    }


def _class_label(prob: float) -> str:
    if prob >= 0.5:
        return "Likely hallucinated"
    return "Likely supported"


def _expert_record(model) -> dict:
    cross = _vector(model.model.cross_expert.weight)
    evid = _vector(model.model.evid_expert.weight)
    fusion = _vector(model.model.fusion.weight)
    return {
        "fusion_input": str(model.config.fusion_input),
        "standardize_signals": bool(model.config.standardize_signals),
        "cross": {
            "signals": ["agree", "contra", "sem_dist"],
            "weights": cross,
            "bias": round(float(model.model.cross_expert.bias), 6),
        },
        "evidence": {
            "signals": ["support", "src_quality", "conflict"],
            "weights": evid,
            "bias": round(float(model.model.evid_expert.bias), 6),
        },
        "fusion": {
            "weights": fusion,
            "bias": round(float(model.model.fusion.linear.bias.detach()), 6),
        },
        "formula": (
            "z_cross = W_cross · [agree, contra, sem_dist] + b_cross; "
            "z_evid = W_evid · [support, src_quality, conflict] + b_evid; "
            "logit = W_fusion · [w_cross * z_cross, w_evid * z_evid] + b_fusion; "
            "probability = sigmoid(logit). "
            "Routing weights come from softmax of a gate that sees only claim type "
            "and generator identity."
        ),
    }


def _load_model(checkpoint: Path):
    import joblib

    model = joblib.load(checkpoint)
    if not hasattr(model, "predict"):
        raise TypeError(f"{checkpoint} is not an RC-Gate checkpoint")
    return model


def _index_responses(path: Path, source_ids: set[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for row in load_jsonl(path):
        if str(row.get("source_id")) in source_ids:
            found[str(row.get("id"))] = row
    return found


def _index_sources(path: Path, source_ids: set[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for row in load_jsonl(path):
        sid = str(row.get("source_id"))
        if sid in source_ids:
            found[sid] = row
    return found


def build_library(
    *,
    table_path: Path = DEFAULT_TABLE,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
    responses_path: Path = DEFAULT_RESPONSES,
    sources_path: Path = DEFAULT_SOURCES,
) -> dict:
    """Assemble the demo library from local artifacts. Does not write."""
    table = pd.read_parquet(table_path)
    model = _load_model(checkpoint_path)
    source_ids = {spec["source_id"] for spec in SCENARIO_SPECS}
    responses = _index_responses(responses_path, source_ids)
    sources = _index_sources(sources_path, source_ids)
    metrics_path = checkpoint_path.parent / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

    scenarios = [
        _scenario(spec, table, model, responses, sources) for spec in SCENARIO_SPECS
    ]
    return {
        "library_id": "rcgate-demo-fixtures-v1",
        "kind": "recorded_demo",
        "official_benchmark_result": False,
        "live_provider_calls": False,
        "playback_label": PLAYBACK_LABEL,
        "generation_method": (
            "RCGateModel.predict on stored rows of the corrected seed-0 signal table. "
            "The checkpoint was loaded. Nothing was trained or tuned."
        ),
        "checkpoint": {
            "path": _relative(checkpoint_path),
            "sha256": sha256_file(checkpoint_path),
            "variant": "A7",
            "split_seed": metrics.get("split_seed"),
            "model_seed": metrics.get("model_seed"),
            "namespace": "ragtruth_factorial_seed_v1",
            "note": (
                "One saved checkpoint from the Stage 8 directory "
                "(split seed 0, model seed 0). Demo probabilities from this file "
                "are not that run's test AUROC and not the Stage 8 mean."
            ),
        },
        "signal_table": {
            "path": _relative(table_path),
            "sha256": sha256_file(table_path),
            "claim_scope": "first_sentence",
            "note": (
                "Corrected seed-0 table. Each stored claim is sentence index 0. "
                "A probability applies only to that sentence."
            ),
        },
        "sources_file": _relative(sources_path),
        "responses_file": _relative(responses_path),
        "roster": list(DEFAULT_ROSTER),
        "experts": _expert_record(model),
        "research": dict(RESEARCH),
        "scenarios": scenarios,
    }


def _scenario(spec: dict, table: pd.DataFrame, model, responses: dict, sources: dict) -> dict:
    source_id = spec["source_id"]
    source = sources.get(source_id)
    if source is None:
        raise KeyError(f"source {source_id} is not in source_info.jsonl")
    question = _question_text(source)
    if not question:
        raise ValueError(f"source {source_id} has no stored question")

    rows = table[table["question_id"].astype(str) == source_id].sort_values("generator_id")
    if rows.empty:
        raise KeyError(f"source {source_id} is not in the signal table")
    scored = rows[rows["claim_id"].astype(str) == spec["scored_claim_id"]]
    if len(scored) != 1:
        raise KeyError(f"claim {spec['scored_claim_id']} not found for source {source_id}")
    scored_row = scored.iloc[0]

    response_cards = []
    for _, row in rows.iterrows():
        response_id = str(row["claim_id"]).split("#", 1)[0]
        recorded = responses.get(response_id)
        if recorded is None:
            raise KeyError(f"response {response_id} is not in response.jsonl")
        model_id = str(recorded.get("model", ""))
        if model_id != str(row["source_model"]):
            raise ValueError(
                f"response {response_id} model {model_id} does not match {row['source_model']}"
            )
        if model_id not in MODEL_NAMES:
            raise ValueError(f"response {response_id} model {model_id} is not in the roster")
        sentence_index = int(str(row["claim_id"]).split("#", 1)[1])
        response_cards.append(
            {
                "generator_id": int(row["generator_id"]),
                "model_id": model_id,
                "model_name": MODEL_NAMES[model_id],
                "response_id": response_id,
                "claim_id": str(row["claim_id"]),
                "text": str(recorded.get("response", "")),
                "opening_sentence": str(row["claim_text"]),
                "sentence_index": sentence_index,
                "n_sentences_in_answer": int(row["n_claims_in_answer"]),
                "provenance": f"RAGTruth response.jsonl id {response_id}",
                "scored": str(row["claim_id"]) == spec["scored_claim_id"],
            }
        )

    prediction = _prediction(scored_row, model)
    passages = _passages(source)
    for passage in passages:
        passage["collection"] = str(source.get("source") or "") or None
    return {
        "id": spec["id"],
        "topic": spec["topic"],
        "summary": spec["summary"],
        "provenance_label": (
            f"RAGTruth {source.get('task_type')} · source {source.get('source')} "
            f"· source id {source_id} · recorded responses"
        ),
        "question": question,
        "source_id": source_id,
        "task_type": str(source.get("task_type") or ""),
        "dataset_source": str(source.get("source") or ""),
        "scored_claim_id": spec["scored_claim_id"],
        "claim_scope": "first_sentence",
        "responses": response_cards,
        "sources": passages,
        "additional_references": [],
        "prediction": prediction,
    }


def _prediction(row: pd.Series, model) -> dict:
    frame = pd.DataFrame(
        [
            {
                "claim_type": int(row["claim_type"]),
                "generator_id": int(row["generator_id"]),
                **{name: float(row[name]) for name in SIGNALS},
            }
        ]
    )
    pred = model.predict(frame)[0]
    claim_type = int(row["claim_type"])
    type_name = CLAIM_TYPE_NAMES[claim_type]
    prob = _r4(pred.prob)
    signals = {name: _r4(row[name]) for name in SIGNALS}
    return {
        "claim_id": str(row["claim_id"]),
        "claim_text": str(row["claim_text"]),
        "sentence_index": int(str(row["claim_id"]).split("#", 1)[1]),
        "claim_type": claim_type,
        "claim_type_name": type_name,
        "generator_id": int(row["generator_id"]),
        "model_id": str(row["source_model"]),
        "model_name": MODEL_NAMES[str(row["source_model"])],
        "prob": prob,
        "predicted_class": _class_label(prob),
        "w_cross": _r4(pred.w_cross),
        "w_evid": _r4(pred.w_evid),
        "z_cross": _r4(pred.z_cross),
        "z_evid": _r4(pred.z_evid),
        "signals": signals,
        "cross_n_others": int(row["cross_n_others"]),
        "evidence_source": str(row["evidence_source"]),
        "evidence_n_passages": int(row["evidence_n_passages"]),
        "arithmetic_verdict": str(row["arithmetic_verdict"]),
        "explanation": one_line(prob, _r4(pred.w_evid), type_name, _r4(pred.z_cross), _r4(pred.z_evid)),
        "human_span_label": int(row["label"]),
        "generation_method": (
            "RCGateModel.predict on this stored signal-table row. "
            "Not an official benchmark result."
        ),
    }


def write_library(payload: dict, path: Path = DEFAULT_OUT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rcgate.demo.fixtures",
        description="Write recorded demo fixtures. Does not train or touch results/.",
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--table", default=str(DEFAULT_TABLE))
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--responses", default=str(DEFAULT_RESPONSES))
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    args = parser.parse_args(argv)
    payload = build_library(
        table_path=Path(args.table),
        checkpoint_path=Path(args.checkpoint),
        responses_path=Path(args.responses),
        sources_path=Path(args.sources),
    )
    path = write_library(payload, Path(args.out))
    print(f"wrote {path} ({len(payload['scenarios'])} scenarios)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

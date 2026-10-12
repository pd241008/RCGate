"""Score one stored sentence from a saved checkpoint.

Precomputed rows use the corrected signal table. Other sentences use the existing
extractor and the same checkpoint. Nothing is trained, and missing features are not invented.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import threading
from pathlib import Path

from ..data.ragtruth import sha256_of
from ..data.schema import CLAIM_TYPE_NAMES, CROSS_SIGNALS, EVID_SIGNALS, SIGNALS
from ..demo.fixtures import MODEL_NAMES
from ..explain import one_line
from ..paths import PROJECT_ROOT
from .catalog import CHECKPOINT_PATH, Catalog, PreparedSentence

THRESHOLD = 0.5
CLOSE_BAND = 0.05
MATCH_TOLERANCE = 1e-3
CACHE_DIR = PROJECT_ROOT / ".cache" / "studio"

PARTITION_NOTES = {
    "train": (
        "This source is in the training partition of the loaded checkpoint "
        "(group-stratified split seed 0). The probability is not an independent test result."
    ),
    "val": (
        "This source is in the validation partition of the loaded checkpoint "
        "(group-stratified split seed 0). The probability is not an independent test result."
    ),
    "test": (
        "This source is in the test partition of this one checkpoint "
        "(group-stratified split seed 0, model seed 0). "
        "That membership is not the Stage 8 mean, and this probability is still a demo inference "
        "on one sentence, not a benchmark score."
    ),
}


def local_weights_present() -> bool:
    """True when the NLI and embedding snapshots used by the experiments are on disk."""
    hub = PROJECT_ROOT / ".cache" / "models" / "hub"
    needed = (
        "models--cross-encoder--nli-deberta-v3-small",
        "models--sentence-transformers--all-MiniLM-L6-v2",
    )
    for name in needed:
        root = hub / name
        if not any(path.suffix in {".safetensors", ".bin"} for path in root.rglob("*") if path.is_file()):
            return False
    return True


class StudioScorer:
    def __init__(self, catalog: Catalog, cache_dir: Path | None = None) -> None:
        self.catalog = catalog
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.checkpoint_path = CHECKPOINT_PATH
        self._model = None
        self._extractors = None
        self._experts = None
        self._checkpoint_sha = None
        self.load_error: str | None = None
        self._lock = threading.Lock()

    @property
    def checkpoint_ready(self) -> bool:
        return self.checkpoint_path.is_file() and self.load_error is None

    @property
    def local_ready(self) -> bool:
        return self.checkpoint_ready and local_weights_present() and self.load_error is None

    def score(
        self,
        source_id: str,
        response_id: str,
        sentence_index: int,
        progress=None,
    ) -> dict:
        try:
            prepared = self.catalog.prepare(source_id, response_id, sentence_index)
        except KeyError as exc:
            return _failure("error", f"Unknown record: {exc}")
        except IndexError as exc:
            return _failure("unavailable", str(exc))
        except RuntimeError as exc:
            return _failure("unavailable", str(exc))

        row = self.catalog.precomputed_rows.get(prepared.claim_id)
        if row and _row_matches(row, prepared):
            if progress:
                progress("Loading the saved checkpoint")
            try:
                model = self._checkpoint()
            except Exception as exc:
                self.load_error = f"{type(exc).__name__}: {exc}"
                return _failure(
                    "unavailable",
                    "The saved checkpoint could not be loaded, so this stored feature row was not scored.",
                    prepared,
                )
            return self._from_signals(
                prepared,
                row["signals"],
                row,
                feature_source="precomputed_row",
                model=model,
                notes=[
                    "Features came from the corrected seed-0 signal table for this claim id, generator, sentence text, and claim type.",
                    "The probability is a recorded demo inference, not a benchmark evaluation of this question.",
                ],
            )

        if not self.checkpoint_path.is_file():
            return _failure(
                "unavailable",
                "No saved RC-Gate checkpoint is available, so this sentence cannot be scored.",
                prepared,
            )
        if not local_weights_present():
            return _failure(
                "unavailable",
                "Offline scoring is unavailable on this machine because the local NLI or embedding weights are missing. The stored answers can still be read.",
                prepared,
                notes=["No features were invented for this sentence."],
            )

        cached = self._read_cache(prepared)
        if cached is not None:
            cached["feature_source"] = "cached_local_extraction"
            cached["notes"] = list(cached.get("notes") or []) + [
                "Signals were loaded from a local demo cache of an earlier calculation on this machine."
            ]
            return cached

        if progress:
            progress("Loading local NLI and embedding weights")
        try:
            if progress:
                progress("Extracting signals from the stored texts")
            signals, provenance = self._extract(prepared)
            if progress:
                progress("Calculating the checkpoint probability")
            model = self._checkpoint()
        except Exception as exc:
            return _failure(
                "unavailable",
                f"Local feature extraction failed ({type(exc).__name__}: {exc}). No features were invented.",
                prepared,
            )
        result = self._from_signals(
            prepared,
            signals,
            provenance,
            feature_source="local_extraction",
            model=model,
            notes=[
                "Signals were calculated on this machine from the stored answer and the supplied task context.",
                "This is a local demo inference, not a new benchmark experiment and not a live provider response.",
            ],
        )
        self._write_cache(prepared, result)
        return result

    def _from_signals(self, prepared, signals, provenance, *, feature_source, model, notes) -> dict:
        import pandas as pd

        frame = pd.DataFrame(
            [
                {
                    "claim_type": prepared.claim_type,
                    "generator_id": prepared.generator_id,
                    **{name: float(signals[name]) for name in SIGNALS},
                }
            ]
        )
        explained = model.predict_frame(frame)
        prediction = model.predict(frame)[0]
        prob = float(prediction.prob)
        logit = float(explained["logit"][0])
        experts = self._expert_record(model)
        worked = _worked(experts, signals, prediction, logit, model)
        partition = self.catalog.partitions.get(prepared.source_id)
        close = abs(prob - THRESHOLD) <= CLOSE_BAND
        claim_type_name = CLAIM_TYPE_NAMES[prepared.claim_type]
        return {
            "status": "complete",
            "reason": None,
            "feature_source": feature_source,
            "demo_inference": True,
            "benchmark_evaluation": False,
            "partition": partition,
            "partition_note": _partition_note(partition, feature_source),
            "checkpoint": self._checkpoint_record(),
            "claim": _claim_payload(prepared),
            "prediction": {
                "prob": prob,
                "predicted_class": "Likely hallucinated" if prob >= THRESHOLD else "Likely supported",
                "threshold": THRESHOLD,
                "close_to_threshold": close,
                "close_note": "Close to the classification threshold; interpret cautiously." if close else None,
                "w_cross": float(prediction.w_cross),
                "w_evid": float(prediction.w_evid),
                "z_cross": float(prediction.z_cross),
                "z_evid": float(prediction.z_evid),
                "logit": logit,
                "signals": {name: float(signals[name]) for name in SIGNALS},
                "cross_n_others": int(provenance["cross_n_others"]),
                "evidence_source": str(provenance["evidence_source"]),
                "evidence_n_passages": int(provenance["evidence_n_passages"]),
                "arithmetic_verdict": str(provenance["arithmetic_verdict"]),
                "explanation": one_line(
                    prob,
                    float(prediction.w_evid),
                    claim_type_name,
                    float(prediction.z_cross),
                    float(prediction.z_evid),
                ),
            },
            "experts": experts,
            "worked": worked,
            "cache_path": None,
            "notes": [
                *notes,
                "The gate saw claim type and generator identity, not the signal values.",
                "Routing weights are not a proof of reliability.",
            ],
        }

    def _extract(self, prepared: PreparedSentence) -> tuple[dict, dict]:
        import pandas as pd

        from ..signals.extract import extract_signals

        scorer, embedder = self._local_extractors()
        frame = pd.DataFrame(
            [
                {
                    "question_id": prepared.source_id,
                    "claim_id": prepared.claim_id,
                    "benchmark": "ragtruth",
                    "claim_text": prepared.claim_text,
                    "claim_type": prepared.claim_type,
                    "generator_id": prepared.generator_id,
                    "label": prepared.label,
                    "context": prepared.context,
                    "source": prepared.dataset_source,
                    "task_type": prepared.task_type,
                    "source_model": prepared.model_id,
                    "label_types": "",
                    "response_quality": "",
                    "n_claims_in_answer": prepared.n_sentences,
                }
            ]
        )
        extracted, _report = extract_signals(
            frame,
            answers_by_question={prepared.source_id: prepared.answers},
            scorer=scorer,
            embedder=embedder,
        )
        row = extracted.iloc[0]
        signals = {name: float(row[name]) for name in SIGNALS}
        if any(math.isnan(value) for value in signals.values()):
            raise RuntimeError("extractor returned a missing signal")
        provenance = {
            "cross_n_others": int(row["cross_n_others"]),
            "evidence_source": str(row["evidence_source"]),
            "evidence_n_passages": int(row["evidence_n_passages"]),
            "arithmetic_verdict": str(row["arithmetic_verdict"]),
        }
        return signals, provenance

    def _local_extractors(self):
        with self._lock:
            if self._extractors is not None:
                return self._extractors
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            from ..signals.nli import (
                CachedEmbedder,
                CachedScorer,
                CrossEncoderScorer,
                Embedder,
                compute_cache,
            )

            inner = CrossEncoderScorer()
            if getattr(inner, "name", "") != "cross_encoder":
                raise RuntimeError("local scoring requires the cross-encoder backend")
            cache = compute_cache(root=self.cache_dir / "compute")
            wrapped = (
                CachedScorer(inner, cache),
                CachedEmbedder(Embedder(inner), cache),
            )
            self._extractors = wrapped
            return wrapped

    def _checkpoint(self):
        with self._lock:
            if self._model is not None:
                return self._model
            import joblib

            model = joblib.load(self.checkpoint_path)
            if not hasattr(model, "predict") or not hasattr(model, "predict_frame"):
                raise TypeError(f"{self.checkpoint_path} is not an RC-Gate checkpoint")
            self._model = model
            self._experts = None
            return model

    def _expert_record(self, model) -> dict:
        if self._experts is not None:
            return self._experts
        cross = [float(value) for value in model.model.cross_expert.weight.detach().cpu().flatten().tolist()]
        evid = [float(value) for value in model.model.evid_expert.weight.detach().cpu().flatten().tolist()]
        fusion = [float(value) for value in model.model.fusion.weight.detach().cpu().flatten().tolist()]
        self._experts = {
            "fusion_input": str(model.config.fusion_input),
            "standardize_signals": bool(model.config.standardize_signals),
            "cross": {"signals": list(CROSS_SIGNALS), "weights": cross, "bias": float(model.model.cross_expert.bias)},
            "evidence": {"signals": list(EVID_SIGNALS), "weights": evid, "bias": float(model.model.evid_expert.bias)},
            "fusion": {
                "weights": fusion,
                "bias": float(model.model.fusion.linear.bias.detach()),
            },
        }
        return self._experts

    def _checkpoint_record(self) -> dict:
        if self._checkpoint_sha is None:
            self._checkpoint_sha = sha256_of(self.checkpoint_path)
        try:
            path = str(self.checkpoint_path.resolve().relative_to(PROJECT_ROOT))
        except ValueError:
            path = str(self.checkpoint_path)
        return {
            "path": path,
            "sha256": self._checkpoint_sha,
            "variant": "A7",
            "split_seed": 0,
            "model_seed": 0,
            "split_method": "group_stratified",
            "namespace": "ragtruth_factorial_seed_v1",
        }

    def _cache_path(self, prepared: PreparedSentence) -> Path:
        blob = json.dumps(
            {
                "source_id": prepared.source_id,
                "response_id": prepared.response_id,
                "sentence_index": prepared.sentence_index,
                "claim_text": prepared.claim_text,
                "checkpoint": self._checkpoint_record()["sha256"],
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        return self.cache_dir / "scores" / f"{digest}.json"

    def _read_cache(self, prepared: PreparedSentence) -> dict | None:
        path = self._cache_path(prepared)
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["cache_path"] = str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path)
        return payload

    def _write_cache(self, prepared: PreparedSentence, result: dict) -> None:
        path = self._cache_path(prepared)
        path.parent.mkdir(parents=True, exist_ok=True)
        stored = dict(result)
        stored["cache_path"] = str(path.relative_to(PROJECT_ROOT)) if path.is_relative_to(PROJECT_ROOT) else str(path)
        path.write_text(json.dumps(stored, ensure_ascii=False), encoding="utf-8")
        result["cache_path"] = stored["cache_path"]


def _row_matches(row: dict, prepared: PreparedSentence) -> bool:
    return (
        row["question_id"] == prepared.source_id
        and row["claim_id"] == prepared.claim_id
        and int(row["generator_id"]) == prepared.generator_id
        and row["claim_text"] == prepared.claim_text
        and int(row["claim_type"]) == prepared.claim_type
        and row["source_model"] in MODEL_NAMES
    )


def _claim_payload(prepared: PreparedSentence) -> dict:
    return {
        "source_id": prepared.source_id,
        "response_id": prepared.response_id,
        "claim_id": prepared.claim_id,
        "sentence_index": prepared.sentence_index,
        "original_sentence": prepared.original_sentence,
        "claim_text": prepared.claim_text,
        "dealias_changed": prepared.dealias_changed,
        "start": prepared.start,
        "end": prepared.end,
        "claim_type": prepared.claim_type,
        "claim_type_name": prepared.claim_type_name,
        "claim_type_rule": prepared.claim_type_rule,
        "generator_id": prepared.generator_id,
        "model_id": prepared.model_id,
        "model_name": prepared.model_name,
        "human_span_label": prepared.label,
        "n_sentences": prepared.n_sentences,
        "task_type": prepared.task_type,
    }


def _partition_note(partition: str | None, feature_source: str) -> str:
    base = PARTITION_NOTES.get(
        partition or "",
        "This source is not in the corrected 800-sentence table, so it has no train, validation, or test assignment for the loaded checkpoint.",
    )
    if feature_source == "precomputed_row":
        return base + " The probability is a recorded demo inference on one stored sentence, not a benchmark score."
    return base + " The probability is a local demo inference, not a benchmark score."


def _worked(experts: dict, signals: dict, prediction, logit: float, model) -> dict:
    values = _maybe_scale(model, [float(signals[name]) for name in SIGNALS])
    cross_values = values[:3]
    evid_values = values[3:]
    z_cross = _affine(experts["cross"]["weights"], experts["cross"]["bias"], cross_values)
    z_evid = _affine(experts["evidence"]["weights"], experts["evidence"]["bias"], evid_values)
    fused = (
        experts["fusion"]["weights"][0] * (float(prediction.w_cross) * z_cross)
        + experts["fusion"]["weights"][1] * (float(prediction.w_evid) * z_evid)
        + experts["fusion"]["bias"]
    )
    prob = 1.0 / (1.0 + math.exp(-fused))
    errors = {
        "z_cross_error": abs(z_cross - float(prediction.z_cross)),
        "z_evid_error": abs(z_evid - float(prediction.z_evid)),
        "logit_error": abs(fused - logit),
        "prob_error": abs(prob - float(prediction.prob)),
    }
    return {
        "z_cross": z_cross,
        "z_evid": z_evid,
        "logit": fused,
        "prob": prob,
        "signal_values": values,
        **errors,
        "matches_model": all(error <= MATCH_TOLERANCE for error in errors.values()),
        "tolerance": MATCH_TOLERANCE,
    }


def _maybe_scale(model, values: list[float]) -> list[float]:
    if not bool(model.config.standardize_signals):
        return values
    mean = model.model.signal_mean.detach().cpu().flatten().tolist()
    std = model.model.signal_std.detach().cpu().flatten().tolist()
    return [(value - float(mu)) / float(sigma) for value, mu, sigma in zip(values, mean, std, strict=True)]


def _affine(weights: list[float], bias: float, values: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, values, strict=True)) + bias


def _failure(status: str, reason: str, prepared: PreparedSentence | None = None, notes: list[str] | None = None) -> dict:
    return {
        "status": status,
        "reason": reason,
        "feature_source": None,
        "demo_inference": True,
        "benchmark_evaluation": False,
        "partition": None,
        "partition_note": None,
        "checkpoint": None,
        "claim": _claim_payload(prepared) if prepared else None,
        "prediction": None,
        "experts": None,
        "worked": None,
        "cache_path": None,
        "notes": notes or ["No features were invented."],
    }

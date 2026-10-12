"""In-memory index of the local RAGTruth files.

Search returns short cards. Full answers and context are loaded only for one source.
No signal extraction runs here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import pandas as pd

from ..claims.claim_type import classify
from ..data.ragtruth import (
    DATASET_CITATION,
    DATASET_LICENSE,
    DATASET_NAME,
    DATASET_URL,
    DEFAULT_ROSTER,
    FILES,
    claims_from_response,
    dealias_labelled_claims,
    load_jsonl,
    sentence_spans,
    sha256_of,
)
from ..data.schema import CLAIM_TYPE_NAMES, SIGNALS
from ..data.splits import group_stratified_split
from ..demo.fixtures import MODEL_NAMES
from ..paths import PROJECT_ROOT
from .references import (
    EMPTY_NOTE,
    SEPARATION_NOTE,
    load_references,
    references_for,
)
from .topics import TOPIC_NOTE, TOPIC_ORDER, assign_topic, topic_label

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ragtruth"
TABLE_PATH = PROJECT_ROOT / "data" / "signal_tables" / "ragtruth_corrected_integrity_v1_s0.parquet"
CHECKPOINT_PATH = (
    PROJECT_ROOT / "results" / "summary" / "ragtruth_factorial_seed_v1" / "A7_split0_model0" / "model.joblib"
)

PREVIEW_CHARS = 500
EXCERPT_CHARS = 180
TASK_LABELS = {"QA": "QA", "Summary": "Summary", "Data2txt": "Data-to-text"}
SCORE_LABELS = {
    "precomputed": "Precomputed first-sentence scores",
    "local": "Needs local scoring",
    "unavailable": "Scoring unavailable offline",
}

QA_CONTEXT_NOTE = (
    "These are the passages supplied to the original models. "
    "RC-Gate also uses this context when calculating its evidence signals."
)
OTHER_CONTEXT_NOTE = (
    "This is the source material supplied with the original task. "
    "RC-Gate also uses this material when calculating its evidence signals."
)
PROMPT_NOTE = (
    "RAGTruth stores a prompt field for this source. The text below is that stored field. "
    "This interface does not reproduce an unavailable provider request byte for byte; "
    "it shows the prompt text recorded in the dataset."
)
_PASSAGE_MARK = re.compile(r"passage\s+(\d+)\s*:", re.IGNORECASE)
_WORD_LIMIT = re.compile(r"within\s+(\d+)\s+words", re.IGNORECASE)


@dataclass
class ResponseRecord:
    response_id: str
    model_id: str
    model_name: str
    generator_id: int
    text: str
    quality: str
    dataset_split: str
    n_annotation_spans: int
    labels: list


@dataclass
class SourceRecord:
    source_id: str
    task_type: str
    dataset_source: str
    topic_id: str
    topic_label: str
    title: str
    preview: str
    prompt: str
    source_info: object
    responses: list[ResponseRecord]
    search_all: str
    search_by_model: dict[str, str]
    precomputed_claim_ids: list[str] = field(default_factory=list)

    def response_by_id(self) -> dict[str, ResponseRecord]:
        return {item.response_id: item for item in self.responses}


@dataclass
class PreparedSentence:
    source_id: str
    response_id: str
    generator_id: int
    model_id: str
    model_name: str
    sentence_index: int
    claim_id: str
    original_sentence: str
    claim_text: str
    dealias_changed: bool
    start: int
    end: int
    claim_type: int
    claim_type_name: str
    claim_type_rule: str
    label: int
    n_sentences: int
    context: str
    answers: dict[int, str]
    task_type: str
    dataset_source: str


class Catalog:
    def __init__(
        self,
        sources: dict[str, SourceRecord],
        precomputed_rows: dict[str, dict],
        partitions: dict[str, str],
        references: list[dict],
        file_hashes: dict[str, dict],
        table_sha256: str,
        response_count: int,
    ) -> None:
        self.sources = sources
        self.precomputed_rows = precomputed_rows
        self.partitions = partitions
        self.references = references
        self.file_hashes = file_hashes
        self.table_sha256 = table_sha256
        self.response_count = response_count
        self._sentences: dict[tuple[str, str], list[dict]] = {}
        self.order = sorted(sources, key=_source_sort)

    @classmethod
    def load(cls) -> Catalog:
        file_hashes = {}
        for name, expected in FILES.items():
            actual = sha256_of(RAW_DIR / name)
            file_hashes[name] = {
                "sha256": actual,
                "expected": expected,
                "match": actual == expected,
            }
        raw_sources = {
            str(row["source_id"]): row for row in load_jsonl(RAW_DIR / "source_info.jsonl")
        }
        grouped: dict[str, list[ResponseRecord]] = {sid: [] for sid in raw_sources}
        response_count = 0
        roster = {model: index for index, model in enumerate(DEFAULT_ROSTER)}
        for row in load_jsonl(RAW_DIR / "response.jsonl"):
            response_count += 1
            source_id = str(row.get("source_id"))
            model_id = str(row.get("model", ""))
            if source_id not in grouped or model_id not in roster:
                continue
            grouped[source_id].append(
                ResponseRecord(
                    response_id=str(row.get("id")),
                    model_id=model_id,
                    model_name=MODEL_NAMES.get(model_id, model_id),
                    generator_id=roster[model_id],
                    text=str(row.get("response") or ""),
                    quality=str(row.get("quality") or ""),
                    dataset_split=str(row.get("split") or ""),
                    n_annotation_spans=len(row.get("labels") or []),
                    labels=list(row.get("labels") or []),
                )
            )

        table = pd.read_parquet(TABLE_PATH)
        precomputed_rows = {
            str(row["claim_id"]): _row_dict(row) for _, row in table.iterrows()
        }
        by_source: dict[str, list[str]] = {}
        for claim_id, row in precomputed_rows.items():
            by_source.setdefault(row["question_id"], []).append(claim_id)
        partitions = _partitions(table)
        references = load_references()

        sources: dict[str, SourceRecord] = {}
        for source_id, raw in raw_sources.items():
            responses = sorted(grouped.get(source_id, []), key=lambda item: item.generator_id)
            title, preview, topic_text = _describe(raw)
            topic_id, label = assign_topic(str(raw.get("task_type") or ""), topic_text)
            prompt = str(raw.get("prompt") or "")
            answer_text = "\n".join(item.text for item in responses)
            base = f"{title}\n{preview}".lower()
            sources[source_id] = SourceRecord(
                source_id=source_id,
                task_type=str(raw.get("task_type") or ""),
                dataset_source=str(raw.get("source") or ""),
                topic_id=topic_id,
                topic_label=label,
                title=title,
                preview=preview,
                prompt=prompt,
                source_info=raw.get("source_info"),
                responses=responses,
                search_all=f"{base}\n{answer_text}".lower(),
                search_by_model={
                    item.model_id: f"{base}\n{item.text}".lower() for item in responses
                },
                precomputed_claim_ids=sorted(by_source.get(source_id, [])),
            )
        return cls(
            sources=sources,
            precomputed_rows=precomputed_rows,
            partitions=partitions,
            references=references,
            file_hashes=file_hashes,
            table_sha256=sha256_of(TABLE_PATH),
            response_count=response_count,
        )

    def inventory(self, *, checkpoint_ready: bool, local_ready: bool) -> dict:
        tasks: dict[str, int] = {}
        topics: dict[str, int] = {}
        generators = dict.fromkeys(DEFAULT_ROSTER, 0)
        partial = []
        for source in self.sources.values():
            tasks[source.task_type] = tasks.get(source.task_type, 0) + 1
            topics[source.topic_id] = topics.get(source.topic_id, 0) + 1
            for response in source.responses:
                generators[response.model_id] = generators.get(response.model_id, 0) + 1
            n_pre = len(source.precomputed_claim_ids)
            if 0 < n_pre < len(DEFAULT_ROSTER):
                partial.append({"source_id": source.source_id, "n_claims": n_pre})
        pre_sources = sum(1 for source in self.sources.values() if source.precomputed_claim_ids)
        needing_local = len(self.sources) - pre_sources
        return {
            "dataset": DATASET_NAME,
            "citation": DATASET_CITATION,
            "license": DATASET_LICENSE,
            "url": DATASET_URL,
            "n_sources": len(self.sources),
            "n_responses": self.response_count,
            "tasks": tasks,
            "topics": [
                {"id": topic_id, "label": topic_label(topic_id), "count": topics.get(topic_id, 0)}
                for topic_id in TOPIC_ORDER
            ],
            "generators": [
                {"id": model, "label": MODEL_NAMES[model], "count": generators.get(model, 0)}
                for model in DEFAULT_ROSTER
            ],
            "files": self.file_hashes,
            "signal_table": {
                "path": _relative(TABLE_PATH),
                "sha256": self.table_sha256,
                "n_claims": len(self.precomputed_rows),
                "n_sources": pre_sources,
                "claim_scope": "first_sentence",
                "partial_sources": partial,
                "note": (
                    "Corrected seed-0 table. Each stored claim is sentence index 0 "
                    "of one recorded answer. It is not a feature row for every sentence."
                ),
            },
            "scoring": {
                "browseable_sources": len(self.sources),
                "precomputed_claims": len(self.precomputed_rows),
                "precomputed_sources": pre_sources,
                "sources_without_precomputed_rows": needing_local,
                "checkpoint_ready": checkpoint_ready,
                "local_extraction_ready": local_ready,
                "checkpoint_path": _relative(CHECKPOINT_PATH),
                "unavailable_without_local_weights": 0 if local_ready else needing_local,
            },
            "topic_note": TOPIC_NOTE,
            "distinctions": _distinctions(len(self.sources), len(self.precomputed_rows), pre_sources, local_ready),
        }

    def search(
        self,
        *,
        q: str = "",
        task: str = "",
        topic: str = "",
        generator: str = "",
        score: str = "",
        sort: str = "auto",
        page: int = 1,
        page_size: int = 20,
        checkpoint_ready: bool = True,
        local_ready: bool = False,
    ) -> dict:
        page = max(1, int(page))
        page_size = min(50, max(1, int(page_size)))
        query = q.strip()
        chosen_sort = sort if sort in {"auto", "relevance", "task", "topic", "source"} else "auto"
        if chosen_sort == "auto":
            chosen_sort = "relevance" if query else "source"
        tokens = [part for part in query.lower().split() if part]

        def status(source: SourceRecord) -> str:
            return _score_status(source, checkpoint_ready=checkpoint_ready, local_ready=local_ready)

        def keep(source: SourceRecord, skip: str = "") -> bool:
            if skip != "task" and task and source.task_type != task:
                return False
            if skip != "topic" and topic and source.topic_id != topic:
                return False
            if skip != "generator" and generator and generator not in source.search_by_model:
                return False
            if skip != "score" and score and status(source) != score:
                return False
            if tokens:
                haystack = source.search_by_model.get(generator, source.search_all) if generator else source.search_all
                if not all(token in haystack for token in tokens):
                    return False
            return True

        matched = [source for source in self.sources.values() if keep(source)]
        matched.sort(key=lambda source: _sort_key(source, chosen_sort, tokens, generator))
        start = (page - 1) * page_size
        page_rows = matched[start : start + page_size]
        return {
            "total": len(matched),
            "page": page,
            "page_size": page_size,
            "n_pages": max(1, (len(matched) + page_size - 1) // page_size),
            "applied": {
                "q": query,
                "task": task,
                "topic": topic,
                "generator": generator,
                "score": score,
                "sort": chosen_sort,
                "page": page,
                "page_size": page_size,
            },
            "facets": {
                "tasks": _facet(self, "task", keep),
                "topics": _facet(self, "topic", keep),
                "generators": _facet(self, "generator", keep),
                "scores": _facet(self, "score", keep, status),
            },
            "results": [
                _card(source, status(source), generator) for source in page_rows
            ],
            "inventory_totals": {
                "sources": len(self.sources),
                "responses": self.response_count,
            },
            "topic_note": TOPIC_NOTE,
        }

    def record(self, source_id: str, *, checkpoint_ready: bool, local_ready: bool) -> dict | None:
        source = self.sources.get(str(source_id))
        if source is None:
            return None
        refs = references_for(self.references, source.source_id)
        pre_generators = [
            int(self.precomputed_rows[claim_id]["generator_id"])
            for claim_id in source.precomputed_claim_ids
        ]
        default_generator = min(pre_generators) if pre_generators else 0
        default_response = next(
            (
                item.response_id
                for item in source.responses
                if item.generator_id == default_generator
            ),
            source.responses[0].response_id if source.responses else "",
        )
        responses = []
        for response in source.responses:
            sentences = self.sentences(
                source,
                response,
                checkpoint_ready=checkpoint_ready,
                local_ready=local_ready,
            )
            responses.append(
                {
                    "response_id": response.response_id,
                    "model_id": response.model_id,
                    "model_name": response.model_name,
                    "generator_id": response.generator_id,
                    "text": response.text,
                    "quality": response.quality,
                    "dataset_split": response.dataset_split,
                    "n_annotation_spans": response.n_annotation_spans,
                    "provenance": f"RAGTruth response.jsonl id {response.response_id}",
                    "sentences": sentences,
                }
            )
        task = _task_view(source)
        return {
            "source_id": source.source_id,
            "task_type": source.task_type,
            "task_label": TASK_LABELS.get(source.task_type, source.task_type),
            "dataset_source": source.dataset_source,
            "topic_id": source.topic_id,
            "topic_label": source.topic_label,
            "topic_note": TOPIC_NOTE,
            "title": source.title,
            "task": task,
            "passages": task["passages"],
            "structured": task["structured"],
            "responses": responses,
            "independent_references": refs,
            "independent_reference_note": SEPARATION_NOTE if refs else EMPTY_NOTE,
            "precomputed_claim_ids": list(source.precomputed_claim_ids),
            "partition": self.partitions.get(source.source_id),
            "scoring": {
                "precomputed_claims": len(source.precomputed_claim_ids),
                "local_extraction_ready": local_ready,
                "checkpoint_ready": checkpoint_ready,
                "default_response_id": default_response,
                "default_sentence_index": 0,
                "score_status": _score_status(
                    source, checkpoint_ready=checkpoint_ready, local_ready=local_ready
                ),
            },
        }

    def sentences(
        self,
        source: SourceRecord,
        response: ResponseRecord,
        *,
        checkpoint_ready: bool = True,
        local_ready: bool = False,
    ) -> list[dict]:
        key = (source.source_id, response.response_id)
        cached = self._sentences.get(key)
        if cached is None:
            cached = _sentence_rows(self, source, response)
            self._sentences[key] = cached
        rows = []
        for item in cached:
            row = dict(item)
            matched = bool(row.pop("precomputed_match"))
            if matched and checkpoint_ready:
                row["score_status"] = "precomputed"
            elif local_ready:
                row["score_status"] = "local"
            else:
                row["score_status"] = "unavailable"
            rows.append(row)
        return rows

    def prepare(self, source_id: str, response_id: str, sentence_index: int) -> PreparedSentence:
        source = self.sources.get(str(source_id))
        if source is None:
            raise KeyError(f"unknown source {source_id}")
        response = source.response_by_id().get(str(response_id))
        if response is None:
            raise KeyError(f"unknown response {response_id}")
        rows = self.sentences(source, response, checkpoint_ready=True, local_ready=True)
        chosen = next((row for row in rows if row["index"] == int(sentence_index)), None)
        if chosen is None:
            raise IndexError(
                f"response {response_id} has {len(rows)} sentences; index {sentence_index} is absent"
            )
        answers = {item.generator_id: item.text for item in source.responses}
        return PreparedSentence(
            source_id=source.source_id,
            response_id=response.response_id,
            generator_id=response.generator_id,
            model_id=response.model_id,
            model_name=response.model_name,
            sentence_index=chosen["index"],
            claim_id=chosen["claim_id"],
            original_sentence=chosen["text"],
            claim_text=chosen["scoring_text"],
            dealias_changed=chosen["dealias_changed"],
            start=chosen["start"],
            end=chosen["end"],
            claim_type=chosen["claim_type"],
            claim_type_name=chosen["claim_type_name"],
            claim_type_rule=chosen["claim_type_rule"],
            label=chosen["human_span_label"],
            n_sentences=len(rows),
            context=_scoring_context(source),
            answers=answers,
            task_type=source.task_type,
            dataset_source=source.dataset_source,
        )

    def alignment_problems(self) -> list[str]:
        problems: list[str] = []
        for claim_id, row in self.precomputed_rows.items():
            source = self.sources.get(row["question_id"])
            if source is None:
                problems.append(f"{claim_id} source {row['question_id']} missing")
                continue
            response_id = claim_id.split("#", 1)[0]
            response = source.response_by_id().get(response_id)
            if response is None:
                problems.append(f"{claim_id} response missing")
                continue
            try:
                prepared = self.prepare(source.source_id, response_id, int(claim_id.split("#", 1)[1]))
            except (KeyError, IndexError) as exc:
                problems.append(f"{claim_id} {exc}")
                continue
            if prepared.claim_text != row["claim_text"]:
                problems.append(f"{claim_id} text mismatch")
            if prepared.claim_type != int(row["claim_type"]):
                problems.append(
                    f"{claim_id} claim type {prepared.claim_type} != stored {row['claim_type']}"
                )
            if prepared.generator_id != int(row["generator_id"]):
                problems.append(f"{claim_id} generator mismatch")
            if set(row["signals"]) != set(SIGNALS):
                problems.append(f"{claim_id} signal keys")
        return problems


def _sentence_rows(catalog: Catalog, source: SourceRecord, response: ResponseRecord) -> list[dict]:
    context = _scoring_context(source)
    dealt_pairs = _dealias(source, response)
    rows = []
    for claim, dealt, start, end in dealt_pairs:
        claim_id = f"{response.response_id}#{claim.index}"
        stored = catalog.precomputed_rows.get(claim_id)
        classification = classify(dealt.text, context or None)
        precomputed = bool(
            stored
            and stored["question_id"] == source.source_id
            and int(stored["generator_id"]) == response.generator_id
            and stored["claim_text"] == dealt.text
            and int(stored["claim_type"]) == classification.claim_type
        )
        rows.append(
            {
                "index": claim.index,
                "claim_id": claim_id,
                "text": claim.text,
                "scoring_text": dealt.text,
                "dealias_changed": dealt.n_changed > 0,
                "start": start,
                "end": end,
                "precomputed_match": precomputed,
                "claim_type": classification.claim_type,
                "claim_type_name": CLAIM_TYPE_NAMES[classification.claim_type],
                "claim_type_rule": classification.rule,
                "human_span_label": int(claim.label),
            }
        )
    return rows


def _dealias(source: SourceRecord, response: ResponseRecord) -> list[tuple]:
    claims = claims_from_response(
        {
            "id": response.response_id,
            "source_id": source.source_id,
            "model": response.model_id,
            "response": response.text,
            "labels": response.labels,
            "quality": response.quality,
        },
        response.generator_id,
    )
    dealt = dealias_labelled_claims(claims, source.prompt)
    spans = sentence_spans(response.text)
    if len(spans) != len(dealt):
        raise RuntimeError(
            f"{response.response_id} has {len(spans)} spans and {len(dealt)} de-aliased sentences"
        )
    return [
        (claim, dealt_row, start, end)
        for (claim, dealt_row), (start, end, _text) in zip(dealt, spans, strict=True)
    ]


def _row_dict(row: pd.Series) -> dict:
    return {
        "question_id": str(row["question_id"]),
        "claim_id": str(row["claim_id"]),
        "claim_text": str(row["claim_text"]),
        "claim_type": int(row["claim_type"]),
        "generator_id": int(row["generator_id"]),
        "source_model": str(row["source_model"]),
        "label": int(row["label"]),
        "signals": {name: float(row[name]) for name in SIGNALS},
        "cross_n_others": int(row["cross_n_others"]),
        "evidence_source": str(row["evidence_source"]),
        "evidence_n_passages": int(row["evidence_n_passages"]),
        "arithmetic_verdict": str(row["arithmetic_verdict"]),
        "sentence_index": int(str(row["claim_id"]).split("#", 1)[1]),
        "response_id": str(row["claim_id"]).split("#", 1)[0],
    }


def _partitions(table: pd.DataFrame) -> dict[str, str]:
    split = group_stratified_split(table, seed=0)
    assigned: dict[str, str] = {}
    for name, frame in (("train", split.train), ("val", split.val), ("test", split.test)):
        for question_id in frame["question_id"].astype(str).unique():
            assigned[str(question_id)] = name
    return assigned


def _describe(raw: dict) -> tuple[str, str, str]:
    info = raw.get("source_info")
    task = str(raw.get("task_type") or "")
    if task == "QA" and isinstance(info, dict):
        question = str(info.get("question") or "").strip()
        passages = _passage_text(info)
        preview = _clip(passages, PREVIEW_CHARS)
        return question or "(question field empty)", preview, f"{question}\n{passages[:800]}"
    if task == "Summary":
        article = str(info or "")
        spans = sentence_spans(article)
        title = spans[0][2] if spans else _clip(article, 160)
        title = _clip(title, 180)
        return title or "Summary", _clip(article, PREVIEW_CHARS), article[:1200]
    if isinstance(info, dict):
        name = str(info.get("name") or "Business overview")
        city = str(info.get("city") or "")
        state = str(info.get("state") or "")
        title = ", ".join(part for part in (name, city, state) if part)
        readable = _business_text(info)
        return title, _clip(readable, PREVIEW_CHARS), readable[:800]
    text = str(info or "")
    return _clip(text, 160) or "Untitled record", _clip(text, PREVIEW_CHARS), text[:800]


def _passage_text(info: dict) -> str:
    raw = str(info.get("passages") or "")
    marks = list(_PASSAGE_MARK.finditer(raw))
    if not marks:
        return raw.strip()
    chunks = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(raw)
        text = raw[mark.end() : end].strip()
        if text:
            chunks.append(text)
    return "\n\n".join(chunks)


def _passages(info: dict) -> list[dict]:
    raw = str(info.get("passages") or "")
    marks = list(_PASSAGE_MARK.finditer(raw))
    rows = []
    if not marks and raw.strip():
        rows.append(_passage(1, raw.strip()))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(raw)
        text = raw[mark.end() : end].strip()
        if text:
            rows.append(_passage(int(mark.group(1)), text))
    return rows


def _passage(number: int, text: str) -> dict:
    return {
        "id": f"passage-{number}",
        "title": f"Supplied context passage {number}",
        "text": text,
        "kind": "supplied_context",
        "evidence_input": True,
    }


def _business_text(info: dict) -> str:
    reviews = _reviews(info.get("review_info"))
    review_text = " ".join(item["text"] for item in reviews[:2])
    return " ".join(
        part
        for part in (
            str(info.get("name") or ""),
            str(info.get("categories") or ""),
            str(info.get("city") or ""),
            review_text,
        )
        if part
    )


def _reviews(value) -> list[dict]:
    raw = value
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    rows = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "stars": item.get("review_stars"),
                "date": str(item.get("review_date") or ""),
                "text": str(item.get("review_text") or ""),
            }
        )
    return rows


def _hours(value) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _task_view(source: SourceRecord) -> dict:
    info = source.source_info
    kind = {"QA": "qa", "Summary": "summary", "Data2txt": "data2txt"}.get(source.task_type, "other")
    question = None
    instruction = ""
    passages: list[dict] = []
    structured = None
    if kind == "qa" and isinstance(info, dict):
        question = str(info.get("question") or "").strip()
        instruction = "Answer the stored question using the supplied passages."
        passages = _passages(info)
        note = QA_CONTEXT_NOTE
    elif kind == "summary":
        limit = _WORD_LIMIT.search(source.prompt or "")
        if limit:
            instruction = f"Summarize the stored news article within {limit.group(1)} words."
        else:
            instruction = "Summarize the stored news article."
        article = str(info or "")
        passages = [
            {
                "id": "article",
                "title": "Article supplied with the summary task",
                "text": article,
                "kind": "supplied_context",
                "evidence_input": True,
            }
        ]
        note = OTHER_CONTEXT_NOTE
    else:
        instruction = "Write an objective overview of this local business from the structured data."
        data = info if isinstance(info, dict) else {}
        structured = {
            "name": data.get("name"),
            "address": data.get("address"),
            "city": data.get("city"),
            "state": data.get("state"),
            "categories": data.get("categories"),
            "stars": data.get("business_stars"),
            "hours": _hours(data.get("hours")),
            "reviews": _reviews(data.get("review_info")),
        }
        passages = [
            {
                "id": "business-record",
                "title": "Business record supplied with the data-to-text task",
                "text": _business_text(data) if data else "",
                "kind": "supplied_context",
                "evidence_input": True,
            }
        ]
        note = OTHER_CONTEXT_NOTE
    return {
        "kind": kind,
        "question": question,
        "instruction": instruction,
        "context_note": note,
        "prompt_note": PROMPT_NOTE,
        "prompt": source.prompt,
        "passages": passages,
        "structured": structured,
    }


def _scoring_context(source: SourceRecord) -> str:
    """The context string ``build_slice`` passes to the extractor."""
    return str(source.source_info or "")


def _score_status(source: SourceRecord, *, checkpoint_ready: bool, local_ready: bool) -> str:
    if source.precomputed_claim_ids and checkpoint_ready:
        return "precomputed"
    if local_ready:
        return "local"
    return "unavailable"


def _card(source: SourceRecord, status: str, generator: str) -> dict:
    response = _excerpt_response(source, generator)
    n_pre = len(source.precomputed_claim_ids)
    if status == "precomputed" and n_pre < len(source.responses):
        label = f"Precomputed scores for {n_pre} of {len(source.responses)} generators"
    else:
        label = SCORE_LABELS[status]
    return {
        "source_id": source.source_id,
        "task_type": source.task_type,
        "task_label": TASK_LABELS.get(source.task_type, source.task_type),
        "dataset_source": source.dataset_source,
        "topic_id": source.topic_id,
        "topic_label": source.topic_label,
        "title": source.title,
        "excerpt": _clip(response.text if response else "", EXCERPT_CHARS),
        "excerpt_model_id": response.model_id if response else "",
        "excerpt_model_name": response.model_name if response else "",
        "excerpt_response_id": response.response_id if response else "",
        "n_generators": len(source.responses),
        "n_precomputed_claims": n_pre,
        "score_status": status,
        "score_label": label,
    }


def _excerpt_response(source: SourceRecord, generator: str) -> ResponseRecord | None:
    if generator:
        for response in source.responses:
            if response.model_id == generator:
                return response
    for response in source.responses:
        if response.generator_id == 0:
            return response
    return source.responses[0] if source.responses else None


def _facet(catalog: Catalog, kind: str, keep, status=None) -> list[dict]:
    if kind == "task":
        values = [(key, TASK_LABELS.get(key, key)) for key in ("QA", "Summary", "Data2txt")]
        return [
            {"id": key, "label": label, "count": sum(1 for source in catalog.sources.values() if keep(source, "task") and source.task_type == key)}
            for key, label in values
        ]
    if kind == "topic":
        counts: dict[str, int] = {}
        for source in catalog.sources.values():
            if keep(source, "topic"):
                counts[source.topic_id] = counts.get(source.topic_id, 0) + 1
        return [
            {"id": topic_id, "label": topic_label(topic_id), "count": counts.get(topic_id, 0)}
            for topic_id in TOPIC_ORDER
        ]
    if kind == "generator":
        return [
            {
                "id": model,
                "label": MODEL_NAMES[model],
                "count": sum(
                    1
                    for source in catalog.sources.values()
                    if keep(source, "generator") and model in source.search_by_model
                ),
            }
            for model in DEFAULT_ROSTER
        ]
    rows = []
    for key in ("precomputed", "local", "unavailable"):
        count = 0
        for source in catalog.sources.values():
            if keep(source, "score") and status is not None and status(source) == key:
                count += 1
        rows.append({"id": key, "label": SCORE_LABELS[key], "count": count})
    return rows


def _sort_key(source: SourceRecord, sort: str, tokens: list[str], generator: str):
    if sort == "relevance":
        haystack = source.search_by_model.get(generator, source.search_all) if generator else source.search_all
        score = sum(haystack.count(token) for token in tokens)
        return (-score, _source_sort(source.source_id))
    if sort == "task":
        return (source.task_type, _source_sort(source.source_id))
    if sort == "topic":
        return (source.topic_label, _source_sort(source.source_id))
    return (_source_sort(source.source_id),)


def _source_sort(source_id: str):
    if source_id.isdigit():
        return (0, int(source_id))
    return (1, source_id)


def _clip(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= limit:
        return compact
    cut = compact[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def _relative(path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _distinctions(n_sources: int, n_claims: int, n_pre_sources: int, local_ready: bool) -> list[dict]:
    local_sentence = (
        "Any other stored sentence can be scored on request with the local NLI and embedding weights and the same checkpoint. That calculation is a demo inference. It is not a new benchmark run."
        if local_ready
        else "Local NLI or embedding weights are not available, so sentences without a stored feature row cannot be scored on this machine."
    )
    return [
        {
            "id": "browse",
            "title": "Available to browse",
            "detail": f"All {n_sources} local source records and their recorded answers can be searched. Nothing is dropped because a topic rule missed it.",
        },
        {
            "id": "precomputed",
            "title": "Precomputed features",
            "detail": (
                f"{n_claims} first-sentence claims across {n_pre_sources} sources have rows in the corrected signal table. "
                "Those rows are not a complete sentence table for the corpus."
            ),
        },
        {
            "id": "local",
            "title": "Scorable with the local pipeline",
            "detail": local_sentence,
        },
        {
            "id": "unavailable",
            "title": "Not scored from the resources here",
            "detail": (
                "A sentence cannot be scored when its text does not match a stored feature row and the local extractor cannot run, "
                "or when the saved checkpoint cannot be loaded. Missing features are left missing."
            ),
        },
    ]

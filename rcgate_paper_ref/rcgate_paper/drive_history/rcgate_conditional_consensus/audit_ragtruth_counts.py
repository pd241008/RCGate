"""Read-only RAGTruth counts for the conditional-consensus data audit.

Does not write under data/raw, does not call a model, and does not fit a score.
Run from the repository root:

    python research/rcgate_conditional_consensus/audit_ragtruth_counts.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rcgate.data.ragtruth import (  # noqa: E402
    FILES,
    HALLUCINATION_LABEL_TYPES,
    sentence_spans,
)

RAW = ROOT / "data" / "raw" / "ragtruth"
OUT = Path(__file__).resolve().parent / "audit_ragtruth_counts.json"

WS = re.compile(r"\s+")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def norm(text: str) -> str:
    return WS.sub(" ", (text or "").strip().lower())


def source_text(record: dict) -> str:
    payload = record.get("source_info")
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)
    source = record.get("source")
    if isinstance(source, str):
        return source
    return json.dumps(source, sort_keys=True, ensure_ascii=False) if source is not None else ""


def overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and a_end > b_start


def main() -> None:
    response_path = RAW / "response.jsonl"
    source_path = RAW / "source_info.jsonl"
    responses = load_jsonl(response_path)
    sources = load_jsonl(source_path)

    response_keys = Counter(tuple(sorted(row.keys())) for row in responses)
    source_keys = Counter(tuple(sorted(row.keys())) for row in sources)
    label_keys = Counter()
    label_types = Counter()
    quality = Counter()
    models = Counter()
    splits = Counter()
    task_by_source = {}
    implicit_true = Counter()
    due_to_null = Counter()
    temperatures = Counter()

    for row in responses:
        quality[str(row.get("quality"))] += 1
        models[str(row.get("model"))] += 1
        splits[str(row.get("split"))] += 1
        temperatures[str(row.get("temperature"))] += 1
        for span in row.get("labels") or []:
            label_keys[tuple(sorted(span.keys()))] += 1
            label_types[str(span.get("label_type"))] += 1
            implicit_true[str(span.get("implicit_true"))] += 1
            due_to_null[str(span.get("due_to_null"))] += 1

    for row in sources:
        task_by_source[str(row.get("source_id"))] = str(row.get("task_type"))

    by_source_models: dict[str, set[str]] = defaultdict(set)
    by_source_split: dict[str, set[str]] = defaultdict(set)
    by_source_ids: dict[str, list[str]] = defaultdict(list)
    response_ids = []
    task_model = Counter()
    task_split = Counter()
    empty_response = 0
    span_text_mismatch = 0
    span_out_of_range = 0
    spans_total = 0
    response_positive = Counter()
    response_positive_by_task_model = Counter()

    # Sentence projection tallies.
    n_sentences = 0
    n_positive_any = 0
    n_positive_half = 0
    n_positive_contained = 0
    n_positive_excluding_implicit = 0
    n_conflict_only = 0
    n_baseless_only = 0
    n_both_families = 0
    responses_with_zero_sentences = 0
    span_crosses_boundary = 0
    span_hits_no_sentence = 0
    span_multi_sentence = 0
    sentences_multi_span = 0
    sentences_partial_overlap = 0
    implicit_only_positive = 0
    quality_sentence = Counter()
    sentence_by_task = Counter()
    positive_by_task = Counter()
    sentence_by_model = Counter()
    positive_by_model = Counter()
    positive_by_task_model = Counter()
    sentences_by_task_model = Counter()
    cross_boundary_spans_by_task = Counter()
    spans_by_task = Counter()

    conflict_types = {"Evident Conflict", "Subtle Conflict"}
    baseless_types = {"Evident Baseless Info", "Subtle Baseless Info"}

    for row in responses:
        source_id = str(row.get("source_id"))
        model = str(row.get("model"))
        split = str(row.get("split"))
        task = task_by_source.get(source_id, "MISSING_SOURCE")
        text = row.get("response") or ""
        by_source_models[source_id].add(model)
        by_source_split[source_id].add(split)
        by_source_ids[source_id].append(str(row.get("id")))
        response_ids.append(str(row.get("id")))
        task_model[(task, model)] += 1
        task_split[(task, split)] += 1
        if not text.strip():
            empty_response += 1

        spans = []
        for span in row.get("labels") or []:
            spans_total += 1
            spans_by_task[task] += 1
            start = int(span.get("start", -1))
            end = int(span.get("end", -1))
            if start < 0 or end > len(text) or start >= end:
                span_out_of_range += 1
            else:
                snippet = text[start:end]
                annotated = span.get("text")
                if isinstance(annotated, str) and annotated != snippet:
                    span_text_mismatch += 1
            spans.append(span)

        has_span = any(str(s.get("label_type")) in HALLUCINATION_LABEL_TYPES for s in spans)
        response_positive[task] += int(has_span)
        response_positive_by_task_model[(task, model)] += int(has_span)

        units = sentence_spans(text)
        if not units:
            responses_with_zero_sentences += 1

        hit_counts = [0] * len(units)
        for span in spans:
            start = int(span.get("start", -1))
            end = int(span.get("end", -1))
            hits = [
                i
                for i, (s0, s1, _) in enumerate(units)
                if overlap(start, end, s0, s1)
            ]
            if len(hits) == 0:
                span_hits_no_sentence += 1
            elif len(hits) > 1:
                span_crosses_boundary += 1
                span_multi_sentence += 1
                cross_boundary_spans_by_task[task] += 1
            for i in hits:
                hit_counts[i] += 1

        for i, (s0, s1, _) in enumerate(units):
            n_sentences += 1
            sentence_by_task[task] += 1
            sentence_by_model[model] += 1
            sentences_by_task_model[(task, model)] += 1
            quality_sentence[str(row.get("quality"))] += 1
            overlapping = [
                s
                for s in spans
                if overlap(int(s.get("start", -1)), int(s.get("end", -1)), s0, s1)
                and str(s.get("label_type")) in HALLUCINATION_LABEL_TYPES
            ]
            if len(overlapping) > 1:
                sentences_multi_span += 1
            if not overlapping:
                continue
            n_positive_any += 1
            positive_by_task[task] += 1
            positive_by_model[model] += 1
            positive_by_task_model[(task, model)] += 1
            sent_len = max(s1 - s0, 1)
            covered = 0
            contained = False
            for span in overlapping:
                a = max(int(span["start"]), s0)
                b = min(int(span["end"]), s1)
                covered += max(0, b - a)
                if int(span["start"]) >= s0 and int(span["end"]) <= s1:
                    contained = True
                if not (int(span["start"]) >= s0 and int(span["end"]) <= s1):
                    sentences_partial_overlap += 1
                    break
            if covered / sent_len >= 0.5:
                n_positive_half += 1
            if contained or any(
                int(s["start"]) >= s0 and int(s["end"]) <= s1 for s in overlapping
            ):
                n_positive_contained += 1
            non_implicit = [s for s in overlapping if not s.get("implicit_true")]
            if non_implicit:
                n_positive_excluding_implicit += 1
            else:
                implicit_only_positive += 1
            types = {str(s.get("label_type")) for s in overlapping}
            has_c = bool(types & conflict_types)
            has_b = bool(types & baseless_types)
            if has_c and not has_b:
                n_conflict_only += 1
            elif has_b and not has_c:
                n_baseless_only += 1
            elif has_c and has_b:
                n_both_families += 1

    # Group leakage against the official split.
    source_split_conflict = sum(1 for splits_here in by_source_split.values() if len(splits_here) > 1)
    panel_sizes = Counter(len(v) for v in by_source_models.values())
    missing_source = sum(1 for sid in by_source_models if sid not in task_by_source)
    orphan_sources = sum(1 for sid in task_by_source if sid not in by_source_models)

    prompt_to_splits: dict[str, set[str]] = defaultdict(set)
    norm_prompt_to_splits: dict[str, set[str]] = defaultdict(set)
    content_to_splits: dict[str, set[str]] = defaultdict(set)
    content_to_sources: dict[str, set[str]] = defaultdict(set)
    prompt_to_sources: dict[str, set[str]] = defaultdict(set)
    norm_prompt_to_sources: dict[str, set[str]] = defaultdict(set)
    task_counts = Counter()
    empty_source_text = 0
    for row in sources:
        sid = str(row.get("source_id"))
        task = str(row.get("task_type"))
        task_counts[task] += 1
        splits_here = by_source_split.get(sid, {"NO_RESPONSE"})
        prompt = row.get("prompt") or ""
        text = source_text(row)
        if not text.strip():
            empty_source_text += 1
        prompt_to_splits[prompt].update(splits_here)
        norm_prompt_to_splits[norm(prompt)].update(splits_here)
        digest = hashlib.sha256(norm(text).encode("utf-8")).hexdigest()
        content_to_splits[digest].update(splits_here)
        content_to_sources[digest].add(sid)
        prompt_to_sources[prompt].add(sid)
        norm_prompt_to_sources[norm(prompt)].add(sid)

    def cross_split(mapping: dict[str, set[str]]) -> int:
        return sum(1 for parts in mapping.values() if "train" in parts and "test" in parts)

    duplicate_response_ids = len(response_ids) - len(set(response_ids))
    duplicate_source_ids = len(sources) - len({str(r.get("source_id")) for r in sources})

    def pack_counter(counter: Counter, limit: int = 30) -> dict:
        return {str(k): int(v) for k, v in counter.most_common(limit)}

    report = {
        "files": {
            "response_sha256": sha256_of(response_path),
            "source_sha256": sha256_of(source_path),
            "response_sha256_expected": FILES["response.jsonl"],
            "source_sha256_expected": FILES["source_info.jsonl"],
            "response_bytes": response_path.stat().st_size,
            "source_bytes": source_path.stat().st_size,
        },
        "n_responses": len(responses),
        "n_sources": len(sources),
        "response_key_patterns": pack_counter(response_keys),
        "source_key_patterns": pack_counter(source_keys),
        "label_key_patterns": pack_counter(label_keys),
        "label_types": pack_counter(label_types),
        "implicit_true": pack_counter(implicit_true),
        "due_to_null": pack_counter(due_to_null),
        "quality": pack_counter(quality),
        "temperature": pack_counter(temperatures),
        "models": pack_counter(models),
        "official_split": pack_counter(splits),
        "task_counts": pack_counter(task_counts),
        "task_model_responses": {f"{a}|{b}": int(v) for (a, b), v in sorted(task_model.items())},
        "task_split_responses": {f"{a}|{b}": int(v) for (a, b), v in sorted(task_split.items())},
        "response_with_any_hallucination_span_by_task": pack_counter(response_positive),
        "responses_per_task": {
            task: int(sum(v for (t, _), v in task_model.items() if t == task))
            for task in task_counts
        },
        "panel_size_counts": pack_counter(panel_sizes),
        "sources_whose_responses_have_mixed_official_splits": source_split_conflict,
        "responses_missing_source": missing_source,
        "sources_missing_responses": orphan_sources,
        "duplicate_response_ids": duplicate_response_ids,
        "duplicate_source_ids": duplicate_source_ids,
        "empty_responses": empty_response,
        "empty_source_text": empty_source_text,
        "spans_total": spans_total,
        "span_text_mismatch": span_text_mismatch,
        "span_out_of_range": span_out_of_range,
        "span_crosses_sentence": span_crosses_boundary,
        "span_hits_no_sentence": span_hits_no_sentence,
        "cross_boundary_spans_by_task": pack_counter(cross_boundary_spans_by_task),
        "spans_by_task": pack_counter(spans_by_task),
        "responses_with_zero_sentences": responses_with_zero_sentences,
        "n_sentences": n_sentences,
        "n_positive_any_overlap": n_positive_any,
        "n_positive_half_coverage": n_positive_half,
        "n_positive_span_contained_in_sentence": n_positive_contained,
        "n_positive_excluding_implicit_true": n_positive_excluding_implicit,
        "n_positive_implicit_true_only": implicit_only_positive,
        "n_conflict_only_sentences": n_conflict_only,
        "n_baseless_only_sentences": n_baseless_only,
        "n_both_families_sentences": n_both_families,
        "sentences_with_multiple_spans": sentences_multi_span,
        "sentences_by_task": pack_counter(sentence_by_task),
        "positive_sentences_by_task": pack_counter(positive_by_task),
        "sentences_by_model": pack_counter(sentence_by_model),
        "positive_sentences_by_model": pack_counter(positive_by_model),
        "sentences_by_task_model": {
            f"{a}|{b}": int(v) for (a, b), v in sorted(sentences_by_task_model.items())
        },
        "positive_sentences_by_task_model": {
            f"{a}|{b}": int(v) for (a, b), v in sorted(positive_by_task_model.items())
        },
        "quality_sentence_rows": pack_counter(quality_sentence),
        "exact_prompt_strings_in_both_official_splits": cross_split(prompt_to_splits),
        "normalized_prompts_in_both_official_splits": cross_split(norm_prompt_to_splits),
        "normalized_source_hashes_in_both_official_splits": cross_split(content_to_splits),
        "exact_prompts_shared_by_multiple_source_ids": sum(
            1 for ids in prompt_to_sources.values() if len(ids) > 1
        ),
        "normalized_prompts_shared_by_multiple_source_ids": sum(
            1 for ids in norm_prompt_to_sources.values() if len(ids) > 1
        ),
        "normalized_source_hashes_shared_by_multiple_source_ids": sum(
            1 for ids in content_to_sources.values() if len(ids) > 1
        ),
        "max_sources_per_normalized_source_hash": max(len(v) for v in content_to_sources.values()),
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "n_responses", "n_sources", "n_sentences", "n_positive_any_overlap",
        "files", "panel_size_counts", "official_split", "task_counts",
    )}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

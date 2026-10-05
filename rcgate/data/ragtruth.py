"""RAGTruth loader: the first real benchmark (milestone M5).

Why this benchmark. The proposal needs, per question, several *black-box* generators whose
answers can be compared, plus a claim-level hallucination label, plus evidence text. RAGTruth
is the only dataset found that ships all three without any API key:

* ``dataset/response.jsonl`` -- 17,790 responses: 2,965 source documents answered by exactly
  **six different LLMs** (gpt-4-0613, gpt-3.5-turbo-0613, mistral-7B-instruct, llama-2-7b/13b/70b-chat).
  Six real generators per question is what makes the cross-model signal family meaningful
  and what makes generator-conditioned gating testable at all.
* ``dataset/source_info.jsonl`` -- for every source the task type (QA / Data2txt / Summary),
  the reference text the model was *given*, and the prompt.
* ``labels`` on each response -- character spans the annotators marked as hallucinated, with
  the failure type (``Evident Conflict``, ``Subtle Conflict``, ``Evident Baseless Info``,
  ``Subtle Baseless Info``). These are human labels, not model judgements.

Licence: MIT, recorded in ``data/benchmarks/ragtruth.json`` together with the sha256 of each
downloaded file, so a rerun can prove it used the same bytes.

Two mapping decisions worth stating, because both are judgement calls:

1. **Claim = sentence of a response.** RAGTruth annotates spans, not sentence units, so a
   sentence is labelled hallucinated when it *overlaps* any annotated span. The alternative,
   taking only exact span matches, throws away a third of the annotations that run across a
   sentence boundary.
2. **The reference text is the evidence corpus, not an oracle.** RAGTruth answers were
   generated *from* ``source_info``, so BM25 over it is the same retrieval any deployment
   would do with the documents in hand. It is not gold knowledge handed to the detector:
   a hallucinated sentence usually looks perfectly retrievable, which is precisely the
   failure the evidence signals are supposed to catch.

The dataset's own ``split`` field (train/test) is deliberately ignored. Constraint C6 wants
grouped splits by ``question_id`` for every benchmark, so that one source's six generators
can never sit on both sides of a boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..config import Config
from ..paths import RAW_DIR
from .schema import signal_frame, validate

DATASET_NAME = "RAGTruth"
DATASET_LICENSE = "MIT"
DATASET_URL = "https://github.com/ParticleMedia/RAGTruth"
DATASET_CITATION = (
    "Niu et al. (2024), 'RAGTruth: A Hallucination Corpus for Developing Trustworthy "
    "Retrieval-Augmented Language Models', ACL 2024."
)

RAW_BASE = "https://raw.githubusercontent.com/ParticleMedia/RAGTruth/main/dataset"

#: sha256 of each file at the pinned revision. A mismatch aborts the build rather than
#: silently training on different bytes than the ones the report claims to describe.
FILES: dict[str, str] = {
    "response.jsonl": "e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073",
    "source_info.jsonl": "0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b",
}

#: Human annotation categories. Every one of them is a hallucination, so the binary label
#: is "this sentence overlaps an annotated span of any of these types".
HALLUCINATION_LABEL_TYPES = [
    "Evident Conflict",
    "Subtle Conflict",
    "Evident Baseless Info",
    "Subtle Baseless Info",
]

#: Ordered generator roster. Position in this list is the ``generator_id`` in the signal
#: table, so it must stay stable across runs; appending is safe, reordering is not.
DEFAULT_ROSTER = [
    "gpt-4-0613",
    "gpt-3.5-turbo-0613",
    "mistral-7B-instruct",
    "llama-2-7b-chat",
    "llama-2-13b-chat",
    "llama-2-70b-chat",
]

_SENT_BOUNDARY = re.compile(r"(?<=[.!?])[\"')\]]*\s+")


# -- download ------------------------------------------------------------------


def sha256_of(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(raw_dir: str | Path | None = None, force: bool = False) -> dict[str, Path]:
    """Download the two JSONL files if absent, verifying each against the pinned sha256."""
    root = Path(raw_dir or (RAW_DIR / "ragtruth"))
    root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    for name, expected in FILES.items():
        path = root / name
        if path.exists() and not force:
            actual = sha256_of(path)
            if actual != expected:
                raise ValueError(
                    f"{path} has sha256 {actual[:12]}, expected {expected[:12]}; "
                    "delete it or pass force=True to re-download"
                )
        else:
            url = f"{RAW_BASE}/{name}"
            with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
                payload = response.read()
            path.write_bytes(payload)
            actual = hashlib.sha256(payload).hexdigest()
            if actual != expected:
                raise ValueError(f"{name} downloaded with sha256 {actual[:12]}, expected {expected[:12]}")
        paths[name] = path
    return paths


# -- parsing -------------------------------------------------------------------


def sentence_spans(text: str) -> list[tuple[int, int, str]]:
    """Split ``text`` into ``(start, end, sentence)`` with offsets into the original.

    Offsets are needed because the hallucination annotations are character spans; a
    sentence has to be matched against them positionally.
    """
    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in _SENT_BOUNDARY.finditer(text or ""):
        spans.extend(_trim(text, start, match.end()))
        start = match.end()
    spans.extend(_trim(text, start, len(text)))
    return spans


def _trim(text: str, start: int, end: int) -> list[tuple[int, int, str]]:
    chunk = text[start:end]
    stripped = chunk.strip()
    if not stripped:
        return []
    offset = start + len(chunk) - len(chunk.lstrip())
    return [(offset, offset + len(stripped), stripped)]


@dataclass
class Claim:
    """One sentence of one response, with its label and provenance."""

    response_id: str
    source_id: str
    model: str
    generator_id: int
    index: int
    start: int
    end: int
    text: str
    label: int
    label_types: list[str] = field(default_factory=list)
    task_type: str = ""
    quality: str = ""
    #: How many sentences this response had in total, so a truncated slice still knows.
    total: int = 0


def claims_from_response(
    response: dict,
    generator_id: int,
    label_types: list[str] | None = None,
) -> list[Claim]:
    """Turn one annotated response into labelled sentences.

    A sentence is labelled 1 when it overlaps any annotated span whose ``label_type`` is in
    ``label_types``. Overlap is one-directional on purpose: a span may cover only part of a
    sentence, and part of a hallucinated sentence is still a hallucinated sentence here.
    """
    wanted = set(label_types or HALLUCINATION_LABEL_TYPES)
    spans = [
        span
        for span in response.get("labels", [])
        if str(span.get("label_type")) in wanted
    ]

    claims: list[Claim] = []
    for index, (start, end, text) in enumerate(sentence_spans(response.get("response", ""))):
        hits = [s for s in spans if int(s["start"]) < end and int(s["end"]) > start]
        claims.append(
            Claim(
                response_id=str(response.get("id", "")),
                source_id=str(response.get("source_id", "")),
                model=str(response.get("model", "")),
                generator_id=generator_id,
                index=index,
                start=start,
                end=end,
                text=text,
                label=int(bool(hits)),
                label_types=sorted({str(s.get("label_type")) for s in hits}),
                quality=str(response.get("quality", "")),
            )
        )
    for claim in claims:
        claim.total = len(claims)
    return claims


def round_robin_claims(responses: dict[int, dict], prompt: str, cap: int | None):
    """Yield this source's claims generator by generator, sentence by sentence.

    Walking generators in ascending id and sentences in order inside each generator would
    hand the whole first generator's answer to the slice before the second generator gets a
    word in. The round-robin keeps all six generators represented in every source, and
    ``cap`` bounds how many sentences one source may contribute -- without it a 200-claim
    slice was drawn from six sources, and a question-grouped split over six questions is
    not an evaluation.
    """
    from ..claims.dealias import dealias_answer

    per_generator: list[list[tuple[Claim, object]]] = []
    for gid in sorted(responses):
        claims = claims_from_response(responses[gid], gid)
        dealt = dealias_answer(str(responses[gid].get("response", "")), question=prompt)
        per_generator.append(list(zip(claims, dealt, strict=False)))

    emitted = 0
    depth = max((len(items) for items in per_generator), default=0)
    for index in range(depth):
        for items in per_generator:
            if index >= len(items):
                continue
            if cap is not None and emitted >= cap:
                return
            emitted += 1
            yield items[index]


def load_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


# -- slice ---------------------------------------------------------------------


@dataclass
class Slice:
    """A claim frame plus the cross-model material the signals need."""

    frame: object
    answers_by_question: dict[str, dict[int, str]]
    roster: dict[str, int]
    stats: dict


def interleave_by_task(usable: dict[str, dict], sources: dict[str, dict]) -> list[str]:
    """Order source ids round-robin across task types, sorted within each type.

    Walking sources in plain ``source_id`` order returned 200 Summary sentences and no QA at
    all, because the id ranges are not interleaved. A slice that is one task type is not a
    representative slice, and QA and Summary carry different hallucination rates.
    """
    by_task: dict[str, list[str]] = defaultdict(list)
    for source_id in sorted(usable):
        by_task[str(sources.get(source_id, {}).get("task_type", ""))].append(source_id)

    ordered: list[str] = []
    cursors = dict.fromkeys(by_task, 0)
    while len(ordered) < sum(len(ids) for ids in by_task.values()):
        progressed = False
        for task in sorted(by_task):
            cursor = cursors[task]
            if cursor < len(by_task[task]):
                ordered.append(by_task[task][cursor])
                cursors[task] = cursor + 1
                progressed = True
        if not progressed:
            break
    return ordered


def build_slice(
    cfg: Config,
    seed: int = 0,
    raw_dir: str | Path | None = None,
    claim_texts: list[str] | None = None,
) -> Slice:
    """Load RAGTruth and build the claim frame for one run.

    Selection is deterministic given ``seed``: sources are visited in sorted ``source_id``
    order, keeping only those with at least ``min_generators`` responses from the roster,
    and the walk stops at ``n_claims`` claims so a 200-claim slice is actually 200 claims
    rather than 200 sources' worth.

    ``claim_texts`` is the test seam: pass it and the raw files are never opened.
    """
    from ..claims.claim_type import classify_frame

    roster_models = [str(m) for m in cfg.get("data.roster", DEFAULT_ROSTER)]
    roster = {model: index for index, model in enumerate(roster_models)}
    task_types = {str(t) for t in cfg.get("data.task_types", ["QA", "Summary"])}
    min_generators = int(cfg.get("data.min_generators", 3))
    n_claims = int(cfg.get("data.n_claims", 200))
    claims_per_source = cfg.get("data.claims_per_source", None)
    claims_per_source = int(claims_per_source) if claims_per_source else len(roster)

    paths = fetch(raw_dir or cfg.get("data.raw_dir", None))
    responses = claim_texts if claim_texts is not None else load_jsonl(paths["response.jsonl"])
    sources = {str(s["source_id"]): s for s in load_jsonl(paths["source_info.jsonl"])}

    # -- group responses by source, keeping only roster models
    by_source: dict[str, dict[int, dict]] = defaultdict(dict)
    for response in responses:
        model = str(response.get("model", ""))
        if model not in roster:
            continue
        source_id = str(response.get("source_id", ""))
        by_source[source_id][roster[model]] = response

    usable = {
        sid: gens
        for sid, gens in by_source.items()
        if len(gens) >= min_generators and str(sources.get(sid, {}).get("task_type", "")) in task_types
    }

    rows: list[dict] = []
    answers: dict[str, dict[int, str]] = {}
    stats = {
        "n_sources_available": len(by_source),
        "n_sources_usable": len(usable),
        "n_sources_written": 0,
        "claims_per_source": claims_per_source,
        "n_claims_written": 0,
        "n_hallucinated": 0,
        "dealias_changed": 0,
        "task_types": {},
        "label_types": {},
        "per_generator": {},
    }

    order = interleave_by_task(usable, sources)
    if seed:
        # A different seed sees a different slice, without touching the group split.
        offset = seed % max(len(order), 1)
        order = order[offset:] + order[:offset]

    for source_id in order:
        if len(rows) >= n_claims:
            break
        source = sources.get(source_id, {})
        context = str(source.get("source_info", "") or "")
        prompt = str(source.get("prompt", "") or "")
        task_type = str(source.get("task_type", ""))
        answers[source_id] = {
            gid: str(resp.get("response", "")) for gid, resp in usable[source_id].items()
        }
        stats["n_sources_written"] += 1

        for claim, dealt in round_robin_claims(usable[source_id], prompt, claims_per_source):
            if len(rows) >= n_claims:
                break
            stats["dealias_changed"] += int(dealt.n_changed > 0)
            rows.append(
                {
                    "question_id": source_id,
                    "claim_id": f"{claim.response_id}#{claim.index}",
                    "claim_text": dealt.text,
                    "benchmark": DATASET_NAME.lower(),
                    "context": context,
                    "generator_id": claim.generator_id,
                    "label": claim.label,
                    "source": str(source.get("source", "")),
                    "task_type": task_type,
                    "source_model": claim.model,
                    "label_types": ",".join(claim.label_types),
                    "response_quality": claim.quality,
                    "n_claims_in_answer": claim.total,
                }
            )

    frame = classify_frame(pd.DataFrame(rows))

    stats["n_claims_written"] = len(frame)
    stats["n_hallucinated"] = int(frame["label"].sum()) if len(frame) else 0
    stats["positive_rate"] = round(stats["n_hallucinated"] / max(len(frame), 1), 4)
    for key, column in (("task_types", "task_type"), ("per_generator", "source_model")):
        if len(frame):
            stats[key] = {str(k): int(v) for k, v in frame[column].value_counts().items()}
    if len(frame):
        counts: dict[str, int] = defaultdict(int)
        for value in frame["label_types"]:
            for name in str(value).split(","):
                if name:
                    counts[name] += 1
        stats["label_types"] = dict(sorted(counts.items()))
    return Slice(frame=frame, answers_by_question=answers, roster=roster, stats=stats)


def schema_record(slice_stats: dict | None = None) -> dict:
    """Machine-readable provenance: licence, hashes, and the column mapping used here."""
    return {
        "benchmark": DATASET_NAME,
        "url": DATASET_URL,
        "license": DATASET_LICENSE,
        "citation": DATASET_CITATION,
        "files": [{"name": name, "sha256": digest} for name, digest in FILES.items()],
        "label_schema": {
            "source": "human span annotation on dataset/response.jsonl",
            "label_types": HALLUCINATION_LABEL_TYPES,
            "mapping": "label = 1 when the sentence overlaps any annotated span of any type",
            "sentence_split": "regex (?<=[.!?])[\"')\\]]*\\s+, offsets kept for span overlap",
        },
        "claim_unit": "one sentence of one model response",
        "generator_roster": DEFAULT_ROSTER,
        "columns": {
            "question_id": "source_id from dataset/source_info.jsonl",
            "claim_id": f"<response id>#<sentence index>, e.g. {123}#2",
            "claim_text": "sentence text after pronoun de-aliasing",
            "benchmark": "constant 'ragtruth'",
            "claim_type": "rule-based, rcgate.claims.claim_type",
            "generator_id": "index of the responding model in the roster above",
            "label": "1 = sentence overlaps a hallucination annotation, else 0",
            "context": "source_info, the text the responding model was given",
            "task_type": "QA | Data2txt | Summary",
        },
        "split_policy": "grouped by question_id by this repo; the dataset's own split field is ignored",
        "slice": slice_stats or {},
    }


def write_schema_record(path: str | Path, slice_stats: dict | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema_record(slice_stats), indent=2) + "\n", encoding="utf-8")
    return path


def save(df, path: str | Path) -> Path:
    """Validate against the data contract, then write the parquet signal table."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    validate(df).raise_if_failed()
    df.to_parquet(path, index=False)
    return path


def contract_frame(rows: list[dict]):
    """Canonical column order and dtypes, for callers that build rows by hand."""
    return signal_frame(rows)

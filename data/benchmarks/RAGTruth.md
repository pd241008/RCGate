# RAGTruth

Benchmark record for milestone M5. The machine-readable twin, `ragtruth.json`, is regenerated
by every build from `rcgate/data/ragtruth.py`; this file is the human explanation of the two
decisions that file encodes.

## Provenance

- **Paper**: Niu et al. (2024), *RAGTruth: A Hallucination Corpus for Developing Trustworthy
  Retrieval-Augmented Language Models*, ACL 2024.
- **Repository**: <https://github.com/ParticleMedia/RAGTruth>
- **Licence**: MIT (verified against the repository `LICENSE`).
- **Citation**: if any number from this benchmark appears in the write-up, this citation has
  to appear with it.

## Files, pinned

| file | sha256 | what it holds |
|---|---|---|
| `dataset/response.jsonl` | `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073` | 17,790 responses: `id`, `source_id`, `model`, `labels`, `split`, `quality`, `response` |
| `dataset/source_info.jsonl` | `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b` | 2,965 sources: `source_id`, `task_type`, `source`, `source_info`, `prompt` |

Both are downloaded by `rcgate.data.ragtruth.fetch` into `data/raw/ragtruth/` (gitignored) and
verified before a single row is parsed. A hash mismatch aborts the build rather than training
on bytes the report does not describe.

## Generators

All six LLMs in the dataset answer the same source document, which is what makes the
cross-model signal family and generator-conditioned gating meaningful. Position in this list is
the `generator_id` in the signal table; reordering it would silently change every id.

| id | model | role |
|---:|---|---|
| 0 | `gpt-4-0613` | strongest |
| 1 | `gpt-3.5-turbo-0613` | |
| 2 | `mistral-7B-instruct` | |
| 3 | `llama-2-7b-chat` | weakest |
| 4 | `llama-2-13b-chat` | |
| 5 | `llama-2-70b-chat` | |

Responses are treated as black boxes (constraint C1): only the text is read, no logits, no
hidden states, no model internals.

## Label schema and its mapping to this repo

RAGTruth annotates **character spans** with one of four human failure types:

| label type | meaning |
|---|---|
| `Evident Conflict` | contradicts the source |
| `Subtle Conflict` | conflicts in a way that needs inference |
| `Evident Baseless Info` | unsupported and plainly new |
| `Subtle Baseless Info` | unsupported, inserted plausibly |

Mapping used here: **claim unit = one sentence of one response**, and `label = 1` when that
sentence *overlaps* any annotated span of any of the four types. Overlap is one-directional on
purpose: an annotation may cover only part of a sentence, and part of a hallucinated sentence
is still a hallucinated sentence. Requiring an exact match would discard a third of the
annotations that cross a sentence boundary.

Sentences come from `re.split(r'(?<=[.!?])["\')\]]*\s+')` with offsets kept, so the match
against the spans is positional rather than textual.

## Splits

The dataset ships its own `split` field (train/test). **It is deliberately ignored**: constraint
C6 wants grouped splits by `question_id` for every benchmark, so one source document and its
six generators can never sit on both sides of a boundary. `rcgate/data/splits.py` does the
grouping.

## What the evidence signals are allowed to see

`source_info` is the text the responding model was *given*. Using it as the retrieval corpus is
the same retrieval any deployment performs with the documents already in hand, and it is what
RAGTruth's own annotation was made against. It is not gold knowledge handed to the detector: a
hallucinated sentence is usually perfectly retrievable, which is exactly the failure
`support`/`conflict` are supposed to expose.
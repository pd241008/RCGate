# RAGTruth schema, from the local files

**Date:** 23 October 2026.  
**Counts:** `audit_ragtruth_counts.py`, run with `.venv/bin/python`. Output: `audit_ragtruth_counts.json`. Raw files were read and not modified.

## Files

| File | Bytes | SHA-256 | Matches pinned hash in `rcgate/data/ragtruth.py` |
|---|---:|---|---|
| `data/raw/ragtruth/response.jsonl` | 21,458,735 | `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073` | Yes |
| `data/raw/ragtruth/source_info.jsonl` | 15,117,971 | `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b` | Yes |

Licence recorded by the repository benchmark note: MIT, checked there against the upstream `LICENSE`. This audit did not re-download the licence file. Citation for any number taken from these files: Niu et al., ACL 2024.

## Response records

17,790 rows. Every row has the same keys: `id`, `source_id`, `model`, `temperature`, `labels`, `split`, `quality`, `response`.

- `id` is unique.
- `response` is the generated text. None is empty.
- `split` is the official split: 15,090 train, 2,700 test.
- `model` is one of six strings, 2,965 rows each: `gpt-4-0613`, `gpt-3.5-turbo-0613`, `mistral-7B-instruct`, `llama-2-7b-chat`, `llama-2-13b-chat`, `llama-2-70b-chat`.
- `temperature` is the generation temperature. Values seen: 0.7 (10,089), 1.0 (3,601), 0.775 (1,610), 0.85 (1,478), 0.925 (1,012). It is generation metadata, not a label and not a grounding feature.
- `quality`: `good` 17,617, `incorrect_refusal` 144, `truncated` 29.

## Source records

2,965 rows. Every row has `source_id`, `task_type`, `source`, `source_info`, `prompt`. No duplicate `source_id`. No response points at a missing source, and no source lacks responses.

`source` is a domain tag, not the evidence text. The four values are `MARCO` (QA, 989), `Yelp` (Data2txt, 1,033), `CNN/DM` (Summary, 628), and `Recent News` (Summary, 315).

`source_info` is the evidence the generator was given:

- Summary: a string, 943 rows. It is not equal to `source`.
- QA: an object with `question` and `passages`, 989 rows.
- Data2txt: an object with `name`, `address`, `city`, `state`, `categories`, `hours`, `attributes`, `business_stars`, and `review_info`, 1,033 rows.

`prompt` is the instruction plus that evidence. Task counts: Data2txt 1,033, QA 989, Summary 943.

## Labels

14,289 spans. Every span has `start`, `end`, `text`, `label_type`, `due_to_null`, `implicit_true`, and `meta`.

| `label_type` | Spans |
|---|---:|
| Evident Baseless Info | 6,237 |
| Evident Conflict | 5,324 |
| Subtle Baseless Info | 2,527 |
| Subtle Conflict | 201 |

`implicit_true` is true on 1,928 spans and false on 12,361. `due_to_null` is true on 1,642 spans and false on 12,647. Every span's `start`/`end` falls inside the response, and `response[start:end]` equals the span's `text` on all 14,289 spans.

## Panel

All 2,965 sources have exactly six responses, one from each model. Each task has all six models. Official test is 150 sources per task (900 responses). Official train is the rest: Data2txt 883, QA 839, Summary 793 sources.

Response-level hallucination, meaning at least one span of the four types: Data2txt 4,254 / 6,198 (68.6%), QA 1,724 / 5,934 (29.1%), Summary 1,686 / 5,658 (29.8%).

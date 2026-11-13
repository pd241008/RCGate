# Sentence label projection

**Date:** 23 October 2026.  
The human annotation is a character span. The principal analysis uses a sentence projection. It is not a token-level evaluation.

## Splitter

Sentences are the offset units from `rcgate.data.ragtruth.sentence_spans`: split on `(?<=[.!?])["')\]]*\s+`, then strip each piece and keep the start and end in the original response. The audit imported that function. It did not reimplement a second splitter.

The full corpus yields **133,684 sentences**. No response produces zero sentences. Quality of the parent response, counted at sentence rows: good 132,934, truncated 592, incorrect_refusal 158.

## Principal label

A sentence is positive when its character range overlaps any span whose `label_type` is one of Evident Conflict, Subtle Conflict, Evident Baseless Info, or Subtle Baseless Info. Partial overlap counts. `implicit_true` spans count. This is the label already implemented in `claims_from_response`.

**14,670 / 133,684 sentences are positive (11.0%).**

| Task | Sentences | Positive | Rate |
|---|---:|---:|---:|
| Data2txt | 55,497 | 7,852 | 14.1% |
| QA | 46,592 | 4,754 | 10.2% |
| Summary | 31,595 | 2,064 | 6.5% |

| Model | Sentences | Positive | Rate |
|---|---:|---:|---:|
| mistral-7B-instruct | 21,290 | 3,553 | 16.7% |
| llama-2-7b-chat | 22,299 | 3,659 | 16.4% |
| llama-2-13b-chat | 23,778 | 3,640 | 15.3% |
| llama-2-70b-chat | 22,276 | 2,814 | 12.6% |
| gpt-3.5-turbo-0613 | 25,353 | 548 | 2.2% |
| gpt-4-0613 | 18,688 | 456 | 2.4% |

Official-test cells that are too small for a stable per-cell average precision are recorded in `SPLIT_SPECIFICATION.md`. The extreme case is GPT-4 QA test: 1 positive sentence.

Among the 14,670 principal positives: 4,584 overlap conflict types only, 9,525 overlap baseless types only, and 561 overlap both families. 1,472 positives overlap more than one span.

## Edge cases

- **Span crosses a sentence boundary.** 996 / 14,289 spans (7.0%) overlap more than one sentence. By task: QA 904 / 2,927 (30.9%), Summary 55 / 2,072, Data2txt 37 / 9,290. The principal rule labels every overlapped sentence positive. That spreads one annotation across two units, mostly in QA.
- **Span hits no sentence.** 0.
- **Span text or offsets disagree with the response.** 0 mismatches, 0 out-of-range spans.
- **Multiple spans in one sentence.** 1,472 positive sentences. The principal label stays binary. The span list is retained for description.
- **Zero spans.** The sentence is negative. 119,014 sentences.
- **Punctuation and whitespace.** The splitter keeps offsets after stripping the sentence. Matching uses those offsets, not a second copy of the string.
- **`implicit_true`.** 1,854 positive sentences overlap only spans with `implicit_true` true. 12,816 positives still remain if those sentences are set aside. An `implicit_true` span is unsupported by the context and marked true in the world. The principal label keeps it, because the question is the human span annotation. The sensitivity that drops implicit-true-only sentences is the faithfulness-versus-world-truth check.
- **`due_to_null`.** 1,642 spans. They stay inside the principal label. A sensitivity may report them separately. It is not a second primary.
- **Truncated or refused responses.** 173 responses are not `good`. Their sentences stay in the principal set. A predeclared sensitivity drops `quality != good`.

## Sensitivities, frozen as sensitivities

These are not alternatives to shop among after test scores exist.

| Projection | Positive sentences | Role |
|---|---:|---|
| Any overlap, all four types, including `implicit_true` | 14,670 | Principal |
| At least half the sentence's characters covered by spans | 6,383 | Sensitivity |
| At least one overlapped span lies entirely inside the sentence | 11,567 | Sensitivity. A sentence can still also touch a crossing span. |
| Drop sentences whose only hits are `implicit_true` | 12,816 | Sensitivity |
| Conflict-only / baseless-only / both, within principal positives | 4,584 / 9,525 / 561 | Descriptive slices of the principal positives |

Original spans stay in the data tables. Sentence metrics are never described as token metrics.

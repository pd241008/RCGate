# Data and split feasibility

**Date:** 23 October 2026.  
No new split was run. Counts below are taken from `data/benchmarks/RAGTruth.md`, `rcgate/data/ragtruth.py`, and the final research report's Stage 10 inventory. They were not recomputed in this audit.

## 1. RAGTruth as it exists on disk

| Item | Record |
|---|---|
| Paper | Niu, Wu, Zhu, Xu, Shum, Zhong, Song, and Zhang, ACL 2024, pages 10862–10878, as cited by Fadeeva et al. The detector tables in that paper were not re-read here. |
| Files | `response.jsonl`, 17,790 responses, sha256 `e4c2e4ac…e18073`. `source_info.jsonl`, 2,965 sources, sha256 `0dffc26e…2d578b`. |
| License | MIT, as recorded in the local benchmark note. |
| Panel | Six generators answer every source: GPT-4-0613, GPT-3.5-turbo-0613, Mistral-7B-instruct, Llama-2-7B-chat, Llama-2-13B-chat, Llama-2-70B-chat. |
| Tasks | QA, Summary, Data2txt. The local note's task field is `QA \| Data2txt \| Summary`. |
| Labels | Character spans: Evident Conflict, Subtle Conflict, Evident Baseless Info, Subtle Baseless Info. |
| Official split | `train` or `test` on the source. This repository ignores it and groups by `question_id`. |

The panel is what makes `agree`, `contra`, and `sem_dist` computable. A dataset without sibling responses to the same source cannot host those features without generating new answers. That generation is out of scope and would change the benchmark.

## 2. What the 800-row slice cannot support

Stage 8 used `ragtruth_corrected_integrity_v1_s0`: 800 first sentences, 134 questions, 57 positives. QA and Summary are mixed. Data-to-text is absent. `src_quality` is 0.9 on every row because every evidence source is benchmark context (`evidence.py` maps `SOURCE_CONTEXT` to 0.90). The arithmetic checker does not fire on the slice. Twenty-one of the slice's sources are official test sources, so those checkpoints are not an untouched official test.

**Inference:** the slice cannot answer generator shift, task shift, or full-response detection. Reusing its AUROC as a pilot of the new question would repeat a different experiment.

## 3. Full responses and word-level labels

A full-corpus study is possible in principle. The aggregation rule has to be frozen before fitting:

- Unit: one sentence of one response, offsets from the repository splitter `re.split(r'(?<=[.!?])["\')\]]*\s+')`, or a different splitter declared in advance.
- Positive: character overlap with any of the four span types, including `implicit_true` if that rule is kept. The final report says 904 of 2,927 QA spans (30.9%) cross a sentence boundary under this splitter, and about one fifth of positive QA sentences are implicit-true only. Those are label-definition choices, not model results.
- Response-level scores are a different task. Dubanowska et al. evaluate response-level labels and show that pooling tasks confounds them. Span overlap is closer to their guideline to localize the error. It is still a coarsening of the official spans.

Context faithfulness is the RAGTruth label. A sentence can be unsupported by the supplied passage and still be true in the world, which is the distinction FRANQ draws. This study must not report the label as factuality.

## 4. Splits that avoid leakage

**Source / query grouping.** `question_id` is the RAGTruth `source_id`. `grouped_split` and `group_stratified_split` keep a source on one side of the cut. Sibling generators of that source stay together. That is the right unit, because cross-model features read the sibling texts and evidence features read the shared context.

**The existing leave-one-generator function is not the protocol the proposal describes.** `leave_one_generator_out` in `rcgate/data/splits.py` first makes a question split, then deletes that generator from train and validation and rewrites its id to `UNK` (`-1`) on the test rows only. Other generators remain in the test frame. Held-out rows that fell in train or validation questions are dropped, not tested. Metrics that score the whole test frame therefore mix the unseen generator with seen generators. A valid generator-shift score uses only the relabeled rows, and the sibling texts may be used as unlabeled feature context because their questions are not in training. This function was not executed in this audit. Stage 8 did not use it.

**Generator embedding at test time.** `MetadataEncoder` keeps an extra row, `unk_index = n_generators`. Training uses `unk_dropout` 0.1. An unseen id can be mapped to that row. A4's one-hot generator indicator, as described in the final report, has seven columns on the RAGTruth roster (six models plus unknown). An unseen generator is representable only as that unknown column. It is not evidence that routing will transfer.

**Task holdout.** QA, Summary, and Data2txt use different sources, so a task holdout is source-disjoint if the split is by `task_type`. Dubanowska et al. show data-to-text's higher hallucination rate is enough for a naïve classifier to match a published detector on pooled AUC. Report each task. Do not put `task_type` in the gate. The current gate does not see `task_type`. It sees rule-based `claim_type` in {numeric, entity, extractive, abstractive} (`schema.py`). That is not a task id, and it can still correlate with task. Under task holdout, claim-type embeddings fit on the other tasks are an inductive bias, not a leak of the test source. They should be ablated.

**Thresholds.** Bakman et al. show that a threshold fit on one distribution fails on another. Fit thresholds only inside the training groups' validation slice. Do not reuse a Stage 8 threshold.

**What still leaks if ignored.** Scoring all six generators after training on five, while the same source's context was in training, lets the evidence encoder see the document before the test generator is scored. The current LOGO function avoids that by splitting questions first. A protocol that holds out a generator across all sources, leaving the other five on those sources in training, does not.

## 5. Other datasets

| Dataset | Can it host the current signals? | Label compatibility | Blocker |
|---|---|---|---|
| Full RAGTruth | Yes, if sibling responses stay available as features and sources are grouped. | Span overlap is definable. It is context faithfulness. | Must not use the 800-row slice or the official split and a custom split at once. `src_quality` does not vary for context evidence. |
| TRIVIA+ | No, not unchanged. Three models and no documented six-way panel on each source. | Sentence faithfulness, then a response bit. Four labels, not four span types. | CC BY-NC-ND 4.0 on the Amazon release page. Long context changes the NLI truncation used here (`max_length` 256 in the cross-encoder). |
| FRANQ long-form set | No. 76 questions, one RAG pipeline per model, not the six-model panel. | Factuality and faithfulness are separate. Collapsing them is the error FRANQ is written to avoid. | Too small for generator, task, and source holdouts. Use as a comparator paper, not as a second training set. |
| HaluEval, as used by HALT-RAG | No panel of the RAGTruth kind. | Task labels differ. | Would test NLI fusion only. |

## 6. Feasibility judgment

Full RAGTruth can support a credible **evaluation of the existing external features** if the sentence rule, the positive span rule, source grouping, per-task reporting, and a corrected generator holdout are fixed before fitting. It cannot support that evaluation through the 800-row slice, a pooled AUC, or the current `leave_one_generator_out` test frame scored as a whole.

TRIVIA+ and FRANQ's set do not preserve the outcome and the feature definition together. A second dataset is not available without a redesign.

`src_quality` and the arithmetic checker cannot be part of a success claim on this corpus. They do not vary in the way the feature comment suggests once the evidence is the benchmark context.

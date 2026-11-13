# Feature availability

**Date:** 23 October 2026.  
No signal was recomputed. No model was loaded.

## What the code can compute on a full sentence

| Feature | Code | Usable on all 133,684 sentences | Uses labels or the split name |
|---|---|---|---|
| `support`, `conflict` | `rcgate/signals/evidence.py` | Yes, from the target sentence and `source_info`, after a local NLI call | No |
| `src_quality` | same file | The function returns 0.90 for every benchmark context. On this corpus it does not vary unless the domain tag is smuggled in. | The constant itself does not use labels. Using the domain tag would identify the task. |
| `agree`, `contra`, `sem_dist` | `rcgate/signals/cross_model.py` | Yes, from the target sentence and the other responses' text on the same evidence. Needs local NLI and `all-MiniLM-L6-v2`. | No, if the other responses contribute text only |
| Lexical overlap with evidence | Not a stored column. BM25 tokenization in `evidence.py` can supply it. | Yes, without a neural model | No |
| `claim_type` | `rcgate/claims/claim_type.py`, called from `build_slice` | Can be recomputed from text | Not inspected as label-free in this audit. It is not part of the frozen primary set. |
| Generator id, task id, temperature, quality | Present on the raw rows | Yes | They are metadata. Quality is not a gold span, but it is not a grounding or peer feature. |

## What is only the old slice

`build_slice` defaults to `n_claims` 200 and task types QA and Summary. The Stage 8 numbers in the shift audit are a later 800-sentence, first-sentence slice with question-grouped refits. Those tables are not a full-corpus feature matrix. This audit found no full-corpus signal table under `data/`.

Historical result directories stay untouched. Their scores are not features and are not reused as this study's test metrics.

## Local model assets, names only

Already cached, so this protocol does not require a download:

- `cross-encoder/nli-deberta-v3-small`, revision `fa2804872c3b4bd748f38c0185cc85775361e735`. This is `DEFAULT_NLI_MODEL` in `rcgate/signals/nli.py`.
- `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

A missing or hash-mismatched weight file fails the run. Lexical overlap is a separate baseline. It is never reported as NLI.

## Leakage rules for the feature job

1. Peer agreement reads unlabeled `response` text from other models on the same evidence hash. It never reads peer spans, peer sentence labels, or `implicit_true`.
2. Grounding reads the target sentence and `source_info` only.
3. The primary scorer does not receive `model`, `task_type`, `temperature`, `quality`, `split`, the domain tag, or `src_quality`.
4. Fitting, calibration, and threshold choice use official-train groups only.

## Scale, without running it

A frozen call pattern of three evidence NLI calls plus one call per peer, at five peers, is about eight calls per sentence. Across 133,684 sentences that is on the order of one million forward passes of the small cached NLI model, before caching repeated premises. That is local compute, not a paid API. It is large enough that the implementation prompt must cache by premise hash and must not shrink the official test set after seeing scores.

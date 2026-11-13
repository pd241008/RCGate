# Prompt 02 — Audit full RAGTruth data and leakage risks

Consume the outputs of Prompt 01. The research direction is fixed. This stage is **read-only data feasibility**, not model scoring.

## Tasks

1. Inspect the official locally present RAGTruth `response.jsonl`, `source_info.jsonl`, data README and license/terms. Confirm actual keys and relationships from sample records instead of assuming them. Do not modify raw files.
2. Verify how `source_id`, query/prompt, generator/model, task type, official split, response text, character-span labels, annotation categories, truncation/refusal flags and context are represented. Document missingness and duplicate/near-duplicate source instances.
3. Explain exactly how a response span becomes a sentence label. Test edge cases: span crossing sentence boundary, punctuation, multiple spans, zero span, whitespace/unicode offsets, implicit-true spans, truncated or low-quality responses. Preserve word/span labels and provide a deterministic sentence-label projection for the principal analysis; record alternative projections for sensitivity analysis. Never call sentence-level evaluation “token-level”.
4. Determine the correct group key(s). Do not assume `question_id` alone is sufficient. Keep all responses generated from the same source/query together for source-disjoint evaluation, and check overlap across official split, source IDs, prompt strings, normalized prompt strings and source content hashes.
5. Confirm the six-generator/source panel: how many sources have all six responses, which generators occur by task, balance of labels, and missingness by source/model/task. Produce counts from the actual files and scripts to reproduce them.
6. Inspect existing feature code and historical signal tables. Identify which signal features can be recomputed on all full responses/sentences, which only exist for the old 800-row first-sentence slice, and which features risk using labels or split metadata.
7. Specify feature leakage rules: peer agreement may use only the *unlabelled generated text* from other responses to the same source/query; it must never use peer hallucination labels. Grounding features may use target sentence and retrieved evidence, never gold hallucination spans.
8. Create `DATA_SCHEMA.md`, `LABEL_MAPPING.md`, `GROUP_LEAKAGE_AUDIT.md`, and `FEATURE_AVAILABILITY.md` under `research/rcgate_conditional_consensus/`.
9. Provide a reproducible read-only script or exact commands to reproduce counts only if needed; do not yet implement the production feature pipeline or create model outputs.

## Stop conditions

If the full data does not permit source/query grouping, a coherent label projection, or enough coverage for the proposed comparisons, document the problem and stop before writing split or training code. Do not silently weaken the evaluation design.

## Safety and completion

No model inference, model downloads, external API, corpus scraping, modifications to raw files or historical results. Only new audit files under `research/rcgate_conditional_consensus/`. Report counts, caveats, changed files and Git status. Wait for Prompt 03.

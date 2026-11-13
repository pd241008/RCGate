# Prompt 05 — Reconstruct full-response and sentence-level labels

Use the frozen protocol and tested scaffold. This stage transforms the existing local RAGTruth data into an immutable, hashed derived table. It must not fit models or compute predictive features.

## Tasks

1. Read raw RAGTruth files read-only and produce an explicit data lineage map. Hash source files and record dataset version/official split. Verify terms/license from the official repository and document any constraints.
2. Implement deterministic response-to-sentence segmentation and span overlap labels according to the approved label mapping. Preserve original response text, original character offsets, original hallucination spans/types, task, source/query/group ids, target generator, official split, quality flags and all transformation provenance.
3. Preserve a raw-response-level table and a sentence-level table. Each sentence must have stable IDs; sentence text must be a substring of its original response where the segmentation tool supports exact offsets. If normalization changes offsets, keep raw offsets and normalized text separately.
4. Record how `implicit_true`, null-related labels, quality issues and truncated responses are handled. Do not discard cases without a predeclared reason. Produce an inclusion/exclusion flow table.
5. Verify source/query duplicate grouping and split assignment with assertions. Group every variant and every model response from one source/query together in the source-disjoint experiment. Do not leak any derived variant across partitions.
6. Generate no predictive feature values or model scores at this stage.
7. Write reproducible scripts and tests; write derived data and manifests only to the approved new directories.

## Acceptance checks

- Counts reconcile with raw JSONL counts, with every difference explained.
- Sentence span overlaps and labels match hand-checked examples.
- No response disappears silently.
- All group IDs and split assignments are present and stable.
- Raw input hashes and transformation versions are included.

## Deliverables

Code, tests, `DATA_RECONSTRUCTION_REPORT.md`, `LABEL_QA_REPORT.md`, and immutable derived outputs in the new output path. Report exact commands/counts, label balance by generator/task, group overlap assertions and Git status. Stop for human review before Prompt 06.

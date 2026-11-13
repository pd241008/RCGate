# RC-Gate — Cursor Research-to-Paper Prompt Pack v1.0

**Project name is fixed: RC-Gate. Research direction is fixed provisionally as a conditional value-and-cost study of peer-model answer agreement given direct evidence-grounding signals.** These prompts are not a license to invent a positive result, alter historical experiments, or claim novelty without support.

## Fixed research question

> For a target RAG-generated sentence, does agreement information derived from other model responses to the same source/query provide incremental predictive information about the target sentence's human-annotated hallucination span, beyond direct evidence-grounding signals; how does that increment vary by generator and task, and is it worth its additional compute/inference burden?

This is an **empirical evaluation study**, not a proposal for a new gating algorithm. The old source-dependence idea stays STOP. The old A7 gate remains a historical comparator only; do not build a new gate to make a novelty claim.

## Scientific rule

We aim to measure and demonstrate improvement if it exists. We cannot guarantee a positive result before the experiment. If peer agreement adds no robust value, report that honestly; do not alter test thresholds, data exclusions, or the primary metric after seeing test results to force a win.

## Execution order

Run **one prompt at a time**, in Cursor Agent mode, in the existing repository. Wait for Cursor to finish and inspect its summary, changed-file list, tests and Git status before using the next prompt. Each prompt is recursive in the practical sense: it uses the artifacts produced by earlier prompts and must not silently redo or overwrite previous stages.

1. `01_COMPETITOR_AUDIT.md`
2. `02_RAGTRUTH_DATA_AUDIT.md`
3. `03_FREEZE_EXPERIMENT_PROTOCOL.md`
4. `04_SAFE_SCAFFOLD_AND_SCHEMA.md`
5. `05_RECONSTRUCT_FULL_RESPONSE_LABELS.md`
6. `06_BUILD_FEATURE_PIPELINE.md`
7. `07_BASELINES_AND_SOURCE_GROUPED_RUN.md`
8. `08_HELDOUT_GENERATOR_AND_TASK_EVALUATION.md`
9. `09_ABLATIONS_CALIBRATION_AND_COST.md`
10. `10_STATISTICS_AND_PUBLICATION_FIGURES.md`
11. `11_RESULTS_LEDGER_AND_CLAIMS_AUDIT.md`
12. `12_SPRINGER_MANUSCRIPT_DRAFT.md`
13. `13_PROFESSOR_COMMENTS_AND_LATEX_AUDIT.md`
14. `14_REPRODUCIBILITY_AND_RELEASE_AUDIT.md`

If Cursor cannot access web search/full texts, report the limitation and do not fill it with guesswork. If a stage uncovers a severe data or validity blocker, pause for a decision before expensive runs; do not silently skip the stage.

## Repository safety defaults

- Start every prompt with `git status --short --branch`, current branch and HEAD.
- Preserve all existing untracked files, manuscripts and results. Never run `git clean`, `git reset`, `git checkout`, `git stash`, or bulk staging. Never run `git add .`, commit, or push.
- Keep original raw RAGTruth data read-only.
- Keep old `results/summary/` and old manuscript folders untouched.
- Place new code under a new isolated package such as `rcgate/conditional_consensus/` or `experiments/conditional_consensus/`, only after the design is frozen.
- Place newly derived data under `data/derived/rcgate_conditional_consensus/` and new outputs under `results/rcgate_conditional_consensus/`.
- Use a manifest with SHA-256 hashes, explicit data/model versions, software versions, prompts/configs if any, split hashes, random seeds and exact commands.
- Never use test labels for features, threshold setting, hyperparameter tuning, feature selection, or model selection.
- No new paid API or model download unless separately approved. Prefer existing local data and pinned local model assets. Model-load failure must fail closed; lexical fallback must never be represented as NLI.

## Required final paper standard

The paper must explain the target and practical meaning of every score. Separate evidence faithfulness from factual truth. Include a substantial related-work comparison table with title, year, authors, method/features and direct relevance. Define symbols on first use and include notation/glossary tables where useful. Put the dataset section immediately after related work. Explain every diagram label. Include numerical comparisons, uncertainty estimates, error analysis, ablations and legible original figures. Discuss A8 as unavailable/unevaluated if legacy variants are described because judge-output columns were not available. Use an official Springer Nature LaTeX template appropriate to the intended venue; do not hand-tune layout to evade template rules. Abstract must be one paragraph, no bold and no embedded paragraph breaks. Future work must be constructive and specific. Do not invent author details, funding, ethics approvals, data-access claims or declarations.

## What qualifies as a strong result

- The incremental peer-agreement comparison uses identical examples/splits and a predeclared primary metric.
- Confidence intervals and tests respect source/query grouping.
- Held-out generator and held-out task findings are reported separately; not merely pooled.
- There is a cost/latency/peer-count analysis.
- Claims do not exceed the data or study design.

A negative or mixed result is still a valid finding, but it may not support the originally desired “substantially better” claim. Never fabricate numbers, images, statistical significance, citations or code execution.

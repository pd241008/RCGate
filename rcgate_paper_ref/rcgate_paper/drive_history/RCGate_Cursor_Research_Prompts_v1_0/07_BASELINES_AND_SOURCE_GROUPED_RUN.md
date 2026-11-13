# Prompt 07 — Fit fair baselines on source/query-grouped splits

Only run after feature QA and the experiment protocol are approved. This is the first predictive model stage. Use only features created under Prompt 06 and split assignments frozen before fitting.

## Required models

At minimum compare on identical source/query-disjoint partitions:
1. Grounding-only logistic regression.
2. Peer-agreement-only logistic regression.
3. Combined grounding + peer-agreement logistic regression.
4. Grounding-only gradient boosting (the strong simple baseline family; match the existing A4 method where feasible).
5. Combined-feature gradient boosting.
6. Historical A7 gate only as a clearly labelled legacy comparator if it can be applied without changing its architecture; do not modify it to win and don't pretend its generator/task embeddings transfer to unknown generators.
7. Any additional closest published baseline that can be reproduced fairly under the fixed evidence inputs; otherwise label it an adaptation and keep out of headline claims.

Use nested or otherwise strictly separated training/validation/testing for hyperparameters and thresholds. The final test partition is frozen. Avoid overfitting feature selection on the test set. Record exact package versions, seeds and commands.

## Primary question

Does peer agreement add predictive value beyond grounding alone? The primary comparison must use identical sentences and paired predictions. Use the primary metric frozen in the protocol; do not switch primary metrics after looking at the result.

## Reporting

- Metrics pooled across sentence instances, with clustered confidence intervals at source/query group level.
- Performance by task and target generator, clearly distinguishing in-distribution generator from unseen generator tests reserved for Prompt 08.
- Label prevalence, confusion matrix, precision/recall, Average Precision, AUROC and threshold-dependent metrics.
- Record training/runtime costs and all model failures.
- If the peer features do not improve over grounding-only on the held-out source/query split, report it. Do not add features or change the split to force a win; improvements to the protocol must be versioned and must use a new untouched evaluation set.

## Deliverables

Scripted train/evaluate commands, saved model artifacts with hashes, raw predictions with stable record IDs, metrics JSON/CSV, per-group prediction file, and `SOURCE_GROUPED_BASELINE_REPORT.md` under the new results directory. Produce no paper claims yet. Run evaluation tests and report Git status; then wait for Prompt 08.

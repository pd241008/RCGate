# Prompt 08 — Held-out generator and held-out task evaluation

Use frozen feature definitions and model-selection decisions from Prompt 07. Do not redesign features based on held-out test results.

## Generator-held-out evaluation

1. Run leave-one-generator-out experiments for each eligible generator, with all responses for the same source/query assigned to one outer group partition. The held-out generator's labels must not enter fitting, threshold choice, feature selection or calibration.
2. Since RC-Gate's historical A7 learns generator identities, define exactly how A7 is handled. Do not fabricate an embedding for an unseen generator. Prefer baselines that do not need generator identity; show A7 only where its setup remains valid and explicitly label limitations.
3. Peer features for test examples may use other generators' unlabelled response text for the same source/query if permitted by the frozen protocol. No peer labels may be used. Document this as a test-time information assumption.
4. Report every held-out generator separately; then summarize macro performance with appropriate uncertainty. Do not present one pooled number as proof of universal transfer.

## Task-held-out evaluation

Run held-out task analyses only where training and test labels, source groups and generators permit a meaningful comparison. Specify whether this is (a) train on other tasks/test on held-out task, or (b) within-task evaluation. Never conflate the two. Report class prevalence and sample/group counts.

## Combined shift

If data permit, run a combined held-out-generator plus held-out-task stress test. Mark it secondary unless the protocol selected it as primary in advance.

## Leakage checks

Run assertions for source/query disjointness, normalized prompt overlap, source-content hashes, feature cache overlap, and any shared group identifiers. Record the actual split indices/hashes. Fail closed on any overlap.

## Deliverables

`HELDOUT_GENERATOR_REPORT.md`, `HELDOUT_TASK_REPORT.md`, split-specific raw predictions/metrics, and a leakage-audit report in the new experiment result directory. Do not tune on these results. Report failure patterns as seriously as gains; wait for Prompt 09.

# Prompt 03 — Freeze the conditional-consensus experiment protocol

Use the competitor audit and full-data audit. Do not reopen unrelated research directions. Draft a protocol for the fixed RC-Gate study, and do not inspect any newly computed test metrics while selecting its choices.

## Fixed scientific question

Does peer-model answer agreement provide incremental predictive information for hallucinated target-response sentences beyond target-sentence grounding against its retrieved evidence; does this incremental value transfer across generators/tasks; and what is its marginal computation/inference burden?

## Required protocol decisions

1. Define the estimand and unit of analysis. Likely unit: a target response sentence with a binary label derived deterministically from RAGTruth span annotation. Retain all original span-level outcomes for descriptive/sensitivity analyses. Explain limitations of the projection.
2. Predeclare a primary comparison: grounding-only features versus grounding-plus-peer-agreement features on identical test examples, using source/query-disjoint splits. Choose one primary metric after inspecting label prevalence, but before new model fitting; Average Precision may suit imbalance. Define exact denominator and macro/pooled handling.
3. Predeclare secondary outcomes: AUROC, precision/recall/F1 at calibration-selected threshold, Brier/log loss and calibration plots only if scores are probabilistic or explicitly calibrated, performance by generator/task, calibration/coverage or selective risk if justified, feature inference time, memory, peer count and marginal inference burden.
4. Specify data splits that respect source/query groups. Keep all responses from a source/query in one partition for the main source-disjoint experiment. Design a leave-one-generator-out protocol separately; prevent generator identity embeddings from pretending to generalize to unseen generators. Design held-out-task evaluations only where sample size/class balance supports interpretation. Report each axis separately before any combined stress test.
5. Decide how peer model text is converted into features at sentence level. Candidates include NLI entailment/contradiction between the target sentence and peer response sentences, semantic match features, fraction of peers with support/contradiction matches, and dispersion. Avoid unbounded feature fishing. Freeze a small, justified set before test runs. Features must be computed without peer labels.
6. Ensure all baseline methods see fair comparable inputs. Required baselines: grounding only; peer agreement only; combined features with logistic regression; combined features with gradient boosting; majority/mean/simple aggregation where meaningful; historical A4/A7 only with limitations noted; and the closest fair published comparators when reproducible. A new gate is not the contribution.
7. Define thresholds and tuning exclusively on training/validation/calibration groups. No test-based feature selection, threshold choice, or model choice.
8. Plan clustered uncertainty: bootstrap or paired resampling by source/query group, not individual sentences as independent. Define seeds and number of repeats based on feasible compute. Predefine multiple-comparison handling or label exploratory comparisons clearly.
9. Cost: distinguish (a) feature extraction latency using already-generated RAGTruth peers; (b) the operational cost of obtaining peers at deployment; and (c) NLI/embedding compute. Do not fabricate historical generation dollars. Report model-call counts, input/output tokens if available, per-peer marginal latency and explicit unknowns.
10. Define feasibility and failure criteria without arbitrary after-the-fact thresholds. Propose a minimum worthwhile effect, justify it against use-case costs/uncertainty, and freeze before final test. If no defensible minimum can be chosen, state that and use estimation with uncertainty rather than claiming superiority.

## Files

Create `EXPERIMENT_PROTOCOL_DRAFT.md`, `METRIC_DEFINITIONS.md`, `SPLIT_SPECIFICATION.md`, and `FEATURE_SPECIFICATION.md` under `research/rcgate_conditional_consensus/`. Add a run-freeze checklist. Document unresolved decisions instead of guessing.

## Gate

Do not train models or compute scored features. The protocol must be reviewed before implementation. Report whether the data audit supports the design, what must be frozen next, and Git status. Wait for Prompt 04.

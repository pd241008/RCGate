# Experiment protocol draft

**Frozen:** 23 October 2026.  
**Status:** draft for review. No model has been fit. No feature matrix has been scored.  
**Name:** RC-Gate. **Question:** the fixed conditional-consensus question below. Source-dependence stays stopped. A new gate is not the contribution.

## Question

Does peer-model answer agreement provide incremental predictive information for hallucinated target-response sentences beyond target-sentence grounding against its retrieved evidence; does that increment transfer across generators and tasks; and what is its marginal computation?

## Estimand

The unit is one sentence of one response, with the principal label in `LABEL_MAPPING.md`. Spans remain available for description and for the predeclared sensitivities.

The quantity of interest is the difference, on the same official-test sentences,

`Delta = AP(grounding + peer) - AP(grounding only)`

averaged across the three tasks with equal task weight. Average precision is defined in `METRIC_DEFINITIONS.md`. Uncertainty is a bootstrap over evidence-hash groups, paired so both scorers see the same groups.

This is an incremental-value estimand. It is not a claim that a new architecture has been invented.

## Why this design is the strong version of the question

The data audit supports it. The panel is complete: 2,965 sources, six responses each. The official split shares no evidence hash between train and test. Sentence labels are deterministic. Local NLI and embedding weights are already cached.

The design asks for the decision a reviewer can use: after a grounding score exists, how many of the other stored answers are worth scoring, on which tasks, and for which generators the test cell can support. That is the version of this study that can be a solid empirical paper if the intervals are stable. It does not become that paper by being written down.

## What a finished paper can support

This protocol does not assign a publication score.

- If the task-macro interval for `Delta` is tight and the peer-count curve tells the same story on the powered cells, the finished paper is the kind of careful evaluation that can reasonably be argued around **6/10** as a journal article.
- **7/10** is available only if that same direction also holds for the held-out-generator axis on cells with at least 30 official-test positives, and the two-peer curve, not only the five-peer curve, is what carries the result. One task, or only the full panel, is not that paper.
- **8/10 and 9/10 are outside this protocol.** They would require a contribution this design does not contain. The protocol must not be described as a new detector, and the manuscript must not be written so that it looks like one.

GPT-4 on official-test QA has one positive sentence. Several GPT task cells have fewer than 30. Those cells are reported as counts. They are not evidence of transfer, and they are not evidence against it.

## Primary comparison

Scorers, fit on official-train groups only:

1. Grounding features, L2 logistic regression.
2. The same grounding features plus the frozen peer features at k=5, L2 logistic regression.

Same sentences. Same splits. No generator identity, task identity, temperature, quality, domain tag, or `src_quality` in either scorer.

The headline is the task-macro `Delta`, with a source-grouped interval. A pooled-sentence `Delta` is secondary, because Data2txt holds 7,852 of 14,670 positive sentences.

## Predeclared decision rule

No minimum AP gain is declared as a substitute for the interval. A superiority sentence is allowed only for the single primary contrast, and only when its task-macro 95% interval lies entirely above zero.

Separately, and only as an operational reading: extra peer scoring is described as worth doing for a task when the task's own interval for k=2 versus k=0 lies entirely above zero. If it does not, the paper says the extra calls are not supported for that task. This rule can fail. It is not revised after the test numbers exist.

## Secondary outcomes

Listed in `METRIC_DEFINITIONS.md`: AUROC, F1 at a validation-chosen threshold, Brier score after validation calibration, per-task and per-generator tables, the k curve, and call counts. Exploratory comparisons are labeled exploratory. They do not replace the primary contrast.

## Baselines

All of these see the same test sentences.

- Task-rate: the training positive rate of the sentence's task, as a constant score within task.
- Lexical overlap of the sentence with evidence, with no neural model.
- Peer features only, logistic regression.
- Grounding only, logistic regression. This is the primary reference.
- Grounding plus peer, logistic regression. This is the primary challenger.
- Grounding plus peer, gradient boosting, as a nonlinearity check. It is not allowed to win a model-selection contest on the test set. If it disagrees with the logistic `Delta`, both are reported and the logistic contrast remains primary.
- A parameter-free score: the mean of max evidence entailment and mean peer entailment. No fitted weight.
- Historical A4 and A7: cited only as the old 800-sentence slice. They are not refit, and their AUROC is not a baseline on this label set.

Published detectors are not given numerical baselines unless the same sentences, the same split, and the same label are recomputed. GASP, Itkin, RLSeek, and the RAGTruth finetune used different units, samples, or training regimes. Their published scores stay in the related-work table.

## Features, splits, cost

Feature formulas are frozen in `FEATURE_SPECIFICATION.md`. Splits are frozen in `SPLIT_SPECIFICATION.md`.

Cost has three columns, and they are not mixed:

1. Measured wall time of feature extraction on the already stored responses.
2. The deployment burden of obtaining k extra model answers. RAGTruth does not record dollar cost or billed token counts. Those dollars are not invented. The paper reports k, character counts of the peer responses, and the known absence of a bill.
3. NLI and embedding call counts under the frozen call pattern.

## Fitting rules

Thresholds, class weights, and any probability calibration are chosen on the calibration groups inside official train. The official test labels are not used to choose features, k, the splitter, the label projection, the model class, or the threshold. The primary model class is already fixed as logistic regression. Gradient boosting is a check, not a candidate that can replace it after test.

Seeds: `20261023` for the train/calibration cut and the bootstrap. Gradient boosting also runs seeds `20261023` through `20261027`. Logistic regression is the solver default with `random_state=20261023`.

Bootstrap: 1,000 resamples of official-test evidence hashes, with replacement. Sentences travel with their hash. The task-macro AP is recomputed inside each resample. The interval is the 2.5 and 97.5 percentiles.

Multiple comparisons: one primary interval. Task intervals, generator intervals, k intervals, and label sensitivities are exploratory. They are not a family of claims that each "reached significance."

## Failure and stop rules

Stop before scoring if the cached NLI revision or the MiniLM revision does not match the hashes in `FEATURE_AVAILABILITY.md`.

Stop rather than drop official-test sources if the full test matrix is too large. A smaller corpus is a different protocol and needs a new freeze.

If a sensitivity reverses the sign of the primary `Delta`, the paper reports the reversal. It does not change the principal label.

## Run-freeze checklist

- [x] Competitor audit read. No new method claimed.
- [x] Raw hashes match the pinned RAGTruth files.
- [x] Principal label and sensitivities written before any score.
- [x] Group key is the evidence hash. Official split has no cross-split hash.
- [x] Primary metric, primary model class, and primary k=5 contrast written before any score.
- [x] Generator protocol does not use `leave_one_generator_out` as the shift result.
- [x] Sparse cells named, including GPT-4 QA test with 1 positive sentence.
- [x] Local model revisions named. No download in this stage.
- [ ] Human review of this draft before Prompt 04 builds code.
- [ ] Implementation reads this file and does not retune it from test output.

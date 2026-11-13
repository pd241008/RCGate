# RC-Gate design options

**Date:** 23 October 2026.  
These options are readings of the code and the papers. None is a recommendation to implement a gate. The decision file selects the evaluation option and rejects a new architecture.

## How the current gate works

From `rcgate/models/rcgate.py` and `gate.py`:

- Metadata vector: claim-type embedding (4) concatenated with generator embedding (4). Generator table has `n_generators + 1` rows. The extra row is unknown.
- Gate: linear 8→16, ReLU, linear 16→2, softmax with fixed temperature 1. It does not receive the six signals unless `see_signals_in_gate` is set. That flag is false for A7. A unit of this design is that changing the signals does not change the weights.
- Experts: each is linear 3→1. Cross-model expert reads `agree`, `contra`, `sem_dist`. Evidence expert reads `support`, `src_quality`, `conflict`.
- Fusion: weights multiply logits, then a linear head maps the pair to one logit. Training is binary cross-entropy. Ten percent of generator ids are replaced by the unknown row during training.
- A5 drops the generator embedding. A6 drops the claim-type embedding. A3 is one scalar blend for every row. A0 is logistic regression on the six signals. A4 is gradient boosting on the six signals plus claim-type and generator indicators.
- Label: 1 if the sentence's character span overlaps any RAGTruth hallucination span.
- Stage 8, from the final research report, not recomputed: mean AUROC 0.6280 (A0), 0.6839 (A4), 0.5717 (A7). Mean paired A7 minus A4 is −0.1122. The slice is 800 first sentences.

`agree` is the fraction of other generators whose text entails the sentence. `contra` is the max contradiction probability. `sem_dist` is one minus the mean best-sentence cosine similarity. Evidence NLI is max or mean entailment and max contradiction against BM25 sentences of the supplied context. On RAGTruth, `src_quality` is the constant 0.90 for benchmark context.

Claim type is a rule label in {numeric, entity, extractive, abstractive}. It is not the RAGTruth task in {QA, Summary, Data2txt}.

## Option 1 — Keep A7 and retrain on the full corpus

The gate still routes on claim type and generator id. An unseen generator can be mapped to the unknown row. That tests cold start of an identity embedding. It does not test reliability-conditioned routing. Stage 8 already compares this gate with A4 on a slice and the gate loses. A full-corpus rerun could change the number. It would not create the distinction the proposal asks for, and a win that appears only when generator id is visible would be the metadata leakage A4 was built to expose.

**Reject as the research claim.**

## Option 2 — New gate on per-example diagnostics

The proposal lists agreement dispersion, NLI margins, evidence coverage, and disagreement between the two families. Those quantities are functions of the six signals and of how many sibling responses exist. A flat model that receives them is stacking, which Bakman et al. already show can be a linear model on normalized scores, and which FRANQ already compares with a hand-built conditional formula.

A gate that sees the diagnostics and outputs two mixture weights is a small mixture-of-experts head. The technical content beyond stacking is the constraint that each expert stays linear in its own family and the weight is a softmax of the diagnostics. That constraint is testable. It is the same kind of constraint A7 used for metadata, and A7 lost to a model without it. FRANQ's result says a hand-built condition can beat a tree when the condition matches the problem. It does not say a new softmax gate will beat gradient boosting on these features.

**Do not treat Option 2 as an unoccupied method.** It is an ablation: same features, constrained mixer versus flat mixer.

## Option 3 — Evaluation of the existing external features under shift

Use full responses. Freeze the sentence and span-overlap rules. Group by source. Report QA, Summary, and Data2txt separately, and compare with a naïve task-rate baseline of the kind Dubanowska et al. define for pooled scores. For generator shift, hold the generator out of training and score only that generator's rows on sources that were not in training. Sibling responses on those test sources may be feature context and may not be training labels. Drop `src_quality` and the arithmetic flag from any headline model, or show that removing them does not change the result.

Models: A0; a flat model on the six varying signals with no generator or task id; A4 with metadata, reported as a leakage diagnostic rather than as the scientific winner; A7 as a legacy control; one family at a time (A1, A2). Thresholds and calibration stay on the validation groups.

This option does not add a gate. It asks whether the black-box features Dubanowska et al. did not test survive the protocol they recommend. A negative answer is a completed result about this feature set. It is not, by itself, a new detector.

## Option 4 — Transfer to TRIVIA+ or FRANQ's label

TRIVIA+ has no six-model panel, a different sentence label, long contexts beyond the local NLI window, and a CC BY-NC-ND release. FRANQ's 76-question set uses factuality as the target and has no panel. Either transfer requires new responses or a redefined feature set, which is a different study. **Not feasible as a compatible external test of the current outcome.**

## What an unseen generator can and cannot do

The unknown embedding lets A7 emit weights for a generator id that was not in the table. The weights then depend on claim type and the unknown vector, not on that generator's reliability. Cross-model features still need other models' texts for the same source. If those texts do not exist, `cross_model.py` fills neutral values (0.5, 0.5, 1.0). A held-out-generator experiment that also removes the siblings is then an evidence-only experiment. The proposal's fusion question requires the panel. RAGTruth has the panel. A deployment with one model does not, and this audit does not assume one can be manufactured.

# Decision: PIVOT

**Date:** 23 October 2026.  
**Decision:** PIVOT. Do not develop a new reliability-conditioned gate. Keep the name RC-Gate. Leave the source-dependence STOP in place.

The candidate question was whether a lightweight gate over external cross-model agreement and evidence-grounding signals beats strong simple baselines under held-out generator, task, and source shifts. The gate is not a distinct method. The shift evaluation of the existing black-box features is the part the opened papers leave open, and it is an evaluation, not a new architecture.

## Answers to the nine questions

1. **Has comparable fusion already been published?** Not of these two families on this label. FRANQ fuses AlignScore with single-model uncertainty by a faithfulness weight, and compares that rule with XGBoost. HALT-RAG fuses two NLI models and lexical features in a calibrated classifier. Bakman et al. stack uncertainty scores. Finch-Zk and the CCUF abstract use cross-model agreement without this evidence expert. The local A7 fuses the two families and loses to A4.

2. **Has reliability-conditioned gating been tested against simple fusion under those three shifts?** No opened paper runs that exact test. FRANQ tests conditioning against stacking without those RAGTruth holdouts. Dubanowska et al. test the holdouts for internal detectors. The local Stage 8 test is question-grouped on 800 first sentences and is not those shifts.

3. **How is the setting different from the named lines of work?** Uncertainty ensembling (Bakman) uses one generator's scores and no retrieved-evidence NLI. Hidden-state probes (Han; Dubanowska) read activations. FRANQ's target is factuality, and unsupported-but-true text is not a hallucination there. Broad internal detectors fail RAGTruth OOD and can match a task-rate rule. RC-Gate's implemented system is black-box text, span overlap, and a metadata gate.

4. **Is there a technical distinction beyond stacking or mixture-of-experts?** The metadata-only constraint is a real constraint, and Stage 8 does not show that it helps. A gate on margins and disagreement is a mixture head on features a flat model can receive. Bakman et al. find a linear stack enough and a tree worse. FRANQ finds a hand-built condition can beat a tree on different features. Neither result licenses a new gate before the flat model on the same features is the baseline.

5. **Is full RAGTruth usable with word-level labels?** Yes, if the sentence rule and the overlap rule are frozen first, sources stay intact, and results are not pooled across tasks without a naïve task baseline. The 800-row first-sentence slice is not that experiment. Span overlap remains context faithfulness, not world truth. About 30.9% of QA spans cross a sentence under the current splitter, as previously counted in the final report.

6. **Can the splits be designed without leakage?** Source grouping already exists. Task holdout is source-disjoint because tasks use different sources. Generator holdout is valid only if that generator is absent from training and the test sources are absent from training. Sibling responses on a test source may be unlabeled feature context. `leave_one_generator_out` does not do this cleanly: it keeps other generators in the test frame and drops most of the held-out generator's rows. Scoring that whole frame is not a generator-shift result.

7. **Can another dataset preserve the outcome?** TRIVIA+ and FRANQ's long-form set do not. They lack the six-model panel, and their labels are not RAGTruth span overlap. TRIVIA+'s Amazon release states CC BY-NC-ND 4.0. They remain related benchmarks, not drop-in test sets.

8. **Strongest fair baseline.** A flat model on the varying signals, without generator id, task id, `src_quality`, or the arithmetic flag. Report A1 and A2 so a family cannot hide inside the fusion. Report A4 only as a metadata-leakage check. Report a per-task majority or task-rate rule so a pooled score cannot repeat Dubanowska et al.'s confound. FRANQ and HALT-RAG are not fair numerical baselines unless their inputs are rebuilt; do not cite their published scores on this label.

9. **What result would continue, and what result would reject the method?** Continue only an evaluation write-up if, on full responses, source-disjoint per-task tests, the flat external-signal model beats both single-family models and the task-rate rule by a margin fixed before test inspection, and the same direction holds for at least one generator whose sources were not in training. Reject a new gate if it does not beat that flat model on the same features and the same splits. Reject the feature set if the gains vanish once `src_quality` is removed, once first sentences are no longer the only unit, or once tasks are separated. A negative Stage 8-style result on the full protocol is a finding about this system. It is not a reason to add parameters.

## What is demonstrated, plausible, and unsupported

**Demonstrated.** Metadata-conditioned fusion of these families, on the reported slice, ranks below gradient boosting with the same metadata. Pooled RAGTruth detection can track task prevalence. Uncertainty-score ensembling and faithfulness-conditioned uncertainty are published. Hidden-state probes transfer across generators to a degree Han et al. measure. Factuality and faithfulness are different labels.

**Plausible, unmeasured.** The six external signals, with constants removed, may still rank span-overlap sentences under source-disjoint and per-task evaluation better than either family alone. That is a property of the features, not of a new gate.

**Not supported.** A novel reliability-conditioned architecture. A claim that long context, label noise, or the factuality/faithfulness split is RC-Gate's contribution. Use of Stage 8 as evidence about generator or task shift. Use of TRIVIA+ as a same-signal, same-label confirmation set.

## The pivoted question, if work continues

It is an evaluation question, and it is not authorized as implementation by this file:

On full RAGTruth responses, with sources held out together, tasks reported separately, and one generator held out of both training and threshold selection, do the existing black-box cross-model and evidence signals improve span-overlap detection over either family alone and over a task-rate rule, once non-informative features are removed?

The historical gate is a control, not the hypothesis. A new mixer is in scope only after that flat comparison is positive and a second, pre-registered comparison still favors the mixer. This audit does not expect that second comparison to be the project.

## What not to do

- Do not revive source-dependence modeling.
- Do not implement Option 2 from `RCGATE_DESIGN_OPTIONS.md` as the next step.
- Do not refit A7 on the 800-row slice and call it a shift result.
- Do not pool QA, Summary, and Data2txt into one headline AUC.
- Do not describe FRANQ, HALT-RAG, or Bakman et al. as if they had already run this RAGTruth protocol. They have not.

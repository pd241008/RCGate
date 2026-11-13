# Decision: STOP

**Audit date:** 23 October 2026.  
**Decision:** STOP the proposed RC-Gate dependence programme. Do not start a method, a pilot dataset, or an auditor as the next research phase.

This is a recommendation about the research question. It is not a claim that the repository is finished as software, and it is not a prediction about publication.

## 1. What the current system actually is

**Repository finding, from the README and the final research report v1.** The implemented RC-Gate is a 233-parameter gate over two linear experts. The gate sees a claim-type embedding and a generator embedding. It does not see the six signal values. One expert scores cross-model agreement, contradiction, and semantic distance. The other scores NLI support, a source-quality constant, and NLI conflict. The output is a probability that a sentence overlaps a RAGTruth hallucination span. On the evaluated slice, `src_quality` does not vary, and the arithmetic checker does not fire.

**Repository finding, Stage 8, same report.** On one corrected 800-sentence RAGTruth slice (134 questions, 57 positive sentences), mean test AUROC over 20 question-grouped splits and 3 initializations is 0.6280 for flat logistic regression (A0), 0.6839 for gradient boosting with the same signals and metadata (A4), and 0.5717 for the full gate (A7). Mean paired A7 minus A4 is −0.1122. These are repeated fits on one question pool. They are not confidence intervals, and they are not a pilot of evidence dependence.

**Repository finding, hypotheses in that report.** Conditional reliability is recovered on synthetic data that were built to contain it. It is not established on the real slice. The gate is not shown to beat A4. The weights can be printed. Their scientific interpretability was not validated. Judge voting was never run.

**Inference:** Stage 8 is a negative result about metadata-only fusion on that slice. It does not measure whether dependent passages inflate a verifier, and it must not be cited as if it did.

## 2. What the proposed contribution claimed

**Paraphrase of the v0.3 pivot, which is a proposal, not a result.** When several passages are used to verify a claim, systems may treat shared-origin text as independent corroboration. A claim-specific origin model might reduce that error beyond deduplication and existing redundancy filters, without ignoring real corroboration. The pivot itself says this is a candidate, that broad novelty is not supported, and that no new empirical evidence for the direction exists yet.

The pilot protocol, annotation protocol, and decision record are unfilled. The preflight matrix of 23 October 2026 finds the LLM judge blocked, the origin-edge store missing, and the IMRRF comparator blocked. No scored pilot has been run.

Planned graphs, gold-provenance oracles, and evidence-status labels are not implemented capabilities.

## 3. Why the decision is STOP

Three separate tests were applied. All three fail for the programme as proposed.

**The method is already occupied.** Zhang, Ives, and Roth (ACL 2020, §4.2) state the overcounting problem, cite the truth-discovery dependence literature, and vote with indegree-0 provenance sources. Dong, Berti-Équille, and Srivastava (PVLDB 2009) infer copying so that repeated false values are not a majority. A public repository from 25 July 2026, `pxnkit/lineagerag`, already describes family-capped aggregation. No paper was found for that repository, and its code was not run, so it is not a verified result. It is still a public design of candidate A. Byrd's SSRN preprint claims the measurement and does not disclose it; the abstract alone is enough to retire "nobody has tried to measure source independence."

**The controlled empirical test already exists, and it is not a single positive effect.** GraphEcho (arXiv preprint, 15 September 2026) holds evidence wording fixed and varies path count separately from origin count. Some models move toward the repeated material. Others move away. Collapsing equivalent paths removes most of the redundant-path sensitivity in the reported Qwen3-4B static comparison and still responds to distinct origins. Provenance-aware training does not dominate that cheap control on both accuracy and coverage, and the reported SciFact transfer loses accuracy. HESM and IMRRF do not answer this test. They filter noisy or irrelevant text. They also mean the phrase "redundant evidence" cannot be used as a novelty claim.

**The leftover is not a justified project.** What GraphEcho leaves open, and what Ross et al. (abstract only, 14 August 2026) make uncertain, is non-identical dependence: paraphrases and shared primary sources in ordinary passage verifiers, after near-duplicate removal. That slice was not shown to be large. Evaluating it credibly needs reliable human labels on the cases Belkin, Madsen, and de-Wit (CogSci 2026) found people reduce to surface similarity. Those labels are not collected, the agreement gate is blank, and the primary LLM judge is not frozen. A 40–60 claim pilot of the current protocol would spend that missing annotation on a question whose identical-text version is already studied.

Candidate E, the auditor, is an integration project. The pivot already says a human-benefit claim needs a separate study. That study is not designed.

No candidate A–E is selected. The instruction for this audit was to select a primary contribution only if the evidence supported it.

## 4. What is demonstrated, what is only plausible, and what is not supported

**Demonstrated by published or inspected evidence**

- Same-source overcounting is a named problem in claim verification, with a provenance-graph vote as a published remedy (Zhang et al. 2020).
- Copying-aware truth discovery for structured values is a 2009 result (Dong et al.).
- LLM "redundancy filtering" in IMRRF is claim-conditioned summarization, not origin modeling.
- HESM's redundancy is noisy extra evidence in a FEVER evidence set.
- For identical graph paths, treating repeats as corroboration is model-dependent, and a collapse baseline is strong (GraphEcho, preprint).
- Human dependence judgments are dominated by verbal similarity in the CogSci 2026 experiment.
- The implemented RC-Gate gate loses to its flat metadata-capable control on the reported Stage 8 slice.
- The dependence pilot has not been run.

**Plausible, not verified**

- Some passage-level verifiers may still move on paraphrased or shared-primary-source evidence after near-duplicate removal.
- Fragment-level partial dependence may be poorly represented by an article-level indegree filter.
- A five-layer annotation scheme might be learnable by annotators who are forced off a wording heuristic. Belkin et al. give a reason to expect this to be hard. They do not prove it is impossible.

**Not supported or contradicted**

- "No existing verifier accounts for independent evidence." Zhang et al. 2020 contradict it.
- "Redundancy filtering for LLM verification is open." IMRRF contradicts the broad version.
- "Verifiers uniformly treat extra dependent text as extra support." GraphEcho's sign changes contradict a uniform version.
- "Stage 8 shows the new hypothesis." The tasks differ.
- "A learned dependence gate is the contribution." No residual over a cluster cap was measured.
- "The Evidence Auditor is a research result." No human outcome exists.
- Any numeric claim about Zhang et al. 2020 Figure 4, Byrd's estimator, or Ross et al. beyond the abstract. Those were not established in this pass.

## 5. Why this is not a pivot to another paper

A pivot would require another contribution that the literature supports. The literature does not support switching to a new aggregator, a new general benchmark, or a product study.

The historical gating paper is also not revived here. The final report already states that publication readiness has not been established and that the real evaluation is one 800-sentence slice. This audit did not produce new evidence that would change that conclusion.

The unresolved measurement in section 4 is not promoted to a GO. A GO would have required an exact question that survived the closest methods, a baseline it could beat, and a credible way to evaluate it now. The leftover question fails the third test. It also fails the first test as a novelty claim, because it is the future-work item GraphEcho states in §7, narrowed to passages.

## 6. What not to do next

- Do not implement a dependence estimator, a provenance graph, or a pilot scorer in this repository under the current question.
- Do not collect a dependence dataset as if the label set were already a contribution.
- Do not describe HESM or IMRRF as if they had solved origin dependence, and do not describe Zhang et al. 2020 as if they had evaluated modern LLM judges.
- Do not cite GraphEcho or Byrd as peer-reviewed.
- Do not fill the pilot decision record, download weights, or call a judge API as a follow-up to this audit. Those steps are a different phase, and this decision says that phase is not justified.

## 7. What would reopen the question

Only a new written question, outside this programme's current A–E framing, should reopen it. A minimum form that is not authorized by this STOP, but that would be the bar if someone later disagreed, is:

1. The estimator is not the contribution. Clustering and Zhang-style source filtering are the baselines, written down first.
2. The only eligible contrast is non-identical dependence that survives those baselines, with length, count, and order controlled, and with independent corroboration reported separately.
3. A calibration batch must show agreement on partial dependence and similar-but-independent pairs before any scored set is labeled.
4. A null or clustering-only result stops the work.

Until that exists as a separate, pre-registered plan, the defensible statement is the one in the title of this file.

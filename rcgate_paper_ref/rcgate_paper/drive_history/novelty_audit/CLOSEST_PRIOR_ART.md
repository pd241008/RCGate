# Closest prior art: methods, not abstracts

**Audit date:** 23 October 2026.  
**Quotation** means source wording with PDF line breaks normalized. **Paraphrase** means a restatement of a page that was opened. **Inference** means a conclusion of this audit.

The decision uses five works as the closest competitors. Other opened papers are here only where they change the comparison.

## 1. Zhang, Ives, and Roth (ACL 2020) already state the failure and change the vote

The proposed question says that verifiers treat dependent passages as independent corroboration. Section 4.2 of Zhang, Ives, and Roth states that failure for articles and source statements.

**Quotation, §4.2:** article-level majority vote is inadequate because of "(1) opinions which are too coarse-grained and (2) overcounting the opinions from the same source, which is also known as collusion or dependency of sources problem in truth finding (Pochampally et al., 2014)."

**Paraphrase of the remedy, same section:** Build a claim-evidence graph from the provenance graph. Add a support, contradiction, or neutral label on each edge by textual entailment. From the sink, take nodes whose indegree is 0. Vote with those nodes, called prov-sources, rather than with every article. The same source set can be passed to Simple LCA (Pasternack and Roth 2013).

**Paraphrase of the experiment, §5.2:** 495 factcheck.org questions are labeled from that site's own conclusions. The top 10 Google results, excluding factcheck.org, are the corpus. Three inputs are compared: the documents themselves (Doc), every graph node (All-Src), and indegree-0 nodes (Prov-Src). The prose says both majority vote and Simple LCA do better with the graph than with articles. Figure 4's bar heights were not transcribed, so this audit does not repeat a numeric accuracy.

What this method does **not** do, because the paper does not describe it:

- It does not embed passages and cluster them.
- It does not hold token count fixed while replacing a passage with a paraphrase.
- It does not label partial dependence, unknown dependence, or "similar wording but independently collected."
- It does not evaluate an LLM judge. The entailment model is a fine-tuned BERT, and the aggregators are majority vote and Simple LCA.

**Inference:** the remaining difference is the evaluator and the control, not the discovery that same-source repetition should not be counted as a new vote. Their own §1 says they have not solved provenance. That sentence limits the completeness of the graph. It does not leave the overcounting problem unnamed.

Simple LCA is not itself a dependence model. Pasternack and Roth (WWW 2013, conclusion) write that future work should capture source dependency. Zhang et al. handle dependence by choosing which sources enter LCA.

The 2021 follow-up by the same authors infers which source article a sentence came from. **Paraphrase of that abstract:** the task is provenance linking, and they explicitly separate it from fact-checking. It does not replace §4.2.

## 2. The structured-data method is older than the NLP wording

Dong, Berti-Équille, and Srivastava (PVLDB 2009) infer copying when sources share rare values, then discount those sources while deciding which value is true. Pochampally et al. (SIGMOD 2014) extend the idea from copying to other correlations.

**Inference:** a new natural-language aggregator that estimates pairwise dependence and then caps a family's vote is a descendant of this design. Zhang et al. 2020 already carried the descendant into claim verification. A further move from their graph vote to a logistic pair classifier plus a log family cap, which is what the unread-in-execution `pxnkit/lineagerag` README specifies, is a variation of a published pattern. It is not, by itself, an unoccupied method.

The data difference is real. Dong et al. use structured values. Passages have partial overlap, quotation, and mixed origins inside one article. That difference would matter if an experiment showed that the 2009/2020 remedies fail on partial, claim-specific dependence and that a new rule fixes the residual. No such experiment exists in this repository, and this audit did not find a result that establishes the residual as large.

## 3. HESM and IMRRF constrain a different redundancy claim

HESM (Subramanian and Lee, EMNLP 2020) is about evidence sets on FEVER. **Paraphrase of the abstract:** concatenating every retrieved sentence admits redundant and noisy text, and scoring each sentence alone misses combinations. The model retrieves sets and attends at word level and set level. Nothing in the sections read estimates whether two sentences share an upstream source.

IMRRF (Li et al., NAACL 2025) is the LLM paper whose title says "redundancy filtering." The filter is Appendix Table 6. **Quotation, rule 1:** "Extract information related to the claim from the provided paragraphs and summarize it; the summary should not exceed 300 words." Rule 4 drops irrelevant information. The pipeline then adds LLM-generated supplementary evidence and asks for a true/false verdict. Datasets are a FEVEROUS sentence subset and HOVER. There is no origin label.

**Inference:** "we filter redundant evidence" is not available as an RC-Gate novelty claim. "We estimate claim-specific origin dependence, which IMRRF's summarizer does not represent" is a true description of IMRRF. It is not yet a contribution, because Zhang et al. 2020 and the truth-discovery line already represent dependence, and IMRRF was never the closest method on that axis.

A fair IMRRF baseline on a frozen passage set would be a reimplementation of the summarizer, not a run of the published retrieval pipeline. The pilot preflight already marks that comparator as blocked. That implementation gap does not create a research gap.

## 4. GraphEcho already runs the controlled count-versus-origin test

GraphEcho (Wang, Zhou, Fan, and Zhang, arXiv:2609.17695, submitted 15 September 2026) is a preprint. It is still the closest empirical design, and it cannot be dismissed for being a preprint.

**Paraphrase of §3:** An atom is an evidential origin. One intervention changes the number of paths while keeping the atoms and their wording. Another changes the number of origins while keeping path count and wording fixed. Conflict conditions ask whether five copies of one supporting atom move the verdict more than one copy does, and whether five distinct supporting origins move it the other way.

**Paraphrase of Table 2, read from the arXiv HTML and not re-checked on the PDF:** the static effect is model-dependent. Qwen3-4B becomes more confident when one origin is repeated. Qwen3-1.7B barely moves. Qwen3-8B and GPT-5-mini become less confident under repetition and more confident when the origins are distinct. A single sentence of the form "verifiers treat dependence as corroboration" is therefore false for this setup.

**Paraphrase of the mitigations:** Showing provenance identifiers, or instructing the model to count origins, does not remove the redundant-path effect for Qwen3-4B. Collapsing equivalent paths does, and the independent-source effect remains (Table 7, M3). Provenance-aware training can beat that collapse by a few synthetic accuracy points while revisiting more and covering fewer origins. On SciFact, training reduces repeated walks and loses accuracy relative to the frozen model (Table 5). The authors say collapse and training do not dominate each other on both repetition and accuracy.

**Paraphrase of §7 and the limitations:** Repeating identical text is a limited form. SciFact document identifiers are not study-level independence. Future scientific data could track shared datasets and experiments across papers, because document boundaries are an incomplete account of source dependence.

**Inference:** the proposed pilot's length-matched arm, in the special case of identical text, has a 2026 preprint result and a strong cheap baseline (collapse). The case GraphEcho leaves open is non-identical dependence: paraphrase, shared primary artifacts, and partial dependence, on ordinary passage lists rather than graph walks. That open case is real. It is also the case their future-work paragraph already names. It has not been shown to be large, and Ross et al. (below) give a reason not to assume it is large.

## 5. Ross et al. are a warning, not a completed verification result

Ross, Koopman, van der Vegt, and Zuccon (arXiv:2608.13956, 14 August 2026) were read from the abstract only. They compare exact duplicate documents, LLM paraphrases of one document, and diverse documents. The abstract says duplicates and paraphrases do not significantly improve RAG answer correctness, while diverse documents improve it by 17%–47% through genre diversity.

**Inference:** this is not a verifier study, so it does not by itself answer the RC-Gate question. It does mean the audit cannot assume that paraphrased copies inflate model behavior. Any new experiment has to measure that inflation. It cannot cite the possibility as if it were already a finding.

## 6. Byrd claims the measurement and does not show the verifier

Byrd (SSRN 6903718, posted 24 June 2026, not peer-reviewed) was available as an abstract. **Quotation:** "The measurement is implemented in Verdict Weight; its internal mechanism is out of scope here." The domains named are medical imaging and pharmacovigilance. The abstract's claim is that provenance alone yields an effective independent-source count, and that agreement-as-corroboration is routinely false.

**Inference:** this preprint is enough to reject the sentence "measuring source independence is an open idea." It is not enough to reject a specific unverified claim about LLM passage verifiers, because the algorithm, data, and task were not in the abstract. The full text remains unresolved. Related SSRN abstracts by the same author were not reviewed.

## 7. Belkin et al. constrain the annotation, not the model

Belkin, Madsen, and de-Wit (CogSci 2026 proceedings; eScholarship header: peer-reviewed) ask people, not models, whether posts were coordinated. Near-identical wording drives the judgment (generalized η² = .283). Knowability does not. The authors' own alternative explanations are a stimulus ceiling and a surface heuristic.

**Inference:** a new benchmark whose gold dependence labels are human judgments of wording will be pulled toward the heuristic they measured, unless the guide forces annotators to use artifacts other than wording and reports agreement on the hard cells: paraphrased dependence and similar-but-independent collection. The proposed annotation protocol already says this. Belkin et al. make it an empirical risk, not a wording preference. They do not implement a verifier.

## 8. What is not the closest work

InteGround (Findings of EMNLP 2025) finds robustness to redundant evidence. In that paper, redundancy means a superset of the gold evidence, and "inter-dependent" means pieces that must be combined. Using it as evidence that verifiers ignore copied sources would be a construct error.

PAGE-RAG separates graph connectivity from answer support. That is a different mistake from counting a syndicated copy as a second witness.

The arXiv paper titled LineageRAG (Zheng et al., arXiv:2608.16004) grounds GraphRAG demands in verbatim spans. The GitHub project `pxnkit/lineagerag` is a different artifact: an MIT repository from 25 July 2026 whose README specifies family-capped Bayesian aggregation. No paper was found for that repository. Its originality note says synthetic smoke numbers are not real-world performance. The code was not run. **Inference:** the README shows that the proposed aggregator has been written down in public. It does not show that the aggregator works on news.

## 9. Comparison against the proposed RC-Gate method

The v0.3 pivot's candidate method is a claim-specific provenance graph over evidence fragments, an estimate of dependence from similarity and metadata, and an aggregator that does not give each URL a vote. The observable claim is a better evidence-status decision than deduplication, clustering, and count caps, without losing real independent corroboration.

| Proposed piece | Where it already appears | What is not copied from that work |
|---|---|---|
| Do not count dependent items as new corroboration | Zhang et al. 2020 §4.2; Dong et al. 2009 | Modern LLM/NLI judges; partial edges; unknown edges |
| Provenance graph for a claim | Zhang et al. 2020 §2; Zhang et al. 2021 for articles | Separation of textual reuse, publication lineage, and epistemic dependence as three stored relations |
| Family cap so copies do not add linearly | `pxnkit/lineagerag` README; GraphEcho M3 collapse | A peer-reviewed natural-language evaluation of the log cap |
| Hold content fixed and vary origin count | GraphEcho §3 | Paraphrase and shared-primary-source passages; NLI aggregation |
| Redundancy filter before verification | IMRRF Table 6; HESM evidence sets | Neither filter is an origin model |
| Human dependence labels that are not text similarity | Not found as a verifier benchmark | Belkin et al. show why those labels are the hard part |

**Inference:** the precise difference that survives is narrow. It is whether passage-level verifiers still change their decisions on non-identical, claim-specific dependence after exact and near-duplicate removal, on evidence a human can defend with artifacts rather than wording. That difference is a possible measurement. It is not a method that has survived comparison, and GraphEcho's collapse result says the first baseline to beat is still clustering, not a learned gate.

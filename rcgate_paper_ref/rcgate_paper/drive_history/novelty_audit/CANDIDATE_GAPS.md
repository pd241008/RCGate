# Candidate contributions

**Audit date:** 23 October 2026.  
Each candidate is judged alone. They are not combined into one verifier paper.  
Evidence is marked **Demonstrated**, **Plausible**, or **Not supported**. Those words describe the literature and this repository. They are not verdicts on the external world beyond the sources that were opened.

The current RC-Gate system is not any of these candidates. What it implements, and what Stage 8 measured, is summarized in `GO_NO_GO_DECISION.md`. Stage 8 is not evidence for or against A–E.

## A. A new dependence estimator inside verification

**Already demonstrated.** Dong, Berti-Équille, and Srivastava (PVLDB 2009) infer copying and discount it in truth discovery. Zhang, Ives, and Roth (ACL 2020, §4.2) move that problem into natural-language claims: they vote with indegree-0 provenance nodes so the same source is not counted once per article. Pasternack and Roth (WWW 2013) do not model dependence; Zhang et al. apply them after the graph filter. The `pxnkit/lineagerag` README (public code, 25 July 2026, no paper found) writes down a later variant: a pairwise derivation score, origin families, and a capped family weight in a Bayesian updater. Byrd (SSRN preprint, 24 June 2026, abstract only) claims a provenance-only independence measure and an effective source count, and withholds the mechanism.

**Closest papers.** Zhang et al. 2020, Dong et al. 2009, Pochampally et al. 2014, GraphEcho's collapse baseline (M3), and the LineageRAG repository. IMRRF is not close on this axis: its filter summarizes relevant paragraphs (Appendix Table 6).

**Unanswered part.** Whether a fragment-level graph with partial and unknown edges beats Zhang-style indegree filtering and text clustering on paraphrased or shared-primary-source passages. That part is **plausible** and unmeasured. It is a residual, not a vacant method.

**Kind of difference.** Mostly a combination of published pieces, plus an engineering change of unit from article or structured value to claim-specific fragment. A technical contribution would exist only if the residual were measured and the new rule beat the simple rules. That measurement does not exist.

**Evidence that would make it matter.** On held-out natural chains, a predeclared dependence rule would need to reduce false support relative to exact dedup, lexical clustering, semantic clustering, and a count cap, while still moving when independent evidence changes the gold status. GraphEcho already shows that collapse can remove identical-text sensitivity. The new rule has to win on the cases collapse misses.

**Strongest simple alternative.** Cluster near-duplicates and cap each cluster at one vote. GraphEcho M3 is the empirical reason to try this before any learned estimator.

**What would invalidate it.** The cap matches the learned or oracle rule on the hard natural cases, or the only gains come from abstaining more often.

**Feasibility.** Not with the current freeze. The preflight matrix marks the oracle, the cluster cap, and the edge store as missing. Byrd's estimator cannot be reproduced from the abstract. Building A before a residual is observed would implement a known pattern.

**Novelty enough for a paper phase?** **Not supported.** Do not select A.

## B. A controlled study of dependent evidence on LLM and NLI verifiers

**Already demonstrated, for identical content on graph agents.** GraphEcho (arXiv preprint, 15 September 2026) holds wording fixed and separates path count from origin count. Static effects change sign across models. Repeated paths increase echo walks for every frozen agent they test. Collapse removes most of the redundant-path sensitivity for Qwen3-4B and keeps a response to distinct origins. Details and the HTML-versus-PDF caveat are in `CLOSEST_PRIOR_ART.md`.

**Plausible, not demonstrated.** The same pattern for a frozen passage list, an NLI aggregator, paraphrases, order effects, and natural syndication. Ross et al. (arXiv preprint, 14 August 2026, abstract only) report that duplicates and LLM paraphrases do not significantly improve RAG answer correctness. That is a different task, and it cuts against assuming a large paraphrase effect.

**Closest papers.** GraphEcho; Ross et al. at abstract level; InteGround only as a warning not to call a superset of gold evidence "source dependence."

**Unanswered part.** Passage-level verifiers, non-identical dependence, and order at matched length. **Plausible.** Also explicitly future work in GraphEcho §7 for shared datasets across papers.

**Kind of difference.** An empirical extension of a robustness test that already has a name and a design. Not a new method.

**Evidence that would make it matter.** A predeclared effect on the primary verifiers, in the naturalistic arm and in the matched arm, that remains after near-duplicate removal, with absolute false-support rates as well as the paired difference. A model-specific wiggle that disappears under clustering would not matter.

**Strongest simple alternative.** The GraphEcho reading: report each verifier separately, and treat cluster-and-cap as the baseline that may already explain the shift.

**What would invalidate it.** Effects are null, reverse, or confined to byte-level copies; or they are indistinguishable from passage order and length. GraphEcho's sign changes mean a one-model positive result cannot be generalized.

**Feasibility.** A synthetic identical-text replica would be feasible and would not be new. A credible paraphrase and natural-chain study needs frozen verifiers, which the preflight marks blocked for the LLM judge, and origin labels, which are not collected. Forty to sixty claims can probe feasibility. They cannot establish a field effect.

**Novelty enough for a paper phase?** **Not supported** as currently framed. The identical-text core has a preprint. The leftover slice is a possible later measurement, not a reason to start the method or the benchmark.

## C. A benchmark that separates truth, evidence status, reuse, lineage, and epistemic dependence

**Already demonstrated in pieces.** FEVER-style sets label support. Zhang et al. 2020 and 2021 label provenance. GraphEcho-Syn labels origin versus path count for fictional atoms. SciFact document IDs are a weaker proxy, which GraphEcho's limitations state. RAGTruth labels hallucination spans, not evidential origin. The v0.3 pivot already says RAGTruth does not supply the required origin labels. That reading is still right.

**Not found.** One audited public benchmark that, for the same claim, stores partial and unknown relations and keeps textual reuse, publication lineage, and epistemic dependence as different fields. This absence was not proven by a complete dataset census. It is **plausible**, and it is not a contribution by itself.

**Closest papers.** GraphEcho; Zhang et al. 2021 (Politi-Prov, source-article links); the survey by Zerong et al. (Findings of EMNLP 2025), whose case studies stress annotation difficulty for veracity, not this taxonomy. TRIVIA+ and PROBE were not re-read. They remain open comparators if a benchmark paper is ever drafted.

**Unanswered part.** Whether the five-way label set can be applied reliably to natural source chains. **Not supported** that it can. Belkin, Madsen, and de-Wit (CogSci 2026) show that human dependence judgments track surface similarity and miss a factor the normative model treats as important. The proposed codebook already separates the layers. Separation on paper is not agreement in practice.

**Kind of difference.** Dataset-related, and only if the labels are reliable and let someone answer a question current sets cannot. Otherwise it is an annotation schema.

**Evidence that would make it matter.** Predeclared agreement on partial dependence and on similar-but-independent cases, a non-trivial unknown rate, and at least one analysis that changes when lineage is separated from wording. A schema file does not do that.

**Strongest simple alternative.** Reuse GraphEcho's origin-versus-copy contrast for identical text, and reuse existing provenance corpora for article lineage. Build new labels only for the relation those resources do not store.

**What would invalidate it.** Annotators cannot beat a wording heuristic on the hard cells, or every published analysis can be redone on GraphEcho-Syn plus a text-reuse detector.

**Feasibility.** The preflight marks per-annotator storage, the four layers, and agreement statistics as missing. Two annotators are a staffing need, not a code need. No reliability gate has been filled in the decision record. **Not currently feasible** as a paper dataset.

**Novelty enough for a paper phase?** **Not supported.** Do not select C before a calibration batch shows the hard labels are usable.

## D. When provenance helps beyond dedup, clustering, and count caps

**Already demonstrated in an older setting.** Zhang et al. 2020 §5.2 compare articles, all graph nodes, and indegree-0 nodes. The graph beats articles for both voters they test. They do not compare shingling or embedding clusters. GraphEcho compares provenance identifiers and an instruction against collapsing repeated evidence. For the identical-text agent, collapse is the strong control, and provenance text in the prompt is not.

**Plausible.** A gain from artifact-level lineage on paraphrases that survive embedding clustering. Unmeasured.

**Closest papers.** Zhang et al. 2020; GraphEcho M0–M3; IMRRF only as a relevance summarizer, not as this comparison.

**Unanswered part.** The incremental value of origin labels after a strong near-duplicate baseline, on non-identical natural pairs. **Plausible** and possibly small.

**Kind of difference.** Empirical. If the winner is the cluster cap, there is no method paper.

**Evidence that would make it matter.** A paired comparison, same passages, in which an origin rule beats both lexical and semantic caps by a predeclared margin on hard pairs, and does not win by dropping coverage.

**Strongest simple alternative.** Semantic cluster cap. It has to be tried before provenance is credited.

**What would invalidate it.** The cap removes the error Zhang-style provenance was supposed to fix, which is what GraphEcho's collapse condition does for identical paths.

**Feasibility.** Same blockers as B and C. In addition, thresholds for semantic clustering must be frozen on a calibration split. That split does not exist.

**Novelty enough for a paper phase?** **Not supported** as a standalone claim. It is the comparison any later measurement would have to include. It is not a reason to build the estimator first.

## E. A practical verification or multi-model audit system

**Already demonstrated as a product shape, not as this repository.** The historical RC-Gate demo scores one answer from a saved checkpoint and displays gate weights. The final report says inspectability was not validated as an explanation. SAFE, FActScore, and ordinary RAG citation interfaces already show claims with evidence. Those three were not re-audited at full text in this pass; FActScore is the EMNLP 2023 paper already cited in the final report. The new "Evidence Auditor" in the v0.3 pivot is specified and not built.

**Closest work.** The implemented studio and Streamlit demo; Zhang et al. 2020 as a provenance view; any citation-bearing fact checker. A UI comparison was not performed.

**Unanswered part.** Whether a specific interface changes human decisions. **Not supported.** The pivot correctly puts a human study out of scope. Without that study, E is engineering.

**Kind of difference.** Engineering integration.

**Evidence that would make it matter.** A predeclared human outcome against a strong evidence-list baseline. That study is not designed.

**Strongest simple alternative.** Show the passages, the cluster ids, and the verifier output. Do not add a new model.

**What would invalidate it.** Users do no better with the auditor than with the passage list, or the system only looks more certain because it hid duplicate text.

**Feasibility.** A thin viewer over manually entered passages is feasible. It would not be a research result. The preflight says the current UI is the wrong annotation surface because it shows historical scores.

**Novelty enough for a paper phase?** **Not supported.** Do not select E.

## Counterarguments, stated as strongly as the sources allow

**Against A.** The contribution reduces to a known provenance vote (Zhang et al. 2020), a known copying model (Dong et al. 2009), or a public family cap (`pxnkit/lineagerag` README), possibly retargeted to a new corpus. Retargeting is not a method.

**Against B.** GraphEcho already ran the matched content intervention and did not find one shared failure. Calling the passage version a new phenomenon renames a robustness test. Ross et al.'s abstract, if it holds up under a full-text read, suggests paraphrases may not move the downstream model either.

**Against C.** A new label set is a contribution only after it is shown to be reliable and necessary. Belkin et al. predict the failure mode of the reliability study. GraphEcho-Syn already supports the identical-text analysis without the new labels.

**Against D.** The strongest published simple alternative may be sufficient. Zhang et al. showed a graph beat raw articles, not that it beat clustering. GraphEcho's collapse result is the warning.

**Against E.** An auditor that displays a known graph is an integration project. The repository's existing demo does not become that contribution by being extended.

## What this file does not say

It does not say that every future RC-Gate question is closed. It says that A–E, as framed for this programme, do not have a literature-backed novelty claim that justifies a paper-development or implementation phase. The only leftover is the unmeasured non-identical passage case inside B and D. That leftover is recorded in the decision file as an unresolved measurement, not as a selected contribution.

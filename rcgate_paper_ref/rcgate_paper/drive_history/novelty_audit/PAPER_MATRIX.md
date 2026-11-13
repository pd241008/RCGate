# Prior-art matrix

**Audit date:** 23 October 2026.  
**How to read this file.** The short table is a comparison, not a ranking of quality. The records below it are the audit. Unknowns stay unknown. **Quotation** is source wording with PDF line breaks normalized. **Paraphrase** restates an opened source. **Inference** is this audit's conclusion.

Works cited by the v0.3 pivot but not re-read in this pass are omitted here on purpose. They are listed in `AUDIT_LIMITATIONS.md`.

## 1. Short comparison

| Work | Status | Dependence | What is repeated | Level | Overlap with the proposed RC-Gate question |
|---|---|---|---|---|---|
| Zhang, Ives, and Roth 2020 | Peer-reviewed, ACL | Inferred from a claim provenance graph; indegree-0 nodes are treated as independent | Same statement reached through multiple articles | Claim and source statement | Direct. Already discounts same-source votes in claim verification. |
| Dong, Berti-Équille, and Srivastava 2009 | Peer-reviewed, PVLDB | Inferred by a Bayesian copying model | Structured values, not passages | Source, over many values | Direct ancestor of the problem. Different data type. |
| Pochampally et al. 2014 | Peer-reviewed, SIGMOD | Inferred correlation, broader than copying | Structured extracted values | Source | Cited by Zhang et al. as the dependence problem. |
| Pasternack and Roth 2013 | Peer-reviewed, WWW | Not modeled. Conclusion defers it. | Claims asserted by sources | Source and claim | The voter Zhang et al. use after graph filtering. |
| HESM 2020 | Peer-reviewed, EMNLP | Ignored | Noisy extra sentences inside a retrieved set | Sentence and evidence set | Overlap is redundant text in FEVER-style verification, not origin dependence. |
| IMRRF 2025 | Peer-reviewed, NAACL | Ignored | Irrelevant retrieved text, removed by summarization | Passage summary | Overlap is the word "redundancy," not shared origin. |
| InteGround 2025 | Peer-reviewed, Findings of EMNLP | Not source dependence. "Inter-dependent" means jointly necessary pieces. | Extra non-essential evidence in a superset | Evidence set | Easy to misread. It does not test copied corroboration. |
| Belkin, Madsen, and de-Wit 2026 | Peer-reviewed proceedings, CogSci 48 | Human inference from wording | Near-identical versus differently worded posts | Human judgment of posts | Shows surface similarity dominates human dependence judgments. Not a verifier. |
| GraphEcho 2026 | Preprint, arXiv:2609.17695, 15 Sep 2026 | Assigned by the benchmark; content held fixed | Repeated graph paths from one origin | Graph path and evidential atom | Closest controlled test of copy count versus origin count. |
| Ross et al. 2026 | Preprint, arXiv:2608.13956, 14 Aug 2026. Abstract only. | Constructed as duplicate, paraphrase, or diverse documents | Exact copies and LLM paraphrases of one document | Document set for generation | Adjacent. Outcome is answer correctness, not a verification verdict. |
| Byrd 2026 | SSRN preprint, posted 24 Jun 2026. Abstract only. | Claimed to be measured from provenance | Not described; mechanism withheld | Domain records in imaging and pharmacovigilance | Threatens the claim that independence measurement is unexplored. Does not show an NL verifier. |
| `pxnkit/lineagerag` | Public code, 25 Jul 2026. No paper found. | Classifier over pair features; family cap in a Bayesian updater | Synthetic cascades, including paraphrase and syndication, as described in the README | Document family | Design overlap with the proposed aggregator. No audited empirical result. |
| PAGE-RAG 2026 | Preprint. Introduction read. | Not copying. Edges are support hypotheses. | Connected but non-supporting hops | Multi-hop candidate path | Different failure: connectivity is not support. |
| Zhang, Ives, and Roth 2021 | Peer-reviewed, ACL | Provenance inference only | Source articles behind sentences | Sentence to source article | Extends provenance linking. Does not re-test dependence-aware voting. |
| Zerong et al. 2025 | Peer-reviewed, Findings of EMNLP | Not the survey's question | Survey window ends March 2025 | Field survey | Sets the search boundary this audit had to extend. Extension is partial. |

## 2. Full records

### Zhang, Ives, and Roth, ACL 2020

- **Title / authors / venue:** "Who said it, and Why?" Provenance for Natural Language Claims. Yi Zhang, Zachary G. Ives, and Dan Roth. ACL 2020, pages 4416–4426.
- **Status:** Peer-reviewed conference paper.
- **DOI / URL:** [10.18653/v1/2020.acl-main.406](https://doi.org/10.18653/v1/2020.acl-main.406). PDF: [aclanthology.org/2020.acl-main.406.pdf](https://aclanthology.org/2020.acl-main.406.pdf).
- **Code / license:** The paper says the code is at `https://cogcomp.seas.upenn.edu/page/publication_view/901` (§5.1, footnote 3). That page was not opened. License: unknown.
- **Question:** Infer where a natural-language claim came from and how it evolved, then use that graph in verification.
- **Input:** A query claim, web or corpus context retrieved by similarity to the claim, and earlier statements.
- **Source relationships:** A directed acyclic graph. Nodes are sources paired with statements, plus the query claim. Edges are inferred influence relations (§2.1).
- **Dependence:** Inferred, then used. **Quotation, §4.2:** article-level majority vote suffers from "overcounting the opinions from the same source, which is also known as collusion or dependency of sources problem in truth finding." They breadth-first search from the sink and vote with indegree-0 nodes, which they call prov-sources.
- **Redundancy:** Handled by not voting every article that repeats a statement. This is not lexical or embedding deduplication.
- **Level:** Claim, statement, and source. Not a passage-level epistemic-origin label separated from publication lineage.
- **Lineage versus independent evidence:** The graph is a dissemination history. Prov-sources are nodes with no incoming edge. **Inference:** that is an ancestry filter, not a tested distinction between a shared press release and two independent investigations that happen to agree.
- **Algorithm:** ELMo retrieval of context; textual-entailment source extraction with BERT variants; entailment labels for support, contradiction, and neutral; majority vote and Simple LCA (Pasternack and Roth 2013) on Doc, All-Src, or Prov-Src inputs (§4–§5).
- **Data / annotation:** Source extraction: MPQA 2.0, opinions restricted to sentences, 10-fold overlap match of at least half the annotated source words (§5.1). Verification: 495 factcheck.org questions, true/false taken from the site's own conclusion, after dropping items without a consolidated conclusion (§5.2). Top-10 Google results, with factcheck.org removed.
- **Baselines / findings:** Table 1 gives source-extraction F1. The best reported mean F1 is TE-D at 0.7645. For verification, the text of §5.2 says both majority vote and Simple LCA improve with the claim-evidence graph relative to using articles as sources. The bar values in Figure 4 were not transcribed.
- **Authors' limitations:** **Quotation, §1:** "we have not solved the claim provenance problem." §7 says unmentioned authors are difficult, and edge labels for how a claim evolved were not exploited.
- **Overlap:** The proposed failure mode, counting repeated sources as separate corroboration, is stated and given a graph remedy.
- **Difference that is actually supported:** Their voter is majority vote or Simple LCA on a 2013 credibility model, not a frozen modern LLM judge or an NLI aggregator. They do not report a length-matched paraphrase intervention, a similar-but-independent control, or separate labels for textual reuse, publication lineage, and epistemic dependence. They do not compare against shingling or embedding clustering.
- **Reproduction:** Conceptually feasible. Exact reproduction needs the unopened code page, a Google search step, and the factcheck.org crawl. Fair adaptation to a frozen passage set is possible only as a reimplementation, which would no longer be their system.

### Dong, Berti-Équille, and Srivastava, PVLDB 2009

- **Title / authors / venue:** Integrating Conflicting Data: The Role of Source Dependence. Xin Luna Dong, Laure Berti-Équille, and Divesh Srivastava. PVLDB 2(1):550–561, 2009.
- **Status:** Peer-reviewed. DOI: [10.14778/1687627.1687690](https://doi.org/10.14778/1687627.1687690). PDF: [vldb09-pvldb47.pdf](http://www.vldb.org/pvldb/vol2/vldb09-pvldb47.pdf).
- **Code / license:** Unknown. Not searched beyond the paper.
- **Question:** Find true values when sources copy one another, so a false value can become the majority.
- **Input:** Sources providing values for data items.
- **Dependence:** Inferred. **Paraphrase of the abstract:** shared rare values are evidence that one source copied another. Bayesian dependence detection alternates with truth discovery. Accuracy and value similarity are extensions.
- **Redundancy:** Copied values are the object of the model, not a text-deduplication preprocess.
- **Level:** Source and structured value. Not a sentence, and not claim-specific partial dependence inside one article.
- **Lineage versus independent evidence:** Copying is the dependence relation. Independent sources are those not inferred to copy.
- **Algorithm:** Iterative Bayesian copying detection plus truth discovery. Equations were not re-derived in this audit.
- **Data:** Synthetic data and real-world data, as stated in the abstract. Dataset names and table numbers were not transcribed.
- **Findings:** The abstract says the algorithm improves truth-discovery accuracy and scales to many sources. Exact deltas were not transcribed.
- **Limitations acknowledged:** Not fully extracted. **Inference:** the paper solves a structured-data problem. Applying it unchanged to paraphrased news passages is a new engineering problem, not an empty research slot, because Zhang et al. 2020 already moved the same idea into claim verification.
- **Reproduction:** The paper is public. A faithful reimplementation was not assessed.

### Pochampally et al., SIGMOD 2014

- **Title / authors / venue:** Fusing Data with Correlations. Ravali Pochampally, Anish Das Sarma, Xin Luna Dong, Alexandra Meliou, and Divesh Srivastava. SIGMOD 2014, pages 433–444, as cited by Zhang et al. 2020.
- **Status:** Peer-reviewed. DOI from the publisher record opened in search: [10.1145/2588555.2593674](https://doi.org/10.1145/2588555.2593674).
- **Code / license:** Unknown.
- **Question / method:** **Paraphrase of the abstract:** correlation among sources is broader than copying, including negative correlation and shared extraction rules. They model those correlations for truth finding.
- **Dependence:** Inferred correlation, not ignored.
- **Level:** Structured sources and extracted values.
- **Overlap:** This is the paper Zhang et al. cite when they name the dependence problem.
- **Difference:** Not a passage-level LLM or NLI study. Full algorithm not re-read.
- **Reproduction:** Unknown.

### Pasternack and Roth, WWW 2013

- **Title / authors / venue:** Latent Credibility Analysis. Jeff Pasternack and Dan Roth. WWW 2013, pages 1009–1020.
- **Status:** Peer-reviewed. PDF: [p1009.pdf](https://archives.iw3c2.org/www2013/proceedings/p1009.pdf).
- **Code / license:** Unknown.
- **Dependence:** Not in the model that was read. **Paraphrase of the conclusion:** future work should capture source dependency. The experiments discuss copying as a domain story that GuessLCA can partly explain as "guessing," which is not a copied-source graph.
- **Role in the matrix:** Zhang et al. 2020 feed prov-sources into Simple LCA. The dependence handling is in the graph filter, not inside Simple LCA.
- **Reproduction:** Not assessed.

### HESM, EMNLP 2020

- **Title / authors / venue:** Hierarchical Evidence Set Modeling for Automated Fact Extraction and Verification. Shyam Subramanian and Kyumin Lee. EMNLP 2020, pages 7798–7809.
- **Status:** Peer-reviewed. DOI: [10.18653/v1/2020.emnlp-main.627](https://doi.org/10.18653/v1/2020.emnlp-main.627).
- **Code / license:** [github.com/ShyamSubramanian/HESM](https://github.com/ShyamSubramanian/HESM). GitHub reports MIT. Code not run.
- **Question:** Retrieve evidence sets for a claim and classify Supported, Refuted, or Not Enough Info.
- **Input:** Claim plus Wikipedia documents. Document retriever reused from Nie et al. 2019 (§4).
- **Dependence:** Ignored. No source-copy variable was found in the sections read.
- **Redundancy:** **Paraphrase of the abstract:** concatenating all evidence sentences includes redundant and noisy information, and pairwise scoring misses early combination of related sentences. Evidence sets are groups of sentences, attended hierarchically.
- **Level:** Document, sentence, and evidence set. Not information-origin.
- **Lineage versus independent evidence:** Not represented.
- **Algorithm:** Multi-hop evidence retrieval; word-level and evidence-set attention; three-way classification. Exact layer sizes were not transcribed.
- **Data:** FEVER, as stated in the abstract and the repository description. Annotation is FEVER's, not a new origin taxonomy.
- **Findings:** The abstract says HESM outperforms 7 prior fact-extraction and verification methods. Cell values were not transcribed.
- **Limitations:** Not fully extracted. **Inference from the method:** a gain on FEVER evidence-set accuracy is not a test of copied news corroboration.
- **Overlap:** Evidence-set aggregation and the motive of avoiding redundant sentences.
- **Difference:** No claim-specific origin graph and no controlled dependent-versus-independent passage intervention.
- **Reproduction:** Repository exists. Whether it still runs was not tested. Task mismatch with a frozen multi-publisher passage set is large.

### IMRRF, NAACL 2025

- **Title / authors / venue:** IMRRF: Integrating Multi-Source Retrieval and Redundancy Filtering for LLM-based Fake News Detection. Dayang Li, Fanxiao Li, Bingbing Song, Li Tang, and Wei Zhou. NAACL 2025, pages 9127–9142.
- **Status:** Peer-reviewed. DOI: [10.18653/v1/2025.naacl-long.461](https://doi.org/10.18653/v1/2025.naacl-long.461).
- **Code / license:** [github.com/quark233/IMRRF](https://github.com/quark233/IMRRF). The GitHub license API returned 404. No license was stated in the README that was opened. The filter step is `generate_summary.py`. Code not run. The README requires an OpenAI API key for the knowledge-graph step.
- **Question:** Verify complex claims by retrieving more evidence and then removing redundant or irrelevant retrieved text before an LLM verdict.
- **Input:** Claim; BM25 paragraphs from Wikipedia; knowledge-graph tuples; an LLM summary; extra LLM-generated "world knowledge."
- **Dependence:** Ignored. No origin, citation, or copying variable appears in §3 or Appendix Table 6.
- **Redundancy:** **Quotation, Appendix Table 6, rule 1:** "Extract information related to the claim from the provided paragraphs and summarize it; the summary should not exceed 300 words." Rule 4 says not to summarize irrelevant information. The operation is summarization, not a dependence estimate.
- **Level:** Retrieved paragraph and summary. The verification prompt then sees two evidence blocks: the summary and the LLM-generated supplement (Table 8 region of the appendix).
- **Lineage versus independent evidence:** Not represented. "Multi-source" in the title means corpus text plus a knowledge graph plus LLM knowledge.
- **Algorithm:** BM25; LLM entity and path selection; GPT-4o for filtering and knowledge conversion at temperature 0; FLAN-T5-XL or GPT-4o as the verifier (§4.1).
- **Data:** FEVEROUS sentence subset of 2,962 claims, following ProgramFC; HOVER validation claims at 2, 3, and 4 hops (§4.1). No new human origin annotation.
- **Findings:** Table 1 is described as higher accuracy and F1 than the listed fact-checking baselines. The ablation text says redundant-information filtering contributes. Exact headline scores were not re-copied into this matrix.
- **Authors' limitations:** The conclusion does not discuss source copying. **Inference:** nothing in the method stops two independent Wikipedia sentences that share an upstream source, because Wikipedia is the corpus and the filter scores relevance, not ancestry.
- **Overlap:** LLM verification and a component named for redundant information.
- **Difference:** It does not estimate claim-specific evidential origin, and it does not hold passage count fixed while swapping dependent and independent evidence.
- **Reproduction:** Possible only as an adaptation on a frozen passage set. The published system retrieves its own evidence and adds LLM-generated evidence. The pilot protocol already says that full IMRRF is not a clean fixed-evidence comparison.

### InteGround, Findings of EMNLP 2025

- **Title / authors / venue:** InteGround: On the Evaluation of Verification and Retrieval Planning in Integrative Grounding. Cheng Jiayang, Qianqian Zhuang, Haoran Li, Chunkit Chan, Xin Liu, Lin Qiu, and Yangqiu Song. Findings of EMNLP 2025, pages 13587–13602.
- **Status:** Peer-reviewed. DOI: [10.18653/v1/2025.findings-emnlp.732](https://doi.org/10.18653/v1/2025.findings-emnlp.732). Code: [github.com/HKUST-KnowComp/InteGround](https://github.com/HKUST-KnowComp/InteGround). License not checked.
- **Question:** Whether models can verify and retrieve multiple pieces of evidence that are jointly needed.
- **Dependence:** Not source dependence. The abstract's "inter-dependent pieces" means evidence that must be synthesized together.
- **Redundancy:** One test condition is a superset of the gold evidence. **Paraphrase of the findings section:** models are relatively robust to that extra evidence, and they are not robust to incomplete evidence, where they use parametric knowledge.
- **Level:** Evidence set for groundedness. Not publication lineage.
- **Overlap:** The word "redundant evidence" in an LLM verification setting.
- **Difference:** A superset of useful evidence is a different intervention from a copied or syndicated passage. This paper must not be cited as a test of source dependence.
- **Reproduction:** Not assessed. Not required for that distinction.

### Belkin, Madsen, and de-Wit, CogSci 2026

- **Title / authors / venue:** When agreement looks like copying: Testing a Bayesian model of source dependency inference. Sonja Belkin, Jens Koed Madsen, and Lee H. de-Wit. Proceedings of the Annual Meeting of the Cognitive Science Society, volume 48, 2026.
- **Status:** The eScholarship PDF header says "Peer reviewed." The LSE record lists the same paper in that proceedings volume: [researchonline.lse.ac.uk/id/eprint/140546](https://researchonline.lse.ac.uk/id/eprint/140546/). A separate proceedings DOI was not retrieved. License on the eScholarship copy: CC BY 4.0.
- **Code:** Analyses are described as being in an OSF repository. The OSF URL was not extracted. Preregistered on AsPredicted. The AsPredicted number was not extracted.
- **Question:** Do people infer coordination from verbal similarity, topic knowability, and expressive diversity, as a Bayesian model predicts?
- **Input:** Social-media posts in a factorial design. N = 156.
- **Dependence:** Measured as a human judgment. Not computed for a verifier.
- **Redundancy:** Low-noise posts are near-identical; high-noise posts are substantively similar but differently worded.
- **Level:** Sets of posts. Not a claim-verification label.
- **Lineage versus independent evidence:** The design contrasts surface copying with factors that should matter if people were doing the normative calculation. It does not annotate news provenance.
- **Findings, from the results section:** Noise (verbal similarity) has generalized η² = .283, F(1, 154) = 91.53. Knowability is not significant, F(1, 154) = 0.75, p = .387. The authors offer two readings: the low-noise stimuli may have been so obviously copied that knowability could not matter, or people use a surface copy-detection heuristic.
- **Limitations:** The authors state the first reading as a possible design limit.
- **Overlap:** Any annotation guide that treats similar wording as dependence, or different wording as independence, has a documented human failure mode.
- **Difference:** No LLM, no NLI model, no verification metric.
- **Reproduction:** The paper gives the analysis specification. Stimuli were not downloaded.

### GraphEcho, arXiv 2026

- **Title / authors / venue:** GraphEcho: Structural Redundancy and Evidence Provenance in LLM Graph Agents. Sikun Wang, Yixi Zhou, Lei Fan, and Fan Zhang.
- **Status:** Preprint. Not peer-reviewed in any record opened here. Submitted 15 September 2026. [arXiv:2609.17695](https://arxiv.org/abs/2609.17695).
- **Code / license:** No code URL was found in the sections read. License: unknown.
- **Question:** Does an agent treat more paths as more corroboration when the evidential origin does not change?
- **Input:** A claim, graph paths, and provenance atoms. Static prompting and an agent with a walk budget.
- **Dependence:** Assigned by the generator, not inferred from wild text. π(p) maps each path to an origin. Conditions change path count, origin count, or both (§3.1–§3.3).
- **Redundancy:** The primary contrast uses the same evidence wording and path templates for one origin versus five origins. A second contrast repeats one origin across five paths.
- **Level:** Graph path and evidential atom. SciFact uses document identifiers as a proxy, which the limitations section says do not establish statistical independence of studies.
- **Lineage versus independent evidence:** Synthetic origins are distinct by construction. The paper does not separate textual reuse from a shared dataset across real papers. §7 names that as future work.
- **Algorithm:** Frozen Qwen3 1.7B/4B/8B and GPT-5-mini; mitigations M0–M3 (source nodes, provenance ids, an instruction to count origins, and collapsing equivalent paths); provenance-aware post-training with GRPO and LoRA on Qwen3-4B (§4–§5).
- **Data:** GraphEcho-Syn, 800 fictional claims, 500/100/200 split, claim-disjoint. SciFact development conversion: 188 claims with gold evidence. Ten claims have multiple evidence documents.
- **Findings read from the arXiv HTML, not re-checked against the PDF:** On the 200-claim static test, redundant-path effects differ by model. Qwen3-4B's path-multiplicity effect is positive (about +7.5 percentage points). Qwen3-8B and GPT-5-mini move in the other direction. Collapsing equivalent paths removes nearly all of the redundant-path sensitivity for Qwen3-4B while leaving a response to distinct origins (Table 7, M3). Trained agents reduce repeated walks and can gain synthetic accuracy, but they cover fewer origins and lose accuracy on the SciFact transfer reported in Table 5.
- **Authors' limitations:** Identical repeated text is a limited form of redundancy. One training seed. Self-reported probabilities are not calibrated. SciFact document IDs are only a proxy.
- **Overlap:** This is the controlled experiment in the proposed pilot: hold content fixed, vary whether extra items are new origins, and require the method not to succeed merely by ignoring evidence.
- **Difference:** Graph agents and identical wording, not a frozen passage list of paraphrases or natural syndication. No three-layer human annotation of news. Preprint.
- **Reproduction:** The construction is specified. Code was not found, so reproduction would be a reimplementation. Not attempted.

### Ross, Koopman, van der Vegt, and Zuccon, arXiv 2026

- **Title:** How retriever redundancy and diversity impact RAG effectiveness.
- **Status:** Preprint, 14 August 2026. [arXiv:2608.13956](https://arxiv.org/abs/2608.13956). **Abstract only in this audit.**
- **Question / method, from the abstract:** Compare retrieved sets that are exact duplicates, LLM paraphrases of one document, or diverse documents, on FictionalQA, so the answer is not in parametric memory.
- **Finding, from the abstract:** Duplicate redundancy and LLM paraphrasing do not significantly improve answer correctness. Diverse documents improve it by 17%–47%, attributed to genre diversity rather than extra answer content.
- **Overlap:** A controlled duplicate-versus-paraphrase test with content controlled.
- **Difference:** The outcome is whether a generator answers correctly, not whether a verifier emits false support. Full method, sample size, and statistics were not read.
- **Reproduction:** Not assessed.

### Byrd, SSRN 2026

- **Title / author:** Source Independence Is a Measurable Property of Evidence. Andre Byrd. SSRN 6903718.
- **Status:** Preprint. Posted 24 June 2026. Not peer-reviewed. [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6903718). DOI recorded on the SSRN page as [10.2139/ssrn.6903718](https://doi.org/10.2139/ssrn.6903718). Five pages. Full text not obtained.
- **Code:** The abstract says the measurement is implemented in Verdict Weight and that the internal mechanism is out of scope. No repository was found in this pass.
- **Claim, from the abstract:** Independence can be measured from provenance alone, without content, models, or ground-truth labels; it is not reducible to one proxy; it is reported on medical imaging and pharmacovigilance; it converts to an effective independent-source count.
- **Dependence:** Claimed to be measured. The estimator was not available to inspect.
- **Level:** Evidentiary records in the two domains named. Not shown, in the abstract, to be natural-language passages.
- **Overlap:** "Agreement is not corroboration" and an effective source count are the proposed RC-Gate idea stated as a measurement claim.
- **Difference that can be supported without the PDF:** Domain and withheld mechanism. **Inference:** an unread 5-page preprint with no disclosed algorithm does not prove a verifier result, and it does block a claim that nobody has proposed measuring independence from provenance.
- **Related unread abstracts:** SSRN 6903278 and SSRN 6728903, same author, same month. Not reviewed.
- **Reproduction:** Not possible from the abstract.

### `pxnkit/lineagerag`, GitHub 2026

- **What it is:** A public repository, "Copy-aware evidence corroboration for offline retrieval-augmented verification." Created 2026-07-25. MIT license. 0 stars at the time of the API read. No paper by this repository was found. It is not Zheng et al., arXiv:2608.16004, which is a different GraphRAG paper.
- **Method, from the README, not from an executed run:** Pairwise logistic probability of shared derivation from publication order, citations, text overlap, SimHash, entity and number overlap, rare-error markers, and URL features. Edges become a directed graph. Families receive a bounded weight, `1 + α log(1 + |f| - 1)`, capped by τ, inside a log-odds verifier. Baselines named in the tree include URL dedup, domain dedup, near-duplicate filtering, and an oracle.
- **Data:** Synthetic cascades described in the README, including paraphrase trees and cross-domain syndication. `docs/originality.md` says synthetic smoke metrics do not establish real-world performance. Result tables were not audited.
- **Overlap:** This is a written design of family-level dependence-aware aggregation with the baselines the pivot calls mandatory.
- **What it does not establish:** A peer-reviewed result, a natural-news finding, or a working system this audit verified.
- **Reproduction:** The repository is public. It was not cloned or run.

### PAGE-RAG and Zhang et al. 2021

PAGE-RAG (Haokun Deng, Xunkai Li, Hongchao Qin, and Rong-Hua Li; arXiv HTML at [arXiv:2608.29753](https://arxiv.org/abs/2608.29753); preprint, submission date not transcribed) promotes multi-hop evidence under a fixed reader budget. The introduction's failure mode is that a graph edge can connect a distractor. That is support versus connectivity, not copy versus independent corroboration.

Zhang, Ives, and Roth, ACL 2021, "What is Your Article Based On? Inferring Fine-grained Provenance," pages 5894–5903, DOI [10.18653/v1/2021.acl-long.458](https://doi.org/10.18653/v1/2021.acl-long.458). **Paraphrase of the abstract:** identify sentences that use external information and infer their source articles on Politi-Prov, built from PolitiFact. The paper distinguishes this from fact-checking. It does not repeat the 2020 voting experiment.

### Zerong et al., Findings of EMNLP 2025

- **Title / authors / venue:** A Systematic Survey of Claim Verification: Corpora, Systems, and Case Studies. Zhaxi Zerong, Chenxi Li, Xinyi Liu, Ju-hui Chen, and Fei Xia. Findings of EMNLP 2025, pages 21452–21474.
- **Status:** Peer-reviewed. DOI: [10.18653/v1/2025.findings-emnlp.1170](https://doi.org/10.18653/v1/2025.findings-emnlp.1170). Repository: [github.com/CLINEEK/EMNLP2025-Claim-Verification-Survey](https://github.com/CLINEEK/EMNLP2025-Claim-Verification-Survey). The repository's paper list was not opened.
- **Search they report, §3:** ACL Anthology, Semantic Scholar, and Google Scholar, query `(fact OR claim) AND (checking OR verification)`, January 2022 through March 2025. 316 papers after deduplication; 198 kept as claim verification.
- **What their conclusion emphasizes:** veracity annotation, limits of the usual pipeline, and claim-decomposition errors. The sections searched did not state a source-dependence agenda.
- **Use in this audit:** The window ends March 2025. This audit's extension past that date is the query log above. It is not a second systematic review.

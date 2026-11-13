# Search protocol and log

**Audit date:** 23 October 2026  
**Scope:** literature-first novelty audit for the proposed RC-Gate dependence question.  
**This is not a systematic review.** It does not re-screen the 198 claim-verification papers in Zerong et al. (Findings of EMNLP 2025) one by one, and it does not claim complete coverage of April 2025–October 2026.

Labels used below:

- **Quotation:** wording taken from a source, with whitespace normalized where a PDF line break split a word. The source location is given.
- **Paraphrase:** a restatement of a source that was opened.
- **Inference:** a conclusion drawn in this audit, not a claim made by the source.

## 1. Databases and sites

Used on 23 October 2026:

| Source | How it was used | Limit |
|---|---|---|
| ACL Anthology HTML and PDF | Primary venue copies for Zhang et al. 2020, HESM 2020, IMRRF 2025, Zerong et al. 2025, Zhang et al. 2021, InteGround 2025 | PDF text extraction splits words across lines. Figure values that were not printed as text were not transcribed. |
| arXiv HTML / abs pages | GraphEcho, Ross et al., PAGE-RAG, and screening of adjacent 2026 preprints | Ross et al. was read at abstract level only. PAGE-RAG was read through the introduction. |
| SSRN abstract pages | Byrd 2026 records | Full PDF was not obtained. |
| eScholarship PDF and LSE repository record | Belkin, Madsen, and de-Wit 2026 | OSF and AsPredicted URLs were not copied out of the PDF. |
| VLDB open PDF | Dong, Berti-Équille, and Srivastava 2009 | Abstract and stated contributions were read; the dependence equations were not re-derived. |
| WWW 2013 PDF | Pasternack and Roth, Latent Credibility Analysis | Read for whether the model already includes source dependence. |
| GitHub repository pages and the GitHub API | HESM, IMRRF, `pxnkit/lineagerag` | IMRRF and LineageRAG code was not executed. |
| Web search | Discovery, citation chasing, and the post-March 2025 extension | Search snippets were not treated as method evidence unless the linked page was opened. |

Not used successfully:

- `export.arxiv.org` API. Six queries for 1 April 2025–23 October 2026 finished with no papers: four returned HTTP 429, and two timed out. A separate single-query fetch also timed out. No result counts from that API are reported.
- Semantic Scholar citation-count API. Not queried. No cited-by totals are reported.
- SSRN full-text delivery for Byrd. Not obtained.
- A manual rescreen of all claim-verification papers published from April 2025 through 23 October 2026. Not done.

## 2. Screening criteria

**Include** a work when it does at least one of the following:

1. verifies or fact-checks a natural-language claim using more than one evidence passage;
2. builds a provenance or lineage graph for a claim or article;
3. filters, clusters, or down-weights redundant or copied evidence;
4. models source dependence, copying, or an effective independent-source count;
5. tests whether repeated evidence changes a model decision while information content is controlled;
6. is a survey whose search window this audit was asked to extend.

**Exclude from the load-bearing comparison,** but record if found:

- generic hallucination detectors with no evidence-dependence claim;
- product or marketing pages that are not papers;
- a second paper that only shares a name with a closer work.

**Publication status** is recorded separately from relevance. A preprint is not described as peer-reviewed.

## 3. Queries

Web-search queries run on 23 October 2026. Result pages were opened only when listed in the log.

1. `Zhang Ives Roth "Who said it, and Why?" Provenance for Natural Language Claims ACL 2020`
2. `EMNLP 2025 systematic survey claim verification 198 studies January 2022 March 2025`
3. `Andre Byrd Source Independence Is a Measurable Property of Evidence SSRN 6903718`
4. `Belkin Madsen de-Wit When agreement looks like copying Bayesian source dependency inference 2026`
5. `IMRRF Integrating Multi-Source Retrieval and Redundancy Filtering NAACL 2025 Li`
6. `Hierarchical Evidence Set Modeling automated fact extraction verification EMNLP 2020 Subramanian Lee`
7. `source dependence copying detection claim verification fact checking natural language 2020..2026`
8. `LLM verifier dependent evidence independent corroboration redundant passages false support 2024 2025 2026`
9. `Dong Berti-Equille Srivastava Integrating Conflicting Data the Role of Source Dependence VLDB`
10. `LineageRAG copy-aware evidence corroboration origin families paper`
11. `"dependency of sources" OR "source dependence" claim verification provenance graph Pochampally LCA`
12. `"independent corroboration" OR "evidential origin" OR "shared origin" fact verification OR claim verification 2025 2026`
13. `GraphEcho Structural Redundancy Evidence Provenance Wang Zhou Fan Zhang arxiv 2609.17695`
14. `InteGround integrative grounding arXiv 2509.16534 venue Ross retriever redundancy 2608.13956 PAGE-RAG 2608.29753`
15. `github ShyamSubramanian HESM license quark233 IMRRF license`

Targeted follow-up page opens, same date:

- ACL PDFs: `2020.acl-main.406`, `2020.emnlp-main.627`, `2025.naacl-long.461`, `2025.findings-emnlp.1170`, `2021.acl-long.458`, `2025.findings-emnlp.732`
- arXiv HTML: `2609.17695`, `2608.16004`, `2609.08943` (screened), `2609.02127` (screened), `2602.18693` (screened), `2608.29753`
- SSRN abstracts: `6903718`, and the related records `6903278` and `6728903` at abstract level
- Belkin PDF: `https://researchonline.lse.ac.uk/id/eprint/140546/1/eScholarship_UC_item_6f6597d3.pdf` and the eScholarship copy
- Dong PDF: `http://www.vldb.org/pvldb/vol2/vldb09-pvldb47.pdf`
- LCA PDF: `https://archives.iw3c2.org/www2013/proceedings/p1009.pdf`
- GitHub API: `https://api.github.com/repos/pxnkit/lineagerag` and `docs/originality.md`
- IMRRF license API: `https://api.github.com/repos/quark233/IMRRF/license` returned 404

Project documents read locally, same date: the v0.3 pivot, pilot protocol v0.2, annotation protocol v0.1, pilot decision record v0.1, pilot-preflight reports, README, final research report v1, and the experiment-index note on Stages 9 and 10. Stage 8 numbers were taken from the final report, which points at `results/summary/ragtruth_factorial_seed_v1/`. Those result files were not recomputed.

## 4. Inclusion and exclusion log

| Date | Query or page | What was retained | Screening note |
|---|---|---|---|
| 2026-10-23 | Zhang, Ives, and Roth, ACL 2020 | Included. Load-bearing. | Full PDF text read for the definition, verification method, datasets, and limitations. Figure 4 bar values were not transcribed. |
| 2026-10-23 | Zerong et al., Findings of EMNLP 2025 | Included as the survey boundary. | Paper-selection section and conclusion read. The 198-paper bibliography was not re-screened item by item. |
| 2026-10-23 | Byrd, SSRN 6903718 | Included as a novelty threat. | Abstract and SSRN record only. |
| 2026-10-23 | Belkin, Madsen, and de-Wit, CogSci 2026 | Included. | Proceedings PDF read, including results and the authors' two interpretations. |
| 2026-10-23 | IMRRF, NAACL 2025 | Included. Load-bearing. | Method, datasets, and Appendix Table 6 prompt read. Python code not executed. |
| 2026-10-23 | HESM, EMNLP 2020 | Included. Load-bearing. | Abstract, motivation, and framework description read. Result-table cells were not transcribed. |
| 2026-10-23 | Dong et al., PVLDB 2009 | Included. Load-bearing for the older dependence method. | Abstract and stated contributions read. |
| 2026-10-23 | Pochampally et al., SIGMOD 2014 | Included at the level cited by Zhang et al. | Abstract read. Full algorithm not re-derived. |
| 2026-10-23 | Pasternack and Roth, WWW 2013 | Included as the voter Zhang et al. plug in. | Conclusion explicitly leaves source dependency to future work. |
| 2026-10-23 | Zhang, Ives, and Roth, ACL 2021 | Included as the provenance follow-up. | Abstract and problem statement read. It infers source articles; it does not add a dependence-aware verifier. |
| 2026-10-23 | GraphEcho, arXiv:2609.17695 | Included. Load-bearing empirical threat. | Abstract, sections 1–7, limitations, and appendix tables read from the arXiv HTML. Not checked cell-by-cell against the PDF. |
| 2026-10-23 | Ross et al., arXiv:2608.13956 | Included as adjacent, abstract-level only. | Duplicate versus paraphrase versus diverse documents for RAG answer correctness. Full text not read. |
| 2026-10-23 | InteGround, Findings of EMNLP 2025 | Included to prevent a construct error. | "Inter-dependent" here means pieces that must be combined. Redundancy is extra non-essential evidence, not a shared origin. |
| 2026-10-23 | PAGE-RAG, arXiv:2608.29753 | Screened. Not the same task. | Introduction read. Provenance here filters connected but non-supporting hops. |
| 2026-10-23 | arXiv:2608.16004, "LineageRAG" | Screened and separated. | GraphRAG evidence-demand grounding. Not the GitHub project of the same name. |
| 2026-10-23 | `pxnkit/lineagerag` | Included as unpublished code, not as a paper. | README and originality note read. Code not run. Created 2026-07-25, MIT, 0 stars. No paper found. |
| 2026-10-23 | arXiv:2609.08943, Fact-Ablated Evaluation | Screened out of the core matrix. | Tests whether a verifier changes when cited evidence is removed, because of parametric knowledge. Different intervention. |
| 2026-10-23 | arXiv:2609.02127, "Stored Is Not Supported" | Screened as adjacent. | Formalizes false corroboration for persistent-agent memory. The end-to-end user study is proposed, not reported as completed. |
| 2026-10-23 | arXiv:2602.18693, dual-perspective verification | Screened out. | Cross-source disagreement and deduplication. Dependence between copies is not the method. |
| 2026-10-23 | Altss and an `iarpa.org` "source independence" page | Not used as scientific prior art. | Web pages, not papers. Institutional authorship of the IARPA URL was not verified beyond the fetched page. |
| 2026-10-23 | ProvenanceGuard, EAEV, CONFACT, and the other works named only in the v0.3 pivot | Not re-audited here. | Listed in `AUDIT_LIMITATIONS.md`. They are not the basis of the decision. |

## 5. Citation chasing that was actually done

Backward, from the opened PDFs:

- Zhang et al. 2020 §4.2 cites Pochampally et al. 2014 for source dependence and Pasternack and Roth 2013 for Simple LCA. Both were opened.
- Zhang et al. 2020 also cites their own 2019 trustworthiness paper. The ACL abstract was read. It estimates source trust and claim credibility. It is not a copied-source discount.
- GraphEcho's references name Ross et al. 2026 and PAGE-RAG. Both arXiv records were opened at the depth stated above.
- Pasternack and Roth 2013 cite earlier truth discovery, including copying detection, and their conclusion says source dependency is future work.

Forward:

- Web search from Zhang et al. 2020 found the authors' ACL 2021 fine-grained provenance paper. That paper was opened.
- No Semantic Scholar cited-by list was downloaded. Later papers may cite Zhang et al. 2020 without appearing in this log.

## 6. Access limits that remain open

These are unresolved, not negative findings:

- Byrd full text, data, and Verdict Weight code.
- Numeric values in Zhang et al. 2020 Figure 4.
- Whether the Zhang et al. 2020 code URL still serves the code.
- Complete cited-by sets for the seed papers.
- An arXiv API census from 1 April 2025 through 23 October 2026.
- Item-level screening of the 198-paper survey bibliography.
- Full text of Ross et al. 2026.
- Execution or result-file audit of `pxnkit/lineagerag`.
- Full-text re-audit of the pivot's other named papers (ProvenanceGuard, EAEV, CONFACT, TRIVIA+, PROBE, and the evidence-sufficiency paper).

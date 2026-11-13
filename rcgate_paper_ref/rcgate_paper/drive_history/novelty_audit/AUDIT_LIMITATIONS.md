# Audit limitations

**Audit date:** 23 October 2026.  
Nothing in this file is a negative result about a paper. Each item is a check that was not completed. The STOP decision does not depend on filling these gaps, and a later reader should not treat them as closed.

## 1. Full texts and code that were not obtained

| Item | What was opened | What remains unknown |
|---|---|---|
| Byrd, SSRN 6903718 | Abstract and SSRN record. Related abstracts 6903278 and 6728903 were seen and not reviewed. | Full text, data, Verdict Weight algorithm, and any evaluation tables. The abstract says the mechanism is out of scope. |
| Zhang, Ives, and Roth 2020, Figure 4 | The prose of §5.2. | The bar values for majority vote and Simple LCA. No accuracy percentage from that figure is used. |
| Zhang et al. 2020 code | The URL printed in footnote 3. | Whether `https://cogcomp.seas.upenn.edu/page/publication_view/901` still serves the code, and under what license. |
| Ross et al., arXiv:2608.13956 | Abstract on the arXiv abs page. | Methods, sample size, statistics, and limitations. The 17%–47% figure is an abstract claim, not a re-computed result. |
| PAGE-RAG, arXiv:2608.29753 | Abstract and introduction from the arXiv HTML. | Experiments, submission date, and whether a later proceedings version exists. |
| Zheng et al., arXiv:2608.16004 | Abstract and introduction. | Enough to separate it from `pxnkit/lineagerag`. Not a full review. |
| `pxnkit/lineagerag` | GitHub API metadata, README, and `docs/originality.md`. | No clone, no test run, no audit of the result tables. The README is a design, not a verified finding. |
| HESM and IMRRF repositories | README and, for IMRRF, the paper's filtering prompt. | Neither codebase was executed. IMRRF has no license file according to the GitHub license API (404). HESM's GitHub page reports MIT. |
| GraphEcho code | Not found in the sections read. | Whether an implementation was released, and whether every HTML table cell matches the PDF. |
| Dong et al. 2009 and Pochampally et al. 2014 | Dong: abstract and the paper's stated contributions. Pochampally: abstract, plus the citation in Zhang et al. 2020. | Equation-level re-derivation and full result tables. |
| Belkin et al. 2026 | Proceedings PDF. | OSF URL and AsPredicted number were not copied out. Stimuli were not downloaded. A proceedings DOI beyond the LSE/eScholarship records was not retrieved. |

## 2. Searches that are incomplete

- The `export.arxiv.org` API census for 1 April 2025 through 23 October 2026 did not return papers. Of six queries, four came back HTTP 429 and two timed out. A separate single-query fetch also timed out. There is no arXiv result count for that window.
- Semantic Scholar was not queried. No cited-by total is reported for any seed paper. Forward chasing was limited to papers found by web search and to references inside opened PDFs.
- Zerong et al. report 198 claim-verification papers from January 2022 through March 2025. Their selection section and conclusion were read. Their bibliography was not screened paper by paper for dependence, provenance, or redundancy. A dependence paper inside that set could have been missed.
- The extension past March 2025 is the query log in `SEARCH_PROTOCOL.md`. It is a keyword search, not a second systematic review.
- Web-search snippets were not used as method evidence unless the linked page was opened.

## 3. Project citations that were not re-audited

The v0.3 pivot names ProvenanceGuard, EAEV, CONFACT, TRIVIA+, PROBE, the evidence-sufficiency paper, News Provenance, Nicholls, FActScore, SAFE, and several others. This audit did not re-open those full texts. They are not load-bearing for the STOP decision. A later revision that cites them as method comparisons has to read them first. Stage 9 of the historical report, as that report states, was also not a systematic review. This audit did not re-litigate Stage 9's hallucination-detector comparisons.

Altss pages and an `iarpa.org` page about source independence were fetched and then set aside. They are not papers. Authorship of the IARPA URL was not verified beyond the fetch.

## 4. Numeric and textual cautions

- GraphEcho table numbers in the other audit files were read from the arXiv HTML rendering of `2609.17695`. They were not checked cell by cell against the PDF. The decision uses the direction of those results (model-dependent effects; collapse is a strong control). It does not depend on a single percentage point.
- PDF extraction splits words across lines. Quotations were rejoined. They are not diplomatic transcriptions of line breaks.
- InteGround's "inter-dependent" evidence and IMRRF's "redundant information" are easy to conflate with source dependence. The matrix records the difference. A summary that drops that difference would misstate the audit.
- `pxnkit/lineagerag` and Zheng et al., arXiv:2608.16004, share a name and are different works.

## 5. Repository limits of this audit

- No model was loaded, no weight was downloaded, no API was called, and no passage was scraped.
- Stage 8 numbers were taken from the final research report. The factorial result files were not recomputed.
- The pilot decision record was not filled in. Doing so would assert a freeze this STOP decision rejects.
- Historical manuscripts, result directories, and untracked files outside `research/novelty_audit/` were not modified.

## 6. Claims this audit therefore does not make

- That the search was exhaustive.
- That Byrd's measurement works, or that it does not work.
- That GraphEcho's HTML tables are a substitute for the PDF.
- That no unread 2026 paper addresses non-identical passage dependence.
- That the implemented RC-Gate system should be rewritten, published, or deleted.

# Audit limitations

**Date:** 23 October 2026.  
These are unchecked items, not negative findings.

## Full text and code

| Item | Opened | Still unknown |
|---|---|---|
| Dubanowska et al. 2025 | Anthology PDF text | Code. Some appendix table cells did not survive extraction and were not used as numbers. |
| Bakman et al. 2025 | Author-hosted PDF and GitHub README | Code not run. The 0.06 PRR figure is the paper's own summary of Table 2, not a recomputation. |
| Han et al. 2025 | Anthology PDF and GitHub README | License. Code not run. Probe AUROCs cited from Table 1 of the extracted text. |
| Chen et al. 2026 | Anthology PDF and the Amazon dataset page | Dataset not downloaded. The Anthology abstract snippet said three noise schemes; the PDF body says four. This audit follows the body. Whether `github.com/Wenbo11/TriviaPlus` and the Amazon repository are the same release was not verified file by file. |
| Fadeeva et al. 2026 | Anthology PDF and DOI HTML | GitHub tree not opened. License unknown. Individual PR-AUC cells were not copied into the decision. |
| HALT-RAG | arXiv HTML method section | Submission date not transcribed. No proceedings version found. Later publication would change the status, not the method description read here. |
| Finch-Zk | Anthology abstract | Methods, splits, and metrics. |
| CCUF | Abstract on the ACM record | Full method. Author list. Whether the record is the final SIGIR paper. |
| AlignScore | Citation inside FRANQ | Full paper not re-read. |
| RAGTruth paper | Local benchmark note, file hashes, and the page range in FRANQ's bibliography | The paper's own detector experiments were not re-read. |
| Niu et al. author spelling | Fadeeva bibliography prints KaShun Shum | The Anthology page was not re-opened to reconcile spellings. |

## Search gaps

- No cited-by census from Semantic Scholar or the arXiv API.
- Forward citations of FRANQ, Han et al., and Dubanowska et al. after their publication dates were not exhaustively listed. A later 2026 paper could still have run the exact four-part protocol. None was found by the queries in `SEARCH_PROTOCOL.md`.
- The previous dependence-audit files were not edited. Their STOP is unchanged. Their unresolved Byrd and Ross items are irrelevant to this decision and were not re-opened.

## Repository limits

- Stage 8 means were read from the final research report. Checkpoints were not rescored.
- `leave_one_generator_out` was read and not executed.
- No model weights were loaded, no API was called, and no corpus was downloaded.
- Tracked application, result, and manuscript files were not modified.

## What this audit does not claim

- That no unread paper has fused some other pair of scores.
- That a full-corpus flat-model evaluation would succeed or fail.
- That FRANQ's win over XGBoost transfers to RAGTruth span overlap.
- That the 800-row negative result is a generator-shift result. It is not.

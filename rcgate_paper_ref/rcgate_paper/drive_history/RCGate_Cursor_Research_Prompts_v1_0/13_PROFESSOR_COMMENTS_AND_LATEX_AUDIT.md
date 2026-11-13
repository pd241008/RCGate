# Prompt 13 — Professor review and Springer compliance audit

Audit the paper draft against the professor's comments and source/result ledger. Make a new version or targeted fixes in the *new* manuscript directory only. Do not modify historical papers.

## Mandatory checklist

1. Abstract is exactly one paragraph, unbolded, no internal paragraph breaks.
2. Official Springer Nature LaTeX template appropriate to the intended venue is used; class files and typography/layout defaults are untouched except documented template-supported settings.
3. Paper has substantive depth, not padding. Every section advances the contribution or evidence.
4. Related-work comparison table includes paper title, year, authors, method/feature inputs, datasets/results where relevant, limitations and direct relevance/difference for RC-Gate.
5. At least one prior algorithm is explained at implementation/mathematical level, with a source citation and a clear comparison to RC-Gate.
6. Every variable (e.g., alpha, s, q, k, any newly introduced symbols) is defined on first use. Include notation table if needed.
7. Dataset section appears immediately after Related Work.
8. Every figure term and pipeline stage is explained; no unexplained ReLU, NLI, RC-Gate, sigmoid, embeddings, AP, AUROC or ECE. Only mention ReLU if actually used in the described architecture.
9. Figures and model comparisons are legible and data-derived. Captions state units, splits, uncertainty and N.
10. The method explains what is built and what its score means in practice.
11. A8 is explicitly marked unavailable/unevaluated if the legacy variants are reported and judge outputs are absent.
12. Future work is constructive, concrete and accurately scoped.
13. No unresolved citation keys, invented references, unexplained abbreviations, broken figures, overfull boxes or missing files. Investigate and fix issues rather than suppress warnings blindly.
14. Data and label statements reflect actual RAGTruth licenses/access. Declarations, authorship, author order, emails, funding, conflict statements and ethics language must be confirmed by authors; unresolved items remain marked for author input, never invented.
15. Every numeric result matches the results ledger. Separate statistical significance, effect size and practical impact. Negative results remain.
16. Explicitly compare against Temporal Multi-Signal Fusion, UAI 2026 multi-agent risk control, Evidence Graph Consistency, GASP, FRANQ, RLSeek and other verified closest papers, without claiming a missing feature unless full text/code supports it.

## Process

Create a compliance matrix with comment, evidence in manuscript (section/page/line), status, correction and unresolved author decision. Apply supported corrections. Build PDF with the official template, render/check every page and inspect figures/tables. Do not manually change template margins/font sizes. Keep the source, PDF, bibliography and build log together in the new directory.

## Deliverable

`PROFESSOR_COMPLIANCE_AUDIT.md`, corrected manuscript version, build log and exact file diff. Report any remaining blockers for author/professor decision. Wait for Prompt 14.

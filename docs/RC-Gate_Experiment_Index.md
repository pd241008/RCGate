# RC-Gate experiment index

**October 10, 2026.** This file maps the project’s documents. It does not report a new measurement.

## Authoritative account

The current scientific account is [`RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md) (final research report, version 1, October 2026). It records the architecture, the hypotheses, the protocols, the Stage 8 results, and the limitations. Publication readiness for a conference or journal has not been established.

The repository overview that points here is [`README.md`](../README.md).

## How to read the numbers

Historical metrics are not current estimates. That includes the milestone log, the original M6 postmortem, the near-0.45 weight remark in ADR-001, [`results/summary/ragtruth.md`](../results/summary/ragtruth.md), and [`results/summary/synthetic.md`](../results/summary/synthetic.md).

The Stage 8 repeated fits are not independent datasets. Every Stage 8 cell uses one corrected 800-sentence RAGTruth slice (134 questions, seed-0 table). Twenty question-grouped splits crossed with three model initialisations are repeated partitions and initialisations of that one pool. The sample standard deviation of those fits describes spread in the grid. It is not a confidence interval.

Protocols differ. A cell from one protocol is not pooled with a cell from another. Table 6 of the final report is the protocol list. Table 7 is the principal result: mean test AUROC 0.6280 (A0), 0.6839 (A4), and 0.5717 (A7); mean paired A7 minus A4 is −0.1122.

## Canonical result: Stage 8 factorial seeds

| File | What it holds |
| --- | --- |
| [`results/summary/ragtruth_factorial_seed_v1/report.md`](../results/summary/ragtruth_factorial_seed_v1/report.md) | Stage 8 report. Principal repeated-fit analysis |
| [`results/summary/ragtruth_factorial_seed_v1/report.json`](../results/summary/ragtruth_factorial_seed_v1/report.json) | Same run, machine-readable |
| [`results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv`](../results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv) | Per-cell metrics |
| [`results/summary/ragtruth_factorial_seed_v1/paired_deltas.csv`](../results/summary/ragtruth_factorial_seed_v1/paired_deltas.csv) | Paired AUROC differences |
| [`results/summary/ragtruth_factorial_seed_v1/provenance.json`](../results/summary/ragtruth_factorial_seed_v1/provenance.json) | Run provenance, including the recorded git HEAD |
| [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md) | Later check of that provenance against commit `6d3ef70` and the local artifacts. It does not replace the run record |

## Corrected integrity and statistical reports

These repairs precede Stage 8. Their point estimates are historical relative to Table 7.

| File | What it holds |
| --- | --- |
| [`results/summary/ragtruth_corrected_integrity_v1/VERDICT.md`](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md) | Stage 4 verdict on sentence alignment and prompt antecedents |
| [`results/summary/ragtruth_corrected_integrity_v1/report.md`](../results/summary/ragtruth_corrected_integrity_v1/report.md) | Stage 4 refit on the corrected tables, legacy split, original estimator |
| [`results/summary/ragtruth_corrected_integrity_v1/comparison.md`](../results/summary/ragtruth_corrected_integrity_v1/comparison.md) | Old versus corrected means under that same estimator |
| [`results/summary/ragtruth_corrected_integrity_v1/statistical_issues.md`](../results/summary/ragtruth_corrected_integrity_v1/statistical_issues.md) | Statistical defects left untouched in the Stage 4 run |
| [`results/summary/ragtruth_corrected_stats_v1/report.md`](../results/summary/ragtruth_corrected_stats_v1/report.md) | Stage 5 question-grouped intervals on the Stage 4 checkpoints. No refit |

Two later protocols sit between those repairs and the canonical grid. They are not additional independent replications.

| File | What it holds |
| --- | --- |
| [`results/summary/ragtruth_split_corrected_v1/report.md`](../results/summary/ragtruth_split_corrected_v1/report.md) | Stage 6 group-stratified split, three overlapping tables |
| [`results/summary/ragtruth_multi_seed_v1/report.md`](../results/summary/ragtruth_multi_seed_v1/report.md) | Stage 7, 20 splits of the seed-0 table, model seed tied to the split seed |

## Historical original results

The original three-seed RAGTruth summary remains in place. Its column headed “AUROC (95% CI)” prints the mean AUROC, and its paired comparison stores a bootstrap fraction under a name that reads like a hypothesis test. Those figures belong to the original protocol.

| File | What it holds |
| --- | --- |
| [`results/summary/ragtruth.md`](../results/summary/ragtruth.md) | Original M6 markdown summary |
| [`results/summary/ragtruth.json`](../results/summary/ragtruth.json) | Original aggregate |
| [`results/summary/ragtruth/`](../results/summary/ragtruth/) | Original per-variant run directory |
| [`results/summary/ragtruth_historical_freeze/MANIFEST.json`](../results/summary/ragtruth_historical_freeze/MANIFEST.json) | Freeze manifest for that original directory |

## Synthetic-only results

[`results/summary/synthetic.md`](../results/summary/synthetic.md) is a mechanism check on tables with a reliability pattern written into the generator. The file’s own banner already limits those numbers to the planted world. The “95% CI” column is the same historical renderer as in the original RAGTruth summary. [`results/summary/synthetic.json`](../results/summary/synthetic.json) is the aggregate for that run. A4 still ranks higher than A7 on the synthetic pooled mean recorded there.

[`results/summary/smoke_A7_explain.md`](../results/summary/smoke_A7_explain.md) is a smoke explanation dump. It is not an evaluation.

## Stage 9 literature audit and Stage 10 feasibility audit

Stages 9 and 10 were read-only documentation audits. They did not add a fitted-model directory under `results/summary/`.

The Stage 9 literature audit is recorded in Section 2 and Section 11 of the final report. It checks the proposal and the initial paper draft against neighbouring papers. It is not a systematic review. Bibliographic items the audit left open are marked unresolved in Section 11.

The Stage 10 feasibility audit is recorded in Section 4.4 of the final report. It inventories the official RAGTruth release and applies a pre-specified support rule (at least 30 training positives and 15 official-test positives in a generator-by-type cell). Under that rule the official QA data do not adequately identify the proposed reliability surface. No full-scale feature build or model fit was performed.

Neither audit has a standalone Markdown file in this repository. The session views that accompanied them live outside the git tree, under the local Cursor project canvases `rcgate-novelty-audit.canvas.tsx` (Stage 9) and `ragtruth-feasibility.canvas.tsx` (Stage 10). The repository record of both audits is the final report.

## Notes on documents the final report supersedes

These files keep their original wording. Each one now carries a status note dated October 10, 2026.

| Document | What the original text still says |
| --- | --- |
| [`DECISIONS.md`](../DECISIONS.md) | Milestone log, including the original paired interval, `p=0.415`, and the inverted-generator result described as the strongest result in the project |
| [`docs/postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md`](postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md) | Original means A4 0.740 and A7 0.631, and the retired `p = 0.415` wording |
| [`docs/adr/001-metadata-only-gate.md`](adr/001-metadata-only-gate.md) | The metadata-only constraint, which still holds, together with “interpretable by construction” and the near-0.45 weight remark |

## Preserved source documents

The original proposal, the user guide, and the initial paper draft were left unchanged. The final report, Section 8.5, already records where they disagree with the repository.

| Document | Status |
| --- | --- |
| [`RC-Gate_Project_Proposal.docx`](../RC-Gate_Project_Proposal.docx) | Preserved. Not the experimental record |
| [`RC-Gate_UserGuide.pdf`](../RC-Gate_UserGuide.pdf) | Preserved. The 229-parameter count matches the synthetic roster |
| [`RC Gate_Intial_Research Paper Draft.pdf`](<../RC Gate_Intial_Research Paper Draft.pdf>) | Preserved. Not a results paper |

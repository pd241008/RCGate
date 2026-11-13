# Search protocol

**Date:** 23 October 2026.  
**Question under audit:** whether reliability-conditioned fusion of external cross-model agreement and evidence-grounding signals improves RAGTruth-style hallucination detection under held-out generator, task, and source shifts, beyond strong simple baselines.  
**Out of scope:** the source-dependence programme stopped in `research/novelty_audit/`. Those files were not edited.

**Quotation** is source wording with PDF line breaks normalized. **Paraphrase** restates an opened source. **Inference** is this audit.

## Sources used

| Source | Use | Limit |
|---|---|---|
| ACL Anthology PDF/HTML | Dubanowska et al. 2025, Bakman et al. 2025, Han et al. 2025, Chen et al. 2026, Fadeeva et al. 2026, Finch-Zk abstract | Figure cells that did not survive text extraction were not transcribed. |
| arXiv HTML | HALT-RAG; Dubanowska HTML used only to confirm the Anthology text | HALT-RAG venue beyond arXiv was not found. |
| GitHub pages | Bakman code, Han code, TRIVIA+ release, FRANQ code link, RAGTruth link | Repositories were not cloned or run. |
| This repository | Gate, experts, signals, splits, RAGTruth benchmark note, final research report | Stage 8 numbers were not recomputed. |
| Web search | Discovery and citation chasing | Snippets are not method evidence unless the page was opened. |

`export.arxiv.org` was not queried in this pass. The previous audit's API batch returned HTTP 429 and timeouts.

## Queries run on 23 October 2026

1. `Dubanowska Representation-based Broad Hallucination Detectors Fail to Generalize Out of Distribution Findings EMNLP 2025 code`
2. `Bakman Reconsidering LLM Uncertainty Estimation Methods in the Wild ACL 2025 code`
3. `Han Simple Factuality Probes Detect Hallucinations Long-Form Findings EMNLP 2025 code`
4. `Chen TRIVIA+ Rethinking Evaluation LLM Hallucination Detection ACL 2026 code`
5. `Fadeeva FRANQ Faithfulness-Aware Uncertainty Quantification RAG Findings ACL 2026 code`
6. `cross-model agreement NLI evidence fusion hallucination detection RAG leave-one-generator-out`

Pages opened from those queries:

- https://aclanthology.org/2025.findings-emnlp.952.pdf
- https://aclanthology.org/2025.acl-long.1429/ and the author-hosted PDF
- https://aclanthology.org/2025.findings-emnlp.880.pdf
- https://aclanthology.org/2026.acl-long.680.pdf
- https://aclanthology.org/2026.findings-acl.338.pdf and the DOI HTML
- https://arxiv.org/html/2509.07475 (HALT-RAG)
- https://aclanthology.org/2025.emnlp-industry.139/ (Finch-Zk abstract)
- https://dlnext.acm.org/doi/10.1145/3805712.3809846 (CCUF abstract only)
- https://github.com/duygunuryldz/uncertainty_in_the_wild
- https://github.com/JThh/fact-probe
- https://github.com/amazon-science/hallucination-benchmark-trivialplus
- https://github.com/stat-ml/rag_uncertainty (linked by the FRANQ paper; the tree was not opened)

Local files read: `RCGate_Gap_Alignment_Proposal_v1_0.md`; `rcgate/models/gate.py`, `rcgate.py`, `experts.py`, `variants.py`; `rcgate/signals/evidence.py`, `cross_model.py`; `rcgate/data/schema.py`, `splits.py`, `ragtruth.py`; `data/benchmarks/RAGTruth.md`; the final research report's Stage 8 and Stage 10 sections as already used in the prior audit. The prior STOP files were listed and not rewritten.

## Inclusion

Include a work if it detects hallucinations or uncertainty, fuses scores, conditions one score on another, or evaluates generator, task, or dataset shift. Record publication status separately.

Exclude from the load-bearing comparison: product white papers, and any method whose only overlap is the word "fusion."

## Screening log

| Date | Work | Decision |
|---|---|---|
| 2026-10-23 | Dubanowska et al., Findings of EMNLP 2025 | Load-bearing. Internal detectors, RAGTruth task-rate confound, cross-task and cross-dataset near chance. |
| 2026-10-23 | Bakman et al., ACL 2025 | Load-bearing. Threshold shift and UE ensembling. No NLI grounding panel. |
| 2026-10-23 | Han et al., Findings of EMNLP 2025 | Load-bearing. Hidden-state probes, including transfer to other generators' text. |
| 2026-10-23 | Chen et al., ACL 2026, TRIVIA+ | Load-bearing as a dataset, not as a fusion method. |
| 2026-10-23 | Fadeeva et al., Findings of ACL 2026, FRANQ | Closest conditional-fusion method. Different inputs and target. |
| 2026-10-23 | HALT-RAG, arXiv:2509.07475 | Adjacent. Calibrated NLI ensemble meta-classifier. Preprint. |
| 2026-10-23 | Finch-Zk, EMNLP Industry 2025 | Abstract only. Cross-model consistency without external evidence. |
| 2026-10-23 | CCUF, SIGIR record | Abstract only. Cross-model consistency calibrates uncertainty for answer selection. |
| 2026-10-23 | RAGTruth local record and Niu et al. citation | Dataset audit. The detector section of the RAGTruth paper was not re-read in this pass. |
| 2026-10-23 | Historical A0–A7 | Repository finding. Not a new experiment. |

## Citation chasing actually done

- FRANQ's related-work section names Lookback Lens, ReDeEP, RAGTruth, and AlignScore. ReDeEP is the method Dubanowska re-evaluates. AlignScore is FRANQ's faithfulness model. Those two links were followed by reading Dubanowska and the FRANQ method section.
- Dubanowska cites Niu et al. 2024 and reports per-task RAGTruth rates. The page range for Niu et al. used here is the one printed in FRANQ's bibliography (10862–10878).
- Bakman's code README lists the four deployment questions matching the paper. The code was not executed.
- No Semantic Scholar cited-by list was downloaded.

## Not done

- Item-level forward-citation census.
- Execution of any linked repository.
- Re-reading the RAGTruth paper's own detector tables.
- Full text of CCUF and Finch-Zk.

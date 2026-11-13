# Search log

**Date:** 23 October 2026.  
**Repository at start.** Branch `review/rcgate-handoff-v1`, HEAD `bf9db7dcff47e9e2e3e813567684a42155cf20d0`. `git status --short` showed 740 untracked paths. Untracked roots were `research/`, manuscript folders, and `results/`. Nothing was staged, cleaned, reset, checked out, stashed, committed, or pushed. Historical audits and results were not edited.

This log records what was opened. The scientific conclusions are in `COMPETITOR_MATRIX.md` and `POSITIONING_AND_LIMITATIONS.md`.

## Files read and not modified

- `research/rcgate_shift_audit/`: `GO_NO_GO_DECISION.md`, `CLOSEST_PRIOR_ART.md`, `SIGNAL_FUSION_MATRIX.md`, `SEARCH_PROTOCOL.md`, and the start of `REFERENCES.bib`.
- `research/novelty_audit/`: `GO_NO_GO_DECISION.md`, `CLOSEST_PRIOR_ART.md`, and the start of `SEARCH_PROTOCOL.md`.
- `rcgate/signals/cross_model.py`, lines 1–80, to fix the meaning of the local peer features. Those features compare a claim with other generators' answers. They are repository code, not a published result.

## Queries on 23 October 2026

1. `SAC3 black-box cross-model consistency hallucination detection EMNLP 2023`
2. `Finch-Zk EMNLP Industry 2025 black-box consistency framework hallucination`
3. `Temporal Multi-Signal Fusion for Token-Level Hallucination Detection arXiv 2608.18115`
4. `Kostka Chudziak Controlling Uncertainty and Hallucination Risk in Multi-Agent Fact Verification UAI 2026`
5. `Evidence Graph Consistency in RAG arXiv 2606.06748 hallucination`
6. `GASP Detecting Hallucinations in RAG through Grounding-Aware Sensitivity by Perturbation arXiv 2607.04223`
7. `RLSeek ACL 2026 hallucination RAG detection`
8. `RAGTruth Niu Wu Ning Ramakrishnan Wang 2024 hallucination corpus github`  
   The author string in that query was wrong. The opened paper's author list is Cheng Niu, Yuanhao Wu, Juno Zhu, Siliang Xu, Kashun Shum, Randy Zhong, Juntong Song, and Tong Zhang. The GitHub README uses a different author order, with Wu first.
9. `RAGTruth cross-model consistency same source responses hallucination span NLI incremental`
10. `SelfCheckGPT versus NLI entailment RAG hallucination span incremental value peer responses`
11. `site:aclanthology.org RAGTruth hallucination detection methodologies prompt-based GPT-4 finetune Niu 2024`
12. `Fadeeva FRANQ Faithfulness-Aware Uncertainty Quantification AlignScore XGBoost findings ACL 2026 cross-model`
13. `Bakman Reconsidering LLM Uncertainty Estimation Methods in the Wild ACL 2025 site:aclanthology.org cross-model NLI RAGTruth`
14. `Dubanowska Representation-based Broad Hallucination Detectors Fail to Generalize Findings EMNLP 2025 RAGTruth naive classifier`
15. `"other models" OR "cross-model agreement" RAGTruth sentence NLI entailment incremental AUROC hallucination span`

`export.arxiv.org` and the Semantic Scholar citation API were not queried. Snippets were not treated as method evidence unless the linked page was opened.

## Pages opened

Full text, or a long extract of the full text, was saved and read for:

- SAC³: `https://arxiv.org/html/2311.01740` and `https://aclanthology.org/2023.findings-emnlp.1032.pdf`
- Finch-Zk: `https://aclanthology.org/2025.emnlp-industry.139.pdf` and `https://arxiv.org/html/2508.14314`
- Itkin: `https://arxiv.org/html/2608.18115` and `https://arxiv.org/pdf/2608.18115.pdf`
- Kostka and Chudziak: `https://raw.githubusercontent.com/mlresearch/v337/main/assets/kostka26a/kostka26a.pdf`
- Shen: `https://arxiv.org/html/2606.06748v2` and `https://arxiv.org/html/2606.06748`
- GASP: `https://arxiv.org/pdf/2607.04223.pdf`, `https://arxiv.org/abs/2607.04223`, and `https://arxiv.org/html/2607.04223`
- RLSeek: `https://aclanthology.org/2026.acl-long.1492.pdf`
- RAGTruth: `https://arxiv.org/html/2401.00396v2`, `https://aclanthology.org/2024.acl-long.585.pdf`, and `https://github.com/ParticleMedia/RAGTruth/blob/main/README.md`
- FRANQ: `https://doi.org/10.18653/v1/2026.findings-acl.338` and `https://arxiv.org/html/2505.21072v3`. The Anthology PDF extract that returned was an appendix fragment, including D.2, not a complete re-read.
- Bakman et al.: `https://aclanthology.org/2025.acl-long.1429.pdf` and the Anthology HTML record
- Dubanowska et al.: `https://arxiv.org/html/2509.19372` and `https://aclanthology.org/2025.findings-emnlp.952.pdf`
- SelfCheckGPT, additional: `https://arxiv.org/html/2303.08896v3`

Search hits that were not opened as full text:

- `https://github.com/intuit/sac3` (snippet)
- `https://github.com/YehudaItkin/temporal-hallucination-detection` (snippet)
- `https://github.com/drbouke/GASP` (snippet; MIT stated on that snippet)
- `https://doi.org/10.5281/zenodo.20932843` (EGC code record snippet)
- `https://proceedings.mlr.press/v337/kostka26a.html` (record; the PDF was the text used)
- `https://firish.github.io/rag-rack/blog/03_verified_rag/` and `https://github.com/firish/rag-rack` (snippets only; excluded)
- LettuceDetect arXiv HTML, RAGChecker PDF, and a SemEval-2025 SelfCheckGPT variant PDF were returned by search. They were screened as adjacent grounding or same-model-consistency work and were not load-bearing for the peer-panel question.

## Screening decisions

| Work | Decision |
|---|---|
| SAC³ | Load-bearing. Cross-model consistency, no evidence, no RAGTruth spans. |
| Finch-Zk | Load-bearing. Cross-model consistency, cost table, zero external knowledge. |
| Bakman et al. | Load-bearing as a negative. One-model uncertainty ensembling. No RAGTruth grounding panel. |
| Dubanowska et al. | Load-bearing as an evaluation constraint. Task-rate confound and OOD failure of internal detectors. |
| Itkin | Load-bearing. RAGTruth token fusion of text, NLI, and surprisal. No peer responses. Generator leave-one-out does not describe source removal. |
| Kostka and Chudziak | Load-bearing partial overlap. Entailment score penalized by ensemble deviation. Different label, agents, and metric. |
| Shen | Load-bearing negative. Evidence-graph similarity, not peer answers. QA response labels. Model-family reversal. |
| GASP | Load-bearing. Grounding versus same-scorer consistency as alternatives on a RAGTruth sentence sample. Not a nested peer increment. |
| FRANQ | Load-bearing negative for the peer feature. Faithfulness-conditioned uncertainty of one generator. Factuality label. |
| RLSeek | Load-bearing negative. Evidence-quoting span detector. No peer panel. |
| RAGTruth paper and README | Corpus and original detector section. Six responses exist. The detector section does not use them as features. |
| SelfCheckGPT | Additional. Defines the sampling baseline used by RAGTruth and by GASP. |
| `rag-rack` blog | Excluded. Not a paper. Dual NLI, not peer responses. Numbers not used. |
| HALT-RAG, CCUF | Not re-opened. Prior shift audit stands: NLI fusion, and an abstract-only consistency calibrator. |

## Code

No repository was cloned. No detector, notebook, or evaluation script was executed. No model was loaded. No corpus file was written.

## Not accessed

- A forward-citation list for each required paper.
- Finch-Zk, RLSeek, and Kostka and Chudziak source code. None was found in the opened results.
- The FRANQ code repository. The shift audit had already recorded the link and had not run it.
- CCUF full text.
- Byrd's SSRN full text. Out of scope for this question; the dependence STOP already records it as abstract-only.
- Item-level verification that Itkin's training split leaks sibling responses. The paper does not specify the grouping, so the leak was not asserted.

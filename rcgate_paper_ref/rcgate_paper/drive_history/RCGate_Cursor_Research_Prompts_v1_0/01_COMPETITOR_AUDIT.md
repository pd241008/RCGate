# Prompt 01 — Final competitor audit for the fixed RC-Gate question

Work in the current RC-Gate repository. This is a focused competitor audit, not a fresh brainstorm. **Do not rename the project or replace the fixed research question with a different project.** The prior source-dependence programme remains STOP.

## Fixed research question

For a target RAG-generated sentence, does agreement information derived from other model responses to the same source/query provide incremental predictive information about the target sentence's human-annotated hallucination span, beyond direct evidence-grounding signals; how does that increment vary by generator and task, and is it worth its additional compute/inference burden?

## Tasks

1. Read `research/rcgate_shift_audit/` and the most recent `research/novelty_audit/` records without modifying either historical audit.
2. Use scholarly web tools and official paper pages to inspect, as closely as access allows, at minimum:
   - SAC³, EMNLP Findings 2023: black-box cross-model consistency.
   - Finch-Zk, EMNLP Industry 2025: black-box consistency framework.
   - Bakman et al., ACL 2025: uncertainty-score combination and distribution shifts.
   - Dubanowska et al., EMNLP Findings 2025: OOD failures of representation-based detectors.
   - Temporal Multi-Signal Fusion for Token-Level Hallucination Detection (arXiv:2608.18115, 2026).
   - Kostka & Chudziak, “Controlling Uncertainty and Hallucination Risk in Multi-Agent Fact Verification,” UAI/PMLR 2026.
   - Evidence Graph Consistency in RAG (arXiv:2606.06748, 2026).
   - GASP, “Detecting Hallucinations in RAG through Grounding-Aware Sensitivity by Perturbation” (arXiv:2607.04223, 2026).
   - FRANQ, ACL Findings 2026.
   - RLSeek, ACL 2026.
   - RAGTruth original paper and official repository.
   - Additional closest work found by backward and forward citations.
3. For each closest competitor, inspect full text and code when available. Record task, labels, granularity, feature inputs, whether it uses multiple generated answers, evidence availability, data, split design, held-out generators/tasks, baseline strength, calibration, cost and limitations. Abstract-only sources must be marked abstract-only.
4. Answer narrowly: has the **conditional incremental value of peer response agreement over target-sentence evidence-grounding signals**, using same-source/query peer responses and RAGTruth-like span labels, already been evaluated with leakage-safe source/query and held-out-generator/task splits plus peer-count cost analysis?
5. If a paper substantially covers it, do not hide that fact. Preserve the direction as requested, but specify the maximum defensible scope (e.g., a careful replication/extension) and clearly flag that novelty/publication prospects are weak. Do not declare novelty just because a study's wording differs.
6. Write under `research/rcgate_conditional_consensus/`:
   - `COMPETITOR_MATRIX.md`
   - `POSITIONING_AND_LIMITATIONS.md`
   - `SEARCH_LOG.md`
   - `REFERENCES.bib`
7. Record exact queries, URLs, dates, papers opened, papers not accessed and whether code actually ran. Citations must be checkable.

## Safety

Read-only repository inspection, plus the four new audit files only. No model inference, downloads, corpus collection, code modifications, score runs, commits or pushes. Start with Git status; preserve all untracked files.

## Completion report

Return the strongest overlap found, the remaining defensible distinction if any, unresolved sources, files written and exact final Git status. Then stop and wait for Prompt 02.

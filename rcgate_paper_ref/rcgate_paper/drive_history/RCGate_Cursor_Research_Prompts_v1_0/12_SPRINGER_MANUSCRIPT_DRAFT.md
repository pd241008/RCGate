# Prompt 12 — Draft the research paper from verified results

Use only the approved research protocol, audited prior-art matrix, results ledger, figure/table index and limitations audit. Do not invent or backfill missing results. The old source-dependence STOP remains historical and must not be rewritten as a success.

## Paper purpose

Write an academically substantive paper under the fixed project name **RC-Gate**. The contribution is the conditional-value and cost evaluation of peer-model answer agreement given direct evidence-grounding signals for RAG hallucination-span detection, as far as—and only as far as—the verified findings support.

## Required structure

1. Title and authors (use placeholders where author order, corresponding email or exact affiliations are unconfirmed; never invent them).
2. Abstract: a **single paragraph**, no bold, no internal paragraph breaks. State problem, exact contribution, data/method, strongest measured result with uncertainty, limitations and significance. Do not claim the best result if it is exploratory.
3. Introduction: practical motivation, precise research question, why current evidence is insufficient, contributions as numbered clear claims.
4. Related Work: substantial method-level comparison table containing paper title, year, authors, inputs/features, method, datasets/evaluation and relevance/difference to RC-Gate. Discuss closest competitors accurately and explicitly note overlap.
5. Dataset and Labels immediately after Related Work: dataset provenance, complete response/span annotations, transformation to the chosen prediction unit, annotation types, data counts and class prevalence, generator/task/source panel, licenses/terms, split design and leakage controls.
6. Task Definition and Notation: define every symbol at first use. Add a notation table for symbols such as claim/sentence, context/evidence, peer set, grounding score, agreement score and label. Explain the output target and what a score can and cannot mean.
7. Method: explain the computation in beginner-accessible order; feature definitions, equations, input/output shapes, peer response matching, NLI direction/aggregation, missing data, caching, calibration, baseline training and model settings. Give at least one prior algorithm a detailed, accurate explanation and distinguish it from RC-Gate.
8. Experimental Setup: exact split procedures, hardware/software, seeds, baselines, training/validation/test policy, metrics, statistical tests, threshold rules and cost accounting.
9. Results: primary paired comparison first, then generator/task generalization, ablations, calibration/coverage, compute/cost and error analysis. Integrate figures/tables with explanations; do not dump unexplained graphics.
10. Discussion: interpret what the results imply, alternative explanations and model-specific reversals.
11. Limitations and Threats to Validity: RAGTruth age/domain, six generator panel, pseudo-independent samples, span-to-sentence projection, signal extractor errors, no universal factual-truth guarantee, cost-accounting constraints, external generalization and prior-work limitations.
12. Conclusion: factual summary, no overclaim.
13. Constructive Future Work: precise next experiments and data needed, not vague promises or wording such as “what a later experiment would need.”
14. Declarations and references as required by the chosen Springer journal/template.

## Professor's requirements

- Use the official Springer Nature LaTeX template that matches the intended venue and its class/style; obey default page dimensions, fonts, margins and heading rules. Do not hand-edit layout to force page counts. If target venue is not known, use the official general Springer Nature journal template and clearly mark venue-dependent fields.
- Abstract is a single unbolded paragraph.
- Related-work table must compare methods and relevance, not just list citations.
- Explain symbols and abbreviations when first introduced; add notation and acronym/glossary tables where helpful.
- Dataset section immediately follows Related Work.
- Explain every diagram term such as NLI, entailment, contradiction, AP, AUROC, ECE, and RC-Gate. If the legacy A7 gate is diagrammed, explain embeddings, linear experts, gate logits and sigmoid/ReLU only if actually used by that diagram; do not draw a fictitious architecture.
- Explain in plain terms what the system outputs. A hallucination-risk score is not automatically a real-world probability. Explain the score's target and calibration evidence.
- Show fair model comparisons, meaningful numerical/visual evidence, uncertainty and ablations.
- If A0–A8 are discussed, explain that A8 is unavailable/unevaluated where judge outputs are absent. Do not invent its metric.
- No artificial padding; depth must come from methods, auditability, analysis and results.
- All funding, conflict-of-interest, ethics, consent and data availability statements must be true. Do not invent author order, emails, approvals or claims of public availability.

## Writing quality

Use precise, natural academic prose reflecting what experiments actually established. Do not optimize for AI-detector scores or disguise authorship; prioritize original analysis, transparent citations and author verification.

## Deliverables

Create manuscript source, figures, tables, bibliography and build instructions under a new directory (e.g. `RCGate_Conditional_Consensus_Paper/`) without modifying historical manuscripts. Compile with the official template and check citations. Report build results. Wait for Prompt 13.

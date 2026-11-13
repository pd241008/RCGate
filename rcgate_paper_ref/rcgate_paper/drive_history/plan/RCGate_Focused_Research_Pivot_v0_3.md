# RC-Gate: Focused Research Pivot and Prior-Art Audit

**Version:** 0.3  
**Prepared:** 23 October 2026  
**Status:** Revised after external methodological review; focused scoping audit and experimental proposal; **not** a validated novelty claim or final method specification  
**Project identity:** RC-Gate retained; historical model architecture/results remain unchanged

---

## Executive decision

The previous blueprint was too broad. It bundled claim truth, evidence sufficiency, source provenance, source credibility, conflict resolution, freshness, calibration, abstention, benchmarking, a multi-model comparison product, and a human-use study. Those are related but distinct research questions. The project must not attempt to claim all of them as one contribution.

### Revised centre of gravity

> **When a factual claim is evaluated using several retrieved passages, does a verifier mistake repeated or shared-origin information for independent corroboration—and can claim-specific evidence-origin modelling reduce that error beyond simple deduplication and existing redundancy filters, without suppressing genuinely independent corroboration?**

This is the **candidate research question**, not an established gap. The literature check so far shows that redundancy filtering, hierarchical evidence aggregation, source attribution, and perturbation-based robustness are already studied. The remaining possible distinction is narrower: *claim-specific dependence in the underlying evidential origin*, separated from surface text similarity and from whether a claim is assigned to the correct named source. We must investigate whether that distinction is already solved before implementing a new algorithm.

### Three tracks, now one programme

1. **Scientific core — a narrowly defined evidence-dependence intervention.** If the pilot supports it, implement a dependence-aware aggregation method. A learned gate is optional; the method must be chosen by evidence rather than preserved for branding.
2. **Evaluation contribution — a paired source-dependence challenge set and study.** Keep claim truth separate from evidence status and evidence-origin labels. Test natural as well as controlled cases. A new benchmark is only a contribution if its annotations and coverage add something not available in current benchmarks.
3. **Practical demonstrator — RC-Gate Evidence Auditor.** Show claims, passages, source relations, uncertainty and verdict rationale; optionally compare generating models under the same frozen verification protocol. This is a practical deliverable, not by itself the research novelty. A human-benefit claim requires a separately designed human study and is out of scope for the first paper unless the core experiment succeeds early.

**Primary recommendation:** do not rewrite the manuscript, build the full product, or train a new model yet. Complete the close-prior-art audit and run a small, human-checked feasibility pilot. The pilot should be allowed to kill the idea.

---

## 1. What is already established: focused prior-art matrix

The table below records the specific overlap found in this first focused audit. It is deliberately cautious: “not the same question” does not mean “novel”; the remaining distinction must be checked in full text, code, datasets and citation chains.

| Work | Venue / year | What the work does | Overlap with proposed RC-Gate | Current implication |
|---|---|---|---|---|
| **Source Independence Is a Measurable Property of Evidence** — Andre Byrd | SSRN preprint, posted June 2026; non-peer-reviewed status | Claims to measure source independence from provenance and derive an effective count of independent sources. The abstract argues that dependence cannot be reduced to one simple proxy. [SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6903718) | Directly challenges the premise that source-independence measurement is an open idea. | High-priority novelty threat. Full text, operational definitions, data, code and independent verification of claims have not yet been reviewed; do not accept the abstract's claims as established results. |
| **When agreement looks like copying: Testing a Bayesian model of source dependency inference** — Belkin, Madsen & de-Wit | 2026 repository/working-paper record; publication status to verify | A registered human study reports that participants infer source dependence strongly from verbal similarity and may rely on a surface-copying heuristic. [Repository record](https://repositories.cdlib.org/uc/item/6f6597d3) | Relevant to dependence inference and an important warning that lexical-similarity shortcuts can mislead. It is not presented here as an LLM verification algorithm. | Inspect full text and methods; use it to motivate hard controls that are similar-but-independent and paraphrased-but-dependent. Peer-review status is not established by the current record. |
| **Hierarchical Evidence Set Modeling for Automated Fact Extraction and Verification** — Subramanian & Lee | EMNLP 2020 | Retrieves documents and multi-hop evidence sets; applies word-level and evidence-set-level attention; combines contextual and non-contextual aggregation for Supported / Refuted / Not Enough Info. Explicitly motivates the design partly by redundant and noisy evidence. [Paper](https://aclanthology.org/2020.emnlp-main.627/) | Redundant/noisy evidence aggregation and evidence-set modelling are not new. | Must compare against evidence-set approaches conceptually and, if feasible, experimentally. Its central idea is not an explicit claim-specific source-origin graph, but that alone does not establish a gap. |
| **Detecting Textual Reuse in News Stories, at Scale** — Nicholls | International Journal of Communication 2019 | Uses n-gram shingling to estimate text reuse across news stories and distinguishes newswire copy, PR reuse, source-to-source copying, common-source and incidental overlap. [Paper](https://ijoc.org/index.php/ijoc/article/view/9904) | Text reuse, shared text and some common-source patterns have established detection methods. | “We detect copied or similar sources” is not a novelty claim. RC-Gate would need to demonstrate a claim-verification-specific contribution beyond text reuse detection. |
| **News Provenance: Revealing News Text Reuse at Web-Scale in an Augmented News Search Experience** — Evans et al. | ACM CHI 2020 | Reconstructs histories/origins of near-duplicate news content at web scale and explores surfacing that provenance in news search. [Microsoft Research](https://www.microsoft.com/en-us/research/publication/news-provenance-revealing-news-text-reuse-at-web-scale-in-an-augmented-news-search-experience/) | Provenance reconstruction and user-facing source lineage already exist in the news domain. | Any novelty must be in the *claim-specific effect on evidence aggregation and verification*, not provenance visualization or article clustering alone. |
| **IMRRF: Integrating Multi-Source Retrieval and Redundancy Filtering for LLM-based Fake News Detection** — Li et al. | NAACL 2025 | Combines corpus retrieval, knowledge-graph retrieval, LLM-based evidence summarization/filtering, additional LLM-generated knowledge, and claim verification; evaluated on FEVEROUS and HOVER. Its filtering prompt summarizes relevant evidence and removes irrelevant material. [Paper](https://aclanthology.org/2025.naacl-long.461/) · [Code](https://github.com/quark233/IMRRF/tree/main) | Directly targets redundant retrieved information in LLM-based claim/fake-news verification. | Essential close competitor. The initial full-text inspection suggests its filtering is not the same as explicitly estimating claim-conditioned origin dependence, but the paper must be compared in detail and the code inspected before making that distinction a novelty claim. |
| **Resolving Conflicting Evidence in Automated Fact-Checking: A Study on Retrieval-Augmented LLMs (CONFACT)** — Ge et al. | IJCAI 2025 | Creates a conflicting-evidence setting and studies RAG fact-checking under conflicting claims and source-credibility differences. [IJCAI](https://www.ijcai.org/proceedings/2025/1073) | Conflict, credibility and aggregation under conflicting retrieved evidence are active research topics. | Do not include general contradiction handling or credibility-aware verification as the proposed method’s unique contribution. Keep them as controlled factors or secondary analyses. |
| **Evidence-Aligned Entity Verification for Hallucination Detection in Retrieval-Augmented Generation (EAEV)** — Jia et al. | Findings of ACL 2026 | Performs entity–evidence alignment across several dimensions and uses counterfactual stability under evidence perturbations. [Paper](https://aclanthology.org/2026.findings-acl.1477/) | Evidence alignment and intervention-based stability testing are established in recent RAG hallucination work. | A generic “perturb evidence and observe stability” benchmark is insufficiently novel. The intervention must specifically test evidence-origin dependence and benchmark its annotation validity. |
| **ProvenanceGuard: Source-Aware Factuality Verification for MCP-Based LLM Agents** — Alvarez et al. | arXiv preprint, 2026 (not treated as peer-reviewed here) | Routes each atomic claim to source-specific evidence, checks entailment and verifies that an answer’s stated attribution belongs to the source providing support; evaluates source-confusion errors. [Preprint](https://arxiv.org/abs/2606.18037) | Source-aware claim verification and source-ownership errors have already been addressed. | Keep **source ownership** separate from **source dependence**. A claim can be supported by the source named in an answer while that source merely repeats another source; conversely, a claim can be attributed to the wrong source even when the underlying documents are independent. |
| **Provenance: A Light-weight Fact-checker for Retrieval Augmented LLM Generation Output** — Sankararaman et al. | EMNLP Industry Track 2024 | Uses a compact NLI model to score factuality of RAG outputs against context and trace issues back to context chunks. [Paper](https://aclanthology.org/2024.emnlp-industry.97/) | Claim-to-context support scoring and evidence localization are already practical methods. | Include an NLI fact-checker in baseline tiers. This use of “Provenance” concerns tracing claims to supplied context; it is not the same as inferring shared origin between retrieved sources. |
| **Topic-Aware Evidence Reasoning and Stance-Aware Aggregation for Fact Verification** — Si et al. | ACL 2021 | Models topical consistency and aggregates evidence based on implicit stance instead of treating all evidence equally. [Paper](https://aclanthology.org/2021.acl-long.128/) | Stance-aware aggregation and the need to avoid spurious evidence influence are established. | The candidate contribution must go beyond better support/refutation aggregation: it must show that the *dependence relationship between evidence origins* improves decisions. |
| **PROBE: PROcess-Based BEnchmark for Hallucination Detection** — Zhang et al. | Findings of ACL 2026 | Evaluates claim decomposition, evidence finding, evidence evaluation and hallucination localization as separate process steps, across 12,000 test cases. [Paper](https://aclanthology.org/2026.findings-acl.2099/) | Multi-stage verification breakdown and diagnosis are already established. | RC-Gate cannot claim novelty for simply separating verification into stages. Its main experiment should isolate the dependence effect. |
| **Rethinking Evaluation for LLM Hallucination Detection: A Desiderata, A New RAG-based Benchmark, New Insights (TRIVIA+)** — Chen et al. | ACL 2026 | Proposes benchmark desiderata and a human-annotated RAG benchmark with long contexts and multiple realistic label-noise schemes. [Paper](https://aclanthology.org/2026.acl-long.680/) | New benchmark proposals must address label reliability, long contexts, data realism and noise. | A small collection of synthetically duplicated snippets is not enough. We need an explicit annotation protocol, adjudication, and natural examples. A broad “hallucination benchmark” is not a viable contribution by itself. |
| **Do LLMs Know When Evidence is Insufficient? An Evidence Sufficiency Benchmark for Answer-Abstention Calibration in RAG** — Zhang & Wu | Computers, Materials & Continua 2026 | Studies insufficient, irrelevant and contradictory evidence and abstention. [Paper](https://www.techscience.com/cmc/v89n1/68467) | Evidence sufficiency and abstention are already direct topics. | Treat sufficiency/abstention as annotation and operating-condition controls, not a second headline contribution. Check quality, peer-review status and full method during citation chasing. |
| **FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation** — Min et al. | EMNLP 2023 | Decomposes long-form generation into atomic facts and estimates factual precision against a knowledge source. [Paper](https://aclanthology.org/2023.emnlp-main.741/) | Atomic claim decomposition and evidence-grounded fact scoring are established. | Use as prior art/baseline family, not as claimed novelty. |
| **SAFE / LongFact** — Google DeepMind | 2024 | Decomposes long answers into facts and checks them using search evidence plus an LLM evaluator. [Publication](https://deepmind.google/research/publications/85420/) | Search-assisted claim checking is established. | “Multi-model + web + citations + claim decomposition” is a product description, not a novelty claim. |
| **RAGTruth** — Wu et al. | ACL 2024 | Provides annotated RAG responses and word-/case-level hallucination labels. [Paper](https://aclanthology.org/2024.acl-long.585/) | A useful hallucination dataset, but not a source-lineage benchmark by default. | It may help evaluate downstream hallucination labels, but does not alone supply the claim-specific information-origin annotations required by this hypothesis. |

### What this table does and does not establish

It establishes that the broad versions of the proposed idea are already covered: redundancy filtering; redundant/noisy evidence-set aggregation; source attribution; evidence perturbation; multi-step verification; evidence sufficiency/abstention; and generic web-grounded fact-checking.

It does **not** yet establish that no previous work evaluates the causal effect of *claim-specific evidence-origin dependence* on LLM-verifier confidence against both text-level deduplication and modern redundancy filters. That is a candidate intersection to investigate—not a statement we can publish as fact today.

The especially dangerous false claim would be: “No existing verifier accounts for independent evidence.” Current work already approaches related pieces of this problem. Do not write that sentence.

---

## 2. Definitions: stop mixing truth, evidence status and provenance

Every datum in the new pilot/benchmark must distinguish at least three annotation layers. These labels answer different questions and must never be collapsed into one gold label.

### Layer A — Claim truth at a reference time

**Question:** Is the proposition true in the world at time `t`?

Suggested labels: `TRUE`, `FALSE`, `UNRESOLVED`, `TIME_DEPENDENT_OR_AMBIGUOUS`. Attach a reference date and authoritative adjudication sources. “Unresolved” is not synonymous with “the retrieved evidence is insufficient.” A claim may be true while the given evidence set fails to establish it.

### Layer B — Evidence status for this particular evidence set

**Question:** What does this exact set of passages justify about the claim, independent of how many pages repeat each passage?

Suggested exclusive target labels:

- `ADEQUATE_SUPPORT`: reliable, relevant, applicable evidence supports the material proposition, with no unresolved material contradiction.
- `ADEQUATE_REFUTATION`: reliable, relevant, applicable evidence refutes the material proposition, with no unresolved material contradiction.
- `INSUFFICIENT`: the provided passages do not establish either side to the stated standard (including irrelevant or too-weak material).
- `CONFLICTING`: there is credible, material support and refutation that cannot responsibly be resolved from the available evidence.

The annotation manual must define “adequate” for the selected domain and claim type. These labels describe the evidence set—not necessarily the world truth. If the factual claim is true but the evidence set only contains weak unsupported repetition, its truth may be `TRUE` while evidence status is `INSUFFICIENT`.

### Layer C — Claim-specific evidence origin / dependence

For every passage pair and claim, label the relationship of the **underlying information relevant to that claim**, not merely whether the documents use similar words.

Suggested relation taxonomy:

- `DIRECT_REUSE_OR_SYNDICATION`: exact/near copy or explicit syndication of an earlier item.
- `SHARED_PRIMARY_ORIGIN`: separately written accounts derived from the same press release, official record, study, dataset, witness statement or other common primary source.
- `INDEPENDENT_ORIGIN`: the evidence was independently collected or established, rather than simply repeating the same underlying evidential item.
- `MIXED_OR_PARTIAL_DEPENDENCE`: the passage partly repeats a shared source but adds a separately sourced item relevant to the claim.
- `UNKNOWN`: the available evidence does not justify deciding the relationship.

Record (i) document/text reuse separately from (ii) underlying evidence origin where feasible. Record the reference URL/artifact, timestamps, explicit citations/links, annotator rationale and confidence. A missing citation is **not proof of independence**. Same-domain/different-domain is not an independence label. An article may be independent for one claim and dependent for another; annotation is claim-specific.

**Key conceptual safeguard:** source independence is not truth. Several independent publishers can be wrong; several articles can share one excellent primary source; one authoritative source can establish a simple claim; and a source may be right about a fact but not be the source an answer claims it is using. This project focuses on dependence-aware evidence aggregation, not a universal truth oracle.

---

## 3. Exact research question and falsifiable hypotheses

### Primary research question

**RQ:** Under a fixed claim and controlled, claim-specific evidence conditions, how much do current evidence-based verifiers change their support assessment when additional passages are dependent repetitions rather than genuinely independent corroboration, and does an explicit dependence-aware correction improve decisions beyond the strongest simple redundancy baseline on natural and controlled cases?

### Hypotheses and primary-verifier policy

The pilot will have **two preselected primary verifier families**, not an open-ended set from which the most vulnerable system is chosen after results are seen:

- **Primary V1 — LLM judge:** exact model identifier/version or dated API snapshot, prompt, decoding parameters, output schema and software wrapper must be recorded before the scored pilot begins.
- **Primary V2 — NLI aggregator:** exact model identifier/revision, tokenizer, label mapping and aggregation rule must be recorded before the scored pilot begins.

If either exact configuration cannot be frozen, the scored pilot does not begin. Other systems are secondary/exploratory and cannot be substituted post hoc for a primary verifier.

- **H1 — Dependence intervention effect:** For preselected primary verifiers, adding claim-relevant passages derived from an existing evidentiary origin changes false-support decisions on evidence sets whose adjudicated status remains non-supporting. Report both primary verifiers separately. A finding in only one supports a verifier-specific observation, not a universal claim; aligned effects across both provide stronger evidence.
- **H2 — Beyond simple filtering:** Any candidate dependence-aware correction improves the predeclared primary outcome over the strongest simple baseline, including semantic clustering and count capping, on held-out claim/source families.
- **H3 — Useful corroboration is retained:** The correction does not achieve lower false support merely by ignoring evidence or increasing abstention; it preserves response to genuinely independent, claim-relevant evidence.
- **H4 — Natural-case transfer:** Any improvement persists on natural source chains and source-held-out cases, not only constructed duplicates.

The feasibility pilot is descriptive and diagnostic, not a powered confirmatory test. H1 cannot be declared established merely because one model among many showed an effect. H2–H4 remain unproven until a separately frozen confirmatory study. Failure to support the claims is an accepted outcome.

---

## 4. The narrow technical distinction to test

### Candidate distinction, subject to audit

Most similar approaches identified so far fall into at least three groups:

1. **Content redundancy handling:** remove irrelevant or repeated text, or model groups of evidence jointly (e.g., IMRRF and HESM).
2. **Document/source provenance:** detect news text reuse or reconstruct article propagation histories (e.g., News Provenance and textual-reuse work).
3. **Source ownership / claim attribution:** check whether a claim is supported by the particular source an answer names (e.g., ProvenanceGuard).

The candidate RC-Gate question is the intersection between these areas: **does estimating claim-specific underlying evidence dependence improve the correctness of an evidence-aggregation decision, beyond content similarity and source ownership?**

This framing remains provisional. If the full-text and citation audit finds a paper already making this contribution with comparable evaluation, stop claiming the gap and reconsider the research question.

**Important boundary:** the proposed contribution is not “detecting duplicates,” “finding article lineage,” “checking attribution,” or “making scores more stable under perturbations.” The candidate claim, if it survives audit, is that **claim-specific estimation of shared evidential origin improves a claim-verification decision beyond strong text-level redundancy baselines**. The observable unit is an adjudicated decision under a controlled evidence intervention; we do not assume that a model's internal reasoning or representation corresponds to provenance.

### What a candidate method may look like—after the pilot, not before

The smallest reasonable method family is a *dependence-aware evidence aggregator*:

1. For each atomic claim `c`, obtain a frozen set of passages `E` and their claim–passage support/refute/irrelevant scores from the same baseline verifier.
2. Represent claim-relevant evidence fragments as nodes in a **typed, claim-specific provenance graph**. Edges can encode direct copying/syndication, quotation or citation, use of a shared primary artifact/dataset, partially shared evidence with an additional independent component, independently collected evidence, or unknown relation. These edges are not assumed to be transitive; a document may contain both shared-origin and independently collected material.
3. Estimate dependence using available cues (text similarity, links/citations, timestamps, quoted-source metadata, primary artifacts and claim-conditioned semantic overlap) while retaining `UNKNOWN` and uncertainty. Text similarity, publication lineage and epistemic dependence are separate annotations; no single cue proves independence or dependence.
4. Correct aggregation so repeated passages do not count as independent votes solely by virtue of document/URL count. Keep support and refutation distinct; provenance alone cannot establish truth.
4. Return an evidence-status verdict and a review score. The score is **not** called a probability unless a well-defined target and held-out calibration demonstrate that interpretation.

Candidate estimators could include (a) explicit clustering / support capping, (b) a supervised pairwise dependence model, and (c) a graph-based or learned aggregation. Because dependencies may be partial and non-transitive, document-level clusters are a baseline rather than an assumed correct representation. We should implement the simplest candidate first. A learned gate is only justified if it outperforms simpler alternatives and its additional complexity has measurable value. This document does not declare one architecture the final algorithm.

### What is explicitly out of scope for the first paper

- A universal hallucination detector for every model/domain.
- General source-credibility rankings as a new contribution.
- A freshness model for every type of claim.
- A new general contradiction-resolution algorithm.
- A new abstention-calibration algorithm.
- Improving the base answer-generating model.
- Claiming that a UI helps humans without a human study.
- Claiming that several models agreeing makes a claim true.

Those can be future product/system capabilities, or controlled nuisance variables, but they must not dilute the primary research question.

---

## 5. First experiment: small pilot designed to falsify the premise

**Purpose:** establish (a) whether dependence-related confidence inflation occurs in current verifiers, (b) whether simple redundancy filtering already solves it, and (c) whether claim-specific provenance can be labelled reliably enough to research.

This is a feasibility pilot, not the final publication benchmark. Do not reuse it as the confirmatory test set.

### Pilot sample and construction

- Start with approximately **40–60 base claims** in one source-rich, manageable domain. Treat this as a feasibility sample for discovering failure modes and annotation cost—not a sample for stable population prevalence or a superiority claim.
- Build two separate experimental arms and report them separately:
  - **Naturalistic duplication arm:** add actual syndicated or dependent reports found in the source chain. This estimates the practical effect of adding real dependent material but is not, by itself, a causal isolation of dependence.
  - **Length/count-controlled arm:** hold passage count and token budget approximately constant. Compare dependent evidence against carefully matched topical/length controls and against independently corroborative evidence where available. Record exact tokens under each target verifier's tokenizer, source metadata presented, passage order and relevance judgments. Replace rather than simply append control passages where necessary to hold context size constant.
- Counterbalance passage order across cases using a recorded random seed. Keep the same order assignment across compared systems where possible. For a small sensitivity subset, repeat selected cases with an alternate order to diagnose position effects.
- For the primary false-support contrast, include only variants for which annotators agree that adding the dependent passage does **not** change the evidence-set gold status. If an added passage genuinely introduces a new evidentiary basis or changes the gold status, do not force it into the duplication-invariance contrast; analyze it separately.
- Preserve natural source chains as natural examples. Any programmatically duplicated or paraphrased material must be tagged as a controlled intervention. Do not use programmatically created examples as the only evidence of a practical problem.
### Annotation work

Use the separate `RCGate_Annotation_Protocol_v0_1.md` codebook. Two annotators label independently and blinded to verifier outputs. Preserve both original label sets; disagreements are adjudicated and logged rather than overwritten. Report raw agreement, confusion matrices and a chance-corrected statistic appropriate to each label layer (nominal Krippendorff's alpha; Cohen's kappa may additionally be reported when exactly two annotators label all cases). Report unknown rates and agreement specifically on difficult partial-dependence and similar-but-independent cases—not only overall agreement. Also measure annotation time and adjudication frequency.

Run a separate calibration/training batch first, revise the codebook on that batch, then freeze it before annotating scored pilot items. The reliability criterion for proceeding must be written down before the scored annotation results are examined. If provenance cannot be adjudicated reliably on the cases central to the hypothesis, do not train a dependence estimator on those labels.

### Verifiers and baselines for the pilot

All primary comparisons receive the exact same frozen claim and passage text wherever their interface permits:

1. **LLM-as-a-judge:** fixed prompt, fixed model/version, deterministic decoding where supported; request a verdict and concise citation-to-passage reasoning.
2. **NLI aggregation:** max support/refute scores, mean aggregation and a contradiction-aware simple aggregator.
3. **Exact duplicate removal:** remove byte-identical/normalized identical passages.
4. **Near-duplicate clustering / capped count:** lexical overlap (e.g., shingling) and embedding similarity variants; count clusters rather than raw URLs, with validation-only thresholds.
5. **Source-count / majority baseline:** simple baseline that exposes how multiplicity alone changes decisions.
6. **Redundancy-filter baseline:** an IMRRF-style/adapted filter if implementation and model requirements make a faithful comparison feasible; label it as an adaptation unless authors' code and full protocol are reproduced.
7. **Gold-provenance oracle diagnostic:** apply the specified aggregation correction using gold relation annotations. This measures that correction under perfect labels; it is not a general theoretical upper bound for all possible dependence-aware methods and is not deployable.

Legacy A0/A4/A7 are useful historical artifacts, but Stage 8 RAGTruth rows are not the same task or dataset. They should not be included in the pilot's headline leaderboard unless each is refit to the same evidence-dependence inputs and labels. Keep the original Stage 8 results untouched.

### Minimal pilot outputs

- Whether duplicate/dependence perturbations measurably affect each baseline's score and verdict.
- Whether LLM support scores inflate under `DEPENDENT_REPETITION` and `DEPENDENT_PARAPHRASE` relative to `BASE` for gold non-support evidence sets.
- Whether independently corroborative evidence changes the score/verdict more appropriately than dependent repeats.
- Performance of simple deduplication/capped aggregation versus a dependence-aware oracle.
- Human agreement and unknown-label rates for evidence-origin annotations.
- Failure cases with source links and adjudication notes.
- Time/cost per claim and whether natural source chains are obtainable at scale.

### Pilot stop/go rules

**Stop or pivot before full model development if any of these occurs:**

- Close prior art already implements claim-specific origin-dependence correction with a similar evaluation; no distinct extension survives comparison.
- Strong baseline verifiers rarely show the hypothesized inflation in the targeted conditions.
- Exact or near-duplicate clustering removes essentially all observed error, and source-origin modelling adds no credible value in hard natural examples.
- Source-origin labels are too ambiguous/unreliable for a reproducible benchmark.
- The observed effect exists only in artificially copied text and does not appear in natural source chains.

**Proceed to a confirmatory study only if:** the targeted error is observable, the dependence label is feasible, the simple baseline has a measurable residual failure on hard cases, and an intervention can plausibly address that residual failure. Pilot thresholds are exploratory; freeze the confirmatory effect threshold, primary metric and test protocol before collecting/inspecting the confirmatory test set.

---

## 6. Exact evaluation target and metrics

The primary task is **evidence-set assessment for a claim under a frozen set of passages**, not a vague “hallucination probability” task.

### Primary outcome candidate: duplicate-induced false-support increase

For each eligible evidence-set variant `v`, define `FS(v)=1` when the system outputs `ADEQUATE_SUPPORT` but the independently adjudicated evidence-set status is not `ADEQUATE_SUPPORT`; otherwise `FS(v)=0`. The denominator for a false-support rate is all evaluated variants whose gold evidence status is `ADEQUATE_REFUTATION`, `INSUFFICIENT`, or `CONFLICTING`; report the three strata separately as well as pooled.

For each eligible claim/source-family case, report all three quantities:

1. **Base false-support rate:** rate of `FS=1` on the unexpanded base evidence sets.
2. **Dependent-addition false-support rate:** rate of `FS=1` after dependent material is added.
3. **Paired risk difference:** `Δ_dup = mean(FS_dependent − FS_base)` over eligible paired cases.

A positive paired risk difference indicates increased false support under dependent addition. A zero difference is not evidence of reliability if the system is wrong in both conditions; therefore the two absolute rates are mandatory. Report the result separately for `INSUFFICIENT`, `ADEQUATE_REFUTATION`, and `CONFLICTING` gold statuses. Because claim variants are related, uncertainty resampling must cluster at claim/source-family level; in the pilot, show per-claim pairs and treat intervals as descriptive rather than confirmatory. Do not count evidence variants as independent claims.

Keep this separate from **truth-level false confirmation**: a false claim may be linguistically asserted by a passage while that passage is not an adequate epistemic basis for it. Report claim truth, passage stance and evidence-set adequacy separately. Requested numeric LLM “support scores” are secondary within-system diagnostics, not probabilities unless their target and calibration are validated.

### Mandatory guardrail: independent corroboration sensitivity

For eligible claims where added independent evidence genuinely changes an insufficient set to adequate support/refutation under the annotation standard, measure whether the method responds in the correct direction. A dependence-aware system must not be “good” only because it ignores all additional evidence.

### Secondary measures

- Four-way evidence-status macro-F1 and class-wise precision/recall.
- Supported-verdict rate / false-support rate on non-support evidence sets.
- Pairwise dependence-detection precision, recall and F1, plus calibration if probabilities are output.
- Robustness on paraphrased reuse and similar-but-independent hard controls.
- Risk–coverage curves if abstention is added; compare at predeclared coverage levels and report the exact definition of coverage.
- AUROC/AUPRC only where they correspond to a clearly defined binary target; avoid presenting them as a full solution to a four-way task.
- Cost, latency and token/context usage.

### Statistical design

- All variants of the same claim and all examples from the same source lineage must remain in one partition.
- Keep claim families, source lineage clusters and time-related duplicates disjoint across train/validation/test as required by the target generalization claim.
- Choose thresholds on validation only. Lock the final test set before model selection.
- Report paired confidence intervals with resampling clustered by claim family / source-origin family, not independent-row bootstrap. State exactly what the confidence interval samples.
- Compare methods at the same retrieval evidence and information budget for the primary study. Evaluate end-to-end retrieval separately if later required.
- Report naturalistic and length/count-controlled results separately; do not treat the naturalistic arm alone as isolating dependence from context length or repetition.
- Log token counts and passage order; conduct an order-sensitivity analysis on the designated subset. Do not use synthetic-only gains as evidence of real-world validity.

### Practical effect criterion

Do not invent a numeric improvement threshold after viewing the final-test results. Use the pilot only to determine feasibility, annotation variance and a plausible minimally important effect. Before confirmatory data is opened, register a concrete threshold for reduced false support, an acceptable maximum loss in independent-corroboration sensitivity, cost/latency bounds and uncertainty criteria. The threshold must be documented in the experiment plan.

---

## 7. Strongest fair baseline policy

Baselines should be organized into tiers rather than one long list of incomparable papers.

### Tier 1 — Mandatory, comparable baselines

All use the same claim and frozen evidence set: LLM judge; max/mean NLI aggregation; exact duplicate removal; near-duplicate clustering; cluster-capped support count; simple source-count majority; claim–passage support scoring with no dependence correction. Include at least two implementations of the near-duplicate baseline (lexical and semantic) so the method cannot win solely because the deduplicator is weak.

### Tier 2 — Closest published comparators

IMRRF is the first priority because it explicitly filters redundant evidence in LLM fake-news verification. Inspect code and paper details, decide whether it can be run with the same frozen evidence, and label adaptations clearly. HESM is highly relevant to evidence-set aggregation but may not be directly comparable unless the data format/task are compatible. EAEV is relevant for entity–evidence alignment and evidence perturbation. ProvenanceGuard is relevant to source ownership, but source ownership is not the same target as source dependence. CONFACT is relevant if conflicts are included as controlled cases. Public implementation availability, model access, data restrictions and task mismatch must be documented for every comparator.

### Tier 3 — Oracle and ablation diagnostics

Use a gold-provenance oracle diagnostic to measure the specified correction when given gold relations. Do not call it a general upper bound: it only diagnoses that particular correction with perfect relationship labels. Ablate lineage features, text similarity, explicit citation/link metadata, origin evidence, and unknown handling. Compare a simple source-cluster cap against the learned estimator.

### Tier 4 — Historical RC-Gate variants

A0, A4 and A7 remain in the record as the old sentence-level RAGTruth study. Do not combine Stage 8 AUROC with the new benchmark's outcomes. The old result is currently negative: A7 mean AUROC 0.5717, below A0 0.6280 and A4 0.6839 on the reported 800-row/134-question slice. It motivates re-examination, but it does not validate the new research question and cannot be used as evidence that the new system is better.

---

## 8. Dataset construction requirements

The confirmatory benchmark is not ready until the annotation protocol and sampling plan exist. Minimum schema per record:

- Stable claim ID and source claim/question ID.
- Claim text, time reference and context necessary to resolve temporal/conditional interpretation.
- Independent claim-truth label + supporting adjudication URLs/artifacts.
- Atomic claim extraction if the natural response contains compound claims; extraction method/version and human corrections.
- Passage text, URL, publisher/domain, timestamp, archived snapshot/hash, retrieval query and rank.
- Claim–passage relation (`SUPPORT`, `REFUTE`, `NEITHER`, `MIXED`) with annotator rationale.
- Evidence-set status (`ADEQUATE_SUPPORT`, `ADEQUATE_REFUTATION`, `INSUFFICIENT`, `CONFLICTING`) with domain-specific rule.
- Text-reuse relation, underlying evidence-origin relation, evidence-origin family ID, relation direction where known, confidence and rationale.
- Source credibility/freshness/context tags as potential confounds—not treated as gold proof of truth.
- Natural versus controlled intervention flag; transformation script/version for controlled rows.
- Train/validation/test partition computed by claim and source-origin family, not at row level.

**A critical annotation distinction:** source dependence is claim-specific and may be partial. A document can use a shared government report for one sentence and add an independently collected interview for another. Do not force all passages in a document into one duplicate cluster. Store claim-relevant evidence fragments as nodes and typed, potentially directed relations as edges. Record separately (a) textual similarity/reuse, (b) publication/citation lineage, and (c) epistemic dependence on underlying evidence. These relations need not be transitive. An absence of found citations is not proof of independent evidence. A copy published by a new outlet may still rely on the same primary artifact.

For the pilot, it is acceptable to have a small, manually audited dataset. For a paper claiming a benchmark contribution, the dataset must be large enough and diverse enough to support the exact claims; annotation quality and representativeness matter more than an arbitrary row count.

---

## 9. Reproducible prior-art audit protocol

The current literature pass is a **focused scoping audit**, not a complete systematic review. It must not be described as exhaustive. The following process should be used to close it:

### Search scope

Search scholarly primary sources and their repositories (ACL Anthology, arXiv, IJCAI/AAAI/ACM proceedings, publishers, Microsoft Research publication archive, and citation indexes accessible to the team) using combinations of:

- `LLM factuality verification redundant evidence`
- `claim verification source dependence independent corroboration`
- `source provenance news text reuse source lineage`
- `evidence redundancy filtering fact checking LLM`
- `correlated evidence aggregation fact verification`
- `source-aware verification evidence lineage`
- `duplicate evidence calibration false confirmation RAG`
- `evidence set aggregation provenance graph fact checking`
- names of each seed work plus `cited by`, `references`, repository and benchmark

The searches in this document were run on 22 October 2026 using web search and authoritative publication pages. Search-engine results are used for discovery, not as the sole basis for a technical claim.

### Inclusion criteria

Include work that materially addresses at least one of: evidence redundancy/dependence; provenance/text reuse/source origin; evidence aggregation/correlation; source-specific claim attribution; verification under evidence perturbation; or evidence sufficiency/conflict in LLM/RAG fact checking. Track venue and peer-review status separately. Include older source-provenance/text-reuse literature because the proposed lineage component is not exclusively an LLM problem.

### Exclusion/triage rules

Do not include generic LLM hallucination detection without retrieved/source evidence in the core novelty table unless it provides a direct baseline or principle. Do not treat a product blog or search snippet as evidence for an algorithmic novelty claim. Record preprints and non-peer-reviewed work, but identify them as such.

### Deliverables for audit closure

1. A query log with database/site, exact query, date, result count if available, and screening notes.
2. A screened bibliography with title, authors, year, venue/status, problem, inputs/outputs, algorithm, dataset, labels, baselines, metrics, code status and limitations.
3. Backward and forward citation chasing from the closest seed papers.
4. An explicit “novelty threat” column: what would make the RC-Gate claim redundant?
5. A written comparison stating which closest method makes the same prediction, from the same inputs, under the same evidence intervention.
6. A documented stop/go decision. Novelty is not established by the absence of an exact title match.

### Current search log (partial; continue it rather than pretend it is exhaustive)

| Date | Search/theme | Key finds | Consequence |
|---|---|---|---|
| 2026-10-22 | `IMRRF NAACL 2025 redundant retrieved information fake news detection` | IMRRF (NAACL 2025) | Direct redundancy-filtering work; must be a close comparator. |
| 2026-10-22 | `Hierarchical Evidence Set Modeling EMNLP 2020` | HESM (EMNLP 2020) | Redundant/noisy evidence aggregation is older than the LLM-verification wave. |
| 2026-10-22 | `news article provenance shared text reuse lineage` | News Provenance (CHI 2020); Nicholls (2019) | Provenance/text reuse detection itself is not new. |
| 2026-10-22 | `Evidence-Aligned Entity Verification ACL Findings 2026` | EAEV | Evidence perturbation/stability overlaps the proposed evaluation style. |
| 2026-10-22 | `Getting the Source Right Not Just the Fact ProvenanceGuard` | ProvenanceGuard preprint (2026) | Source ownership is already being handled; separate it from dependence. |
| 2026-10-22 | `conflicting evidence fact checking source credibility 2025` | CONFACT (IJCAI 2025) | Conflict/credibility should not be a second headline contribution. |
| 2026-10-22 | `TRIVIA+ ACL 2026 hallucination benchmark label noise` | TRIVIA+ (ACL 2026) | Benchmark quality/annotation/noise standards are high and current. |
| 2026-10-22 | `PROBE process-based hallucination detection ACL 2026` | PROBE (Findings ACL 2026) | Process decomposition alone is not novel. |
| 2026-10-22 | `evidence sufficiency benchmark abstention 2026` | Evidence Sufficiency Benchmark | Insufficiency/abstention already has a direct benchmark. |
| 2026-10-22 | `RAG claim factuality NLI context chunks provenance` | Provenance (EMNLP Industry 2024) | Claim–context scoring/localization is a practical baseline family. |
| 2026-10-22 | `stance-aware aggregation fact verification` | Topic-Aware Evidence Reasoning (ACL 2021) | Non-uniform evidence aggregation and stance signals predate the proposed method. |
| 2026-10-23 | `"Source Independence Is a Measurable Property of Evidence"` | Byrd, SSRN record (June 2026) | Directly overlaps independence measurement and effective source counting; full-text/code audit still open. |
| 2026-10-23 | `"When agreement looks like copying" source dependency inference` | Belkin, Madsen & de-Wit, 2026 repository record | Human source-dependence judgments may rely too heavily on surface similarity; annotation and adversarial-control implications. |
| 2026-10-23 | `correlated evidence aggregation evidence synthesis provenance dependence` | Cross-disciplinary search initiated; screening incomplete | Search beyond NLP is mandatory before gap closure; no novelty conclusion from this partial pass. |

This log is partial and should be expanded through citation chaining, full-text inspection and repository inspection before any public novelty statement. The Byrd preprint and Belkin et al. record have been added because they are direct or adjacent threats; in this revision, their search records/abstract-level descriptions were inspected, but their full methods/code have not been audited. Do not describe the novelty audit as closed.

---

## 10. Updated research contribution options after pilot

We do not pre-commit to one paper type. The pilot decides which of these options is justified.

### Outcome A — Dependence-aware method contribution survives

Condition: clear gap after audit; current verifiers exhibit the failure; a method beats simple dedup/capping on hard natural cases; no significant loss on independent corroboration; source-held-out results remain useful.

Paper centre: the dependence-aware aggregation method and controlled/natural evaluation. The benchmark and auditor support this one headline contribution.

### Outcome B — Learned method is not better, but a new evaluation finding is robust

Condition: a simple baseline is strongest, but a carefully annotated source-dependence challenge set exposes a substantial and previously under-measured failure across multiple verifiers, with rigorous natural examples and reliable labels.

Possible paper centre: a measurement/benchmark paper, only if the prior-art audit establishes a distinct evaluation contribution over TRIVIA+, EAEV, PROBE, IMRRF and related work. Do not present a weak method as the contribution.

### Outcome C — The failure is trivial, rare, or already solved

Condition: standard models do not fail materially, simple deduplication solves it, source-lineage labels are not reliable, or a closest method already solves the task.

Decision: stop this research direction and choose a different narrowly evidenced question. This is preferable to inventing novelty around a system that does not need to exist.

---

## 11. Project artifact plan

Keep history and old manuscript/results unchanged. New work should live in versioned, separate files/directories.

1. `RCGate_Prior_Art_Matrix_v0_1.csv` — paper-level comparison and novelty-threat columns.
2. `RCGate_Search_Log_v0_1.csv` — exact queries, dates, sources, screening decisions and citation chains.
3. `RCGate_Annotation_Protocol_v0_1.md` — codebook for claim truth, semantic stance, evidence-set adequacy and claim-specific provenance graph.
4. `RCGate_Pilot_Protocol_v0_2.md` — paired naturalistic and controlled arms, preselected primary verifier families, absolute rates and paired outcomes.
5. `RCGate_Pilot_Decision_Record_v0_1.md` — freeze-before-scored-pilot checklist and outcome record.
5. `pilot_data/` and `pilot_results/` — separate from historical RAGTruth data/results; immutable raw annotation exports and derived outputs.
6. Only after the pilot: a versioned method specification, preregistered confirmatory experiment plan and implementation.

Do not overwrite old `Stage 8`, `A0/A4/A7` results, the original paper draft, or existing historical artifacts. Do not commit or push any changes without an explicit instruction.

---

## 12. Final readiness verdict

The critique is correct: the prior blueprint was a useful intention-setting document, not proof of a research contribution. This revision is narrower and more falsifiable, but it still does **not** establish novelty or show that a method works.

### Current status

- **Problem importance:** plausible.
- **Broad novelty:** not supported; adjacent work already covers many components.
- **Narrow dependence-aware aggregation gap:** candidate only; requires citation-chain audit and direct comparator review.
- **Method:** intentionally not frozen.
- **Dataset:** not yet constructed; annotation feasibility unknown.
- **Empirical evidence for the new direction:** none yet.
- **Historical A7 superiority:** contradicted by reported Stage 8 results against A0/A4 on its current slice.
- **Publication readiness:** not ready.

Replace the “9.5/10” promise with auditable go/no-go conditions. A numeric research-readiness score cannot guarantee acceptance. The goal is to create a study that a skeptical researcher can reproduce and challenge—and that remains worthwhile after those challenges.

---

## References inspected in this pass

1. Subramanian, S. & Lee, K. (2020). *Hierarchical Evidence Set Modeling for Automated Fact Extraction and Verification*. EMNLP. https://aclanthology.org/2020.emnlp-main.627/
2. Nicholls, T. (2019). *Detecting Textual Reuse in News Stories, at Scale*. International Journal of Communication. https://ijoc.org/index.php/ijoc/article/view/9904
3. Evans, N., Edge, D., Larson, J. & White, C. (2020). *News Provenance: Revealing News Text Reuse at Web-Scale in an Augmented News Search Experience*. ACM CHI. https://www.microsoft.com/en-us/research/publication/news-provenance-revealing-news-text-reuse-at-web-scale-in-an-augmented-news-search-experience/
4. Li, D. et al. (2025). *IMRRF: Integrating Multi-Source Retrieval and Redundancy Filtering for LLM-based Fake News Detection*. NAACL. https://aclanthology.org/2025.naacl-long.461/
5. Ge, Z. et al. (2025). *Resolving Conflicting Evidence in Automated Fact-Checking: A Study on Retrieval-Augmented LLMs*. IJCAI. https://www.ijcai.org/proceedings/2025/1073
6. Jia, R. et al. (2026). *Evidence-Aligned Entity Verification for Hallucination Detection in Retrieval-Augmented Generation*. Findings of ACL. https://aclanthology.org/2026.findings-acl.1477/
7. Alvarez, A. et al. (2026). *ProvenanceGuard: Source-Aware Factuality Verification for MCP-Based LLM Agents*. arXiv preprint. https://arxiv.org/abs/2606.18037
8. Zhang, Y. et al. (2026). *PROBE: PROcess-Based BEnchmark for Hallucination Detection*. Findings of ACL. https://aclanthology.org/2026.findings-acl.2099/
9. Chen, W. et al. (2026). *Rethinking Evaluation for LLM Hallucination Detection: A Desiderata, A New RAG-based Benchmark, New Insights*. ACL. https://aclanthology.org/2026.acl-long.680/
10. Zhang, H. & Wu, W. (2026). *Do LLMs Know When Evidence is Insufficient? An Evidence Sufficiency Benchmark for Answer-Abstention Calibration in Retrieval-Augmented Generation*. Computers, Materials & Continua. https://www.techscience.com/cmc/v89n1/68467
11. Min, S. et al. (2023). *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation*. EMNLP. https://aclanthology.org/2023.emnlp-main.741/
12. Google DeepMind (2024). *Long-form factuality in large language models* (SAFE/LongFact). https://deepmind.google/research/publications/85420/
13. Wu, Z. et al. (2024). *RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models*. ACL. https://aclanthology.org/2024.acl-long.585/
14. Sankararaman, H. et al. (2024). *Provenance: A Light-weight Fact-checker for Retrieval Augmented LLM Generation Output*. EMNLP Industry Track. https://aclanthology.org/2024.emnlp-industry.97/
15. Si, J. et al. (2021). *Topic-Aware Evidence Reasoning and Stance-Aware Aggregation for Fact Verification*. ACL. https://aclanthology.org/2021.acl-long.128/
16. Byrd, A. (2026). *Source Independence Is a Measurable Property of Evidence*. SSRN preprint, posted 24 June 2026. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6903718. **Not peer reviewed in this audit; full methods/code review remains open.**
17. Belkin, S., Madsen, J. K., & de-Wit, L. H. (2026). *When agreement looks like copying: Testing a Bayesian model of source dependency inference*. 2026 repository/working-paper record. https://repositories.cdlib.org/uc/item/6f6597d3. **Publication status/full-text audit remains open.**

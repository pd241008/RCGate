# RC-Gate: A Metadata-Conditioned Two-Expert Prototype for Sentence-Level Hallucination Detection

**Final research report, version 1.** October 2026.

This document is the authoritative account of the RC-Gate project after Stages 4–10. It is a research report. Publication readiness for a conference or journal has not been established.

Three kinds of statement are kept apart throughout:

- **Repository finding.** A number, file, or behaviour read from this repository’s code, configs, or result reports.
- **Literature finding.** A claim checked against a paper during the Stage 9 novelty audit or the Stage 10 feasibility audit.
- **Interpretation.** A conclusion drawn from those findings. Interpretations are labelled as such.

No new model was trained for this report. No dataset or weight file was downloaded. Historical result directories were not rewritten.

## Abstract

Hallucination detectors often combine two families of clues. One family asks whether other models’ answers agree with a sentence. The other asks whether a supplied document supports that sentence. RC-Gate is a small research prototype that tries to decide, from metadata alone, how much to trust each family. The metadata are the sentence’s claim type (numeric, entity, extractive, or abstractive) and the identity of the model that wrote it. Two linear experts score the two families. A 233-parameter gate on the RAGTruth setup produces a trust weight for each expert. The weights scale the experts’ logits, and a linear head turns the pair into a probability that the sentence is hallucinated.

On synthetic tables built so that the trustworthy family depends on claim type, the gate recovers that planted pattern. A flat logistic regression does not, on the numeric slice. A gradient-boosting model that sees the same signals and the same metadata still ranks higher than the gate, including on the synthetic tables. Recovering a planted pattern is a mechanism check. It is not independent evidence about real generators.

On one corrected 800-sentence slice of RAGTruth (134 source questions, six generators, 57 hallucinated sentences), the principal repeated-fit analysis is Stage 8. That analysis refits every variant on the same frozen table, crossing 20 question-grouped splits with 3 model initialisations (60 fits per variant, 480 fits in total). Mean test AUROC over those 60 cells is 0.6280 for flat logistic regression (A0), 0.6839 for gradient boosting with metadata (A4), and 0.5717 for the full gate (A7). The sample standard deviation of A7’s 60 AUROC values is 0.1247. The mean paired difference A7 minus A0 is −0.0563. The mean paired difference A7 minus A4 is −0.1122. These summaries describe repeated fits on one question pool. They are not confidence intervals, and the 20 splits are not 20 datasets.

A read-only audit of the official RAGTruth QA release found that the proposed generator-by-type reliability surface is not adequately identified under a pre-specified support rule (at least 30 training positives and 15 official-test positives in a cell). No full-scale evaluation was run. Judge voting was never evaluated, because the signal tables contain no judge votes. The prototype, the synthetic recovery test, and this negative unstable evaluation are the current contribution. They do not establish that metadata-conditioned gating fails in general, and they do not establish a paper ready for submission.

## 1. Introduction and research question

A retrieval-augmented generator can produce a sentence that conflicts with the documents it was given, or that adds material those documents do not support. Detecting that sentence without opening the generator’s hidden states is a black-box problem. Two cheap families of evidence are widely used. Cross-model consistency compares the sentence with other models’ answers to the same question. Retrieval evidence compares the sentence with the supplied document, usually with a natural-language inference (NLI) model.

The project proposal stated three hypotheses (proposal §5; wording below is the proposal’s):

- **H1.** Signal reliability is conditional on claim type and generator identity, not stationary across the dataset.
- **H2.** A learned conditional gate outperforms both flat-concatenation fusion and naive model-judge voting, especially on claim types where flat fusion is documented to fail.
- **H3.** The gate’s learned weights are interpretable — they can show, after training, which signal family was trusted and why for a given claim, turning a previously silent failure mode into a visible, explainable one.

The research question that follows from those hypotheses is narrow. On sentence-level hallucination labels, does a gate that sees only claim type and generator identity assign the more reliable signal family a higher weight, and does that assignment rank hallucinated sentences better than a flat model that sees the same inputs?

**Interpretation.** The experiments answer that question only for a planted synthetic generator and for one 800-sentence RAGTruth slice. They do not answer it for the official RAGTruth test split, for DROP, for FinanceBench, or for hallucination detection in general.

### How to read a ranking metric

AUROC is the probability that a randomly chosen hallucinated sentence receives a higher score than a randomly chosen faithful sentence. A value of 0.5 is chance. AUROC does not depend on the decision threshold. Precision, recall, and F1 do. Expected calibration error (ECE) measures how far the predicted probabilities sit from the observed rates in bins of those probabilities. A low ECE means the probabilities are roughly honest frequencies. It does not mean the ranking is good.

When this report says “sample SD”, it means the ordinary sample standard deviation (divisor \(n-1\)) of a listed set of scores. That SD describes spread in the set. It is not a confidence interval. When a bootstrap procedure reports the fraction of resamples in which one model’s AUROC exceeds another’s, that fraction describes the resamples. It is not a p-value. No classical hypothesis test is reported.

## 2. Related work

This section follows the Stage 9 literature audit. Papers were included because they bear on the proposal’s gaps or on the implemented system. The audit is not a complete survey of 2024–2026 hallucination research. Bibliographic details that the audit did not confirm are marked unresolved. Author lists from the initial paper draft are not repeated here: that audit found that the draft’s lists for the papers it numbered [1]–[8] do not match the papers at the cited identifiers.

### 2.1 What the neighbouring methods actually do

**SelfCheckGPT** (Manakul, Liusie, and Gales, EMNLP 2023) scores a sentence by drawing extra samples from the same black-box model and measuring consistency. It does not use an external document, and it does not take a generator identity as a gate input.

**SAC³** (Zhang et al., Findings of EMNLP 2023) adds cross-model checking and question perturbation on top of self-consistency. It uses disagreement among models. It does not learn a fusion of that disagreement with a retrieval expert. The full author string was not re-copied from the PDF in the Stage 9 audit.

**FActScore** (Min et al., EMNLP 2023) breaks long-form text into atomic facts and checks them against a knowledge source. The draft’s title “Fine-grained Atomic Carving” is not the paper’s title. FActScore is an evaluation method for factual precision. It is not a two-expert consistency model.

**MiniCheck** (Tang, Laban, and Durrett, EMNLP 2024) fact-checks a sentence against grounding documents with a small NLI model. It is an evidence-side verifier. It has no cross-model gate. Its checkpoints were not present locally, and they were not downloaded.

**Medico** (Zhao et al., EMNLP 2024 System Demonstrations) retrieves web and knowledge-base evidence and revises spans. The Stage 9 audit read a reported detection F1 of 0.927–0.951. The draft’s author list, an F1 of 0.82, and a 3.8-second latency were not supported by that paper.

**Rowen** (Ding, Pang, Wei, Shen, and Cheng, SIGIR-AP 2025) computes a hybrid consistency score \(Z_{\text{Hybrid}} = Z_{\text{CL}} + \alpha Z_{\text{CM}}\) and retrieves only when that score indicates uncertainty. The weight \(\alpha\) is a scalar, not a claim-type network. Rowen corrects answers. It does not train a sentence detector. A “greater than 24%” transfer drop cited in the draft was not found in the sections read for Stage 9 and remains unverified.

**Evidence Graph Consistency (EGC)** (Shen, arXiv:2606.06748, 2026) evaluates five graph-consistency features on the full RAGTruth QA split: 5,767 responses from the same six models used here. The Stage 9 audit verified a qualitative reversal: Llama-2 features point in the expected direction, while GPT-4, GPT-3.5, and Mistral-7B reverse. Reported figures read from that paper include \(\Delta_m = -0.038\) for GPT-4, an AUROC of 0.244 for GPT-3.5, and a direction-corrected pooled AUROC of 0.669 after a family-level sign flip. The draft’s correlations \(r = +0.42\) and \(r = -0.31\), and the draft’s authors, were not in the paper. EGC does not train a gate. The arXiv page’s claim of an IEEE-proceedings venue was not independently confirmed in IEEE Xplore.

**BEACON** (Bera et al., arXiv:2606.07528, 20 April 2026) is a 31-feature gradient-boosting detector on multi-pass outputs of one model, without an external knowledge base. The abstract AUROC read in Stage 9 is 0.8123. The proposal’s “AUROC ≈ 0.87” does not match that abstract. The repository’s A1 baseline is a logistic regression on three cross-model signals. Calling A1 “BEACON-style” is a loose label in `rcgate/variants.py`. A1 does not reimplement BEACON.

**FLaG** (Ye et al., KDD 2026) softly assigns each instance to latent evidence groups and aggregates group-conditional signals. It uses hidden states and token logits. Its limitations section says it does not apply when only the final text is observable. RC-Gate is black-box. FLaG’s routing inputs are not claim type and generator identity.

**CAR-RAG** (Petrova, Koriakov, and State, IEEE BigData 2025) defines a policy from query category to a distribution over retrieval modalities and calls that policy a mixture of experts. In the system that was read, the weights are fixed. Learned instance-level gating is listed as future work. CAR-RAG mitigates hallucinations in retrieval. It is not a trained claim-level detector. A DOI was not on the pages inspected in Stage 9 and is not supplied here.

**Lynx / HaluBench** (Ravi et al., arXiv:2407.08488, 2024) introduces a benchmark of context–question–answer triples drawn from FinanceBench, DROP, COVID-QA, PubMedQA, HaluEval, and RAGTruth, generally one answer per row. This repository’s ADR-005 records a local HaluBench table of 14,900 rows with no model field. Those benchmarks were not run, because a cross-model panel cannot be formed without manufacturing answers.

**Itkin** (arXiv:2608.18115, June 2026) reports a token-level bidirectional GRU on RAGTruth, with an AUC of 0.840 and a ceiling near 0.845 across architectures. The Stage 9 audit read that ceiling as a statement about Itkin’s own feature set for token-level labelling. It does not establish a gap that RC-Gate fills.

**AuthenHallu** (Ren, Gruhlke, and Lauscher, arXiv:2510.10539, 2025; LREC 2026) is a 400-dialogue benchmark. It does not report the draft’s majority-vote versus GPT-4o comparison.

The Huang et al. survey (arXiv:2311.05232; ACM Transactions on Information Systems, 2025) is a survey. It is not a nine-signal detector, and it is not an ACL 2026 Findings paper by an “EdinburghNLP Consortium.” The draft’s Gap 2 numbers (0.94 AUC on TruthfulQA and about 0.44 / 0.48 on DROP and FinanceBench) were not found in a paper. They are unverified and are not results of this project.

Semantic entropy (Kuhn, Gal, and Farquhar, Nature, 2023) is a standard sampling-based uncertainty baseline. RC-Gate does not implement it. A DOI was not re-checked for this report.

**RAGTruth** (Niu et al., ACL 2024; arXiv:2401.00396, as used in the Stage 10 audit) is the corpus. The full author list was not re-transcribed from the ACL anthology. The repository record is `data/benchmarks/RAGTruth.md`. The release repository is <https://github.com/ParticleMedia/RAGTruth>.

### 2.2 What is and is not unexplored

**Literature finding.** Conditional routing for hallucination detection or mitigation is already published. FLaG routes over latent groups using hidden states. CAR-RAG gates retrieval modalities by query category. EGC shows that the direction of a consistency feature can depend on model family, and it adapts with a sign flip rather than a learned embedding.

**Literature finding.** Consistency and retrieval are already combined, at least as a cascade. Rowen uses a consistency score to decide when to retrieve. RC-Gate’s more specific design is to fuse both families inside one trained detector, with weights that are a function of claim type and generator identity only.

**Interpretation.** A learned generator embedding as the gate’s only generator input is a small residual relative to EGC’s analysis. It is not accurate to say that conditioning fusion on metadata, or combining consistency with retrieval, is wholly unexplored. The residual claim, stated narrowly in Section 9, is an untested design hypothesis: that forcing the weights to ignore the signal values will generalise better than letting a flat model see the same metadata. On the evaluated RAGTruth slice, that hypothesis is not supported. That does not show the hypothesis is false for every dataset or every gate.

Table 1 summarises the distinction. It is a comparison of methods, not a comparison of published AUROC numbers on a shared test set. This repository did not score SelfCheckGPT, MiniCheck, Lynx, FLaG, or the RAGTruth paper’s own detectors.

**Table 1. How neighbouring methods differ from RC-Gate A7.**

| Work | What it conditions on | Learned gate over two signal families? | Task this project would have to match |
| --- | --- | --- | --- |
| SelfCheckGPT | Samples of one model | No | Sentence detection from samples |
| SAC³ | Cross-model disagreement and question changes | No | Detection, not a retrieval fusion |
| FActScore, MiniCheck, Medico | A document or retrieved evidence | No | Evidence checking or correction |
| Rowen | A scalar \(\alpha\) on consistency, then retrieval | No | Answer mitigation |
| EGC | Model family, by analysis and a sign flip | No | Diagnostic probe on full RAGTruth QA |
| FLaG | Latent groups from hidden states | Yes, different inputs | White-box detection |
| CAR-RAG | Query category, hand-set weights | Proposed as future work | Retrieval mitigation |
| RC-Gate A7 | Claim type and generator id only | Yes, two linear experts | Not shown to beat its own flat control |

## 3. RC-Gate architecture

The description in this section is from the code (`rcgate/models/gate.py`, `rcgate/models/experts.py`, `rcgate/models/meta.py`, `rcgate/models/rcgate.py`), not from the proposal’s prose. A reader who has not trained a neural network can treat the gate as a small formula with two jobs: score each clue family, then decide from the metadata which score to emphasise.

### 3.1 Units and features

The unit of prediction is one sentence of one generated answer. The label is 1 when that sentence overlaps any human-annotated hallucination span, and 0 otherwise (Section 4).

Six signals, each scaled to the interval \([0, 1]\), are split into two families.

**Table 2. Feature families implemented in this repository.**

| Family | Signal | Repository definition |
| --- | --- | --- |
| Cross-model | `agree` | Fraction of the other generators whose text entails the sentence |
| Cross-model | `contra` | Largest contradiction probability among the other generators (a maximum, not a mean) |
| Cross-model | `sem_dist` | One minus the mean cosine similarity between the sentence and each other generator’s best-matching sentence |
| Evidence | `support` | Highest NLI entailment of the sentence against the top BM25 sentences of the supplied context |
| Evidence | `src_quality` | A constant that records where the evidence came from, not whether the sentence is true |
| Evidence | `conflict` | Highest NLI contradiction against those retrieved sentences |

On RAGTruth, evidence is the benchmark context. The code assigns `src_quality = 0.9` whenever the source is that context (`rcgate/signals/evidence.py`). On the corrected 800-row tables, and on the full QA file under the same rule, the value does not vary. It cannot change a ranking.

An arithmetic checker looks for an explicit expression such as `847 x 12 = 10164`. A sentence with no such expression is marked `unverifiable`. The checker does not guess. On the corrected 800-row slice it returns `unverifiable` on all 800 rows, including every numeric claim. On the full QA sentence set the Stage 10 audit found a checkable expression in 10 of 46,592 sentences (9 verified, 1 refuted). Arithmetic verification is not an active feature of the evaluated slice.

NLI and embeddings use `cross-encoder/nli-deberta-v3-small` and `sentence-transformers/all-MiniLM-L6-v2` (`configs/ragtruth.yaml`). Both run locally. The evaluated runs record no paid API calls.

Claim type is assigned by rules, not by a learned classifier (`rcgate/claims/claim_type.py`): numeric (quantities, rates, dates, arithmetic), entity (named things), extractive (text lifted from the context), abstractive (everything else). The proposal listed three categories. The code uses four (ADR-003). Extractive claims are, by that rule, sentences copied from the same context the evidence expert reads. That dependence is part of the design. It is the same information at training time and at test time.

### 3.2 The metadata-only gate

Let the claim-type embedding be a vector \(e_{\text{type}} \in \mathbb{R}^{4}\) and the generator embedding be \(e_{\text{gen}} \in \mathbb{R}^{4}\). The gate input is their concatenation

\[
x_{\text{meta}} = [e_{\text{type}} \,\|\, e_{\text{gen}}] \in \mathbb{R}^{8}.
\]

There is one extra generator row, reserved for an unknown generator. With RAGTruth’s six models, the generator embedding table has 7 rows. The gate is a multilayer perceptron

\[
h = \mathrm{ReLU}(W_1 x_{\text{meta}} + b_1), \qquad
g = W_2 h + b_2, \qquad
w = \mathrm{softmax}(g / \tau),
\]

with \(W_1\) mapping 8 dimensions to 16, \(W_2\) mapping 16 dimensions to 2, and temperature \(\tau = 1\) fixed in configuration. A learned temperature is not used, because it could push the weights toward one half each and hide the routing. The two components of \(w\) are \(w_{\text{cross}}\) and \(w_{\text{evid}}\), and they sum to 1.

The gate does not receive the six signal values. That constraint is the content of ADR-001, and a unit test checks that changing the signals does not change \(w\). A5 drops the generator embedding. A6 drops the claim-type embedding. A7 uses both. Those three are the only gating variants that were fit.

### 3.3 Experts and fusion

Each expert is a linear map from three signals to one logit (a score that is not yet a probability):

\[
z_{\text{cross}} = a_{\text{cross}}^{\top} s_{\text{cross}} + b_{\text{cross}}, \qquad
z_{\text{evid}} = a_{\text{evid}}^{\top} s_{\text{evid}} + b_{\text{evid}}.
\]

Default fusion multiplies weights by logits, not by probabilities (ADR-002):

\[
u = \big(w_{\text{cross}}\, z_{\text{cross}},\; w_{\text{evid}}\, z_{\text{evid}}\big), \qquad
\text{logit} = \phi^{\top} u + b_{\phi}, \qquad
P(\text{hallucinated}) = \sigma(\text{logit}).
\]

A probability-fusion option exists in configuration and was not the reported setting. Stage 8 records `fusion_input: logit`.

Counting parameters for the RAGTruth roster (4 type rows × 4, plus 7 generator rows × 4, plus the 8→16→2 gate, two experts, and a fusion head with bias) gives 233. Stage 8 records `n_parameters: 233` and `gate_input_dim: 8` for the A7 fit at split seed 0 and model seed 0. The user guide’s figure of 229 parameters matches the synthetic roster of five generators plus the unknown row. It is the wrong count for the RAGTruth model.

Training minimises binary cross-entropy with Adam and stops early on validation AUROC. During training, 10% of generator ids are replaced by the unknown row (`unk_dropout: 0.1` in the Stage 8 fit record). That dropout is an implementation detail. It is not a new calibration method.

Every prediction object returns \(P\), both weights, and both expert logits. Returning the weights makes the routing decision inspectable. Inspectability is not the same as a validated explanation of why a family is reliable. Section 6 returns to H3.

### 3.4 The variant ladder

**Table 3. Variants defined in `rcgate/variants.py`.**

| Id | What is fit | Role in the argument |
| --- | --- | --- |
| A0 | Logistic regression on the six signals | Flat fusion, no metadata |
| A1 | Logistic regression on the three cross-model signals | Family ablation. Not a reimplementation of BEACON |
| A2 | Logistic regression on the three evidence signals | Family ablation. Not a reimplementation of Medico |
| A3 | One validation-chosen scalar blend of the two expert logits | Static weight, shared by every claim |
| A4 | Histogram gradient boosting on the six signals plus one-hot claim type and generator id | Flat model that may use metadata. The critical control |
| A5 | Gate on claim type only | Ablation of A7 |
| A6 | Gate on generator id only | Ablation of A7 |
| A7 | Gate on claim type and generator id | The proposed model |
| A8 | Majority vote over judge columns | Never fit. Those columns are absent |

A4’s one-hot metadata is a 4-way claim-type indicator and a 7-way generator indicator, appended to the six signals (`rcgate/data/schema.py`). A tree can split on an indicator and then on a signal. A7 does not give the model new measurements. It constrains how metadata and signals may interact: the weights cannot depend on the signal values, and each expert sees only its own three signals.

## 4. Dataset and annotation methodology

### 4.1 What was evaluated

The fitted experiments use three parquet tables produced by the Stage 4 integrity correction, not the official RAGTruth split:

| Table | Rows | SHA-256 (Stage 10 inventory) |
| --- | --- | --- |
| `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` | 800 | `082e524ccc3c062cfcec423b00e970f5fa846eefa2646c3d0c4139cd73954245` |
| `..._s1.parquet` | 800 | `98aece3e06f20ed017178f2c9f092ef73584d0965953c63c2bbf073f57c9f917` |
| `..._s2.parquet` | 800 | `074cfcd5e769b4d1770ad7c50590bf1ae2dc780d59732ded70425cd68bcdd86b` |

From Stage 4 onward, the canonical fit table is seed 0. It has 800 sentences, 134 source questions, 57 positive labels (rate 0.07125), 402 QA claims, and 398 Summary claims. Every `claim_id` is sentence index 0: the slice is a first-sentence prefix, not a sample of whole answers. `cross_n_others` is 5 on every row, so each sentence is scored against the other five generators. QA and CNN/DM summaries are mixed. Recent News is absent. Each of the three tables contains 21 official test sources and 113 train sources (Stage 10). Models fit on these tables have already seen some official test questions. Their checkpoints cannot be scored on an untouched official test.

Positive counts on seed 0, counted in the Stage 9 audit from that parquet: GPT-4-0613, 1 of 134; GPT-3.5-turbo-0613, 5; Mistral-7B, 19; Llama-2-7B, 13; Llama-2-13B, 12; Llama-2-70B, 7. By rule-based type: numeric 38, entity 7, extractive 7, abstractive 5. `src_quality` is 0.9 on every row. `arithmetic_verdict` is `unverifiable` on every row.

The three tables are not three datasets. Stage 6 records claim overlap of 794, 788, and 794 rows among the three pairs, and question overlap of 133, 132, and 133.

### 4.2 How a sentence inherits a span label

RAGTruth annotates character spans, not sentences. This repository labels a sentence positive when its character offsets overlap any span of any of the four human types: Evident Conflict, Evident Baseless Info, Subtle Baseless Info, or Subtle Conflict (ADR-004). The sentence splitter is `re.split(r'(?<=[.!?])["\')\]]*\s+')`, with offsets kept. Stage 10 checked the official files: `response[start:end]` equals the span text for all 14,289 spans.

**Repository finding.** Of 2,927 QA spans, 904 (30.9%) overlap more than one sentence under this splitter, and none fall between sentences (Stage 10). Sentence labels are a defined coarsening of the official spans. They are not the official annotation unit. Papers that score responses or exact spans are not directly comparable.

Spans marked `implicit_true` are counted as hallucinations in this labelling, matching a strict reading of the RAGTruth definition. Stage 10 found 969 QA sentences whose only overlapping spans are implicitly true, about one fifth of the positive QA sentences. No sensitivity that drops those sentences was run.

### 4.3 Integrity corrections, and what they changed

Stage 4 compared the original signal tables with a corrected build. Two defects were real. Their effect on the headline ordering was small.

**Sentence alignment.** On seed 0, 11 first sentences had been concatenated with the following sentence (12 sentences on seeds 1 and 2). Labels did not change. The largest mean shift among the six signals on the whole slice was 0.015, against within-slice standard deviations of about 0.24 to 0.45 (`ragtruth_corrected_integrity_v1/VERDICT.md`).

**Prompt antecedents.** A de-aliaser had inserted the instruction words “Briefly” and “Summarize” into claim text. On seed 0, 90 of 800 claims were affected. After the fix, entity claims fall from 211 to 183. One positive row changes type. Labels stay at 57 positives. The integrity report’s claim-type AUROCs that depend on the old entity strings are historical.

**Interpretation of the integrity run.** Mean AUROC for A7 moved from 0.631 on the original tables to 0.638 on the corrected tables, under the same three-seed protocol and the same non-stratifying split. A4 remained ahead of A7 (0.740 then 0.706 at three-decimal reporting). The corrections repaired text and types. They did not create an A7 advantage. The statistical procedure used for that comparison was itself defective; Section 5 separates that issue from the text repair.

### 4.4 The official release, inspected and not fit

Stage 10 was read-only. Both official files match the hashes pinned in `rcgate/data/ragtruth.py`:

| File | Bytes | Rows | SHA-256 |
| --- | ---: | ---: | --- |
| `data/raw/ragtruth/response.jsonl` | 21,458,735 | 17,790 | `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073` |
| `data/raw/ragtruth/source_info.jsonl` | 15,117,971 | 2,965 | `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b` |

Every source has exactly six responses, one from each roster model, and one shared `split`. The split field is only `train` or `test`. The test set is 450 sources (150 per task) and 2,700 responses. Train is 2,515 sources and 15,090 responses. There is no official validation partition.

**Table 4. Official release counts (Stage 10, from the local files).**

| Task | Instances | Responses | Hallucinated responses | Spans |
| --- | ---: | ---: | ---: | ---: |
| QA (MARCO) | 989 | 5,934 | 1,724 | 2,927 |
| Summary, combined | 943 | 5,658 | 1,686 | 2,072 |
| Data-to-text (Yelp) | 1,033 | 6,198 | 4,254 | 9,290 |
| All | 2,965 | 17,790 | 7,664 | 14,289 |

The licence recorded in the Stage 10 audit is the MIT licence of the RAGTruth repository.

QA sentence construction with this repository’s splitter produces 46,592 sentences, 4,754 positive (rate 0.102). The official QA test contributes 6,143 sentences and 447 positives. Official QA test positives by generator are GPT-4 1/805, GPT-3.5 16/616, Mistral 82/882, Llama-2-7B 159/1,456, Llama-2-13B 88/1,238, and Llama-2-70B 101/1,146. GPT-4’s entire QA training support is 51 positive sentences. The model produced 52 positive QA sentences in the whole QA corpus.

**Table 5. Official QA test positives by generator and rule-based claim type (Stage 10). Entries are positive/sentences. This table is a support count. It is not a model evaluation.**

| Generator | Numeric | Entity | Extractive | Abstractive |
| --- | ---: | ---: | ---: | ---: |
| GPT-4 | 0/51 | 0/87 | 0/436 | 1/231 |
| GPT-3.5 | 7/133 | 0/46 | 1/249 | 8/188 |
| Mistral-7B | 37/302 | 10/87 | 2/258 | 33/235 |
| Llama-2-7B | 89/677 | 26/142 | 9/318 | 35/319 |
| Llama-2-13B | 45/547 | 19/150 | 2/278 | 22/263 |
| Llama-2-70B | 40/393 | 25/160 | 0/296 | 36/297 |

The Stage 10 support rule requires at least 30 training positives and at least 15 official-test positives before a generator-by-type cell is called estimable. Under that rule, 11 of 24 cells are estimable. All 11 are Mistral or Llama, on numeric, abstractive, or some entity cells. Every GPT cell fails the rule. Every extractive cell fails it. **Repository finding, and the decision that follows:** the official QA data do not adequately identify the proposed generator-by-type reliability surface. The audit stopped. No full-scale feature build or model fit was performed.

A score that is only the generator’s training positive rate has AUROC 0.632 on the official QA test sentences under the labelling above (Mann–Whitney; 447 positives, 6,143 sentences). Training rates run from 0.011 for GPT-4 to 0.155 for Llama-2-7B. **Interpretation.** A pooled AUROC can rank generators by how often they hallucinate. That is prevalence, not evidence that a signal family is conditionally reliable inside a generator. Within-generator AUROC is the comparison that separates the two. With one GPT-4 test positive, that comparison is not available for GPT-4.

## 5. Experimental design and baselines

### 5.1 Synthetic mechanism check

The synthetic generator is a simulator with planted conditional reliability (`configs/planted.yaml`, as recorded in `DECISIONS.md`). Evidence was made anti-informative for non-numeric types. On numeric claims, agreement was left nearly flat and contradiction was inverted, to imitate a shared-source numeric error. `sem_dist` was left uninformative. Evidence gaps were swept until flat logistic regression on numeric claims fell below 0.65 AUROC. The recorded operating point is A0 numeric AUROC 0.478.

**Interpretation.** A model that recovers a high evidence weight on numeric claims is recovering a pattern the authors wrote into the generator. The synthetic banner in `results/summary/synthetic.md` already says these numbers are not evidence for or against H1–H3 as claims about real model outputs. This report keeps that limit, and it adds the mechanism-recovery reading: success on the plant shows that the optimiser can find the plant. It does not show that real generators behave that way.

The synthetic summary (`results/summary/synthetic.md`; 5 tables × 5 seeds; the “95% CI” column of that file is the same historical renderer described below and is not reused here) reports mean test AUROC 0.756 for A0, 0.929 for A4, and 0.874 for A7 on the pooled synthetic slice. Numeric means recorded in `DECISIONS.md` are A0 0.478 and A7 0.855 (difference +0.377). Mean \(w_{\text{evid}}\) on numeric claims is 0.809. Leave-one-generator-out on the planted inverted generator (held-out id 4) gives A0 AUROC 0.171 and A7 AUROC 0.748 on the unknown-generator rows. Those two figures are a recovery of the inverted plant. They are not a result about an unseen real model. A4 remains ahead of A7 on the synthetic pooled mean (0.929 versus 0.874). The synthetic intervals in the milestone log are historical claim-level bootstrap summaries. They are not current estimates, and they are not repeated in the principal tables below.

### 5.2 Splits

Cross-model signals for a sentence use the other answers to the same source. A split that places those answers on both sides of the cut leaks the panel. Every experimental split in this repository therefore keeps a `question_id` (the RAGTruth `source_id`) inside one partition. The official `split` field was deliberately ignored (ADR-004, `data/benchmarks/RAGTruth.md`). Results are not the official RAGTruth split result.

The original function `grouped_split(..., stratify=True)` sorts groups by mean label, draws one permutation of that sorted list, and cuts the permuted list into blocks of about 60/20/20 groups. The permutation removes the sort. **Repository finding (Stage 6):** the flag does not stratify. Question ids are still disjoint across train, validation, and test.

The corrected splitter, `group_stratified_split`, stratifies on the group’s integer count of positive sentences. Inside each count stratum it assigns `round(0.6 n)` groups to train, `round(0.2 n)` to validation, and the remainder to test. A separate random stream is used per stratum, seeded by `SeedSequence([split_seed, stratum])`. Group ids are sorted before the shuffle. On the seed-0 table this yields 33 training positives, 9 validation positives, and 15 test positives on every seed. Strata of size 2 cannot enter all three partitions, so the seven positive claims in the count-3 and count-4 strata never enter validation. The test set stays a few positive claims above a 20% share. Stage 6’s mean absolute deviation of positive rates improved from 0.0171 (legacy) to 0.0112 (stratified). That drop of 0.0059 did not meet the pre-specified 0.01 bar for calling the balance change material. The test questions nevertheless changed: Jaccard overlap with the legacy test set was 0.078, 0.196, and 0.100 on seeds 0, 1, and 2.

Thresholds are chosen by the existing validation quantile rule, on validation scores only. Stage 8 confirmed that test rows are not an input to `tune_threshold`. AUROC does not depend on the threshold. F1 does. With about nine validation positives, the operating point is unstable (Section 7).

### 5.3 What each later stage held fixed

**Table 6. Experimental protocols. Rows are different experiments. Do not average a cell in one row with a cell in another.**

| Protocol | Fit data | Split | Seeds | What was refit | Uncertainty as reported then |
| --- | --- | --- | --- | --- | --- |
| Original M6, `results/summary/ragtruth.md` | Original 800-row tables, three overlapping slices | Legacy sort-then-permute; `stratify=True` does not stratify | 3; model seed equals split seed | A0–A7 | Claim-level bootstrap. The markdown “95% CI” column prints the mean AUROC, because the interval lookup misses. Paired comparison uses 500 resamples. `p_gt_0` is a bootstrap fraction |
| Stage 4 integrity, `ragtruth_corrected_integrity_v1/` | Corrected tables s0–s2 | Same legacy split | Same 3 | A0–A7 refit on corrected text | Same historical procedure, left untouched on purpose |
| Stage 5, `ragtruth_corrected_stats_v1/` | Stage 4 checkpoints reloaded | Same legacy split | Same 3; no refit | None | 95% question-grouped percentile bootstrap, 1000 resamples, per seed. Endpoints are not averaged. No p-value |
| Stage 6, `ragtruth_split_corrected_v1/` | Corrected tables s0, s1, and s2, one table per seed | Group-stratified | 3; model seed equals split seed | A0–A7 | Same question-grouped procedure as Stage 5 |
| Stage 7, `ragtruth_multi_seed_v1/` | Corrected table s0 only, every seed | Group-stratified | 20; model seed equals split seed | A0–A7 | Distribution over 20 partitions of one pool, plus per-seed grouped intervals. The distribution is not a confidence interval |
| Stage 8, `ragtruth_factorial_seed_v1/` | Corrected table s0 only | Group-stratified | 20 split seeds × 3 model seeds | A0–A7, 480 fits, no Stage 7 checkpoint reused | 60-cell distribution and paired grouped intervals. Principal analysis of this report |
| Stage 10 feasibility | Official JSONL, read-only | Official `split` field counted, not used for training | None | None | Support counts and a prevalence-only AUROC. Not a detector evaluation |

A8 is skipped in every row. The tables have no `judge_votes` column.

### 5.4 Bootstrap

From Stage 5 onward, a within-seed interval resamples `question_id` with replacement and recomputes AUROC on the drawn questions. A paired interval draws the questions once and scores both models on that draw. The fraction of draws with a positive difference is stored as a description of the draws. Stage 5, Stage 6, Stage 7, and Stage 8 each state that this fraction is not a p-value. Some draws are single-class and are left out of the quantile; the reports list how many of the 1000 requested resamples stayed finite.

The original file `results/summary/ragtruth.md` reports, for A7 minus A0 on the full slice, a difference of −0.050, an interval \([−0.210, 0.100]\), and `p_gt_0 = 0.415`. **Repository finding.** That interval is an average of per-seed claim-level endpoints, which Stage 5 retired as not a confidence interval. The value 0.415 is an average of bootstrap fractions. It is not a p-value. It belongs to the original protocol only. It is not a Stage 8 result, and it is not reused as an inferential claim in this report.

## 6. Results

### 6.1 Principal result: Stage 8

Stage 8 is the principal repeated-fit analysis. Every cell uses `ragtruth_corrected_integrity_v1_s0.parquet`. Split seeds 0 through 19 are crossed with model seeds 0, 1, and 2. Changing the model seed does not change the split. Changing the split seed does not change A7’s initial weights when the model seed is fixed, because the splitter never draws from the torch generator that the model seed resets. Logistic A0–A3 and the gradient-boosting control A4 did not move with the model seed on this protocol: their within-split AUROC sample SD is 0.0000. A5, A6, and A7 did move.

Test size is 15 positive sentences and 28 questions in every split. Claim counts move slightly (164 or 168 test sentences) when a short group changes partition. Positive totals do not: 33 train, 9 validation, 15 test.

**Table 7. Stage 8 test metrics over 60 cells (20 splits × 3 model seeds) on one 134-question pool.** The SD column is the sample standard deviation of the 60 cell values. It is not a confidence interval. The 20 splits are repeated partitions of the same questions, not 20 datasets.

| Variant | Mean AUROC | AUROC SD | AUROC min | AUROC max | Mean F1 | Mean precision | Mean recall | Mean ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0 | 0.6280 | 0.0597 | 0.5046 | 0.7320 | 0.1807 | 0.1156 | 0.4967 | 0.0347 |
| A1 | 0.6280 | 0.0461 | 0.5516 | 0.7181 | 0.1811 | 0.1263 | 0.5167 | 0.0279 |
| A2 | 0.5594 | 0.1125 | 0.3203 | 0.7468 | 0.1501 | 0.0944 | 0.4533 | 0.0358 |
| A3 | 0.6113 | 0.0974 | 0.3821 | 0.8022 | 0.1661 | 0.1200 | 0.3700 | 0.0343 |
| A4 | 0.6839 | 0.0656 | 0.5669 | 0.8017 | 0.1920 | 0.1919 | 0.3067 | 0.0957 |
| A5 | 0.6368 | 0.1108 | 0.3817 | 0.8443 | 0.1804 | 0.1288 | 0.4022 | 0.1668 |
| A6 | 0.5267 | 0.1074 | 0.2972 | 0.7163 | 0.1511 | 0.1054 | 0.3778 | 0.1495 |
| A7 | 0.5717 | 0.1247 | 0.3072 | 0.7983 | 0.1538 | 0.1040 | 0.3956 | 0.2099 |

A4 has the highest mean AUROC. A7’s mean sits below A0 and below A4. A6, the generator-only gate, is lower still, at 0.5267, close to chance. A5, the type-only gate, has mean AUROC 0.6368, close to A0 and below A4. A7’s mean precision is 0.1040 and its mean ECE is 0.2099, against 0.0347 for A0. The probabilities from the gate are poorly calibrated on this slice relative to logistic regression. Calibration here is a measured gap. It is not a new method.

**Table 8. Stage 8 paired test-AUROC differences, A7 minus the named baseline, on the same test sentences.** “Cells” are the 60 split–model pairs. “Split-level means” average the three model seeds inside a split and then summarise those 20 numbers. A count of interval positions is not one combined interval.

| Comparison | Mean over 60 cells | Sample SD of the 60 deltas | Cells with A7 higher | Intervals entirely above 0 | Intervals entirely below 0 | Intervals covering 0 | Split-level means with A7 higher |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A7 − A0 | −0.0563 | 0.1377 | 24 of 60 | 3 | 9 | 48 | 6 of 20 |
| A7 − A4 | −0.1122 | 0.1526 | 16 of 60 | 2 | 14 | 44 | 4 of 20 |

The mean paired difference favours A0 and, by a larger margin, A4. Most paired intervals still cover 0, which is expected with 15 positive test sentences and 28 questions. The intervals that do not cover 0 predominantly favour the baseline, especially against A4 (14 below, 2 above).

**Repository finding on variability.** A7’s 60 AUROC values range from 0.3072 to 0.7983. Inside a fixed split, the three model seeds still move A7: the median of the 20 within-split sample SDs is 0.1169, and the mean of those SDs is 0.1211. The sample SD of the 20 split-level mean AUROCs is 0.0684, smaller than the 60-cell SD because averaging three initialisations removes part of the initialisation noise. Three model seeds make each within-split SD a preliminary description. Stage 8’s own label for a method-of-moments split of the variance is explicit: it is a descriptive calculation on repeated partitions of one pool, not a variance component from independent datasets. The between-split share for A7 AUROC was not identified (the report records a null share). For the paired A7−A0 delta, the between-split share of cell variance is 0.146. For A7−A4 it is 0.308. Those shares are descriptions of this grid. They are not population estimates.

A4’s validation threshold across the 60 cells has median 0.0031 and maximum 0.5000. One Stage 7 checkpoint, A4 at split seed 6, had stored a threshold rounded to six decimal places. The exact validation cut was \(6.45 \times 10^{-6}\). Rounding it to \(6 \times 10^{-6}\) flipped one negative test sentence, changed F1 from 0.2857 to 0.2824, and left AUROC at 0.7168. Stage 8 stores the exact threshold and rescores from reloaded validation scores. The scientific ordering does not depend on that one F1 change.

### 6.2 Earlier protocols, reported separately

These figures are historical relative to Table 7. They document how the estimate moved as the pipeline was repaired. They are not additional independent replications.

**Original protocol** (`results/summary/ragtruth.md`). Mean AUROC at three-decimal reporting: A0 0.681, A1 0.705, A4 0.740, A7 0.631. The paired A7−A0 figure −0.050 with `p_gt_0 = 0.415` is the retired bootstrap summary of Section 5.4.

**Stage 4 corrected tables, legacy split, same estimator.** Three-decimal means in the integrity report: A0 0.667, A4 0.706, A7 0.638. Stage 5 recomputed the same checkpoints at four decimals: A0 0.6669 (seed SD 0.0627), A4 0.7062 (seed SD 0.1061), A7 0.6377 (seed SD 0.0997). Mean paired A7−A0 is −0.0292 (seed SD 0.1303). Mean paired A7−A4 is −0.0684 (seed SD 0.0186). All three paired intervals for each comparison cover 0. The seed SD is the spread of three heavily overlapping slices. It is not a confidence interval. On this corrected report, A7’s numeric-slice mean AUROC is 0.408. That slice mean uses the repaired claim types and the legacy split. Stage 8 does not re-break AUROC by claim type, so 0.408 is not a Stage 8 estimate.

**Stage 6, group-stratified split, three overlapping tables, model seed tied to split seed.** Mean AUROC: A0 0.6903 (seed SD 0.0253), A4 0.6890 (seed SD 0.0618), A7 0.5025 (seed SD 0.1588). Mean paired A7−A0 is −0.1878. Mean paired A7−A4 is −0.1865. No paired interval lies entirely above 0. Two of three A7−A0 intervals lie entirely below 0. This rerun uses a different test-question assignment from Stage 5 (Jaccard below 0.20). It still does not show an A7 advantage. Because seeds 1 and 2 use tables s1 and s2, Stage 6 is not a 20-seed study and is not the same experiment as Stage 7.

**Stage 7, one table, 20 splits, model seed tied to the split seed.** Mean AUROC: A0 0.6280 (SD of the 20 seeds 0.0608), A4 0.6838 (SD 0.0668), A7 0.5982 (SD 0.1427). Mean paired A7−A0 is −0.0298 (A7 higher on 10 of 20 seeds; 1 interval entirely above 0, 3 entirely below). Mean paired A7−A4 is −0.0857 (A7 higher on 7 of 20 seeds; 0 intervals entirely above 0, 4 entirely below). A0 matches the Stage 8 mean because A0 ignores the model seed. A7’s Stage 7 mean is higher than Stage 8’s 0.5717 because Stage 7 keeps only the initialisation whose seed equals the split seed. That coupling confounds split assignment with initialisation. Stage 8 is the unconfounded summary. A4’s Stage 7 mean (0.6838) and Stage 8 mean (0.6839) differ in the fourth decimal because Stage 7 averages statistics that were already rounded to four decimals. The ordering is the same.

### 6.3 Hypothesis outcomes

**Table 9. Evidence-based outcomes for the proposal’s hypotheses.** “Not established” means the evaluated data do not show the claim. It does not mean the claim has been shown false for every corpus.

| Hypothesis | Outcome | What the evidence is |
| --- | --- | --- |
| H1. Reliability depends on claim type and generator identity | Partially supported on planted synthetic data. Not established on the evaluated real data | The synthetic generator was built so that the trustworthy family depends on type, and the gate’s numeric evidence weight moved with that plant (mean \(w_{\text{evid}}\) 0.809). On the corrected RAGTruth slice, one GPT-4 positive, five abstractive positives, a constant `src_quality`, and an arithmetic checker that never fires do not identify a generator-by-type surface. The official QA audit, under a 30/15 support rule, leaves every GPT cell and every extractive cell non-estimable. Absence of support on these data does not prove the pattern never occurs elsewhere |
| H2. The learned gate outperforms flat fusion and judge voting, especially where flat fusion fails | The gate is not shown to outperform the flat metadata-capable control on the evaluated RAGTruth slice. The judge-voting clause is untested | Stage 8 mean AUROC is 0.6839 for A4 and 0.5717 for A7. Mean paired A7−A4 is −0.1122. A4 also leads on the synthetic pooled mean (0.929 versus 0.874). A8 was never fit. The “especially where flat fusion fails” clause referred to DROP and FinanceBench in the proposal. Those datasets were not run |
| H3. The learned weights are interpretable | The weights are inspectable. Scientific interpretability has not been validated | The forward pass returns \(w_{\text{cross}}\) and \(w_{\text{evid}}\). That shows the routing decision. It does not show that the preferred expert is the reliable one, and it does not identify a cause. The user guide’s statement that real-data weights sit near 0.45 is a pre-factorial description. Stages 5–8 do not re-report a gate-weight spread, so that description is not a Stage 8 measurement. On synthetic data the weights move with the planted type. That checks that training responded to the plant |

**Interpretation.** These outcomes do not universally refute metadata-conditioned gating. They bound this prototype: a metadata-only linear two-expert gate, on this feature set, on this slice, under this split. A gate that is allowed to see signal values, a nonlinear expert, or a different corpus was not the system under test. A loss for this constrained gate is not evidence about every conditional-weighting idea.

## 7. Robustness and reproducibility audit

The useful robustness work in this project is the sequence of repairs, not a claim that the AUROC has converged.

1. **Text and type.** Sentence concatenation and prompt-word leakage were measured. Labels did not change. The A4 > A7 ordering of the three-seed mean did not change.
2. **Dependence.** Claim-level bootstrap was replaced, from Stage 5 on, by question-grouped bootstrap. Averaging interval endpoints was stopped. Bootstrap fractions were no longer reported as p-values.
3. **The stratify flag.** Stage 6 showed that `stratify=True` did not stratify, replaced the splitter, and refit. The negative conclusion for A7 remained, with a lower A7 mean on that three-seed rerun.
4. **One pool versus many seeds.** Stage 7 drew 20 group-stratified partitions of the same 134 questions. The seed distribution is wide, and it is not a confidence interval for a shared mean.
5. **Two seeds that had been tied.** Stage 8 crossed split seed and model seed. A7’s mean fell from the Stage 7 figure of 0.5982 to 0.5717 once three initialisations were averaged. A0 and A4 did not move with initialisation. The loss to A4 remained.
6. **Serialization.** Rounding one threshold to six decimals changed one F1 and not AUROC. Checkpoints reloaded to the in-memory scores on 480 of 480 Stage 8 cells, with maximum absolute gap 0.

**Repository finding on provenance.** Stage 8 records git HEAD `47090018414f657bca8e5a43e97663feba2e5a7d`, a dirty working tree, and the statement that HEAD alone does not reproduce the run. The synthetic fingerprint was unchanged, and prior result directories were not rewritten. A reader who checks out that commit without the working-tree edits does not have the Stage 8 code path.

Repeated strings such as “Sure!” and “Unable to answer based on given passages.” appear in more than one partition (Stage 6). They are short, non-positive refusals. They were not removed. Their presence is a residual leakage of exact text, not of question identity.

**Interpretation.** The evaluation is careful about what a seed is. It is still one 134-question pool, one first-sentence prefix, and three neural initialisations. That is enough to show that A7’s score on this slice is unstable and that its mean sits below A4. It is not a multi-corpus replication.

## 8. Discussion

### 8.1 What the negative result does and does not say

On the evaluated slice, the flat metadata-capable control ranks hallucinated sentences better than the gate. The mean gap is about eleven hundredths of AUROC (Table 8), and A7’s own scores swing from roughly 0.31 to 0.80 depending on the split and the initialisation. A reviewer who treats Table 7 as the result is reading the repository correctly.

The same table does not support a field-level claim that “gating cannot work.” The evidence channels the proposal treats as the numeric solution are inactive: `src_quality` is constant, and the arithmetic checker never fires. Five of the six signals do vary (`agree`, `contra`, `sem_dist`, `support`, and `conflict`, with standard deviations from about 0.24 to 0.45 on the slice). The sixth signal and the arithmetic path do not. Generator identity is weakly supported: GPT-4 contributes one positive sentence in the slice, and A6’s mean AUROC is 0.5267. Claim type is a rule label, and an earlier bug moved some of those labels by inserting instruction words.

A4’s advantage is also the advantage of capacity and of seeing signals and metadata jointly. If the scientific claim is that the metadata-only constraint should beat an unconstrained model with the same metadata, Stage 8 is evidence against that claim on this slice. If the scientific claim is that no conditional weighting method can help, Stage 8 is the wrong experiment, because that method was not fit.

### 8.2 Synthetic results are a recovery test

The planted numeric failure was strengthened until a flat model looked bad, and the evidence gap was kept smaller than the cross-model gap so that the flat model would not simply ignore the broken family (`DECISIONS.md`). Under that construction, A7 beats A0 on numeric claims by 0.377 AUROC, and A7 survives a planted inverted generator where A0 falls to 0.171. A4, which is allowed to split on type and generator, still leads the pooled synthetic table (0.929 versus 0.874). **Interpretation.** The synthetic study is a unit test of the mechanism against a known function. Reporting it as generalisation to unseen generators, without the word “planted,” overstates it. The original milestone log did that. This report does not.

### 8.3 The full QA file does not repair identification

Stage 10 asked whether moving from 800 first sentences to the official QA release would identify H1. The files are complete, licensed, fully paneled (six generators on every source), and officially split. The blocker is support. The official QA test has one GPT-4 positive sentence. The whole QA corpus has 52. Annotating those responses again will not create hallucinations GPT-4 did not generate. Data-to-text contains many more GPT-4 hallucinations and is a different task, with null-value spans. It is not a silent substitute, and it was not evaluated.

EGC already reported a model-family reversal on this same QA split, at response level, and adapted with a sign flip. The GPT side of that reversal is exactly the side this sentence-level test cannot measure under the support rule. A full official-test run of A7 could still compare the constrained gate with A4 after prevalence is set aside, on the Mistral and Llama cells that have enough positives. That would be a different, narrower question. It was not run. Running it would not create the missing GPT-4 labels.

The 800-row checkpoints are also the wrong starting point for an official-test score: 21 of their sources are official test sources.

### 8.4 Contribution, stated narrowly

**Interpretation, offered as the contribution of the project as it stands.** RC-Gate is a metadata-conditioned two-expert research prototype. It is accompanied by a synthetic mechanism-recovery test and by a negative, unstable evaluation on a limited RAGTruth slice. The evaluation-integrity record — sentence alignment, antecedent leakage into claim type, a stratify flag that did not stratify, a bootstrap fraction reported under a p-value-like name, split seed separated from model seed, and a six-decimal threshold that changed one F1 — is part of what the project learned. That record does not, by itself, establish a novel field-wide method. The architectural idea is a specific assembly of known consistency features, NLI evidence, and conditional weighting. Neighbouring work already conditions fusion or retrieval on a category, a latent group, or a model family (Section 2).

The strongest accurate summary is the one in the abstract. A summary that says the method overcomes documented failure modes, or that the conditioning has not been proposed, is not supported by the sources audited in Stage 9 or by Tables 7 and 8.

### 8.5 Documents that still carry earlier claims

This report supersedes those claims. The following files were left unchanged on purpose. They are historical records or preserved source documents, not the current result.

| Document | What a reader can still find there | Status |
| --- | --- | --- |
| `RC-Gate_Project_Proposal.docx` | H1–H3 as open hypotheses; a novelty claim for the conditioning; baselines (random forest, XGBoost, SVM, reimplemented BEACON and Medico) that were not built | Preserved. Not the experimental record |
| `RC Gate_Intial_Research Paper Draft.pdf` | Gap analysis with author lists and numerical gap claims that Stage 9 did not verify; no repository experiment | Preserved. Not a results paper |
| `RC-Gate_UserGuide.pdf` | Code-aligned description, including a 229-parameter count that matches the synthetic roster, and a near-0.45 weight description that predates Stage 8 | Preserved. Parameter count is for the synthetic gate |
| `DECISIONS.md` | Milestone log, including the original paired interval and `p=0.415`, and the inverted-generator result described as the strongest result in the project | Historical log. Synthetic success there is the planted recovery of Section 5.1 |
| `docs/postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md` | Original means A4 0.740 and A7 0.631, and the retired `p = 0.415` wording | Historical M6 note. Superseded by Table 7 for the estimate |
| `docs/adr/001-metadata-only-gate.md` | The constraint, which still holds, together with “interpretable by construction” and the near-0.45 weight remark | The constraint is current. The interpretability sentence is stronger than H3’s outcome in Table 9 |
| `results/summary/ragtruth.md` | Original protocol. The column headed “AUROC (95% CI)” prints the mean | Historical. Do not cite as a current interval |
| `results/summary/synthetic.md` | Planted-data means, correctly bannered as synthetic. The leave-one-generator-out markdown header is wider than the rows, so the interval is concatenated into the AUROC cell | Synthetic only. Read the AUROC with `DECISIONS.md` |

The README now points here and no longer leads with the retired headline.

## 9. Threats to validity and limitations

**Table 10. Principal threats.** Each row is a reason a numerical claim in this report might fail to travel.

| Threat | What it affects | Why it is still open |
| --- | --- | --- |
| One question pool | External validity of every AUROC in Table 7 | 20 splits repartition 134 questions. They share training sentences. The sample SD is not a standard error for a new corpus |
| First-sentence prefix | Construct validity of the label | RAGTruth’s own position analysis places many hallucinations later in the answer. This slice keeps sentence index 0 |
| Span overlap, including implicit-true spans | Label definition | 30.9% of QA spans cross a sentence boundary. About one fifth of positive QA sentences are implicit-true only. No sensitivity was fit |
| Official split ignored, and 21 test sources inside the slice | Comparability | Published RAGTruth numbers use the official split. These checkpoints have seen some of those sources |
| Degenerate features | Internal validity of H1 | Constant `src_quality`; arithmetic inactive on the slice; rule-based types; one GPT-4 positive |
| Support on the full QA file | Identification of a larger study | The pre-specified 30/15 rule already fails for GPT-4, GPT-3.5, and extractive claims. Stage 10 did not fit a model |
| Three model seeds | Stability of A7 | Median within-split SD 0.1169 is a description of three draws. It is not a precise population SD |
| Thresholds | F1, precision, recall | About nine validation positives. A4’s threshold median is 0.0031 and its maximum is 0.5000. AUROC is the metric that does not depend on this choice |
| Missing external detectors | Relevance to the field | SelfCheckGPT, MiniCheck, Lynx, and RAGTruth’s own detectors were not scored. A4 is the internal control. It is not the published state of the art |
| A8 absent | H2’s voting clause | No judge columns. The clause is untested, not failed |
| Synthetic plant | Any sentence that cites +0.377 or 0.171 versus 0.748 | Those figures recover a simulator. A4 still wins the synthetic pooled mean |
| Dirty tree at Stage 8 | Exact reproduction from git HEAD | HEAD alone does not reproduce the run |
| Literature scope | Novelty | Stage 9 is not a systematic review. Unresolved items are listed in the references |
| No full-scale evaluation | Any claim about “RAGTruth” without a qualifier | The fitted results are the 800-sentence slice. The official QA counts are a feasibility audit |

Paper-safe summary of the limits. The real evaluation is one 800-sentence slice of RAGTruth, not the official split and not the full QA set. Fifty-seven sentences are labelled hallucinated, and one of those comes from GPT-4-0613. Source quality does not vary. The arithmetic checker verifies nothing in the slice. Claim types come from rules, and an earlier de-aliasing bug moved some of them. Test folds contain 15 positive sentences, so rank metrics move substantially when the 134 questions are repartitioned or the neural gate is reinitialised. The synthetic improvement recovers a pattern written into the simulator, and a flat tree model beats the gate there as well. Judge voting, HaluBench, FinanceBench, TruthfulQA, and HaluEval-QA were not run. These limits bound the prototype. They leave open whether a different conditioner, or the same conditioner on a larger and less degenerate sample, would behave differently. The official QA release, under the support rule in Section 4.4, is not that sample for the generator-by-type surface the proposal named.

## 10. Conclusion and future research

RC-Gate, as implemented, is a 233-parameter black-box gate over two linear experts. The gate input is a claim-type embedding and a generator embedding. Fusion is a linear map on trust-weighted logits. The implementation matches that specification, and tests enforce the metadata-only constraint.

H1 is partially supported on data that were generated to contain the pattern, and it is not established on the real slice that was fit or on the official QA support counts. H2 is not shown for the flat metadata-capable control: Stage 8’s mean AUROC is 0.6839 for A4 and 0.5717 for A7, with mean paired difference −0.1122. The judge-voting half of H2 was never run. H3 holds only in the mechanical sense that the weights can be printed. Their scientific interpretability was not validated.

The next research step, if one is taken, is not another fit on this slice and not a download of a larger detector aimed at raising AUROC. Stage 10’s decision stands: the available QA data do not adequately identify the proposed hypothesis, so a suitable dataset or a narrower question is required before any further method experiment. A narrower question that could be pre-registered, and that this report does not answer, is whether the constrained gate beats A4 inside the Mistral and Llama cells that meet a support floor, on the official QA test, with `src_quality` removed and arithmetic left out of the features. That experiment was not authorised and was not run. Until it exists, the honest description of the project is the contribution statement in Section 8.4.

Publication readiness has not been established.

## 11. References

Verification status is the status after the Stage 9 and Stage 10 audits. This report did not repeat those literature searches and did not invent missing DOIs, author lists, or venues.

1. Manakul, Potsawee; Liusie, Adian; Gales, Mark. “SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models.” EMNLP 2023. <https://aclanthology.org/2023.emnlp-main.557/>. Abstract-level check in Stage 9.
2. Min, Sewon; Krishna, Kalpesh; Lyu, Xinxi; Lewis, Mike; Yih, Wen-tau; Koh, Pang Wei; Iyyer, Mohit; Zettlemoyer, Luke; Hajishirzi, Hannaneh. “FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.” EMNLP 2023. <https://aclanthology.org/2023.emnlp-main.741/>. Abstract-level check in Stage 9. The draft title does not match.
3. Zhang et al. “SAC³: Reliable Hallucination Detection in Black-Box Language Models via Semantic-aware Cross-check Consistency.” Findings of EMNLP 2023. <https://aclanthology.org/2023.findings-emnlp.1032/>. **Unresolved:** the full author string was not re-copied from the PDF.
4. Tang, Liyan; Laban, Philippe; Durrett, Greg. “MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents.” EMNLP 2024. <https://aclanthology.org/2024.emnlp-main.499/>. Not a full re-read in Stage 9.
5. Zhao, Xinping; Yu, Jindi; Liu, Zhenyu; Wang, Jifang; Li, Dongfang; Chen, Yibin; Hu, Baotian; Zhang, Min. “Medico: Towards Hallucination Detection and Correction with Multi-source Evidence Fusion.” EMNLP 2024 System Demonstrations. DOI 10.18653/v1/2024.emnlp-demo.4. arXiv:2410.10408.
6. Ding, Hanxing; Pang, Liang; Wei, Zihao; Shen, Huawei; Cheng, Xueqi. “Rowen: Adaptive Retrieval-Augmented Generation for Hallucination Mitigation in LLMs.” SIGIR-AP 2025. DOI 10.1145/3767695.3769500. arXiv:2402.10612. **Unresolved:** the draft’s 24% transfer drop was not verified.
7. Shen, Jianru. “Evidence Graph Consistency in Retrieval-Augmented Generation: A Model-Dependent Analysis of Hallucination Detection.” arXiv:2606.06748, 2026. DOI 10.48550/arXiv.2606.06748. **Unresolved:** IEEE Xplore publication was claimed on the arXiv page and not separately confirmed. The draft’s correlation figures are not part of this citation.
8. Bera, Naveen; Pulijala Sai Nikhila; Kondaguduru Abhiram; Shaik Gayaz Ali; Shoaib Sadiq Salehmohamed; Shaik Mohammed Omar; Jinal Prashant Thakkar; Hansika Aredla; Shalmali Ayachit. “BEACON: Behavioral Entropy Aggregation for Cross-Model Hallucination Detection in Large Language Models.” arXiv:2606.07528, 20 April 2026. DOI 10.48550/arXiv.2606.07528. Abstract AUROC read as 0.8123. The coauthor order is the arXiv record as transcribed in Stage 9.
9. Ye, Wentao; Li, Liyao; Xiao, Zhiqing; Zhu, Muzhi; Hu, Jiaqi; Shen, Zhanming; Hu, Xiaomeng; Du, Sean; Wang, Haobo. “FLaG: Fine-Grained Latent Grouping for Hallucination Detection.” KDD 2026. DOI 10.1145/3770855.3818137. arXiv:2606.00301.
10. Petrova, Tatiana; Koriakov, Dmitrii; State, Radu. “CAR-RAG: Category-Aware Hybrid Retrieval-Augmented Generation for Hallucination Mitigation.” IEEE BigData 2025. **Unresolved:** a DOI was not on the pages inspected.
11. Itkin, Igor. “Temporal Multi-Signal Fusion for Token-Level Hallucination Detection.” arXiv:2608.18115, June 2026; Research Square rs-10303630.
12. Ren, Yujie; Gruhlke, Niklas; Lauscher, Anne. “Detecting Hallucinations in Authentic LLM-Human Interactions.” arXiv:2510.10539, 2025; LREC 2026, <https://aclanthology.org/2026.lrec-1.475/>.
13. Huang, Lei, and coauthors. “A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions.” arXiv:2311.05232; ACM Transactions on Information Systems, 2025. **Unresolved:** a DOI was not re-checked, and the full author list was not re-transcribed. This survey is not a pooled nine-signal detector.
14. Ravi, Selvan Sunitha, and coauthors. “Lynx: An Open Source Hallucination Evaluation Model.” arXiv:2407.08488, 2024. **Unresolved:** the full author list was not re-transcribed.
15. Niu et al. “RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models.” ACL 2024. arXiv:2401.00396, as cited in the Stage 10 audit. Repository: <https://github.com/ParticleMedia/RAGTruth>. **Unresolved:** the full author list and a DOI were not re-fetched from the ACL anthology.
16. Kuhn, Lorenz; Gal, Yarin; Farquhar, Sebastian. “Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation.” Nature, 2023. **Unresolved:** the Nature PDF was not re-opened for this report, so no DOI is given.

Items deliberately not cited as findings: an ACL 2026 “pooled 9-signal detector”; the draft’s author lists; EGC’s \(r\) values; Rowen’s 24% transfer drop; Medico’s 3.8-second latency; BEACON’s 0.87 AUROC.

## Appendix A. Where the numbers live

| Claim in this report | Primary artefact |
| --- | --- |
| Stage 8 means, SDs, and paired deltas | [Stage 8 report](../results/summary/ragtruth_factorial_seed_v1/report.md) |
| Stage 7 coupled-seed distribution | [Stage 7 report](../results/summary/ragtruth_multi_seed_v1/report.md) |
| Stage 6 stratified three-seed refit | [Stage 6 report](../results/summary/ragtruth_split_corrected_v1/report.md) |
| Stage 5 grouped intervals on Stage 4 checkpoints | [Stage 5 report](../results/summary/ragtruth_corrected_stats_v1/report.md) |
| Text and type corrections | [Stage 4 verdict](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md) |
| Original protocol, including `p_gt_0 = 0.415` | [Original RAGTruth summary](../results/summary/ragtruth.md) |
| Synthetic planted means and leave-one-generator-out | [Synthetic summary](../results/summary/synthetic.md), [DECISIONS.md](../DECISIONS.md) |
| Official QA support counts | Stage 10 feasibility audit (read-only; not a result directory of fitted models) |
| Literature distinctions | Stage 9 novelty audit |

Stages 9 and 10 were documentation audits. They did not add a fitted-model directory under `results/summary/`.

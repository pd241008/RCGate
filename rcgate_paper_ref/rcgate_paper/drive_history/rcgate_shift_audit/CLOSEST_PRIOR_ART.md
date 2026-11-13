# Closest prior art

**Date:** 23 October 2026.  
The source-dependence STOP in `research/novelty_audit/GO_NO_GO_DECISION.md` stands. This file does not reopen it.

## 1. What would count as the same contribution

The candidate needs all of the following:

1. Inputs are externally observable cross-model agreement or contradiction, plus NLI or evidence-grounding scores. Hidden states and single-model samples do not qualify.
2. A reliability-conditioned rule combines those families, and the paper compares that rule with flat fusion or stacking on the same features.
3. The test holds out generator, task, and source groups.
4. The label is context faithfulness of a RAG response, not world factuality and not answer selection.

No opened paper has all four. Several have one or two, and those are enough to retire a method claim for the gate.

## 2. Dubanowska et al., Findings of EMNLP 2025

- **Paper:** Representation-based Broad Hallucination Detectors Fail to Generalize Out of Distribution. Zuzanna Dubanowska, Maciej Żelaszczyk, Michał Brzozowski, Paolo Mandica, and Michał P. Karpowicz. Findings of EMNLP 2025, pages 17563–17575. DOI [10.18653/v1/2025.findings-emnlp.952](https://doi.org/10.18653/v1/2025.findings-emnlp.952). arXiv:2509.19372. No code repository was found.
- **Task:** Response-level hallucination detection from model-internal activations.
- **Inputs:** Residual-stream activations, ReDeEP token features, SAPLMA-style probes, SAE features. Not cross-model text and not an external NLI score.
- **Method:** Linear probes, random forests, and re-evaluation of published internal detectors.
- **The RAGTruth finding that matters:** **Paraphrase of §3.** Data-to-text has a much higher hallucination rate than QA or summarization. A naïve classifier that predicts "hallucinated" exactly when the task is data-to-text matches ReDeEP's pooled AUC and can beat it on correlation. A linear probe on Llama-2-7B-Chat activations predicts the JSON task with AUC 1.0. Pooled RAGTruth scores can be task detection.
- **Shift protocol:** Cross-task within RAGTruth, and RAGTruth versus SQuAD and Dolly. **Paraphrase of §4.1 and the conclusion:** outside the training distribution, the analyzed methods, including linear probes, are close to random.
- **Guidelines, §4.3:** compare with a naïve feature classifier and with linear probes; tune on one dataset and evaluate on another; prefer span localization over one response label.
- **Authors' limit:** they do not claim OOD detection is impossible for every future method. They do claim it for the internal methods they tested.
- **Relation to RC-Gate:** This is an evaluation constraint, not a fusion method. Any new RC-Gate number that pools QA, summary, and data-to-text is exposed to the naïve task classifier they define.

## 3. Bakman et al., ACL 2025

- **Paper:** Reconsidering LLM Uncertainty Estimation Methods in the Wild. Yavuz Faruk Bakman, Duygu Nur Yaldiz, Sungmin Kang, Tuo Zhang, Baturalp Buyukates, Salman Avestimehr, and Sai Praneeth Karimireddy. ACL 2025, pages 29531–29556. DOI [10.18653/v1/2025.acl-long.1429](https://doi.org/10.18653/v1/2025.acl-long.1429).
- **Code:** [github.com/duygunuryldz/uncertainty_in_the_wild](https://github.com/duygunuryldz/uncertainty_in_the_wild), MIT as reported on the GitHub page. Not run.
- **Task:** Deploy uncertainty estimates for hallucination or error detection. Short-form QA (TriviaQA, Natural Questions, GSM8K) and a long-form adaptation (FActScore-Bio, LongFact-Objects).
- **Inputs:** 19 uncertainty methods from one generator: probabilities, consistency, internal state, verbalized confidence. Not a second model's answer and not NLI against retrieved evidence.
- **Shift:** Thresholds chosen on TriviaQA, Natural Questions, or GSM8K and tested on another. Most methods keep low absolute recall error in-domain and degrade when calibration and test distributions differ. Probability and consistency methods are more stable than internal-state and self-check methods. Only MARS, semantic entropy, and eccentricity stay low-error across the calibration sets they report.
- **Fusion:** §6 ensembles the 19 scores. With 100 labeled calibration items, normalization or isotonic calibration plus a mean or a linear model gains up to about 0.06 PRR over the best single method in Table 2. A decision tree does not. **Paraphrase of the conclusion:** simple ensembling is a practical improvement, and further ensembling strategies are future work.
- **Relation to RC-Gate:** Score stacking and calibration shift are published. A claim that "combining signals" or "robust thresholds" is the contribution is not available. Their scores are not RC-Gate's two families.

## 4. Han et al., Findings of EMNLP 2025

- **Paper:** Simple Factuality Probes Detect Hallucinations in Long-Form Natural Language Generation. Jiatong Han, Neil Band, Muhammed Razzak, Jannik Kossen, Tim G. J. Rudner, and Yarin Gal. Findings of EMNLP 2025, pages 16209–16226. DOI [10.18653/v1/2025.findings-emnlp.880](https://doi.org/10.18653/v1/2025.findings-emnlp.880).
- **Code:** [github.com/JThh/fact-probe](https://github.com/JThh/fact-probe). License not checked. Not run.
- **Task:** Claim-level factuality in long-form generation. Labels come from retrieval verifiers (FActScore / web search), which the paper treats as an oracle.
- **Inputs:** Hidden states of the generator or a smaller encoder, at selected tokens or layer groups. Classifiers are logistic regression and XGBoost.
- **Shift:** Probes trained on one model's activations are applied to another model's generations, including GPT-4o-mini text encoded by a smaller open model. Table 1 reports in-domain AUROC about 0.73–0.76 by training-model size, and OOD AUROC about 0.62–0.71 when the generator is GPT-4o-mini. They also train on LongFact and test on FActScore.
- **Relation to RC-Gate:** This is the lightweight-probe and cross-generator comparison. It uses internals. RC-Gate's constraint is black-box text. Beating or matching these probes is not possible without hidden states, and matching their task is world factuality, not RAGTruth span overlap.

## 5. Chen et al., ACL 2026 (TRIVIA+)

- **Paper:** Rethinking Evaluation for LLM Hallucination Detection: A Desiderata, A New RAG-based Benchmark, New Insights. Wenbo Chen, Veena Padmanabhan, Tootiya Giyahchi, Elaine Wong, and Leman Akoglu. ACL 2026, pages 14912–14931. DOI [10.18653/v1/2026.acl-long.680](https://doi.org/10.18653/v1/2026.acl-long.680).
- **Release:** The paper text points at `github.com/Wenbo11/TriviaPlus`. The Amazon Science repository [hallucination-benchmark-trivialplus](https://github.com/amazon-science/hallucination-benchmark-trivialplus) states CC BY-NC-ND 4.0. Counts on that page: 2,263 train, 316 valid, 645 test, 3,224 total. The repository was not downloaded.
- **What the benchmark is:** RAG responses with long contexts. Table 2 in the paper gives median context 2.8K characters, mean 9.3K, max 94K, hallucination rate 35%, three LLMs, several source domains. Sentence labels are Supported, Contradicted, Not Mentioned, and Supplementary, then mapped to a binary response label. The body says four noisy-label schemes; the Anthology abstract snippet said three. This audit follows the PDF body.
- **Findings that bind RC-Gate:** Organic hallucinations are harder than synthetic ones. LLM-as-a-judge is competitive. Sample-dependent label noise hurts. Long-context RAG benchmarks and label-noise tests are not an open claim.
- **Fit to the candidate:** Three generators do not form the six-way same-source panel RC-Gate's `agree` / `contra` / `sem_dist` features require. The label is sentence faithfulness aggregated to a response, not RAGTruth character-span overlap. The non-commercial no-derivatives license is a use constraint. TRIVIA+ can be a transfer set only if the signal definition and the label are rewritten and the license is accepted. It cannot host the current feature extractor unchanged.

## 6. Fadeeva et al., Findings of ACL 2026 (FRANQ)

This is the closest method.

- **Paper:** Faithfulness-Aware Uncertainty Quantification for Fact-Checking the Output of Retrieval-Augmented Generation. Ekaterina Fadeeva, Aleksandr Rubashevskii, Dzianis Piatrashyn, Roman Vashurin, Shehzaad Dhuliawala, Artem Shelmanov, Timothy Baldwin, Preslav Nakov, Mrinmaya Sachan, and Maxim Panov. Findings of ACL 2026, pages 6814–6836. DOI [10.18653/v1/2026.findings-acl.338](https://doi.org/10.18653/v1/2026.findings-acl.338).
- **Code:** [github.com/stat-ml/rag_uncertainty](https://github.com/stat-ml/rag_uncertainty), as printed in the paper. Not opened or run. License unknown.
- **Target:** Probability that an atomic claim is factually true. Faithfulness to the retrieved context is an intermediate variable, not the label. The paper says RAGTruth marks unsupported content even when it is factually correct, and FRANQ refuses that collapse.
- **Rule, equation (4):** `P(faithful) * UQ_faithful + (1 - P(faithful)) * UQ_unfaithful`. Faithfulness is AlignScore (Zha et al., ACL 2023). For long-form QA, the two uncertainty terms are max claim probability given the retrieval, and token probability with the retrieval removed. For short-form QA they are semantic entropy and the sum of eigenvalues. Isotonic calibration can be fit separately on faithful and unfaithful claims.
- **This is reliability-conditioned fusion.** The weight is a measured faithfulness score. The branches are different uncertainty estimators. It is not a metadata embedding of generator identity.
- **Baselines include stacking.** XGBoost is trained on the three FRANQ components and, separately, on all unsupervised UQ features. Appendix D.2 says the first tree splits on AlignScore and then on the branch that FRANQ hand-codes. The paper reports that condition-calibrated FRANQ beats those XGBoost models across the training sizes in Figure 3. Exact table cells were not re-copied beyond that qualitative result and the method description.
- **Data and shift:** Long-form set of 76 questions (44 hard RAGTruth questions plus 32 generated how-to questions), labeled for factuality with automatic labels and manual review of false or unverifiable claims. Short-form: NQ, PopQA, TriviaQA, SimpleQA, several models reported separately. They also shuffle and corrupt retrievals. They do not hold out a generator family while forbidding its outputs from training, and they do not hold out RAGTruth task types.
- **Limits the authors state:** Ambiguous claims, bad retrieval, and miscalibration still hurt. Some variants need a small labeled calibration set. Claim extraction uses GPT-4o.
- **Difference from the candidate that is real:** no panel of other generators; the label is factuality; the grounding model is AlignScore rather than the local DeBERTa NLI max/mean; the conditioning is a fixed formula, and they already show it can beat a tree on those features.
- **Difference that does not remain:** "nobody has conditioned a detector on whether evidence supports the claim, and compared that with stacking."

## 7. Adjacent fusion papers, read less deeply

**HALT-RAG** (Saumya Goswami and Siddharth Kurra, arXiv HTML [2509.07475](https://arxiv.org/html/2509.07475)). Preprint. No proceedings record was found. Two frozen NLI models plus lexical features train a calibrated, task-specific meta-classifier on HaluEval. Reported out-of-fold F1 is 0.7756, 0.9786, and 0.7391 on summarization, QA, and dialogue. There is no cross-model generator panel and no RAGTruth source split. It does occupy "calibrated fusion of NLI scores with a small classifier and an abstention threshold."

**Finch-Zk** (Aman Goel, Daniel Schwartz, and Yanjun Qi, EMNLP Industry 2025, [2025.emnlp-industry.139](https://aclanthology.org/2025.emnlp-industry.139/)). Abstract only. Fine-grained cross-model consistency without external knowledge. It blocks a cross-model-only novelty claim. It does not fuse NLI evidence.

**CCUF** (SIGIR record [10.1145/3805712.3809846](https://dlnext.acm.org/doi/10.1145/3805712.3809846)). Abstract only, so it is not a full-text comparison. The abstract says individual-model uncertainty is calibrated by cross-model agreement for factoid answer selection. That is consistency-calibrated uncertainty, not span-level NLI fusion.

## 8. Judgment

| Piece of the candidate | Status after reading |
|---|---|
| External cross-model text agreement | Used by Finch-Zk and, at abstract level, CCUF. Not paired there with an NLI evidence expert. |
| NLI / evidence grounding | HALT-RAG, FRANQ's AlignScore, and the local evidence expert. |
| Conditioned combination versus flat stacking | FRANQ versus XGBoost; Bakman linear ensemble versus a tree; local A7 versus A4. |
| Held-out task and source on RAGTruth | Dubanowska for internal features. Not for these black-box families. |
| Held-out generator with hidden states | Han et al. |
| The full four-part candidate | Not found in the texts opened. |

**Inference:** the untested cell is an evaluation cell. It is whether the existing black-box families survive source-disjoint, per-task, and generator-held-out tests on RAGTruth span labels. It is not an unoccupied architecture. A new gate that reweights the same scores is stacking unless a pre-registered comparison shows the constraint beats a flat model on those scores. The local Stage 8 result is already a negative example of that comparison for metadata routing.

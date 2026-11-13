# Positioning and limitations

**Date:** 23 October 2026.  
**Decision of this audit:** keep the fixed question, and keep it an evaluation. Do not start a new detector, a new gate, or a novelty claim.

The name stays RC-Gate. The source-dependence programme stays STOP. The historical A7 gate stays a comparator from the old slice. It is not evidence about this question.

## 1. Strongest overlap

Three opened works come closest, and none of them is the experiment.

**Kostka and Chudziak, UAI 2026,** is the closest rule. A weak judge scores how well an atomic claim is entailed by a reference document. A Score Deviation penalty lowers that score when the ensemble's claim scores disagree. The primary ensemble is five copies of one Gemini model. Labels come from a stronger model, on FACTS Grounding, and the reported success is recall at a certified false-discovery rate, not span discrimination. A heterogeneous-model ablation exists. It is not a source-grouped RAGTruth test and not a curve over how many distinct generators are worth calling.

**Finch-Zk, EMNLP Industry 2025,** is the closest costed peer-consistency system. Diverse sampler models and semantically equivalent prompts produce a fine-grained consistency judgment, with an ablation on how many samplers are used and a latency and dollar table. The paper's defining constraint is that no external knowledge is used. It therefore cannot say whether peer agreement adds anything once a grounding score is already in the model. The label is FELM factuality, not a RAGTruth span.

**GASP, arXiv:2607.04223,** is the closest head-to-head of grounding against consistency on RAGTruth sentence labels. Chunk-level NLI and a four-sample SelfCheckGPT-style score are baselines for a context-perturbation detector. On the reported Qwen2.5-1.5B span comparison, chunk NLI reaches AUC 0.677 and the consistency baseline reaches 0.486. The samples are new draws from the scorer under the same context. They are not the other RAGTruth generators' answers to that source. The sample is 400 summarization and data-to-text responses, grouped by response rather than by source. Adding perplexity and length to the grounding features is not the peer-agreement increment.

SAC³ occupies the older form of the same idea: a verifier model's answers catch hallucinations that one model's self-consistency misses, on factuality benchmarks that are not RAG span labels.

## 2. What is already unsafe to claim

- A new architecture that mixes peer agreement with evidence grounding. FRANQ already conditions uncertainty on a faithfulness score and compares that rule with a tree. Bakman et al. already find a linear stack of uncertainty scores enough. The local A7 gate already lost to flat fusion on the old 800-sentence slice. That local result is not this experiment, and it is also not a reason to design another mixer.
- "Cross-model consistency detects hallucinations." SAC³, SelfCheckGPT, and Finch-Zk have published that, without retrieved evidence.
- "Evidence NLI detects RAGTruth hallucinations." Itkin, GASP's chunk-NLI baseline, RLSeek, and the RAGTruth finetuned detector occupy grounding-based detection. Itkin's own ablation gives BiGRU only about 1.3 AUC points for adding NLI and language-model features on top of text features. Extra signals can be small.
- "Held-out generator" as a phrase. Itkin trains on five RAGTruth generators and tests the sixth, and does not describe removing the test sources from the other five. Dubanowska et al. show that a pooled RAGTruth score can track the data-to-text rate. Shen shows an evidence-structure score reversing between Llama-2 and GPT-class models on the QA split alone. Generator and task have to be reported as separate, source-safe slices.
- World truth and context faithfulness as one label. FRANQ states the distinction and chooses factuality. RAGTruth's `implicit_true` field exists because a span can be unsupported by the context and still be true. This question is about the human span annotation, which is a grounding label.

## 3. The distinction that remains

The unoccupied cell is a measurement, not a method.

On the same RAGTruth sentences, with each source or query kept on one side of every split:

1. Score evidence grounding alone.
2. Add agreement features computed only from the other models' already stored responses to that same source and query.
3. Report the increment separately by generator and by task, against a task-rate baseline so a pooled number cannot rediscover data-to-text.
4. Repeat the peer features with fewer peers, and record the inference that those peers would have cost if they were not already in the corpus.

Sibling responses used as features must not contribute their labels to training, threshold choice, or feature selection. A generator holdout is not met by training on the other five answers to the test sources.

If that increment is absent, unstable across generators, or confined to one task, the honest result is that peer agreement is not worth the extra inference once grounding is measured. That result would still be the finding. It would not support a "substantially better detector" claim.

If the increment is present, the defensible statement is still narrow. It would be an empirical property of two published feature families on one corpus. It would not be a new gating algorithm. Finch-Zk and Kostka and Chudziak already occupy the neighbouring designs, so a positive number has to be described as a comparison, not as the invention of peer agreement or of evidence grounding.

## 4. Maximum defensible scope

A careful, pre-registered evaluation on the existing RAGTruth responses. No new generator calls unless a later prompt approves them. No paid API. No new checkpoint download. The historical gate may appear only as a named comparator, and only after the flat grounding-only and grounding-plus-peer models are the primary contrast.

Publication as a methods paper is weak. The wording difference between "peer agreement," "cross-model consistency," and "ensemble deviation" does not create a gap. An evaluation note is the largest product this literature check supports, and only if the protocol in the next stage is frozen before any test number is computed.

## 5. Limits of this audit

- This is not a systematic review and not a cited-by census. Semantic Scholar citation counts were not downloaded.
- Repositories were not cloned or executed. Licenses are recorded only where the opened page stated them.
- Finch-Zk, RLSeek, and Kostka and Chudziak had no code page in the searches that were opened.
- FRANQ's full PDF was not re-read page by page in this pass. The method decomposition was opened on the DOI HTML, Appendix D.2 was in the PDF extract, and the 23 October shift audit's fuller notes were checked against those pages.
- Itkin's leave-one-generator description does not state the source rule. This audit does not upgrade that silence into a demonstrated leak.
- GASP's 0.486 consistency AUC is one span-level comparison for one scorer. It is not a universal constant.
- The `rag-rack` blog was excluded. Its AUROC figures are not findings of this audit.
- No number in the local Stage 8 summary is reused as a result about peer agreement given grounding.

## 6. What not to do next

- Do not rename the project or replace the question.
- Do not revive source-dependence modelling.
- Do not build a gate in order to have a novelty sentence.
- Do not treat same-model resamples, question paraphrases, or passage-to-passage similarity as if they were the other generators' answers.
- Do not pool QA, summarization, and data-to-text into one headline score.
- Do not choose features, thresholds, or models on the test labels.

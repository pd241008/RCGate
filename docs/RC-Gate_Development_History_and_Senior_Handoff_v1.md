# RC-Gate development history and senior handoff

**Version 1.** 10 October 2026.

**Purpose.** This is the handoff for the work done after the inherited repository. It records what RC-Gate is, what was repaired, what the experiments actually found, how the offline Research Studio works, and how to share that work without treating about two thousand GitHub Desktop entries as two thousand source edits.

Three kinds of statement are kept apart:

- **Verified in this audit.** A fact read from the current working tree, Git, source, or a result file while this document was written.
- **Recorded finding.** A result stated in a repository report. Where this audit also recomputed it, that is said explicitly.
- **Recommendation.** A proposed next step. It has not been executed.

This document does not replace [`RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md). That report remains the scientific record. This file is the map of how the repository got there, plus the Git and application handoff.

When this handoff was written on 10 October 2026, no branch had been created and nothing had been committed, pushed, reset, cleaned, or deleted. No model was trained. No benchmark was refit. Existing research reports were not edited. The tree checked at commit `6d3ef70` is in the status section below. This documentation commit does not change the hashed fit sources and does not move `main`.

## Repository status on 20 October 2026

Checked with `git status`, `git rev-parse HEAD`, `git branch -vv`, `git ls-files -o --exclude-standard`, and `git check-ignore -v`. This section does not replace the 10 October inventory later in the document.

- On 20 October 2026, before this documentation commit, branch `review/rcgate-handoff-v1` and `origin/review/rcgate-handoff-v1` were both at `6d3ef709367d55a27a413477c624fc9f96a215ce` (`6d3ef70`), message `Record the RC-Gate integrity repairs, Stage 8 findings, and offline research studio.`
- `main` was, and remains, `47090018414f657bca8e5a43e97663feba2e5a7d`. A clone of `main` still has the milestone tree only.
- At the start of this check, no tracked file was modified. `git ls-files -o --exclude-standard` listed 2,628 untracked files, all under the Stage 4–8 result directories named in [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md). `git status --porcelain` collapses them to 732 lines.
- The committed `.gitignore` rule `node_modules/` ignores both the repository-root `node_modules/` directory and `frontend/node_modules/`. Both directories are on disk. Neither is tracked. `node_modules/.vitest/.vitest-secret-token` matches that rule and is not staged.
- The twelve source hashes in Stage 8 `provenance.json` match the files in `6d3ef70`. The 480 fits were not rerun. Exact reproduction from Git alone is not established. The limits are in the reproduction note.

## 2. Executive summary

RC-Gate is a small sentence-level hallucination detector. For one sentence of a stored answer it computes two families of clues: how the other models’ answers compare with that sentence, and how the supplied task context supports or conflicts with it. A gate sees only the sentence’s claim type and the identity of the model that wrote it. It does not see the clue values. Two linear experts score the two families. The gate’s weights scale those scores, and a final step turns them into a probability that the sentence is hallucinated. On the RAGTruth roster that gate has 233 trainable parameters. The weights can be printed. Printing them is not a validated explanation that one expert is the reliable one.

The inherited repository already contained a milestone pipeline (M0–M7), a synthetic mechanism check, and a first real-data run on an 800-sentence RAGTruth slice. That first run did not show the gated model (A7) beating a flat gradient-boosting control that sees the same clues and the same metadata (A4). Later work kept those historical files and repaired the pipeline beside them.

The repairs were real. Sentence boundaries had been merged by a non-strict alignment, and a pronoun rewriter had inserted instruction words such as “Briefly” and “Summarize” into claim text, which changed some claim types. A confidence interval had been mis-rendered, a bootstrap fraction had been stored under a name that reads like a p-value, and a split flag named `stratify=True` did not stratify. Those defects were corrected in new result directories. The scientific ordering did not flip. On the principal repeated-fit analysis (Stage 8), mean test AUROC is **0.6280** for flat logistic regression (A0), **0.6839** for A4, and **0.5717** for A7. The mean paired difference A7 minus A4 is **−0.1122**. A7’s 60 AUROC values have sample standard deviation **0.1247**. This audit recomputed those four-decimal figures from [`results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv`](../results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv). They match the Stage 8 report and Table 7 of the final report. They describe 20 partitions of one 134-question pool, each fit three times. They are not 60 datasets, and the standard deviation is not a confidence interval.

A read-only look at the official RAGTruth files, recorded in the final report, found that a generator-by-claim-type reliability surface is not adequately identified under a pre-stated support rule. This audit rechecked the file sizes, row counts, task counts, and SHA-256 hashes of the local JSONL files and the seed-0 signal table. It did not re-derive the sentence-level generator-by-type grid. No full-scale QA experiment was run.

The current application is a local offline Research Studio: a Python API on `127.0.0.1:8765` and a React/Vite page. It browses the RAGTruth files on disk and can score a stored sentence from one saved checkpoint. It does not call a model provider. A clean clone of `main` cannot run that studio, because `main` does not contain the studio. A clone of `review/rcgate-handoff-v1` at `6d3ef70` contains the studio source and still cannot browse or score until the local files in Section 15 are present. The raw JSONL files, the corrected signal table, the checkpoint, and the local NLI and embedding weights are absent from Git.

GitHub Desktop’s large change count is the expanded untracked tree. Measured on 10 October 2026:

| Quantity | Count |
| --- | ---: |
| Current branch | `main`, even with `origin/main` |
| HEAD | `47090018414f657bca8e5a43e97663feba2e5a7d` |
| Staged files | 0 |
| Modified tracked files | 17 |
| Deleted or renamed files | 0 |
| Untracked files (`git status --short -uall`) | 2,727 |
| Of which under `results/` | 2,646 |
| Ignored files | 48,345 |
| Tracked files | 348 |

Collapsed `git status --short` prints about 50 lines because Git hides the contents of untracked directories. GitHub Desktop expands them. The bulk is one config, one metrics file, one checkpoint, and often one predictions table per fitted cell, not 2,000 hand-edited source files.

That table is the 10 October working tree, before commit `6d3ef70`. The 20 October status section records the branch that now contains the source.

**Immediate recommendation.** Freeze the current interface. Do not start another fit on this 800-sentence slice unless the question is narrower than “can we make A7’s AUROC higher?” Publication readiness has not been established.

## 3. What RC-Gate is and what it actually does

The unit of prediction is one sentence of one generated answer. The label is 1 when that sentence’s character span overlaps a human annotation in RAGTruth, and 0 otherwise. The four annotation types that count are Evident Conflict, Evident Baseless Info, Subtle Conflict, and Subtle Baseless Info. That rule is [ADR-004](adr/004-ragtruth-span-overlap-labelling.md). A sentence label is coarser than the official span annotation. The final report records that 904 of 2,927 QA spans (30.9%) cross more than one sentence under this project’s splitter. This handoff did not re-count those spans.

Six numbers, each scaled to the range 0–1, are split into two families. The definitions below are the ones in the final report, Section 3, which cites `rcgate/models/gate.py`, `rcgate/models/experts.py`, `rcgate/models/meta.py`, and `rcgate/models/rcgate.py`.

| Family | Signal | Plain meaning |
| --- | --- | --- |
| Cross-model | `agree` | Fraction of the other generators whose text entails the sentence |
| Cross-model | `contra` | Largest contradiction probability among the other generators |
| Cross-model | `sem_dist` | One minus the average similarity between this sentence and each other generator’s closest sentence |
| Evidence | `support` | Highest entailment of the sentence against retrieved sentences of the supplied context |
| Evidence | `src_quality` | A constant that records where the evidence came from, not whether the sentence is true |
| Evidence | `conflict` | Highest contradiction against those retrieved sentences |

On the corrected 800-row seed-0 table, this audit read `src_quality` as 0.9 on all 800 rows and `arithmetic_verdict` as `unverifiable` on all 800 rows. The arithmetic checker looks for an explicit expression. It does not guess. It is not an active feature of the evaluated slice.

Claim type is assigned by rules, not by a learned classifier: numeric, entity, extractive, or abstractive ([ADR-003](adr/003-four-claim-types.md)). The proposal listed three categories. The code uses four.

The gate’s input is two small learned lookup tables: one row per claim type and one row per generator, plus a reserved row for an unknown generator. With six RAGTruth models that is 7 generator rows. Those vectors are concatenated and passed through a small two-layer network. A softmax produces two weights that sum to 1. Temperature is fixed at 1. The gate never receives the six signal values ([ADR-001](adr/001-metadata-only-gate.md)). A unit test checks that changing the signals does not change the weights.

Each expert is a linear map from its three signals to one logit, a score that is not yet a probability. Default fusion multiplies each weight by its expert’s logit, then applies one more linear map and a sigmoid ([ADR-002](adr/002-fuse-logits-not-probabilities.md)). The Stage 8 checkpoint at split seed 0 and model seed 0 records `fusion_input: logit`, `gate_input_dim: 8`, and `n_parameters: 233`. The user guide’s figure of 229 parameters matches the synthetic roster of five generators plus the unknown row. It is the wrong count for RAGTruth.

The variant ladder in `rcgate/variants.py` is:

| Id | What is fit | Role |
| --- | --- | --- |
| A0 | Logistic regression on the six signals | Flat fusion, no metadata |
| A1 | Logistic regression on the three cross-model signals | Family ablation. Not a reimplementation of BEACON |
| A2 | Logistic regression on the three evidence signals | Family ablation. Not a reimplementation of Medico |
| A3 | One validation-chosen scalar blend of the two expert logits | One weight, shared by every claim |
| A4 | Histogram gradient boosting on the six signals plus one-hot claim type and generator id | The critical flat control |
| A5 | Gate on claim type only | Ablation of A7 |
| A6 | Gate on generator id only | Ablation of A7 |
| A7 | Gate on claim type and generator id | The proposed model |
| A8 | Majority vote over judge columns | Never fit. Those columns are absent |

A4 can split on a metadata indicator and then on a signal. A7 cannot let the weights depend on the signal values. A7 does not receive new measurements. It constrains how metadata and signals may interact.

The weights returned with a prediction are inspectable values. They are not, by themselves, evidence that the preferred expert is the reliable one.

## 4. Original inherited state and initial issues

**Verified.** `main` points at `47090018414f657bca8e5a43e97663feba2e5a7d`, message `Merge pull request #1 from pd241008/dev`. The branch is up to date with `origin/main`. Remote branches are `origin/main` and `origin/dev`. The remote is `https://github.com/pd241008/RCGate.git`. The commit log on this HEAD is the milestone sequence M0 through M7: scaffold, synthetic table, baselines A0–A4, the gate and ablations, evaluation, RAGTruth signal extraction, the first real-data run, and the Streamlit demo, followed by README, ADR, and postmortem commits.

**Verified.** 348 files are tracked. 275 of them are under `results/`, including the original `results/summary/ragtruth/` checkpoints for A0–A7 and skip records for A8. A8’s tracked `metrics.json` says `skipped: no judge outputs in the signal table; A8 skipped by design` and stores null test metrics. That file also embeds an old absolute path under `/root/workspace/...`. It is provenance residue from the inherited run, not a credential introduced by the later work.

**Recorded, and still visible in tracked files.** The original three-seed RAGTruth summary at [`results/summary/ragtruth.md`](../results/summary/ragtruth.md) reports mean AUROC about 0.681 (A0), 0.705 (A1), 0.740 (A4), and 0.631 (A7). Its “AUROC (95% CI)” column prints the mean because the interval lookup misses the renamed columns. Its paired comparison stores `p_gt_0 = 0.415`, which is an average of bootstrap fractions, not a p-value. [`DECISIONS.md`](../DECISIONS.md) and the M6 postmortem still contain those historical sentences. Each now has a status note dated 10 October 2026 pointing at the final report. The original wording underneath the note was left in place.

**Limitation.** There is no Git-tracked document named as a Stage 0, Stage 1, Stage 2, or Stage 3 audit. Those stages are reconstructed below from the code, the tests, the Stage 4 verdict, `statistical_issues.md`, and the final report. A local Cursor canvas named `ragtruth-integrity.canvas.tsx` exists outside the Git tree. This handoff did not use it as a source of numbers.

The inherited reproducibility problems that later stages actually addressed were:

- Sentence alignment could concatenate neighbouring sentences and attach a label to the wrong text.
- Pronoun de-aliasing could insert prompt words into claim text and change claim type.
- `grouped_split(..., stratify=True)` sorted groups and then fully permuted them, so the flag did not stratify.
- Uncertainty reporting mixed point estimates, claim-level bootstrap intervals, averaged interval endpoints, and a bootstrap fraction.
- Split seed and model initialisation seed were the same integer, so partition and initialisation were confounded.
- One validation threshold was rounded to six decimal places on the way into JSON, which moved one F1 and not AUROC.
- The fitted slice is a first-sentence prefix of mixed QA and Summary, not the official RAGTruth test split.
- `src_quality` does not vary on that slice, and the arithmetic checker does not fire.
- A8 could not be run.
- Headline README numbers needed to be retired in favour of the later protocol.

## 5. Stage 0–16 chronology

Filesystem modification times order the result reports on 9 October 2026 (Stage 4 verdict 00:57, Stage 5 report 01:27, Stage 6 report 01:51, Stage 7 report 10:25, Stage 8 report 11:14) and the final report at 08:55 on 10 October 2026. Many application files share a later timestamp of 22:13 on 10 October 2026, so that clock does not by itself order the interface stages. Stage 8’s own `provenance.json` records a dirty tree that already contained the integrity, statistics, split, and factorial modules, and records that checking out HEAD alone does not reproduce the run. The studio, frontend, fixtures, and the two new docs are not in that provenance snapshot’s porcelain list, so they were added after that snapshot was written.

Stages 9 and 10 have no standalone Markdown file in Git. The experiment index names two local canvases outside the repository, `rcgate-novelty-audit.canvas.tsx` and `ragtruth-feasibility.canvas.tsx`. This audit confirmed that both files exist on this machine under the Cursor project canvases directory. They are not Git-tracked. The numbers below for those stages are the final report’s numbers. This audit did not re-read the canvases as an independent literature or feasibility review. No conversation transcripts were recovered. Phrases such as “unstaged” in the table describe the tree before commit `6d3ef70`. Those source files are in that commit.

| Stage | Objective | Main findings | Exact changes | Evidence files | Outcome and remaining work |
| --- | --- | --- | --- | --- | --- |
| 0 | Inspect the inherited repository | Milestone code, tests, original RAGTruth and synthetic summaries, and the statistical and alignment defects above were already present. A8 was skipped. | No separate Stage 0 patch is identifiable. The inherited state is HEAD `4709001`. | Tracked tree; [`results/summary/ragtruth.md`](../results/summary/ragtruth.md); [`DECISIONS.md`](../DECISIONS.md) | Findings fed Stages 3–5. No standalone audit file. |
| 1 | Explain the architecture in plain language | Metadata-only gate, two linear experts, logit fusion, variants A0–A8. 233 parameters on the RAGTruth roster. | Explanation, not a new model. Later written into the final report, Section 3, and the studio’s How-it-works page. | [`docs/RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md); [`frontend/src/views/HowItWorks.tsx`](../frontend/src/views/HowItWorks.tsx) | The explanation matches the code. It does not establish H1–H3. |
| 2 | Trace the file-level pipeline | Path runs from JSONL to sentence spans, de-aliasing, signal extraction, group split, fit, checkpoint, evaluation, and summary rendering. | No separate trace document in Git. The path is the package under `rcgate/data/`, `rcgate/signals/`, `rcgate/pipeline.py`, and `rcgate/evaluate.py`. | Those modules; [`results/README.md`](../results/README.md) | The trace is reconstructable from code. Intermediate caches under `.cache/` are local and ignored. |
| 3 | Verify two RAGTruth defects and the statistical reporting | Alignment mismatches and prompt-word antecedents were real. `stratify=True` did not stratify. Markdown “95% CI” printed the mean. `p_gt_0` is not a p-value. | Diagnosis is preserved in the Stage 4 notes. The statistical defects were deliberately left in the Stage 4 estimator. | [`results/summary/ragtruth_corrected_integrity_v1/VERDICT.md`](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md); [`statistical_issues.md`](../results/summary/ragtruth_corrected_integrity_v1/statistical_issues.md) | Defects confirmed by the later repairs and tests. Not a separate Git report. |
| 4 | Correct integrity without overwriting history | On seed 0, 11 first sentences had been concatenated (12 on seeds 1 and 2). Labels stayed at 57 positives. 90 of 800 claims had been rewritten with “Briefly” or “Summarize”. Entity claims fell from 211 to 183. One positive row changed type. Mean A7 AUROC moved from 0.631 to 0.638 under the old estimator. A4 stayed ahead (0.740, then 0.706). | New namespace `ragtruth_corrected_integrity_v1`. Historical `results/summary/ragtruth/` left in place. Freeze manifest added. Sentence splitter and de-aliaser changed. Regression tests added. | [`VERDICT.md`](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md); [`comparison.md`](../results/summary/ragtruth_corrected_integrity_v1/comparison.md); [`rcgate/claims/dealias.py`](../rcgate/claims/dealias.py); [`rcgate/data/ragtruth.py`](../rcgate/data/ragtruth.py); [`tests/test_dealias.py`](../tests/test_dealias.py); [`tests/test_ragtruth.py`](../tests/test_ragtruth.py) | Text and types repaired. A7 still did not beat A4. The estimator used for that comparison was still the defective one. |
| 5 | Repair uncertainty reporting | Point estimate, within-seed grouped bootstrap interval, across-seed sample SD, and paired difference are separate. Interval endpoints are not averaged. The bootstrap fraction is not labelled as a p-value. | New `rcgate/stats_protocol.py` and grouped bootstrap functions in `rcgate/metrics.py`. Stage 4 checkpoints reloaded. No refit. | [`rcgate/stats_protocol.py`](../rcgate/stats_protocol.py); [`results/summary/ragtruth_corrected_stats_v1/report.md`](../results/summary/ragtruth_corrected_stats_v1/report.md); [`tests/test_stats_protocol.py`](../tests/test_stats_protocol.py) | Reporting repaired. Three overlapping slices remained. Not the principal estimate. |
| 6 | Replace the pseudo-stratified split | Legacy flag does not stratify. New splitter stratifies on each question’s positive-sentence count. Mean absolute deviation of positive rates fell from 0.0171 to 0.0112, short of the pre-specified 0.01 materiality bar. Test-question Jaccard with the legacy test set was 0.078, 0.196, and 0.100. Mean AUROC: A0 0.6903, A4 0.6890, A7 0.5025. | `group_stratified_split` in `rcgate/data/splits.py`. New module `rcgate/split_sensitivity.py`. | [`results/summary/ragtruth_split_corrected_v1/report.md`](../results/summary/ragtruth_split_corrected_v1/report.md); [`tests/test_group_stratified_split.py`](../tests/test_group_stratified_split.py) | Split method replaced. A7 still behind. Seeds 1 and 2 still use companion tables, so this is not the 20-seed study. |
| 7 | Repeat the group split twenty times | One corrected seed-0 table, seeds 0–19, model seed tied to the split seed. Mean AUROC: A0 0.6280 (SD 0.0608), A4 0.6838 (SD 0.0668), A7 0.5982 (SD 0.1427). Mean paired A7−A4 is −0.0857. A7 is higher on 7 of 20 seeds. | `rcgate/multi_seed.py` and `configs/ragtruth_multi_seed_v1.yaml`. | [`results/summary/ragtruth_multi_seed_v1/report.md`](../results/summary/ragtruth_multi_seed_v1/report.md); [`tests/test_multi_seed.py`](../tests/test_multi_seed.py) | Wide spread documented. Split and initialisation still coupled. Superseded by Stage 8 for the headline. |
| 8 | Separate split seed from model seed | 20 split seeds × 3 model seeds on one table. 480 fits. A0 and A4 did not move with the model seed. A7 mean AUROC 0.5717, sample SD 0.1247, range 0.3072–0.7983. Mean paired A7−A0 −0.0563. Mean paired A7−A4 −0.1122. Checkpoints reloaded exactly on 480 of 480 cells. One Stage 7 threshold rounded to six decimals flipped one F1 and not AUROC. | `rcgate/factorial_seed.py`. `RunResult.to_dict` now stores the exact threshold. Stage 7 files were not rewritten. | [`results/summary/ragtruth_factorial_seed_v1/report.md`](../results/summary/ragtruth_factorial_seed_v1/report.md); [`seed_metrics.csv`](../results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv); [`provenance.json`](../results/summary/ragtruth_factorial_seed_v1/provenance.json); [`tests/test_factorial_seed.py`](../tests/test_factorial_seed.py) | Principal real-data experiment. A7 does not beat A4. Still one 134-question pool. |
| 9 | Literature and novelty audit | Neighbouring methods already combine consistency, retrieval, or conditional routing in other forms. The residual claim is the metadata-only constraint versus a flat model with the same inputs. Draft gap numbers and author lists were not verified. | No fitted-model directory. Findings written into final report Sections 2 and 11. | [`docs/RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md) Sections 2 and 11; local canvas outside Git | Not a systematic review. Unresolved bibliographic items remain in Section 11. |
| 10 | Full QA feasibility, read-only | Official files match the pinned hashes. Six responses per source. Support rule: at least 30 training positives and 15 official-test positives in a generator-by-type cell. The report says 11 of 24 QA cells meet it, all Mistral or Llama, and every GPT cell and every extractive cell fails. | No feature build and no fit. | Final report Section 4.4. This audit rechecked JSONL row counts and hashes only. | The proposed surface is not adequately identified. No full-scale experiment was started. |
| 11 | Write the scientific record | Final report made authoritative. README no longer leads with the retired three-seed headline. | New report. README rewritten. Original proposal, draft, and user guide not overwritten. | [`docs/RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md); [`README.md`](../README.md) | Publication readiness explicitly not established. |
| 12 | Documentation consistency | Experiment index maps current versus historical files. Status notes added to `DECISIONS.md`, ADR-001, and the M6 postmortem. | Those notes are unstaged modifications. Original sentences kept. | [`docs/RC-Gate_Experiment_Index.md`](RC-Gate_Experiment_Index.md) | Historical documents remain easy to misread if the status note is skipped. |
| 13 | Streamlit visual redesign | Single-answer scorer presentation expanded. Prediction, weights, and routing are shown more explicitly. | Large unstaged edit to `rcgate/demo/app.py` and `tests/test_demo.py`. Theme file `.streamlit/config.toml` added (`gatherUsageStats = false`). | [`rcgate/demo/app.py`](../rcgate/demo/app.py); [`.streamlit/config.toml`](../.streamlit/config.toml) | Still a separate single-answer tool. It does not browse the corpus. |
| 14 | Demo semantics and provenance | Generator must be selected, including an unknown-generator option. Missing cross-model answers produce a warning instead of a silent fallback to a named model. Checkpoint provenance is taken from the loaded artifact. | Tests in `tests/test_demo.py` cover identity, unknown generator, missing comparisons, and checkpoint lines. | [`tests/test_demo.py`](../tests/test_demo.py) | The page still does not train. It is not the Stage 8 mean. |
| 15 | Recorded React walkthrough | Three stored scenarios with real RAGTruth answers, supplied context, cross-checks, and a checkpoint score. Playback stages: task, context, answers, cross-check, result. | `demo_fixtures/scenarios.json` (three scenarios). `rcgate/demo/fixtures.py`. React playback and fusion modules. | [`demo_fixtures/scenarios.json`](../demo_fixtures/scenarios.json); [`frontend/src/playback.ts`](../frontend/src/playback.ts); [`tests/test_demo_fixtures.py`](../tests/test_demo_fixtures.py) | The three-scenario file remains an input to frontend unit tests. The live library no longer depends on only those three records. |
| 16 | Research Studio | Full local browser: search, filters, sort, pagination, six stored answers, supplied context separated from two curated external references, score provenance, typeset formulas, glossary, research page. | `rcgate/studio/`, `frontend/`, `scripts/dev_studio.sh`, `tests/test_studio.py`, `demo_fixtures/independent_references.json`. | Paths in Section 13 of this document | Offline studio, not a live multi-model product. Requires local data and a checkpoint. No screenshots are stored in the repository. |

## 6. Architecture and data flow

### The original task

RAGTruth gives a source and six stored responses, one from each roster model:

- `gpt-4-0613`
- `gpt-3.5-turbo-0613`
- `mistral-7B-instruct`
- `llama-2-7b-chat`
- `llama-2-13b-chat`
- `llama-2-70b-chat`

This audit counted 2,965 sources and 17,790 responses in the local JSONL files, with 2,965 responses from each of those six models. Tasks are QA (989 sources), Summary (943), and Data-to-text (1,033). The official response split field is only `train` (15,090) or `test` (2,700). There is no official validation partition. The fitted experiments deliberately did not use that official split, because a cross-model signal uses the other answers to the same source, and the project’s split keeps a whole `source_id` on one side of the cut. Results are therefore not official RAGTruth leaderboard numbers.

The material stored with the source is the supplied task context. For QA it is the passages the original models were given. The evidence expert reads that context. It is not an independently retrieved web page.

### From text to a probability

1. Split the answer into sentences with offsets, using `re.split(r'(?<=[.!?])["\')\]]*\s+')`.
2. Label a sentence positive when its offsets overlap an annotation span.
3. Optionally rewrite a pronoun from an antecedent in a prior sentence or in the question. Instruction verbs such as “Briefly” and “Summarize” are no longer accepted as antecedents.
4. Assign a claim type with rules.
5. Compute the three cross-model signals against the other five answers, and the three evidence signals against the supplied context. NLI uses `cross-encoder/nli-deberta-v3-small`. Embeddings use `sentence-transformers/all-MiniLM-L6-v2`. Both are local. The evaluated runs record no paid API calls.
6. The metadata gate, seeing only claim type and generator id, produces two weights.
7. Two linear experts turn their own three signals into two logits.
8. The weights scale the logits. A linear head and a sigmoid produce \(P(\text{hallucinated})\).

The studio returns the probability, both weights, both logits, the feature source, and the checkpoint identity. A reader who knows ordinary programming can treat the gate as a small formula with two jobs: score each clue family, then decide from the metadata which score to emphasise. The decision is visible. It is not a tested causal explanation.

### Supplied context versus external references

Two curated pages are stored in [`demo_fixtures/independent_references.json`](../demo_fixtures/independent_references.json):

| Id | Source | Page | `used_in_rcgate_score` |
| --- | --- | --- | --- |
| `sep-game-theory-12180` | source `12180` | Stanford Encyclopedia of Philosophy, “Game Theory” | `false` |
| `nara-dred-scott-12172` | source `12172` | National Archives, Dred Scott v. Sandford (1857) | `false` |

The loader in `rcgate/studio/references.py` rejects any reference that does not set `used_in_rcgate_score` to false. The studio does not fetch the URLs. The pages are reader-verification aids. They are not inputs to the score. RAGTruth passages are the supplied task context and are used when evidence signals are calculated. Most records have no curated external reference. The interface says so.

### Precomputed signals versus local calculation

The corrected seed-0 table has 800 rows, all with claim ids ending in `#0`. For those claim ids the studio scores the stored signal row through the checkpoint. It does not recompute the features.

Any other sentence needs local extraction: the same NLI and embedding models, then the same checkpoint. Extracted signals are cached under `.cache/studio/`. If the checkpoint is missing, or the local weights are missing, the API returns an unavailable result and does not invent features. Stored answers can still be read when the raw JSONL files are present and the API is up.

### Research Studio versus the Streamlit scorer

| | Research Studio | Streamlit scorer |
| --- | --- | --- |
| Entry | `python -m rcgate.studio` and `frontend` | `streamlit run rcgate/demo/app.py` |
| What it shows | The local RAGTruth library, one source at a time | One answer typed or loaded into a single page |
| Scoring | Checkpoint, precomputed row or local extraction | Checkpoint on the text in the form |
| Generator | The stored roster identity of the selected response | An explicit selector, including unknown |
| Corpus browser | Yes | No |
| Live provider calls | No | No |
| Training | No | No |

Neither application generates new model answers.

## 7. Data-integrity repairs

**Verified from the seed-0 parquet during this audit.** 800 rows, 134 distinct `question_id` values, 57 positive labels, 402 QA rows, 398 Summary rows, six generators, every `claim_id` ending in `#0`, `src_quality` equal to 0.9 on every row, `arithmetic_verdict` equal to `unverifiable` on every row. SHA-256 of that file is `082e524ccc3c062cfcec423b00e970f5fa846eefa2646c3d0c4139cd73954245`, matching the final report. Companion tables `s1` and `s2` are on disk. This audit hashed only `s0`.

**Recorded in the Stage 4 verdict, not re-measured sentence by sentence in this audit.**

- Alignment: 11 seed-0 first sentences (12 on seeds 1 and 2) had been concatenated with the next sentence. Row count, claim ids, and all 57 labels were unchanged. The largest mean shift among the six signals was 0.015, against within-slice standard deviations of about 0.24 to 0.45.
- Antecedents: 90 of 800 seed-0 claims had been rewritten with “Briefly” or “Summarize”. After the fix, entity claims fall from 211 to 183. One positive row changes type. Labels stay at 57.
- Under the original estimator, mean A7 AUROC moved from 0.631 to 0.638. A4 moved from 0.740 to 0.706 and remained ahead.

Historical claim-type counts and any AUROC that depended on the old entity strings are historical. The original result directory was not overwritten. [`results/summary/ragtruth_historical_freeze/MANIFEST.json`](../results/summary/ragtruth_historical_freeze/MANIFEST.json) says its purpose is an immutable record of the RAGTruth result before the integrity corrections, and it points at the already tracked `results/summary/ragtruth/` directory.

The code changes that implement the repair are in commit `6d3ef70`: `rcgate/claims/dealias.py`, `rcgate/data/ragtruth.py`, `rcgate/data/build.py`, and `rcgate/data/__init__.py`, plus `tests/test_dealias.py` and the extensions of `tests/test_ragtruth.py`. On 10 October those edits were still unstaged.

## 8. Statistical and split methodology repairs

A claim-level bootstrap redraws individual sentences. Sentences that share a question are not independent: the split keeps the question together, and each source contributes one sentence from each generator. A question-grouped bootstrap redraws whole `question_id` values and recomputes AUROC on the drawn questions. That interval describes uncertainty inside one fitted split. It is still not a confidence interval for a new corpus, and it is not the spread across seeds.

Across-seed dispersion is the ordinary sample standard deviation of the seed-level scores. It describes spread. It is not a confidence interval.

The fraction of bootstrap draws in which one model’s AUROC exceeds another’s describes those draws. Stage 5 and later reports say it is not a p-value. The original name `p_gt_0` and the value 0.415 belong only to the original protocol.

Averaging the lower endpoints of several intervals, and averaging the upper endpoints, does not produce one interval for the mean. Stage 4’s `statistical_issues.md` records that the original markdown renderer also looked up the wrong column names, so the “95% CI” column printed the point estimate. Stage 5 stopped using that procedure for inference. It left the Stage 4 numbers reproducible under the old estimator on purpose.

The legacy splitter sorted groups by positive rate and then applied a permutation, which removed the sort. Question ids were still disjoint across train, validation, and test. They were not stratified. `group_stratified_split` assigns whole questions inside each positive-count stratum, with fractions about 60/20/20, and a separate random stream per stratum. On the seed-0 table the final report records 33 training positives, 9 validation positives, and 15 test positives on every Stage 8 seed. This audit confirmed from `seed_metrics.csv` that every Stage 8 test cell has 15 positives and 28 questions.

Stage 6’s balance improvement missed its own 0.01 bar. The test questions nevertheless changed. The module’s docstring says nothing in it retunes a model after seeing A7.

## 9. Results of Stages 4–8

Protocols are different experiments. A cell from one row is not pooled with a cell from another. The labels below match Table 6 of the final report.

### Stage 4 — corrected text, legacy split, original estimator

Three overlapping corrected tables, model seed equal to split seed. Three-decimal means in the integrity report: A0 0.667, A4 0.706, A7 0.638. Stage 5 recomputed the same checkpoints at four decimals: A0 0.6669, A4 0.7062, A7 0.6377. Mean paired A7−A4 is −0.0684. All three paired intervals for A7 versus A0 and versus A4 cover 0. These intervals are the later grouped ones, computed without refitting. The Stage 4 run itself still used the old estimator; that was intentional.

### Stage 5 — same checkpoints, new uncertainty

No new fit. Question-grouped percentile bootstrap, 1,000 requested resamples, per seed. Endpoints are not averaged. No p-value is reported. The point estimates are the Stage 4 checkpoints.

### Stage 6 — group-stratified split, three tables

Mean AUROC: A0 0.6903 (seed SD 0.0253), A4 0.6890 (seed SD 0.0618), A7 0.5025 (seed SD 0.1588). Mean paired A7−A0 is −0.1878. Mean paired A7−A4 is −0.1865. No paired interval lies entirely above 0. This is a different test-question assignment from Stage 5. It is not Stage 7 and not Stage 8.

### Stage 7 — twenty splits, seeds tied

One table. Mean AUROC: A0 0.6280 (SD of 20 seeds 0.0608), A4 0.6838 (SD 0.0668), A7 0.5982 (SD 0.1427). Mean paired A7−A0 is −0.0298 (A7 higher on 10 of 20 seeds). Mean paired A7−A4 is −0.0857 (A7 higher on 7 of 20 seeds). A7’s Stage 7 mean is higher than Stage 8’s because Stage 7 keeps only the initialisation whose seed equals the split seed.

### Stage 8 — principal experiment

**Design.** Fit table `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` for every cell. Split seeds 0 through 19 crossed with model seeds 0, 1, and 2. Variants A0–A7. A8 skipped. 480 fits. No Stage 7 checkpoint was reused as a Stage 8 model. Changing the model seed does not change the split. Changing the split seed does not change A7’s initial weights when the model seed is fixed, because the splitter does not draw from the torch generator that the model seed resets.

**Verified by recomputing `seed_metrics.csv` in this audit.** 480 rows, 60 per variant. Every test cell has 15 positives and 28 questions. `scores_equal_in_memory` is true on all 480 rows. Within a split, A0 and A4 have sample standard deviation 0 across the three model seeds. Four-decimal means:

| Variant | Mean test AUROC | Sample SD of the 60 cells | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| A0 | 0.6280 | 0.0597 | 0.5046 | 0.7320 |
| A4 | 0.6839 | 0.0656 | 0.5669 | 0.8017 |
| A7 | 0.5717 | 0.1247 | 0.3072 | 0.7983 |

Paired differences, same test sentences:

| Comparison | Mean over 60 cells | Sample SD | Cells with A7 higher | Split-level means with A7 higher |
| --- | ---: | ---: | ---: | ---: |
| A7 − A0 | −0.0563 | 0.1377 | 24 of 60 | 6 of 20 |
| A7 − A4 | −0.1122 | 0.1526 | 16 of 60 | 4 of 20 |

The final report additionally records, from the Stage 8 report rather than from a recomputation in this handoff, that 3 of 60 paired intervals versus A0 lie entirely above 0 and 9 entirely below, and that 2 of 60 versus A4 lie entirely above 0 and 14 entirely below. Most intervals cover 0. That is expected with 15 positive test sentences. The sample SD is the spread of repeated fits on one pool. It is not a confidence interval.

The threshold bug is documented in the Stage 8 report. Stage 7 stored `round(threshold, 6)`. For A4 at split seed 6 the exact validation cut was about \(6.45 \times 10^{-6}\). Rounding it to \(6 \times 10^{-6}\) flipped one negative test sentence, changed F1 from 0.2857 to 0.2824, and left AUROC at 0.7168. Stage 8 stores the exact threshold. `rcgate/pipeline.py` no longer rounds it in `to_dict`. The ordering does not depend on that one F1 change.

### Synthetic mechanism check

The synthetic generator plants a reliability pattern. Evidence was made useful on numeric claims and weak elsewhere. A numeric cross-model signal was made anti-informative. The recorded operating point in the final report, taken from `DECISIONS.md`, is A0 numeric AUROC 0.478 and A7 numeric AUROC 0.855 (difference +0.377), with mean evidence weight 0.809 on numeric claims. Pooled synthetic means in `results/summary/synthetic.md` are A0 0.756, A4 0.929, and A7 0.874. Leave-one-generator-out on the planted inverted generator gives A0 0.171 and A7 0.748. Those figures show that training can recover a pattern the simulator was built to contain. They are not independent evidence that real models follow that pattern. A4 still ranks higher than A7 on the synthetic pooled mean. The “95% CI” column in that file is the historical renderer.

## 10. Literature, novelty, and H1/H2/H3

The Stage 9 account in the final report is a targeted audit, not a systematic review. It compares the implemented system with SelfCheckGPT, SAC³, FActScore, MiniCheck, Medico, Rowen, Evidence Graph Consistency, BEACON, FLaG, CAR-RAG, Lynx/HaluBench, Itkin, AuthenHallu, the Huang survey, semantic entropy, and RAGTruth itself. This repository did not score SelfCheckGPT, MiniCheck, Lynx, FLaG, or the RAGTruth paper’s detectors.

**Recorded literature finding.** Conditional routing and the combination of consistency with retrieval already exist in neighbouring work, in different forms. FLaG routes using hidden states. CAR-RAG maps a query category to retrieval modalities with fixed weights. Rowen uses a consistency score to decide when to retrieve. Evidence Graph Consistency reports that the direction of a consistency feature can depend on model family and adapts with a sign flip. A learned generator embedding as the gate’s only generator input is a small residual relative to that analysis.

**Recorded interpretation.** It is not accurate to say that conditioning fusion on metadata, or combining consistency with retrieval, is wholly unexplored. The residual, untested design hypothesis is that forcing the weights to ignore the signal values will generalise better than letting a flat model see the same signals and the same metadata. On the evaluated slice, that hypothesis is not supported. That does not show it is false for every dataset or every gate.

Several claims in the initial paper draft were not verified: author lists for the papers it numbered [1]–[8], a FActScore title the paper does not use, Medico’s F1 of 0.82 and a 3.8-second latency, Rowen’s “greater than 24%” transfer drop, EGC’s correlations \(r = +0.42\) and \(r = -0.31\), BEACON’s “AUROC ≈ 0.87” against an abstract figure of 0.8123, and Gap 2 numbers that were not found in a paper. Unresolved bibliographic items are listed in Section 11 of the final report. This handoff did not repeat the literature search.

| Hypothesis | Status | Evidence |
| --- | --- | --- |
| H1. Signal reliability depends on claim type and generator identity | Partially supported on planted synthetic data. Not established on the real slice or on the official QA support counts | The synthetic plant moves the numeric evidence weight. The real slice has one GPT-4 positive, five abstractive positives, constant `src_quality`, and an arithmetic checker that never fires |
| H2. The learned gate beats flat fusion and judge voting | Not shown against A4. Judge voting is untested | Stage 8 mean AUROC 0.6839 (A4) versus 0.5717 (A7). Mean paired difference −0.1122. A8 was never fit. DROP and FinanceBench were not run |
| H3. The weights are interpretable | Inspectable. Scientific interpretability is not validated | The forward pass returns the weights. It does not show that the preferred expert is the reliable one |

These outcomes do not disprove conditional gating in general. They bound this prototype: a metadata-only linear two-expert gate, on this feature set, on this slice, under this split.

## 11. Full RAGTruth feasibility findings

**Verified in this audit from the local files.**

| File | Bytes | Lines | SHA-256 |
| --- | ---: | ---: | --- |
| `data/raw/ragtruth/response.jsonl` | 21,458,735 | 17,790 | `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073` |
| `data/raw/ragtruth/source_info.jsonl` | 15,117,971 | 2,965 | `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b` |

Responses with any annotation span: 7,664. Task counts: QA 989, Summary 943, Data-to-text 1,033. Train responses 15,090. Test responses 2,700. These match Section 4.4 of the final report. The licence recorded there is the MIT licence of the RAGTruth repository.

**Recorded in the final report and not re-derived here.** QA sentence construction yields 46,592 sentences and 4,754 positives. The official QA test contributes 6,143 sentences and 447 positives. GPT-4 has 1 positive sentence in the official QA test and 52 positive QA sentences in the whole QA corpus. Table 5 of the final report is the official QA test positive counts by generator and rule-based claim type. The support rule requires at least 30 training positives and 15 official-test positives before a generator-by-type cell is called estimable. Under that rule the report says 11 of 24 cells are estimable, all of them Mistral or Llama, on numeric, abstractive, or some entity cells. Every GPT cell fails. Every extractive cell fails.

**Interpretation, as stated in the report.** The official QA data do not adequately identify the proposed generator-by-type reliability surface. A pooled AUROC can also rank generators by how often they hallucinate. The report gives a prevalence-only score of 0.632 on the official QA test sentences. That is prevalence, not evidence that a signal family is conditionally reliable inside a generator. Within-generator AUROC is the comparison that separates the two. With one GPT-4 test positive, that comparison is not available for GPT-4. No full-scale feature build or model fit was performed. Data-to-text has more GPT-4 hallucinations and is a different task. It was not evaluated, and it is not a silent substitute.

The 800-row checkpoints are also the wrong starting point for an official-test score. The final report says 21 of their sources are official test sources.

## 12. Final scientific conclusions

What the project has established:

- A working implementation of a metadata-only two-expert gate, with tests that enforce the constraint.
- A synthetic recovery of a planted reliability pattern, which A4 still outranks on the pooled mean.
- A negative, unstable evaluation of A7 against A4 on one corrected 800-sentence RAGTruth slice.
- An integrity and statistics record: alignment, antecedent leakage, a stratify flag that did not stratify, a mislabelled bootstrap fraction, split seed separated from model seed, and a six-decimal threshold that changed one F1.
- A feasibility bound: the official QA release does not identify the proposed generator-by-type surface under the stated support rule.

What it has not established:

- That A7 improves on a flat metadata-capable model.
- That the gate weights explain reliability.
- That conditional gating fails in general.
- A result on the official RAGTruth test split, or on DROP, FinanceBench, TruthfulQA, or HaluBench.
- A paper ready for submission.

The current residual research question is whether metadata-only conditional routing over cross-model and evidence experts generalises better than a flat model that uses the same signals and the same metadata. The current data do not support an improvement by A7, and the QA support audit does not adequately identify the full generator-by-type surface.

## 13. Frontend and offline API architecture

The page is a React 18 application in `frontend/`, built with Vite 6 and TypeScript. It is not a set of URL routes. `frontend/src/App.tsx` keeps one view in component state:

| View | Component | Needs the API? |
| --- | --- | --- |
| Library | `views/Library.tsx` | Yes |
| Record | `views/Record.tsx` | Yes |
| How RC-Gate works | `views/HowItWorks.tsx` | No. Static explanation |
| Research | `views/Research.tsx` | No. Figures are compiled into the page |
| Glossary and FAQ | `views/Glossary.tsx` | No |
| Stored demo data | `views/Dataset.tsx` | Yes. Health and inventory |

The record view still uses the playback reducer in `frontend/src/playback.ts` (task, provided context, recorded answers, cross-check, result). The sentences and scores come from the API, not from the three-scenario fixture. `frontend/src/library.ts` still imports `demo_fixtures/scenarios.json` for unit tests that check the recorded fixture.

Vite proxies `/api` to `http://127.0.0.1:8765` (`frontend/vite.config.ts`).

The API is `python -m rcgate.studio`. `rcgate/studio/__main__.py` sets `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, and `HF_DATASETS_OFFLINE` before model libraries load. The server binds to localhost. It does not call a provider. Endpoints implemented in `rcgate/studio/server.py`:

| Method and path | Behaviour |
| --- | --- |
| `GET /api/health` | File-hash match, checkpoint readiness, local-weight readiness, inventory. `live_provider_calls` is false |
| `GET /api/meta` | Stage 8 figure strings and the playback label |
| `GET /api/library` | Search (`q`, `task`, `topic`, `generator`, `score`, `sort`, `page`, `page_size`) |
| `GET /api/library/{source_id}` | One source: six responses, context, sentences, references |
| `POST /api/score` | Body: `source_id`, `response_id`, `sentence_index`. Returns a result immediately when the row is precomputed or cached. Otherwise returns HTTP 202 and a job id |
| `GET /api/jobs/{job_id}` | Poll a local extraction job |

`Catalog.load` in `rcgate/studio/catalog.py` reads:

- `data/raw/ragtruth/response.jsonl`
- `data/raw/ragtruth/source_info.jsonl`
- `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet`
- `demo_fixtures/independent_references.json` if present

It checks the JSONL bytes against the SHA-256 pins in `rcgate/data/ragtruth.py`. Precomputed rows are keyed by `claim_id` (`response_id#sentence_index`). A score uses the precomputed row only when the question id, generator, sentence text, and claim type also match.

The checkpoint path is fixed:

`results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib`

That is one cell of the Stage 8 grid (split seed 0, model seed 0). A probability from it is a demo inference. It is not the Stage 8 mean. The scorer attaches a note saying whether that source sits in the train, validation, or test partition of this one checkpoint.

Local extraction uses the existing signal pipeline and writes a cache under `.cache/studio/`. Missing weights produce an explicit unavailable message. Features are not filled in.

External references are displayed from the manifest. Both stored records have `used_in_rcgate_score: false`. The record view prints that flag.

No runtime call is made to an LLM provider, and the reference URLs are not fetched. Model-weight files are read from the local Hugging Face cache only when a sentence is not in the precomputed table and is not already cached.

## 14. Application usage and startup commands

These commands match [`README.md`](../README.md), [`frontend/package.json`](../frontend/package.json), and [`scripts/dev_studio.sh`](../scripts/dev_studio.sh).

```bash
pip install -e ".[dev,demo]"

# Rebuild the three recorded scenarios. Needs the raw JSONL, the seed-0 table, and the A7 checkpoint.
python -m rcgate.demo.fixtures

# Research studio, two shells:
python -m rcgate.studio
cd frontend && npm install && npm test && npm run dev

# Or both together. The script prefers .venv/bin/python, then python3.
# API on 127.0.0.1:8765, Vite on 127.0.0.1:5173.
./scripts/dev_studio.sh

# Separate single-answer scorer. Loads a checkpoint. Does not train.
streamlit run rcgate/demo/app.py
```

`npm run dev` is Vite. `npm test` is `vitest run`. `npm run lint` is `tsc --noEmit`. `npm run build` is `tsc --noEmit && vite build`.

The `make m0` … `make m7` targets reproduce the original milestone pipeline. They do not replace the Stage 8 protocol and they do not establish the headline AUROCs.

If the API is not running, the library view says “The local question library is not running” and prints `python -m rcgate.studio`. The dataset view says the inventory is read by the API. The how-it-works, research, and glossary views still render, because they do not fetch. If the API is up but the checkpoint or the offline weights are missing, browsing can succeed and scoring returns an unavailable status. The stored answers remain readable. The API cannot start a useful catalog if `response.jsonl`, `source_info.jsonl`, or the seed-0 parquet is missing, because `Catalog.load` reads those files at startup.

## 15. Dataset, model-resource, and offline requirements

A reviewer who clones `main` at `4709001` and does not receive the working tree gets the milestone code and the original tracked summaries. They do not get the integrity repairs, the Stage 4–8 reports, the studio, or the frontend. A reviewer who clones `review/rcgate-handoff-v1` at `6d3ef70` gets that source and the tracked Stage 4–8 reports. The local data and weights below are still required. Record browsing needs the two JSONL files and the seed-0 parquet. Precomputed scoring also needs `results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib`. On-demand scoring of any other sentence also needs the local NLI and embedding snapshots named in the README. The reproduction note lists the same paths and the checks that were run against them.

A reviewer who receives the source tree but not the local data still cannot run the studio. These paths are required on disk and are not in a clean clone:

| Resource | Path | Git status | Approximate size |
| --- | --- | --- | --- |
| Official RAGTruth JSONL | `data/raw/ragtruth/` | Ignored by `data/raw/` | 35 MB |
| Corrected signal tables | `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` and companions `s1`, `s2` | Ignored by `data/signal_tables/` | about 100 KB each |
| Studio checkpoint | `results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib` | Untracked | part of the Stage 8 tree |
| NLI and embedding weights | `.cache/models/hub/` snapshots for `nli-deberta-v3-small` and `all-MiniLM-L6-v2` | Ignored by `.cache/` | inside the 685 MB `.cache` directory |
| Python environment | `.venv/` | Ignored | 1.2 GB |
| Frontend packages | `frontend/node_modules/` | Ignored by the committed `node_modules/` rule. The directory is on disk and is not tracked | 103 MB |
| Accidental root install | `node_modules/` | Ignored by the same committed rule, including `.vitest/.vitest-secret-token` | 244 KB on 10 October |

`python -m rcgate.demo.fixtures` needs the same raw files, the seed-0 table, and the checkpoint in order to rewrite `scenarios.json`. The checked-in copy of that JSON, once it is shared, lets the frontend unit tests import three scenarios without rebuilding them. It does not let the corpus browser run.

Do not push the raw dataset or the model weights merely to make a clone easier to start. The JSONL files are the official RAGTruth release and are already excluded by the inherited ignore rule. The weight files are third-party model snapshots used as local feature extractors.

## 16. Tests, lint, build, and visual verification

**What exists in the tree.** New or extended tests cover de-aliasing, sentence alignment, grouped bootstrap labelling, the group-stratified splitter, the multi-seed and factorial helpers, demo generator identity and checkpoint provenance, the three-scenario fixture, and the studio catalog, scoring, and HTTP handlers. Frontend tests cover playback, fusion against the fixture, layout, and the app shell. Commands are `pytest` (dev extra), `ruff`, `npm test`, and `npm run lint`.

**What this handoff did not do.** On 10 October it did not re-run pytest, ruff, vitest, the TypeScript check, or the production build. It did not open the studio in a browser. A green test log from an earlier session is not stored as a file this audit could read.

**Checked on 20 October 2026.** `.venv/bin/pytest -q` exited 0: 317 tests, with three pre-existing warnings (a non-writable NumPy tensor, a loky core-count fallback, and a torch.jit.script deprecation). `ruff check tests/test_stage8_record.py` exited 0. A full-tree ruff run was not part of this check. In `frontend/`, `npm test` passed 10 tests, `npm run lint` (`tsc --noEmit`) exited 0, and `npm run build` exited 0. The studio was not opened in a browser.

**Screenshots.** The repository contains historical result plots (`results/summary/ragtruth.gate_weights.png`, `synthetic.gate_weights.png`, the Stage 4 `report.gate_weights.png`, and two smoke-test plots). It does not contain Research Studio screenshots. A reviewer cannot see the visual verification from Git.

## 17. Complete file-change inventory and Git audit

The counts in this section are the 10 October 2026 audit, before commit `6d3ef70`. They are not the branch state recorded in the 20 October status section.

Commands actually run for this section included `git status`, `git status --short`, `git status --short -uall`, `git status --ignored --short -uall`, `git diff --stat`, `git diff --numstat`, `git diff --check`, `git diff` on `.gitignore` and the three status-note files, `git branch -vv`, `git branch -a`, `git log`, `git ls-files`, `git check-ignore -v`, and `git remote -v`. `git diff --check` exited 0. There were no whitespace errors in the tracked diff.

| Item | Result |
| --- | --- |
| Branch | `main`, tracking `origin/main`, not ahead, not behind |
| Other remote branches | `origin/dev`, `origin/main` |
| HEAD | `47090018414f657bca8e5a43e97663feba2e5a7d` |
| Staged | 0 |
| Unstaged modifications | 17 files, +2,270 / −200 lines |
| Added (tracked new files in the index) | 0 |
| Deleted | 0 |
| Renamed | 0 |
| Mode changes | none in `git diff --summary` |
| Untracked files | 2,727 |
| Ignored files | 48,345 |
| Tracked files | 348 |
| Working tree size | 2.1 GB, of which `.git` is 7.1 MB |

The 17 modified tracked files are:

| File | Role of the unstaged diff |
| --- | --- |
| `.gitignore` | Adds `frontend/node_modules/` and `frontend/dist/` |
| `DECISIONS.md` | Status note only |
| `README.md` | Points at the final report and the studio; retires the old headline |
| `docs/adr/001-metadata-only-gate.md` | Status note only |
| `docs/postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md` | Status note only |
| `rcgate/claims/dealias.py` | Prompt-antecedent repair |
| `rcgate/data/__init__.py`, `build.py`, `ragtruth.py` | Alignment and claim construction |
| `rcgate/data/splits.py` | Group-stratified splitter beside the legacy function |
| `rcgate/metrics.py` | Grouped bootstrap and paired grouped delta |
| `rcgate/pipeline.py` | Exact threshold serialization |
| `rcgate/evaluate.py` | Small evaluation-path change accompanying the metrics work |
| `rcgate/demo/app.py` | Streamlit scorer redesign, generator selection, provenance |
| `tests/test_demo.py`, `test_ragtruth.py`, `test_synthetic.py` | Regression coverage |

Untracked files by top directory:

| Directory or file | Files | Approx. size | What it is |
| --- | ---: | ---: | --- |
| `results/` | 2,646 | 91 MB | Stage 4–8 outputs and the historical freeze |
| `frontend/` | 33 | 176 KB of source, plus a 106 KB lockfile | Research Studio page. `node_modules` is not in this count |
| `node_modules/` at repo root | 16 | 244 KB | Accidental install, still on disk. Git now ignores it, including `.vitest-secret-token`. It is not staged |
| `rcgate/` new modules | 12 | inside the 1.6 MB package tree | Studio, factorial, multi-seed, split sensitivity, stats, fixtures |
| `tests/` | 7 | small | New test modules |
| `configs/` | 4 | small | Stage 4–8 YAML |
| Preserved documents at repo root | 3 | 0.83 MB | Proposal, user guide, initial draft |
| `docs/` | 2 | inside 128 KB | Final report and experiment index |
| `demo_fixtures/` | 2 | 36 KB | Three scenarios and two references |
| `scripts/` | 1 | small | `dev_studio.sh` |
| `.streamlit/` | 1 | small | Theme. Usage stats off |

Stage result trees:

| Directory | Files | Size | Contents |
| --- | ---: | ---: | --- |
| `results/summary/ragtruth_factorial_seed_v1/` | 1,930 | 64.0 MB | Stage 8. 481 checkpoints, 482 prediction tables, per-cell JSON and YAML, plus the report, provenance, and CSVs |
| `results/summary/ragtruth_multi_seed_v1/` | 526 | 18.8 MB | Stage 7 |
| `results/summary/ragtruth_corrected_integrity_v1/` | 98 | 4.0 MB | Stage 4, including verdict and comparison notes |
| `results/summary/ragtruth_split_corrected_v1/` | 81 | 2.9 MB | Stage 6 |
| `results/summary/ragtruth_historical_freeze/` | 8 | 1.1 MB | Freeze manifest and reconstructed frames. The original tracked `ragtruth/` directory is the canonical historical copy |
| `results/summary/ragtruth_corrected_stats_v1/` | 3 | 0.1 MB | Stage 5 report, JSON, provenance. No new checkpoints |

Ignored files are mostly `.venv` (32,761), `.cache` (10,087), and `frontend/node_modules` plus `frontend/dist` (5,402). They do not appear in the 2,727 untracked count. `data/raw/` and `data/signal_tables/` are ignored. Tracked data is only `data/benchmarks/` (the RAGTruth notes, not the JSONL).

`git check-ignore -v` on 10 October 2026 confirmed that `frontend/node_modules/`, `frontend/dist/`, `.venv/`, `.cache/`, `data/raw/`, `data/signal_tables/`, and `.pytest_cache/` matched `.gitignore`. That check did not yet ignore the repo-root `node_modules/`. The review-branch `.gitignore` now has a `node_modules/` rule, so Git ignores both the root directory and nested ones such as `frontend/node_modules/`. The root `node_modules/` directory remains on disk. It is not staged. The file `node_modules/.vitest/.vitest-secret-token` stays inside that ignored directory and is not staged. Generated dependencies are not part of the review branch. The same ignore file does not hide `demo_fixtures/`, the new docs, the React source, or the Stage 8 report.

### Category classification

**A. Required application source.** The 17 modified Python and documentation files that are real code or status notes, plus 12 new Python modules, `scripts/dev_studio.sh`, and 33 frontend source and config files. On 10 October they were unstaged or untracked. Commit `6d3ef70` tracks them.

**B. Tests.** 7 new test modules, plus the three modified test files. Small. Required with the source.

**C. Documentation.** Final report, experiment index, this handoff, README, status notes, and the three preserved source documents (proposal `.docx`, user guide PDF, initial draft PDF). The preserved documents are historical. They are not the experimental record. Their filenames include a space in `RC Gate_Intial_Research Paper Draft.pdf`.

**D. Demo fixtures.** `demo_fixtures/scenarios.json`, `demo_fixtures/independent_references.json`, and `.streamlit/config.toml`. Small. Required for the recorded fixture tests, the reference panel, and the Streamlit theme. Not benchmark results.

**E. Canonical experiment record.** Stage 8 report, `report.json`, `provenance.json`, `seed_metrics.csv`, `paired_deltas.csv`, and the Stage 4–7 reports. The per-cell checkpoints and prediction tables are the reproducibility archive for those reports. They are untracked because `results/summary/` is the exception to `results/*` in `.gitignore`. [`results/README.md`](../results/README.md) says curated summary tables are what get committed. It was written for the original milestone summaries. It does not by itself say that all 1,930 Stage 8 files must be committed, and it does not say they should be deleted.

**F. Historical results deliberately retained.** Already tracked: `results/summary/ragtruth/`, `ragtruth.md`, `ragtruth.json`, synthetic summaries, and gate-weight plots. Untracked freeze: `results/summary/ragtruth_historical_freeze/`. Do not delete the tracked original to tidy the branch.

**G. Local raw data.** `data/raw/ragtruth/` (35 MB) and `data/benchmarks/` (tracked notes only). The JSONL files are required to run the studio and were required to build the slice. They are intentionally untracked.

**H. Model checkpoints and other binaries.** Stage 4–8 `model.joblib` files (hundreds of them, the largest about 0.66 MB each, mostly A4). The one studio checkpoint is `A7_split0_model0/model.joblib`. Local transformer weights live under `.cache/` and are ignored. The inherited tracked checkpoints under `results/summary/ragtruth/` stay tracked.

**I. Generated and local-only material.** `.venv`, `.cache`, `.pytest_cache`, `.ruff_cache`, `rcgate.egg-info`, `__pycache__`, `frontend/node_modules`, `frontend/dist`, and the root `node_modules`. The root directory remains on disk and is now ignored. Its Vitest token file is not staged. Generated dependencies should not be included in the review branch.

Nothing in this inventory was deleted or reverted.

## 18. `.gitignore` findings and recommendations

The inherited rules already ignore Python caches, virtual environments, `.cache/`, `data/raw/`, `data/signal_tables/`, and everything under `results/` except `results/README.md`, `results/.gitkeep`, and `results/summary/`. That last exception is why the Stage 4–8 directories appear as thousands of untracked files. The exception is doing what it was written to do. Adding `results/summary/` to the ignore list would hide the scientific record from review, and it would not untrack the original summaries that are already in Git. Adding a path to `.gitignore` never removes a tracked file.

The review-branch `.gitignore` adds:

```
frontend/node_modules/
frontend/dist/
node_modules/
.DS_Store
.env
.env.*
!.env.example
```

`node_modules/` ignores the accidental root install and nested installs, including `frontend/node_modules/`. The root `node_modules/` directory remains on disk. Git ignores it. `node_modules/.vitest/.vitest-secret-token` is not staged. Generated dependencies should not be included in the review branch. These rules do not match React source, `package.json`, `package-lock.json`, fixtures, reports, or checkpoints. `.env` is not present. `!.env.example` keeps an example file visible if one is added later. No tracked `.env.example` exists.

**Do not add**, without a separate human decision:

- `demo_fixtures/`
- `frontend/src/`
- `docs/`
- `*.joblib` or `*.parquet` as global patterns
- `data/signal_tables/` beyond the existing directory ignore
- anything that would hide `configs/`, `scripts/`, or the final report

## 19. What is complete, incomplete, and deliberately not implemented

**Complete enough to hand off**

- Integrity repair in a separate namespace, with historical results kept.
- Statistical labelling repair from Stage 5 onward.
- Group-stratified splitter, twenty-seed study, and the 20×3 factorial.
- Final research report and experiment index.
- Offline studio and the separate Streamlit scorer.
- Tests that encode the repairs and the studio invariants.

**Incomplete**

- Exact reproduction of the 480 Stage 8 fits from Git is not established. The hashed fit sources match `6d3ef70`. The signal table and per-cell checkpoints remain outside the commit. [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md) records the check.
- Official-split evaluation was not run.
- A8 was not run.
- Generator-by-type AUROC on the full QA file was not fit.
- Gate-weight scientific interpretability was not validated.
- This handoff did not re-run the test suite or a browser pass.
- No Research Studio screenshots are in the repository.
- Stages 0–3, 9, and 10 have no Git-tracked standalone audit files.

**Deliberately not implemented**

- Live multi-model generation or web retrieval inside the studio.
- Using the two curated references as scoring inputs.
- Another fit on the 800-sentence slice aimed at raising A7’s AUROC.
- A full-scale QA feature build after the support audit failed the pre-specified rule.
- Overwriting the proposal, the user guide, or the initial draft.

## 20. Recommended research roadmap

The scientific roadmap starts from a named uncertainty and a fair baseline. It does not start from hyperparameter search on A7.

### A. Necessary before sharing the branch

| Item | Objective | Why it matters | Effort | Dependency | Uncertainty addressed | What would narrow or abandon the work |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | Review this document against the final report and the Stage 8 CSV | The senior should receive one map, not 2,727 unexplained files | Small | This file | Whether the handoff matches the artifacts | If a cited figure disagrees with `seed_metrics.csv`, correct the handoff before sharing |
| A2 | Choose the commit set using Section 22 | `git add .` no longer picks up the ignored root `node_modules/`. It would still stage the untracked result archive | Small | Human approval of categories E and H | Branch hygiene | If the checkpoint archive is declined, still commit the reports, CSVs, provenance, and the one studio checkpoint, and say the rest stayed local |
| A3 | Keep the `node_modules/` ignore, including the root directory that remains on disk | The Vitest token stays unstaged with the generated dependencies | Small | The rule is already in `.gitignore` | Secrets and generated files | If a real source file would match a proposed pattern, do not add that pattern |
| A4 | Confirm a reviewer machine can start the API with the local JSONL, seed-0 table, and one checkpoint | The studio is not runnable from Git alone | Small | Those three local resources | Setup gap | If startup fails, document the missing file. Do not upload the full raw release or the weight cache to close the gap casually |
| A5 | Run the existing pytest and frontend test commands once, on the chosen tree, and keep the log with the review notes | This handoff did not re-execute them | Small to moderate | A local environment | Whether the tree still passes its own tests | A failing test is a share blocker until it is understood. Do not retune a model to make a test pass |

### B. Necessary before submitting to a venue

| Item | Objective | Why it matters | Effort | Dependency | Uncertainty addressed | What would narrow or abandon the work |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Write a pre-registered question that the available support can actually identify | Stage 10 says the full generator-by-type surface is not identified | Moderate, design only | A dataset decision | H1 and the residual gating question | If no cell meets a support floor that the authors will defend, do not submit a detector paper |
| B2 | If that question is the constrained gate versus A4 on official-test Mistral and Llama cells, with `src_quality` removed and arithmetic left out, run it once under a frozen protocol | This is the narrower question the final report already names and does not answer | Large | Official QA features built from scratch, not from the 800-row checkpoints | H2 on a less degenerate slice | If A7 still loses to A4, report the negative result or abandon the superiority claim |
| B3 | Keep A4, or an equally flat metadata-capable model, as a matched baseline | Capacity and joint use of signals and metadata are the alternative explanation for A4’s lead | Part of B2 | B2 | Whether the metadata-only constraint is doing any work | A win that disappears when the flat model sees the same inputs is not evidence for the gate |
| B4 | State label and evidence definitions as limitations or as a sensitivity | Sentence overlap, implicit-true spans, and first-sentence-only labels can change the hypothesis | Moderate | A decision to spend the annotation budget | Construct validity | If the result exists only for one labelling choice, narrow the claim to that choice |
| B5 | Resolve the open bibliographic items in final-report Section 11, or drop the sentences that depend on them | Stage 9 left author strings, DOIs, and several draft numbers unresolved | Moderate | The papers, not this repository | Novelty wording | Any sentence that still cannot be checked should leave the submission |

### C. Optional future research

| Item | Objective | Why it matters | Effort | Dependency | Uncertainty addressed | What would narrow or abandon the work |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Obtain or construct a corpus with enough positive sentences in the generator-by-type cells the hypothesis names | The current QA release does not provide that support | Large | Data, licence, annotation | H1 | If the new corpus still cannot fill the GPT or extractive cells, drop those cells from the claim |
| C2 | Test the interaction of claim type, generator family, and signal reliability with the matched flat baseline | That interaction is the content of H1 | Large | C1 or an explicit subset | H1 | A flat model that captures the same interaction removes the reason for the constrained gate |
| C3 | Change the architecture only after C1 or B2 identifies a failure the current gate cannot express | An architecture change now would be aimed at the same under-identified slice | Unknown | A precise negative result | Whether the loss is the metadata-only constraint or the data | Do not treat a higher AUROC from tuning as a new scientific result |

**Engineering notes that are not experiments.** The milestone `make` targets remain the old pipeline. Dependency installation is `pip install -e ".[dev,demo]"` and `npm install` inside `frontend/`. A clone of `6d3ef70` contains the hashed Stage 8 fit sources and the tracked summaries. Reproducing the 480 fits still requires the local signal table, and that rerun has not been verified. The limits are in [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md). Branch hygiene is Section 23.

**Not recommended.** Broad hyperparameter tuning to improve A7’s AUROC on this slice. Another 20-seed fit on the same 800 sentences without a new question. Presenting the synthetic recovery as evidence about real generators.

**Immediate scientific recommendation.** Freeze the current UI. Do not start another experiment on the same slice without a narrower question that names the cells, the baseline, and the support floor in advance.

## 21. Publication-readiness judgment

Publication readiness has not been established.

A submission could be reconsidered only if all of the following are true:

- The claim is no wider than the evidence. The present evidence supports an implementation, a synthetic mechanism check, a negative unstable slice result, and a feasibility bound.
- A pre-registered comparison against a flat metadata-capable baseline has been run on data that meet a support rule the authors will defend, or the superiority claim has been withdrawn.
- Judge voting is either evaluated or removed from the hypothesis.
- Official-split comparability is either established or explicitly disclaimed.
- Unverified draft numbers and author lists are gone.
- The synthetic result is described as recovery of a planted pattern.
- The sample standard deviation of repeated splits is not presented as a confidence interval.

Until then, the honest description is Section 8.4 of the final report: a research prototype, a synthetic recovery test, and a negative unstable evaluation.

## 22. Exact list of materials to share

Share one review branch plus this document. Do not send 2,000 files as individual attachments.

| # | Material | Why |
| --- | --- | --- |
| 1 | Branch `review/rcgate-handoff-v1` | The implementation check was made at `6d3ef70`, then the tip of that branch and of `origin/review/rcgate-handoff-v1`. `main` remains `4709001`. This documentation commit is a descendant of `6d3ef70` |
| 2 | This handoff, `docs/RC-Gate_Development_History_and_Senior_Handoff_v1.md` | The map |
| 3 | [`docs/RC-Gate_Final_Research_Report_v1.md`](RC-Gate_Final_Research_Report_v1.md) | The scientific record |
| 4 | [`docs/RC-Gate_Experiment_Index.md`](RC-Gate_Experiment_Index.md) | Which file is current |
| 5 | [`README.md`](../README.md) | Startup commands and the retired-headline warning |
| 6 | Stage 4 verdict and comparison: [`VERDICT.md`](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md), [`comparison.md`](../results/summary/ragtruth_corrected_integrity_v1/comparison.md) | What the integrity repair changed |
| 7 | Stage 5 report: [`ragtruth_corrected_stats_v1/report.md`](../results/summary/ragtruth_corrected_stats_v1/report.md) | The uncertainty repair |
| 8 | Stage 6 report: [`ragtruth_split_corrected_v1/report.md`](../results/summary/ragtruth_split_corrected_v1/report.md) | The split repair |
| 9 | Stage 7 report: [`ragtruth_multi_seed_v1/report.md`](../results/summary/ragtruth_multi_seed_v1/report.md) | Twenty coupled seeds |
| 10 | Stage 8 report, CSV, and provenance: [`report.md`](../results/summary/ragtruth_factorial_seed_v1/report.md), [`seed_metrics.csv`](../results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv), [`provenance.json`](../results/summary/ragtruth_factorial_seed_v1/provenance.json) | The principal numbers |
| 11 | Launch commands in Section 14 | How to start the studio |
| 12 | A short note of the local requirements in Section 15 | What a clone does not contain |

Research Studio screenshots are not in the repository. If a visual record is wanted, capture it later and add those images deliberately. Do not block the document handoff on screenshots that were never stored.

The preserved proposal, user guide, and initial draft may be included on the branch as historical documents, with the final report named as the record. They should not be described as results.

### Can a reviewer run the studio from a clean clone?

No. A clone of `main` at `4709001` lacks the studio source. A clone of `review/rcgate-handoff-v1` at `6d3ef70` contains the source and still lacks:

- `data/raw/ragtruth/response.jsonl` and `source_info.jsonl`
- `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet`
- `results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib`, unless that checkpoint is included in the branch
- the local NLI and embedding weights, if the reviewer wants to score sentences that are not in the 800-row table

Without the JSONL files the API cannot build the library. Without the parquet, precomputed rows are unavailable. Without the checkpoint, scoring returns unavailable. Without the weights, only precomputed rows can be scored. The how-it-works, research, and glossary pages can be built as a static frontend, and they do not prove the scorer works.

### Sharing categories

| Category | What | Action |
| --- | --- | --- |
| 1. Required to share the implementation | Modified Python sources, new `rcgate/studio/`, experiment driver modules, `scripts/dev_studio.sh`, frontend source and lockfile, tests, the four new configs, `.streamlit/config.toml`, the `.gitignore` lines for `frontend/node_modules/` and `frontend/dist/` | Include on the review branch |
| 2. Required to understand the research | This handoff, the final report, the experiment index, README, status notes, Stage 4–8 reports, Stage 8 CSV, JSON, and provenance | Include |
| 3. Required only for local scoring or reproduction | Raw JSONL, signal tables, `.cache` model weights, `.venv`, and every per-cell checkpoint beyond the reports | Keep local, except the single studio checkpoint if the reviewer must click Score |
| 4. Historical artifacts already tracked | `results/summary/ragtruth/`, synthetic summaries, ADRs, postmortems, `DECISIONS.md` | Leave tracked. Do not delete them in the review branch |
| 5. Exclude from the new commit | Root `node_modules/` including `.vitest/.vitest-secret-token`, `frontend/node_modules/`, `frontend/dist/`, `.venv`, `.cache`, caches, egg-info | Do not `git add` them |
| 6. Human approval | Whether all Stage 7–8 joblib and prediction files are committed; whether the historical-freeze parquets are committed; whether the three preserved office documents are committed; whether the one studio checkpoint is committed while the other checkpoints stay local | Decide before `git add`. Do not decide by deleting files |

## 23. Proposed branch and controlled merge plan

**Recommended branch name:** `review/rcgate-handoff-v1`

That branch exists. Commit `6d3ef709367d55a27a413477c624fc9f96a215ce` is on it and on `origin/review/rcgate-handoff-v1`. On 20 October 2026 that commit was the tip. This documentation commit is a descendant of it. The commands below are the 10 October procedure. They were not run while this handoff was first written. They are not the next action, and creating the branch again from a later worktree would duplicate it.

The procedure was written to be run later from the then-current `main` worktree so the uncommitted files would come along. A clean checkout of `4709001` still does not contain this work.

```bash
# From the repository root, with the current working tree intact.
git switch -c review/rcgate-handoff-v1

# Inspect ignore state before any add.
git status --short
git check-ignore -v node_modules frontend/node_modules demo_fixtures/scenarios.json \
  docs/RC-Gate_Final_Research_Report_v1.md \
  results/summary/ragtruth_factorial_seed_v1/report.md

# Stage explicit paths. Do not run git add .
# Source, tests, docs, fixtures, configs, script, streamlit theme, gitignore.
git add -- .gitignore README.md DECISIONS.md \
  docs/adr/001-metadata-only-gate.md \
  docs/postmortems/rcgate/002-m6-a4-beats-a7-on-real-data.md \
  docs/RC-Gate_Final_Research_Report_v1.md \
  docs/RC-Gate_Experiment_Index.md \
  docs/RC-Gate_Development_History_and_Senior_Handoff_v1.md \
  rcgate tests configs scripts .streamlit demo_fixtures frontend

# Do not add node_modules, .venv, .cache, data/raw, or data/signal_tables.
# Add result directories only after the human decision in Section 22 category 6.
# Example of the minimum scientific record, if full checkpoints are declined:
#   git add -- results/summary/ragtruth_corrected_stats_v1 \
#     results/summary/ragtruth_factorial_seed_v1/report.md \
#     results/summary/ragtruth_factorial_seed_v1/report.json \
#     results/summary/ragtruth_factorial_seed_v1/provenance.json \
#     results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv \
#     results/summary/ragtruth_factorial_seed_v1/paired_deltas.csv \
#     results/summary/ragtruth_factorial_seed_v1/A7_split0_model0
# Plus the Stage 4–7 report files named in Section 22.
# If the full archive is approved, add the six results/summary/ragtruth_* directories
# as explicit paths, still never with git add .

git status --short
git diff --cached --stat

# Commit and push only when the staged set has been read.
# git push -u origin review/rcgate-handoff-v1
# gh pr create --base main --head review/rcgate-handoff-v1
```

`frontend/` as a path is safe only while `frontend/node_modules/` and `frontend/dist/` remain ignored. Confirm that with `git check-ignore` and `git status` before the add. `git add frontend` will still pick up source and the lockfile.

Do not open the pull request against a force-push of `main`. The review branch should be a normal pull request into `main` after the staged set is agreed. `origin/dev` exists from the original milestone PR. This handoff does not recommend appending the new work onto `origin/dev` without looking at how far that branch has moved. At the time of this audit, local `main` and `origin/main` are the merge of that PR, and there is no local `dev` branch.

## 24. Risks, caveats, and unresolved questions

- **Stage 8 provenance.** `provenance.json` records a dirty tree at `47090018414f657bca8e5a43e97663feba2e5a7d` and says that HEAD alone does not reproduce the run. That remains true for `main`. On `6d3ef70` the twelve hashed fit sources match the provenance digests. Unhashed dirty-tree files have no stored run-time digest, the table was not rebuilt, and the 480 fits were not rerun. See [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md).
- **One question pool.** Twenty splits are repeated partitions of 134 questions. Training sentences overlap across splits.
- **First-sentence prefix.** Every evaluated claim is sentence index 0. Later sentences in the answers were not the fitted sample.
- **Mixed tasks.** The 800-row table is 402 QA and 398 Summary. Recent News is absent. Data-to-text was not in the fit.
- **Official split ignored, and official test sources inside the slice.** Published RAGTruth numbers are not comparable without that qualifier.
- **Degenerate features.** Constant source quality, inactive arithmetic checker, rule-based types, one GPT-4 positive in the slice.
- **A7 instability.** AUROC on the 60 cells runs from 0.3072 to 0.7983. Three model seeds are a small sample of initialisation noise.
- **Thresholds.** About nine validation positives. F1 is unstable. AUROC is the metric that does not depend on the threshold.
- **Missing external detectors.** A4 is an internal control, not the published state of the art.
- **Synthetic plant.** Recovery is not evidence about real generators.
- **Literature scope.** Stage 9 is not a systematic review. Several citations remain unresolved in the final report.
- **Canvases outside Git.** Stages 9 and 10, and an integrity canvas, are local Cursor files. They can disappear without the repository noticing. The Git record is the final report.
- **No stored UI screenshots.** The 20 October test commands are in Section 16. The studio was not opened in a browser.
- **GitHub Desktop count.** On 10 October the expanded untracked count was 2,727, not the collapsed status of about 50 lines. On 20 October, after `6d3ef70`, `git ls-files -o --exclude-standard` listed 2,628 untracked files, all result artifacts. `git status --porcelain` showed 732 collapsed lines.
- **Accidental root `node_modules`.** The directory remains on disk and is ignored. Its `.vitest-secret-token` is not staged. Generated dependencies are not included in the review branch.
- **Preserved documents disagree with the repository.** The status notes and the final report, Section 8.5, are the warning. The original sentences were kept on purpose.
- **Historical A8 metrics** contain an old absolute filesystem path. It is not a secret. It is a reminder that inherited artifacts carry the machine they were written on.

Unresolved questions that are scientific rather than clerical:

- Does the metadata-only constraint beat a flat metadata-capable model on any cell that has adequate positive support?
- Do sentence-level overlap labels, including implicit-true spans, change that answer?
- Are the gate weights calibrated to the family that is actually more reliable, or only printable?

This audit does not answer those questions.

## 25. Appendix: claims, artifacts, and Git state

The rows below are the 10 October 2026 checks. The 20 October branch state and the Stage 8 hash check are in the status section and in [`docs/RC-Gate_Stage8_Reproduction_Note.md`](RC-Gate_Stage8_Reproduction_Note.md).

| Claim | Where it was checked | Git state of that artifact |
| --- | --- | --- |
| HEAD is `4709001`, branch `main` even with `origin/main` | `git status -sb`, `git log -1`, `git branch -vv` | Committed |
| 17 modified, 0 staged, 0 deleted, 2,727 untracked, 48,345 ignored | `git status --short -uall` and `git status --ignored --short -uall` on 10 October 2026 | Working tree |
| `git diff --check` is clean | Exit code 0 | Applies to the 17-file diff only |
| Stage 8 means 0.6280, 0.6839, 0.5717; paired −0.0563 and −0.1122; A7 sample SD 0.1247 | Recomputed from [`seed_metrics.csv`](../results/summary/ragtruth_factorial_seed_v1/seed_metrics.csv); also printed in [`report.md`](../results/summary/ragtruth_factorial_seed_v1/report.md) and final-report Table 7 | Untracked |
| 480 fits, 60 cells, 15 test positives, 28 test questions, in-memory scores matched | Same CSV, `scores_equal_in_memory` all true | Untracked |
| A7 has 233 parameters, gate input 8, logit fusion | `A7_split0_model0/metrics.json` field `fit_info` | Untracked |
| Seed-0 table: 800 rows, 134 questions, 57 positives, QA 402, Summary 398, sentence index 0 only, `src_quality` 0.9, arithmetic unverifiable | Read from the parquet in this audit. SHA-256 matches the final report | Ignored (`data/signal_tables/`) |
| Official JSONL sizes, row counts, six models, task counts, train/test response counts, hashes | Read from the local JSONL in this audit | Ignored (`data/raw/`) |
| Sentence-level QA support grid and the 11-of-24 estimable-cell count | Final report Section 4.4 only. Not re-derived in this audit | No result directory |
| Stage 4 text-repair counts and the 0.631 to 0.638 movement | [`VERDICT.md`](../results/summary/ragtruth_corrected_integrity_v1/VERDICT.md) | Untracked |
| Stage 5–7 secondary means | The three report.md files linked in Section 9 | Untracked |
| Synthetic pooled means and the numeric plant | Final report Section 5.1, citing [`results/summary/synthetic.md`](../results/summary/synthetic.md) and [`DECISIONS.md`](../DECISIONS.md) | Synthetic summary is tracked. `DECISIONS.md` has an unstaged status note |
| H1/H2/H3 outcomes | Final report Table 9 | Untracked report |
| Both references have `used_in_rcgate_score: false` | [`independent_references.json`](../demo_fixtures/independent_references.json) and `rcgate/studio/references.py` | Untracked |
| Studio checkpoint path and offline flags | `rcgate/studio/catalog.py`, `rcgate/studio/__main__.py` | Untracked |
| Launch commands | [`README.md`](../README.md), [`frontend/package.json`](../frontend/package.json), [`scripts/dev_studio.sh`](../scripts/dev_studio.sh) | README is modified. Package and script are untracked |
| Stages 9 and 10 have no Git-tracked standalone report | [`docs/RC-Gate_Experiment_Index.md`](RC-Gate_Experiment_Index.md). Canvases exist only outside the repository | Index is untracked |
| This task changed no research result and no source file other than this document | `git status` after writing this file. See the validation note below | This file is untracked |

### Validation note for this document

Checked while writing:

- Relative links in this file point at paths that exist in the working tree, including untracked paths. A clean clone of `main` will not contain the untracked targets until they are committed.
- Stage 8 headline figures were recomputed from `seed_metrics.csv`.
- File counts and branch state were taken from the Git commands listed in Section 17.
- Launch commands were compared with the README and `frontend/package.json`.
- `git diff --check` was run on the pre-existing tracked diff and exited 0.
- No result file and no existing source file was edited to produce this document. The working tree was already dirty. It is not clean.

### Materials this audit did not treat as proof

- Conversation transcripts. None were opened.
- The local canvases. Their presence was confirmed. Their contents were not used as a second source of experimental numbers.
- A fresh pytest, ruff, vitest, or browser pass was not part of the 10 October audit. The 20 October check in Section 16 ran pytest, the new-file ruff check, vitest, `tsc --noEmit`, and the production build. It did not open the studio in a browser, and it did not run ruff on the whole tree.
- A re-derivation of the official QA sentence grid or of the 30/15 cell counts.

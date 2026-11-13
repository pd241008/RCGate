# Protocol-to-code feasibility matrix

**Date:** 23 October 2026  
**Status:** Inventory only. No scored inference, no corpus download, no method implementation.  
**Governing documents:** `research/plan/RCGate_Focused_Research_Pivot_v0_3.md`, `RCGate_Pilot_Protocol_v0_2.md`, `RCGate_Annotation_Protocol_v0_1.md`, `RCGate_Pilot_Decision_Record_v0_1.md`.

Support labels:

- `READY` — existing code can be used for this pilot requirement with a recorded configuration.
- `PARTIAL` — a related primitive exists and can be reused, and the pilot behavior is not implemented.
- `MISSING` — no implementation.
- `BLOCKED` — a required input, freeze, or external dependency is absent, so the step cannot start.

Stage 8 AUROC and A0–A8 hallucination-detection results are historical. They are not pilot findings.

Novelty is not established. The Byrd SSRN preprint and the Belkin, Madsen, and de-Wit 2026 source-dependence record remain unaudited at full-text and code level, as the pivot document states.

## Environment found during inventory

| Item | Observation |
|---|---|
| Python | 3.12.14 at `.venv/bin/python`. `pyproject.toml` requires `>=3.11` and does not pin dependency versions. No `requirements.txt`, Poetry lock, or `uv.lock`. |
| Installed libraries | torch 2.14.1 (MPS built; device availability not probed), transformers 5.19.0, sentence-transformers 6.1.0, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1, rank-bm25 0.2.2, scipy 1.18.1, matplotlib 3.11.2, pytest 9.1.1, ruff 0.16.10, streamlit 1.65.0 |
| Absent libraries | `tiktoken`, `openai`, `anthropic`, `krippendorff`, `simpledorff` |
| Node | v24.13.0, npm 11.6.2. Lockfile: `frontend/package-lock.json`. Frontend tests: `frontend/src/*.test.ts(x)` via Vitest. |
| Hardware | Apple M4, 10 cores, 24 GiB RAM (25769803776 bytes). No CUDA device was probed. |
| Secrets | No `.env` file. The checked API-key names were unset in the process environment. Values were not printed. |
| API budget file | `configs/budget.yaml` sets `dry_run: true`, `max_usd: 2.0`, `max_calls: 400`. That file is a historical spend guard. It is not authorization for a pilot API run. |
| Annotation tools | `label-studio` and `prodigy` were not on `PATH`. |
| Tests | 21 Python modules under `tests/`. They target the historical signal-table, split, demo, and Stage 8 record. They were not executed in this preflight. `.venv/bin/pytest` exists; `pytest` is not on the shell `PATH`. |
| Local model cache | `.cache/models` is about 639 MB inside a 685 MB `.cache`. Two Hugging Face snapshots only: `cross-encoder/nli-deberta-v3-small` revision `fa2804872c3b4bd748f38c0185cc85775361e735`, and `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. |
| Local LLM files | Ollama client 0.33.3 is installed. The server was not running. Manifests on disk show `llama3.2:1b` and `llama3.2:latest` pointing at the same 1.2B Q8_0 GGUF, weight digest `sha256:74701a8c35f6c8d9a4b91f3f3497643001d63e0c7a84e085bed452548fa88d45` (about 1.32 GB). |
| Data on disk | `data/raw/ragtruth/`: 2,965 `source_info` rows and 17,790 responses. Signal tables `data/signal_tables/ragtruth_corrected_integrity_v1_s{0,1,2}.parquet` have 800 rows each. |

## Mandatory pilot pieces

| Requirement | Support | Existing support | Dependency and cost | Smallest safe next step |
|---|---|---|---|---|
| Frozen V1 LLM judge | `BLOCKED` | No judge client exists. `DiskCache.call` in `rcgate/signals/cache.py` (about lines 118–174) caches an injected function. It does not call a provider. `configs/budget.yaml` names `gpt-4o-mini`, `gpt-4.1-mini`, and `claude-haiku` as price placeholders. `MajorityVote` in `rcgate/models/baselines.py` (lines 209–222) reads `judge_votes` / `judge_n` if those columns exist. `is_runnable` in `rcgate/variants.py` (lines 52–58) skips A8 when they do not. Signal tables have no judge columns. `rcgate/prompts/` has no prompt files. Decision-record V1 fields are blank. | The only on-disk LLM is Llama 3.2 1.2B Q8_0 via Ollama. Using it costs local CPU/Metal time and $0 API. It is not frozen: no prompt hash, decoding settings, output schema, retry rule, or context length. A larger judge requires a download or an API key, neither of which is authorized. | User decides whether this 1.2B digest is an acceptable V1. Do not start `ollama serve` or generate text until that decision is written down. |
| Frozen V2 NLI model | `PARTIAL` | `CrossEncoderScorer` in `rcgate/signals/nli.py` (lines 125–184) loads `cross-encoder/nli-deberta-v3-small` by default (lines 32–33). Local `config.json` maps labels `contradiction=0`, `entailment=1`, `neutral=2`. `score_claim` in `rcgate/signals/evidence.py` (lines 182–224) aggregates entailment by `max` or `mean` and sets conflict to max contradiction. `build_scorer` (nli.py lines 259–289) falls back to `LexicalScorer` if loading fails. | Weights are on disk. A CPU forward pass is affordable on this M4 for a 40–60 claim pilot. The pilot aggregation rule, truncation policy, and four-way verdict map are not frozen. Silent lexical fallback would break the freeze. | Record the snapshot hash and label map in the decision record when the user accepts V2. Specify a fail-closed loader and the verdict rule before any scored call. |
| Lexical duplicate baseline | `MISSING` | `LexicalScorer.score` (nli.py lines 78–122) is token-overlap entailment, not passage deduplication. `_hashing_embed` (nli.py lines 234–249) is a trigram hash used when MiniLM is absent. `_text_duplication` in `rcgate/split_sensitivity.py` (lines 195–252) counts exact duplicate `claim_text` strings for leakage diagnosis. `Bm25Index` in `rcgate/signals/evidence.py` (lines 101–116) ranks sentences. None remove or cluster passages. | New code. CPU-only. No new model. | After the manifest schema exists, add exact/normalized duplicate removal and a character- or word-shingle overlap on a fixture. Choose any threshold on the calibration batch only. |
| Semantic duplicate baseline | `PARTIAL` | `Embedder.best_sentence_similarity` and `CrossEncoderScorer.similarity` (nli.py lines 189–220) compute cosine similarity with MiniLM when the cross-encoder backend loads. The local MiniLM snapshot is `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 dimensions, `model_max_length` 512. There is no clustering, no frozen threshold, and no “count clusters rather than URLs” routine. | Local encoder, CPU, $0. Running it is scored-model-adjacent and waits for approval. A threshold fit on the same cases later reported as the pilot would leak the baseline. | Keep the encoder id and snapshot in the proposed freeze. Implement clustering only after a calibration/dev split exists. Do not encode the pilot set in this preflight. |
| Cap / count baseline | `MISSING` | Evidence aggregation is max or mean of NLI scores (evidence.py lines 215–216). `src_quality` (evidence.py lines 11–18 and 81–91) is a domain-tier heuristic for benchmark context versus web domains. A8 is a judge-vote ratio, not a source count. Nothing caps support by cluster or by independent-source count. | New code once cluster ids exist. The cap is a baseline, and document-level clusters remain a baseline in the pivot, not the gold representation. | Define the cap on a fixture: one vote per lexical or semantic cluster, with `UNKNOWN` pairs left unmerged. |
| Token counting | `PARTIAL` | NLI truncation is `max_length: int = 256` in `CrossEncoderScorer.__init__` (nli.py lines 134–140). The cached DeBERTa tokenizer config says `model_max_length` 512. `rcgate/signals/extract.py` notes that truncation (around line 50). `tiktoken` is not installed. The Llama GGUF has no separate tokenizer file in the Ollama manifest. Ollama’s runtime context was not read because the server was down. | Counting with the cached DeBERTa tokenizer is a local, non-scoring load and still needs an explicit approval if it initializes Transformers. V1 token budgets cannot be matched until a Llama context length and tokenizer are frozen. | Add a count-only function for the NLI tokenizer after V2 is accepted. Leave V1 token matching blocked until the context setting is chosen. |
| Order randomization | `MISSING` | `grouped_split` in `rcgate/data/splits.py` (from line 56) shuffles question groups for train/val/test. That is a data split, not passage order inside a prompt. No counterbalance seed or alternate-order subset exists for evidence sets. | New code. A recorded seed and a stored permutation are enough. No model call. | When evidence-set records exist, assign a permutation per case from a frozen seed and store it in the manifest. |
| Source metadata | `PARTIAL` | RAGTruth `source_info` keys are `prompt`, `source`, `source_id`, `source_info`, `task_type` (`rcgate/data/ragtruth.py` lines 11–16). Task counts: Summary 943, Data2txt 1033, QA 989. Forty-nine of 2,965 source rows contain an `http` token in `source_info` or `prompt`. There is no publisher, author, archive id, or publication timestamp field. The studio catalog formats passages for the historical demo (`rcgate/studio/catalog.py`). | Historical fields describe one supplied context. They do not carry lineage. New pilot records need URL, archive, timestamps, publisher, and cited primary artifact, as annotation protocol §9. | Design those fields in the annotation schema. Do not scrape them in this preflight. |
| Immutable manifests / hashes | `PARTIAL` | `sha256_of` in `rcgate/data/ragtruth.py` (lines 99–100) hashes dataset files. Similar helpers exist in `rcgate/factorial_seed.py` (line 210), `rcgate/multi_seed.py` (line 97), `rcgate/split_sensitivity.py` (line 74), and `rcgate/demo/fixtures.py` (line 105). `make_key` in `rcgate/signals/cache.py` (lines 66–78) hashes provider, model, prompt, and params. Nothing writes a pilot input manifest of passages, snapshots, and annotation exports. | New manifest writer can reuse the SHA-256 pattern. Cost is local hashing. | First implementation step: a manifest format and a hasher for pilot files, outside `results/` and `data/raw/`. |
| Per-annotator labels | `MISSING` | `rcgate/data/schema.py` defines a binary hallucination signal table (`label` 0/1, lines 14–22). Optional columns include `judge_votes` (lines 25–32). There is no `annotator_id`, raw-versus-adjudicated split, or relation edge. | New export format. No model. Two human annotators are a staffing dependency, not a code dependency. | Validate exports against `ANNOTATION_SCHEMA_PROPOSAL.json` on a hand-written fixture that keeps two raw records and one adjudication object. |
| Metric scripts | `PARTIAL` | `rcgate/metrics.py` provides binary AUROC (line 19), F1 at a threshold (line 45), validation-only threshold search (line 72), and question-grouped AUROC bootstrap (`bootstrap_auroc_ci_grouped`, line 169). `rcgate/stats_protocol.py` `within_seed_auroc_interval` (line 109) and `paired_question_delta` (line 150) estimate AUROC differences. The pilot primary outcome is a paired false-support risk difference on four-way evidence status. Krippendorff’s alpha is not installed. scikit-learn can supply Cohen’s kappa, and no project function calls it for these labels. | New metric script. Can be tested on synthetic label fixtures with no model. Clustered resampling ideas can be reused later; the estimand cannot be copied from Stage 8. | Implement FS rates, stratum splits, and paired risk difference on a fixture before any verifier exists. |

## Rest of the pilot protocol

| Requirement | Support | Existing support | Dependency and cost | Smallest safe next step |
|---|---|---|---|---|
| Four annotation layers kept separate | `MISSING` | Historical label is one binary hallucination bit per response sentence. | Schema proposal only. | Use the proposal schema. Do not collapse truth, stance, evidence status, and origin. |
| Claim–passage stance | `PARTIAL` | NLI returns entailment, contradiction, and neutral probabilities. The codebook stance set is `ENTAILS_OR_ASSERTS`, `CONTRADICTS`, `NEITHER`, `MIXED`. Neutral probability is not the human label `NEITHER`. | Human labels first. Model scores are not gold. | Store human stance. Keep NLI probabilities in a separate prediction record. |
| Evidence-set status, four classes | `MISSING` | No `ADEQUATE_SUPPORT` / `ADEQUATE_REFUTATION` / `INSUFFICIENT` / `CONFLICTING` field. | Human adjudication. Domain standard is not yet written. | User writes the domain adequacy standard before scored annotation. |
| Text, lineage, and epistemic edges | `MISSING` | No graph storage. Clustering code is also absent, so the repo does not currently force clusters. | Schema must store directed, partial, non-transitive edges and explicit `UNKNOWN`. | Adopt the edge object in the schema proposal. |
| Two experimental arms and gold-status invariant | `MISSING` | No condition ids, token-match report, or eligibility flag. Codebook and protocol use different condition strings (see the data report). | Annotation workload. | Freeze one condition vocabulary before labeling. |
| Exact/normalized duplicate removal | `MISSING` | Exact-text counts exist only as a split diagnostic. | Local string normalization. | Fixture test: byte-identical and whitespace-normalized copies collapse; paraphrases do not. |
| Uncorrected claim–passage support baseline | `PARTIAL` | `score_claim` is this family of baseline, aimed at one claim string against BM25 sentences, with a continuous support score. | Needs a declared map from scores to four evidence-status labels. | Specify that map before scoring. A continuous score is only a diagnostic. |
| IMRRF-style redundancy filter | `BLOCKED` | IMRRF code is not in this repository. The protocol allows an adaptation only when it sees the same frozen evidence, and requires it to be labeled an adaptation. | Reimplementation would be a new method and may need its own model. Out of the smallest path. | Leave it out of the first pilot build. Record it as a later comparator. |
| Gold-provenance oracle diagnostic | `MISSING` | No relation-corrected aggregator. | Depends on adjudicated edges. It is a diagnostic for one correction rule. | Specify the correction on paper after the edge schema is accepted. Implement it after labels exist. |
| Calibration batch disjoint from scored items | `MISSING` | Historical splits group `question_id` (`rcgate/data/splits.py`). They do not know `claim_family_id` or `source_origin_family_id`. | New partitioner. | Assign families before collection. Exclude calibration ids in the metric script. |
| Blinding to verifier output | `MISSING` | Studio and demo display historical model scores to a user. That UI is the wrong annotation surface. | Process requirement. | Keep annotation files in a directory the scoring job does not read, and keep predictions out of the annotation export. |
| Agreement, unknown rate, adjudication, time | `MISSING` | No annotation timer or agreement report. | Optional later dependency: a Krippendorff package. Cohen’s kappa can come from scikit-learn already installed. | Compute raw agreement from the fixture first. Add alpha when the dependency is approved. The numeric reliability gate stays blank until the user sets it before scored labels. |
| Naturalistic versus controlled reporting | `MISSING` | No arm field. | Reporting script only. | Stratify metrics by `condition_id` and by arm. |
| Independent-corroboration guardrail | `MISSING` | No such contrast. | Needs cases where annotators judge that independent evidence changes gold status. | Store those cases outside the primary duplicate-invariance set. |
| Order-sensitivity subset | `MISSING` | No second permutation. | A small extra annotation/scoring set later. | Reserve the subset id in the manifest before scoring. |
| Stop/go record | `PARTIAL` | `RCGate_Pilot_Decision_Record_v0_1.md` has the checklist and blank outcome lines. No freeze field is filled. | User decisions. | Fill freeze fields only when the user chooses. This preflight does not fill them. |
| Reproducible run environment | `PARTIAL` | Git HEAD is known. Python versions above were read from the venv and are not locked. | A lockfile would be a source change and is not made here. | Copy the version table into the decision record at freeze time. |
| Historical A0/A4/A7 leaderboard | `BLOCKED` for pilot use | Implemented and reported under `results/summary/` for the RAGTruth sentence task. | Reuse would mix tasks. | Leave those files untouched. Omit them from pilot tables. |

## What can be reused, and what the reuse is for

Reusable without treating old numbers as pilot results:

- SHA-256 file hashing and content-hash cache keys.
- Grouped split idea, retargeted to claim family and source-origin family.
- Local NLI cross-encoder and MiniLM embedder, after a fail-closed freeze.
- Max and mean score aggregation as one uncorrected support baseline.
- Grouped bootstrap mechanics, retargeted to the paired false-support estimand and labeled exploratory.
- `DiskCache` if a future local scorer should avoid repeat CPU work. It must not be pointed at a paid API in the pilot’s first build.

Not reusable as the pilot task:

- Binary `label` on RAGTruth sentences.
- Six-signal hallucination table and A0–A8 gates.
- `src_quality` domain tiers as evidence of independence.
- Stage 8 metrics, manuscripts, and `results/summary/` tables.

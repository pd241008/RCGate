# Stage 8 reproduction note

**Checked 20 October 2026.** This note records what was verified about the existing Stage 8 run. It does not replace [`results/summary/ragtruth_factorial_seed_v1/provenance.json`](../results/summary/ragtruth_factorial_seed_v1/provenance.json). That file is the run’s own record and was not rewritten. No model was retrained, and `python -m rcgate.factorial_seed` was not run again.

## Verification commit

The check started on branch `review/rcgate-handoff-v1` at `6d3ef709367d55a27a413477c624fc9f96a215ce` (`6d3ef70`), message `Record the RC-Gate integrity repairs, Stage 8 findings, and offline research studio.` At that moment the same commit was the tip of `origin/review/rcgate-handoff-v1`. Local `main` was `47090018414f657bca8e5a43e97663feba2e5a7d`. This note is documentation added after that check. It does not change the hashed fit sources, and it does not move `main`.

At the start of the check, `git status` showed no modifications to tracked files. `git ls-files -o --exclude-standard` listed 2,628 untracked files, all under `results/summary/`:

| Directory | Untracked files |
| --- | ---: |
| `ragtruth_factorial_seed_v1/` | 1,925 |
| `ragtruth_multi_seed_v1/` | 524 |
| `ragtruth_corrected_integrity_v1/` | 93 |
| `ragtruth_split_corrected_v1/` | 79 |
| `ragtruth_historical_freeze/` | 7 |

`git status --porcelain` collapses those into 732 lines. They are local experiment artifacts. They were left in place.

## What the run itself recorded

`provenance.json` records:

| Field | Recorded value |
| --- | --- |
| `git.head` | `47090018414f657bca8e5a43e97663feba2e5a7d` |
| `git.dirty` | `true` |
| `git.n_porcelain_lines` | 32 |
| `head_alone_reproduces_this_experiment` | `false` |
| `fit_table` | `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` |
| `fit_table_sha256` | `082e524ccc3c062cfcec423b00e970f5fa846eefa2646c3d0c4139cd73954245` |
| `config_sha256` | `66e1c6f1d02b770f2b9465abc20f1b945b6014dda05a96048eabe9b2c32d3d63` |
| Split seeds | 0 through 19 |
| Model seeds | 0, 1, 2 |
| Variants | A0 through A7 |
| A8 | skipped; no judge votes |
| Fits | 480 |
| Bootstrap | seed is the split seed; 1,000 requested resamples; the bootstrap fraction is not a p-value |
| `numpy` | `2.5.3` |
| `command` | `python -m rcgate.factorial_seed` |

The stored command has no extra flags. With no flags, `rcgate.factorial_seed.main` calls `evaluate(fit=True)`. `--score-only` is a separate rescore path, and this check did not use it. The reason string in provenance says the working tree was dirty, the Stage 8 source edits were uncommitted, and checkout of that HEAD alone does not reproduce the run. That statement describes `4709001`. It remains true for `main`.

## Source identity

The twelve `source_hashes` in `provenance.json` were recomputed from the files in commit `6d3ef70`. Each one matches:

- `rcgate/pipeline.py`
- `rcgate/data/splits.py`
- `rcgate/models/rcgate.py`
- `rcgate/models/baselines.py`
- `rcgate/models/gate.py`
- `rcgate/models/experts.py`
- `rcgate/models/meta.py`
- `rcgate/metrics.py`
- `rcgate/utils.py`
- `rcgate/stats_protocol.py`
- `rcgate/factorial_seed.py`
- `configs/ragtruth_factorial_seed_v1.yaml`

Those paths are `SOURCE_FILES` in `rcgate/factorial_seed.py`. The config hash equals the hash of `configs/ragtruth_factorial_seed_v1.yaml`. Commit `6d3ef70` therefore contains the hashed fit implementation that provenance recorded.

The same provenance porcelain list also names files that were dirty at run time and were **not** given a hash. They are present in `6d3ef70`, and byte-identity with the process that wrote the report is not proven for them:

- `rcgate/claims/dealias.py`
- `rcgate/data/__init__.py`
- `rcgate/data/build.py`
- `rcgate/data/ragtruth.py`
- `rcgate/evaluate.py`
- `rcgate/multi_seed.py`
- `rcgate/split_sensitivity.py`
- `configs/ragtruth_corrected_integrity_v1.yaml`
- `configs/ragtruth_multi_seed_v1.yaml`
- `configs/ragtruth_split_corrected_v1.yaml`
- `tests/test_dealias.py`
- `tests/test_factorial_seed.py`
- `tests/test_group_stratified_split.py`
- `tests/test_multi_seed.py`
- `tests/test_ragtruth.py`
- `tests/test_stats_protocol.py`
- `tests/test_synthetic.py`

`rcgate/factorial_seed.py` does not import `rcgate/evaluate.py`. The de-alias and RAGTruth builders affect how the signal table is produced. The table file’s SHA-256 matches the recorded hash, and the table was not rebuilt. The studio, frontend, fixtures, and later docs are absent from that porcelain list, so they were added after the snapshot. They are in the same commit as the hashed sources. The hash match shows those later edits did not change the twelve hashed files.

## Inputs, seeds, and artifacts checked on disk

The local seed-0 table matches `fit_table_sha256`. It has 800 rows, 134 question ids, and 57 positive labels. Every `claim_id` ends in `#0`. `task_type` is QA on 402 rows and Summary on 398. `src_quality` is 0.9 on every row. `arithmetic_verdict` is `unverifiable` on every row.

`split_assignments.parquet` has 2,680 rows (20 seeds × 134 questions). Each question appears in exactly one of `train`, `val`, and `test` within a seed. All 20 assignment SHA-256 values match `provenance.json`. Recomputing `group_stratified_split` from the local table, without fitting, reproduces those twenty hashes. `seed_metrics.csv` has 480 rows. Every row has 15 test positives and 28 test questions. The same positive and question counts are in `report.json` under `splits`.

`seed_metrics.csv`, `report.json`, and the “Distributions over the 60 cells” table in `report.md` agree on the cell-level AUROC summaries. Rounded with the report’s four-decimal formatter, the means are 0.6280 (A0), 0.6839 (A4), and 0.5717 (A7). A7’s sample standard deviation across the 60 cells is 0.1247 (minimum 0.3072, maximum 0.7983). The mean paired A7−A0 delta is −0.0563. The mean paired A7−A4 delta is −0.1122. A0 and A4 AUROC do not change across the three model seeds inside a split. These figures were recomputed from the CSV and compared with the JSON and Markdown. They are the recorded grid, not a new experiment.

All 480 cell checkpoints `A*_split*_model*/model.joblib` are on this machine. Each file’s SHA-256 matches `checkpoint_sha256` in `seed_metrics.csv`. Each cell also has `metrics.json`, `predictions.parquet`, and `config.yaml`. The combined `predictions.parquet` holds validation and test scores only (74,592 validation rows and 80,064 test rows). Its test-row counts match column `n` in `seed_metrics.csv` for all 480 cells, and its question ids stay inside the recorded partition. Training rows are not in that file. `checkpoint_repro/A4_split6_model6/` is an extra local diagnostic of the Stage 7 threshold rounding. It is not one of the 480 cells.

`data/raw/ragtruth/response.jsonl` has 17,790 lines and SHA-256 `e4c2e4ac24fff676d8984cc61c35d791612fadc58015335d97dd632375e18073`. `source_info.jsonl` has 2,965 lines and SHA-256 `0dffc26ea9f3c1c3d7c7e8336b56ef1646e3cec876edffcca3c9c624d12d578b`. Those digests are the pins in `rcgate/data/ragtruth.py`. Task counts in `source_info.jsonl` are QA 989, Summary 943, and Data2txt 1,033. Each of the six roster models has 2,965 responses. The response `split` field is train 15,090 and test 2,700.

This check used `.venv` (Python 3.12.14). That environment’s NumPy version string is `2.5.3`, which matches `provenance.json`. The provenance file does not record a Python version, torch, scikit-learn, pandas, or pyarrow version. Matching NumPy does not identify the rest of the original process.

## What a later run needs

Record browsing (`python -m rcgate.studio`) reads:

- `data/raw/ragtruth/response.jsonl`
- `data/raw/ragtruth/source_info.jsonl`
- `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet`

Scoring a sentence already present in that table also needs:

- `results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib`

That file is one cell (split seed 0, model seed 0). A probability from it is a demo inference. Scoring a sentence that is not in the table also needs local weight snapshots under `.cache/models/hub/`, each containing a `.safetensors` or `.bin` file:

- `models--cross-encoder--nli-deberta-v3-small`
- `models--sentence-transformers--all-MiniLM-L6-v2`

`data/raw/`, `data/signal_tables/`, and `.cache/` are gitignored. The cell checkpoint is untracked. None of those files are in commit `6d3ef70`. `tests/test_stage8_record.py` skips the corresponding checks when a local file is absent, and it fails if a partial archive disagrees with the tracked summary.

## Artifact roles

Tracked in `6d3ef70`, and enough to read the recorded Stage 8 numbers: `report.md`, `report.json`, `provenance.json`, `seed_metrics.csv`, and `paired_deltas.csv`. The same commit tracks the Stage 4–7 report and provenance files already listed in the experiment index.

Needed on disk to rerun or to inspect a fitted cell, and currently untracked: the 480 cell directories, `split_assignments.parquet`, and the combined `predictions.parquet`. Per-cell `config.yaml` repeats the resolved config. `checkpoint_repro/` and `results/summary/ragtruth_corrected_integrity_v1/diagnostics/` are supporting outputs from earlier checks. The historical-freeze parquets and the Stage 4–7 checkpoints are the same kind of local archive. Deleting them is not part of this note.

## Limits

Commit `6d3ef70` contains the hashed fit sources and the tracked summary. It does not, by itself, reproduce the 480 fits. The original provenance already says `4709001` alone does not. The unhashed dirty-tree files have no stored run-time digest. The signal table was not rebuilt. The factorial command was not rerun. Checkpoint hashes confirm that the files named in `seed_metrics.csv` are the files on disk. They do not refit those models. Environment identity beyond the recorded NumPy string was not established.

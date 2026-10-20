<div align="center">

# RC-Gate

**A metadata-conditioned two-expert prototype for sentence-level hallucination detection.**

[![Python](https://img.shields.io/badge/python-3.11%2B-3670A0?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Status](https://img.shields.io/badge/status-research%20prototype-9B59B6?style=flat-square)]()
[![License](https://img.shields.io/badge/license-TBD-lightgrey?style=flat-square)]()

</div>

The authoritative account is [`docs/RC-Gate_Final_Research_Report_v1.md`](docs/RC-Gate_Final_Research_Report_v1.md). The map of which result file is current is [`docs/RC-Gate_Experiment_Index.md`](docs/RC-Gate_Experiment_Index.md). Publication readiness for a conference or journal has not been established. The proposal, the user guide, and the initial paper draft are historical documents. They are not the experimental record.

## What the prototype does

For each sentence of a generated answer, RC-Gate scores two families of clues.

- **Cross-model:** agreement, contradiction, and semantic distance against the other models’ answers to the same source.
- **Evidence:** NLI support and conflict against the supplied document, plus a source-quality flag.

A small gate sees only the sentence’s claim type and the identity of the model that wrote it. It does not see the signal values. Two linear experts produce one logit each. The gate’s weights scale those logits, and a linear head maps the pair to a probability that the sentence is hallucinated. On the RAGTruth roster the gate has 233 trainable parameters. The weights are returned with the probability, so the routing decision can be inspected. Inspectability is not a validated scientific explanation of why a family is reliable.

The comparison that matters is A7 (the full gate) against A4, a gradient-boosting model that receives the same six signals and the same claim-type and generator metadata without the gate constraint. A8, majority vote over judge models, was never run: the signal tables have no judge votes.

## What the experiments support

The principal real-data analysis is Stage 8: 20 question-grouped splits crossed with 3 model initialisations, all on one corrected 800-sentence RAGTruth slice (134 questions, 57 hallucinated sentences). Mean test AUROC over those 60 fits is **0.6280** for flat logistic regression (A0), **0.6839** for A4, and **0.5717** for A7. The mean paired difference A7 minus A4 is **−0.1122**. A7’s 60 AUROC values have sample standard deviation **0.1247** (range 0.3072 to 0.7983). That standard deviation describes repeated fits on one question pool. It is not a confidence interval, and the 20 splits are not 20 datasets.

On synthetic tables with a reliability pattern written into the generator, the gate can recover that pattern. That recovery is a mechanism check. It is not independent evidence about real generators. A4 still ranks higher than A7 on the synthetic pooled mean.

A read-only audit of the official RAGTruth QA release found that the proposed generator-by-type reliability surface is not adequately identified under the stated support rule. No full-scale evaluation was performed. `src_quality` is constant on the evaluated slice, and the arithmetic checker does not fire there.

The original three-seed summary is retired. It remains at [`results/summary/ragtruth.md`](results/summary/ragtruth.md) as a historical file. Its paired comparison stored a bootstrap fraction under a name that reads like a hypothesis test, and its “95% CI” column prints the mean AUROC. Neither figure is a current estimate.

## Evidence

| Record | What it holds |
| --- | --- |
| [Final research report](docs/RC-Gate_Final_Research_Report_v1.md) | Architecture, hypotheses, protocols, Stage 8 results, limitations |
| [Experiment index](docs/RC-Gate_Experiment_Index.md) | Which file is current, which files are historical, and where Stages 9 and 10 are recorded |
| [`results/summary/ragtruth_factorial_seed_v1/`](results/summary/ragtruth_factorial_seed_v1/) | Stage 8, the principal repeated-fit analysis |
| [`results/summary/ragtruth_multi_seed_v1/`](results/summary/ragtruth_multi_seed_v1/) | Stage 7, 20 splits with the model seed tied to the split seed |
| [`results/summary/ragtruth_split_corrected_v1/`](results/summary/ragtruth_split_corrected_v1/) | Stage 6, group-stratified split, three overlapping tables |
| [`results/summary/ragtruth_corrected_stats_v1/`](results/summary/ragtruth_corrected_stats_v1/) | Stage 5, question-grouped intervals on the Stage 4 checkpoints |
| [`results/summary/ragtruth_corrected_integrity_v1/`](results/summary/ragtruth_corrected_integrity_v1/) | Stage 4, sentence-alignment and antecedent corrections |
| [`results/summary/synthetic.md`](results/summary/synthetic.md) | Planted synthetic mechanism check |

Protocols differ. The report does not pool them into one table.

## Quickstart

The primary presentation is the research studio: a local search over the RAGTruth files on disk, with optional scoring from a saved checkpoint. The Streamlit page remains a separate single-answer scorer. Neither one generates model answers or retrieves live sources.

```bash
pip install -e ".[dev,demo]"

# Recorded demo fixtures (no training; writes demo_fixtures/scenarios.json):
python -m rcgate.demo.fixtures

# Research studio. Run the API and the page in two shells:
#   python -m rcgate.studio
#   cd frontend && npm install && npm test && npm run dev

# Or both together:
./scripts/dev_studio.sh

# Single-answer scorer (loads a saved checkpoint; never trains):
streamlit run rcgate/demo/app.py

# Run the whole build order, M0 -> M7, in sequence:
make stages

# Or one stage at a time:
make m0        # scaffold check: pytest + ruff + CLIs answer
make m1        # synthetic signal table with planted structure
make m2        # baselines A0-A4
make m3        # RC-Gate + ablations A3/A5/A6
make m4        # full evaluation (bootstrap CIs, leave-one-generator-out, heatmap)
make m5        # real RAGTruth signal table (cached NLI/embedding extractors)
make m6        # full evaluation on RAGTruth
make m7        # glass-box demo, headless verification
```

The `make` targets reproduce the milestone pipeline. They do not replace the Stage 8 protocol, and they do not establish the headline results above. Signal extraction is cached. NLI and embeddings run on CPU.

Install the page from `frontend/` (`npm install`). That creates `frontend/node_modules/`. A `node_modules/` directory at the repository root, if one is present, is an accidental install. The committed `.gitignore` rule `node_modules/` ignores it at any depth, including `frontend/node_modules/` and `node_modules/.vitest/.vitest-secret-token`. Those directories stay on disk and are not tracked.

## Local files the Research Studio needs

A clean clone does not contain these paths, and this repository does not download them. The startup commands above are sufficient only after the files are already on disk.

Record browsing, precomputed scoring, and on-demand scoring need different local files. `python -m rcgate.studio` reads three files before it can browse the library (`rcgate/studio/catalog.py`):

- `data/raw/ragtruth/response.jsonl`
- `data/raw/ragtruth/source_info.jsonl`
- `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet`

Without those three, the library API does not start. The how-it-works, research, and glossary pages are static and do not need the API. `data/raw/` and `data/signal_tables/` are gitignored, so a clone does not contain the JSONL files or the signal table.

Scoring a sentence whose features are already in that seed-0 table also needs:

- `results/summary/ragtruth_factorial_seed_v1/A7_split0_model0/model.joblib`

That checkpoint is one Stage 8 cell (split seed 0, model seed 0), not the Stage 8 mean. It is untracked. Those stored rows do not need the NLI or embedding weights.

Scoring any other sentence calculates features on this machine. That path needs the same checkpoint plus local weight snapshots under `.cache/models/hub/`:

- `models--cross-encoder--nli-deberta-v3-small`
- `models--sentence-transformers--all-MiniLM-L6-v2`

Each snapshot must contain a `.safetensors` or `.bin` file. `.cache/` is gitignored. The weight files are third-party snapshots and are not part of this repository. If either snapshot is missing, the API leaves that sentence unscored and does not invent features. Stored answers can still be read. `python -m rcgate.demo.fixtures` needs the same three library files and the checkpoint in order to rebuild `demo_fixtures/scenarios.json`.

What commit `6d3ef70` does and does not reproduce is recorded in [`docs/RC-Gate_Stage8_Reproduction_Note.md`](docs/RC-Gate_Stage8_Reproduction_Note.md).

## Repository layout

```text
rcgate/               # package: data/, claims/, signals/, models/, demo/, train/evaluate/explain CLIs
frontend/             # verification studio (React). Primary walkthrough
demo_fixtures/        # recorded demo library. Not a benchmark result
configs/              # one YAML per benchmark + planted probabilities + budget
docs/adr/             # architecture decision records
docs/postmortems/rcgate/ # failure stories from the milestone build
docs/RC-Gate_Final_Research_Report_v1.md
docs/RC-Gate_Experiment_Index.md
tests/                # offline tests; the network is never touched
results/summary/      # summary tables and the Stage 4–8 audit trail
DECISIONS.md          # milestone judgment log (historical; see the final report)
```

## Documentation

| Artifact | What it holds |
| --- | --- |
| [Final research report](docs/RC-Gate_Final_Research_Report_v1.md) | current scientific account |
| [Experiment index](docs/RC-Gate_Experiment_Index.md) | which result file to cite |
| [Stage 8 reproduction note](docs/RC-Gate_Stage8_Reproduction_Note.md) | what was verified about the Stage 8 commit, inputs, and local artifacts |
| [DECISIONS.md](DECISIONS.md) | milestone log; earlier numbers there are historical |
| [docs/adr/](docs/adr/) | metadata-only gate, logit fusion, four claim types, span-overlap labelling, blocked benchmarks, compute-cache split |
| [docs/postmortems/rcgate/](docs/postmortems/rcgate/) | stale-table reuse, the original M6 negative, an inverted explanation line |

---

_[pd241008](https://github.com/pd241008) · [ct-os-dev-portfolio.vercel.app](https://ct-os-dev-portfolio.vercel.app)_

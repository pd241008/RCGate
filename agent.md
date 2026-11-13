# RC-Gate build order (agent.md)

This file documents the M0–M7 milestones that `make stages` drives, and the output
contract those milestones must honour. It is the single source of truth for what a
"finished" stage produces.

## Stage targets

| target | what it runs | milestone |
|--------|--------------|-----------|
| `m0` | `pytest`, `ruff check`, `python -m rcgate.train --help` | scaffold check |
| `m1` | `python -m rcgate.data.build --config synthetic` | synthetic signal table (planted structure) |
| `m2` | `python -m rcgate.train --config synthetic --variant A0..A4 --seeds 5` | baselines A0–A4 |
| `m3` | `python -m rcgate.train --config synthetic --variant A3,A5,A6,A7 --seeds 5` | RC-Gate + ablations |
| `m4` | `python -m rcgate.evaluate --config synthetic --bootstrap 1000` | full evaluation (CIs, LOGO, heatmap) |
| `m5` | `python -m rcgate.data.build --config ragtruth` | RAGTruth signal table (cached extractors) |
| `m6` | `python -m rcgate.evaluate --config ragtruth --bootstrap 1000` | full evaluation on RAGTruth |
| `m7` | `m6`, then `python -m rcgate.demo.app --config ragtruth ...` | glass-box demo |

`make stages` runs m0 → m7 in order. Every stage is idempotent and cache-aware;
data tables, caches and results are gitignored and regenerate from committed code +
configs.

## Output contract (LaTeX-ready)

M4 (and M6) must produce everything the paper needs from a single command:

1. **Tables** — `results/tables/<tag>.tex`, one LaTeX table per file, each
   `\input{}`-able into the manuscript. Required tables:
   - main results: AUROC, F1 and ECE for A0–A7, with 95% CI and mean ± std over seeds
   - same table split by claim type
   - ablation table (A3, A4, A5, A6, A7)
   - leave-one-generator-out results
   - gate-weight table (claim type × generator)
   - cost & latency table (per-claim latency, API calls, total cost)
2. **Figures** — `results/figures/<tag>_gate_weights.pdf`, vector PDF so they stay
   sharp (gate-weight heatmap; raster PNG may also be emitted but the PDF is the
   archival form).
3. **Run records** — every run stores, next to its results, its resolved config, the
   full seed list, and the git hash of HEAD, so every number in the paper can be
   traced to a run. Per-run records live in
   `results/summary/<tag>/<variant>_seed<seed>/{config.yaml,metrics.json}` (config +
   git hash already written by `rcgate.pipeline.persist`); the aggregate
   `results/summary/<tag>.json` additionally records the seed list and git hash.

Constraint C8 still applies: synthetic-table output is labelled synthetic and never
mixed with real-benchmark numbers.

# Prompt 10 — Statistical analysis and publication figures

Generate analysis from saved predictions and metrics only. Do not rerun training or change the metric because a figure looks weak. Every figure must be reproducible from a script and raw predictions.

## Statistical requirements

- Cluster bootstrap/pair resampling at source/query level, keeping all sentences and generator responses for a group together.
- Paired confidence intervals for differences between grounding-only and grounding-plus-peer-agreement on identical test records.
- State bootstrap count, random seeds, estimand, grouping unit and treatment of missing outputs.
- If several models, tasks and metrics are compared, identify the primary comparison and clearly label multiple secondary comparisons; apply a reasonable multiplicity policy or mark exploratory analyses exploratory.
- Report effect sizes and uncertainty, not only p-values. Do not say “significant” without the stated test and result.

## Publication-grade figures

Create vector PDF/SVG and high-resolution PNG where relevant, with accessible fonts, readable labels and captions. Required figure candidates:
1. Method/data flow: one target sentence, its retrieved context, peer responses, grounding features, agreement features, target label and evaluation splits.
2. Signal-family ablation plot with confidence intervals.
3. Performance by held-out generator.
4. Performance by task.
5. Incremental value against peer-panel size and measured latency/call burden.
6. Calibration or risk-coverage plot only if justified.
7. Error taxonomy/feature interaction analysis if sufficiently supported.

Use consistent data and uncertainty intervals. Do not create decorative charts or manually edit plotted values. All captions must state dataset, split, metric, error bars and sample/group counts. Every visual insight in the paper must map to actual code and stored results.

## Tables

Generate camera-ready result tables as CSV/LaTeX: dataset counts; prior-art comparison; primary results; per-generator/task results; ablations; costs; reproducibility details. Preserve enough decimal precision and include CIs. Explicitly mark unavailable/unrun baselines, including A8 if legacy variants are described.

## Deliverables

Store plotting code under the new package, figures under `results/rcgate_conditional_consensus/figures/`, tables under `.../tables/`, and create `FIGURE_AND_TABLE_INDEX.md`. Verify vector and raster outputs can be opened and captions have no invented claims. Wait for Prompt 11.

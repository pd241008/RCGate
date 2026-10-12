# Statistical issues left untouched

This sensitivity run uses the current evaluation procedure so the data-pipeline fixes are not mixed with a change of estimator. None of the items below were fixed.

## Claim-level bootstrap

`bootstrap_auroc_ci` in `rcgate/metrics.py` resamples claims (rows) with replacement. Claims that share a `question_id` are not independent: the split is grouped by question, and each source contributes one sentence from each generator. The interval ignores that clustering. The function's own docstring says the interval is, if anything, too narrow.

## Grouped bootstrap is not used

`bootstrap_auroc_ci_grouped` resamples whole questions. `score_run`, `_deltas`, and `logo_runs` never call it. The reported intervals are the claim-level ones.

## Per-seed intervals are averaged across seeds

`aggregate` takes the mean of each seed's `auroc_ci_lo` and `auroc_ci_hi`, producing `auroc_ci_lo_mean` and `auroc_ci_hi_mean`. An average of interval endpoints is not a confidence interval for the mean AUROC across seeds. The across-seed standard deviation is a separate column and is the only seed-level dispersion the report computes.

## Paired bootstrap uses 500 resamples, not 1000

`eval.n_bootstrap` is 1000, and the report header says 1000 resamples per slice per seed. `_deltas` calls `paired_bootstrap_delta` with `n_resamples=min(n_bootstrap, 500)`. The H2 comparison is therefore a 500-resample bootstrap. Those per-seed probabilities are then averaged across seeds.

## `p_gt_0` is not a p-value

`p_gt_0` is the fraction of bootstrap replicates in which A7's AUROC exceeds the baseline (`delta > 0`). Ties are not counted as favouring A7. The report text describes it as "the bootstrap fraction of resamples favouring A7." The column name reads like a p-value. Averaging that fraction across three seeds is not a combined test.

## CI rendering

`markdown_report` looks up `auroc_ci_lo` and `auroc_ci_hi` on the aggregated frame. `aggregate` has already renamed those columns to `auroc_ci_lo_mean` and `auroc_ci_hi_mean`. The lookup misses, so the "AUROC (95% CI)" column prints only the point estimate. The intervals are in `report.json`. The same lookup miss affects the per-generator table.

A second gap: `CI_SLICES` lists `"claim_type"` and `"generator_id"`, but the slice names are `claim_type=0` and `generator_id=0`. The membership test is exact, so those slices never receive a bootstrap interval. Their CI columns in the JSON are null. That is why the claim-type and generator tables have no interval to render.

## What this run therefore does and does not support

The corrected point estimates are comparable to the historical ones because both used this procedure. Neither set of intervals should be read as a cluster-robust confidence interval for the mean across seeds, and the markdown tables still omit the intervals that were computed.

# RC-Gate Stage 5 statistical repair — corrected RAGTruth

Inference in this file uses question-grouped percentile bootstrap intervals.
The sample standard deviation across seeds is not a confidence interval.
The mean of per-seed interval endpoints is reported only as a historical diagnostic.
No classical p-value is reported.

## Protocol

- group: `question_id` (RAGTruth source_id. The frozen tables contain one claim from each available generator per source, about six claims per question.)
- within-seed interval: within-seed 95% question-grouped percentile bootstrap interval
- resamples requested for every Stage 5 interval: 1000
- across seeds: sample standard deviation across seeds (ddof=1); not a confidence interval
- paired delta: per-seed 95% paired question-grouped percentile bootstrap interval for delta AUROC
- bootstrap fraction: bootstrap fraction of resamples with delta > 0; not a p-value
- formal p-value: not computed; three seeds and 27 test questions do not support one here
- point estimate: unweighted mean of the three seed-level statistics after 4-decimal rounding
- models: Stage 4 checkpoints reloaded; no refit
- thresholds: Stage 4 validation-tuned thresholds reloaded; not retuned
- split: unchanged grouped_split by question_id; stratify flag left untouched

## Point estimates

Means match Stage 4 because the checkpoints, labels, splits, and thresholds are unchanged.
The sd column is dispersion across the three seeds.

| variant | mean AUROC (point estimate) | sd of AUROC across seeds (not a confidence interval) | mean F1 (point estimate) | sd of F1 across seeds (not a confidence interval) | mean precision (point estimate) | sd of precision across seeds (not a confidence interval) | mean recall (point estimate) | sd of recall across seeds (not a confidence interval) | mean ECE (point estimate) | sd of ECE across seeds (not a confidence interval) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 0.6669 | 0.0627 | 0.2218 | 0.0152 | 0.1291 | 0.0074 | 0.8346 | 0.2374 | 0.0509 | 0.0110 |
| A1 | 0.7021 | 0.0757 | 0.1965 | 0.0686 | 0.1211 | 0.0315 | 0.6481 | 0.4027 | 0.0478 | 0.0045 |
| A2 | 0.5634 | 0.0672 | 0.1679 | 0.1069 | 0.0987 | 0.0543 | 0.6875 | 0.5413 | 0.0421 | 0.0139 |
| A3 | 0.6210 | 0.0832 | 0.1958 | 0.0542 | 0.1183 | 0.0258 | 0.6716 | 0.3836 | 0.0379 | 0.0073 |
| A4 | 0.7062 | 0.1061 | 0.2511 | 0.0978 | 0.2395 | 0.1113 | 0.2676 | 0.0780 | 0.1048 | 0.0056 |
| A5 | 0.6983 | 0.0107 | 0.1876 | 0.0479 | 0.1274 | 0.0190 | 0.3919 | 0.2005 | 0.2099 | 0.2837 |
| A6 | 0.5486 | 0.0968 | 0.1749 | 0.0065 | 0.1198 | 0.0406 | 0.5936 | 0.3512 | 0.1818 | 0.0848 |
| A7 | 0.6377 | 0.0997 | 0.2090 | 0.0466 | 0.1274 | 0.0300 | 0.6832 | 0.2864 | 0.2439 | 0.1765 |

## Per-seed AUROC intervals

Each bracket is that seed's own interval. Endpoints are not averaged.

| variant | seed | n claims (point count) | n questions (bootstrap groups) | n positive claims | AUROC (point estimate) | within-seed 95% question-grouped percentile bootstrap interval | resamples requested | resamples finite | F1 (point estimate) | precision (point estimate) | recall (point estimate) | ECE (point estimate) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 0 | 162 | 27 | 17 | 0.7197 | [0.6139, 0.8163] | 1000 | 1000 | 0.2388 | 0.1368 | 0.9412 | 0.0426 |
| A0 | 1 | 162 | 27 | 16 | 0.5976 | [0.4267, 0.7523] | 1000 | 999 | 0.2093 | 0.1286 | 0.5625 | 0.0634 |
| A0 | 2 | 158 | 27 | 15 | 0.6834 | [0.4882, 0.8002] | 1000 | 1000 | 0.2174 | 0.1220 | 1.0000 | 0.0467 |
| A1 | 0 | 162 | 27 | 17 | 0.7164 | [0.5907, 0.8382] | 1000 | 1000 | 0.2617 | 0.1556 | 0.8235 | 0.0427 |
| A1 | 1 | 162 | 27 | 16 | 0.6203 | [0.4733, 0.7550] | 1000 | 999 | 0.1250 | 0.0938 | 0.1875 | 0.0501 |
| A1 | 2 | 158 | 27 | 15 | 0.7697 | [0.6110, 0.8777] | 1000 | 1000 | 0.2029 | 0.1138 | 0.9333 | 0.0507 |
| A2 | 0 | 162 | 27 | 17 | 0.6304 | [0.4888, 0.7647] | 1000 | 1000 | 0.2519 | 0.1441 | 1.0000 | 0.0406 |
| A2 | 1 | 162 | 27 | 16 | 0.4961 | [0.3799, 0.6275] | 1000 | 999 | 0.0476 | 0.0385 | 0.0625 | 0.0567 |
| A2 | 2 | 158 | 27 | 15 | 0.5636 | [0.3194, 0.7932] | 1000 | 1000 | 0.2041 | 0.1136 | 1.0000 | 0.0291 |
| A3 | 0 | 162 | 27 | 17 | 0.7164 | [0.5907, 0.8382] | 1000 | 1000 | 0.2453 | 0.1461 | 0.7647 | 0.0426 |
| A3 | 1 | 162 | 27 | 16 | 0.5830 | [0.4226, 0.7447] | 1000 | 999 | 0.1379 | 0.0952 | 0.2500 | 0.0416 |
| A3 | 2 | 158 | 27 | 15 | 0.5636 | [0.3194, 0.7932] | 1000 | 1000 | 0.2041 | 0.1136 | 1.0000 | 0.0294 |
| A4 | 0 | 162 | 27 | 17 | 0.7826 | [0.6396, 0.9120] | 1000 | 1000 | 0.3529 | 0.3529 | 0.3529 | 0.1050 |
| A4 | 1 | 162 | 27 | 16 | 0.7509 | [0.6283, 0.8717] | 1000 | 999 | 0.2424 | 0.2353 | 0.2500 | 0.0991 |
| A4 | 2 | 158 | 27 | 15 | 0.5851 | [0.3771, 0.7365] | 1000 | 1000 | 0.1579 | 0.1304 | 0.2000 | 0.1103 |
| A5 | 0 | 162 | 27 | 17 | 0.6876 | [0.5318, 0.8230] | 1000 | 1000 | 0.2381 | 0.1493 | 0.5882 | 0.5375 |
| A5 | 1 | 162 | 27 | 16 | 0.7089 | [0.5428, 0.8289] | 1000 | 999 | 0.1429 | 0.1154 | 0.1875 | 0.0497 |
| A5 | 2 | 158 | 27 | 15 | 0.6984 | [0.4965, 0.8464] | 1000 | 1000 | 0.1818 | 0.1176 | 0.4000 | 0.0425 |
| A6 | 0 | 162 | 27 | 17 | 0.4998 | [0.3546, 0.6992] | 1000 | 1000 | 0.1690 | 0.0960 | 0.7059 | 0.1710 |
| A6 | 1 | 162 | 27 | 16 | 0.4859 | [0.2281, 0.7177] | 1000 | 999 | 0.1739 | 0.0966 | 0.8750 | 0.1029 |
| A6 | 2 | 158 | 27 | 15 | 0.6601 | [0.4586, 0.8398] | 1000 | 1000 | 0.1818 | 0.1667 | 0.2000 | 0.2715 |
| A7 | 0 | 162 | 27 | 17 | 0.6933 | [0.6013, 0.7843] | 1000 | 1000 | 0.2581 | 0.1495 | 0.9412 | 0.3850 |
| A7 | 1 | 162 | 27 | 16 | 0.6973 | [0.4810, 0.8278] | 1000 | 999 | 0.2034 | 0.1395 | 0.3750 | 0.0460 |
| A7 | 2 | 158 | 27 | 15 | 0.5226 | [0.2770, 0.7682] | 1000 | 1000 | 0.1654 | 0.0932 | 0.7333 | 0.3007 |

## Paired comparisons

Delta is AUROC(A7) minus AUROC(baseline) on the same test claims.
The interval resamples question ids once per draw and scores both models on the drawn claims.
Stage 5 uses 1000 resamples. The historical paired procedure used 500.

| comparison | seed | delta AUROC (point estimate) | per-seed 95% paired question-grouped percentile bootstrap interval for delta AUROC | interval vs 0 | resamples requested | resamples finite | bootstrap fraction of resamples with delta > 0; not a p-value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A7 - A0 | 0 | -0.0264 | [-0.1039, 0.0565] | covers_0 | 1000 | 1000 | 0.2690 |
| A7 - A0 | 1 | 0.0997 | [-0.1835, 0.2863] | covers_0 | 1000 | 999 | 0.8138 |
| A7 - A0 | 2 | -0.1608 | [-0.4805, 0.2026] | covers_0 | 1000 | 1000 | 0.2510 |
| A7 - A1 | 0 | -0.0231 | [-0.1458, 0.0957] | covers_0 | 1000 | 1000 | 0.3490 |
| A7 - A1 | 1 | 0.0771 | [-0.1843, 0.2645] | covers_0 | 1000 | 999 | 0.7758 |
| A7 - A1 | 2 | -0.2471 | [-0.5023, -0.0046] | entirely_below_0 | 1000 | 1000 | 0.0190 |
| A7 - A2 | 0 | 0.0629 | [-0.0679, 0.2209] | covers_0 | 1000 | 1000 | 0.8120 |
| A7 - A2 | 1 | 0.2012 | [-0.1213, 0.3805] | covers_0 | 1000 | 999 | 0.9399 |
| A7 - A2 | 2 | -0.0410 | [-0.5083, 0.4467] | covers_0 | 1000 | 1000 | 0.4520 |
| A7 - A3 | 0 | -0.0231 | [-0.1458, 0.0957] | covers_0 | 1000 | 1000 | 0.3490 |
| A7 - A3 | 1 | 0.1143 | [-0.1843, 0.3198] | covers_0 | 1000 | 999 | 0.8398 |
| A7 - A3 | 2 | -0.0410 | [-0.5083, 0.4467] | covers_0 | 1000 | 1000 | 0.4520 |
| A7 - A4 | 0 | -0.0892 | [-0.2014, 0.0536] | covers_0 | 1000 | 1000 | 0.1070 |
| A7 - A4 | 1 | -0.0535 | [-0.2500, 0.0841] | covers_0 | 1000 | 999 | 0.2382 |
| A7 - A4 | 2 | -0.0625 | [-0.3930, 0.2744] | covers_0 | 1000 | 1000 | 0.4010 |
| A7 - A5 | 0 | 0.0057 | [-0.1630, 0.1892] | covers_0 | 1000 | 1000 | 0.5390 |
| A7 - A5 | 1 | -0.0116 | [-0.1286, 0.0645] | covers_0 | 1000 | 999 | 0.3994 |
| A7 - A5 | 2 | -0.1758 | [-0.5136, 0.1246] | covers_0 | 1000 | 1000 | 0.2280 |
| A7 - A6 | 0 | 0.1935 | [0.0187, 0.3433] | entirely_above_0 | 1000 | 1000 | 0.9860 |
| A7 - A6 | 1 | 0.2115 | [-0.0741, 0.4435] | covers_0 | 1000 | 999 | 0.9239 |
| A7 - A6 | 2 | -0.1375 | [-0.2425, 0.0114] | covers_0 | 1000 | 1000 | 0.0350 |

### Across-seed summary of paired deltas

| comparison | mean delta AUROC (point estimate) | sd of delta across seeds (not a confidence interval) | per-seed interval positions |
| --- | --- | --- | --- |
| A7 - A0 | -0.0292 | 0.1303 | covers_0, covers_0, covers_0 |
| A7 - A1 | -0.0644 | 0.1660 | covers_0, covers_0, entirely_below_0 |
| A7 - A2 | 0.0744 | 0.1215 | covers_0, covers_0, covers_0 |
| A7 - A3 | 0.0167 | 0.0850 | covers_0, covers_0, covers_0 |
| A7 - A4 | -0.0684 | 0.0186 | covers_0, covers_0, covers_0 |
| A7 - A5 | -0.0606 | 0.1002 | covers_0, covers_0, covers_0 |
| A7 - A6 | 0.0892 | 0.1965 | entirely_above_0, covers_0, covers_0 |

## Old versus new

Stage 4's markdown column headed `AUROC (95% CI)` displayed the mean AUROC.
The claim-level interval endpoints were averaged into `auroc_ci_lo_mean` and `auroc_ci_hi_mean` and were not printed. That nonstandard average is not a confidence interval.

| variant | mean AUROC, both stages (point estimate) | Stage 4 nonstandard mean of claim-level endpoints (not a confidence interval) | Stage 5 per-seed question-grouped intervals |
| --- | --- | --- | --- |
| A0 | 0.6669 | [0.5483, 0.7841] | seed 0 [0.6139, 0.8163]; seed 1 [0.4267, 0.7523]; seed 2 [0.4882, 0.8002] |
| A1 | 0.7021 | [0.5769, 0.8152] | seed 0 [0.5907, 0.8382]; seed 1 [0.4733, 0.7550]; seed 2 [0.6110, 0.8777] |
| A2 | 0.5634 | [0.4397, 0.6908] | seed 0 [0.4888, 0.7647]; seed 1 [0.3799, 0.6275]; seed 2 [0.3194, 0.7932] |
| A3 | 0.6210 | [0.4886, 0.7493] | seed 0 [0.5907, 0.8382]; seed 1 [0.4226, 0.7447]; seed 2 [0.3194, 0.7932] |
| A4 | 0.7062 | [0.5712, 0.8253] | seed 0 [0.6396, 0.9120]; seed 1 [0.6283, 0.8717]; seed 2 [0.3771, 0.7365] |
| A5 | 0.6983 | [0.5806, 0.8087] | seed 0 [0.5318, 0.8230]; seed 1 [0.5428, 0.8289]; seed 2 [0.4965, 0.8464] |
| A6 | 0.5486 | [0.3835, 0.7143] | seed 0 [0.3546, 0.6992]; seed 1 [0.2281, 0.7177]; seed 2 [0.4586, 0.8398] |
| A7 | 0.6377 | [0.5023, 0.7661] | seed 0 [0.6013, 0.7843]; seed 1 [0.4810, 0.8278]; seed 2 [0.2770, 0.7682] |

### Paired deltas, historical endpoint average versus Stage 5

| comparison | mean delta (point estimate) | Stage 4 nonstandard mean of 500-resample claim-level endpoints (not a confidence interval) | Stage 5 per-seed question-grouped intervals |
| --- | --- | --- | --- |
| A7 - A0 | -0.0292 | [-0.1868, 0.1325] | seed 0 [-0.1039, 0.0565]; seed 1 [-0.1835, 0.2863]; seed 2 [-0.4805, 0.2026] |
| A7 - A4 | -0.0684 | [-0.2341, 0.1127] | seed 0 [-0.2014, 0.0536]; seed 1 [-0.2500, 0.0841]; seed 2 [-0.3930, 0.2744] |

## Verdict

Statistical repair does not change the point estimates and does not give A7 an advantage.

- Mean AUROC stays 0.6377 for A7, 0.6669 for A0, and 0.7062 for A4. Across-seed standard deviations are 0.0997, 0.0627, and 0.1061. Those standard deviations are not confidence intervals.
- A4 remains ahead of A7 on the point estimate (0.7062 versus 0.6377). The three seed-level deltas A7−A4 are all negative (mean -0.0684, sd 0.0186).
- A7 remains unsupported as better than A0. The mean delta is -0.0292 (sd 0.1303).
- Paired A7−A0 interval positions: covers_0, covers_0, covers_0. Paired A7−A4 interval positions: covers_0, covers_0, covers_0. Intervals lying entirely above 0, which would be the within-seed sign of an A7 advantage: A7−A0 count 0; A7−A4 count 0.
- Stage 4 numbers that are now historical: the markdown cells under `AUROC (95% CI)` (they were mean AUROC), the averaged claim-level endpoint fields `auroc_ci_lo_mean` and `auroc_ci_hi_mean`, the paired intervals formed by averaging 500-resample claim-level endpoints, and the field `p_gt_0`. The leave-one-generator-out table is also historical: its interval column was misaligned, and those intervals used 200 claim-level resamples. `results/summary/ragtruth/` was not recomputed.

### Paper-safe paragraph

On the frozen corrected RAGTruth tables, with the Stage 4 checkpoints and thresholds reused and the question-grouped split left unchanged, mean test AUROC is 0.6377 for RC-Gate (A7), 0.6669 for the flat logistic baseline (A0), and 0.7062 for the metadata gradient-boosting control (A4). Within each seed, the uncertainty for AUROC and for paired AUROC differences is a 95% percentile bootstrap that resamples the 27 test `question_id` clusters, using 1000 requested resamples. Every such paired interval for A7−A0 and for A7−A4 covers 0. Across the three seeds, only the sample standard deviation is reported. These results do not support a claim that A7 improves on A0 or on A4. They do not support reading the Stage 4 bootstrap fraction as a p-value, or treating an average of per-seed interval endpoints as a confidence interval. They also do not support claims that would require a different split or more seeds; those were not changed.

### Limitations that remain

- Three seeds. The claim pools overlap heavily, so the seed standard deviation mixes split assignment and fitting variation. It is not a confidence interval for a shared mean.
- Each test split has 27 questions and 15 to 17 positive claims. The grouped intervals are wide, especially on seed 2.
- The interval is a percentile interval of the finite resamples. Some question draws were single-class and were left out of the quantile: A0 seed 1 kept 999 of 1000 resamples; A1 seed 1 kept 999 of 1000 resamples; A2 seed 1 kept 999 of 1000 resamples; A3 seed 1 kept 999 of 1000 resamples; A4 seed 1 kept 999 of 1000 resamples; A5 seed 1 kept 999 of 1000 resamples; A6 seed 1 kept 999 of 1000 resamples; A7 seed 1 kept 999 of 1000 resamples.
- No formal hypothesis test is reported.
- F1, precision, recall, and ECE are point estimates with an across-seed standard deviation only. They were not bootstrapped in Stage 4 either.
- `grouped_split(..., stratify=True)` still does not stratify. That is left for a later stage.
- Leave-one-generator-out was not refit.

## What this file does not claim

- The sd across three seeds is not a confidence interval.
- A bootstrap fraction is not a p-value.
- Averaging interval endpoints across seeds is not a confidence interval.
- The question-grouped interval is for one seed's test split, not for the mean across seeds.
- Split construction, the number of seeds, labels, signals, and model parameters were not changed.

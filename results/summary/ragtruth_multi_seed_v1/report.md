# RC-Gate Stage 7 — 20-seed group-stratified robustness

This file varies the split seed and nothing else. The group-stratified
splitter, the signal tables, the variants, the hyperparameters, and the
Stage 5 uncertainty procedure are unchanged. No earlier result directory
was rewritten. The seed distribution below is not a confidence interval.

## Protocol

- Split function: `group_stratified_split` in `rcgate/data/splits.py`.
- Split method key: `group_stratified`.
- Grouping field: `question_id` (RAGTruth source id). Whole groups move together.
- Stratum: the group's integer positive-claim count, the sum of `label`.
- Fractions: 0.6 train, 0.2 validation, 0.2 test, applied inside each stratum
  by `cut_counts` (`round(0.6 n)`, `round(0.2 n)`, remainder test).
- Seed: `numpy.random.default_rng(SeedSequence([seed, stratum]))` shuffles
  group ids that were sorted first. Strata do not share a random stream.
- Seeds: 0 through 19. The model seed equals the split seed, as in Stage 6.
- Fit table: `ragtruth_corrected_integrity_v1_s0.parquet` for every seed.
  The config path has no `{seed}` placeholder, so s3–s19 are not built.
- Companion tables s1 and s2 are hashed below and are not fit tables.
  Shared claims match s0 on labels, text, types, and the six signals.
  Stage 6 seed k used table sk, so Stage 7 seeds 1 and 2 are not copies
  of Stage 6 seeds 1 and 2. Stage 7 seed 0 is the same fit as Stage 6 seed 0.
- Variants A0–A7 refit. A8 skipped because the table has no judge votes.
- Thresholds: the existing validation quantile rule. Not chosen from test A7.
- Point metrics are the seed statistics already rounded to 4 decimals.
- Distribution: mean, median, sample SD (ddof=1), min, max, 25th percentile,
  75th percentile, interquartile range. `numpy.quantile` linear method.
  This distribution is not a confidence interval.
- Within-seed interval: 95% question-grouped percentile bootstrap, 1000 resamples.
- Paired interval: one question draw scores both models. The bootstrap
  fraction of positive deltas is not a p-value. No classical p-value is reported.

## Companion tables

- s0 vs s1: shared questions 133, only s0 ['12161'], only s1 ['12229'], shared-claim column differences 0.
- s0 vs s2: shared questions 132, only s0 ['11316', '12161'], only s2 ['11776', '12229'], shared-claim column differences 0.
- s1 vs s2: shared questions 133, only s1 ['11316'], only s2 ['11776'], shared-claim column differences 0.

Stage 6 test-question Jaccard against the Stage 7 test set at the same seed:

- seed 0: Jaccard 1.0000 (28 shared of 28 and 28).
- seed 1: Jaccard 0.4737 (18 shared of 28 and 28).
- seed 2: Jaccard 0.3023 (13 shared of 28 and 28).

Stage 6 seed-0 metrics reproduced on this path: True.

Point metrics are the fit-time `metrics.json` values. Reloaded checkpoints
matched those AUROCs. A reload that only changes a thresholded metric is a
score sitting on the stored threshold, not a second model.

Reloaded checkpoints with a thresholded-metric difference: 1.
- A4 seed 6: {"f1": {"reloaded": 0.2824, "fit": 0.2857}, "precision": {"reloaded": 0.1714, "fit": 0.1739}}.

## Split balance

Deviation is the partition positive rate minus the full-table positive rate.
Group counts follow from the stratum sizes, so they do not depend on the seed.
Claim counts can still move when a short group changes partition.

| seed | train groups | val groups | test groups | train positives | val positives | test positives | train claims | val claims | test claims | train rate dev | val rate dev | test rate dev | test positive groups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 1 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 2 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 3 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 4 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 5 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 6 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 7 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 8 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 9 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 10 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 11 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 12 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 | -0.0025 | -0.0120 | 0.0180 | 8 |
| 13 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 14 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 | -0.0025 | -0.0120 | 0.0180 | 8 |
| 15 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 | -0.0025 | -0.0136 | 0.0202 | 8 |
| 16 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 17 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |
| 18 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 | -0.0025 | -0.0120 | 0.0180 | 8 |
| 19 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 | -0.0019 | -0.0136 | 0.0180 | 8 |

## Distributions

Each row is 20 seed-level statistics. The SD is not a confidence interval.

| variant | metric | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | auroc | 0.6280 | 0.6278 | 0.0608 | 0.5046 | 0.7320 | 0.5980 | 0.6794 | 0.0815 |
| A0 | f1 | 0.1807 | 0.1872 | 0.0671 | 0.0000 | 0.2857 | 0.1650 | 0.2245 | 0.0595 |
| A0 | precision | 0.1156 | 0.1193 | 0.0449 | 0.0000 | 0.2222 | 0.1011 | 0.1362 | 0.0351 |
| A0 | recall | 0.4967 | 0.4667 | 0.2697 | 0.0000 | 1.0000 | 0.3333 | 0.6833 | 0.3500 |
| A0 | ece | 0.0347 | 0.0315 | 0.0110 | 0.0195 | 0.0621 | 0.0290 | 0.0409 | 0.0119 |
| A1 | auroc | 0.6280 | 0.6248 | 0.0469 | 0.5516 | 0.7181 | 0.5914 | 0.6608 | 0.0694 |
| A1 | f1 | 0.1811 | 0.1933 | 0.0469 | 0.0909 | 0.2581 | 0.1595 | 0.2074 | 0.0479 |
| A1 | precision | 0.1263 | 0.1163 | 0.0421 | 0.0741 | 0.2500 | 0.1053 | 0.1367 | 0.0313 |
| A1 | recall | 0.5167 | 0.4334 | 0.3133 | 0.0667 | 0.9333 | 0.2500 | 0.8000 | 0.5500 |
| A1 | ece | 0.0279 | 0.0282 | 0.0090 | 0.0114 | 0.0456 | 0.0211 | 0.0340 | 0.0130 |
| A2 | auroc | 0.5594 | 0.5657 | 0.1145 | 0.3203 | 0.7468 | 0.5087 | 0.6483 | 0.1397 |
| A2 | f1 | 0.1501 | 0.1709 | 0.0789 | 0.0000 | 0.3019 | 0.1053 | 0.2005 | 0.0952 |
| A2 | precision | 0.0944 | 0.1076 | 0.0497 | 0.0000 | 0.2105 | 0.0714 | 0.1250 | 0.0536 |
| A2 | recall | 0.4533 | 0.4333 | 0.3205 | 0.0000 | 1.0000 | 0.2000 | 0.7333 | 0.5333 |
| A2 | ece | 0.0358 | 0.0284 | 0.0172 | 0.0193 | 0.0805 | 0.0222 | 0.0463 | 0.0241 |
| A3 | auroc | 0.6113 | 0.6225 | 0.0991 | 0.3821 | 0.8022 | 0.5528 | 0.6689 | 0.1161 |
| A3 | f1 | 0.1661 | 0.1720 | 0.0724 | 0.0000 | 0.3171 | 0.1171 | 0.2014 | 0.0844 |
| A3 | precision | 0.1200 | 0.1132 | 0.0510 | 0.0000 | 0.2083 | 0.0948 | 0.1472 | 0.0524 |
| A3 | recall | 0.3700 | 0.3000 | 0.2591 | 0.0000 | 0.8667 | 0.2000 | 0.4834 | 0.2833 |
| A3 | ece | 0.0343 | 0.0318 | 0.0139 | 0.0186 | 0.0788 | 0.0257 | 0.0355 | 0.0097 |
| A4 | auroc | 0.6838 | 0.6856 | 0.0668 | 0.5669 | 0.8017 | 0.6355 | 0.7274 | 0.0919 |
| A4 | f1 | 0.1920 | 0.2041 | 0.0989 | 0.0000 | 0.3636 | 0.1135 | 0.2542 | 0.1407 |
| A4 | precision | 0.1919 | 0.1723 | 0.1066 | 0.0000 | 0.4000 | 0.1450 | 0.2625 | 0.1175 |
| A4 | recall | 0.3067 | 0.3000 | 0.2412 | 0.0000 | 0.8000 | 0.1167 | 0.4667 | 0.3500 |
| A4 | ece | 0.0957 | 0.0959 | 0.0108 | 0.0806 | 0.1235 | 0.0872 | 0.1016 | 0.0144 |
| A5 | auroc | 0.5627 | 0.5634 | 0.1020 | 0.3447 | 0.7226 | 0.5194 | 0.6167 | 0.0972 |
| A5 | f1 | 0.1415 | 0.1495 | 0.0637 | 0.0000 | 0.2273 | 0.1096 | 0.1780 | 0.0684 |
| A5 | precision | 0.1125 | 0.1043 | 0.0720 | 0.0000 | 0.3333 | 0.0706 | 0.1326 | 0.0620 |
| A5 | recall | 0.3400 | 0.2667 | 0.2709 | 0.0000 | 0.8667 | 0.1833 | 0.4834 | 0.3000 |
| A5 | ece | 0.2277 | 0.2234 | 0.1797 | 0.0105 | 0.5110 | 0.0519 | 0.3414 | 0.2895 |
| A6 | auroc | 0.5348 | 0.5282 | 0.0906 | 0.3207 | 0.7081 | 0.4751 | 0.5949 | 0.1197 |
| A6 | f1 | 0.1270 | 0.1159 | 0.0631 | 0.0339 | 0.2778 | 0.0905 | 0.1470 | 0.0565 |
| A6 | precision | 0.0938 | 0.0960 | 0.0456 | 0.0227 | 0.2381 | 0.0621 | 0.1053 | 0.0432 |
| A6 | recall | 0.2533 | 0.1667 | 0.1978 | 0.0667 | 0.7333 | 0.1333 | 0.3333 | 0.2000 |
| A6 | ece | 0.2030 | 0.1946 | 0.1481 | 0.0072 | 0.4773 | 0.0543 | 0.3283 | 0.2740 |
| A7 | auroc | 0.5982 | 0.6375 | 0.1427 | 0.2802 | 0.7906 | 0.5341 | 0.7006 | 0.1665 |
| A7 | f1 | 0.1516 | 0.1567 | 0.0954 | 0.0000 | 0.3200 | 0.0689 | 0.2235 | 0.1546 |
| A7 | precision | 0.1062 | 0.0934 | 0.0686 | 0.0000 | 0.2286 | 0.0539 | 0.1720 | 0.1181 |
| A7 | recall | 0.3367 | 0.2667 | 0.2653 | 0.0000 | 0.8000 | 0.1333 | 0.5500 | 0.4167 |
| A7 | ece | 0.1762 | 0.1400 | 0.1323 | 0.0138 | 0.3827 | 0.0563 | 0.2839 | 0.2275 |

### Seed-level AUROC

| seed | A0 | A1 | A2 | A3 | A4 | A5 | A6 | A7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.6959 | 0.6854 | 0.5952 | 0.6601 | 0.7407 | 0.6702 | 0.4941 | 0.6845 |
| 1 | 0.6743 | 0.7181 | 0.5691 | 0.7181 | 0.6685 | 0.6899 | 0.4765 | 0.4698 |
| 2 | 0.6606 | 0.6305 | 0.7468 | 0.8022 | 0.7669 | 0.6070 | 0.4675 | 0.3978 |
| 3 | 0.6279 | 0.5743 | 0.7024 | 0.7155 | 0.7098 | 0.6418 | 0.4540 | 0.2915 |
| 4 | 0.6792 | 0.6260 | 0.6792 | 0.7163 | 0.7239 | 0.7074 | 0.4711 | 0.7123 |
| 5 | 0.5763 | 0.6600 | 0.5195 | 0.6586 | 0.6322 | 0.5987 | 0.6371 | 0.6327 |
| 6 | 0.6018 | 0.5767 | 0.5025 | 0.5767 | 0.7168 | 0.5678 | 0.4877 | 0.5347 |
| 7 | 0.6819 | 0.6083 | 0.6479 | 0.6092 | 0.7948 | 0.5024 | 0.5808 | 0.7155 |
| 8 | 0.5869 | 0.5699 | 0.4680 | 0.5246 | 0.6026 | 0.6083 | 0.5573 | 0.6375 |
| 9 | 0.7320 | 0.6758 | 0.6658 | 0.6658 | 0.8017 | 0.3447 | 0.4610 | 0.7163 |
| 10 | 0.5338 | 0.6523 | 0.3730 | 0.5259 | 0.6366 | 0.5447 | 0.5420 | 0.2802 |
| 11 | 0.6063 | 0.5799 | 0.6497 | 0.6358 | 0.7378 | 0.7226 | 0.5383 | 0.7906 |
| 12 | 0.6096 | 0.6070 | 0.5381 | 0.5381 | 0.6261 | 0.4187 | 0.5015 | 0.5638 |
| 13 | 0.5046 | 0.6353 | 0.3203 | 0.4536 | 0.6841 | 0.4048 | 0.3207 | 0.5325 |
| 14 | 0.6898 | 0.6235 | 0.5725 | 0.6784 | 0.5752 | 0.5926 | 0.6453 | 0.6375 |
| 15 | 0.6277 | 0.6206 | 0.5624 | 0.5866 | 0.5669 | 0.5508 | 0.6398 | 0.6103 |
| 16 | 0.6802 | 0.6632 | 0.6427 | 0.6427 | 0.6871 | 0.5590 | 0.5181 | 0.7303 |
| 17 | 0.5373 | 0.5952 | 0.3717 | 0.3821 | 0.6584 | 0.5251 | 0.6549 | 0.6575 |
| 18 | 0.6523 | 0.7068 | 0.5107 | 0.5577 | 0.6915 | 0.4540 | 0.7081 | 0.6719 |
| 19 | 0.6017 | 0.5516 | 0.5499 | 0.5782 | 0.6553 | 0.5429 | 0.5394 | 0.6967 |

Seed-level F1, precision, recall, and ECE are in `seed_metrics.csv`.
Their distributions are in the table above.

## A7 minus A0

Delta is test AUROC(A7) minus test AUROC(A0) on the same claims.
The interval is the paired question-grouped percentile bootstrap.
A position of `entirely_above_0` favors A7. `entirely_below_0` favors A0.
`covers_0` favors neither. The bootstrap fraction is not a p-value.

|  | mean | median | sd | min | max |
| --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.0298 | 0.0042 | 0.1357 | -0.3364 | 0.1843 |

- Seeds with A7 above the baseline (point estimate): 10.
- Seeds with A7 below the baseline: 10.
- Seeds with equal AUROC: 0.
- Paired intervals entirely above 0 (favor A7): 1.
- Paired intervals entirely below 0 (favor the baseline): 3.
- Paired intervals that cover 0: 16.

| seed | delta | interval | position vs 0 | bootstrap frac delta > 0 (not a p-value) |
| --- | --- | --- | --- | --- |
| 0 | -0.0113 | [-0.1074, 0.1024] | covers_0 | 0.4220 |
| 1 | -0.2045 | [-0.4914, 0.0247] | covers_0 | 0.0460 |
| 2 | -0.2627 | [-0.4135, -0.0984] | entirely_below_0 | 0.0000 |
| 3 | -0.3364 | [-0.4771, -0.1644] | entirely_below_0 | 0.0010 |
| 4 | 0.0331 | [-0.1299, 0.2164] | covers_0 | 0.6770 |
| 5 | 0.0564 | [-0.0778, 0.1905] | covers_0 | 0.8100 |
| 6 | -0.0671 | [-0.2375, 0.1014] | covers_0 | 0.2230 |
| 7 | 0.0336 | [-0.2285, 0.2560] | covers_0 | 0.6130 |
| 8 | 0.0505 | [-0.1173, 0.2336] | covers_0 | 0.7250 |
| 9 | -0.0157 | [-0.2316, 0.1435] | covers_0 | 0.4710 |
| 10 | -0.2536 | [-0.4654, -0.0566] | entirely_below_0 | 0.0060 |
| 11 | 0.1843 | [0.0993, 0.2550] | entirely_above_0 | 0.9980 |
| 12 | -0.0458 | [-0.3375, 0.1593] | covers_0 | 0.3390 |
| 13 | 0.0279 | [-0.3252, 0.3923] | covers_0 | 0.5560 |
| 14 | -0.0523 | [-0.2087, 0.1038] | covers_0 | 0.2550 |
| 15 | -0.0174 | [-0.2824, 0.2175] | covers_0 | 0.4290 |
| 16 | 0.0501 | [-0.1459, 0.2094] | covers_0 | 0.7360 |
| 17 | 0.1203 | [-0.0985, 0.3478] | covers_0 | 0.8630 |
| 18 | 0.0196 | [-0.1589, 0.2024] | covers_0 | 0.5490 |
| 19 | 0.0950 | [-0.0535, 0.2837] | covers_0 | 0.8620 |

## A7 minus A4

|  | mean | median | sd | min | max |
| --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.0857 | -0.0379 | 0.1490 | -0.4183 | 0.0623 |

- Seeds with A7 above the baseline (point estimate): 7.
- Seeds with A7 below the baseline: 13.
- Seeds with equal AUROC: 0.
- Paired intervals entirely above 0 (favor A7): 0.
- Paired intervals entirely below 0 (favor the baseline): 4.
- Paired intervals that cover 0: 16.

| seed | delta | interval | position vs 0 | bootstrap frac delta > 0 (not a p-value) |
| --- | --- | --- | --- | --- |
| 0 | -0.0562 | [-0.1943, 0.0630] | covers_0 | 0.1830 |
| 1 | -0.1987 | [-0.4931, 0.0853] | covers_0 | 0.0730 |
| 2 | -0.3691 | [-0.5406, -0.1980] | entirely_below_0 | 0.0000 |
| 3 | -0.4183 | [-0.5652, -0.2018] | entirely_below_0 | 0.0000 |
| 4 | -0.0116 | [-0.2329, 0.1941] | covers_0 | 0.4500 |
| 5 | 0.0004 | [-0.1483, 0.2319] | covers_0 | 0.4910 |
| 6 | -0.1821 | [-0.3407, -0.0256] | entirely_below_0 | 0.0110 |
| 7 | -0.0793 | [-0.1534, 0.0000] | covers_0 | 0.0250 |
| 8 | 0.0349 | [-0.1146, 0.1354] | covers_0 | 0.7120 |
| 9 | -0.0854 | [-0.2838, 0.0532] | covers_0 | 0.1170 |
| 10 | -0.3564 | [-0.5994, -0.1071] | entirely_below_0 | 0.0030 |
| 11 | 0.0528 | [-0.0761, 0.1955] | covers_0 | 0.7680 |
| 12 | -0.0623 | [-0.2497, 0.1062] | covers_0 | 0.2250 |
| 13 | -0.1516 | [-0.4722, 0.1749] | covers_0 | 0.1760 |
| 14 | 0.0623 | [-0.1699, 0.2133] | covers_0 | 0.7110 |
| 15 | 0.0434 | [-0.2964, 0.3314] | covers_0 | 0.5700 |
| 16 | 0.0431 | [-0.1374, 0.2354] | covers_0 | 0.6590 |
| 17 | -0.0009 | [-0.1704, 0.2096] | covers_0 | 0.5260 |
| 18 | -0.0196 | [-0.2537, 0.1745] | covers_0 | 0.3950 |
| 19 | 0.0414 | [-0.1295, 0.1680] | covers_0 | 0.7160 |

## Test-set overlap

- Pairwise test-question Jaccard over 190 pairs: min 0.0182, median 0.1200, max 0.2727.
- Unique question groups that appear in at least one test set: 134 of 134.
- Question groups that never appear in a test set: 0.

Stage 6 pairwise test-question overlap, each seed on its own frozen table:

- seeds 0 and 1: Jaccard 0.1429, 7 shared questions.
- seeds 0 and 2: Jaccard 0.2174, 10 shared questions.
- seeds 1 and 2: Jaccard 0.1667, 8 shared questions.

Twenty seeds repartition one pool of question groups. A test set is about 28 groups drawn inside positive-count strata, so successive test sets share groups. The sample SD across seeds describes that dependent repartition. It is not the standard error of 20 independent datasets, and it is not a confidence interval.

Stage 6's three seeds were a small sample from this same kind of overlap.
Adding seeds does not create 20 fresh RAGTruth corpora.

## Generator and claim-type support

Counts are positive claims. The gate is conditioned on generator and claim type.
These margins are properties of the frozen table and of the splits.
The model was not changed to compensate.

### Full table

| cell | claims | positives |
| --- | --- | --- |
| gpt-4-0613 / numeric | 14 | 0 |
| gpt-4-0613 / entity | 31 | 0 |
| gpt-4-0613 / extractive | 55 | 1 |
| gpt-4-0613 / abstractive | 34 | 0 |
| gpt-3.5-turbo-0613 / numeric | 18 | 1 |
| gpt-3.5-turbo-0613 / entity | 30 | 0 |
| gpt-3.5-turbo-0613 / extractive | 54 | 3 |
| gpt-3.5-turbo-0613 / abstractive | 32 | 1 |
| mistral-7B-instruct / numeric | 46 | 11 |
| mistral-7B-instruct / entity | 37 | 5 |
| mistral-7B-instruct / extractive | 25 | 2 |
| mistral-7B-instruct / abstractive | 25 | 1 |
| llama-2-7b-chat / numeric | 78 | 10 |
| llama-2-7b-chat / entity | 34 | 1 |
| llama-2-7b-chat / extractive | 12 | 1 |
| llama-2-7b-chat / abstractive | 9 | 1 |
| llama-2-13b-chat / numeric | 55 | 10 |
| llama-2-13b-chat / entity | 19 | 1 |
| llama-2-13b-chat / abstractive | 59 | 1 |
| llama-2-70b-chat / numeric | 43 | 6 |
| llama-2-70b-chat / entity | 32 | 0 |
| llama-2-70b-chat / extractive | 28 | 0 |
| llama-2-70b-chat / abstractive | 30 | 1 |

### Training positives across 20 seeds

The range is the min and max training-positive count of that margin.

| margin | min | median | max |
| --- | --- | --- | --- |
| gpt-4-0613 | 0 | 0.5 | 1 |
| gpt-3.5-turbo-0613 | 0 | 3.0 | 4 |
| mistral-7B-instruct | 9 | 11.5 | 14 |
| llama-2-7b-chat | 6 | 7.5 | 9 |
| llama-2-13b-chat | 4 | 7.0 | 10 |
| llama-2-70b-chat | 2 | 4.0 | 5 |
| type numeric | 17 | 22.0 | 26 |
| type entity | 2 | 4.0 | 7 |
| type extractive | 1 | 4.5 | 6 |
| type abstractive | 0 | 4.0 | 5 |

### Exploratory association

The rank associations and the scarcest-generator partition split are exploratory descriptions. They were limited to the conditioning variables the gate already uses. They are not a model search.

Count of test positive claims whose (generator_id, claim_type) cell has at most 0 training positives.
Across seeds: min 0, median 2.5, max 8.
Spearman rank correlation with AUROC, not a p-value: A7 -0.0741, A0 -0.2332, A4 -0.5735.

Count of test positive claims whose (generator_id, claim_type) cell has at most 1 training positives.
Across seeds: min 0, median 3.0, max 8.
Spearman rank correlation with AUROC, not a p-value: A7 -0.0458, A0 -0.3245, A4 -0.5650.

The generator with the fewest positives in the full table is gpt-4-0613 (id 0), with 1 positive claim(s), in question(s) ['11395'].

### Exploratory high-count test composition

Group question ids with at least 3 positive claims. Tabulate the test subset of those ids. No other grouping is tried.

| test questions with ≥3 positives | n seeds | mean A7 | mean A0 | mean A4 |
| --- | --- | --- | --- | --- |
| 12224,12189 | 6 | 0.6616 | 0.6401 | 0.6477 |
| 12224,12195 | 3 | 0.5867 | 0.5960 | 0.6530 |
| 12228,12189 | 4 | 0.4778 | 0.5625 | 0.6659 |
| 12228,12195 | 7 | 0.6176 | 0.6689 | 0.7383 |

## Synthetic regression

The planted table was regenerated at the frozen fingerprint settings
(seed 0, 30 questions, 3 generators) and compared with the stored parquet.
Synthetic models were not refit. Planted parameters were not edited.

- File hash matches the historical manifest: True.
- Regenerated frame equals the stored frame: True.
- Unchanged: True.

## Answers

1. Stage 6's three-seed mean A7 AUROC was 0.5025. On 20 seeds the mean is 0.5982 and the median is 0.6375, with range [0.2802, 0.7906] and 25th percentile 0.5341. 0.5025 falls inside that range and below the 25th percentile, so it is a low draw the distribution contains, not the typical seed.

2. A7 AUROC across 20 seeds: mean 0.5982, median 0.6375, SD 0.1427, min 0.2802, max 0.7906, IQR 0.1665 (25th 0.5341, 75th 0.7006). The SD is not a confidence interval.

3. A0 AUROC: mean 0.6280, median 0.6278, SD 0.0608, min 0.5046, max 0.7320, IQR 0.0815. A4 AUROC: mean 0.6838, median 0.6856, SD 0.0668, min 0.5669, max 0.8017, IQR 0.0919.

4. A7 is below A0 on 10 seeds, above on 10, tied on 0. Mean delta -0.0298.

5. A7 is below A4 on 13 seeds, above on 7, tied on 0. Mean delta -0.0857.

6. By point estimate, A7 beats A0 on 10 of 20 seeds and A4 on 7 of 20 seeds.

7. A7's sample SD is larger than both baselines. SD A7 0.1427, A0 0.0608, A4 0.0668. IQR A7 0.1665, A0 0.0815, A4 0.0919.

8. Partition positive counts are the same on every seed ([[33, 9, 15]] for train, validation, test). The seed still sets both the group assignment and A7's optimizer RNG, so group identity and initialization stay confounded with each other. The evidence points to instability beyond split-label imbalance, because the positive counts do not move.

9. Exploratory. The least-supported generator has 1 positive claim in the full table, and several generator-by-type cells have none. The count of test positives with no training positive in the same cell varies across seeds (see the cutoff-0 row). Spearman against AUROC, not a p-value: A7 -0.0741, A0 -0.2332, A4 -0.5735. The A7 rank correlation is near zero, so this sparsity count does not explain A7's seed-to-seed AUROC movement. The stronger A4 correlation is not an A7 finding. The high-count test-pair table is the other pre-specified description; its lowest A7 cell also has a lower A0 mean, and each cell has only a few seeds.

10. A7's median is not above both baselines, its seed SD is larger than both, and the paired intervals do not show a stable advantage. At least one generator has fewer than five positive claims, so a gate conditioned on generator is weakly identified on this slice. That supports keeping A7 as a mechanism prototype. It does not support publishing A7 as the main architecture on this RAGTruth result, and it does not by itself refute the mechanism on a better-supported sample.

## Paper-safe wording

### Result

On the frozen corrected RAGTruth table of 800 claims and 134 question groups, A0–A7 were refit for split seeds 0–19 with the Stage 6 positive-count group stratification and the unchanged training and threshold rules. A7 test AUROC had mean 0.5982, median 0.6375, sample SD 0.1427 (not a confidence interval), and range [0.2802, 0.7906]. A0 had mean 0.6280 (SD 0.0608) and A4 had mean 0.6838 (SD 0.0668). The A7−A0 delta had mean -0.0298; A7 was higher on 10 of 20 seeds and lower on 10. The A7−A4 delta had mean -0.0857; A7 was higher on 7 of 20 seeds and lower on 13. Paired question-grouped bootstrap intervals excluded 0 in favor of A7 on 1 of 20 seeds versus A0 and 0 of 20 versus A4, and in favor of the baseline on 3 and 4 of 20 seeds. The Stage 6 three-seed A7 mean of 0.5025 lies inside the 20-seed range and below the 25th percentile.

### Limitations

The 20 seeds repartition one pool of 134 questions. Pairwise Jaccard overlap of the test question sets has minimum 0.0182, median 0.1200, and maximum 0.2727. 134 groups appear in some test set and 0 never do. The across-seed SD is dispersion under that dependence, not a confidence interval and not evidence from 20 corpora. Each test set has 15 positive claims. Validation has 9. gpt-4-0613 contributes 1 positive claim in the whole table, and several generator-by-type cells have none, so a gate conditioned on those factors is weakly identified. The model seed equals the split seed, so A7's extra dispersion mixes assignment with optimizer noise. The sparsity associations are exploratory. A8 was not run. The synthetic check regenerated the planted fingerprint only.

### Recommendation

Recommendation 2: retain A7 only as a research hypothesis and mechanism prototype. A7's median is not above both baselines, its seed SD is larger than both, and the paired intervals do not show a stable advantage. At least one generator has fewer than five positive claims, so a gate conditioned on generator is weakly identified on this slice. That supports keeping A7 as a mechanism prototype. It does not support publishing A7 as the main architecture on this RAGTruth result, and it does not by itself refute the mechanism on a better-supported sample. The recommendation uses the median, the seed SD, the point-estimate win counts, the paired intervals, and the positive-count support of the conditioning variables. It does not use a selected subset of seeds.

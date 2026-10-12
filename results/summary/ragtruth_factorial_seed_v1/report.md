# RC-Gate Stage 8 — factorial split and model seeds

Split seed and model seed are crossed. The frozen seed-0 corrected table,
the group-stratified splitter, the variants, the hyperparameters, and the
Stage 5 question-grouped bootstrap are unchanged. Stage 4 through Stage 7
directories were not rewritten. Distributions below are not confidence intervals.

## Randomness-control audit

What each seed controls:

- Split assignment: `group_stratified_split` builds one `numpy.random.Generator`
  per positive-count stratum from `SeedSequence([split_seed, stratum])`. Group
  ids are sorted before the shuffle. The function does not call `set_seed` and
  does not read the global Python, NumPy, or torch generators.
- Global state at fit time: `RunContext.start` calls `set_seed(model_seed)`,
  which sets `random.seed`, `np.random.seed`, `torch.manual_seed`, and
  `PYTHONHASHSEED`. That call uses the model seed. It does not rebuild the split
  when a split object is passed in.
- Logistic A0–A3: `LogisticRegression(..., solver='lbfgs', random_state=model_seed)`.
  For `lbfgs`, scikit-learn does not use `random_state` to shuffle. A3's alpha
  grid is `numpy.linspace`. On this grid their test scores did not move with the model seed.
- A4: `HistGradientBoostingClassifier(..., early_stopping=False, random_state=model_seed)`.
  The seed is available for binning. Whether it moves predictions is an empirical
  result of this run, recorded in the within-split SDs.
- A5–A7 weight initialization: `set_seed(model_seed)` runs, then `RCGate()` draws
  the current torch state. The splitter does not draw torch numbers, so a different
  split seed does not advance that state. `fit` then calls `torch.manual_seed(model_seed)`
  again and draws batch order and UNK dropout from `numpy.random.default_rng(model_seed)`.
  There is no PyTorch `DataLoader` and no worker shuffle.
- Validation threshold: `tune_threshold` sees validation labels and validation
  scores only. The candidate grid is deterministic. Test rows are not an input.
- Bootstrap: a separate `default_rng(split_seed)` resamples `question_id`. It does
  not affect fitting. The requested count is 1000. The fraction of positive paired
  deltas is not a p-value.
- Checkpoint: A0–A7 are joblib payloads. `RCGateModel` is not an `nn.Module`, so
  the torch wrapper is not sent through `torch.save`.

Changing the model seed does not change split assignments. Changing the split
seed does not change A7's initial weights when the model seed is fixed, because
the splitter never consumes the torch generator that `set_seed` just reset.

## Checkpoint reproducibility

Joblib reload reproduced the in-memory scores exactly, including the Stage 7 checkpoint. RunResult.to_dict had stored round(threshold, 6). That moved the validation threshold from the exact quantile-grid value onto 6e-6. One negative test claim scored between those two cuts, so precision and F1 changed and AUROC did not. The discrepancy is threshold serialization, not model serialization, prediction drift, or a second fit.

- Exact threshold: 6.453252374040946e-06.
- Rounded to 6 decimals: 6e-06.
- Stage 7 stored threshold equals that rounding: True.
- Calls flipped by the rounding: 1 (1592#0).
- Nearest claim 1592#0 scored 6.420037727803235e-06 (label 0).
- In-memory scores equal a fresh reload: True.
- Fresh reload equals the Stage 7 checkpoint: True.
- Max absolute score gap versus the Stage 7 checkpoint: 0.0.

Fit-time metrics at the exact threshold: {"auroc": 0.7168, "f1": 0.2857, "precision": 0.1739, "recall": 0.8, "ece": 0.0916, "n": 164}. Metrics at the rounded threshold: {"auroc": 0.7168, "f1": 0.2824, "precision": 0.1714, "recall": 0.8, "ece": 0.0916, "n": 164}. Stage 7's stored fit-time metrics: {"auroc": 0.7168, "f1": 0.2857, "precision": 0.1739, "recall": 0.8, "ece": 0.0916, "n": 164}.

The serialization change is separate from the seed design. `RunResult.to_dict`
now stores the exact threshold instead of `round(threshold, 6)`. Stage 7 files
were not rewritten. Stage 8 selects the threshold on the reloaded model's
validation scores and scores the test set from that same reload.

## Protocol

- Fit table: `data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet` for every cell.
- Split seeds: 0 through 19. Model seeds: 0, 1, and 2. Variants: A0 through A7.
- A8 skipped: the table has no judge votes.
- 480 fits. No Stage 7 checkpoint was reused.
- Fractions 0.6/0.2/0.2 inside each positive-count stratum, via `cut_counts`.
- Threshold: unchanged `tune_threshold` on reloaded validation scores.
- Point metrics: Stage 5 `slice_metrics` on reloaded test scores. Full-precision
  values are stored beside the 4-decimal reported view.
- Paired AUROC: one question resample scores both models. 1000 requested resamples.
  The bootstrap seed is the split seed, so the draw is a property of the partition.
- Cell distribution, mean of the three model seeds, distribution of those 20 means,
  and the distribution of the 20 within-split SDs. Interval endpoints are not averaged.

Questions in the pool: 134. In-memory scores matched the first reload on 480 of 480 cells. Maximum absolute gap: 0.0.

## Split balance

Positive totals are fixed by the stratum sizes. Claim totals can still change
when a short group changes partition. Model seed does not enter this table.

| split | train groups | val groups | test groups | train positives | val positives | test positives | train claims | val claims | test claims |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 1 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 2 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 3 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 4 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 5 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 6 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 7 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 8 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 9 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 10 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 11 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 12 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 |
| 13 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 14 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 |
| 15 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 156 | 164 |
| 16 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 17 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |
| 18 | 80 | 26 | 28 | 33 | 9 | 15 | 480 | 152 | 168 |
| 19 | 80 | 26 | 28 | 33 | 9 | 15 | 476 | 156 | 168 |

## Distributions over the 60 cells

Each row pools 20 split seeds and 3 model seeds. The SD is not a confidence interval.

| variant | metric | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | auroc | 0.6280 | 0.6278 | 0.0597 | 0.5046 | 0.7320 | 0.5980 | 0.6794 | 0.0814 |
| A0 | f1 | 0.1807 | 0.1872 | 0.0660 | 0.0000 | 0.2857 | 0.1650 | 0.2245 | 0.0595 |
| A0 | precision | 0.1156 | 0.1193 | 0.0442 | 0.0000 | 0.2222 | 0.1010 | 0.1362 | 0.0352 |
| A0 | recall | 0.4967 | 0.4667 | 0.2651 | 0.0000 | 1.0000 | 0.3333 | 0.6833 | 0.3500 |
| A0 | ece | 0.0347 | 0.0315 | 0.0108 | 0.0195 | 0.0621 | 0.0290 | 0.0410 | 0.0119 |
| A0 | threshold | 0.0803 | 0.0830 | 0.0252 | 0.0280 | 0.1147 | 0.0617 | 0.1016 | 0.0399 |
| A1 | auroc | 0.6280 | 0.6247 | 0.0461 | 0.5516 | 0.7181 | 0.5914 | 0.6608 | 0.0694 |
| A1 | f1 | 0.1811 | 0.1933 | 0.0461 | 0.0909 | 0.2581 | 0.1595 | 0.2074 | 0.0479 |
| A1 | precision | 0.1263 | 0.1163 | 0.0413 | 0.0741 | 0.2500 | 0.1054 | 0.1367 | 0.0313 |
| A1 | recall | 0.5167 | 0.4333 | 0.3080 | 0.0667 | 0.9333 | 0.2500 | 0.8000 | 0.5500 |
| A1 | ece | 0.0279 | 0.0282 | 0.0089 | 0.0114 | 0.0456 | 0.0211 | 0.0341 | 0.0130 |
| A1 | threshold | 0.0785 | 0.0775 | 0.0298 | 0.0373 | 0.1246 | 0.0523 | 0.1024 | 0.0501 |
| A2 | auroc | 0.5594 | 0.5658 | 0.1125 | 0.3203 | 0.7468 | 0.5086 | 0.6484 | 0.1397 |
| A2 | f1 | 0.1501 | 0.1709 | 0.0776 | 0.0000 | 0.3019 | 0.1053 | 0.2005 | 0.0952 |
| A2 | precision | 0.0944 | 0.1075 | 0.0489 | 0.0000 | 0.2105 | 0.0714 | 0.1250 | 0.0536 |
| A2 | recall | 0.4533 | 0.4333 | 0.3150 | 0.0000 | 1.0000 | 0.2000 | 0.7333 | 0.5333 |
| A2 | ece | 0.0358 | 0.0284 | 0.0169 | 0.0193 | 0.0805 | 0.0222 | 0.0463 | 0.0241 |
| A2 | threshold | 0.0760 | 0.0754 | 0.0197 | 0.0353 | 0.1219 | 0.0680 | 0.0861 | 0.0182 |
| A3 | auroc | 0.6113 | 0.6225 | 0.0974 | 0.3821 | 0.8022 | 0.5528 | 0.6690 | 0.1161 |
| A3 | f1 | 0.1661 | 0.1720 | 0.0711 | 0.0000 | 0.3171 | 0.1171 | 0.2014 | 0.0843 |
| A3 | precision | 0.1200 | 0.1132 | 0.0502 | 0.0000 | 0.2083 | 0.0948 | 0.1471 | 0.0523 |
| A3 | recall | 0.3700 | 0.3000 | 0.2547 | 0.0000 | 0.8667 | 0.2000 | 0.4833 | 0.2833 |
| A3 | ece | 0.0343 | 0.0318 | 0.0136 | 0.0186 | 0.0788 | 0.0257 | 0.0355 | 0.0098 |
| A3 | threshold | 0.0828 | 0.0809 | 0.0162 | 0.0551 | 0.1217 | 0.0745 | 0.0887 | 0.0143 |
| A4 | auroc | 0.6839 | 0.6856 | 0.0656 | 0.5669 | 0.8017 | 0.6355 | 0.7274 | 0.0919 |
| A4 | f1 | 0.1920 | 0.2042 | 0.0972 | 0.0000 | 0.3636 | 0.1135 | 0.2542 | 0.1407 |
| A4 | precision | 0.1919 | 0.1723 | 0.1047 | 0.0000 | 0.4000 | 0.1450 | 0.2625 | 0.1175 |
| A4 | recall | 0.3067 | 0.3000 | 0.2371 | 0.0000 | 0.8000 | 0.1167 | 0.4667 | 0.3500 |
| A4 | ece | 0.0957 | 0.0959 | 0.0106 | 0.0806 | 0.1235 | 0.0872 | 0.1016 | 0.0144 |
| A4 | threshold | 0.1274 | 0.0031 | 0.2170 | 0.0000 | 0.5000 | 0.0002 | 0.1381 | 0.1379 |
| A5 | auroc | 0.6368 | 0.6391 | 0.1108 | 0.3817 | 0.8443 | 0.5695 | 0.7119 | 0.1424 |
| A5 | f1 | 0.1804 | 0.1818 | 0.0989 | 0.0000 | 0.4727 | 0.1127 | 0.2305 | 0.1178 |
| A5 | precision | 0.1288 | 0.1209 | 0.0733 | 0.0000 | 0.3333 | 0.0857 | 0.1674 | 0.0817 |
| A5 | recall | 0.4022 | 0.3667 | 0.2855 | 0.0000 | 1.0000 | 0.1833 | 0.6000 | 0.4167 |
| A5 | ece | 0.1668 | 0.0469 | 0.2008 | 0.0078 | 0.5545 | 0.0308 | 0.2320 | 0.2013 |
| A5 | threshold | 0.2510 | 0.1300 | 0.2092 | 0.0695 | 0.6513 | 0.1027 | 0.3406 | 0.2379 |
| A6 | auroc | 0.5267 | 0.5296 | 0.1074 | 0.2972 | 0.7163 | 0.4618 | 0.6045 | 0.1427 |
| A6 | f1 | 0.1511 | 0.1653 | 0.0740 | 0.0000 | 0.3125 | 0.1104 | 0.1984 | 0.0880 |
| A6 | precision | 0.1054 | 0.0987 | 0.0578 | 0.0000 | 0.2941 | 0.0766 | 0.1333 | 0.0567 |
| A6 | recall | 0.3778 | 0.3333 | 0.2830 | 0.0000 | 1.0000 | 0.1333 | 0.6000 | 0.4667 |
| A6 | ece | 0.1495 | 0.1846 | 0.0979 | 0.0051 | 0.2795 | 0.0375 | 0.2425 | 0.2050 |
| A6 | threshold | 0.2431 | 0.2849 | 0.1015 | 0.0663 | 0.3791 | 0.1432 | 0.3294 | 0.1861 |
| A7 | auroc | 0.5717 | 0.5911 | 0.1247 | 0.3072 | 0.7983 | 0.4690 | 0.6781 | 0.2091 |
| A7 | f1 | 0.1538 | 0.1638 | 0.0873 | 0.0000 | 0.3457 | 0.1053 | 0.1958 | 0.0906 |
| A7 | precision | 0.1040 | 0.1029 | 0.0614 | 0.0000 | 0.2400 | 0.0719 | 0.1338 | 0.0618 |
| A7 | recall | 0.3956 | 0.3333 | 0.2963 | 0.0000 | 1.0000 | 0.2000 | 0.5667 | 0.3667 |
| A7 | ece | 0.2099 | 0.2795 | 0.1528 | 0.0057 | 0.4507 | 0.0478 | 0.3088 | 0.2610 |
| A7 | threshold | 0.2962 | 0.3507 | 0.1637 | 0.0583 | 0.5492 | 0.1263 | 0.4175 | 0.2911 |

## Split-level means

For each split seed, average the three model seeds. The row then summarizes those
20 means. Averaging three seeds is not a confidence interval, and the 20 splits
are not 20 datasets.

| variant | metric | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | auroc | 0.6280 | 0.6278 | 0.0608 | 0.5046 | 0.7320 | 0.5980 | 0.6794 | 0.0814 |
| A0 | f1 | 0.1807 | 0.1872 | 0.0671 | 0.0000 | 0.2857 | 0.1650 | 0.2245 | 0.0595 |
| A0 | precision | 0.1156 | 0.1193 | 0.0449 | 0.0000 | 0.2222 | 0.1010 | 0.1362 | 0.0352 |
| A0 | recall | 0.4967 | 0.4667 | 0.2697 | 0.0000 | 1.0000 | 0.3333 | 0.6833 | 0.3500 |
| A0 | ece | 0.0347 | 0.0315 | 0.0110 | 0.0195 | 0.0621 | 0.0290 | 0.0410 | 0.0119 |
| A0 | threshold | 0.0803 | 0.0830 | 0.0257 | 0.0280 | 0.1147 | 0.0617 | 0.1016 | 0.0399 |
| A1 | auroc | 0.6280 | 0.6247 | 0.0469 | 0.5516 | 0.7181 | 0.5914 | 0.6608 | 0.0694 |
| A1 | f1 | 0.1811 | 0.1933 | 0.0469 | 0.0909 | 0.2581 | 0.1595 | 0.2074 | 0.0479 |
| A1 | precision | 0.1263 | 0.1163 | 0.0421 | 0.0741 | 0.2500 | 0.1054 | 0.1367 | 0.0313 |
| A1 | recall | 0.5167 | 0.4333 | 0.3133 | 0.0667 | 0.9333 | 0.2500 | 0.8000 | 0.5500 |
| A1 | ece | 0.0279 | 0.0282 | 0.0090 | 0.0114 | 0.0456 | 0.0211 | 0.0341 | 0.0130 |
| A1 | threshold | 0.0785 | 0.0775 | 0.0303 | 0.0373 | 0.1246 | 0.0523 | 0.1024 | 0.0501 |
| A2 | auroc | 0.5594 | 0.5658 | 0.1145 | 0.3203 | 0.7468 | 0.5086 | 0.6484 | 0.1397 |
| A2 | f1 | 0.1501 | 0.1709 | 0.0789 | 0.0000 | 0.3019 | 0.1053 | 0.2005 | 0.0952 |
| A2 | precision | 0.0944 | 0.1075 | 0.0497 | 0.0000 | 0.2105 | 0.0714 | 0.1250 | 0.0536 |
| A2 | recall | 0.4533 | 0.4333 | 0.3205 | 0.0000 | 1.0000 | 0.2000 | 0.7333 | 0.5333 |
| A2 | ece | 0.0358 | 0.0284 | 0.0172 | 0.0193 | 0.0805 | 0.0222 | 0.0463 | 0.0241 |
| A2 | threshold | 0.0760 | 0.0754 | 0.0201 | 0.0353 | 0.1219 | 0.0680 | 0.0861 | 0.0182 |
| A3 | auroc | 0.6113 | 0.6225 | 0.0991 | 0.3821 | 0.8022 | 0.5528 | 0.6690 | 0.1161 |
| A3 | f1 | 0.1661 | 0.1720 | 0.0723 | 0.0000 | 0.3171 | 0.1171 | 0.2014 | 0.0843 |
| A3 | precision | 0.1200 | 0.1132 | 0.0510 | 0.0000 | 0.2083 | 0.0948 | 0.1471 | 0.0523 |
| A3 | recall | 0.3700 | 0.3000 | 0.2591 | 0.0000 | 0.8667 | 0.2000 | 0.4833 | 0.2833 |
| A3 | ece | 0.0343 | 0.0318 | 0.0139 | 0.0186 | 0.0788 | 0.0257 | 0.0355 | 0.0098 |
| A3 | threshold | 0.0828 | 0.0809 | 0.0165 | 0.0551 | 0.1217 | 0.0745 | 0.0887 | 0.0143 |
| A4 | auroc | 0.6839 | 0.6856 | 0.0668 | 0.5669 | 0.8017 | 0.6355 | 0.7274 | 0.0919 |
| A4 | f1 | 0.1920 | 0.2042 | 0.0989 | 0.0000 | 0.3636 | 0.1135 | 0.2542 | 0.1407 |
| A4 | precision | 0.1919 | 0.1723 | 0.1066 | 0.0000 | 0.4000 | 0.1450 | 0.2625 | 0.1175 |
| A4 | recall | 0.3067 | 0.3000 | 0.2412 | 0.0000 | 0.8000 | 0.1167 | 0.4667 | 0.3500 |
| A4 | ece | 0.0957 | 0.0959 | 0.0108 | 0.0806 | 0.1235 | 0.0872 | 0.1016 | 0.0144 |
| A4 | threshold | 0.1274 | 0.0031 | 0.2207 | 0.0000 | 0.5000 | 0.0002 | 0.1381 | 0.1379 |
| A5 | auroc | 0.6368 | 0.6516 | 0.0722 | 0.4848 | 0.7371 | 0.5883 | 0.6894 | 0.1011 |
| A5 | f1 | 0.1804 | 0.1838 | 0.0602 | 0.0704 | 0.2806 | 0.1442 | 0.2168 | 0.0726 |
| A5 | precision | 0.1288 | 0.1240 | 0.0511 | 0.0520 | 0.2361 | 0.0886 | 0.1583 | 0.0696 |
| A5 | recall | 0.4022 | 0.4000 | 0.1479 | 0.1111 | 0.6667 | 0.3278 | 0.4889 | 0.1611 |
| A5 | ece | 0.1668 | 0.1964 | 0.0762 | 0.0273 | 0.2662 | 0.1084 | 0.2099 | 0.1015 |
| A5 | threshold | 0.2510 | 0.2732 | 0.0752 | 0.0942 | 0.3439 | 0.1948 | 0.3012 | 0.1065 |
| A6 | auroc | 0.5267 | 0.5459 | 0.0812 | 0.3728 | 0.6832 | 0.4699 | 0.5604 | 0.0906 |
| A6 | f1 | 0.1511 | 0.1560 | 0.0533 | 0.0670 | 0.2735 | 0.1058 | 0.1761 | 0.0704 |
| A6 | precision | 0.1054 | 0.1042 | 0.0427 | 0.0481 | 0.2340 | 0.0742 | 0.1260 | 0.0518 |
| A6 | recall | 0.3778 | 0.3778 | 0.1776 | 0.1111 | 0.7556 | 0.2389 | 0.4556 | 0.2167 |
| A6 | ece | 0.1495 | 0.1374 | 0.0645 | 0.0401 | 0.2478 | 0.1059 | 0.2237 | 0.1178 |
| A6 | threshold | 0.2431 | 0.2258 | 0.0650 | 0.1457 | 0.3329 | 0.1939 | 0.3225 | 0.1286 |
| A7 | auroc | 0.5717 | 0.5796 | 0.0684 | 0.4537 | 0.6720 | 0.5078 | 0.6264 | 0.1186 |
| A7 | f1 | 0.1538 | 0.1656 | 0.0464 | 0.0473 | 0.2209 | 0.1265 | 0.1822 | 0.0557 |
| A7 | precision | 0.1040 | 0.1147 | 0.0311 | 0.0262 | 0.1435 | 0.0850 | 0.1253 | 0.0403 |
| A7 | recall | 0.3956 | 0.3222 | 0.1786 | 0.0889 | 0.7556 | 0.2889 | 0.5056 | 0.2167 |
| A7 | ece | 0.2099 | 0.2237 | 0.0594 | 0.0564 | 0.2916 | 0.1796 | 0.2523 | 0.0727 |
| A7 | threshold | 0.2962 | 0.3147 | 0.0665 | 0.1249 | 0.3817 | 0.2456 | 0.3463 | 0.1007 |

## Within-split dispersion

Each split contributes one sample SD across model seeds 0, 1, and 2.
The table summarizes those 20 SDs. Three seeds make each SD preliminary.

| variant | metric | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | auroc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A0 | f1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A0 | ece | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A1 | auroc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A1 | f1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A1 | ece | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A2 | auroc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A2 | f1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A2 | ece | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A3 | auroc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A3 | f1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A3 | ece | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A4 | auroc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A4 | f1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A4 | ece | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| A5 | auroc | 0.0987 | 0.1023 | 0.0312 | 0.0224 | 0.1659 | 0.0777 | 0.1142 | 0.0365 |
| A5 | f1 | 0.0871 | 0.0784 | 0.0421 | 0.0308 | 0.2260 | 0.0587 | 0.1061 | 0.0474 |
| A5 | ece | 0.2004 | 0.2658 | 0.1079 | 0.0070 | 0.3044 | 0.1164 | 0.2850 | 0.1686 |
| A6 | auroc | 0.0774 | 0.0779 | 0.0413 | 0.0210 | 0.1725 | 0.0375 | 0.0999 | 0.0624 |
| A6 | f1 | 0.0567 | 0.0548 | 0.0291 | 0.0092 | 0.1320 | 0.0338 | 0.0713 | 0.0375 |
| A6 | ece | 0.0809 | 0.0815 | 0.0416 | 0.0296 | 0.1490 | 0.0376 | 0.1173 | 0.0797 |
| A7 | auroc | 0.1211 | 0.1169 | 0.0412 | 0.0474 | 0.2068 | 0.0976 | 0.1404 | 0.0428 |
| A7 | f1 | 0.0777 | 0.0657 | 0.0474 | 0.0128 | 0.1728 | 0.0414 | 0.0995 | 0.0581 |
| A7 | ece | 0.1580 | 0.1727 | 0.0682 | 0.0112 | 0.2336 | 0.1212 | 0.2137 | 0.0925 |

### A7 AUROC by split and model seed

| split | model 0 | model 1 | model 2 | mean | within SD |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.6845 | 0.4318 | 0.5965 | 0.5710 | 0.1283 |
| 1 | 0.7418 | 0.4698 | 0.5499 | 0.5872 | 0.1398 |
| 2 | 0.6797 | 0.7983 | 0.3978 | 0.6253 | 0.2057 |
| 3 | 0.7503 | 0.7769 | 0.4061 | 0.6444 | 0.2068 |
| 4 | 0.6103 | 0.4103 | 0.3405 | 0.4537 | 0.1400 |
| 5 | 0.6452 | 0.6268 | 0.5230 | 0.5984 | 0.0659 |
| 6 | 0.6013 | 0.4604 | 0.3718 | 0.4779 | 0.1158 |
| 7 | 0.6126 | 0.4157 | 0.4096 | 0.4793 | 0.1155 |
| 8 | 0.5969 | 0.7891 | 0.5028 | 0.6296 | 0.1459 |
| 9 | 0.5495 | 0.6680 | 0.4736 | 0.5637 | 0.0979 |
| 10 | 0.5922 | 0.6928 | 0.4575 | 0.5808 | 0.1181 |
| 11 | 0.6295 | 0.4282 | 0.4680 | 0.5086 | 0.1066 |
| 12 | 0.5900 | 0.5024 | 0.4235 | 0.5053 | 0.0833 |
| 13 | 0.5586 | 0.3072 | 0.5451 | 0.4703 | 0.1414 |
| 14 | 0.7059 | 0.6667 | 0.4466 | 0.6064 | 0.1397 |
| 15 | 0.7011 | 0.7588 | 0.4694 | 0.6431 | 0.1532 |
| 16 | 0.7107 | 0.7089 | 0.5965 | 0.6720 | 0.0654 |
| 17 | 0.6209 | 0.6771 | 0.7150 | 0.6710 | 0.0474 |
| 18 | 0.6776 | 0.5264 | 0.4976 | 0.5672 | 0.0967 |
| 19 | 0.7037 | 0.5181 | 0.5133 | 0.5784 | 0.1086 |

Method of moments for A7 AUROC: {"within_variance_mean": 0.016278333695674402, "variance_of_split_means": 0.004676966729412898, "between_split_variance": -0.0007491445024785694, "between_share_of_cell_variance": null, "n_model_seeds": 3, "label": "descriptive method of moments on repeated partitions of one pool; not a variance component from independent datasets"}.

Split-level statistics are repeated partitions of one question pool, not independent datasets.
Within-split dispersion uses the model seeds inside each split. With only three model seeds this is a preliminary description, not a precise population estimate.

## A7 minus A0

Delta is test AUROC(A7) minus test AUROC of the baseline on the same claims.
The interval is that cell's own paired question-grouped bootstrap.
A count of positions is not one combined interval, and the bootstrap fraction
is not a p-value.

### Over 60 cells

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.0563 | -0.0665 | 0.1377 | -0.3387 | 0.2022 | -0.1633 | 0.0514 | 0.2147 |

### Over 20 split-level means

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.0563 | -0.0593 | 0.0906 | -0.2255 | 0.1338 | -0.1092 | 0.0157 | 0.1249 |

### Within-split SDs of the delta

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| within-split SD | 0.1211 | 0.1169 | 0.0412 | 0.0474 | 0.2068 | 0.0976 | 0.1404 | 0.0428 |

- Cells with A7 above the baseline: 24.
- Cells with A7 below the baseline: 36.
- Cells with equal AUROC: 0.
- Intervals entirely above 0: 3.
- Intervals entirely below 0: 9.
- Intervals that cover 0: 48.
- Mean of interval endpoints: None.

| split | model 0 | model 1 | model 2 | mean | within SD |
| --- | --- | --- | --- | --- | --- |
| 0 | -0.0113 | -0.2641 | -0.0993 | -0.1249 | 0.1283 |
| 1 | 0.0676 | -0.2045 | -0.1244 | -0.0871 | 0.1398 |
| 2 | 0.0192 | 0.1377 | -0.2627 | -0.0353 | 0.2057 |
| 3 | 0.1224 | 0.1490 | -0.2218 | 0.0166 | 0.2068 |
| 4 | -0.0689 | -0.2689 | -0.3387 | -0.2255 | 0.1400 |
| 5 | 0.0689 | 0.0506 | -0.0532 | 0.0221 | 0.0659 |
| 6 | -0.0004 | -0.1414 | -0.2300 | -0.1239 | 0.1158 |
| 7 | -0.0693 | -0.2662 | -0.2723 | -0.2026 | 0.1155 |
| 8 | 0.0100 | 0.2022 | -0.0841 | 0.0427 | 0.1459 |
| 9 | -0.1826 | -0.0641 | -0.2584 | -0.1683 | 0.0979 |
| 10 | 0.0584 | 0.1590 | -0.0763 | 0.0471 | 0.1181 |
| 11 | 0.0233 | -0.1781 | -0.1383 | -0.0977 | 0.1066 |
| 12 | -0.0196 | -0.1072 | -0.1861 | -0.1043 | 0.0833 |
| 13 | 0.0540 | -0.1974 | 0.0405 | -0.0343 | 0.1414 |
| 14 | 0.0161 | -0.0231 | -0.2431 | -0.0834 | 0.1397 |
| 15 | 0.0734 | 0.1311 | -0.1584 | 0.0154 | 0.1532 |
| 16 | 0.0305 | 0.0288 | -0.0837 | -0.0081 | 0.0654 |
| 17 | 0.0837 | 0.1399 | 0.1778 | 0.1338 | 0.0474 |
| 18 | 0.0253 | -0.1259 | -0.1547 | -0.0851 | 0.0967 |
| 19 | 0.1020 | -0.0837 | -0.0885 | -0.0234 | 0.1086 |

Method of moments: {"within_variance_mean": 0.016278333695674402, "variance_of_split_means": 0.008206594564697441, "between_split_variance": 0.002780483332805973, "between_share_of_cell_variance": 0.14588960734818862, "n_model_seeds": 3, "label": "descriptive method of moments on repeated partitions of one pool; not a variance component from independent datasets"}.

## A7 minus A4

Delta is test AUROC(A7) minus test AUROC of the baseline on the same claims.
The interval is that cell's own paired question-grouped bootstrap.
A count of positions is not one combined interval, and the bootstrap fraction
is not a p-value.

### Over 60 cells

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.1122 | -0.1145 | 0.1526 | -0.3852 | 0.1919 | -0.1996 | 0.0144 | 0.2141 |

### Over 20 split-level means

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delta AUROC | -0.1122 | -0.1011 | 0.1126 | -0.3155 | 0.0762 | -0.2177 | -0.0292 | 0.1885 |

### Within-split SDs of the delta

|  | mean | median | sd | min | max | p25 | p75 | iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| within-split SD | 0.1211 | 0.1169 | 0.0412 | 0.0474 | 0.2068 | 0.0976 | 0.1404 | 0.0428 |

- Cells with A7 above the baseline: 16.
- Cells with A7 below the baseline: 44.
- Cells with equal AUROC: 0.
- Intervals entirely above 0: 2.
- Intervals entirely below 0: 14.
- Intervals that cover 0: 44.
- Mean of interval endpoints: None.

| split | model 0 | model 1 | model 2 | mean | within SD |
| --- | --- | --- | --- | --- | --- |
| 0 | -0.0562 | -0.3089 | -0.1442 | -0.1698 | 0.1283 |
| 1 | 0.0734 | -0.1987 | -0.1186 | -0.0813 | 0.1398 |
| 2 | -0.0871 | 0.0314 | -0.3691 | -0.1416 | 0.2057 |
| 3 | 0.0405 | 0.0671 | -0.3037 | -0.0654 | 0.2068 |
| 4 | -0.1136 | -0.3136 | -0.3834 | -0.2702 | 0.1400 |
| 5 | 0.0130 | -0.0054 | -0.1092 | -0.0339 | 0.0659 |
| 6 | -0.1154 | -0.2564 | -0.3450 | -0.2389 | 0.1158 |
| 7 | -0.1821 | -0.3791 | -0.3852 | -0.3155 | 0.1155 |
| 8 | -0.0057 | 0.1865 | -0.0998 | 0.0270 | 0.1459 |
| 9 | -0.2523 | -0.1338 | -0.3281 | -0.2381 | 0.0979 |
| 10 | -0.0444 | 0.0562 | -0.1791 | -0.0558 | 0.1181 |
| 11 | -0.1083 | -0.3096 | -0.2698 | -0.2292 | 0.1066 |
| 12 | -0.0362 | -0.1237 | -0.2026 | -0.1208 | 0.0833 |
| 13 | -0.1255 | -0.3769 | -0.1390 | -0.2138 | 0.1414 |
| 14 | 0.1307 | 0.0915 | -0.1285 | 0.0312 | 0.1397 |
| 15 | 0.1342 | 0.1919 | -0.0975 | 0.0762 | 0.1532 |
| 16 | 0.0235 | 0.0218 | -0.0906 | -0.0151 | 0.0654 |
| 17 | -0.0375 | 0.0187 | 0.0566 | 0.0126 | 0.0474 |
| 18 | -0.0139 | -0.1651 | -0.1939 | -0.1243 | 0.0967 |
| 19 | 0.0484 | -0.1373 | -0.1420 | -0.0770 | 0.1086 |

Method of moments: {"within_variance_mean": 0.016278333695674402, "variance_of_split_means": 0.012673281615990871, "between_split_variance": 0.007247170384099403, "between_share_of_cell_variance": 0.30805590220403406, "n_model_seeds": 3, "label": "descriptive method of moments on repeated partitions of one pool; not a variance component from independent datasets"}.

## Reproduction checks

- Cells recomputed from saved scores and a second checkpoint load: 480.
- Checkpoints matching the saved scores: 480.
- Max absolute second-reload gap: 0.0.
- Stage 7 coupled cells (split seed = model seed in {0, 1, 2}) matched fit-time metrics: True.
- Synthetic fingerprint unchanged: True.
- Prior result directories unchanged: True.

## Provenance

- Git HEAD: `47090018414f657bca8e5a43e97663feba2e5a7d`.
- Dirty working tree: True.
- HEAD alone reproduces this experiment: False.
- The working tree is dirty. Stage 8 source edits are uncommitted, and other untracked result files are present. Git HEAD alone does not reproduce this run.

Source porcelain lines:

- ` M rcgate/claims/dealias.py`
- ` M rcgate/data/__init__.py`
- ` M rcgate/data/build.py`
- ` M rcgate/data/ragtruth.py`
- ` M rcgate/data/splits.py`
- ` M rcgate/evaluate.py`
- ` M rcgate/metrics.py`
- ` M rcgate/pipeline.py`
- ` M tests/test_ragtruth.py`
- ` M tests/test_synthetic.py`
- `?? configs/ragtruth_corrected_integrity_v1.yaml`
- `?? configs/ragtruth_factorial_seed_v1.yaml`
- `?? configs/ragtruth_multi_seed_v1.yaml`
- `?? configs/ragtruth_split_corrected_v1.yaml`
- `?? rcgate/factorial_seed.py`
- `?? rcgate/multi_seed.py`
- `?? rcgate/split_sensitivity.py`
- `?? rcgate/stats_protocol.py`
- `?? tests/test_dealias.py`
- `?? tests/test_factorial_seed.py`
- `?? tests/test_group_stratified_split.py`
- `?? tests/test_multi_seed.py`
- `?? tests/test_stats_protocol.py`

Fit-table SHA-256: `082e524ccc3c062cfcec423b00e970f5fa846eefa2646c3d0c4139cd73954245`.

Source-file SHA-256:

- `rcgate/pipeline.py` `2bbfe06ad20ea4975bfb4c8f634b15a7e2de22c11975a1868f02ff3698d53e5c`
- `rcgate/data/splits.py` `bcf06557d665f5de9c4ba04a32f07355a8e73ebc99956606d73ce15895a10ae6`
- `rcgate/models/rcgate.py` `f7fd6aafc1d18fc5049b6e64c7e7e61223a75b3b18777072dd02a921eff36c41`
- `rcgate/models/baselines.py` `b53abc6cb0ee523a50198af8784dcc19ce3305295d844bd11214e846e9b0b1e7`
- `rcgate/models/gate.py` `89bd10a2c7bfb977d22cc98973e65af62e171b7dd18d32b36e8d5c78605db822`
- `rcgate/models/experts.py` `791efef96fcf1087ca3e3a93eb507d3b1b1301852833ec6a7fa00c1b80c2bf1d`
- `rcgate/models/meta.py` `f1b49232af6f19b4d820e399182470c9dcdbb87ccc02589376fd77ff2e62fb57`
- `rcgate/metrics.py` `d37285264e729d90cb5cc1e3d19089532d1bf72df48eb210516d249036b4ed09`
- `rcgate/utils.py` `0d1072abf2b7c9063a7ce424bfd396641bf7422ee1f18513bc227da3a3546e85`
- `rcgate/stats_protocol.py` `4cb9184b287db28ba4e769a0e863c9a73b0b859b8f37b0b9c376bc67f6275739`
- `rcgate/factorial_seed.py` `6af6088bd6ee8a52b80a08c712f2dced75d444c694b0ab93df2ce7b0373a368f`
- `configs/ragtruth_factorial_seed_v1.yaml` `66e1c6f1d02b770f2b9465abc20f1b945b6014dda05a96048eabe9b2c32d3d63`

## Answers

1. Yes. Stage 7 set the model seed equal to the split seed, so each reported seed changed the question assignment and, for models that read that seed, the initialization together. The two generators were already separate. The confounding is in that coupled design, not in a hidden shared stream.

2. At a fixed model seed, A7's AUROC SD across the 20 splits is 0.0600, 0.1509, and 0.0883. The median within-split SD is 0.1169 and the maximum is 0.2068. Both the split and the model seed move A7. With three model seeds, the initialization term is preliminary. The method-of-moments between-split share is undefined, on repeated partitions of one pool.

3. Yes. With the model seed held fixed, A7's test AUROC still spans 0.2009 at model seed 0, 0.4911 at model seed 1, 0.3745 at model seed 2. The criterion is a range above 0.10. Initialization is not required for that movement.

4. Within a split, A7's AUROC SD across the three model seeds has median 0.1169, minimum 0.0474, and maximum 0.2068. Initialization still moves A7 when the split is held fixed. Three model seeds make this a preliminary description, not a precise population SD.

5. Versus A0: No stable advantage over A0. The split-level mean delta is positive on 6 of 20 splits and negative on 14. Of 60 separate paired intervals, 3 lie entirely above 0 and 9 lie entirely below 0. Interval endpoints are not averaged.
   Versus A4: No stable advantage over A4. The split-level mean delta is positive on 4 of 20 splits and negative on 16. Of 60 separate paired intervals, 2 lie entirely above 0 and 14 lie entirely below 0. Interval endpoints are not averaged.

6. Joblib reload reproduced the in-memory scores exactly, including the Stage 7 checkpoint. RunResult.to_dict had stored round(threshold, 6). That moved the validation threshold from the exact quantile-grid value onto 6e-6. One negative test claim scored between those two cuts, so precision and F1 changed and AUROC did not. The discrepancy is threshold serialization, not model serialization, prediction drift, or a second fit.

7. Yes. All 480 reported point-metric blocks were recomputed from the saved validation scores, the saved test scores, and a second load of the checkpoint.

8. Supported:

- Question groups do not cross the train, validation, and test partitions.
- The split seed controls split assignment. The model seed does not.
- A7 training is reproducible at a fixed split and a fixed model seed, and it changes when the model seed changes.
- The Stage 7 A4 seed-6 F1 gap is explained by rounding the stored threshold to 6 decimals.

Unsupported:

- Stage 7's seed dispersion can be read as a pure split effect or a pure initialization effect. The design set the two seeds equal.
- A7 has a stable test-AUROC advantage over A0 on this RAGTruth table.
- A7 has a stable test-AUROC advantage over A4 on this RAGTruth table.

Uncertain:

- The magnitude of initialization variance. Only three model seeds were fit, so the within-split SD is preliminary.
- Generalization beyond this 134-question pool. The 20 splits repartition that one pool.
- A8. Judge votes are not in the frozen table, so A8 was not fit.


## Paper-safe wording

On the frozen corrected RAGTruth table, A0–A7 were refit on a 20 by 3 grid of group-stratified split seeds and model seeds. The fit table, splitter, features, labels, architectures, and validation threshold rule were unchanged. A7 test AUROC across the 60 cells had mean 0.5717 and sample SD 0.1247. The mean of the three model seeds inside each split, then summarized over the 20 splits, had mean 0.5717 and SD 0.0684. The median within-split SD was 0.1169. The split-level mean A7−A0 delta was positive on 6 of 20 splits (mean -0.0563). The split-level mean A7−A4 delta was positive on 4 of 20 splits (mean -0.1122). Separate paired intervals lay entirely above 0 on 3 of 60 cells versus A0 and 2 of 60 versus A4. Those endpoints were not averaged into one interval.

The 20 splits repartition one pool of 134 questions. They are not 20 independent datasets, and the across-split SD is not a confidence interval. Three model seeds per split make the initialization SD preliminary. Stage 7 coupled the two seeds, so its seed SD mixes assignment with initialization. The A4 seed-6 F1 difference was a threshold rounded to 6 decimals; the reloaded scores matched the fit. A8 was not run. The model was not retuned.

A7 does not show a stable advantage over A0 or A4 once split assignment and model initialization are separated. The result is a description of that instability, not a repaired estimate for A7.

# RC-Gate Stage 6 — group-stratified split sensitivity

This file changes the split and nothing else. Architecture, variant definitions,
signals, labels, claim text, and the Stage 5 uncertainty procedure are unchanged.
Historical result directories were not rewritten.
Three seeds are three seeds. They are not a robustness proof.

## What the old splitter does

`grouped_split(..., stratify=True)` sorts `question_id` groups by their mean label,
draws one permutation of that sorted list with `numpy.random.default_rng(seed)`,
and cuts the permuted list into blocks of about 60/20/20 groups.
The permutation removes the sort. The flag does not stratify.
Question ids are still disjoint across train, validation, and test.

## Corrected split

What is stratified: the group's positive-claim count, not the claim.
What is grouped: `question_id` (RAGTruth `source_id`). Every claim of a source stays together.
Proportions: inside each count stratum, `round(0.6 n)` train groups, `round(0.2 n)` validation groups, remainder test.
Seed: `numpy.random.default_rng(SeedSequence([seed, stratum]))` shuffles the sorted group ids of that stratum.
The same seed repeats. A different seed can reshuffle a stratum that has more than one group.
The shuffle does not depend on row order or on which other strata exist.
Limit: a stratum of size 2 contributes 1 train group, 0 validation groups, and 1 test group.
On these tables the counts 3 and 4 each have two groups, so validation receives none of those 7 positive claims.
The resulting positive totals are 33 train, 9 validation, and 15 test, on every seed.
The method does not search for a closer rate.

## Protocol

- Tables: `ragtruth_corrected_integrity_v1_s{0,1,2}.parquet` (800 claims, not rebuilt).
- Variants A0–A7 refit. A8 skipped because the tables have no judge votes.
- Seeds 0, 1, and 2 are both the model seed and the split seed.
- Thresholds are the validation F1 quantile rule from the training code, applied to the new validation split.
- Point estimate: unweighted mean of the three seed statistics after 4-decimal rounding.
- Across-seed dispersion: sample standard deviation, ddof=1. Not a confidence interval.
- Within-seed interval: 95% question-grouped percentile bootstrap, 1000 resamples.
- Paired interval: the same question draw scores both models. Not an average of endpoints.
- No classical p-value.

## Split balance

Deviation is the partition positive rate minus the full-table positive rate (0.07125, 57/800).
A mean-absolute-deviation reduction of at least 0.01 was specified as the bar for calling the balance change real. Smaller movements are not called material.

| method | seed | part | groups | claims | positives | positive rate | deviation from full table |
| --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_sort_then_permute | 0 | train | 80 | 480 | 33 | 0.0688 | -0.0025 |
| legacy_sort_then_permute | 0 | val | 27 | 158 | 7 | 0.0443 | -0.0269 |
| legacy_sort_then_permute | 0 | test | 27 | 162 | 17 | 0.1049 | 0.0337 |
| group_stratified | 0 | train | 80 | 476 | 33 | 0.0693 | -0.0019 |
| group_stratified | 0 | val | 26 | 156 | 9 | 0.0577 | -0.0136 |
| group_stratified | 0 | test | 28 | 168 | 15 | 0.0893 | 0.0180 |
| legacy_sort_then_permute | 1 | train | 80 | 476 | 27 | 0.0567 | -0.0145 |
| legacy_sort_then_permute | 1 | val | 27 | 162 | 14 | 0.0864 | 0.0152 |
| legacy_sort_then_permute | 1 | test | 27 | 162 | 16 | 0.0988 | 0.0275 |
| group_stratified | 1 | train | 80 | 476 | 33 | 0.0693 | -0.0019 |
| group_stratified | 1 | val | 26 | 156 | 9 | 0.0577 | -0.0136 |
| group_stratified | 1 | test | 28 | 168 | 15 | 0.0893 | 0.0180 |
| legacy_sort_then_permute | 2 | train | 80 | 480 | 31 | 0.0646 | -0.0067 |
| legacy_sort_then_permute | 2 | val | 27 | 162 | 11 | 0.0679 | -0.0033 |
| legacy_sort_then_permute | 2 | test | 27 | 158 | 15 | 0.0949 | 0.0237 |
| group_stratified | 2 | train | 80 | 476 | 33 | 0.0693 | -0.0019 |
| group_stratified | 2 | val | 26 | 156 | 9 | 0.0577 | -0.0136 |
| group_stratified | 2 | test | 28 | 168 | 15 | 0.0893 | 0.0180 |

- Legacy mean MAD: 0.0171.
- Group-stratified mean MAD: 0.0112.
- MAD drop (legacy minus stratified): 0.0059.
- Meets the 0.01 bar: False.
- Legacy test positive counts: 17, 16, 15.
- Stratified test positive counts: 15, 15, 15.

Test-question Jaccard between the legacy split and the stratified split, by seed:

- seed 0: 0.0784
- seed 1: 0.1957
- seed 2: 0.1000

## Leakage and duplication

- `question_id` in this repository: source_id from dataset/source_info.jsonl.
- `claim_id`: <response id>#<sentence index>, e.g. 123#2.
- Split policy recorded with the loader: grouped by question_id by this repo; the dataset's own split field is ignored.
- Within-question dependence: agree, contra, and sem_dist are scored against the other generators' answers for the same source. On these tables cross_n_others is 5 for every claim, so each row uses the other five answers. Those answers belong to the same question_id, and the split keeps that question in one partition.
- No additional grouping key is introduced. `source` has two corpus names and `task_type` has two task names; both are coarse labels, and each question has one task. `evidence_source` is a constant. The response prefix of `claim_id` maps to one question.
- Question overlap across the three frozen tables: {'0_1': 133, '0_2': 132, '1_2': 133}.
- Claim overlap across the three frozen tables: {'0_1': 794, '0_2': 788, '1_2': 794}.

### Seed 0

Generators present: {'train': [0, 1, 2, 3, 4, 5], 'val': [0, 1, 2, 3, 4, 5], 'test': [0, 1, 2, 3, 4, 5]}. Positive counts: {'train': 33, 'val': 9, 'test': 15}. Truncated groups: [{'question_id': '11775', 'claims': 2, 'generators': [0, 1], 'positives': 0, 'partition': 'train'}]. `cross_n_others` range: {'min': 5, 'max': 5}.

Duplicate exact texts: 14 (11 confined to one question, 3 spanning questions). Max questions per response prefix: 1. Max partitions per response prefix: 1.

Cross-question repeated strings:

- `Unable to answer based on given passages.` length 41, rows 63, questions 31, positives 0.
- `Sure!` length 5, rows 58, questions 53, positives 0.
- `Sure, I can help you with that!` length 31, rows 3, questions 3, positives 0.

- Exact text overlap train_val: 3 (`Sure!`, `Sure, I can help you with that!`, `Unable to answer based on given passages.`).
- Exact text overlap train_test: 3 (`Sure!`, `Sure, I can help you with that!`, `Unable to answer based on given passages.`).
- Exact text overlap val_test: 3 (`Sure!`, `Sure, I can help you with that!`, `Unable to answer based on given passages.`).

### Seed 1

Generators present: {'train': [0, 1, 2, 3, 4, 5], 'val': [0, 1, 2, 3, 4, 5], 'test': [0, 1, 2, 3, 4, 5]}. Positive counts: {'train': 33, 'val': 9, 'test': 15}. Truncated groups: [{'question_id': '12229', 'claims': 2, 'generators': [0, 1], 'positives': 0, 'partition': 'train'}]. `cross_n_others` range: {'min': 5, 'max': 5}.

Duplicate exact texts: 14 (11 confined to one question, 3 spanning questions). Max questions per response prefix: 1. Max partitions per response prefix: 1.

Cross-question repeated strings:

- `Unable to answer based on given passages.` length 41, rows 62, questions 30, positives 0.
- `Sure!` length 5, rows 59, questions 54, positives 0.
- `Sure, I can help you with that!` length 31, rows 3, questions 3, positives 0.

- Exact text overlap train_val: 2 (`Sure!`, `Unable to answer based on given passages.`).
- Exact text overlap train_test: 3 (`Sure!`, `Sure, I can help you with that!`, `Unable to answer based on given passages.`).
- Exact text overlap val_test: 2 (`Sure!`, `Unable to answer based on given passages.`).

### Seed 2

Generators present: {'train': [0, 1, 2, 3, 4, 5], 'val': [0, 1, 2, 3, 4, 5], 'test': [0, 1, 2, 3, 4, 5]}. Positive counts: {'train': 33, 'val': 9, 'test': 15}. Truncated groups: [{'question_id': '11776', 'claims': 2, 'generators': [0, 1], 'positives': 0, 'partition': 'train'}]. `cross_n_others` range: {'min': 5, 'max': 5}.

Duplicate exact texts: 13 (10 confined to one question, 3 spanning questions). Max questions per response prefix: 1. Max partitions per response prefix: 1.

Cross-question repeated strings:

- `Unable to answer based on given passages.` length 41, rows 62, questions 30, positives 0.
- `Sure!` length 5, rows 59, questions 54, positives 0.
- `Sure, I can help you with that!` length 31, rows 3, questions 3, positives 0.

- Exact text overlap train_val: 2 (`Sure!`, `Unable to answer based on given passages.`).
- Exact text overlap train_test: 3 (`Sure!`, `Sure, I can help you with that!`, `Unable to answer based on given passages.`).
- Exact text overlap val_test: 2 (`Sure!`, `Unable to answer based on given passages.`).

## Stage 5 canonical result (previous split)

### Means

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

### Per seed

Each bracket is that seed's interval. Endpoints are not averaged.

| variant | seed | n claims | n questions | n positive | AUROC (point estimate) | within-seed 95% question-grouped percentile bootstrap interval | resamples requested | resamples finite | F1 | precision | recall | ECE |
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

### Paired A7 minus A0 and A7 minus A4

Delta is AUROC(A7) minus AUROC(baseline) on the same test claims.
One resample draws question ids once and scores both models on those claims.
The bootstrap fraction is not a p-value. Interval endpoints are not averaged.

| comparison | seed | delta AUROC (point estimate) | per-seed 95% paired question-grouped percentile bootstrap interval | interval vs 0 | resamples finite | bootstrap fraction delta > 0 (not a p-value) |
| --- | --- | --- | --- | --- | --- | --- |
| A7 - A0 | 0 | -0.0264 | [-0.1039, 0.0565] | covers_0 | 1000/1000 | 0.2690 |
| A7 - A0 | 1 | 0.0997 | [-0.1835, 0.2863] | covers_0 | 999/1000 | 0.8138 |
| A7 - A0 | 2 | -0.1608 | [-0.4805, 0.2026] | covers_0 | 1000/1000 | 0.2510 |
| A7 - A4 | 0 | -0.0892 | [-0.2014, 0.0536] | covers_0 | 1000/1000 | 0.1070 |
| A7 - A4 | 1 | -0.0535 | [-0.2500, 0.0841] | covers_0 | 999/1000 | 0.2382 |
| A7 - A4 | 2 | -0.0625 | [-0.3930, 0.2744] | covers_0 | 1000/1000 | 0.4010 |

| comparison | mean delta AUROC (point estimate) | sd of delta across seeds (not a confidence interval) | per-seed interval positions |
| --- | --- | --- | --- |
| A7 - A0 | -0.0292 | 0.1303 | covers_0, covers_0, covers_0 |
| A7 - A4 | -0.0684 | 0.0186 | covers_0, covers_0, covers_0 |

## Stage 6 group-stratified result

### Means

| variant | mean AUROC (point estimate) | sd of AUROC across seeds (not a confidence interval) | mean F1 (point estimate) | sd of F1 across seeds (not a confidence interval) | mean precision (point estimate) | sd of precision across seeds (not a confidence interval) | mean recall (point estimate) | sd of recall across seeds (not a confidence interval) | mean ECE (point estimate) | sd of ECE across seeds (not a confidence interval) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 0.6903 | 0.0253 | 0.2339 | 0.0493 | 0.1814 | 0.0386 | 0.3778 | 0.1678 | 0.0239 | 0.0062 |
| A1 | 0.6787 | 0.0332 | 0.1831 | 0.0830 | 0.1599 | 0.0768 | 0.2222 | 0.1018 | 0.0332 | 0.0145 |
| A2 | 0.6430 | 0.0593 | 0.2047 | 0.0460 | 0.1310 | 0.0381 | 0.5778 | 0.3150 | 0.0280 | 0.0121 |
| A3 | 0.7143 | 0.0576 | 0.2259 | 0.1206 | 0.1637 | 0.0800 | 0.4000 | 0.3055 | 0.0397 | 0.0121 |
| A4 | 0.6890 | 0.0618 | 0.1976 | 0.0205 | 0.1515 | 0.0225 | 0.2889 | 0.0385 | 0.0998 | 0.0131 |
| A5 | 0.6678 | 0.0327 | 0.2287 | 0.0257 | 0.1895 | 0.0254 | 0.3556 | 0.2143 | 0.1792 | 0.2873 |
| A6 | 0.4764 | 0.0495 | 0.1438 | 0.1054 | 0.1702 | 0.1802 | 0.1555 | 0.0385 | 0.1306 | 0.1011 |
| A7 | 0.5025 | 0.1588 | 0.0862 | 0.1232 | 0.0643 | 0.0942 | 0.1333 | 0.1764 | 0.2446 | 0.1650 |

### Per seed

Each bracket is that seed's interval. Endpoints are not averaged.

| variant | seed | n claims | n questions | n positive | AUROC (point estimate) | within-seed 95% question-grouped percentile bootstrap interval | resamples requested | resamples finite | F1 | precision | recall | ECE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 0 | 168 | 28 | 15 | 0.6959 | [0.5742, 0.8095] | 1000 | 1000 | 0.2857 | 0.2222 | 0.4000 | 0.0212 |
| A0 | 1 | 168 | 28 | 15 | 0.7124 | [0.5729, 0.8563] | 1000 | 1000 | 0.2286 | 0.1455 | 0.5333 | 0.0310 |
| A0 | 2 | 168 | 28 | 15 | 0.6627 | [0.5207, 0.7706] | 1000 | 1000 | 0.1875 | 0.1765 | 0.2000 | 0.0195 |
| A1 | 0 | 168 | 28 | 15 | 0.6854 | [0.5835, 0.8113] | 1000 | 1000 | 0.2564 | 0.2083 | 0.3333 | 0.0333 |
| A1 | 1 | 168 | 28 | 15 | 0.7081 | [0.5640, 0.8150] | 1000 | 1000 | 0.0930 | 0.0714 | 0.1333 | 0.0477 |
| A1 | 2 | 168 | 28 | 15 | 0.6427 | [0.4953, 0.7624] | 1000 | 1000 | 0.2000 | 0.2000 | 0.2000 | 0.0187 |
| A2 | 0 | 168 | 28 | 15 | 0.5952 | [0.3877, 0.7472] | 1000 | 1000 | 0.1639 | 0.1087 | 0.3333 | 0.0197 |
| A2 | 1 | 168 | 28 | 15 | 0.6244 | [0.4884, 0.7976] | 1000 | 1000 | 0.1958 | 0.1094 | 0.9333 | 0.0224 |
| A2 | 2 | 168 | 28 | 15 | 0.7094 | [0.5246, 0.8474] | 1000 | 1000 | 0.2545 | 0.1750 | 0.4667 | 0.0419 |
| A3 | 0 | 168 | 28 | 15 | 0.6601 | [0.4525, 0.8109] | 1000 | 1000 | 0.2564 | 0.2083 | 0.3333 | 0.0259 |
| A3 | 1 | 168 | 28 | 15 | 0.7081 | [0.5640, 0.8150] | 1000 | 1000 | 0.0930 | 0.0714 | 0.1333 | 0.0445 |
| A3 | 2 | 168 | 28 | 15 | 0.7747 | [0.6897, 0.8587] | 1000 | 1000 | 0.3284 | 0.2115 | 0.7333 | 0.0486 |
| A4 | 0 | 168 | 28 | 15 | 0.7407 | [0.6368, 0.8585] | 1000 | 1000 | 0.2083 | 0.1515 | 0.3333 | 0.1045 |
| A4 | 1 | 168 | 28 | 15 | 0.6205 | [0.4248, 0.8061] | 1000 | 1000 | 0.1739 | 0.1290 | 0.2667 | 0.1099 |
| A4 | 2 | 168 | 28 | 15 | 0.7059 | [0.6112, 0.8087] | 1000 | 1000 | 0.2105 | 0.1739 | 0.2667 | 0.0850 |
| A5 | 0 | 168 | 28 | 15 | 0.6702 | [0.4588, 0.8372] | 1000 | 1000 | 0.2222 | 0.1905 | 0.2667 | 0.5110 |
| A5 | 1 | 168 | 28 | 15 | 0.6993 | [0.5507, 0.8460] | 1000 | 1000 | 0.2571 | 0.1636 | 0.6000 | 0.0133 |
| A5 | 2 | 168 | 28 | 15 | 0.6340 | [0.4619, 0.7539] | 1000 | 1000 | 0.2069 | 0.2143 | 0.2000 | 0.0133 |
| A6 | 0 | 168 | 28 | 15 | 0.4941 | [0.3006, 0.7477] | 1000 | 1000 | 0.1143 | 0.1000 | 0.1333 | 0.1003 |
| A6 | 1 | 168 | 28 | 15 | 0.4205 | [0.2460, 0.5538] | 1000 | 1000 | 0.0563 | 0.0357 | 0.1333 | 0.2434 |
| A6 | 2 | 168 | 28 | 15 | 0.5146 | [0.3569, 0.6779] | 1000 | 1000 | 0.2609 | 0.3750 | 0.2000 | 0.0482 |
| A7 | 0 | 168 | 28 | 15 | 0.6845 | [0.5960, 0.7927] | 1000 | 1000 | 0.2273 | 0.1724 | 0.3333 | 0.3827 |
| A7 | 1 | 168 | 28 | 15 | 0.3917 | [0.2281, 0.5276] | 1000 | 1000 | 0.0312 | 0.0204 | 0.0667 | 0.2891 |
| A7 | 2 | 168 | 28 | 15 | 0.4314 | [0.2788, 0.5947] | 1000 | 1000 | 0.0000 | 0.0000 | 0.0000 | 0.0619 |

### Paired A7 minus A0 and A7 minus A4

Delta is AUROC(A7) minus AUROC(baseline) on the same test claims.
One resample draws question ids once and scores both models on those claims.
The bootstrap fraction is not a p-value. Interval endpoints are not averaged.

| comparison | seed | delta AUROC (point estimate) | per-seed 95% paired question-grouped percentile bootstrap interval | interval vs 0 | resamples finite | bootstrap fraction delta > 0 (not a p-value) |
| --- | --- | --- | --- | --- | --- | --- |
| A7 - A0 | 0 | -0.0113 | [-0.1074, 0.1024] | covers_0 | 1000/1000 | 0.4220 |
| A7 - A0 | 1 | -0.3207 | [-0.6075, -0.0853] | entirely_below_0 | 1000/1000 | 0.0080 |
| A7 - A0 | 2 | -0.2314 | [-0.4080, -0.0572] | entirely_below_0 | 1000/1000 | 0.0010 |
| A7 - A4 | 0 | -0.0562 | [-0.1943, 0.0630] | covers_0 | 1000/1000 | 0.1830 |
| A7 - A4 | 1 | -0.2288 | [-0.5068, 0.0236] | covers_0 | 1000/1000 | 0.0350 |
| A7 - A4 | 2 | -0.2745 | [-0.4336, -0.1187] | entirely_below_0 | 1000/1000 | 0.0000 |

| comparison | mean delta AUROC (point estimate) | sd of delta across seeds (not a confidence interval) | per-seed interval positions |
| --- | --- | --- | --- |
| A7 - A0 | -0.1878 | 0.1592 | covers_0, entirely_below_0, entirely_below_0 |
| A7 - A4 | -0.1865 | 0.1151 | covers_0, covers_0, entirely_below_0 |

## Mean shifts (Stage 6 minus Stage 5)

A shift is a difference of point estimates. It is not a confidence interval.

| variant | mean AUROC shift | Stage 5 sd of AUROC | Stage 6 sd of AUROC |
| --- | --- | --- | --- |
| A0 | 0.0234 | 0.0627 | 0.0253 |
| A1 | -0.0234 | 0.0757 | 0.0332 |
| A2 | 0.0796 | 0.0672 | 0.0593 |
| A3 | 0.0933 | 0.0832 | 0.0576 |
| A4 | -0.0172 | 0.1061 | 0.0618 |
| A5 | -0.0305 | 0.0107 | 0.0327 |
| A6 | -0.0722 | 0.0968 | 0.0495 |
| A7 | -0.1352 | 0.0997 | 0.1588 |

| comparison | mean delta shift | Stage 5 sd of delta | Stage 6 mean delta | Stage 6 sd of delta |
| --- | --- | --- | --- | --- |
| A7 - A0 | -0.1586 | 0.1303 | -0.1878 | 0.1592 |
| A7 - A4 | -0.1181 | 0.0186 | -0.1865 | 0.1151 |

## Verdict

Label for the Stage 5 claim: **strengthened**.

- A7 mean above A0: Stage 5 False, Stage 6 False.
- A7 mean above A4: Stage 5 False, Stage 6 False.
- Any Stage 6 paired A7−A0 or A7−A4 interval entirely above 0: False.
- Balance MAD reduction meets 0.01: False.
- The label uses the across-seed SD of the paired delta as the scale for a mean shift.
  A shift inside that SD, with the same ordering and intervals that still cover 0, is not a new conclusion.
- This label is not a hypothesis test, and three seeds do not prove robustness.

### Paper-safe paragraph

On the frozen corrected RAGTruth tables, refitting A0–A7 with positive-count group stratification in place of the sort-then-permute split gives mean test AUROC 0.5025 for RC-Gate (A7), 0.6903 for flat logistic regression (A0), and 0.6890 for the metadata gradient-boosting control (A4). Under the previous split those means were 0.6377, 0.6669, and 0.7062. The A7 mean is lower after the change; it remains below A0 and below A4. Across-seed standard deviations on the new split are 0.1588 for A7, 0.0253 for A0, and 0.0618 for A4, and are not confidence intervals. Within each seed the uncertainty is a 95% percentile bootstrap on the test question ids (1000 resamples). The paired A7−A0 intervals are covers_0, entirely_below_0, entirely_below_0; the paired A7−A4 intervals are covers_0, covers_0, entirely_below_0. No paired interval lies entirely above 0. The Stage 5 statement that A7 is not supported as better than A0 or A4 still holds, and the point estimates sit further from an A7 advantage. The three seeds reuse nearly the same claims, so this rerun does not show that the result is robust to split construction in general, and it does not show that the earlier negative conclusion was produced by the sort-then-permute split.

### Limitations

- Three seeds, and the frozen tables share almost all of their claims, so the seed SD mixes split assignment with fitting on one pool.
- Validation has 9 positive claims and 26 questions. Test has 15 positive claims and 28 questions. The grouped intervals are wide.
- Strata with two groups cannot enter all three partitions. Test stays a few positive claims above the 20% share.
- Claims inside a question share cross-model features. The split keeps the question together; the bootstrap treats it as one group.
- A few short repeated strings appear in more than one partition. They were not removed.
- F1, precision, recall, and ECE have an across-seed SD only.
- Leave-one-generator-out was not refit. It still calls the legacy splitter.
- A8 remains skipped.

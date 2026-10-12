# Old vs corrected metrics

Old figures are the means across seeds 0, 1, and 2 in `results/summary/ragtruth.json`. Corrected figures are the same summary in `report.json` from this run. Deltas are corrected minus old. A8 stays skipped: the tables have no judge votes.

Uncertainty used here, not a percentage cutoff: the across-seed standard deviation of AUROC is about 0.06 to 0.12 on the full test slice, and the claim-level bootstrap interval for one seed is about 0.24 wide. A mean shift inside that seed scatter, and not consistent in sign across the three seeds, is not treated as a real change in detector quality.

## Overall AUROC

| Variant | Old AUC | Corrected AUC | Delta | Old SD | Corrected SD |
|---|---:|---:|---:|---:|---:|
| A0 | 0.681 | 0.667 | -0.014 | 0.066 | 0.063 |
| A1 | 0.705 | 0.702 | -0.003 | 0.076 | 0.076 |
| A2 | 0.564 | 0.563 | -0.001 | 0.078 | 0.067 |
| A3 | 0.618 | 0.621 | +0.003 | 0.066 | 0.083 |
| A4 | 0.740 | 0.706 | -0.034 | 0.082 | 0.106 |
| A5 | 0.690 | 0.698 | +0.009 | 0.027 | 0.011 |
| A6 | 0.532 | 0.549 | +0.017 | 0.089 | 0.097 |
| A7 | 0.631 | 0.638 | +0.006 | 0.123 | 0.100 |

Every overall delta is smaller than the across-seed SD of that variant. A4's −0.034 is the largest, and its three seeds move −0.052, +0.054, and −0.104, so the mean drop is not a shift in one direction.

## Other overall metrics

| Variant | Old F1 | New F1 | Old precision | New precision | Old recall | New recall | Old ECE | New ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 | 0.218 | 0.222 | 0.129 | 0.129 | 0.772 | 0.835 | 0.046 | 0.051 |
| A1 | 0.161 | 0.197 | 0.098 | 0.121 | 0.567 | 0.648 | 0.047 | 0.048 |
| A2 | 0.168 | 0.168 | 0.099 | 0.099 | 0.708 | 0.688 | 0.043 | 0.042 |
| A3 | 0.201 | 0.196 | 0.122 | 0.118 | 0.673 | 0.672 | 0.038 | 0.038 |
| A4 | 0.247 | 0.251 | 0.207 | 0.240 | 0.307 | 0.268 | 0.104 | 0.105 |
| A5 | 0.191 | 0.188 | 0.129 | 0.127 | 0.412 | 0.392 | 0.210 | 0.210 |
| A6 | 0.173 | 0.175 | 0.118 | 0.120 | 0.595 | 0.594 | 0.181 | 0.182 |
| A7 | 0.204 | 0.209 | 0.124 | 0.127 | 0.661 | 0.683 | 0.243 | 0.244 |

F1, precision, recall, and ECE on the full test slice move by amounts that are small next to the seed-to-seed scatter already present in the historical run. A1's F1 rise (0.161 to 0.197) is the largest of these and is still a thresholded metric on about 16 positive test rows per seed.

## Claim-type slices (AUROC)

Test-slice sizes shifted with the type correction: numeric about 50 to 49, entity about 42 to 37, extractive stays 31, abstractive about 38 to 43. Those slices have across-seed SDs of 0.05 to 0.34. The larger point-estimate moves (A4 extractive −0.142, A6 extractive +0.104, A2 extractive −0.082, A2 abstractive −0.074) sit inside that noise. They are not a change in slice behaviour.

| Variant | Numeric old | Numeric new | Entity old | Entity new | Extractive old | Extractive new | Abstractive old | Abstractive new |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 | 0.556 | 0.539 | 0.678 | 0.676 | 0.773 | 0.743 | 0.895 | 0.872 |
| A1 | 0.570 | 0.561 | 0.733 | 0.715 | 0.739 | 0.788 | 0.944 | 0.915 |
| A2 | 0.507 | 0.526 | 0.418 | 0.482 | 0.644 | 0.561 | 0.845 | 0.772 |
| A3 | 0.465 | 0.478 | 0.571 | 0.583 | 0.726 | 0.756 | 0.891 | 0.855 |
| A4 | 0.604 | 0.642 | 0.809 | 0.803 | 0.711 | 0.569 | 0.858 | 0.854 |
| A5 | 0.564 | 0.555 | 0.685 | 0.687 | 0.687 | 0.613 | 0.965 | 0.929 |
| A6 | 0.441 | 0.434 | 0.643 | 0.603 | 0.349 | 0.453 | 0.849 | 0.858 |
| A7 | 0.422 | 0.408 | 0.634 | 0.609 | 0.524 | 0.582 | 0.811 | 0.819 |

## A7 minus baseline, paired bootstrap (slice `all`)

`p_gt_0` is the fraction of resamples with a positive delta, averaged across seeds. The interval is the average of per-seed percentile intervals from 500 resamples. Both intervals for A7 − A4 include 0.

| Comparison | Old Δ | Old interval | Old p_gt_0 | Corrected Δ | Corrected interval | Corrected p_gt_0 |
|---|---:|---|---:|---:|---|---:|
| A7 − A0 | -0.050 | [-0.210, 0.100] | 0.415 | -0.029 | [-0.187, 0.133] | 0.399 |
| A7 − A1 | -0.074 | [-0.216, 0.067] | 0.461 | -0.064 | [-0.204, 0.081] | 0.390 |
| A7 − A2 | +0.067 | [-0.128, 0.250] | 0.709 | +0.074 | [-0.128, 0.265] | 0.741 |
| A7 − A3 | +0.014 | [-0.165, 0.196] | 0.567 | +0.017 | [-0.173, 0.213] | 0.525 |
| A7 − A4 | -0.109 | [-0.261, 0.044] | 0.201 | -0.068 | [-0.234, 0.113] | 0.208 |

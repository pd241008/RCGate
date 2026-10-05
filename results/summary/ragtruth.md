# RC-Gate results -- ragtruth

- generated: 2026-10-05 17:29
- git: `9865b61`
- config: `ragtruth.yaml`
- signal table: `/root/workspace/workspace/03-Code/Projects/Legacy/RCgate/data/signal_tables/ragtruth_s0.parquet`
- seeds: 3; bootstrap resamples: 1000 per slice per seed
- total wall clock: 34s

## Overall

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `all` | 160 | 0.681 | 0.681 ± 0.066 | 0.217 | 0.129 | 0.772 | 0.046 |
| A1 | `all` | 160 | 0.705 | 0.705 ± 0.076 | 0.161 | 0.098 | 0.567 | 0.047 |
| A2 | `all` | 160 | 0.564 | 0.564 ± 0.078 | 0.168 | 0.099 | 0.708 | 0.043 |
| A3 | `all` | 160 | 0.618 | 0.618 ± 0.066 | 0.201 | 0.122 | 0.673 | 0.038 |
| A4 | `all` | 160 | 0.740 | 0.740 ± 0.082 | 0.247 | 0.207 | 0.307 | 0.104 |
| A5 | `all` | 160 | 0.690 | 0.690 ± 0.027 | 0.191 | 0.129 | 0.412 | 0.210 |
| A6 | `all` | 160 | 0.532 | 0.532 ± 0.089 | 0.173 | 0.118 | 0.595 | 0.181 |
| A7 | `all` | 160 | 0.631 | 0.631 ± 0.123 | 0.204 | 0.124 | 0.661 | 0.243 |

## Per benchmark

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `benchmark=ragtruth` | 160 | 0.681 | 0.681 ± 0.066 | 0.217 | 0.129 | 0.772 | 0.046 |
| A1 | `benchmark=ragtruth` | 160 | 0.705 | 0.705 ± 0.076 | 0.161 | 0.098 | 0.567 | 0.047 |
| A2 | `benchmark=ragtruth` | 160 | 0.564 | 0.564 ± 0.078 | 0.168 | 0.099 | 0.708 | 0.043 |
| A3 | `benchmark=ragtruth` | 160 | 0.618 | 0.618 ± 0.066 | 0.201 | 0.122 | 0.673 | 0.038 |
| A4 | `benchmark=ragtruth` | 160 | 0.740 | 0.740 ± 0.082 | 0.247 | 0.207 | 0.307 | 0.104 |
| A5 | `benchmark=ragtruth` | 160 | 0.690 | 0.690 ± 0.027 | 0.191 | 0.129 | 0.412 | 0.210 |
| A6 | `benchmark=ragtruth` | 160 | 0.532 | 0.532 ± 0.089 | 0.173 | 0.118 | 0.595 | 0.181 |
| A7 | `benchmark=ragtruth` | 160 | 0.631 | 0.631 ± 0.123 | 0.204 | 0.124 | 0.661 | 0.243 |

## Per claim type

Claim types: 0 numeric, 1 entity, 2 extractive, 3 abstractive. The proposal's "numeric/extractive" reporting group is types 0 and 2.

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `claim_type=0` | 49 | 0.556 | 0.556 ± 0.178 | 0.250 | 0.156 | 0.736 | 0.113 |
| A0 | `claim_type=1` | 41 | 0.678 | 0.678 ± 0.116 | 0.102 | 0.056 | 0.722 | 0.039 |
| A0 | `claim_type=2` | 31 | 0.773 | 0.773 ± 0.151 | 0.211 | 0.119 | 0.933 | 0.068 |
| A0 | `claim_type=3` | 38 | 0.895 | 0.895 ± 0.092 | 0.302 | 0.186 | 1.000 | 0.057 |
| A1 | `claim_type=0` | 49 | 0.570 | 0.570 ± 0.223 | 0.207 | 0.138 | 0.609 | 0.112 |
| A1 | `claim_type=1` | 41 | 0.733 | 0.733 ± 0.141 | 0.049 | 0.027 | 0.444 | 0.025 |
| A1 | `claim_type=2` | 31 | 0.739 | 0.739 ± 0.090 | 0.162 | 0.094 | 0.600 | 0.053 |
| A1 | `claim_type=3` | 38 | 0.944 | 0.944 ± 0.096 | 0.167 | 0.095 | 0.667 | 0.071 |
| A2 | `claim_type=0` | 49 | 0.507 | 0.507 ± 0.175 | 0.242 | 0.165 | 0.700 | 0.117 |
| A2 | `claim_type=1` | 41 | 0.418 | 0.418 ± 0.041 | 0.060 | 0.032 | 0.667 | 0.033 |
| A2 | `claim_type=2` | 31 | 0.644 | 0.644 ± 0.265 | 0.227 | 0.131 | 1.000 | 0.050 |
| A2 | `claim_type=3` | 38 | 0.845 | 0.845 ± 0.071 | 0.182 | 0.112 | 0.667 | 0.064 |
| A3 | `claim_type=0` | 49 | 0.465 | 0.465 ± 0.134 | 0.241 | 0.155 | 0.676 | 0.111 |
| A3 | `claim_type=1` | 41 | 0.571 | 0.571 ± 0.143 | 0.090 | 0.051 | 0.611 | 0.030 |
| A3 | `claim_type=2` | 31 | 0.726 | 0.726 ± 0.207 | 0.256 | 0.147 | 1.000 | 0.052 |
| A3 | `claim_type=3` | 38 | 0.891 | 0.891 ± 0.095 | 0.226 | 0.139 | 0.667 | 0.067 |
| A4 | `claim_type=0` | 49 | 0.604 | 0.604 ± 0.116 | 0.263 | 0.218 | 0.337 | 0.193 |
| A4 | `claim_type=1` | 41 | 0.809 | 0.809 ± 0.157 | 0.189 | 0.120 | 0.444 | 0.054 |
| A4 | `claim_type=2` | 31 | 0.711 | 0.711 ± 0.191 | 0.000 | 0.000 | 0.000 | 0.079 |
| A4 | `claim_type=3` | 38 | 0.858 | 0.858 ± 0.139 | 0.633 | 0.833 | 0.556 | 0.062 |
| A5 | `claim_type=0` | 49 | 0.564 | 0.564 ± 0.263 | 0.266 | 0.182 | 0.645 | 0.208 |
| A5 | `claim_type=1` | 41 | 0.685 | 0.685 ± 0.168 | 0.048 | 0.027 | 0.222 | 0.211 |
| A5 | `claim_type=2` | 31 | 0.687 | 0.687 ± 0.244 | 0.061 | 0.033 | 0.333 | 0.235 |
| A5 | `claim_type=3` | 38 | 0.965 | 0.965 ± 0.042 | 0.000 | 0.000 | 0.000 | 0.251 |
| A6 | `claim_type=0` | 49 | 0.441 | 0.441 ± 0.082 | 0.215 | 0.135 | 0.542 | 0.128 |
| A6 | `claim_type=1` | 41 | 0.643 | 0.643 ± 0.087 | 0.069 | 0.037 | 0.556 | 0.233 |
| A6 | `claim_type=2` | 31 | 0.349 | 0.349 ± 0.311 | 0.144 | 0.351 | 0.400 | 0.195 |
| A6 | `claim_type=3` | 38 | 0.849 | 0.849 ± 0.155 | 0.139 | 0.080 | 0.889 | 0.224 |
| A7 | `claim_type=0` | 49 | 0.422 | 0.422 ± 0.046 | 0.238 | 0.147 | 0.636 | 0.211 |
| A7 | `claim_type=1` | 41 | 0.634 | 0.634 ± 0.253 | 0.165 | 0.099 | 0.833 | 0.275 |
| A7 | `claim_type=2` | 31 | 0.524 | 0.524 ± 0.282 | 0.130 | 0.075 | 0.533 | 0.244 |
| A7 | `claim_type=3` | 38 | 0.811 | 0.811 ± 0.284 | 0.139 | 0.077 | 0.667 | 0.287 |

## Per generator

`UNK` (-1) only appears in the leave-one-generator-out table below.

| variant | generator | n | AUROC (95% CI) | AUROC mean ± sd | F1 | ECE |
|---|---|---:|---|---|---:|---:|
| A0 | 0 | 27 | - | - | 0.000 | 0.063 |
| A0 | 1 | 27 | 0.796 | 0.796 ± 0.171 | 0.158 | 0.031 |
| A0 | 2 | 26 | 0.589 | 0.589 ± 0.014 | 0.331 | 0.164 |
| A0 | 3 | 26 | 0.686 | 0.686 ± 0.218 | 0.268 | 0.105 |
| A0 | 4 | 26 | 0.683 | 0.683 ± 0.193 | 0.225 | 0.054 |
| A0 | 5 | 26 | 0.805 | 0.805 ± 0.144 | 0.223 | 0.058 |
| A1 | 0 | 27 | - | - | 0.000 | 0.064 |
| A1 | 1 | 27 | 0.814 | 0.814 ± 0.255 | 0.080 | 0.033 |
| A1 | 2 | 26 | 0.704 | 0.704 ± 0.075 | 0.309 | 0.159 |
| A1 | 3 | 26 | 0.626 | 0.626 ± 0.183 | 0.179 | 0.106 |
| A1 | 4 | 26 | 0.689 | 0.689 ± 0.228 | 0.174 | 0.062 |
| A1 | 5 | 26 | 0.816 | 0.816 ± 0.073 | 0.144 | 0.076 |
| A2 | 0 | 27 | - | - | 0.000 | 0.060 |
| A2 | 1 | 27 | 0.674 | 0.674 ± 0.258 | 0.179 | 0.036 |
| A2 | 2 | 26 | 0.384 | 0.384 ± 0.076 | 0.257 | 0.163 |
| A2 | 3 | 26 | 0.625 | 0.625 ± 0.137 | 0.221 | 0.101 |
| A2 | 4 | 26 | 0.647 | 0.647 ± 0.252 | 0.183 | 0.064 |
| A2 | 5 | 26 | 0.580 | 0.580 ± 0.172 | 0.109 | 0.049 |
| A3 | 0 | 27 | - | - | 0.000 | 0.060 |
| A3 | 1 | 27 | 0.854 | 0.854 ± 0.221 | 0.218 | 0.027 |
| A3 | 2 | 26 | 0.498 | 0.498 ± 0.150 | 0.270 | 0.151 |
| A3 | 3 | 26 | 0.610 | 0.610 ± 0.133 | 0.218 | 0.106 |
| A3 | 4 | 26 | 0.601 | 0.601 ± 0.053 | 0.241 | 0.038 |
| A3 | 5 | 26 | 0.680 | 0.680 ± 0.174 | 0.197 | 0.049 |
| A4 | 0 | 27 | - | - | 0.000 | 0.000 |
| A4 | 1 | 27 | 0.727 | 0.727 ± 0.045 | 0.000 | 0.049 |
| A4 | 2 | 26 | 0.606 | 0.606 ± 0.177 | 0.274 | 0.224 |
| A4 | 3 | 26 | 0.594 | 0.594 ± 0.066 | 0.169 | 0.161 |
| A4 | 4 | 26 | 0.816 | 0.816 ± 0.135 | 0.356 | 0.105 |
| A4 | 5 | 26 | 0.697 | 0.697 ± 0.264 | 0.286 | 0.093 |
| A5 | 0 | 27 | - | - | 0.000 | 0.249 |
| A5 | 1 | 27 | 0.620 | 0.620 ± 0.330 | 0.051 | 0.223 |
| A5 | 2 | 26 | 0.664 | 0.664 ± 0.047 | 0.284 | 0.207 |
| A5 | 3 | 26 | 0.544 | 0.544 ± 0.148 | 0.204 | 0.247 |
| A5 | 4 | 26 | 0.726 | 0.726 ± 0.151 | 0.222 | 0.214 |
| A5 | 5 | 26 | 0.765 | 0.765 ± 0.045 | 0.201 | 0.239 |
| A6 | 0 | 27 | - | - | 0.000 | 0.280 |
| A6 | 1 | 27 | 0.230 | 0.230 ± 0.166 | 0.026 | 0.225 |
| A6 | 2 | 26 | 0.610 | 0.610 ± 0.071 | 0.361 | 0.111 |
| A6 | 3 | 26 | 0.449 | 0.449 ± 0.093 | 0.278 | 0.167 |
| A6 | 4 | 26 | 0.377 | 0.377 ± 0.070 | 0.113 | 0.187 |
| A6 | 5 | 26 | 0.602 | 0.602 ± 0.256 | 0.098 | 0.191 |
| A7 | 0 | 27 | - | - | 0.000 | 0.310 |
| A7 | 1 | 27 | 0.336 | 0.336 ± 0.312 | 0.075 | 0.267 |
| A7 | 2 | 26 | 0.695 | 0.695 ± 0.101 | 0.386 | 0.190 |
| A7 | 3 | 26 | 0.490 | 0.490 ± 0.169 | 0.158 | 0.246 |
| A7 | 4 | 26 | 0.631 | 0.631 ± 0.142 | 0.159 | 0.237 |
| A7 | 5 | 26 | 0.725 | 0.725 ± 0.123 | 0.274 | 0.274 |

## Per (claim type, generator) cell

Point estimates only; bootstrap CIs are not computed for 20 cells x 3 seeds.

| variant | cell | n | AUROC mean ± sd |
|---|---|---:|---|
| A0 | `abstractive|0` | 9 | - |
| A0 | `abstractive|1` | 8 | - |
| A0 | `abstractive|2` | 4 | 0.583 ± 0.118 |
| A0 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A0 | `abstractive|4` | 9 | 1.000 |
| A0 | `abstractive|5` | 6 | 0.938 ± 0.088 |
| A0 | `entity|0` | 6 | - |
| A0 | `entity|1` | 7 | - |
| A0 | `entity|2` | 9 | 0.633 ± 0.047 |
| A0 | `entity|3` | 5 | - |
| A0 | `entity|4` | 7 | 0.548 ± 0.168 |
| A0 | `entity|5` | 6 | - |
| A0 | `extractive|0` | 9 | - |
| A0 | `extractive|1` | 8 | 0.829 ± 0.199 |
| A0 | `extractive|2` | 4 | 0.500 |
| A0 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A0 | `extractive|5` | 6 | - |
| A0 | `numeric|0` | 2 | - |
| A0 | `numeric|1` | 3 | - |
| A0 | `numeric|2` | 8 | 0.593 ± 0.116 |
| A0 | `numeric|3` | 17 | 0.655 ± 0.327 |
| A0 | `numeric|4` | 10 | 0.457 ± 0.141 |
| A0 | `numeric|5` | 8 | 0.722 ± 0.293 |
| A1 | `abstractive|0` | 9 | - |
| A1 | `abstractive|1` | 8 | - |
| A1 | `abstractive|2` | 4 | 0.875 ± 0.177 |
| A1 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A1 | `abstractive|4` | 9 | 1.000 |
| A1 | `abstractive|5` | 6 | 0.875 ± 0.177 |
| A1 | `entity|0` | 6 | - |
| A1 | `entity|1` | 7 | - |
| A1 | `entity|2` | 9 | 0.767 ± 0.094 |
| A1 | `entity|3` | 5 | - |
| A1 | `entity|4` | 7 | 0.786 ± 0.303 |
| A1 | `entity|5` | 6 | - |
| A1 | `extractive|0` | 9 | - |
| A1 | `extractive|1` | 8 | 0.792 ± 0.260 |
| A1 | `extractive|2` | 4 | 1.000 |
| A1 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A1 | `extractive|5` | 6 | - |
| A1 | `numeric|0` | 2 | - |
| A1 | `numeric|1` | 3 | - |
| A1 | `numeric|2` | 8 | 0.491 ± 0.216 |
| A1 | `numeric|3` | 17 | 0.599 ± 0.366 |
| A1 | `numeric|4` | 10 | 0.515 ± 0.299 |
| A1 | `numeric|5` | 8 | 0.736 ± 0.120 |
| A2 | `abstractive|0` | 9 | - |
| A2 | `abstractive|1` | 8 | - |
| A2 | `abstractive|2` | 4 | 0.417 ± 0.118 |
| A2 | `abstractive|3` | 2 | 0.250 ± 0.354 |
| A2 | `abstractive|4` | 9 | 1.000 |
| A2 | `abstractive|5` | 6 | 1.000 ± 0.000 |
| A2 | `entity|0` | 6 | - |
| A2 | `entity|1` | 7 | - |
| A2 | `entity|2` | 9 | 0.567 ± 0.377 |
| A2 | `entity|3` | 5 | - |
| A2 | `entity|4` | 7 | 0.309 ± 0.034 |
| A2 | `entity|5` | 6 | - |
| A2 | `extractive|0` | 9 | - |
| A2 | `extractive|1` | 8 | 0.639 ± 0.376 |
| A2 | `extractive|2` | 4 | 0.000 |
| A2 | `extractive|3` | 3 | 0.583 ± 0.118 |
| A2 | `extractive|5` | 6 | - |
| A2 | `numeric|0` | 2 | - |
| A2 | `numeric|1` | 3 | - |
| A2 | `numeric|2` | 8 | 0.556 ± 0.389 |
| A2 | `numeric|3` | 17 | 0.675 ± 0.243 |
| A2 | `numeric|4` | 10 | 0.439 ± 0.445 |
| A2 | `numeric|5` | 8 | 0.653 ± 0.349 |
| A3 | `abstractive|0` | 9 | - |
| A3 | `abstractive|1` | 8 | - |
| A3 | `abstractive|2` | 4 | 0.417 ± 0.118 |
| A3 | `abstractive|3` | 2 | 0.250 ± 0.354 |
| A3 | `abstractive|4` | 9 | 1.000 |
| A3 | `abstractive|5` | 6 | 1.000 ± 0.000 |
| A3 | `entity|0` | 6 | - |
| A3 | `entity|1` | 7 | - |
| A3 | `entity|2` | 9 | 0.667 ± 0.000 |
| A3 | `entity|3` | 5 | - |
| A3 | `entity|4` | 7 | 0.452 ± 0.168 |
| A3 | `entity|5` | 6 | - |
| A3 | `extractive|0` | 9 | - |
| A3 | `extractive|1` | 8 | 0.847 ± 0.168 |
| A3 | `extractive|2` | 4 | 0.000 |
| A3 | `extractive|3` | 3 | 0.583 ± 0.118 |
| A3 | `extractive|5` | 6 | - |
| A3 | `numeric|0` | 2 | - |
| A3 | `numeric|1` | 3 | - |
| A3 | `numeric|2` | 8 | 0.361 ± 0.100 |
| A3 | `numeric|3` | 17 | 0.621 ± 0.275 |
| A3 | `numeric|4` | 10 | 0.306 ± 0.179 |
| A3 | `numeric|5` | 8 | 0.625 ± 0.273 |
| A4 | `abstractive|0` | 9 | - |
| A4 | `abstractive|1` | 8 | - |
| A4 | `abstractive|2` | 4 | 0.750 ± 0.354 |
| A4 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A4 | `abstractive|4` | 9 | 1.000 |
| A4 | `abstractive|5` | 6 | 0.583 ± 0.118 |
| A4 | `entity|0` | 6 | - |
| A4 | `entity|1` | 7 | - |
| A4 | `entity|2` | 9 | 0.733 ± 0.141 |
| A4 | `entity|3` | 5 | - |
| A4 | `entity|4` | 7 | 0.786 ± 0.303 |
| A4 | `entity|5` | 6 | - |
| A4 | `extractive|0` | 9 | - |
| A4 | `extractive|1` | 8 | 0.799 ± 0.076 |
| A4 | `extractive|2` | 4 | 0.500 |
| A4 | `extractive|3` | 3 | 0.750 ± 0.354 |
| A4 | `extractive|5` | 6 | - |
| A4 | `numeric|0` | 2 | - |
| A4 | `numeric|1` | 3 | - |
| A4 | `numeric|2` | 8 | 0.593 ± 0.370 |
| A4 | `numeric|3` | 17 | 0.428 ± 0.100 |
| A4 | `numeric|4` | 10 | 0.734 ± 0.145 |
| A4 | `numeric|5` | 8 | 0.806 ± 0.173 |
| A5 | `abstractive|0` | 9 | - |
| A5 | `abstractive|1` | 8 | - |
| A5 | `abstractive|2` | 4 | 1.000 ± 0.000 |
| A5 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A5 | `abstractive|4` | 9 | 1.000 |
| A5 | `abstractive|5` | 6 | 1.000 ± 0.000 |
| A5 | `entity|0` | 6 | - |
| A5 | `entity|1` | 7 | - |
| A5 | `entity|2` | 9 | 0.583 ± 0.118 |
| A5 | `entity|3` | 5 | - |
| A5 | `entity|4` | 7 | 0.857 ± 0.202 |
| A5 | `entity|5` | 6 | - |
| A5 | `extractive|0` | 9 | - |
| A5 | `extractive|1` | 8 | 0.615 ± 0.334 |
| A5 | `extractive|2` | 4 | 1.000 |
| A5 | `extractive|3` | 3 | 1.000 ± 0.000 |
| A5 | `extractive|5` | 6 | - |
| A5 | `numeric|0` | 2 | - |
| A5 | `numeric|1` | 3 | - |
| A5 | `numeric|2` | 8 | 0.565 ± 0.181 |
| A5 | `numeric|3` | 17 | 0.560 ± 0.308 |
| A5 | `numeric|4` | 10 | 0.540 ± 0.468 |
| A5 | `numeric|5` | 8 | 0.694 ± 0.337 |
| A6 | `abstractive|0` | 9 | - |
| A6 | `abstractive|1` | 8 | - |
| A6 | `abstractive|2` | 4 | 0.667 ± 0.471 |
| A6 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A6 | `abstractive|4` | 9 | 1.000 |
| A6 | `abstractive|5` | 6 | 0.812 ± 0.265 |
| A6 | `entity|0` | 6 | - |
| A6 | `entity|1` | 7 | - |
| A6 | `entity|2` | 9 | 0.500 ± 0.236 |
| A6 | `entity|3` | 5 | - |
| A6 | `entity|4` | 7 | 0.691 ± 0.034 |
| A6 | `entity|5` | 6 | - |
| A6 | `extractive|0` | 9 | - |
| A6 | `extractive|1` | 8 | 0.280 ± 0.098 |
| A6 | `extractive|2` | 4 | 1.000 |
| A6 | `extractive|3` | 3 | 0.500 ± 0.707 |
| A6 | `extractive|5` | 6 | - |
| A6 | `numeric|0` | 2 | - |
| A6 | `numeric|1` | 3 | - |
| A6 | `numeric|2` | 8 | 0.463 ± 0.032 |
| A6 | `numeric|3` | 17 | 0.273 ± 0.188 |
| A6 | `numeric|4` | 10 | 0.274 ± 0.205 |
| A6 | `numeric|5` | 8 | 0.458 ± 0.191 |
| A7 | `abstractive|0` | 9 | - |
| A7 | `abstractive|1` | 8 | - |
| A7 | `abstractive|2` | 4 | 0.833 ± 0.236 |
| A7 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A7 | `abstractive|4` | 9 | 1.000 |
| A7 | `abstractive|5` | 6 | 0.833 ± 0.236 |
| A7 | `entity|0` | 6 | - |
| A7 | `entity|1` | 7 | - |
| A7 | `entity|2` | 9 | 0.700 ± 0.189 |
| A7 | `entity|3` | 5 | - |
| A7 | `entity|4` | 7 | 0.691 ± 0.034 |
| A7 | `entity|5` | 6 | - |
| A7 | `extractive|0` | 9 | - |
| A7 | `extractive|1` | 8 | 0.414 ± 0.400 |
| A7 | `extractive|2` | 4 | 1.000 |
| A7 | `extractive|3` | 3 | 0.583 ± 0.118 |
| A7 | `extractive|5` | 6 | - |
| A7 | `numeric|0` | 2 | - |
| A7 | `numeric|1` | 3 | - |
| A7 | `numeric|2` | 8 | 0.593 ± 0.085 |
| A7 | `numeric|3` | 17 | 0.263 ± 0.300 |
| A7 | `numeric|4` | 10 | 0.372 ± 0.244 |
| A7 | `numeric|5` | 8 | 0.444 ± 0.173 |

## H2 test: A7 minus baseline, paired bootstrap

Both models are scored on the *same* test rows, so this is a paired comparison and much tighter than differencing two separate CIs. `p_gt_0` is the bootstrap fraction of resamples favouring A7.

| slice | comparison | ΔAUROC | 95% CI | p_gt_0 |
|---|---|---:|---|---:|
| `all` | A7 - A0 | -0.050 | [-0.210, 0.100] | 0.415 |
| `benchmark=ragtruth` | A7 - A0 | -0.050 | [-0.210, 0.100] | 0.415 |
| `claim_type=0` | A7 - A0 | -0.134 | [-0.405, 0.120] | 0.295 |
| `claim_type=1` | A7 - A0 | -0.044 | [-0.269, 0.183] | 0.485 |
| `claim_type=2` | A7 - A0 | -0.249 | [-0.470, -0.033] | 0.091 |
| `claim_type=3` | A7 - A0 | -0.084 | [-0.233, 0.053] | 0.331 |
| `generator_id=0` | A7 - A0 | - | [-, -] | - |
| `generator_id=1` | A7 - A0 | -0.461 | [-0.644, -0.243] | 0.000 |
| `generator_id=2` | A7 - A0 | 0.107 | [-0.167, 0.364] | 0.700 |
| `generator_id=3` | A7 - A0 | -0.196 | [-0.503, 0.201] | 0.263 |
| `generator_id=4` | A7 - A0 | -0.052 | [-0.457, 0.389] | 0.422 |
| `generator_id=5` | A7 - A0 | -0.080 | [-0.394, 0.224] | 0.306 |
| `all` | A7 - A1 | -0.074 | [-0.216, 0.067] | 0.461 |
| `benchmark=ragtruth` | A7 - A1 | -0.074 | [-0.216, 0.067] | 0.461 |
| `claim_type=0` | A7 - A1 | -0.148 | [-0.380, 0.069] | 0.321 |
| `claim_type=1` | A7 - A1 | -0.099 | [-0.274, 0.076] | 0.386 |
| `claim_type=2` | A7 - A1 | -0.215 | [-0.444, 0.025] | 0.266 |
| `claim_type=3` | A7 - A1 | -0.134 | [-0.265, -0.017] | 0.326 |
| `generator_id=0` | A7 - A1 | - | [-, -] | - |
| `generator_id=1` | A7 - A1 | -0.478 | [-0.705, -0.256] | 0.014 |
| `generator_id=2` | A7 - A1 | -0.009 | [-0.244, 0.224] | 0.425 |
| `generator_id=3` | A7 - A1 | -0.135 | [-0.495, 0.250] | 0.388 |
| `generator_id=4` | A7 - A1 | -0.058 | [-0.416, 0.346] | 0.461 |
| `generator_id=5` | A7 - A1 | -0.091 | [-0.396, 0.203] | 0.290 |
| `all` | A7 - A2 | 0.067 | [-0.128, 0.250] | 0.709 |
| `benchmark=ragtruth` | A7 - A2 | 0.067 | [-0.128, 0.250] | 0.709 |
| `claim_type=0` | A7 - A2 | -0.085 | [-0.423, 0.240] | 0.362 |
| `claim_type=1` | A7 - A2 | 0.216 | [-0.049, 0.480] | 0.770 |
| `claim_type=2` | A7 - A2 | -0.120 | [-0.485, 0.259] | 0.493 |
| `claim_type=3` | A7 - A2 | -0.035 | [-0.184, 0.145] | 0.631 |
| `generator_id=0` | A7 - A2 | - | [-, -] | - |
| `generator_id=1` | A7 - A2 | -0.338 | [-0.640, 0.018] | 0.378 |
| `generator_id=2` | A7 - A2 | 0.312 | [-0.062, 0.645] | 0.909 |
| `generator_id=3` | A7 - A2 | -0.135 | [-0.520, 0.321] | 0.346 |
| `generator_id=4` | A7 - A2 | -0.016 | [-0.397, 0.405] | 0.497 |
| `generator_id=5` | A7 - A2 | 0.145 | [-0.289, 0.573] | 0.683 |
| `all` | A7 - A3 | 0.014 | [-0.165, 0.196] | 0.567 |
| `benchmark=ragtruth` | A7 - A3 | 0.014 | [-0.165, 0.196] | 0.567 |
| `claim_type=0` | A7 - A3 | -0.043 | [-0.366, 0.268] | 0.529 |
| `claim_type=1` | A7 - A3 | 0.062 | [-0.154, 0.266] | 0.580 |
| `claim_type=2` | A7 - A3 | -0.202 | [-0.516, 0.129] | 0.364 |
| `claim_type=3` | A7 - A3 | -0.080 | [-0.231, 0.082] | 0.334 |
| `generator_id=0` | A7 - A3 | - | [-, -] | - |
| `generator_id=1` | A7 - A3 | -0.518 | [-0.795, -0.191] | 0.054 |
| `generator_id=2` | A7 - A3 | 0.197 | [-0.143, 0.518] | 0.695 |
| `generator_id=3` | A7 - A3 | -0.120 | [-0.509, 0.316] | 0.393 |
| `generator_id=4` | A7 - A3 | 0.030 | [-0.437, 0.547] | 0.545 |
| `generator_id=5` | A7 - A3 | 0.045 | [-0.374, 0.466] | 0.453 |
| `all` | A7 - A4 | -0.109 | [-0.261, 0.044] | 0.201 |
| `benchmark=ragtruth` | A7 - A4 | -0.109 | [-0.261, 0.044] | 0.201 |
| `claim_type=0` | A7 - A4 | -0.182 | [-0.439, 0.054] | 0.081 |
| `claim_type=1` | A7 - A4 | -0.176 | [-0.419, 0.030] | 0.414 |
| `claim_type=2` | A7 - A4 | -0.187 | [-0.474, 0.083] | 0.081 |
| `claim_type=3` | A7 - A4 | -0.047 | [-0.264, 0.231] | 0.307 |
| `generator_id=0` | A7 - A4 | - | [-, -] | - |
| `generator_id=1` | A7 - A4 | -0.391 | [-0.573, -0.180] | 0.047 |
| `generator_id=2` | A7 - A4 | 0.089 | [-0.157, 0.335] | 0.620 |
| `generator_id=3` | A7 - A4 | -0.104 | [-0.421, 0.216] | 0.342 |
| `generator_id=4` | A7 - A4 | -0.185 | [-0.477, 0.119] | 0.177 |
| `generator_id=5` | A7 - A4 | 0.028 | [-0.404, 0.424] | 0.480 |

## Gate weights (A7)

Mean softmax weights over the test split, by claim type and by generator. Both columns should sum to 1 per cell.

| claim type | w_cross g0 | w_cross g1 | w_cross g2 | w_cross g3 | w_cross g4 | w_cross g5 |
|---|---|---|---|---|---|---|
| abstractive | 0.353 | 0.471 | 0.301 | 0.343 | 0.278 | 0.460 |
| entity | 0.428 | 0.516 | 0.461 | 0.420 | 0.418 | 0.576 |
| extractive | 0.369 | 0.428 | 0.357 | 0.365 | nan | 0.278 |
| numeric | 0.465 | 0.432 | 0.491 | 0.472 | 0.427 | 0.514 |

## Leave-one-generator-out (UNK cold start)

Each generator is removed from train and val, relabelled `UNK` in test, and scored on the UNK rows only. `seen_auroc` is the rest of the test set.

| held out | variant | n UNK | UNK AUROC | 95% CI | seen AUROC | in train? |
|---|---|---:|---:|---|---:|---|
| 0 | A0 | 27 | - | 0.715 | False |
| 0 | A7 | 27 | - | 0.694 | False |
| 1 | A0 | 27 | 0.846 [0.710, 0.962] | 0.711 | False |
| 1 | A7 | 27 | 0.692 [0.500, 0.840] | 0.688 | False |
| 2 | A0 | 27 | 0.614 [0.381, 0.834] | 0.800 | False |
| 2 | A7 | 27 | 0.593 [0.389, 0.802] | 0.765 | False |
| 3 | A0 | 27 | 0.663 [0.327, 0.964] | 0.711 | False |
| 3 | A7 | 27 | 0.728 [0.489, 0.959] | 0.704 | False |
| 4 | A0 | 27 | 0.583 [0.040, 0.923] | 0.679 | False |
| 4 | A7 | 27 | 0.667 [0.129, 1.000] | 0.702 | False |
| 5 | A0 | 27 | 0.900 [0.731, 1.000] | 0.656 | False |
| 5 | A7 | 27 | 0.900 [0.720, 1.000] | 0.659 | False |

## Cost and latency

Wall clock per run, and API accounting. API calls are zero for every table that was already built; they are non-zero only for tables whose signals came from a live extractor.

| variant | mean train s | mean predict s | API calls | API USD |
|---|---:|---:|---:|---:|
| A0 | 0.01 | 0.001 | 0 | 0.0000 |
| A1 | 0.01 | 0.000 | 0 | 0.0000 |
| A2 | 0.01 | 0.001 | 0 | 0.0000 |
| A3 | 0.40 | 0.001 | 0 | 0.0000 |
| A4 | 0.53 | 0.005 | 0 | 0.0000 |
| A5 | 1.93 | 0.002 | 0 | 0.0000 |
| A6 | 0.49 | 0.002 | 0 | 0.0000 |
| A7 | 0.65 | 0.001 | 0 | 0.0000 |
| A8 | 0.00 | 0.000 | 0 | 0.0000 |

## Variant glossary

| id | name | purpose |
|---|---|---|
| A0 | Flat LR on 6 signals | naive fusion baseline the project must beat |
| A1 | Cross-model only (LR) | BEACON-style |
| A2 | Evidence only (LR) | Medico-style |
| A3 | Static learned alpha blend | Rowen-style; tests conditioning vs learning |
| A4 | Flat GBM on 6 signals + metadata | critical control for metadata leakage; report honestly |
| A5 | Gate on claim type only | isolates claim-type contribution |
| A6 | Gate on generator only | isolates generator contribution |
| A7 | Full RC-Gate | proposed method |
| A8 | Naive majority vote | skipped unless judge votes are in the table |

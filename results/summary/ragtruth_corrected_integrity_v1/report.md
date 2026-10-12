# RC-Gate results -- ragtruth

- generated: 2026-10-09 00:52
- git: `4709001`
- config: `ragtruth_corrected_integrity_v1.yaml`
- signal table: `/Users/nishant/Documents/GitHub/RCGate/data/signal_tables/ragtruth_corrected_integrity_v1_s0.parquet`
- seeds: 3; bootstrap resamples: 1000 per slice per seed
- total wall clock: 12s

## Overall

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `all` | 160 | 0.667 | 0.667 ± 0.063 | 0.222 | 0.129 | 0.835 | 0.051 |
| A1 | `all` | 160 | 0.702 | 0.702 ± 0.076 | 0.197 | 0.121 | 0.648 | 0.048 |
| A2 | `all` | 160 | 0.563 | 0.563 ± 0.067 | 0.168 | 0.099 | 0.688 | 0.042 |
| A3 | `all` | 160 | 0.621 | 0.621 ± 0.083 | 0.196 | 0.118 | 0.672 | 0.038 |
| A4 | `all` | 160 | 0.706 | 0.706 ± 0.106 | 0.251 | 0.240 | 0.268 | 0.105 |
| A5 | `all` | 160 | 0.698 | 0.698 ± 0.011 | 0.188 | 0.127 | 0.392 | 0.210 |
| A6 | `all` | 160 | 0.549 | 0.549 ± 0.097 | 0.175 | 0.120 | 0.594 | 0.182 |
| A7 | `all` | 160 | 0.638 | 0.638 ± 0.100 | 0.209 | 0.127 | 0.683 | 0.244 |

## Per benchmark

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `benchmark=ragtruth` | 160 | 0.667 | 0.667 ± 0.063 | 0.222 | 0.129 | 0.835 | 0.051 |
| A1 | `benchmark=ragtruth` | 160 | 0.702 | 0.702 ± 0.076 | 0.197 | 0.121 | 0.648 | 0.048 |
| A2 | `benchmark=ragtruth` | 160 | 0.563 | 0.563 ± 0.067 | 0.168 | 0.099 | 0.688 | 0.042 |
| A3 | `benchmark=ragtruth` | 160 | 0.621 | 0.621 ± 0.083 | 0.196 | 0.118 | 0.672 | 0.038 |
| A4 | `benchmark=ragtruth` | 160 | 0.706 | 0.706 ± 0.106 | 0.251 | 0.240 | 0.268 | 0.105 |
| A5 | `benchmark=ragtruth` | 160 | 0.698 | 0.698 ± 0.011 | 0.188 | 0.127 | 0.392 | 0.210 |
| A6 | `benchmark=ragtruth` | 160 | 0.549 | 0.549 ± 0.097 | 0.175 | 0.120 | 0.594 | 0.182 |
| A7 | `benchmark=ragtruth` | 160 | 0.638 | 0.638 ± 0.100 | 0.209 | 0.127 | 0.683 | 0.244 |

## Per claim type

Claim types: 0 numeric, 1 entity, 2 extractive, 3 abstractive. The proposal's "numeric/extractive" reporting group is types 0 and 2.

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `claim_type=0` | 49 | 0.539 | 0.539 ± 0.158 | 0.257 | 0.159 | 0.767 | 0.115 |
| A0 | `claim_type=1` | 37 | 0.676 | 0.676 ± 0.081 | 0.134 | 0.073 | 0.889 | 0.047 |
| A0 | `claim_type=2` | 31 | 0.743 | 0.743 ± 0.174 | 0.225 | 0.128 | 1.000 | 0.068 |
| A0 | `claim_type=3` | 43 | 0.872 | 0.872 ± 0.092 | 0.234 | 0.137 | 1.000 | 0.057 |
| A1 | `claim_type=0` | 49 | 0.561 | 0.561 ± 0.205 | 0.241 | 0.160 | 0.673 | 0.116 |
| A1 | `claim_type=1` | 37 | 0.715 | 0.715 ± 0.150 | 0.137 | 0.079 | 0.722 | 0.028 |
| A1 | `claim_type=2` | 31 | 0.788 | 0.788 ± 0.189 | 0.175 | 0.103 | 0.600 | 0.055 |
| A1 | `claim_type=3` | 43 | 0.915 | 0.915 ± 0.128 | 0.131 | 0.073 | 0.667 | 0.062 |
| A2 | `claim_type=0` | 49 | 0.526 | 0.526 ± 0.170 | 0.218 | 0.133 | 0.667 | 0.119 |
| A2 | `claim_type=1` | 37 | 0.482 | 0.482 ± 0.058 | 0.072 | 0.039 | 0.667 | 0.030 |
| A2 | `claim_type=2` | 31 | 0.561 | 0.561 ± 0.341 | 0.216 | 0.123 | 1.000 | 0.066 |
| A2 | `claim_type=3` | 43 | 0.771 | 0.771 ± 0.046 | 0.165 | 0.097 | 0.667 | 0.034 |
| A3 | `claim_type=0` | 49 | 0.478 | 0.478 ± 0.143 | 0.239 | 0.154 | 0.673 | 0.114 |
| A3 | `claim_type=1` | 37 | 0.583 | 0.583 ± 0.100 | 0.098 | 0.056 | 0.611 | 0.030 |
| A3 | `claim_type=2` | 31 | 0.756 | 0.756 ± 0.332 | 0.252 | 0.144 | 1.000 | 0.051 |
| A3 | `claim_type=3` | 43 | 0.855 | 0.855 ± 0.111 | 0.165 | 0.097 | 0.667 | 0.040 |
| A4 | `claim_type=0` | 49 | 0.642 | 0.642 ± 0.119 | 0.349 | 0.442 | 0.385 | 0.201 |
| A4 | `claim_type=1` | 37 | 0.803 | 0.803 ± 0.147 | 0.241 | 0.222 | 0.278 | 0.055 |
| A4 | `claim_type=2` | 31 | 0.569 | 0.569 ± 0.119 | 0.000 | 0.000 | 0.000 | 0.079 |
| A4 | `claim_type=3` | 43 | 0.854 | 0.854 ± 0.055 | 0.167 | 0.333 | 0.111 | 0.056 |
| A5 | `claim_type=0` | 49 | 0.555 | 0.555 ± 0.260 | 0.267 | 0.184 | 0.645 | 0.202 |
| A5 | `claim_type=1` | 37 | 0.687 | 0.687 ± 0.134 | 0.061 | 0.035 | 0.222 | 0.202 |
| A5 | `claim_type=2` | 31 | 0.613 | 0.613 ± 0.101 | 0.033 | 0.019 | 0.167 | 0.226 |
| A5 | `claim_type=3` | 43 | 0.929 | 0.929 ± 0.094 | 0.000 | 0.000 | 0.000 | 0.232 |
| A6 | `claim_type=0` | 49 | 0.434 | 0.434 ± 0.073 | 0.221 | 0.139 | 0.542 | 0.133 |
| A6 | `claim_type=1` | 37 | 0.603 | 0.603 ± 0.115 | 0.077 | 0.042 | 0.556 | 0.228 |
| A6 | `claim_type=2` | 31 | 0.453 | 0.453 ± 0.310 | 0.143 | 0.351 | 0.233 | 0.195 |
| A6 | `claim_type=3` | 43 | 0.858 | 0.858 ± 0.141 | 0.135 | 0.077 | 0.889 | 0.230 |
| A7 | `claim_type=0` | 49 | 0.408 | 0.408 ± 0.066 | 0.240 | 0.149 | 0.636 | 0.210 |
| A7 | `claim_type=1` | 37 | 0.609 | 0.609 ± 0.240 | 0.171 | 0.103 | 0.833 | 0.272 |
| A7 | `claim_type=2` | 31 | 0.582 | 0.582 ± 0.281 | 0.150 | 0.086 | 0.600 | 0.238 |
| A7 | `claim_type=3` | 43 | 0.819 | 0.819 ± 0.250 | 0.102 | 0.056 | 0.667 | 0.289 |

## Per generator

`UNK` (-1) only appears in the leave-one-generator-out table below.

| variant | generator | n | AUROC (95% CI) | AUROC mean ± sd | F1 | ECE |
|---|---|---:|---|---|---:|---:|
| A0 | 0 | 27 | - | - | 0.000 | 0.063 |
| A0 | 1 | 27 | 0.816 | 0.816 ± 0.163 | 0.177 | 0.031 |
| A0 | 2 | 26 | 0.556 | 0.556 ± 0.020 | 0.373 | 0.167 |
| A0 | 3 | 26 | 0.603 | 0.603 ± 0.137 | 0.249 | 0.093 |
| A0 | 4 | 26 | 0.692 | 0.692 ± 0.205 | 0.211 | 0.073 |
| A0 | 5 | 26 | 0.798 | 0.798 ± 0.139 | 0.209 | 0.060 |
| A1 | 0 | 27 | - | - | 0.000 | 0.065 |
| A1 | 1 | 27 | 0.808 | 0.808 ± 0.269 | 0.083 | 0.034 |
| A1 | 2 | 26 | 0.679 | 0.679 ± 0.047 | 0.341 | 0.159 |
| A1 | 3 | 26 | 0.645 | 0.645 ± 0.207 | 0.179 | 0.118 |
| A1 | 4 | 26 | 0.726 | 0.726 ± 0.221 | 0.246 | 0.063 |
| A1 | 5 | 26 | 0.816 | 0.816 ± 0.073 | 0.213 | 0.062 |
| A2 | 0 | 27 | - | - | 0.000 | 0.060 |
| A2 | 1 | 27 | 0.694 | 0.694 ± 0.277 | 0.186 | 0.038 |
| A2 | 2 | 26 | 0.436 | 0.436 ± 0.064 | 0.276 | 0.163 |
| A2 | 3 | 26 | 0.537 | 0.537 ± 0.065 | 0.167 | 0.087 |
| A2 | 4 | 26 | 0.638 | 0.638 ± 0.231 | 0.195 | 0.064 |
| A2 | 5 | 26 | 0.627 | 0.627 ± 0.182 | 0.116 | 0.050 |
| A3 | 0 | 27 | - | - | 0.000 | 0.060 |
| A3 | 1 | 27 | 0.873 | 0.873 ± 0.219 | 0.190 | 0.029 |
| A3 | 2 | 26 | 0.529 | 0.529 ± 0.116 | 0.255 | 0.151 |
| A3 | 3 | 26 | 0.577 | 0.577 ± 0.132 | 0.214 | 0.093 |
| A3 | 4 | 26 | 0.643 | 0.643 ± 0.098 | 0.248 | 0.038 |
| A3 | 5 | 26 | 0.689 | 0.689 ± 0.166 | 0.200 | 0.050 |
| A4 | 0 | 27 | - | - | 0.000 | 0.000 |
| A4 | 1 | 27 | 0.738 | 0.738 ± 0.120 | 0.000 | 0.049 |
| A4 | 2 | 26 | 0.524 | 0.524 ± 0.246 | 0.244 | 0.219 |
| A4 | 3 | 26 | 0.541 | 0.541 ± 0.110 | 0.222 | 0.168 |
| A4 | 4 | 26 | 0.880 | 0.880 ± 0.035 | 0.222 | 0.105 |
| A4 | 5 | 26 | 0.717 | 0.717 ± 0.145 | 0.378 | 0.095 |
| A5 | 0 | 27 | - | - | 0.000 | 0.247 |
| A5 | 1 | 27 | 0.627 | 0.627 ± 0.292 | 0.051 | 0.217 |
| A5 | 2 | 26 | 0.685 | 0.685 ± 0.064 | 0.315 | 0.209 |
| A5 | 3 | 26 | 0.488 | 0.488 ± 0.062 | 0.171 | 0.225 |
| A5 | 4 | 26 | 0.726 | 0.726 ± 0.151 | 0.222 | 0.223 |
| A5 | 5 | 26 | 0.785 | 0.785 ± 0.025 | 0.195 | 0.222 |
| A6 | 0 | 27 | - | - | 0.000 | 0.281 |
| A6 | 1 | 27 | 0.224 | 0.224 ± 0.191 | 0.000 | 0.225 |
| A6 | 2 | 26 | 0.598 | 0.598 ± 0.087 | 0.352 | 0.110 |
| A6 | 3 | 26 | 0.545 | 0.545 ± 0.136 | 0.309 | 0.172 |
| A6 | 4 | 26 | 0.371 | 0.371 ± 0.076 | 0.114 | 0.187 |
| A6 | 5 | 26 | 0.625 | 0.625 ± 0.271 | 0.103 | 0.192 |
| A7 | 0 | 27 | - | - | 0.000 | 0.310 |
| A7 | 1 | 27 | 0.355 | 0.355 ± 0.329 | 0.073 | 0.267 |
| A7 | 2 | 26 | 0.635 | 0.635 ± 0.072 | 0.364 | 0.188 |
| A7 | 3 | 26 | 0.548 | 0.548 ± 0.136 | 0.186 | 0.246 |
| A7 | 4 | 26 | 0.638 | 0.638 ± 0.139 | 0.164 | 0.240 |
| A7 | 5 | 26 | 0.709 | 0.709 ± 0.146 | 0.268 | 0.275 |

## Per (claim type, generator) cell

Point estimates only; bootstrap CIs are not computed for 20 cells x 3 seeds.

| variant | cell | n | AUROC mean ± sd |
|---|---|---:|---|
| A0 | `abstractive|0` | 9 | - |
| A0 | `abstractive|1` | 8 | - |
| A0 | `abstractive|2` | 6 | 0.500 ± 0.000 |
| A0 | `abstractive|3` | 2 | 0.500 ± 0.707 |
| A0 | `abstractive|4` | 9 | 1.000 |
| A0 | `abstractive|5` | 7 | 0.944 ± 0.079 |
| A0 | `entity|0` | 5 | - |
| A0 | `entity|1` | 6 | - |
| A0 | `entity|2` | 7 | 0.611 ± 0.157 |
| A0 | `entity|3` | 5 | - |
| A0 | `entity|4` | 6 | 0.417 ± 0.118 |
| A0 | `entity|5` | 5 | - |
| A0 | `extractive|0` | 9 | - |
| A0 | `extractive|1` | 8 | 0.848 ± 0.156 |
| A0 | `extractive|2` | 4 | 0.500 |
| A0 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A0 | `extractive|5` | 6 | - |
| A0 | `numeric|0` | 2 | - |
| A0 | `numeric|1` | 3 | - |
| A0 | `numeric|2` | 8 | 0.518 ± 0.085 |
| A0 | `numeric|3` | 16 | 0.667 ± 0.333 |
| A0 | `numeric|4` | 10 | 0.476 ± 0.152 |
| A0 | `numeric|5` | 8 | 0.722 ± 0.293 |
| A1 | `abstractive|0` | 9 | - |
| A1 | `abstractive|1` | 8 | - |
| A1 | `abstractive|2` | 6 | 0.875 ± 0.177 |
| A1 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A1 | `abstractive|4` | 9 | 1.000 |
| A1 | `abstractive|5` | 7 | 0.889 ± 0.157 |
| A1 | `entity|0` | 5 | - |
| A1 | `entity|1` | 6 | - |
| A1 | `entity|2` | 7 | 0.667 ± 0.000 |
| A1 | `entity|3` | 5 | - |
| A1 | `entity|4` | 6 | 0.750 ± 0.354 |
| A1 | `entity|5` | 5 | - |
| A1 | `extractive|0` | 9 | - |
| A1 | `extractive|1` | 8 | 0.812 ± 0.325 |
| A1 | `extractive|2` | 4 | 1.000 |
| A1 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A1 | `extractive|5` | 6 | - |
| A1 | `numeric|0` | 2 | - |
| A1 | `numeric|1` | 3 | - |
| A1 | `numeric|2` | 8 | 0.454 ± 0.185 |
| A1 | `numeric|3` | 16 | 0.569 ± 0.341 |
| A1 | `numeric|4` | 10 | 0.515 ± 0.299 |
| A1 | `numeric|5` | 8 | 0.736 ± 0.120 |
| A2 | `abstractive|0` | 9 | - |
| A2 | `abstractive|1` | 8 | - |
| A2 | `abstractive|2` | 6 | 0.375 ± 0.177 |
| A2 | `abstractive|3` | 2 | 0.250 ± 0.354 |
| A2 | `abstractive|4` | 9 | 1.000 |
| A2 | `abstractive|5` | 7 | 0.819 ± 0.098 |
| A2 | `entity|0` | 5 | - |
| A2 | `entity|1` | 6 | - |
| A2 | `entity|2` | 7 | 0.694 ± 0.196 |
| A2 | `entity|3` | 5 | - |
| A2 | `entity|4` | 6 | 0.250 ± 0.118 |
| A2 | `entity|5` | 5 | - |
| A2 | `extractive|0` | 9 | - |
| A2 | `extractive|1` | 8 | 0.637 ± 0.357 |
| A2 | `extractive|2` | 4 | 0.000 |
| A2 | `extractive|3` | 3 | 0.167 ± 0.236 |
| A2 | `extractive|5` | 6 | - |
| A2 | `numeric|0` | 2 | - |
| A2 | `numeric|1` | 3 | - |
| A2 | `numeric|2` | 8 | 0.667 ± 0.294 |
| A2 | `numeric|3` | 16 | 0.678 ± 0.233 |
| A2 | `numeric|4` | 10 | 0.439 ± 0.445 |
| A2 | `numeric|5` | 8 | 0.722 ± 0.411 |
| A3 | `abstractive|0` | 9 | - |
| A3 | `abstractive|1` | 8 | - |
| A3 | `abstractive|2` | 6 | 0.375 ± 0.177 |
| A3 | `abstractive|3` | 2 | 0.250 ± 0.354 |
| A3 | `abstractive|4` | 9 | 1.000 |
| A3 | `abstractive|5` | 7 | 0.875 ± 0.177 |
| A3 | `entity|0` | 5 | - |
| A3 | `entity|1` | 6 | - |
| A3 | `entity|2` | 7 | 0.667 ± 0.000 |
| A3 | `entity|3` | 5 | - |
| A3 | `entity|4` | 6 | 0.417 ± 0.118 |
| A3 | `entity|5` | 5 | - |
| A3 | `extractive|0` | 9 | - |
| A3 | `extractive|1` | 8 | 0.875 ± 0.217 |
| A3 | `extractive|2` | 4 | 0.000 |
| A3 | `extractive|3` | 3 | 0.333 ± 0.471 |
| A3 | `extractive|5` | 6 | - |
| A3 | `numeric|0` | 2 | - |
| A3 | `numeric|1` | 3 | - |
| A3 | `numeric|2` | 8 | 0.435 ± 0.163 |
| A3 | `numeric|3` | 16 | 0.624 ± 0.269 |
| A3 | `numeric|4` | 10 | 0.306 ± 0.179 |
| A3 | `numeric|5` | 8 | 0.667 ± 0.333 |
| A4 | `abstractive|0` | 9 | - |
| A4 | `abstractive|1` | 8 | - |
| A4 | `abstractive|2` | 6 | 0.625 ± 0.177 |
| A4 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A4 | `abstractive|4` | 9 | 1.000 |
| A4 | `abstractive|5` | 7 | 0.778 ± 0.314 |
| A4 | `entity|0` | 5 | - |
| A4 | `entity|1` | 6 | - |
| A4 | `entity|2` | 7 | 0.861 ± 0.196 |
| A4 | `entity|3` | 5 | - |
| A4 | `entity|4` | 6 | 0.750 ± 0.354 |
| A4 | `entity|5` | 5 | - |
| A4 | `extractive|0` | 9 | - |
| A4 | `extractive|1` | 8 | 0.911 ± 0.078 |
| A4 | `extractive|2` | 4 | 0.250 |
| A4 | `extractive|3` | 3 | 0.000 ± 0.000 |
| A4 | `extractive|5` | 6 | - |
| A4 | `numeric|0` | 2 | - |
| A4 | `numeric|1` | 3 | - |
| A4 | `numeric|2` | 8 | 0.500 ± 0.441 |
| A4 | `numeric|3` | 16 | 0.489 ± 0.127 |
| A4 | `numeric|4` | 10 | 0.858 ± 0.137 |
| A4 | `numeric|5` | 8 | 0.764 ± 0.105 |
| A5 | `abstractive|0` | 9 | - |
| A5 | `abstractive|1` | 8 | - |
| A5 | `abstractive|2` | 6 | 1.000 ± 0.000 |
| A5 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A5 | `abstractive|4` | 9 | 1.000 |
| A5 | `abstractive|5` | 7 | 1.000 ± 0.000 |
| A5 | `entity|0` | 5 | - |
| A5 | `entity|1` | 6 | - |
| A5 | `entity|2` | 7 | 0.694 ± 0.039 |
| A5 | `entity|3` | 5 | - |
| A5 | `entity|4` | 6 | 0.833 ± 0.236 |
| A5 | `entity|5` | 5 | - |
| A5 | `extractive|0` | 9 | - |
| A5 | `extractive|1` | 8 | 0.646 ± 0.308 |
| A5 | `extractive|2` | 4 | 1.000 |
| A5 | `extractive|3` | 3 | 0.667 ± 0.471 |
| A5 | `extractive|5` | 6 | - |
| A5 | `numeric|0` | 2 | - |
| A5 | `numeric|1` | 3 | - |
| A5 | `numeric|2` | 8 | 0.546 ± 0.185 |
| A5 | `numeric|3` | 16 | 0.538 ± 0.329 |
| A5 | `numeric|4` | 10 | 0.540 ± 0.468 |
| A5 | `numeric|5` | 8 | 0.750 ± 0.250 |
| A6 | `abstractive|0` | 9 | - |
| A6 | `abstractive|1` | 8 | - |
| A6 | `abstractive|2` | 6 | 0.750 ± 0.354 |
| A6 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A6 | `abstractive|4` | 9 | 1.000 |
| A6 | `abstractive|5` | 7 | 0.833 ± 0.236 |
| A6 | `entity|0` | 5 | - |
| A6 | `entity|1` | 6 | - |
| A6 | `entity|2` | 7 | 0.472 ± 0.196 |
| A6 | `entity|3` | 5 | - |
| A6 | `entity|4` | 6 | 0.667 ± 0.000 |
| A6 | `entity|5` | 5 | - |
| A6 | `extractive|0` | 9 | - |
| A6 | `extractive|1` | 8 | 0.249 ± 0.164 |
| A6 | `extractive|2` | 4 | 1.000 |
| A6 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A6 | `extractive|5` | 6 | - |
| A6 | `numeric|0` | 2 | - |
| A6 | `numeric|1` | 3 | - |
| A6 | `numeric|2` | 8 | 0.481 ± 0.032 |
| A6 | `numeric|3` | 16 | 0.243 ± 0.225 |
| A6 | `numeric|4` | 10 | 0.274 ± 0.205 |
| A6 | `numeric|5` | 8 | 0.556 ± 0.268 |
| A7 | `abstractive|0` | 9 | - |
| A7 | `abstractive|1` | 8 | - |
| A7 | `abstractive|2` | 6 | 0.875 ± 0.177 |
| A7 | `abstractive|3` | 2 | 1.000 ± 0.000 |
| A7 | `abstractive|4` | 9 | 1.000 |
| A7 | `abstractive|5` | 7 | 0.875 ± 0.177 |
| A7 | `entity|0` | 5 | - |
| A7 | `entity|1` | 6 | - |
| A7 | `entity|2` | 7 | 0.750 ± 0.118 |
| A7 | `entity|3` | 5 | - |
| A7 | `entity|4` | 6 | 0.667 ± 0.000 |
| A7 | `entity|5` | 5 | - |
| A7 | `extractive|0` | 9 | - |
| A7 | `extractive|1` | 8 | 0.404 ± 0.393 |
| A7 | `extractive|2` | 4 | 1.000 |
| A7 | `extractive|3` | 3 | 0.833 ± 0.236 |
| A7 | `extractive|5` | 6 | - |
| A7 | `numeric|0` | 2 | - |
| A7 | `numeric|1` | 3 | - |
| A7 | `numeric|2` | 8 | 0.518 ± 0.085 |
| A7 | `numeric|3` | 16 | 0.265 ± 0.314 |
| A7 | `numeric|4` | 10 | 0.372 ± 0.244 |
| A7 | `numeric|5` | 8 | 0.472 ± 0.210 |

## H2 test: A7 minus baseline, paired bootstrap

Both models are scored on the *same* test rows, so this is a paired comparison and much tighter than differencing two separate CIs. `p_gt_0` is the bootstrap fraction of resamples favouring A7.

| slice | comparison | ΔAUROC | 95% CI | p_gt_0 |
|---|---|---:|---|---:|
| `all` | A7 - A0 | -0.029 | [-0.187, 0.132] | 0.399 |
| `benchmark=ragtruth` | A7 - A0 | -0.029 | [-0.187, 0.132] | 0.399 |
| `claim_type=0` | A7 - A0 | -0.131 | [-0.406, 0.171] | 0.325 |
| `claim_type=1` | A7 - A0 | -0.067 | [-0.288, 0.177] | 0.400 |
| `claim_type=2` | A7 - A0 | -0.162 | [-0.363, 0.036] | 0.236 |
| `claim_type=3` | A7 - A0 | -0.053 | [-0.209, 0.109] | 0.390 |
| `generator_id=0` | A7 - A0 | - | [-, -] | - |
| `generator_id=1` | A7 - A0 | -0.461 | [-0.631, -0.244] | 0.000 |
| `generator_id=2` | A7 - A0 | 0.079 | [-0.208, 0.340] | 0.606 |
| `generator_id=3` | A7 - A0 | -0.054 | [-0.547, 0.342] | 0.325 |
| `generator_id=4` | A7 - A0 | -0.054 | [-0.479, 0.392] | 0.356 |
| `generator_id=5` | A7 - A0 | -0.089 | [-0.425, 0.251] | 0.323 |
| `all` | A7 - A1 | -0.064 | [-0.204, 0.081] | 0.390 |
| `benchmark=ragtruth` | A7 - A1 | -0.064 | [-0.204, 0.081] | 0.390 |
| `claim_type=0` | A7 - A1 | -0.152 | [-0.371, 0.074] | 0.307 |
| `claim_type=1` | A7 - A1 | -0.106 | [-0.288, 0.100] | 0.478 |
| `claim_type=2` | A7 - A1 | -0.206 | [-0.430, 0.018] | 0.221 |
| `claim_type=3` | A7 - A1 | -0.096 | [-0.238, 0.037] | 0.385 |
| `generator_id=0` | A7 - A1 | - | [-, -] | - |
| `generator_id=1` | A7 - A1 | -0.452 | [-0.672, -0.243] | 0.015 |
| `generator_id=2` | A7 - A1 | -0.044 | [-0.287, 0.194] | 0.327 |
| `generator_id=3` | A7 - A1 | -0.097 | [-0.581, 0.276] | 0.333 |
| `generator_id=4` | A7 - A1 | -0.088 | [-0.429, 0.260] | 0.410 |
| `generator_id=5` | A7 - A1 | -0.107 | [-0.435, 0.211] | 0.302 |
| `all` | A7 - A2 | 0.074 | [-0.128, 0.265] | 0.741 |
| `benchmark=ragtruth` | A7 - A2 | 0.074 | [-0.128, 0.265] | 0.741 |
| `claim_type=0` | A7 - A2 | -0.118 | [-0.454, 0.270] | 0.319 |
| `claim_type=1` | A7 - A2 | 0.127 | [-0.123, 0.411] | 0.678 |
| `claim_type=2` | A7 - A2 | 0.020 | [-0.321, 0.367] | 0.599 |
| `claim_type=3` | A7 - A2 | 0.048 | [-0.115, 0.224] | 0.684 |
| `generator_id=0` | A7 - A2 | - | [-, -] | - |
| `generator_id=1` | A7 - A2 | -0.338 | [-0.641, 0.027] | 0.401 |
| `generator_id=2` | A7 - A2 | 0.199 | [-0.181, 0.546] | 0.784 |
| `generator_id=3` | A7 - A2 | 0.011 | [-0.529, 0.439] | 0.467 |
| `generator_id=4` | A7 - A2 | 0.000 | [-0.428, 0.459] | 0.499 |
| `generator_id=5` | A7 - A2 | 0.082 | [-0.362, 0.507] | 0.545 |
| `all` | A7 - A3 | 0.017 | [-0.173, 0.212] | 0.525 |
| `benchmark=ragtruth` | A7 - A3 | 0.017 | [-0.173, 0.212] | 0.525 |
| `claim_type=0` | A7 - A3 | -0.070 | [-0.387, 0.299] | 0.496 |
| `claim_type=1` | A7 - A3 | 0.026 | [-0.202, 0.269] | 0.557 |
| `claim_type=2` | A7 - A3 | -0.174 | [-0.504, 0.146] | 0.266 |
| `claim_type=3` | A7 - A3 | -0.035 | [-0.195, 0.130] | 0.401 |
| `generator_id=0` | A7 - A3 | - | [-, -] | - |
| `generator_id=1` | A7 - A3 | -0.518 | [-0.808, -0.165] | 0.074 |
| `generator_id=2` | A7 - A3 | 0.106 | [-0.248, 0.438] | 0.585 |
| `generator_id=3` | A7 - A3 | -0.029 | [-0.596, 0.435] | 0.359 |
| `generator_id=4` | A7 - A3 | -0.005 | [-0.451, 0.453] | 0.498 |
| `generator_id=5` | A7 - A3 | 0.020 | [-0.414, 0.453] | 0.439 |
| `all` | A7 - A4 | -0.068 | [-0.234, 0.113] | 0.208 |
| `benchmark=ragtruth` | A7 - A4 | -0.068 | [-0.234, 0.113] | 0.208 |
| `claim_type=0` | A7 - A4 | -0.233 | [-0.475, 0.011] | 0.044 |
| `claim_type=1` | A7 - A4 | -0.194 | [-0.438, 0.085] | 0.116 |
| `claim_type=2` | A7 - A4 | 0.013 | [-0.359, 0.413] | 0.534 |
| `claim_type=3` | A7 - A4 | -0.034 | [-0.195, 0.199] | 0.585 |
| `generator_id=0` | A7 - A4 | - | [-, -] | - |
| `generator_id=1` | A7 - A4 | -0.383 | [-0.578, -0.160] | 0.032 |
| `generator_id=2` | A7 - A4 | 0.111 | [-0.159, 0.358] | 0.604 |
| `generator_id=3` | A7 - A4 | 0.007 | [-0.463, 0.483] | 0.460 |
| `generator_id=4` | A7 - A4 | -0.243 | [-0.554, 0.051] | 0.066 |
| `generator_id=5` | A7 - A4 | -0.008 | [-0.389, 0.383] | 0.434 |

## Gate weights (A7)

Mean softmax weights over the test split, by claim type and by generator. Both columns should sum to 1 per cell.

| claim type | w_cross g0 | w_cross g1 | w_cross g2 | w_cross g3 | w_cross g4 | w_cross g5 |
|---|---|---|---|---|---|---|
| abstractive | 0.338 | 0.469 | 0.319 | 0.354 | 0.272 | 0.460 |
| entity | 0.418 | 0.509 | 0.514 | 0.416 | 0.421 | 0.551 |
| extractive | 0.368 | 0.428 | 0.376 | 0.361 | nan | 0.276 |
| numeric | 0.461 | 0.432 | 0.489 | 0.476 | 0.434 | 0.514 |

## Leave-one-generator-out (UNK cold start)

Each generator is removed from train and val, relabelled `UNK` in test, and scored on the UNK rows only. `seen_auroc` is the rest of the test set.

| held out | variant | n UNK | UNK AUROC | 95% CI | seen AUROC | in train? |
|---|---|---:|---:|---|---:|---|
| 0 | A0 | 27 | - | 0.713 | False |
| 0 | A7 | 27 | - | 0.682 | False |
| 1 | A0 | 27 | 0.846 [0.710, 0.962] | 0.710 | False |
| 1 | A7 | 27 | 0.731 [0.560, 0.885] | 0.681 | False |
| 2 | A0 | 27 | 0.629 [0.400, 0.834] | 0.776 | False |
| 2 | A7 | 27 | 0.579 [0.369, 0.772] | 0.746 | False |
| 3 | A0 | 27 | 0.620 [0.271, 0.927] | 0.735 | False |
| 3 | A7 | 27 | 0.598 [0.337, 0.907] | 0.709 | False |
| 4 | A0 | 27 | 0.708 [0.389, 0.923] | 0.686 | False |
| 4 | A7 | 27 | 0.653 [0.129, 0.962] | 0.685 | False |
| 5 | A0 | 27 | 0.900 [0.731, 1.000] | 0.671 | False |
| 5 | A7 | 27 | 0.840 [0.671, 0.973] | 0.663 | False |

## Cost and latency

Wall clock per run, and API accounting. API calls are zero for every table that was already built; they are non-zero only for tables whose signals came from a live extractor.

| variant | mean train s | mean predict s | API calls | API USD |
|---|---:|---:|---:|---:|
| A0 | 0.00 | 0.000 | 0 | 0.0000 |
| A1 | 0.00 | 0.000 | 0 | 0.0000 |
| A2 | 0.00 | 0.000 | 0 | 0.0000 |
| A3 | 0.12 | 0.000 | 0 | 0.0000 |
| A4 | 0.43 | 0.005 | 0 | 0.0000 |
| A5 | 0.35 | 0.001 | 0 | 0.0000 |
| A6 | 0.08 | 0.001 | 0 | 0.0000 |
| A7 | 0.13 | 0.001 | 0 | 0.0000 |
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

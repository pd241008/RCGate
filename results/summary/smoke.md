# RC-Gate results -- synthetic

> **SYNTHETIC DATA.** These numbers validate the machinery on data with known planted signal reliability. They are not evidence for or against H1-H3, which are claims about real model outputs. Every table and plot from this run must be labelled synthetic (constraint C8).

- generated: 2026-10-25 14:23
- git: `ee8ffb7`
- config: `smoke.yaml`
- signal table: `/root/workspace/workspace/03-Code/Projects/Legacy/RCgate/data/signal_tables/smoke.parquet`
- seeds: 1; bootstrap resamples: 100 per slice per seed
- total wall clock: 10s

## Overall

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `all` | 534 | 0.963 | 0.963 | 0.933 | 0.936 | 0.931 | 0.035 |
| A1 | `all` | 534 | 0.857 | 0.857 | 0.744 | 0.845 | 0.665 | 0.053 |
| A2 | `all` | 534 | 0.955 | 0.955 | 0.891 | 0.889 | 0.894 | 0.033 |
| A3 | `all` | 534 | 0.960 | 0.960 | 0.928 | 0.926 | 0.931 | 0.031 |
| A4 | `all` | 534 | 0.958 | 0.958 | 0.924 | 0.940 | 0.910 | 0.043 |
| A5 | `all` | 534 | 0.463 | 0.463 | 0.511 | 0.351 | 0.936 | 0.019 |
| A6 | `all` | 534 | 0.947 | 0.947 | 0.872 | 0.894 | 0.851 | 0.195 |
| A7 | `all` | 534 | 0.784 | 0.784 | 0.641 | 0.522 | 0.830 | 0.003 |

## Per benchmark

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `benchmark=synthetic` | 534 | 0.963 | 0.963 | 0.933 | 0.936 | 0.931 | 0.035 |
| A1 | `benchmark=synthetic` | 534 | 0.857 | 0.857 | 0.744 | 0.845 | 0.665 | 0.053 |
| A2 | `benchmark=synthetic` | 534 | 0.955 | 0.955 | 0.891 | 0.889 | 0.894 | 0.033 |
| A3 | `benchmark=synthetic` | 534 | 0.960 | 0.960 | 0.928 | 0.926 | 0.931 | 0.031 |
| A4 | `benchmark=synthetic` | 534 | 0.958 | 0.958 | 0.924 | 0.940 | 0.910 | 0.043 |
| A5 | `benchmark=synthetic` | 534 | 0.463 | 0.463 | 0.511 | 0.351 | 0.936 | 0.019 |
| A6 | `benchmark=synthetic` | 534 | 0.947 | 0.947 | 0.872 | 0.894 | 0.851 | 0.195 |
| A7 | `benchmark=synthetic` | 534 | 0.784 | 0.784 | 0.641 | 0.522 | 0.830 | 0.003 |

## Per claim type

Claim types: 0 numeric, 1 entity, 2 extractive, 3 abstractive. The proposal's "numeric/extractive" reporting group is types 0 and 2.

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `claim_type=0` | 127 | 0.975 | 0.975 | 0.946 | 0.936 | 0.957 | 0.039 |
| A0 | `claim_type=1` | 146 | 0.958 | 0.958 | 0.947 | 0.957 | 0.938 | 0.019 |
| A0 | `claim_type=2` | 135 | 0.968 | 0.968 | 0.948 | 0.965 | 0.932 | 0.034 |
| A0 | `claim_type=3` | 126 | 0.952 | 0.952 | 0.873 | 0.861 | 0.886 | 0.104 |
| A1 | `claim_type=0` | 127 | 0.589 | 0.589 | 0.271 | 0.615 | 0.174 | 0.186 |
| A1 | `claim_type=1` | 146 | 0.963 | 0.963 | 0.928 | 0.918 | 0.938 | 0.089 |
| A1 | `claim_type=2` | 135 | 0.882 | 0.882 | 0.789 | 0.860 | 0.729 | 0.112 |
| A1 | `claim_type=3` | 126 | 0.929 | 0.929 | 0.817 | 0.806 | 0.829 | 0.140 |
| A2 | `claim_type=0` | 127 | 0.969 | 0.969 | 0.936 | 0.917 | 0.957 | 0.027 |
| A2 | `claim_type=1` | 146 | 0.958 | 0.958 | 0.926 | 0.936 | 0.917 | 0.070 |
| A2 | `claim_type=2` | 135 | 0.963 | 0.963 | 0.948 | 0.965 | 0.932 | 0.045 |
| A2 | `claim_type=3` | 126 | 0.900 | 0.900 | 0.694 | 0.676 | 0.714 | 0.069 |
| A3 | `claim_type=0` | 127 | 0.969 | 0.969 | 0.946 | 0.936 | 0.957 | 0.036 |
| A3 | `claim_type=1` | 146 | 0.961 | 0.961 | 0.947 | 0.957 | 0.938 | 0.020 |
| A3 | `claim_type=2` | 135 | 0.963 | 0.963 | 0.948 | 0.965 | 0.932 | 0.044 |
| A3 | `claim_type=3` | 126 | 0.943 | 0.943 | 0.849 | 0.816 | 0.886 | 0.082 |
| A4 | `claim_type=0` | 127 | 0.971 | 0.971 | 0.945 | 0.956 | 0.935 | 0.037 |
| A4 | `claim_type=1` | 146 | 0.957 | 0.957 | 0.947 | 0.957 | 0.938 | 0.035 |
| A4 | `claim_type=2` | 135 | 0.958 | 0.958 | 0.930 | 0.964 | 0.898 | 0.048 |
| A4 | `claim_type=3` | 126 | 0.935 | 0.935 | 0.857 | 0.857 | 0.857 | 0.070 |
| A5 | `claim_type=0` | 127 | 0.540 | 0.540 | 0.544 | 0.384 | 0.935 | 0.012 |
| A5 | `claim_type=1` | 146 | 0.561 | 0.561 | 0.487 | 0.326 | 0.958 | 0.054 |
| A5 | `claim_type=2` | 135 | 0.307 | 0.307 | 0.582 | 0.423 | 0.932 | 0.098 |
| A5 | `claim_type=3` | 126 | 0.406 | 0.406 | 0.418 | 0.271 | 0.914 | 0.094 |
| A6 | `claim_type=0` | 127 | 0.979 | 0.979 | 0.913 | 0.913 | 0.913 | 0.248 |
| A6 | `claim_type=1` | 146 | 0.946 | 0.946 | 0.901 | 0.954 | 0.854 | 0.128 |
| A6 | `claim_type=2` | 135 | 0.958 | 0.958 | 0.948 | 0.965 | 0.932 | 0.296 |
| A6 | `claim_type=3` | 126 | 0.847 | 0.847 | 0.647 | 0.667 | 0.629 | 0.111 |
| A7 | `claim_type=0` | 127 | 0.863 | 0.863 | 0.762 | 0.842 | 0.696 | 0.014 |
| A7 | `claim_type=1` | 146 | 0.936 | 0.936 | 0.832 | 0.792 | 0.875 | 0.022 |
| A7 | `claim_type=2` | 135 | 0.638 | 0.638 | 0.609 | 0.480 | 0.831 | 0.078 |
| A7 | `claim_type=3` | 126 | 0.792 | 0.792 | 0.468 | 0.311 | 0.943 | 0.083 |

## Per generator

`UNK` (-1) only appears in the leave-one-generator-out table below.

| variant | generator | n | AUROC (95% CI) | AUROC mean ± sd | F1 | ECE |
|---|---|---:|---|---|---:|---:|
| A0 | 0 | 132 | 0.931 | 0.931 | 0.893 | 0.047 |
| A0 | 1 | 143 | 0.947 | 0.947 | 0.919 | 0.040 |
| A0 | 2 | 126 | 0.985 | 0.985 | 0.967 | 0.052 |
| A0 | 3 | 133 | 0.984 | 0.984 | 0.957 | 0.055 |
| A1 | 0 | 132 | 0.797 | 0.797 | 0.690 | 0.124 |
| A1 | 1 | 143 | 0.829 | 0.829 | 0.737 | 0.089 |
| A1 | 2 | 126 | 0.911 | 0.911 | 0.814 | 0.084 |
| A1 | 3 | 133 | 0.894 | 0.894 | 0.736 | 0.070 |
| A2 | 0 | 132 | 0.930 | 0.930 | 0.868 | 0.056 |
| A2 | 1 | 143 | 0.938 | 0.938 | 0.886 | 0.037 |
| A2 | 2 | 126 | 0.972 | 0.972 | 0.899 | 0.061 |
| A2 | 3 | 133 | 0.975 | 0.975 | 0.915 | 0.049 |
| A3 | 0 | 132 | 0.923 | 0.923 | 0.904 | 0.053 |
| A3 | 1 | 143 | 0.945 | 0.945 | 0.921 | 0.047 |
| A3 | 2 | 126 | 0.982 | 0.982 | 0.956 | 0.056 |
| A3 | 3 | 133 | 0.983 | 0.983 | 0.936 | 0.051 |
| A4 | 0 | 132 | 0.914 | 0.914 | 0.893 | 0.080 |
| A4 | 1 | 143 | 0.958 | 0.958 | 0.919 | 0.051 |
| A4 | 2 | 126 | 0.983 | 0.983 | 0.944 | 0.031 |
| A4 | 3 | 133 | 0.981 | 0.981 | 0.945 | 0.032 |
| A5 | 0 | 132 | 0.456 | 0.456 | 0.557 | 0.034 |
| A5 | 1 | 143 | 0.448 | 0.448 | 0.452 | 0.069 |
| A5 | 2 | 126 | 0.447 | 0.447 | 0.542 | 0.024 |
| A5 | 3 | 133 | 0.499 | 0.499 | 0.494 | 0.019 |
| A6 | 0 | 132 | 0.934 | 0.934 | 0.854 | 0.153 |
| A6 | 1 | 143 | 0.918 | 0.918 | 0.861 | 0.220 |
| A6 | 2 | 126 | 0.967 | 0.967 | 0.899 | 0.229 |
| A6 | 3 | 133 | 0.966 | 0.966 | 0.876 | 0.176 |
| A7 | 0 | 132 | 0.753 | 0.753 | 0.641 | 0.036 |
| A7 | 1 | 143 | 0.829 | 0.829 | 0.578 | 0.051 |
| A7 | 2 | 126 | 0.840 | 0.840 | 0.695 | 0.009 |
| A7 | 3 | 133 | 0.821 | 0.821 | 0.661 | 0.001 |

## Per (claim type, generator) cell

Point estimates only; bootstrap CIs are not computed for 20 cells x 1 seeds.

| variant | cell | n | AUROC mean ± sd |
|---|---|---:|---|
| A0 | `abstractive|0` | 25 | 0.818 |
| A0 | `abstractive|1` | 41 | 0.977 |
| A0 | `abstractive|2` | 25 | 1.000 |
| A0 | `abstractive|3` | 35 | 0.991 |
| A0 | `entity|0` | 40 | 0.957 |
| A0 | `entity|1` | 35 | 0.898 |
| A0 | `entity|2` | 33 | 0.989 |
| A0 | `entity|3` | 38 | 0.972 |
| A0 | `extractive|0` | 33 | 0.977 |
| A0 | `extractive|1` | 36 | 0.894 |
| A0 | `extractive|2` | 36 | 0.987 |
| A0 | `extractive|3` | 30 | 1.000 |
| A0 | `numeric|0` | 34 | 0.917 |
| A0 | `numeric|1` | 31 | 1.000 |
| A0 | `numeric|2` | 32 | 0.976 |
| A0 | `numeric|3` | 30 | 1.000 |
| A1 | `abstractive|0` | 25 | 0.706 |
| A1 | `abstractive|1` | 41 | 0.966 |
| A1 | `abstractive|2` | 25 | 1.000 |
| A1 | `abstractive|3` | 35 | 0.968 |
| A1 | `entity|0` | 40 | 0.963 |
| A1 | `entity|1` | 35 | 0.884 |
| A1 | `entity|2` | 33 | 0.981 |
| A1 | `entity|3` | 38 | 0.979 |
| A1 | `extractive|0` | 33 | 0.898 |
| A1 | `extractive|1` | 36 | 0.829 |
| A1 | `extractive|2` | 36 | 0.921 |
| A1 | `extractive|3` | 30 | 0.884 |
| A1 | `numeric|0` | 34 | 0.466 |
| A1 | `numeric|1` | 31 | 0.615 |
| A1 | `numeric|2` | 32 | 0.647 |
| A1 | `numeric|3` | 30 | 0.662 |
| A2 | `abstractive|0` | 25 | 0.818 |
| A2 | `abstractive|1` | 41 | 0.914 |
| A2 | `abstractive|2` | 25 | 0.949 |
| A2 | `abstractive|3` | 35 | 0.917 |
| A2 | `entity|0` | 40 | 0.960 |
| A2 | `entity|1` | 35 | 0.903 |
| A2 | `entity|2` | 33 | 0.993 |
| A2 | `entity|3` | 38 | 0.963 |
| A2 | `extractive|0` | 33 | 0.981 |
| A2 | `extractive|1` | 36 | 0.876 |
| A2 | `extractive|2` | 36 | 0.984 |
| A2 | `extractive|3` | 30 | 1.000 |
| A2 | `numeric|0` | 34 | 0.917 |
| A2 | `numeric|1` | 31 | 1.000 |
| A2 | `numeric|2` | 32 | 0.942 |
| A2 | `numeric|3` | 30 | 0.995 |
| A3 | `abstractive|0` | 25 | 0.786 |
| A3 | `abstractive|1` | 41 | 0.971 |
| A3 | `abstractive|2` | 25 | 1.000 |
| A3 | `abstractive|3` | 35 | 0.972 |
| A3 | `entity|0` | 40 | 0.969 |
| A3 | `entity|1` | 35 | 0.884 |
| A3 | `entity|2` | 33 | 0.989 |
| A3 | `entity|3` | 38 | 0.979 |
| A3 | `extractive|0` | 33 | 0.959 |
| A3 | `extractive|1` | 36 | 0.898 |
| A3 | `extractive|2` | 36 | 0.991 |
| A3 | `extractive|3` | 30 | 0.996 |
| A3 | `numeric|0` | 34 | 0.905 |
| A3 | `numeric|1` | 31 | 1.000 |
| A3 | `numeric|2` | 32 | 0.966 |
| A3 | `numeric|3` | 30 | 0.995 |
| A4 | `abstractive|0` | 25 | 0.825 |
| A4 | `abstractive|1` | 41 | 0.966 |
| A4 | `abstractive|2` | 25 | 1.000 |
| A4 | `abstractive|3` | 35 | 0.986 |
| A4 | `entity|0` | 40 | 0.946 |
| A4 | `entity|1` | 35 | 0.949 |
| A4 | `entity|2` | 33 | 0.974 |
| A4 | `entity|3` | 38 | 0.975 |
| A4 | `extractive|0` | 33 | 0.959 |
| A4 | `extractive|1` | 36 | 0.898 |
| A4 | `extractive|2` | 36 | 0.994 |
| A4 | `extractive|3` | 30 | 1.000 |
| A4 | `numeric|0` | 34 | 0.890 |
| A4 | `numeric|1` | 31 | 1.000 |
| A4 | `numeric|2` | 32 | 0.995 |
| A4 | `numeric|3` | 30 | 1.000 |
| A5 | `abstractive|0` | 25 | 0.405 |
| A5 | `abstractive|1` | 41 | 0.471 |
| A5 | `abstractive|2` | 25 | 0.272 |
| A5 | `abstractive|3` | 35 | 0.412 |
| A5 | `entity|0` | 40 | 0.541 |
| A5 | `entity|1` | 35 | 0.486 |
| A5 | `entity|2` | 33 | 0.526 |
| A5 | `entity|3` | 38 | 0.652 |
| A5 | `extractive|0` | 33 | 0.376 |
| A5 | `extractive|1` | 36 | 0.302 |
| A5 | `extractive|2` | 36 | 0.289 |
| A5 | `extractive|3` | 30 | 0.272 |
| A5 | `numeric|0` | 34 | 0.386 |
| A5 | `numeric|1` | 31 | 0.491 |
| A5 | `numeric|2` | 32 | 0.623 |
| A5 | `numeric|3` | 30 | 0.657 |
| A6 | `abstractive|0` | 25 | 0.746 |
| A6 | `abstractive|1` | 41 | 0.871 |
| A6 | `abstractive|2` | 25 | 0.882 |
| A6 | `abstractive|3` | 35 | 0.843 |
| A6 | `entity|0` | 40 | 0.946 |
| A6 | `entity|1` | 35 | 0.889 |
| A6 | `entity|2` | 33 | 0.981 |
| A6 | `entity|3` | 38 | 0.954 |
| A6 | `extractive|0` | 33 | 0.989 |
| A6 | `extractive|1` | 36 | 0.858 |
| A6 | `extractive|2` | 36 | 0.975 |
| A6 | `extractive|3` | 30 | 1.000 |
| A6 | `numeric|0` | 34 | 0.943 |
| A6 | `numeric|1` | 31 | 1.000 |
| A6 | `numeric|2` | 32 | 0.961 |
| A6 | `numeric|3` | 30 | 0.991 |
| A7 | `abstractive|0` | 25 | 0.675 |
| A7 | `abstractive|1` | 41 | 0.891 |
| A7 | `abstractive|2` | 25 | 0.846 |
| A7 | `abstractive|3` | 35 | 0.861 |
| A7 | `entity|0` | 40 | 0.923 |
| A7 | `entity|1` | 35 | 0.884 |
| A7 | `entity|2` | 33 | 0.955 |
| A7 | `entity|3` | 38 | 0.966 |
| A7 | `extractive|0` | 33 | 0.737 |
| A7 | `extractive|1` | 36 | 0.844 |
| A7 | `extractive|2` | 36 | 0.752 |
| A7 | `extractive|3` | 30 | 0.616 |
| A7 | `numeric|0` | 34 | 0.712 |
| A7 | `numeric|1` | 31 | 0.957 |
| A7 | `numeric|2` | 32 | 0.874 |
| A7 | `numeric|3` | 30 | 0.949 |

## H2 test: A7 minus baseline, paired bootstrap

Both models are scored on the *same* test rows, so this is a paired comparison and much tighter than differencing two separate CIs. `p_gt_0` is the bootstrap fraction of resamples favouring A7.

| slice | comparison | ΔAUROC | 95% CI | p_gt_0 |
|---|---|---:|---|---:|
| `all` | A7 - A0 | -0.179 | [-0.218, -0.138] | 0.000 |
| `benchmark=synthetic` | A7 - A0 | -0.179 | [-0.218, -0.138] | 0.000 |
| `claim_type=0` | A7 - A0 | -0.112 | [-0.179, -0.063] | 0.000 |
| `claim_type=1` | A7 - A0 | -0.022 | [-0.065, 0.014] | 0.110 |
| `claim_type=2` | A7 - A0 | -0.330 | [-0.443, -0.242] | 0.000 |
| `claim_type=3` | A7 - A0 | -0.160 | [-0.247, -0.076] | 0.000 |
| `generator_id=0` | A7 - A0 | -0.177 | [-0.235, -0.118] | 0.000 |
| `generator_id=1` | A7 - A0 | -0.117 | [-0.191, -0.056] | 0.000 |
| `generator_id=2` | A7 - A0 | -0.145 | [-0.201, -0.076] | 0.000 |
| `generator_id=3` | A7 - A0 | -0.162 | [-0.228, -0.101] | 0.000 |
| `all` | A7 - A1 | -0.073 | [-0.106, -0.044] | 0.000 |
| `benchmark=synthetic` | A7 - A1 | -0.073 | [-0.106, -0.044] | 0.000 |
| `claim_type=0` | A7 - A1 | 0.275 | [0.186, 0.375] | 1.000 |
| `claim_type=1` | A7 - A1 | -0.027 | [-0.066, 0.005] | 0.050 |
| `claim_type=2` | A7 - A1 | -0.244 | [-0.329, -0.177] | 0.000 |
| `claim_type=3` | A7 - A1 | -0.138 | [-0.224, -0.060] | 0.000 |
| `generator_id=0` | A7 - A1 | -0.043 | [-0.102, 0.011] | 0.110 |
| `generator_id=1` | A7 - A1 | 0.000 | [-0.067, 0.078] | 0.510 |
| `generator_id=2` | A7 - A1 | -0.071 | [-0.127, -0.011] | 0.000 |
| `generator_id=3` | A7 - A1 | -0.072 | [-0.113, -0.026] | 0.010 |
| `all` | A7 - A2 | -0.172 | [-0.214, -0.129] | 0.000 |
| `benchmark=synthetic` | A7 - A2 | -0.172 | [-0.214, -0.129] | 0.000 |
| `claim_type=0` | A7 - A2 | -0.106 | [-0.177, -0.059] | 0.000 |
| `claim_type=1` | A7 - A2 | -0.022 | [-0.062, 0.016] | 0.130 |
| `claim_type=2` | A7 - A2 | -0.326 | [-0.444, -0.234] | 0.000 |
| `claim_type=3` | A7 - A2 | -0.109 | [-0.196, -0.009] | 0.000 |
| `generator_id=0` | A7 - A2 | -0.176 | [-0.244, -0.120] | 0.000 |
| `generator_id=1` | A7 - A2 | -0.108 | [-0.183, -0.040] | 0.000 |
| `generator_id=2` | A7 - A2 | -0.133 | [-0.188, -0.066] | 0.000 |
| `generator_id=3` | A7 - A2 | -0.153 | [-0.210, -0.093] | 0.000 |
| `all` | A7 - A3 | -0.176 | [-0.212, -0.137] | 0.000 |
| `benchmark=synthetic` | A7 - A3 | -0.176 | [-0.212, -0.137] | 0.000 |
| `claim_type=0` | A7 - A3 | -0.105 | [-0.174, -0.061] | 0.000 |
| `claim_type=1` | A7 - A3 | -0.026 | [-0.067, 0.008] | 0.070 |
| `claim_type=2` | A7 - A3 | -0.325 | [-0.427, -0.236] | 0.000 |
| `claim_type=3` | A7 - A3 | -0.151 | [-0.234, -0.071] | 0.000 |
| `generator_id=0` | A7 - A3 | -0.170 | [-0.232, -0.110] | 0.000 |
| `generator_id=1` | A7 - A3 | -0.115 | [-0.189, -0.051] | 0.000 |
| `generator_id=2` | A7 - A3 | -0.143 | [-0.198, -0.076] | 0.000 |
| `generator_id=3` | A7 - A3 | -0.162 | [-0.225, -0.102] | 0.000 |
| `all` | A7 - A4 | -0.174 | [-0.214, -0.132] | 0.000 |
| `benchmark=synthetic` | A7 - A4 | -0.174 | [-0.214, -0.132] | 0.000 |
| `claim_type=0` | A7 - A4 | -0.108 | [-0.184, -0.056] | 0.000 |
| `claim_type=1` | A7 - A4 | -0.021 | [-0.054, 0.009] | 0.080 |
| `claim_type=2` | A7 - A4 | -0.321 | [-0.425, -0.232] | 0.000 |
| `claim_type=3` | A7 - A4 | -0.143 | [-0.224, -0.052] | 0.000 |
| `generator_id=0` | A7 - A4 | -0.160 | [-0.225, -0.099] | 0.000 |
| `generator_id=1` | A7 - A4 | -0.128 | [-0.203, -0.061] | 0.000 |
| `generator_id=2` | A7 - A4 | -0.143 | [-0.200, -0.072] | 0.000 |
| `generator_id=3` | A7 - A4 | -0.160 | [-0.228, -0.098] | 0.000 |

## Gate weights (A7)

Mean softmax weights over the test split, by claim type and by generator. Both columns should sum to 1 per cell.

| claim type | w_cross g0 | w_cross g1 | w_cross g2 | w_cross g3 |
|---|---|---|---|---|
| abstractive | 0.848 | 0.597 | 0.703 | 0.798 |
| entity | 0.930 | 0.845 | 0.890 | 0.941 |
| extractive | 0.887 | 0.620 | 0.759 | 0.848 |
| numeric | 0.947 | 0.829 | 0.892 | 0.935 |

## Leave-one-generator-out (UNK cold start)

Each generator is removed from train and val, relabelled `UNK` in test, and scored on the UNK rows only. `seen_auroc` is the rest of the test set.

| held out | variant | n UNK | UNK AUROC | 95% CI | seen AUROC | in train? |
|---|---|---:|---:|---|---:|---|
| 0 | A0 | 132 | 0.932 [0.890, 0.974] | 0.971 | False |
| 0 | A7 | 132 | 0.539 [0.438, 0.623] | 0.547 | False |
| 1 | A0 | 143 | 0.947 [0.883, 0.997] | 0.968 | False |
| 1 | A7 | 143 | 0.625 [0.518, 0.719] | 0.512 | False |
| 2 | A0 | 126 | 0.985 [0.963, 1.000] | 0.955 | False |
| 2 | A7 | 126 | 0.512 [0.425, 0.622] | 0.509 | False |
| 3 | A0 | 133 | 0.982 [0.955, 1.000] | 0.955 | False |
| 3 | A7 | 133 | 0.608 [0.509, 0.699] | 0.522 | False |

## Cost and latency

Wall clock per run, and API accounting. API calls are zero for every table that was already built; they are non-zero only for tables whose signals came from a live extractor.

| variant | mean train s | mean predict s | API calls | API USD |
|---|---:|---:|---:|---:|
| A0 | 0.01 | 0.000 | 0 | 0.0000 |
| A1 | 0.01 | 0.001 | 0 | 0.0000 |
| A2 | 0.01 | 0.001 | 0 | 0.0000 |
| A3 | 0.33 | 0.002 | 0 | 0.0000 |
| A4 | 0.83 | 0.008 | 0 | 0.0000 |
| A5 | 4.11 | 0.003 | 0 | 0.0000 |
| A6 | 0.14 | 0.002 | 0 | 0.0000 |
| A7 | 0.23 | 0.002 | 0 | 0.0000 |
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

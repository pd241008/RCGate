# RC-Gate results -- synthetic

> **SYNTHETIC DATA.** These numbers validate the machinery on data with known planted signal reliability. They are not evidence for or against H1-H3, which are claims about real model outputs. Every table and plot from this run must be labelled synthetic (constraint C8).

- generated: 2026-10-05 14:46
- git: `b7b5889`
- config: `synthetic.yaml`
- signal table: `/root/workspace/workspace/03-Code/Projects/Legacy/RCgate/data/signal_tables/synthetic_s0.parquet`
- seeds: 5; bootstrap resamples: 1000 per slice per seed
- total wall clock: 405s

## Overall

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `all` | 2701 | 0.756 | 0.756 ± 0.012 | 0.617 | 0.529 | 0.747 | 0.027 |
| A1 | `all` | 2701 | 0.650 | 0.650 ± 0.018 | 0.564 | 0.508 | 0.636 | 0.065 |
| A2 | `all` | 2701 | 0.692 | 0.692 ± 0.007 | 0.564 | 0.470 | 0.708 | 0.022 |
| A3 | `all` | 2701 | 0.756 | 0.756 ± 0.012 | 0.618 | 0.533 | 0.739 | 0.027 |
| A4 | `all` | 2701 | 0.929 | 0.929 ± 0.009 | 0.866 | 0.888 | 0.846 | 0.036 |
| A5 | `all` | 2701 | 0.902 | 0.902 ± 0.010 | 0.786 | 0.793 | 0.782 | 0.031 |
| A6 | `all` | 2701 | 0.804 | 0.804 ± 0.014 | 0.653 | 0.603 | 0.716 | 0.027 |
| A7 | `all` | 2701 | 0.874 | 0.874 ± 0.063 | 0.750 | 0.730 | 0.776 | 0.035 |

## Per benchmark

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `benchmark=synthetic` | 2701 | 0.756 | 0.756 ± 0.012 | 0.617 | 0.529 | 0.747 | 0.027 |
| A1 | `benchmark=synthetic` | 2701 | 0.650 | 0.650 ± 0.018 | 0.564 | 0.508 | 0.636 | 0.065 |
| A2 | `benchmark=synthetic` | 2701 | 0.692 | 0.692 ± 0.007 | 0.564 | 0.470 | 0.708 | 0.022 |
| A3 | `benchmark=synthetic` | 2701 | 0.756 | 0.756 ± 0.012 | 0.618 | 0.533 | 0.739 | 0.027 |
| A4 | `benchmark=synthetic` | 2701 | 0.929 | 0.929 ± 0.009 | 0.866 | 0.888 | 0.846 | 0.036 |
| A5 | `benchmark=synthetic` | 2701 | 0.902 | 0.902 ± 0.010 | 0.786 | 0.793 | 0.782 | 0.031 |
| A6 | `benchmark=synthetic` | 2701 | 0.804 | 0.804 ± 0.014 | 0.653 | 0.603 | 0.716 | 0.027 |
| A7 | `benchmark=synthetic` | 2701 | 0.874 | 0.874 ± 0.063 | 0.750 | 0.730 | 0.776 | 0.035 |

## Per claim type

Claim types: 0 numeric, 1 entity, 2 extractive, 3 abstractive. The proposal's "numeric/extractive" reporting group is types 0 and 2.

| variant | slice | n | AUROC (95% CI) | AUROC mean ± sd | F1 | precision | recall | ECE |
|---|---|---:|---|---|---:|---:|---:|---:|
| A0 | `claim_type=0` | 689 | 0.478 | 0.478 ± 0.021 | 0.452 | 0.354 | 0.630 | 0.165 |
| A0 | `claim_type=1` | 668 | 0.858 | 0.858 ± 0.022 | 0.690 | 0.613 | 0.793 | 0.076 |
| A0 | `claim_type=2` | 678 | 0.837 | 0.837 ± 0.022 | 0.718 | 0.656 | 0.796 | 0.082 |
| A0 | `claim_type=3` | 665 | 0.805 | 0.805 ± 0.012 | 0.651 | 0.568 | 0.773 | 0.060 |
| A1 | `claim_type=0` | 689 | 0.060 | 0.060 ± 0.012 | 0.074 | 0.058 | 0.100 | 0.507 |
| A1 | `claim_type=1` | 668 | 0.926 | 0.926 ± 0.016 | 0.832 | 0.812 | 0.855 | 0.219 |
| A1 | `claim_type=2` | 678 | 0.882 | 0.882 ± 0.021 | 0.774 | 0.742 | 0.818 | 0.201 |
| A1 | `claim_type=3` | 665 | 0.882 | 0.882 ± 0.019 | 0.755 | 0.721 | 0.798 | 0.196 |
| A2 | `claim_type=0` | 689 | 0.833 | 0.833 ± 0.010 | 0.672 | 0.555 | 0.857 | 0.090 |
| A2 | `claim_type=1` | 668 | 0.608 | 0.608 ± 0.018 | 0.471 | 0.378 | 0.630 | 0.067 |
| A2 | `claim_type=2` | 678 | 0.696 | 0.696 ± 0.018 | 0.590 | 0.528 | 0.672 | 0.061 |
| A2 | `claim_type=3` | 665 | 0.613 | 0.613 ± 0.013 | 0.509 | 0.416 | 0.660 | 0.063 |
| A3 | `claim_type=0` | 689 | 0.470 | 0.470 ± 0.051 | 0.447 | 0.353 | 0.617 | 0.167 |
| A3 | `claim_type=1` | 668 | 0.860 | 0.860 ± 0.028 | 0.695 | 0.624 | 0.788 | 0.082 |
| A3 | `claim_type=2` | 678 | 0.837 | 0.837 ± 0.023 | 0.716 | 0.662 | 0.781 | 0.082 |
| A3 | `claim_type=3` | 665 | 0.807 | 0.807 ± 0.020 | 0.659 | 0.576 | 0.775 | 0.066 |
| A4 | `claim_type=0` | 689 | 0.942 | 0.942 ± 0.011 | 0.914 | 0.940 | 0.891 | 0.039 |
| A4 | `claim_type=1` | 668 | 0.927 | 0.927 ± 0.015 | 0.888 | 0.919 | 0.860 | 0.046 |
| A4 | `claim_type=2` | 678 | 0.911 | 0.911 ± 0.016 | 0.829 | 0.848 | 0.815 | 0.051 |
| A4 | `claim_type=3` | 665 | 0.922 | 0.922 ± 0.014 | 0.835 | 0.853 | 0.820 | 0.049 |
| A5 | `claim_type=0` | 689 | 0.834 | 0.834 ± 0.010 | 0.678 | 0.686 | 0.676 | 0.037 |
| A5 | `claim_type=1` | 668 | 0.932 | 0.932 ± 0.013 | 0.870 | 0.897 | 0.845 | 0.040 |
| A5 | `claim_type=2` | 678 | 0.913 | 0.913 ± 0.013 | 0.822 | 0.826 | 0.822 | 0.055 |
| A5 | `claim_type=3` | 665 | 0.898 | 0.898 ± 0.016 | 0.783 | 0.780 | 0.789 | 0.047 |
| A6 | `claim_type=0` | 689 | 0.640 | 0.640 ± 0.031 | 0.505 | 0.468 | 0.554 | 0.081 |
| A6 | `claim_type=1` | 668 | 0.884 | 0.884 ± 0.018 | 0.744 | 0.708 | 0.785 | 0.061 |
| A6 | `claim_type=2` | 678 | 0.800 | 0.800 ± 0.029 | 0.680 | 0.624 | 0.748 | 0.058 |
| A6 | `claim_type=3` | 665 | 0.851 | 0.851 ± 0.014 | 0.698 | 0.627 | 0.789 | 0.064 |
| A7 | `claim_type=0` | 689 | 0.855 | 0.855 ± 0.046 | 0.727 | 0.727 | 0.731 | 0.050 |
| A7 | `claim_type=1` | 668 | 0.869 | 0.869 ± 0.144 | 0.791 | 0.787 | 0.804 | 0.041 |
| A7 | `claim_type=2` | 678 | 0.867 | 0.867 ± 0.112 | 0.773 | 0.748 | 0.802 | 0.059 |
| A7 | `claim_type=3` | 665 | 0.841 | 0.841 ± 0.122 | 0.727 | 0.698 | 0.772 | 0.046 |

## Per generator

`UNK` (-1) only appears in the leave-one-generator-out table below.

| variant | generator | n | AUROC (95% CI) | AUROC mean ± sd | F1 | ECE |
|---|---|---:|---|---|---:|---:|
| A0 | 0 | 540 | 0.785 | 0.785 ± 0.022 | 0.646 | 0.058 |
| A0 | 1 | 543 | 0.790 | 0.790 ± 0.013 | 0.644 | 0.049 |
| A0 | 2 | 547 | 0.777 | 0.777 ± 0.013 | 0.626 | 0.056 |
| A0 | 3 | 534 | 0.782 | 0.782 ± 0.016 | 0.646 | 0.065 |
| A0 | 4 | 537 | 0.637 | 0.637 ± 0.019 | 0.535 | 0.088 |
| A1 | 0 | 540 | 0.695 | 0.695 ± 0.028 | 0.590 | 0.059 |
| A1 | 1 | 543 | 0.689 | 0.689 ± 0.028 | 0.588 | 0.071 |
| A1 | 2 | 547 | 0.706 | 0.706 ± 0.027 | 0.609 | 0.088 |
| A1 | 3 | 534 | 0.694 | 0.694 ± 0.022 | 0.603 | 0.083 |
| A1 | 4 | 537 | 0.446 | 0.446 ± 0.046 | 0.449 | 0.180 |
| A2 | 0 | 540 | 0.695 | 0.695 ± 0.021 | 0.563 | 0.051 |
| A2 | 1 | 543 | 0.702 | 0.702 ± 0.022 | 0.564 | 0.054 |
| A2 | 2 | 547 | 0.672 | 0.672 ± 0.016 | 0.554 | 0.051 |
| A2 | 3 | 534 | 0.687 | 0.687 ± 0.009 | 0.563 | 0.043 |
| A2 | 4 | 537 | 0.706 | 0.706 ± 0.026 | 0.575 | 0.045 |
| A3 | 0 | 540 | 0.786 | 0.786 ± 0.020 | 0.644 | 0.060 |
| A3 | 1 | 543 | 0.791 | 0.791 ± 0.010 | 0.646 | 0.053 |
| A3 | 2 | 547 | 0.778 | 0.778 ± 0.011 | 0.628 | 0.056 |
| A3 | 3 | 534 | 0.783 | 0.783 ± 0.016 | 0.648 | 0.061 |
| A3 | 4 | 537 | 0.631 | 0.631 ± 0.016 | 0.537 | 0.095 |
| A4 | 0 | 540 | 0.922 | 0.922 ± 0.015 | 0.854 | 0.051 |
| A4 | 1 | 543 | 0.933 | 0.933 ± 0.016 | 0.863 | 0.039 |
| A4 | 2 | 547 | 0.923 | 0.923 ± 0.025 | 0.854 | 0.052 |
| A4 | 3 | 534 | 0.927 | 0.927 ± 0.016 | 0.866 | 0.054 |
| A4 | 4 | 537 | 0.937 | 0.937 ± 0.009 | 0.892 | 0.046 |
| A5 | 0 | 540 | 0.903 | 0.903 ± 0.014 | 0.787 | 0.050 |
| A5 | 1 | 543 | 0.908 | 0.908 ± 0.016 | 0.791 | 0.042 |
| A5 | 2 | 547 | 0.905 | 0.905 ± 0.015 | 0.789 | 0.050 |
| A5 | 3 | 534 | 0.905 | 0.905 ± 0.013 | 0.806 | 0.054 |
| A5 | 4 | 537 | 0.888 | 0.888 ± 0.017 | 0.754 | 0.046 |
| A6 | 0 | 540 | 0.834 | 0.834 ± 0.024 | 0.684 | 0.064 |
| A6 | 1 | 543 | 0.830 | 0.830 ± 0.012 | 0.681 | 0.053 |
| A6 | 2 | 547 | 0.825 | 0.825 ± 0.015 | 0.673 | 0.059 |
| A6 | 3 | 534 | 0.813 | 0.813 ± 0.019 | 0.666 | 0.053 |
| A6 | 4 | 537 | 0.706 | 0.706 ± 0.026 | 0.566 | 0.071 |
| A7 | 0 | 540 | 0.882 | 0.882 ± 0.056 | 0.757 | 0.055 |
| A7 | 1 | 543 | 0.876 | 0.876 ± 0.069 | 0.751 | 0.048 |
| A7 | 2 | 547 | 0.877 | 0.877 ± 0.071 | 0.760 | 0.056 |
| A7 | 3 | 534 | 0.875 | 0.875 ± 0.067 | 0.763 | 0.053 |
| A7 | 4 | 537 | 0.861 | 0.861 ± 0.058 | 0.718 | 0.057 |

## Per (claim type, generator) cell

Point estimates only; bootstrap CIs are not computed for 20 cells x 5 seeds.

| variant | cell | n | AUROC mean ± sd |
|---|---|---:|---|
| A0 | `abstractive|0` | 139 | 0.838 ± 0.032 |
| A0 | `abstractive|1` | 131 | 0.846 ± 0.029 |
| A0 | `abstractive|2` | 129 | 0.812 ± 0.023 |
| A0 | `abstractive|3` | 132 | 0.830 ± 0.032 |
| A0 | `abstractive|4` | 133 | 0.678 ± 0.028 |
| A0 | `entity|0` | 126 | 0.903 ± 0.036 |
| A0 | `entity|1` | 135 | 0.894 ± 0.036 |
| A0 | `entity|2` | 134 | 0.874 ± 0.021 |
| A0 | `entity|3` | 139 | 0.867 ± 0.043 |
| A0 | `entity|4` | 133 | 0.736 ± 0.046 |
| A0 | `extractive|0` | 135 | 0.837 ± 0.027 |
| A0 | `extractive|1` | 132 | 0.845 ± 0.053 |
| A0 | `extractive|2` | 143 | 0.860 ± 0.017 |
| A0 | `extractive|3` | 132 | 0.860 ± 0.025 |
| A0 | `extractive|4` | 134 | 0.777 ± 0.025 |
| A0 | `numeric|0` | 138 | 0.510 ± 0.056 |
| A0 | `numeric|1` | 144 | 0.528 ± 0.049 |
| A0 | `numeric|2` | 140 | 0.504 ± 0.051 |
| A0 | `numeric|3` | 129 | 0.499 ± 0.018 |
| A0 | `numeric|4` | 136 | 0.349 ± 0.071 |
| A1 | `abstractive|0` | 139 | 0.917 ± 0.030 |
| A1 | `abstractive|1` | 131 | 0.911 ± 0.042 |
| A1 | `abstractive|2` | 129 | 0.933 ± 0.031 |
| A1 | `abstractive|3` | 132 | 0.926 ± 0.024 |
| A1 | `abstractive|4` | 133 | 0.624 ± 0.027 |
| A1 | `entity|0` | 126 | 0.940 ± 0.014 |
| A1 | `entity|1` | 135 | 0.958 ± 0.016 |
| A1 | `entity|2` | 134 | 0.944 ± 0.020 |
| A1 | `entity|3` | 139 | 0.918 ± 0.032 |
| A1 | `entity|4` | 133 | 0.818 ± 0.035 |
| A1 | `extractive|0` | 135 | 0.905 ± 0.019 |
| A1 | `extractive|1` | 132 | 0.891 ± 0.037 |
| A1 | `extractive|2` | 143 | 0.920 ± 0.023 |
| A1 | `extractive|3` | 132 | 0.912 ± 0.011 |
| A1 | `extractive|4` | 134 | 0.749 ± 0.085 |
| A1 | `numeric|0` | 138 | 0.066 ± 0.017 |
| A1 | `numeric|1` | 144 | 0.068 ± 0.044 |
| A1 | `numeric|2` | 140 | 0.092 ± 0.024 |
| A1 | `numeric|3` | 129 | 0.055 ± 0.023 |
| A1 | `numeric|4` | 136 | 0.036 ± 0.011 |
| A2 | `abstractive|0` | 139 | 0.621 ± 0.036 |
| A2 | `abstractive|1` | 131 | 0.641 ± 0.055 |
| A2 | `abstractive|2` | 129 | 0.562 ± 0.043 |
| A2 | `abstractive|3` | 132 | 0.599 ± 0.041 |
| A2 | `abstractive|4` | 133 | 0.638 ± 0.033 |
| A2 | `entity|0` | 126 | 0.626 ± 0.059 |
| A2 | `entity|1` | 135 | 0.598 ± 0.056 |
| A2 | `entity|2` | 134 | 0.591 ± 0.023 |
| A2 | `entity|3` | 139 | 0.611 ± 0.035 |
| A2 | `entity|4` | 133 | 0.616 ± 0.049 |
| A2 | `extractive|0` | 135 | 0.681 ± 0.040 |
| A2 | `extractive|1` | 132 | 0.692 ± 0.053 |
| A2 | `extractive|2` | 143 | 0.711 ± 0.021 |
| A2 | `extractive|3` | 132 | 0.698 ± 0.029 |
| A2 | `extractive|4` | 134 | 0.697 ± 0.044 |
| A2 | `numeric|0` | 138 | 0.828 ± 0.032 |
| A2 | `numeric|1` | 144 | 0.839 ± 0.020 |
| A2 | `numeric|2` | 140 | 0.795 ± 0.050 |
| A2 | `numeric|3` | 129 | 0.838 ± 0.012 |
| A2 | `numeric|4` | 136 | 0.860 ± 0.011 |
| A3 | `abstractive|0` | 139 | 0.841 ± 0.043 |
| A3 | `abstractive|1` | 131 | 0.850 ± 0.030 |
| A3 | `abstractive|2` | 129 | 0.818 ± 0.030 |
| A3 | `abstractive|3` | 132 | 0.834 ± 0.022 |
| A3 | `abstractive|4` | 133 | 0.673 ± 0.032 |
| A3 | `entity|0` | 126 | 0.906 ± 0.036 |
| A3 | `entity|1` | 135 | 0.895 ± 0.038 |
| A3 | `entity|2` | 134 | 0.875 ± 0.021 |
| A3 | `entity|3` | 139 | 0.868 ± 0.047 |
| A3 | `entity|4` | 133 | 0.734 ± 0.046 |
| A3 | `extractive|0` | 135 | 0.838 ± 0.025 |
| A3 | `extractive|1` | 132 | 0.846 ± 0.054 |
| A3 | `extractive|2` | 143 | 0.864 ± 0.016 |
| A3 | `extractive|3` | 132 | 0.859 ± 0.024 |
| A3 | `extractive|4` | 134 | 0.775 ± 0.029 |
| A3 | `numeric|0` | 138 | 0.505 ± 0.080 |
| A3 | `numeric|1` | 144 | 0.516 ± 0.081 |
| A3 | `numeric|2` | 140 | 0.498 ± 0.069 |
| A3 | `numeric|3` | 129 | 0.494 ± 0.040 |
| A3 | `numeric|4` | 136 | 0.334 ± 0.068 |
| A4 | `abstractive|0` | 139 | 0.906 ± 0.036 |
| A4 | `abstractive|1` | 131 | 0.919 ± 0.051 |
| A4 | `abstractive|2` | 129 | 0.926 ± 0.044 |
| A4 | `abstractive|3` | 132 | 0.925 ± 0.031 |
| A4 | `abstractive|4` | 133 | 0.934 ± 0.020 |
| A4 | `entity|0` | 126 | 0.937 ± 0.018 |
| A4 | `entity|1` | 135 | 0.950 ± 0.018 |
| A4 | `entity|2` | 134 | 0.947 ± 0.035 |
| A4 | `entity|3` | 139 | 0.910 ± 0.047 |
| A4 | `entity|4` | 133 | 0.911 ± 0.038 |
| A4 | `extractive|0` | 135 | 0.893 ± 0.017 |
| A4 | `extractive|1` | 132 | 0.894 ± 0.038 |
| A4 | `extractive|2` | 143 | 0.904 ± 0.026 |
| A4 | `extractive|3` | 132 | 0.928 ± 0.023 |
| A4 | `extractive|4` | 134 | 0.932 ± 0.006 |
| A4 | `numeric|0` | 138 | 0.935 ± 0.025 |
| A4 | `numeric|1` | 144 | 0.946 ± 0.024 |
| A4 | `numeric|2` | 140 | 0.904 ± 0.041 |
| A4 | `numeric|3` | 129 | 0.947 ± 0.006 |
| A4 | `numeric|4` | 136 | 0.966 ± 0.010 |
| A5 | `abstractive|0` | 139 | 0.900 ± 0.036 |
| A5 | `abstractive|1` | 131 | 0.895 ± 0.045 |
| A5 | `abstractive|2` | 129 | 0.920 ± 0.040 |
| A5 | `abstractive|3` | 132 | 0.915 ± 0.019 |
| A5 | `abstractive|4` | 133 | 0.850 ± 0.027 |
| A5 | `entity|0` | 126 | 0.936 ± 0.022 |
| A5 | `entity|1` | 135 | 0.957 ± 0.015 |
| A5 | `entity|2` | 134 | 0.939 ± 0.015 |
| A5 | `entity|3` | 139 | 0.918 ± 0.036 |
| A5 | `entity|4` | 133 | 0.917 ± 0.017 |
| A5 | `extractive|0` | 135 | 0.916 ± 0.018 |
| A5 | `extractive|1` | 132 | 0.901 ± 0.041 |
| A5 | `extractive|2` | 143 | 0.920 ± 0.016 |
| A5 | `extractive|3` | 132 | 0.926 ± 0.016 |
| A5 | `extractive|4` | 134 | 0.903 ± 0.031 |
| A5 | `numeric|0` | 138 | 0.829 ± 0.031 |
| A5 | `numeric|1` | 144 | 0.839 ± 0.022 |
| A5 | `numeric|2` | 140 | 0.792 ± 0.053 |
| A5 | `numeric|3` | 129 | 0.843 ± 0.011 |
| A5 | `numeric|4` | 136 | 0.863 ± 0.014 |
| A6 | `abstractive|0` | 139 | 0.898 ± 0.030 |
| A6 | `abstractive|1` | 131 | 0.895 ± 0.027 |
| A6 | `abstractive|2` | 129 | 0.887 ± 0.026 |
| A6 | `abstractive|3` | 132 | 0.891 ± 0.021 |
| A6 | `abstractive|4` | 133 | 0.638 ± 0.033 |
| A6 | `entity|0` | 126 | 0.939 ± 0.017 |
| A6 | `entity|1` | 135 | 0.941 ± 0.023 |
| A6 | `entity|2` | 134 | 0.926 ± 0.028 |
| A6 | `entity|3` | 139 | 0.897 ± 0.030 |
| A6 | `entity|4` | 133 | 0.615 ± 0.051 |
| A6 | `extractive|0` | 135 | 0.814 ± 0.044 |
| A6 | `extractive|1` | 132 | 0.804 ± 0.043 |
| A6 | `extractive|2` | 143 | 0.852 ± 0.019 |
| A6 | `extractive|3` | 132 | 0.817 ± 0.043 |
| A6 | `extractive|4` | 134 | 0.697 ± 0.043 |
| A6 | `numeric|0` | 138 | 0.610 ± 0.044 |
| A6 | `numeric|1` | 144 | 0.595 ± 0.060 |
| A6 | `numeric|2` | 140 | 0.551 ± 0.081 |
| A6 | `numeric|3` | 129 | 0.562 ± 0.067 |
| A6 | `numeric|4` | 136 | 0.861 ± 0.013 |
| A7 | `abstractive|0` | 139 | 0.853 ± 0.116 |
| A7 | `abstractive|1` | 131 | 0.838 ± 0.104 |
| A7 | `abstractive|2` | 129 | 0.851 ± 0.168 |
| A7 | `abstractive|3` | 132 | 0.847 ± 0.138 |
| A7 | `abstractive|4` | 133 | 0.801 ± 0.098 |
| A7 | `entity|0` | 126 | 0.880 ± 0.147 |
| A7 | `entity|1` | 135 | 0.876 ± 0.191 |
| A7 | `entity|2` | 134 | 0.872 ± 0.148 |
| A7 | `entity|3` | 139 | 0.861 ± 0.126 |
| A7 | `entity|4` | 133 | 0.860 ± 0.133 |
| A7 | `extractive|0` | 135 | 0.871 ± 0.109 |
| A7 | `extractive|1` | 132 | 0.846 ± 0.138 |
| A7 | `extractive|2` | 143 | 0.883 ± 0.087 |
| A7 | `extractive|3` | 132 | 0.878 ± 0.122 |
| A7 | `extractive|4` | 134 | 0.845 ± 0.123 |
| A7 | `numeric|0` | 138 | 0.845 ± 0.055 |
| A7 | `numeric|1` | 144 | 0.856 ± 0.047 |
| A7 | `numeric|2` | 140 | 0.824 ± 0.058 |
| A7 | `numeric|3` | 129 | 0.864 ± 0.043 |
| A7 | `numeric|4` | 136 | 0.881 ± 0.053 |

## H2 test: A7 minus baseline, paired bootstrap

Both models are scored on the *same* test rows, so this is a paired comparison and much tighter than differencing two separate CIs. `p_gt_0` is the bootstrap fraction of resamples favouring A7.

| slice | comparison | ΔAUROC | 95% CI | p_gt_0 |
|---|---|---:|---|---:|
| `all` | A7 - A0 | 0.118 | [0.102, 0.133] | 0.974 |
| `benchmark=synthetic` | A7 - A0 | 0.118 | [0.102, 0.133] | 0.974 |
| `claim_type=0` | A7 - A0 | 0.377 | [0.341, 0.414] | 1.000 |
| `claim_type=1` | A7 - A0 | 0.011 | [-0.014, 0.037] | 0.800 |
| `claim_type=2` | A7 - A0 | 0.029 | [0.006, 0.053] | 0.800 |
| `claim_type=3` | A7 - A0 | 0.036 | [0.008, 0.063] | 0.800 |
| `generator_id=0` | A7 - A0 | 0.098 | [0.066, 0.130] | 0.945 |
| `generator_id=1` | A7 - A0 | 0.086 | [0.055, 0.118] | 0.845 |
| `generator_id=2` | A7 - A0 | 0.101 | [0.066, 0.135] | 0.878 |
| `generator_id=3` | A7 - A0 | 0.093 | [0.057, 0.126] | 0.816 |
| `generator_id=4` | A7 - A0 | 0.223 | [0.180, 0.265] | 1.000 |
| `all` | A7 - A1 | 0.225 | [0.202, 0.248] | 1.000 |
| `benchmark=synthetic` | A7 - A1 | 0.225 | [0.202, 0.248] | 1.000 |
| `claim_type=0` | A7 - A1 | 0.795 | [0.747, 0.838] | 1.000 |
| `claim_type=1` | A7 - A1 | -0.056 | [-0.073, -0.039] | 0.610 |
| `claim_type=2` | A7 - A1 | -0.015 | [-0.035, 0.004] | 0.800 |
| `claim_type=3` | A7 - A1 | -0.041 | [-0.061, -0.021] | 0.795 |
| `generator_id=0` | A7 - A1 | 0.188 | [0.141, 0.237] | 1.000 |
| `generator_id=1` | A7 - A1 | 0.187 | [0.138, 0.238] | 0.983 |
| `generator_id=2` | A7 - A1 | 0.171 | [0.121, 0.221] | 0.977 |
| `generator_id=3` | A7 - A1 | 0.180 | [0.132, 0.230] | 0.972 |
| `generator_id=4` | A7 - A1 | 0.415 | [0.359, 0.470] | 1.000 |
| `all` | A7 - A2 | 0.182 | [0.163, 0.201] | 1.000 |
| `benchmark=synthetic` | A7 - A2 | 0.182 | [0.163, 0.201] | 1.000 |
| `claim_type=0` | A7 - A2 | 0.022 | [0.012, 0.032] | 0.554 |
| `claim_type=1` | A7 - A2 | 0.262 | [0.222, 0.300] | 0.944 |
| `claim_type=2` | A7 - A2 | 0.170 | [0.139, 0.203] | 0.840 |
| `claim_type=3` | A7 - A2 | 0.227 | [0.187, 0.266] | 0.926 |
| `generator_id=0` | A7 - A2 | 0.187 | [0.145, 0.232] | 1.000 |
| `generator_id=1` | A7 - A2 | 0.174 | [0.134, 0.217] | 1.000 |
| `generator_id=2` | A7 - A2 | 0.205 | [0.161, 0.251] | 1.000 |
| `generator_id=3` | A7 - A2 | 0.188 | [0.145, 0.232] | 1.000 |
| `generator_id=4` | A7 - A2 | 0.154 | [0.113, 0.196] | 1.000 |
| `all` | A7 - A3 | 0.119 | [0.103, 0.135] | 0.972 |
| `benchmark=synthetic` | A7 - A3 | 0.119 | [0.103, 0.135] | 0.972 |
| `claim_type=0` | A7 - A3 | 0.385 | [0.348, 0.422] | 1.000 |
| `claim_type=1` | A7 - A3 | 0.010 | [-0.016, 0.036] | 0.800 |
| `claim_type=2` | A7 - A3 | 0.030 | [0.007, 0.054] | 0.800 |
| `claim_type=3` | A7 - A3 | 0.033 | [0.006, 0.061] | 0.800 |
| `generator_id=0` | A7 - A3 | 0.097 | [0.065, 0.130] | 0.943 |
| `generator_id=1` | A7 - A3 | 0.085 | [0.054, 0.119] | 0.833 |
| `generator_id=2` | A7 - A3 | 0.099 | [0.064, 0.134] | 0.859 |
| `generator_id=3` | A7 - A3 | 0.092 | [0.056, 0.125] | 0.811 |
| `generator_id=4` | A7 - A3 | 0.229 | [0.185, 0.272] | 1.000 |
| `all` | A7 - A4 | -0.054 | [-0.065, -0.044] | 0.000 |
| `benchmark=synthetic` | A7 - A4 | -0.054 | [-0.065, -0.044] | 0.000 |
| `claim_type=0` | A7 - A4 | -0.087 | [-0.113, -0.060] | 0.005 |
| `claim_type=1` | A7 - A4 | -0.058 | [-0.080, -0.034] | 0.536 |
| `claim_type=2` | A7 - A4 | -0.044 | [-0.063, -0.026] | 0.434 |
| `claim_type=3` | A7 - A4 | -0.081 | [-0.103, -0.059] | 0.004 |
| `generator_id=0` | A7 - A4 | -0.040 | [-0.063, -0.017] | 0.090 |
| `generator_id=1` | A7 - A4 | -0.057 | [-0.080, -0.035] | 0.004 |
| `generator_id=2` | A7 - A4 | -0.046 | [-0.070, -0.021] | 0.133 |
| `generator_id=3` | A7 - A4 | -0.052 | [-0.076, -0.029] | 0.024 |
| `generator_id=4` | A7 - A4 | -0.076 | [-0.105, -0.050] | 0.000 |

## Gate weights (A7)

Mean softmax weights over the test split, by claim type and by generator. Both columns should sum to 1 per cell.

| claim type | w_cross g0 | w_cross g1 | w_cross g2 | w_cross g3 | w_cross g4 |
|---|---|---|---|---|---|
| abstractive | 0.641 | 0.636 | 0.637 | 0.647 | 0.558 |
| entity | 0.651 | 0.690 | 0.682 | 0.697 | 0.657 |
| extractive | 0.576 | 0.603 | 0.605 | 0.626 | 0.544 |
| numeric | 0.192 | 0.188 | 0.191 | 0.180 | 0.202 |

## Leave-one-generator-out (UNK cold start)

Each generator is removed from train and val, relabelled `UNK` in test, and scored on the UNK rows only. `seen_auroc` is the rest of the test set.

| held out | variant | n UNK | UNK AUROC | 95% CI | seen AUROC | in train? |
|---|---|---:|---:|---|---:|---|
| 0 | A0 | 542 | 0.742 [0.701, 0.789] | 0.743 | False |
| 0 | A7 | 542 | 0.891 [0.862, 0.926] | 0.908 | False |
| 1 | A0 | 535 | 0.775 [0.734, 0.815] | 0.734 | False |
| 1 | A7 | 535 | 0.904 [0.875, 0.926] | 0.905 | False |
| 2 | A0 | 545 | 0.749 [0.704, 0.794] | 0.740 | False |
| 2 | A7 | 545 | 0.908 [0.878, 0.934] | 0.904 | False |
| 3 | A0 | 528 | 0.746 [0.705, 0.782] | 0.740 | False |
| 3 | A7 | 528 | 0.915 [0.890, 0.939] | 0.902 | False |
| 4 | A0 | 546 | 0.171 [0.139, 0.203] | 0.816 | False |
| 4 | A7 | 546 | 0.748 [0.698, 0.795] | 0.910 | False |

## Cost and latency

Wall clock per run, and API accounting. API calls are zero for every table that was already built; they are non-zero only for tables whose signals came from a live extractor.

| variant | mean train s | mean predict s | API calls | API USD |
|---|---:|---:|---:|---:|
| A0 | 0.01 | 0.001 | 0 | 0.0000 |
| A1 | 0.01 | 0.001 | 0 | 0.0000 |
| A2 | 0.01 | 0.001 | 0 | 0.0000 |
| A3 | 0.80 | 0.002 | 0 | 0.0000 |
| A4 | 1.11 | 0.017 | 0 | 0.0000 |
| A5 | 14.16 | 0.004 | 0 | 0.0000 |
| A6 | 18.28 | 0.003 | 0 | 0.0000 |
| A7 | 10.13 | 0.003 | 0 | 0.0000 |
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

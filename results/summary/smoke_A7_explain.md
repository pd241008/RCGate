# Gate weights -- A7 (seed 0)

- git: `b7b5889`
- trainable parameters: 225
- gate input dimension: 8 (claim-type embedding ‖ generator embedding)

## Collapse check (spec section 11)

- spread of cell means: **0.0032**
- range: [0.0001, 0.0121]
- verdict: gate collapsed: metadata carries no signal in this dataset

## w_cross by claim type and generator

Blue in the heatmap is cross-model; the two tables below are the same numbers.

| claim type \ generator | g0 | g1 | g2 | g3 |
|---|---|---|---|---|
| abstractive | 0.003 | 0.003 | 0.004 | 0.012 |
| entity | 0.002 | 0.002 | 0.002 | 0.008 |
| extractive | 0.001 | 0.001 | 0.001 | 0.004 |
| numeric | 0.000 | 0.000 | 0.000 | 0.001 |

| claim type \ generator | g0 | g1 | g2 | g3 |
|---|---|---|---|---|
| abstractive | 0.997 | 0.997 | 0.996 | 0.988 |
| entity | 0.998 | 0.998 | 0.998 | 0.992 |
| extractive | 0.999 | 0.999 | 0.999 | 0.996 |
| numeric | 1.000 | 1.000 | 1.000 | 0.999 |

## w_cross by generator

| generator | mean | std | min | max |
|---|---:|---:|---:|---:|
| g0 | 0.001 | 0.001 | 0.000 | 0.003 |
| g1 | 0.001 | 0.001 | 0.000 | 0.003 |
| g2 | 0.002 | 0.001 | 0.000 | 0.004 |
| g3 | 0.007 | 0.004 | 0.001 | 0.012 |

## Most-flagged claims

| claim | type | prob | w_evid | z_cross | z_evid | explanation |
|---|---|---:|---:|---:|---:|---|
| In 2017, total output reached 227 units, a increase of 29 units. | numeric | 0.410 | 0.999 | +0.07 | -0.79 | numeric claim; likely supported (0.41); evidence down-weighted (w_evid 0.00) |
| The report states total output of 695 megawatt-hours across all sites, | extractive | 0.407 | 0.996 | +0.14 | -0.82 | extractive claim; likely supported (0.41); evidence down-weighted (w_evid 0.00) |
| In 2021, total output reached 381 tonnes, a increase of 33 tonnes. | numeric | 0.403 | 1.000 | +0.12 | -0.85 | numeric claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| The Bellweather facility is operated from Calder by a regional contrac | entity | 0.403 | 0.992 | +0.13 | -0.86 | entity claim; likely supported (0.40); evidence down-weighted (w_evid 0.01) |
| The report states total output of 700 kilometres across all sites, up  | extractive | 0.402 | 0.996 | +0.05 | -0.86 | extractive claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| The report states total output of 247 tonnes across all sites, up from | extractive | 0.402 | 0.996 | +0.14 | -0.86 | extractive claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| In 2017, total output reached 829 units, a increase of 34 units. | numeric | 0.402 | 0.999 | +0.16 | -0.86 | numeric claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| The report states total output of 445 megawatt-hours across all sites, | extractive | 0.401 | 0.996 | +0.17 | -0.87 | extractive claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| In 2017, total output reached 900 megawatt-hours, a increase of 8 mega | numeric | 0.399 | 1.000 | +0.03 | -0.89 | numeric claim; likely supported (0.40); evidence down-weighted (w_evid 0.00) |
| The Juniper facility is operated from Ironbridge by a regional contrac | entity | 0.396 | 0.992 | +0.06 | -0.92 | entity claim; likely supported (0.40); evidence down-weighted (w_evid 0.01) |
| The report states total output of 894 tonnes across all sites, up from | extractive | 0.395 | 0.996 | +0.08 | -0.93 | extractive claim; likely supported (0.39); evidence down-weighted (w_evid 0.00) |
| The report states total output of 208 shares across all sites, up from | extractive | 0.390 | 0.996 | +0.13 | -0.97 | extractive claim; likely supported (0.39); evidence down-weighted (w_evid 0.00) |

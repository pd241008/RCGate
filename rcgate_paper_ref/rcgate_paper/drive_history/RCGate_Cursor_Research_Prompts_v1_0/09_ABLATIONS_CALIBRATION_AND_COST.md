# Prompt 09 — Ablations, calibration and cost/peer-panel analysis

Continue only after the primary and shift evaluations are complete and frozen. Any exploratory analyses must be labelled exploratory and cannot replace the primary result.

## Ablations

1. Grounding-only vs peer-agreement-only vs combined features.
2. Per peer-generator contribution, leaving one peer out at a time where data permit.
3. Peer panel size (e.g. 1, 2, 3, up to all available peers) using a frozen ordering/subset plan, not a best-subset selected on test results. Use repeated fixed peer subsets or a predeclared panel-selection scheme.
4. Individual NLI support, contradiction, neutral/margin signals and semantic agreement, but only those predeclared in the protocol.
5. Per-task and per-target-generator performance to diagnose reversals.
6. Missing peer outputs and incomplete source/query panels.

## Calibration/selective decisions

Evaluate calibration only on a target with a defined probability interpretation. Fit calibrators and thresholds on calibration/validation groups only; do not use test outcomes. Include reliability diagrams, Brier score/log loss or ECE only with binning details and uncertainty. If the model is not calibrated, call output a score, not a probability. For selective prediction, show risk-coverage curves and abstention rates rather than only one operating point.

## Cost and latency

Separate:
- feature extraction latency with the already stored peer responses;
- NLI/embedding inference latency and hardware;
- the number of peer model responses required at deployment;
- token counts/calls where available;
- historical generation dollars, which must be marked unavailable unless verified from records.

Do not multiply current model prices by unknown historical token usage and present it as actual cost. A scenario analysis must be labelled hypothetical and list assumptions.

## Deliverables

Ablation tables and JSON, calibration/coverage outputs, per-model latency and panel-size costs, `ABLATION_CALIBRATION_COST_REPORT.md`, and unit tests. No cherry-picking the best subset after test. Then wait for Prompt 10.

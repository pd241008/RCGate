# Prompt 11 — Build the final results ledger and claims audit

Before drafting prose, produce a line-by-line ledger connecting each intended claim to the result that supports or contradicts it.

## Results ledger

Create `RESULTS_LEDGER.md` with columns: claim ID; exact proposed scientific claim; dataset/condition; metric; estimate; uncertainty interval/test; baseline; artifact path; script/command; limitations; claim status (supported, mixed, unsupported, exploratory).

Include:
- descriptive label/data counts;
- main conditional contribution of peer agreement over grounding-only;
- in-distribution source/query evaluation;
- every eligible held-out generator and task;
- ablations and panel cost;
- calibration/coverage only when valid;
- negative findings and performance reversals;
- unavailable baselines and missing competitor reproductions.

## Claim audit

Audit every numerical statement against saved outputs and independent recomputation where possible. Confirm old A0/A4/A7 numbers are clearly labelled historical and never represented as this study's results. Confirm no Stage 8 result is reused as new evidence. Confirm no feature uses gold spans, test labels, or target generator labels improperly.

Do not claim “substantially better” unless the predeclared primary comparison shows a clear, practically meaningful gain against the strongest fair baseline, supported by uncertainty estimates and shift analyses. If only some tasks/generators improve, write that precisely. If it fails, document failure and its implications.

## Deliverables

`RESULTS_LEDGER.md`, `CLAIMS_AND_LIMITATIONS_AUDIT.md`, final metrics manifest, and a table of all executed commands. Do not draft the final paper until claims have been signed off in these files. Then wait for Prompt 12.

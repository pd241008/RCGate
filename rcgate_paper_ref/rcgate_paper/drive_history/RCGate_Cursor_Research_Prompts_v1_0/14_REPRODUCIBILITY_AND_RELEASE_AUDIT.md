# Prompt 14 — Final reproducibility, artifact and claim integrity audit

Perform a final pre-submission audit of the new RC-Gate paper and experiment artifacts. Do not hide failures or create missing results.

## Reproduction

1. Verify environment specification and lockfiles; pin Python/package versions and model snapshot revisions. Record hardware, OS, random seeds and nondeterminism caveats.
2. Ensure raw RAGTruth data are not modified and access/license constraints are documented.
3. From a clean copy/worktree if feasible, run the documented pipeline in order: data validation, label transformation, feature generation, split verification, fit, test evaluation, statistics, figure generation and paper build.
4. Compare rerun hashes/metrics against the results ledger. Explain numerical variation; never overwrite the original run silently.
5. Verify all caches have complete keys and cannot reuse stale features from the 800-row historical experiment.
6. Verify no test labels influence train/validation features, model selection, thresholds, calibration, peer-subset selection or exclusions.
7. Verify all source/query groups and peer outputs align correctly. Confirm held-out generator protocols are real held-out tests, not pooled splits leaving the target generator in training.
8. Check all figures and table numbers against machine-readable outputs.
9. Check citations and BibTeX; distinguish published papers from preprints; confirm all bibliography entries are cited and all citations resolve.
10. Check manuscript PDF, all pages, figures, tables, equations, notation, supplementary/reproducibility files and professor compliance audit.
11. Report licensing of data, code and model assets. Do not redistribute assets with unclear permission.

## Final output

Create `REPRODUCIBILITY_REPORT.md` with exact commands, environment, hashes, test results, known deviations, leakage checks, license/access notes and files needed to reproduce. Create an artifact index. Clearly state whether the evidence supports, partially supports or fails to support the main hypothesis and each claimed contribution.

## Git safety

Do not stage, commit, push, reset, clean or switch branches. Preserve all historical and untracked files. End with exact Git status and list of new directories/files. Do not call the manuscript submission-ready if authorship/declaration/venue decisions remain unresolved.

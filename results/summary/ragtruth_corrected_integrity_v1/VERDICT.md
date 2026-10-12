# Verdict

A change is treated as material when it is large relative to the uncertainty of the comparison, not when it exceeds a fixed percentage. For AUROC, that uncertainty is the across-seed standard deviation (about 0.06 to 0.12 on the full test slice) and the claim-level bootstrap interval (about 0.24 wide for one seed). For the dataset, a material change is one that alters which rows are included, which labels they carry, or the text and type of enough rows to change what the slice is.

## Answers

1. The sentence-alignment correction did not materially change the RAGTruth evaluation set. Row count, claim IDs, generator counts, and all 57 positive labels are unchanged. It did correct 11 seed-0 sentences (12 on seeds 1 and 2) that had been concatenated with the following sentence. Those individual strings were wrong. Their number is too small to move labels or aggregate signal means (the largest mean signal shift on the whole slice is 0.015, against within-slice SDs of about 0.24 to 0.45).

2. The prompt-antecedent correction did materially change claim text and claim type, and it did not change labels. On seed 0, 90 of 800 claims had been rewritten with `Briefly` or `Summarize`. After the fix, `dealias_changed` is 0: this slice keeps the first sentence of each answer, so the question fallback was the only antecedent, and every one of those antecedents was an instruction word. Entity claims fall from 211 to 183. Of the 53 entity rows whose proper nouns included `Briefly` or `Summarize`, 27 leave the entity class and 26 stay entity because another name remains. One positive row changes type. Seven positive rows change text.

3. Neither correction materially changed A7. Mean AUROC moves from 0.631 to 0.638 (Δ +0.006). The three seeds move by −0.007, −0.007, and +0.033. The across-seed SD is 0.10 to 0.12.

4. The A4 > A7 ordering of the mean did not change (0.740 > 0.631, then 0.706 > 0.638). The paired interval for A7 − A4 still includes 0 (−0.109 [−0.261, 0.044] historically; −0.068 [−0.234, 0.113] corrected). Seed 1 was a near-tie that changes sign (A7 ahead by 0.008, then A4 ahead by 0.054). That single-seed flip is inside the noise of one test split of about 160 rows.

5. The main interpretation does not change. On this RAGTruth slice, A7 does not beat the flat GBM control A4, and it does not beat A0. The paired comparisons remain consistent with no advantage for A7. The historical reading that H1 and H2 are not supported on this slice still holds.

6. These conclusions from the original run remain valid. A4 has the highest mean AUROC among A0–A7. A7's paired deltas against A0 and A4 are negative and their intervals include 0. The slice is 800 claims, 57 positives (7.1%), the same claim IDs, the same six generators, and the same QA/Summary mix. `src_quality` is constant at 0.9. A8 remains skipped because there are no judge votes.

7. These items are now historical only. The exact AUROC, F1, precision, recall, and ECE point estimates. The entity and abstractive counts, and any claim-type slice AUROC that depended on rows typed entity because the claim said `Briefly` or `Summarize`. Any quoted claim whose text was that substitution, or one of the 11–12 merged first sentences. The numerical size of the A4 − A7 gap (0.109 versus 0.068); the sign and the overlapping interval remain, the third decimal does not.

## What was not changed

Model architecture, A0–A8 definitions, the synthetic generator, hyperparameters, the threshold procedure, and the bootstrap procedure were left as they were. The statistical defects of that procedure are listed in `statistical_issues.md` and were not fixed in this run.

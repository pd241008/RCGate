# Postmortem 002: M6 Honest Negative — A4 Beats A7 on Real Data

> **Date:** October 5, 2026  
> **Severity:** Major finding — the proposed method's headline comparison fails on the first real benchmark  
> **Status:** Complete — reported as measured, nothing retuned

> **Status note, October 10, 2026.** The measurements in this note stay as the original M6 record: A0 0.681, A1 0.705, A4 0.740, A7 0.631, and a paired difference of −0.050 with the bootstrap fraction written as `p = 0.415`. [`docs/RC-Gate_Final_Research_Report_v1.md`](../../RC-Gate_Final_Research_Report_v1.md) supersedes those figures as performance claims, and it supersedes the statement that H3 holds because the weights are explainable. The current repeated-fit estimates are Table 7 of that report. The near-0.45 weight description is a pre-factorial observation from this slice, not a Stage 8 measurement. Historical metrics in this note are not current estimates. The file map is [`docs/RC-Gate_Experiment_Index.md`](../../RC-Gate_Experiment_Index.md).

## Issues Summary

On synthetic data, A7 (RC-Gate) beat flat fusion by +0.38 AUROC on numeric claims and survived an unseen inverted generator where A0 scored 0.17. On the first real benchmark (RAGTruth, 800 claims × 3 seeds, ~57 positives per table), the ordering inverted: **A0 0.681, A1 0.705, A4 0.740, A7 0.631**. The paired bootstrap for A7 − A0 on `all` is **−0.050 [−0.21, 0.10], p = 0.415** — a loss with the null inside it. The critical control A4 (flat GBM on six signals + one-hot claim type/generator) leads every slice.

> [!IMPORTANT]  
> This is a *negative result about the current slice*, not a disproof of the architecture — but per constraint C8 and agent.md §12 it is reported exactly as measured, in every table, and the paper's A4 paragraph must lead with it.

---

## Finding #1 — The Gate Did Not Collapse; the Metadata Carried Nothing

### What Happened

Gate weights across (claim type × generator) cells sit near **0.45** with little spread — the gate is producing near-uniform trust. On synthetic data, claim type alone moved `w_cross` from 0.19 (numeric) to 0.68 (entity); on RAGTruth the same conditioning input has almost nothing to condition on.

### Root Cause

RAGTruth's six generators answered the *same source document*; their per-family signal distributions overlap far more than the synthetic roster's planted regimes. The metadata (type, generator id) no longer predicts which family is reliable, so a correctly-functioning gate *should* approach uniform. Per §11 this is a finding, not a bug — and the gate's uniformity is itself the evidence.

### Honest Assessment

H3 (interpretable weights) still holds mechanically — the weights are computed, logged and explainable. But an interpreter that says "trust both families equally, everywhere" is not a competitive advantage over a flat model.

---

## Finding #2 — Subtle Hallucinations Are Near-Invisible to Black-Box Signals

### What Happened

A7 trails A0 on every claim-type slice, and all variants cluster between 0.63 and 0.74 — a narrow band consistent with a ceiling imposed by the signals themselves, not the fusion on top of them.

### Root Cause

RAGTruth hallucinations on this slice are dominated by *subtle* conflicts: a sentence that is retrievable from the context (so `support` looks fine) and that other models, decoding from similar knowledge, do not contradict (so `agree`/`contra` look fine). This is the correlated-error failure the proposal itself flags (reviewer attack 5) — shared training distributions produce correlated *misses*, not just correlated errors.

### Honest Assessment

No black-box fusion can rank a claim whose six signals are all healthy. The honest ceiling for this slice is set by signal informativeness; the machinery correctly reports it.

---

## Finding #3 — The Numbers Are Fragile: 11 Positives per Test Slice

### What Happened

Every CI is roughly ±0.2 wide; A7−A0's interval [−0.21, 0.10] cannot separate "loses" from "ties" from "wins". Val-tuned thresholds at a 7% positive rate give catastrophic precision (A0: 0.129) even when recall is high.

### Root Cause

160 test rows with ~11 positives. The slice was sized for a build-time budget (800 claims, ~22 min, $0.00), not for statistical power.

### Honest Assessment

This does not rescue the result — it makes the honest claim "no detectable difference on this slice" rather than "A7 is worse". The distinction must survive into the paper.

---

## What Does NOT Follow From This Result

1. **It does not refute H1.** On synthetic data, per-cell conditional reliability was real and learnable (A5 0.834 numeric). On RAGTruth the *precondition* — metadata predicting reliability — fails, which H1 itself predicts would flatten the gate.
2. **It does not validate A4 as a method.** A4's win is the control doing its job: showing that with these signals, conditioning adds nothing. Per agent.md §8/M3, A4 was not tuned down to flatter A7 — on either dataset.
3. **It does not license signal leakage into the gate** (ADR-001). The fix for "metadata carries nothing" cannot be to make the gate uninterpretable.

## Cheapest Honest Follow-Ups, In Order

1. **Run the full 1,933-source ceiling** — one overnight build, no API cost; multiplies test positives ~10x and shrinks CIs.
2. **Score all folds' claims**, not test-only slices, when reporting the CI width.
3. **Report the subtle-vs-evident label split separately** — the machinery either separates them or it does not; either answer is reportable.

---

## Lessons Learned

1. **A control that beats the method on real data is the project working, not failing** — the entire purpose of A4 is to make this outcome visible instead of publishable-by-accident.
2. **Synthetic validation validates the machinery, never the hypotheses** (C8). The synthetic gate's +0.38 was true *of the planted world*; this document is what happens when the world's priors change.
3. **Gate-weight uniformity is diagnostic, not decorative.** Near-constant weights are the built-in detector for "metadata carries no signal here" (§11) — read them before reading the AUROC.
4. **Power budgeting is part of experimental design.** A slice sized to a build budget cannot answer a hypothesis question; report CI width alongside every point estimate.

## Prevention

- The M6 results table carries the negative result in its title and the paired bootstrap in its body; the same convention applies to any future real-data run.
- Per-slice positive counts are printed next to every AUROC so no number is ever read without its power context.
- DECISIONS.md (M6) records the three root causes above with pointers to the artefacts that evidence them.

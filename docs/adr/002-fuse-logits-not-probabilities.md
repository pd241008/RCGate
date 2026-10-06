# 📜 ADR-002: Fuse Expert Logits, Not Probabilities

> **Status:** `Decided`
> **Date:** October, 2026

---

## 🌎 Context

The gate produces softmax trust weights `w = softmax(gate(x_meta) / τ)` with `w_cross + w_evid = 1`, and each expert produces its own score. The fusion step must combine `w_cross · z_cross` and `w_evid · z_evid` into one meta-learner input. The question is *what* the weights multiply: the experts' raw logits, or their squashed probabilities.

## 🛤️ Options Considered

1. **Fuse logits** (`z ∈ ℝ`) — _keeps the full dynamic range; weights scale evidence, not evidence×0.5._
2. **Fuse probabilities** (`p ∈ (0,1)`) — _feels intuitive ("weighted average of opinions") but shrinks every product toward zero._
3. **Fuse rank-normalised scores** — _scale-free but destroys calibration, which the project must report (ECE)._

---

## 🎯 Decision

> [!IMPORTANT]  
> **Fuse logits by default (`fusion_input: logit` in config). The `prob` variant exists in config only as an ablation.**

## 🧠 Reasoning

Multiplying a probability in (0,1) by a softmax weight in (0,1) shrinks the product quadratically toward zero — with typical weights around 0.5, an expert at p=0.9 contributes 0.45 and one at p=0.1 contributes 0.05, so the meta-learner's input lives in a narrow band near the origin and Φ's linear job becomes an unnecessary uphill fight against squashing. Logits preserve the sign and magnitude of disagreement between experts, which is exactly the information "which family do I trust" is supposed to modulate. Calibration is recovered downstream by the meta-learner itself rather than destroyed twice.

## ⚖️ Consequences

- **Good:** 🟢 Expert disagreement survives fusion; meta-learner input is unbounded, well-scaled; ECE is computed on the final P, not double-squashed intermediates.
- **Bad:** 🔴 The `prob` path must stay tested so the config flag is not a lie; raw logits are less intuitive to explain on stage than "weighted average of two probabilities".

## 🔄 Revisit When

- A calibration-sensitive deployment (risk-scored reporting) shows ECE regression vs the `prob` fusion ablation — then re-measure, do not assume.

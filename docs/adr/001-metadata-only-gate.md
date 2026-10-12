# 📜 ADR-001: The Gate Sees Metadata Only — Signals Never Reach It

> **Status:** `Decided`
> **Date:** October, 2026

> **Status note, October 10, 2026.** The decision in this record still holds: the gate input is metadata only, and tests enforce that constraint. [`docs/RC-Gate_Final_Research_Report_v1.md`](../RC-Gate_Final_Research_Report_v1.md) supersedes the interpretability sentence in Consequences (“interpretable by construction”) and the remark that real-data gate weights sit near 0.45. Returning the weights makes the routing decision inspectable. Table 9 of the final report records that scientific interpretability has not been validated, and that the near-0.45 description is not a Stage 8 measurement. The file map is [`docs/RC-Gate_Experiment_Index.md`](../RC-Gate_Experiment_Index.md).

---

## 🌎 Context

RC-Gate's central claim (H1) is that signal *reliability* is conditional on claim type and generator, so the gate that weights the two experts should be conditioned on exactly that metadata. The six signal values (`agree, contra, sem_dist, support, src_quality, conflict`) are cheap to compute and tempting to feed the gate — but a gate that sees the signals degrades into "a small MLP on the features", indistinguishable from flat fusion (A0) with extra steps, and the trust weights stop meaning "which family is reliable for claims like this" and start meaning "which family happens to be reliable for *this* claim". The project's whole identification strategy collapses if the conditioning variable and the conditioned quantity are the same thing.

## 🛤️ Options Considered

1. **Gate on metadata only (claim type ⊕ generator embeddings)** — _matches the hypothesis exactly; risks under-fitting when metadata is coarse._
2. **Gate on metadata + signals** — _strictly more input, better validation loss in principle, but destroys the interpretation and makes the A4 control meaningless._
3. **Two-stage: signals pick the gate, metadata regularises it** — _a compromise nobody can interpret; not defensible in a viva._

---

## 🎯 Decision

> [!IMPORTANT]  
> **The gate input is exactly `x_meta = [Emb_type ‖ Emb_gen]` (8-d). No signal value ever reaches the gate, and this is enforced by tests, not by discipline.**

## 🧠 Reasoning

The method's contribution is the *inductive bias* — a structural constraint that reliability is a function of metadata — not extra capacity. A4 (flat GBM on signals + metadata) is precisely the "no constraint" control: if A4 matches A7, the honest conclusion is that the gate adds nothing, and that conclusion is only meaningful if A7 truly was constrained. Two tests guard the boundary mechanically: `test_weights_do_not_depend_on_signal_values` perturbs all six signals and asserts the gate weights do not move; `test_signals_do_change_the_experts_and_the_probability` asserts they do move the output. Anyone who wires the signals into the gate breaks the build, not the claim.

## ⚖️ Consequences

- **Good:** 🟢 Trust weights remain interpretable by construction (H3 is checkable, not rhetorical); A4 stays a clean control; the UNK cold-start path is a metadata problem only.
- **Bad:** 🔴 When metadata is coarse — exactly what happened on the real RAGTruth slice, where gate weights sit near 0.45 across cells — the gate *cannot* adapt, and A4 wins. Accepted: that is the finding the design exists to surface, not a bug to patch by leaking signals.

## 🔄 Revisit When

- A "gate sees signals too" variant is built — it must ship as a clearly labelled ablation, never as A7.
- A benchmark appears where generator identity is genuinely unavailable at inference (then the gate degenerates to claim-type-only, A5, which is already implemented).

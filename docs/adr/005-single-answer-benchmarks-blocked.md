# 📜 ADR-005: Benchmarks Without a Generator Panel Are Blocked, Not Faked

> **Status:** `Decided`
> **Date:** October, 2026

---

## 🌎 Context

The M6 milestone lists five benchmarks. The cross-model signal family (`agree, contra, sem_dist`) is *defined* as a comparison across several generators' answers to the same question — that is the "model-aware" half of the method's name. HaluBench (incl. its DROP slice), FinanceBench, and TruthfulQA/HaluEval-QA all ship **one answer per question** — verified against the HaluBench parquet itself (14,900 rows: `id, passage, question, answer, label, source_ds`; no model field, no spans). Using them as-is would mean inventing agreement values, and constraint C3 caps API spend for manufacturing panels with LLM judges.

## 🛤️ Options Considered

1. **Run them with neutral/synthesised cross-model signals** — _produces numbers, but the cross expert would be scoring noise; every table would need an asterisk the paper cannot afford._
2. **Manufacture the panel: NLI-judge each claim against a stored reference, or query LLM judges through the cached client under `max_usd`** — _scientifically honest, but a real design decision with budget and licence implications._
3. **Block the benchmark, record the structural reason, run what is runnable** — _slower breadth; every claim in the paper is backed by an artefact._

---

## 🎯 Decision

> [!IMPORTANT]  
> **Benchmarks that cannot produce all six signals without inventing data are blocked with the reason recorded in `DECISIONS.md`; unblocking them (judge panel design, budget, licence) is flagged to the human, not improvised. RAGTruth — six generators per source, span labels, shipped context, MIT licence — runs.**

## 🧠 Reasoning

C8 (honest reporting) forbids numbers whose provenance is synthetic inference about what other models *would have said*. A cross-model family computed from one answer is not a degraded measurement, it is a different measurement wearing the same column names — and the A1/A7 comparisons would silently absorb the fabrication. Blocking costs breadth but keeps every cell in every table traceable to a real artefact, which is the property the viva and the paper both rest on.

## ⚖️ Consequences

- **Good:** 🟢 No table ever contains invented signals; the blocker reasons are reusable (any future multi-generator dataset can be slotted in immediately); budget stays at $0.00.
- **Bad:** 🔴 M6 delivers one real benchmark instead of five; the paper's real-data section is thinner and the viva will ask why — the answer is a table of structural blockers, which is a stronger position than fabricated breadth.

## 🔄 Revisit When

- The human approves a judge-panel design (then each unblocked benchmark needs its own licence check recorded per §11 before any number appears).
- HaluBench's licence is verified — it is still pending and blocks any HaluBench number regardless of panel design.

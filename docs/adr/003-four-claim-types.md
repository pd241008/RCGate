# 📜 ADR-003: Four Claim Types, Not the Proposal's Three

> **Status:** `Decided`
> **Date:** October, 2026

---

## 🌎 Context

The proposal lists three claim categories; the survey lists four. The data contract needs a single `claim_type` integer, and the whole H1/H2 story is told per claim type — numeric claims are where cross-model agreement is expected to fail (correlated errors), so the taxonomy directly shapes which slices get reported and which gate cells exist.

## 🛤️ Options Considered

1. **Proposal's three categories** — _matches the primary document; loses the extractive/abstractive distinction that RAGTruth labels natively._
2. **Survey's four: numeric, entity, extractive, abstractive** — _finer conditioning, aligns with real benchmark label schemas; one more embedding row to learn._
3. **Free-text claim taxonomy via LLM classifier** — _richest, but violates C7 (no LLM fine-tuning scope creep) and adds API cost to a metadata feature._

---

## 🎯 Decision

> [!IMPORTANT]  
> **Use the survey's four types (0 numeric, 1 entity, 2 extractive, 3 abstractive). The proposal's "numeric/extractive" reporting group is simply types 0 and 2 reported together.**

## 🧠 Reasoning

RAGTruth — the one benchmark satisfying every C1–C7 constraint — annotates extractive and abstractive hallucinations as genuinely different phenomena (span copies vs paraphrases), and the rule-based classifier (digits/operators/units → numeric; entity lookups → entity; span-from-context → extractive; else abstractive) maps onto those labels without an LLM. Collapsing them would merge two reliability regimes into one gate cell and quietly destroy the per-type analysis the review hinges on. The reconciliation with the proposal is a reporting convention, not a modelling compromise.

## ⚖️ Consequences

- **Good:** 🟢 Gate cells match benchmark label schemas; per-type tables are directly comparable to RAGTruth's own taxonomy; rule-based typing stays CPU-cheap and inspectable.
- **Bad:** 🔴 The proposal text and the implementation disagree on paper — every results table must state the four-type convention once, or a reviewer comparing documents sees an unexplained mismatch.

## 🔄 Revisit When

- A benchmark's labels force a different taxonomy (then remap in the loader, never in `claim_type.py` — the rule classifier is the single source of truth for the integer).

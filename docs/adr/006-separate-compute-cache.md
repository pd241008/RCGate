# 📜 ADR-006: Separate Compute Cache From the API Budget

> **Status:** `Decided`
> **Date:** October, 2026

---

## 🌎 Context

C3 requires every LLM/search call to flow through one disk cache with `--dry-run` and hard `max_usd`/`max_calls` caps — written when the assumption was that *everything* touching a model costs money. M5 introduced local NLI (DeBERTa-v3-small) and MiniLM embeddings: thousands of calls per build (~12,300 for the 800-claim RAGTruth slice), all on CPU, all free, all slow enough to want caching. Routing them through the API cache would charge free compute against the USD cap and block cached offline reruns behind `--dry-run` — making both the budget accounting and the test story wrong.

## 🛤️ Options Considered

1. **One cache for everything** — _simplest mental model; corrupts budget accounting (free calls consume `max_usd`) and makes `--dry-run` useless for real builds._
2. **No cache for local compute** — _honest accounting, but every rebuild re-pays ~35 s of CPU per table and the C4 "second run from cache" acceptance test fails by construction._
3. **Two caches: `.cache/api` (metered, capped, dry-runnable) and `.cache/compute` (local, uncapped, always allowed)** — _slightly more code; each cache's semantics match its cost model._

---

## 🎯 Decision

> [!IMPORTANT]  
> **Local NLI/embedding inference goes through a dedicated `.cache/compute`, deliberately separate from the metered API cache: it is never charged against `max_usd`, never blocked by `--dry-run`, and never touched by tests (tests use the lexical fallback).**

## 🧠 Reasoning

The cap exists to protect money, and the `--dry-run` switch exists to let a build prove what it *would* spend — both semantics break if free local inference flows through the same ledger. Separating them keeps each artefact's invariants true: the API cache answers "what did we spend", the compute cache answers "what have we already computed". The lexical NLI fallback (labelled `backend=lexical` in any result it produces) keeps tests and CI on the no-network path, so the compute cache is a performance artefact, never a correctness dependency.

## ⚖️ Consequences

- **Good:** 🟢 Budget tables report real API spend ($0.00 so far); cached rebuilds are near-instant (5,201 cached / 0 computed NLI calls on the forced M5 rebuild); `--dry-run` remains meaningful.
- **Bad:** 🔴 Two cache directories to reason about; a stale compute cache can silently serve an old model's outputs — mitigated by keying on (model name, backend, input hash), and by the M5 acceptance test that asserts a fully-cached second run.

## 🔄 Revisit When

- Any paid inference moves into the compute path (it must migrate back to the metered cache or the cap is a lie).
- The cache outgrows disk — then evict by (benchmark, backend) with the build CLI, never by hand.

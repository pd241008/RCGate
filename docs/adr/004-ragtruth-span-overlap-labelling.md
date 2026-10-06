# 📜 ADR-004: RAGTruth Labelling — Span Overlap, Corpus Not Oracle, Own Split Ignored

> **Status:** `Decided`
> **Date:** October, 2026

---

## 🌎 Context

RAGTruth ships human-annotated hallucination *spans* inside per-sentence responses, plus the reference text the answers were generated from, plus a train/test field. Turning that into the signal table requires three choices at once: how a sentence-level claim inherits a span label, what the evidence corpus is for BM25, and how rows are split. Each choice can silently inflate or deflate every downstream number.

## 🛤️ Options Considered

1. **Exact-span-only labelling** — _precise, but discards a third of annotations that cross sentence boundaries; systematically under-counts hallucinations on long sentences._
2. **Span-overlap labelling** — _a sentence is hallucinated when it overlaps an annotated span; keeps boundary-crossing annotations; risks over-counting partially-faithful sentences._
3. **Oracle evidence (annotate against the reference as ground truth)** and/or **respect the dataset's train/test field** — _the former inflates `support` beyond what a deployment could achieve; the latter splits by source document, so sibling claims land on both sides of the boundary._

---

## 🎯 Decision

> [!IMPORTANT]  
> **Label by span overlap; use the shipped reference text as the BM25 evidence corpus (what a deployment with the documents in hand would do, never as an oracle); ignore RAGTruth's own split field and split by `question_id` per C6.**

## 🧠 Reasoning

Exact-span matching throws away 33% of annotations for a precision gain nobody can bank — the unit of downstream decision-making is the claim (sentence), so the label must live at that granularity too. The reference-as-corpus choice is the deployment-faithful one: in production the evidence store holds the retrieved documents, and retrieval quality is a real cost the system should be measured against; treating the reference as an oracle would give `support` a meaning no deployed system could reproduce. And C6 exists because a grouped split is the only split under which a six-generator source cannot leak across the boundary — the dataset's field knows nothing about generator panels.

## ⚖️ Consequences

- **Good:** 🟢 Labels comparable across sentence lengths; evidence signal means what a real deployment would get; split hygiene is uniform across every benchmark in the table.
- **Bad:** 🔴 Partially-faithful sentences count as hallucinated, adding label noise near spans; results are not directly comparable to papers that use exact-span matching or the dataset's own split — the deviation must be stated wherever numbers are reported.

## 🔄 Revisit When

- A second span-labelled benchmark enters (then re-check that overlap labelling transfers rather than assuming it).
- A reviewer disputes the label noise — quantify by reporting the fraction of overlap-only positives separately.

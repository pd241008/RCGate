# 📜 ADRs — RC-Gate

> Every decision here comes from a real constraint hit during the M0–M7 build. The one-line version of each lives in [`DECISIONS.md`](../../DECISIONS.md); the full tradeoff lives here.

| ADR | Decision | Source |
| --- | -------- | ------ |
| [ADR-001](./001-metadata-only-gate.md) | The gate sees metadata only — signals never reach it, enforced by tests | M0/M3 (C1, §6) |
| [ADR-002](./002-fuse-logits-not-probabilities.md) | Fuse expert logits, not probabilities | M3 (§6) |
| [ADR-003](./003-four-claim-types.md) | Four claim types (survey), not the proposal's three | M1 (§5) |
| [ADR-004](./004-ragtruth-span-overlap-labelling.md) | RAGTruth: span-overlap labels, corpus-not-oracle evidence, `question_id` splits | M5 |
| [ADR-005](./005-single-answer-benchmarks-blocked.md) | Benchmarks without a generator panel are blocked, not faked | M6 |
| [ADR-006](./006-separate-compute-cache.md) | Separate compute cache from the API budget | M5 (C3) |

## Format

Each ADR follows the [Design Dungeons template](https://github.com/pd241008/Design-Dungeons): Context → Options Considered → Decision → Reasoning → Consequences (good/bad) → Revisit When. Status is `Decided` once shipped; superseded ADRs keep their file and gain a note, they are never edited into silence.

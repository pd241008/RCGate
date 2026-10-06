# Postmortem 001: Stale Signal Table Silently Reused During M6 Builds

> **Date:** October 5, 2026  
> **Severity:** High — one of three evaluation tables was the wrong data  
> **Status:** Complete — caught before any number was reported

## Issues Summary

During M6, the RAGTruth slice was enlarged from 200 to 800 claims and three table builds (seeds 0–2) were launched in parallel. Seed 0 exited within seconds while seeds 1–2 kept computing. The cause: `ensure_table` skips generation when the target file exists, and `data/signal_tables/ragtruth_s0.parquet` still held the **old 200-row M5 table**. Without `--force`, one third of the evaluation would have been run on the wrong slice — mixed row counts, different positive rates, unmergeable splits — with no error.

---

## Finding #1 — The Silent Exit Looked Like Success

### What Happened

The build CLI's contract was "reuse an existing table unless `--force`" — correct behaviour for the M5 acceptance test ("a second run served entirely from cache"). But the M6 config change (800 claims, `claims_per_source` retuned) invalidated the existing artefact while the filename stayed identical. The seed-0 build validated nothing about the table it was skipping: not row count, not schema, not config hash.

### Root Cause

Filename identity was treated as artefact identity. The cache key that correctly gates *NLI calls* (input hash) and the *table existence check* (path exists) had different strength, and the weaker one sat in front of the stronger one.

### Honest Assessment

Nothing downstream crashed — the mixed tables would have merged cleanly at the pandas level, since both are valid signal tables with identical columns. The corruption would have surfaced only as an unexplained ~4x positive-rate disparity between seeds, if at all. This is the worst kind of failure mode in a research repo: wrong numbers that look plausible.

---

## Finding #2 — Detection Was Accidental, Prevention Is Structural

### What Happened

The bug was caught by watching process CPU time, not by any check. After the discovery, seed 0 was rebuilt with `--force` (198 fresh NLI calls; seeds 1–2 had already warmed the shared compute cache), and the final M6 table was verified: 800 rows × 3 seeds, ~57 positives each, 134 sources, all six generators.

### Root Cause

The build pipeline had no assertion tying table shape to config. The fix belongs in the builder, not in human vigilance.

### Prevention

- Builds that would reuse a table **must** verify it against the current config (row expectations, schema) or refuse; `--force` remains the explicit override.
- Rule adopted repo-wide: when a config parameter that determines table shape changes, the build either fails loudly or regenerates — it never silently mixes generations.
- Recorded in `DECISIONS.md` (M6) because the acceptance criterion ("cached rerun") is what made the reuse path attractive in the first place.

---

## Lessons Learned

1. **Existence is not validity.** A cached artefact check must validate against the thing that made it stale, or `--force` becomes a manual, error-prone contract.
2. **Parallel launches hide single-point failures.** Seed 0's instant "success" was invisible among two healthy workers; any stage that can no-op should say so on stdout.
3. **The failure that looks like a fast cache hit is the one to distrust most** — the M5 acceptance criterion trained exactly the wrong reflex.

## Prevention (implemented)

- M6 builds re-verified row counts and positive rates per seed before evaluation; the numbers are in `DECISIONS.md`.
- The build CLI's `--force` semantics and the config-hash check are now the documented contract in `docs/adr/006-separate-compute-cache.md` (cache-key discipline).

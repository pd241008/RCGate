# DECISIONS

One line per judgment call. Newest at the bottom. M0 entries come first.

## M0 — Scaffold

- Environment has Python 3.14.6, not the 3.11 named in the spec; all code is written to 3.11 syntax so it runs on both. No pin change needed.
- `typer` install was denied, so every CLI is built on stdlib `argparse` (`rcgate/train.py`, `rcgate/evaluate.py`, `rcgate/explain.py`). Argument names match what `typer` would have produced.
- `streamlit` install was denied, so `demo/app.py` is written but cannot be executed here; it is guarded by an import check in tests and flagged as unverified in the README.
- Interpreter-specific dependency versions are not pinned to exact patches (no lockfile); `pyproject.toml` pins the major stack instead. Rationale: the environment ships Python 3.14 wheels that older pins may not resolve.
- Split unit is `question_id` (constraint C6). Splitting by claim would leak sibling claims from the same question across train/test.
- `UNK` generator is a *sentinel id* (`generators.yaml` count `G`, i.e. the next free integer), not a string, so `generator_id` stays an `int` as the data contract requires.
- All randomness flows from a single `seed` per run; per-seed variation is created by seeding Python/NumPy/torch, not by shuffling the input file.

## M1 — Synthetic data with planted structure

- Planted emission probabilities live in `configs/planted.yaml`, not in `synthetic.py`. A viva question about "why is numeric contra 0.12" should be answerable by reading one file.
- `src_quality` is deliberately absent from the planted tables. It is a property of the evidence source, so it is emitted from the generator roster plus jitter and carries no label information. A label-conditioned value there would invent precision the heuristic does not have (spec section 8, M5 note).
- The numeric failure mode is planted as *anti-informative*, not merely uninformative: `agree` is flat (0.85 vs 0.80) and `contra` is inverted (0.45 faithful vs 0.12 hallucinated), because all generators copy the same wrong number from a shared source table. Merely making the cross family uninformative would not have failed the M2 gate, since a flat model would still rank numeric claims correctly off the evidence signals. This is the mechanism behind reviewer attack 5 (correlated LLM errors).
- Question and answer random effects were raised to 0.7 / 1.1 on the logit. At the original 0.12 / 0.25 the within-answer variance inflation was only 1.02x, i.e. question grouping bought nothing; it is now ~1.4x, so a claim-level split would leak materially.
- Four claim types are used (numeric, entity, extractive, abstractive), matching the survey rather than the proposal's three. The proposal's "numeric/extractive" reporting group is types 0 and 2 reported together.
- Full-scale table: 900 questions x 5 generators x 2-4 claims = ~13.5k claims, comfortably over the 4,000 floor. Smoke config uses a 220-question table.
- Label noise is applied *after* signal emission, so signals reflect the latent truth and the label is a noisy observation of it. That is why no single signal reaches AUROC 1.0.

## M2 — Baselines A0-A4

- **M2's acceptance criterion contradicts M1's prose, and this is the important finding of the milestone.** M1 prescribes "numeric claims: agree is high regardless of label, `support` and `conflict` informative" and "entity claims: both signal families informative". If the evidence family is informative for *every* claim type, a flat logistic regression simply ignores the cross-model family and scores 0.91 AUROC on numeric. The M2 target of A0-numeric < 0.65 is then unreachable by any generator, not just by this one. Measured directly: evidence-family-only LR gets numeric 0.890 and pooled 0.908.
- Resolution, per M2's own instruction to "fix it before continuing": the planted table now has two opposing conflict cells. Numeric trusts evidence and has an **anti-informative** cross family (agree flat, contra inverted, because a shared-source numeric error makes every generator emit the same wrong number). Entity, extractive and abstractive trust cross-model consensus and have a **near-null** evidence family. The M1 numeric mechanism is preserved verbatim; the deviation is that evidence is weak off numeric, which M1's "entity: both informative" did not anticipate.
- A sweep over evidence strength (`f` off-numeric, `g` on numeric, 18 combinations, 3 tables each) found the reachable region: `A0 numeric < 0.65` requires `f <= 0.35`. Final values sit at evidence gaps of 0.13-0.25 on numeric and 0.02-0.14 elsewhere.
- **The evidence gap on numeric must stay *smaller* than the cross gap (0.68) or flat fusion wins anyway.** An intermediate attempt set numeric `support` to a gap of 0.68, equal to `contra`'s; the flat model then resolved the tie in its own favour and A0-numeric went back to 0.92. This is a magnitude condition, not a sign condition, so it is fragile by nature and is the main thing to re-check if the planted numbers are ever edited.
- `sem_dist` is deliberately uninformative everywhere. With it informative on three claim types it is collinear with `contra`, the flat LR moved the cross family's weight onto it, `contra`'s weight collapsed to -0.11, and the numeric failure disappeared entirely. Costs realism; documented in `configs/planted.yaml`.
- A3 is implemented as a genuine static scalar, not a two-feature LR: `logit = b + s * (alpha * z_cross + (1 - alpha) * z_evid)` with alpha grid-searched over 101 values on validation AUROC and ties broken toward alpha = 0.5. This is the control that separates *learning* a blend from *conditioning* it.
- `stratify=True` is the default in `grouped_split`. Hallucination rates differ a lot between cells and an unstratified split can leave a slice single-class.
- Per-seed tables: `data.table` accepts a `{seed}` placeholder and one table is generated per `data.table_seeds`. A config can no longer claim 4 generators over a 5-generator table, which is what let A4 crash in the first smoke run.
- Duplicate YAML keys are now rejected by the loader. PyYAML silently keeps the last value, and `configs/synthetic.yaml` had `n_questions` twice (900 declared, 1400 used).

### M2 acceptance result (5 tables x 5 seeds, mean test AUROC)

| variant | numeric | entity | extractive | abstractive | all |
|---------|---------|--------|------------|-------------|-----|
| A0 flat LR | **0.478** | 0.858 | 0.837 | 0.805 | 0.756 |
| A1 cross only | 0.060 | 0.926 | 0.882 | 0.882 | 0.650 |
| A2 evidence only | 0.833 | 0.608 | 0.696 | 0.613 | 0.692 |
| A3 static alpha | 0.470 | 0.860 | 0.837 | 0.807 | 0.756 |
| A4 flat GBM + metadata | 0.942 | 0.927 | 0.911 | 0.922 | 0.929 |

A0 numeric 0.478 < 0.65 and A0 entity 0.858 > 0.85: **gate met.**

**Flag for the human (reviewer attack 1, "is this just metadata leakage?"):** A4 reaches 0.942 on numeric against A7's expected ~0.85. A gradient-boosted tree given claim type and generator identity can learn the per-cell interaction directly, which is precisely the function the gate is supposed to provide. This is an honest negative for H2 on synthetic data and must be reported, not tuned around. It does not refute H1 or H3, and it predicts that on real data, where metadata is coarser and evidence quality varies within a cell, A4 should degrade faster than A7.

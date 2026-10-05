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

## M3 — RC-Gate

- A7 has **229 trainable parameters** (A5 141, A6 149), against the ~50k cap. Gate input is exactly 8-d as specified: two 4-d embeddings, `MLP(8 -> 16 -> 2)` with ReLU.
- Signals are **not** standardised before the experts. All six already live in [0,1], so the spec's unscaled `Linear(3 -> 1)` is the literal reading. `standardize_signals` exists in config but defaults to off.
- `tau` is a fixed config value, not learned. A learnable temperature would let the model flatten its own weights toward uniform, which is the collapse H3 is meant to rule out.
- `standardize_signals` / `fusion_bias` / `dropout` are exposed in config but left at spec defaults; no staged-training ablation was built, since A3 already serves as the flat-blend control and staging is listed as optional.
- Trained end to end with BCE on `P`, Adam, early stopping on validation AUROC, best-state restore. `unk_dropout=0.1` sends the generator to the reserved `UNK` embedding row during training.
- The signal tables are left unscaled in the loader, so the expert input is the raw triple. Confirmed by test: perturbing one family moves only its own expert logit.
- **Tests that guard the method's central claim**: `test_weights_do_not_depend_on_signal_values` perturbs the signals and asserts the gate weights do not move, while `test_signals_do_change_the_experts_and_the_probability` asserts they do change the output. Together these fail if anyone ever wires the signals into the gate.

### M3 acceptance result (5 tables x 5 seeds, mean test AUROC)

| variant | numeric | entity | extractive | abstractive | all | params |
|---------|---------|--------|------------|-------------|-----|--------|
| A0 flat LR | 0.478 | 0.858 | 0.837 | 0.805 | 0.756 | - |
| A2 evidence only | 0.833 | 0.608 | 0.696 | 0.613 | 0.692 | - |
| A3 static alpha | 0.470 | 0.860 | 0.837 | 0.807 | 0.756 | - |
| A4 flat GBM + metadata | **0.942** | **0.927** | **0.911** | **0.922** | **0.929** | - |
| A5 gate on claim type | 0.834 | 0.932 | 0.913 | 0.898 | 0.902 | 141 |
| A6 gate on generator | 0.640 | 0.884 | 0.800 | 0.851 | 0.804 | 149 |
| A7 full RC-Gate | 0.855 | 0.870 | 0.867 | 0.841 | 0.875 | 229 |

- **A7 beats A0 on numeric by +0.377** (0.855 vs 0.478), against a target of +0.15. Met.
- **Mean `w_evid` on numeric = 0.809**, against a target of >0.7. Met.
- **The gate did not collapse.** Cell-mean `w_cross` has a spread of 0.199 across (claim type, generator) cells, and claim type alone moves `w_cross` from 0.19 (numeric) to 0.68 (entity).
- **A4 beats A7 on every claim type.** This is an honest negative for H2 on synthetic data and is reported as such. A gradient-boosted tree given claim type and generator can learn the per-cell reliability function directly; the gate's inductive bias is a constraint, not an advantage. Per the spec, A4 was not tuned down.
- **Claim-type conditioning does nearly all the work; generator conditioning adds little.** A5 (claim type only) reaches 0.834 on numeric against A7's 0.855, and A6 (generator only) reaches only 0.640. So H1 is strongly supported for the claim-type half and barely supported for the generator half.
- **The generator effect is weak and unstable.** The inverted generator (4) shifts `w_cross` down within a claim type by -0.060 (extractive) and -0.061 (abstractive), but per claim type the paired t-test over 5 seeds gives p = 0.08 to 0.33 and is not significant. Pooled across the four claim types the delta is -0.038 with p = 0.0053. Seed 3 gives a delta of exactly 0.000 (smallest embedding norms of any seed, a partial collapse), so the criterion "measurably different" is met only in aggregate, not per claim type. Reported as a partial pass rather than a pass.
- **Two distinct solutions to the inverted-generator dilemma, across seeds.** Seeds 0, 2 and 4 learn `agree = +0.4..0.65, contra = -3.1..-3.4`; seed 1 learns the reverse sign assignment with `agree = -0.37, contra = +3.20`. The benchmark admits more than one correct weighting, which is worth saying out loud in a viva rather than presenting one seed's weights as "the" explanation.
- `alpha` for A3 lands at ~0.03, i.e. almost pure evidence-family weighting overall. That is the point: A3 can only learn one global compromise, and on this table the compromise is evidence-first, which is exactly wrong for the three non-numeric types.

## M4 — Evaluation harness

- One command produces everything: `python -m rcgate.evaluate --config synthetic --bootstrap 1000` writes `results/summary/synthetic.md`, a `.json` twin, and a gate-weight heatmap PNG. Full run is 9 variants x 5 tables x 5 seeds and takes ~17 min on CPU.
- The report leads with a **SYNTHETIC DATA** banner naming H1-H3 as out of scope, and every commit of a summary table must carry that label (constraint C8).
- Bootstrap CIs are computed per seed and then averaged, rather than pooling claims across seeds. Pooling would resample the same claim ids repeatedly under five different splits and report an interval that is too narrow.
- **The headline H2 test is a paired bootstrap, not a difference of two CIs.** A7 and A0 are scored on identical test rows with one shared resample per replicate. Per-claim-type CIs in the main tables are claim-level resamples; `metrics.bootstrap_auroc_ci_grouped` provides a question-clustered variant that ignores within-question correlation, and is the more conservative choice when there is time to run it.
- `auroc_fast` (rank form via `scipy.stats.rankdata`) replaced sklearn's `roc_auc_score` inside the bootstrap loops, ~10x faster; `tests/test_metrics.py` asserts the two agree. 1,000-resample CIs on ~2,700-row slices are otherwise not affordable.
- Per-cell (claim type x generator) tables are point estimates only: 20 cells x 5 seeds x 9 variants with CIs would dominate the runtime for little extra information.
- Every run records wall clock and API accounting in the report's cost table, so reviewer attack 3 (latency and cost) is answered from the artefacts rather than from memory.

### M4 acceptance result (synthetic, 5 tables x 5 seeds)

Overall AUROC: A0 0.756, A1 0.650, A2 0.692, A3 0.756, A4 **0.929**, A5 0.902, A6 0.804, A7 0.874.

Paired bootstrap, A7 minus A0:

| slice | delta AUROC | 95% CI | p(A7 better) |
|---|---:|---|---:|
| all | +0.118 | [0.102, 0.133] | 0.974 |
| numeric | **+0.377** | [0.341, 0.414] | **1.000** |
| entity | +0.011 | [-0.014, 0.037] | 0.800 |
| extractive | +0.029 | [0.006, 0.053] | 0.800 |
| abstractive | +0.036 | [0.008, 0.063] | 0.800 |

H2 is supported on numeric and marginal on the other three types. A4 still beats A7 overall.

**Leave-one-generator-out is the strongest result in the project.** Holding out generator 4, the planted *inverted* family, and scoring only the UNK rows:

| held out | A0 UNK AUROC | A7 UNK AUROC | A0 seen | A7 seen |
|---|---:|---:|---:|---:|
| 0 | 0.742 | 0.891 | 0.743 | 0.908 |
| 1 | 0.775 | 0.904 | 0.734 | 0.905 |
| 2 | 0.749 | 0.908 | 0.740 | 0.904 |
| 3 | 0.746 | 0.915 | 0.740 | 0.902 |
| 4 (inverted) | **0.171** | **0.748** | 0.816 | 0.910 |

A0 scores **0.171** on the unseen inverted generator -- worse than random, because the global coefficient it learned for `agree` has exactly the wrong sign there. A7 degrades to 0.748 and stays useful. This is the cleanest available answer to reviewer attack 2 ("does it generalise to unseen generators?"), and it is a stronger result than the in-distribution comparison.

## M5 — Real signal extractors

- RAGTruth is the first real benchmark because it is the only dataset found that ships all three things the gate needs with no API key: six generators answering the same source document, human span labels, and the evidence text itself. Licence MIT; both downloads are sha256-pinned in `data/benchmarks/`.
- A claim is a sentence of a response, labelled hallucinated when it *overlaps* an annotated span. Exact-span-only matching was rejected because it discards a third of the annotations that cross sentence boundaries.
- The shipped reference text is used as the BM25 evidence corpus, not as an oracle: the answers were generated from it, so retrieval over it is what any deployment with the documents in hand would do.
- The dataset's own train/test field is ignored. Constraint C6 wants question-grouped splits for every benchmark, so one source's six generators can never sit on both sides of a boundary.
- A naive first-200 slice collapsed onto six source documents, i.e. a grouped split over six questions is not an evaluation. `claims_per_source: 6` spreads the same 200 claims over ~34 sources with all six generators represented.
- The compute cache `.cache/compute` is deliberately separate from the API cache: local NLI/embedding calls cost nothing, so they must neither be charged against `max_usd` nor blocked by `--dry-run`. Models are `nli-deberta-v3-small` + MiniLM-L6-v2, per C2.
- The lexical NLI fallback exists so tests and CI run with no model download; its scores are much weaker and any result produced with it must be labelled `backend=lexical`.
- `contra` is a max, not a mean: one generator flatly denying a claim is what a human reviewer cares about. Rows with no other generator get neutral 0.5/0.5/1.0 and are flagged via `cross_n_others` instead of silently averaged.
- Arithmetic checking is deterministic and refuses to guess: `847 x 12` is checked exactly, "a dozen less than three times the total" is not attempted. All 53 numeric claims in the slice were `UNVERIFIABLE`, so the check folded nothing into support — recorded rather than fudged.

### M5 acceptance result

Table builds end to end on the 200-claim RAGTruth slice: 34 sources, all six generators represented, 8/200 hallucinated. First build: 37.6s wall, 5,201 NLI calls, all local CPU (33.7s compute). Second build served entirely from cache in 2.4s. pytest: 182 passed. ruff: clean.

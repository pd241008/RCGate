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

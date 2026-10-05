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

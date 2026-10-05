"""The one signal table every modelling code path reads (proposal section 5).

Extractors write it; baselines, RC-Gate and the evaluation harness only ever read it.
That decoupling is what lets M2-M4 rerun in seconds without touching an API.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# -- columns -----------------------------------------------------------------
ID_COLS = ["question_id", "claim_id"]
CONTEXT_COLS = ["benchmark", "claim_text"]
META_COLS = ["claim_type", "generator_id"]
CROSS_SIGNALS = ["agree", "contra", "sem_dist"]
EVID_SIGNALS = ["support", "src_quality", "conflict"]
SIGNALS = CROSS_SIGNALS + EVID_SIGNALS
LABEL_COL = "label"

SIGNAL_COLUMNS = ID_COLS + CONTEXT_COLS + META_COLS + SIGNALS + [LABEL_COL]

#: Optional columns that extractors may add. Read defensively, never required.
OPTIONAL_COLUMNS = [
    "context",
    "source",
    "arithmetic_verified",
    "n_claims_in_answer",
    "judge_votes",
    "judge_n",
]

# -- vocabularies ------------------------------------------------------------
CLAIM_TYPES: dict[int, str] = {0: "numeric", 1: "entity", 2: "extractive", 3: "abstractive"}
CLAIM_TYPE_NAMES = list(CLAIM_TYPES.values())
N_CLAIM_TYPES = len(CLAIM_TYPES)
NUMERIC, ENTITY, EXTRACTIVE, ABSTRACTIVE = 0, 1, 2, 3

BENCHMARKS = ["synthetic", "truthfulqa", "ragtruth", "drop", "financebench"]

#: Reserved generator id for "generator not seen at training time" (proposal challenge 5).
UNK_GENERATOR = -1


def signal_frame(rows: list[dict]) -> pd.DataFrame:
    """Build a frame with the canonical column order and dtypes."""
    df = pd.DataFrame(rows)
    for col in ID_COLS + CONTEXT_COLS + [LABEL_COL]:
        if col not in df.columns:
            df[col] = ""
    for col in META_COLS:
        if col not in df.columns:
            df[col] = 0
    for col in SIGNALS:
        if col not in df.columns:
            df[col] = 0.0
    df = df[SIGNAL_COLUMNS].copy()
    df["claim_type"] = df["claim_type"].astype("int64")
    df["generator_id"] = df["generator_id"].astype("int64")
    df["label"] = df["label"].astype("int64")
    df[SIGNALS] = df[SIGNALS].astype("float64")
    return df


@dataclass
class SchemaReport:
    ok: bool
    problems: list[str]

    def raise_if_failed(self) -> None:
        if self.problems:
            raise ValueError("signal table schema problems:\n  " + "\n  ".join(self.problems))


def validate(df: pd.DataFrame, *, require_labels: bool = True) -> SchemaReport:
    """Check the contract: columns, ranges, keys, and label values."""
    problems: list[str] = []

    missing = [c for c in SIGNAL_COLUMNS if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")
        return SchemaReport(ok=False, problems=problems)

    if df["claim_id"].duplicated().any():
        dupes = df.loc[df["claim_id"].duplicated(), "claim_id"].head(3).tolist()
        problems.append(f"claim_id not unique, e.g. {dupes}")

    for col in SIGNALS:
        values = df[col].to_numpy(dtype="float64")
        if not pd.Series(values).between(0.0, 1.0).all():
            bad = float(pd.Series(values).dropna().abs().max())
            problems.append(f"signal {col} outside [0,1] (max |value| {bad:.4f})")

    if df["claim_type"].isin(CLAIM_TYPES).all() is False or not df["claim_type"].isin(CLAIM_TYPES).all():
        problems.append(f"claim_type outside {sorted(CLAIM_TYPES)}")

    if require_labels:
        if not df["label"].isin([0, 1]).all():
            problems.append("label must be 0/1")
    else:
        if df[LABEL_COL].isna().any():
            problems.append("labels required for training/eval but contain NaN")

    if df["question_id"].astype(str).eq("").any():
        problems.append("question_id must be non-empty")

    return SchemaReport(ok=not problems, problems=problems)


def split_xy(df: pd.DataFrame) -> tuple[list[list[float]], list[int], list[int]]:
    """Return ``(signals, meta, labels)`` as plain lists for sklearn baselines."""
    x = df[SIGNALS].to_numpy(dtype="float64").tolist()
    m = df[META_COLS].to_numpy(dtype="float64").tolist()
    y = df[LABEL_COL].to_numpy(dtype="int64").tolist()
    return x, m, y


def onehot_meta(df: pd.DataFrame, n_generators: int) -> list[list[float]]:
    """One-hot ``[claim_type x 4, generator_id x (G+1)]`` for the A4 control."""
    rows: list[list[float]] = []
    for claim_type, generator_id in zip(df["claim_type"], df["generator_id"], strict=True):
        vec = [0.0] * N_CLAIM_TYPES
        vec[int(claim_type)] = 1.0
        gen = [0.0] * (n_generators + 1)
        gen[_generator_index(generator_id, n_generators)] = 1.0
        rows.append(vec + gen)
    return rows


def _generator_index(generator_id: int, n_generators: int) -> int:
    """Map a real generator id into one-hot space, folding ``UNK`` into the last slot."""
    if generator_id == UNK_GENERATOR:
        return n_generators
    if 0 <= generator_id < n_generators:
        return int(generator_id)
    raise ValueError(f"generator_id {generator_id} out of range for {n_generators} generators")


def signal_slices(df: pd.DataFrame) -> dict[str, list[list[float]]]:
    """Split the six signals into the two families the gate later weighs."""
    return {
        "cross": df[CROSS_SIGNALS].to_numpy(dtype="float64").tolist(),
        "evid": df[EVID_SIGNALS].to_numpy(dtype="float64").tolist(),
    }

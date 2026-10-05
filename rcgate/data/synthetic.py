"""Synthetic signal table with planted conditional reliability (milestone M1).

The point of this module is to produce a table where the *true* relationship between
each signal family and the label is known per (claim type, generator), so the M2 and M3
acceptance criteria can be checked against ground truth rather than against a hunch.

It validates the machinery, not the hypotheses. Every result derived from it is labelled
**synthetic** (constraint C8).

All emission parameters live in ``configs/planted.yaml``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config, load_config
from ..paths import PROJECT_ROOT, TABLES_DIR
from .schema import CLAIM_TYPE_NAMES, SIGNALS, signal_frame, validate

#: Concentration of the Beta used to emit each signal. Higher = less spread around the
#: planted mean. Chosen so signals look like real-valued model scores, not 0/1 flags.
EMIT_CONCENTRATION = 8.0

_TOPIC_NOUNS = [
    "Aurora", "Bellweather", "Calder", "Dunmore", "Everly", "Fairhaven",
    "Granite Bay", "Halstead", "Ironbridge", "Juniper",
]
_YEARS = ["2016", "2017", "2018", "2019", "2020", "2021"]
_UNITS = ["units", "tonnes", "kilometres", "megawatt-hours", "shares"]
_ROLES = ["chief executive", "regional director", "board chair", "operations lead"]


@dataclass(frozen=True)
class RosterEntry:
    id: int
    family: str
    src_quality: float
    note: str


def load_planted(path: str | Path | None = None) -> Config:
    return load_config(path or PROJECT_ROOT / "configs" / "planted.yaml")


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype="float64")))


def _sigmoid_scalar(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-float(x))))


def _emit(rng: np.random.Generator, mean: float, concentration: float = EMIT_CONCENTRATION):
    """Draw a value in (0,1) whose mean is ``mean``. Keeps range checks trivially true."""
    mean = float(np.clip(mean, 1e-3, 1 - 1e-3))
    alpha = mean * concentration
    beta = (1.0 - mean) * concentration
    return rng.beta(alpha, beta)


def _lookup(table: Config, claim_type_name: str, latent_hallucinated: bool) -> float:
    key = "hallucinated" if latent_hallucinated else "faithful"
    return float(table[claim_type_name][key])


def _make_context(rng: np.random.Generator, noun: str, year: str, unit: str) -> str:
    n1, n2 = int(rng.integers(120, 900)), int(rng.integers(4, 40))
    return (
        f"According to the {noun} annual report for {year}, total output reached "
        f"{n1} {unit} across all sites, up from {n2} {unit} in the prior period."
    )


def _claim_text(claim_type: int, rng: np.random.Generator, context: str, latent: bool) -> str:
    """Plausible surface text so the claim-type rules (M5) can be exercised on it."""
    noun = _TOPIC_NOUNS[int(rng.integers(len(_TOPIC_NOUNS)))]
    year = _YEARS[int(rng.integers(len(_YEARS)))]
    unit = _UNITS[int(rng.integers(len(_UNITS)))]
    n1 = int(rng.integers(120, 900)) + (37 if latent else 0)
    n2 = int(rng.integers(4, 40))

    if claim_type == 0:  # numeric
        verb = "increase" if latent else "decrease"
        return f"In {year}, total output reached {n1} {unit}, a {verb} of {n2} {unit}."
    if claim_type == 1:  # entity
        other = _TOPIC_NOUNS[(int(rng.integers(len(_TOPIC_NOUNS))) + 3) % len(_TOPIC_NOUNS)]
        return f"The {noun} facility is operated from {other} by a regional contractor."
    if claim_type == 2:  # extractive: a span lifted from the context
        span = context.split(" reached ", 1)[-1].rstrip(".").strip()
        return f"The report states total output of {span}."
    role = _ROLES[int(rng.integers(len(_ROLES)))]
    return f"The {noun} programme is managed by the {role} and reviewed annually."


def generate(
    cfg: Config | None = None,
    seed: int = 0,
    n_questions: int | None = None,
    n_generators: int | None = None,
) -> pd.DataFrame:
    """Build the planted signal table. Deterministic given ``seed`` and ``cfg``."""
    cfg = cfg or load_planted()
    rng = np.random.default_rng(seed)

    roster: list[RosterEntry] = [
        RosterEntry(int(e["id"]), str(e["family"]), float(e["src_quality"]), str(e["note"]))
        for e in cfg.generator_roster
    ]
    n_generators = n_generators or len(roster)
    roster = roster[:n_generators]

    n_questions = int(n_questions or cfg.get("n_questions", 900))
    claims_lo, claims_hi = 2, int(cfg.get("claims_per_answer", 3)) + 2
    label_noise = float(cfg.get("label_noise", 0.05))
    inverted = set(cfg.get("inverted_generators", []))
    q_sd = float(cfg.get("question_effect_sd", 0.12))
    a_sd = float(cfg.get("answer_effect_sd", 0.25))
    sq_cfg = cfg.src_quality
    signals_cfg = cfg.signals
    inverted_agree = cfg.inverted_agree

    rows: list[dict] = []
    q_effect = rng.normal(0.0, q_sd, size=n_questions)

    for q in range(n_questions):
        question_id = f"syn_q{q:05d}"
        noun = _TOPIC_NOUNS[q % len(_TOPIC_NOUNS)]
        year = _YEARS[q % len(_YEARS)]
        unit = _UNITS[q % len(_UNITS)]
        context = _make_context(rng, noun, year, unit)

        for entry in roster:
            a_effect = rng.normal(0.0, a_sd)
            n_claims = int(rng.integers(claims_lo, claims_hi))
            src_mean = float(np.clip(
                entry.src_quality + rng.normal(0.0, float(sq_cfg.get("jitter_sd", 0.08))),
                float(sq_cfg.get("floor", 0.05)),
                float(sq_cfg.get("ceiling", 1.0)),
            ))

            for j in range(n_claims):
                claim_type = int(rng.integers(len(CLAIM_TYPE_NAMES)))
                type_name = CLAIM_TYPE_NAMES[claim_type]

                base = float(cfg.base_rate[type_name])
                p_hall = _sigmoid_scalar(np.log(base / (1 - base)) + q_effect[q] + a_effect)
                latent = bool(rng.random() < p_hall)

                emitted: dict[str, float] = {}
                for signal in SIGNALS:
                    if signal == "src_quality":
                        emitted[signal] = float(_emit(rng, src_mean))
                    elif signal == "agree" and entry.id in inverted:
                        mean = _lookup(inverted_agree, type_name, latent)
                        emitted[signal] = float(_emit(rng, mean))
                    else:
                        mean = _lookup(signals_cfg[signal], type_name, latent)
                        emitted[signal] = float(_emit(rng, mean))

                observed_label = latent ^ bool(rng.random() < label_noise)

                rows.append(
                    {
                        "question_id": question_id,
                        "claim_id": f"{question_id}_g{entry.id}_c{j}",
                        "claim_text": _claim_text(claim_type, rng, context, latent),
                        "benchmark": "synthetic",
                        "claim_type": claim_type,
                        "generator_id": entry.id,
                        "agree": emitted["agree"],
                        "contra": emitted["contra"],
                        "sem_dist": emitted["sem_dist"],
                        "support": emitted["support"],
                        "src_quality": emitted["src_quality"],
                        "conflict": emitted["conflict"],
                        "label": int(observed_label),
                        "context": context,
                        "source": entry.family,
                        "n_claims_in_answer": n_claims,
                    }
                )

    df = signal_frame(rows)
    extra = pd.DataFrame(rows)[["context", "source", "n_claims_in_answer"]]
    df = pd.concat([df, extra], axis=1)
    validate(df).raise_if_failed()
    return df


def save(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def build(path: str | Path, seed: int = 0, cfg: Config | None = None, **kwargs) -> Path:
    return save(generate(cfg, seed=seed, **kwargs), path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m rcgate.data.synthetic",
        description="Generate the synthetic planted-structure signal table.",
    )
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--questions", type=int, default=None)
    p.add_argument("--generators", type=int, default=None)
    p.add_argument("--planted", default=None, help="path to planted.yaml")
    p.add_argument("--out", default=str(TABLES_DIR / "synthetic.parquet"))
    args = p.parse_args(argv)

    df = generate(
        load_planted(args.planted),
        seed=args.seed,
        n_questions=args.questions,
        n_generators=args.generators,
    )
    out = save(df, args.out)
    rate = df["label"].mean()
    print(
        f"wrote {out} rows={len(df)} questions={df.question_id.nunique()} "
        f"generators={df.generator_id.nunique()} label_rate={rate:.3f}"
    )
    print(df.groupby("claim_type")["label"].mean().round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Cross-model signals: agreement, contradiction, semantic distance (milestone M5).

For each claim produced by one generator, the *other* generators are asked whether it
holds. Three signals, all in [0, 1]:

``agree``
    Fraction of other generators whose text entails the claim.
``contra``
    The single largest contradiction probability across the other generators. A max rather
    than a mean, because one generator flatly denying a claim is what a human reviewer
    cares about.
``sem_dist``
    ``1 - mean`` over the other generators of the cosine similarity between the claim and
    that generator's best-matching sentence.

A claim with no other generator to check against gets 0.5 / 0.5 / 1.0, i.e. "no
information", and the row is flagged via ``cross_n_others`` so the shortfall is visible in
the table rather than hidden in a number.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..claims.dealias import split_sentences
from ..data.schema import CROSS_SIGNALS
from .nli import Embedder, NliScorer

NEUTRAL_AGREE = 0.5
NEUTRAL_CONTRA = 0.5
NEUTRAL_SEM_DIST = 1.0


@dataclass
class CrossModelSignals:
    agree: float
    contra: float
    sem_dist: float
    n_others: int
    per_generator: list[dict] = field(default_factory=list)

    def as_row(self) -> dict[str, float]:
        return {
            "agree": float(np.clip(self.agree, 0.0, 1.0)),
            "contra": float(np.clip(self.contra, 0.0, 1.0)),
            "sem_dist": float(np.clip(self.sem_dist, 0.0, 1.0)),
            "cross_n_others": int(self.n_others),
        }


def _other_answer_texts(answers: dict[int, str], generator_id: int) -> list[str]:
    return [text for gid, text in answers.items() if gid != generator_id and text and text.strip()]


def score_claim(
    claim_text: str,
    answers: dict[int, str],
    generator_id: int,
    scorer: NliScorer,
    embedder: Embedder,
    premise_builder=None,
) -> CrossModelSignals:
    """Score one claim against every other generator's answer.

    ``premise_builder`` maps ``(other generator's text, claim)`` to the text used as the NLI
    premise (for example to keep only the top-k BM25 sentences, which both speeds up the
    check and stops a long answer from entailing a claim by accident). The default is the
    whole answer, split into sentences.
    """
    others = _other_answer_texts(answers, generator_id)
    if not others:
        return CrossModelSignals(NEUTRAL_AGREE, NEUTRAL_CONTRA, NEUTRAL_SEM_DIST, 0)

    entailments: list[float] = []
    contradictions: list[float] = []
    similarities: list[float] = []
    per_generator: list[dict] = []

    for gid, text in sorted(answers.items()):
        if gid == generator_id:
            continue
        premise = (
            premise_builder(text, claim_text)
            if premise_builder
            else " ".join(split_sentences(text))
        )
        if not premise.strip():
            continue
        result = scorer.score(premise, claim_text)
        entailments.append(result.entailment)
        contradictions.append(result.contradiction)
        similarities.append(embedder.best_sentence_similarity(claim_text, split_sentences(premise)))
        per_generator.append(
            {
                "generator_id": gid,
                "entailment": round(result.entailment, 4),
                "contradiction": round(result.contradiction, 4),
                "best_sentence_similarity": round(similarities[-1], 4),
            }
        )

    if not entailments:
        return CrossModelSignals(NEUTRAL_AGREE, NEUTRAL_CONTRA, NEUTRAL_SEM_DIST, 0)

    return CrossModelSignals(
        agree=float(np.mean(entailments)),
        contra=float(np.max(contradictions)),
        sem_dist=float(1.0 - np.mean(similarities)),
        n_others=len(entailments),
        per_generator=per_generator,
    )


def score_frame(
    df: pd.DataFrame,
    answers_by_question: dict[str, dict[int, str]],
    scorer: NliScorer,
    embedder: Embedder,
    premise_builder=None,
    question_column: str = "question_id",
    generator_column: str = "generator_id",
    claim_column: str = "claim_text",
) -> pd.DataFrame:
    """Fill the three cross-model signal columns for a frame of claims."""
    rows: list[dict] = []
    for _, row in df.iterrows():
        answers = answers_by_question.get(str(row[question_column]), {})
        signals = score_claim(
            str(row[claim_column]),
            answers,
            int(row[generator_column]),
            scorer,
            embedder,
            premise_builder=premise_builder,
        )
        out = signals.as_row()
        out["cross_per_generator"] = signals.per_generator
        rows.append(out)

    out_df = df.copy()
    out_df[CROSS_SIGNALS] = [[r["agree"], r["contra"], r["sem_dist"]] for r in rows]
    out_df["cross_n_others"] = [r["cross_n_others"] for r in rows]
    out_df["cross_per_generator"] = [r["cross_per_generator"] for r in rows]
    return out_df


def summarise(df: pd.DataFrame) -> dict:
    """Coverage and mean values, for the build log."""
    if "cross_n_others" not in df.columns:
        return {}
    others = df["cross_n_others"]
    return {
        "n_claims": int(len(df)),
        "n_without_any_other_generator": int((others == 0).sum()),
        "mean_others": round(float(others.mean()), 3),
        **{col: round(float(df[col].mean()), 4) for col in CROSS_SIGNALS},
        "out_of_range": int((df[list(CROSS_SIGNALS)] < 0).sum().sum()
                            + (df[list(CROSS_SIGNALS)] > 1).sum().sum()),
    }

"""Evidence signals: BM25 retrieval plus NLI support and conflict (milestone M5).

For benchmarks that ship a context (RAGTruth, DROP, FinanceBench) the context is the
evidence corpus and BM25 picks the passages worth an NLI check. For open QA
(TruthfulQA, HaluEval-QA) there is no context, so a single configured search source is
used instead; if none is configured the signals stay neutral rather than being invented.

``src_quality`` is a documented heuristic about *where the evidence came from*, never about
whether the claim is true:

======================  ======  =========================================
source                  score   reasoning
======================  ======  =========================================
benchmark context       0.90    shipped with the question, curated, in-domain
retrieved web (tier 1)  0.65    major reference domain
retrieved web (tier 2)  0.45    general web page, uncorroborated
no evidence at all       0.10    nothing to check against
======================  ======  =========================================

The tiers are configuration, not code, and the labels are recorded in the output so the
number can be audited. It carries no label information by design: giving it any would be
inventing precision the heuristic does not have (spec section 8, M5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

from ..claims.dealias import split_sentences
from ..data.schema import EVID_SIGNALS
from .nli import Embedder, NliScorer

NEUTRAL_SUPPORT = 0.5
NEUTRAL_CONFLICT = 0.0

#: Domain tiers for the optional web search source. Longer, better-maintained names first.
DEFAULT_DOMAIN_TIERS: list[tuple[str, float]] = [
    ("wikipedia.org", 0.70),
    ("britannica.com", 0.70),
    ("worldbank.org", 0.70),
    ("imf.org", 0.70),
    ("oecd.org", 0.70),
    ("sec.gov", 0.75),
    ("gov.uk", 0.70),
    ("europa.eu", 0.70),
    ("nature.com", 0.65),
    ("science.org", 0.65),
    ("reuters.com", 0.60),
    ("apnews.com", 0.60),
    ("statista.com", 0.50),
    ("medium.com", 0.30),
]

SOURCE_CONTEXT = "context"
SOURCE_WEB = "web"
SOURCE_NONE = "none"

SOURCE_SCORES = {
    SOURCE_CONTEXT: 0.90,
    SOURCE_WEB: 0.55,
    SOURCE_NONE: 0.10,
}


@dataclass
class EvidenceBundle:
    """The retrieved evidence for one claim, plus its provenance."""

    sentences: list[str]
    source: str
    domain: str | None = None
    src_quality: float = NEUTRAL_SUPPORT
    n_candidates: int = 0
    detail: dict = field(default_factory=dict)


def source_quality(source: str, domain: str | None = None,
                   tiers: list[tuple[str, float]] | None = None) -> float:
    """Tier-based quality for an evidence source. Depends on the source, never the claim."""
    if source == SOURCE_CONTEXT:
        return SOURCE_SCORES[SOURCE_CONTEXT]
    if source == SOURCE_WEB:
        for suffix, score in tiers or DEFAULT_DOMAIN_TIERS:
            if domain and domain.endswith(suffix):
                return score
        return SOURCE_SCORES[SOURCE_WEB]
    return SOURCE_SCORES[SOURCE_NONE]


def tokenise(text: str) -> list[str]:
    """Lowercase alphanumeric tokens. Shared by BM25 and anything else that needs a split."""
    import re

    return re.findall(r"[a-z0-9][a-z0-9'\-/\.]*", (text or "").lower())


class Bm25Index:
    """BM25 over the sentences of one context."""

    def __init__(self, sentences: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.sentences = [s for s in sentences if s and s.strip()]
        self.tokenised = [tokenise(s) for s in self.sentences]
        self.bm25 = None
        if any(self.tokenised):
            self.bm25 = BM25Okapi(self.tokenised, k1=k1, b=b)

    def top(self, query: str, k: int = 3) -> list[tuple[int, float]]:
        if self.bm25 is None:
            return []
        scores = self.bm25.get_scores(tokenise(query))
        order = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0.0]


def gather_evidence(
    claim_text: str,
    context: str | None,
    top_k: int = 3,
    tiers: list[tuple[str, float]] | None = None,
) -> EvidenceBundle:
    """Retrieve the evidence sentences for one claim.

    With a context, this is BM25 over the context sentences. Without one, there is no
    evidence and the bundle says so honestly instead of returning an empty-but-confident
    score.
    """
    if context and context.strip():
        index = Bm25Index(split_sentences(context))
        hits = index.top(claim_text, k=top_k)
        if not hits:
            # No lexical overlap: fall back to the leading sentences of the context, which
            # is where a passage normally states its own conclusion.
            fallback = index.sentences[:top_k]
            return EvidenceBundle(
                sentences=fallback,
                source=SOURCE_CONTEXT,
                src_quality=source_quality(SOURCE_CONTEXT, tiers=tiers),
                n_candidates=len(index.sentences),
                detail={"retrieval": "fallback_lead", "bm25_hits": 0},
            )
        return EvidenceBundle(
            sentences=[index.sentences[i] for i, _ in hits],
            source=SOURCE_CONTEXT,
            src_quality=source_quality(SOURCE_CONTEXT, tiers=tiers),
            n_candidates=len(index.sentences),
            detail={"retrieval": "bm25", "bm25_hits": len(hits),
                    "top_score": round(hits[0][1], 3)},
        )

    return EvidenceBundle(
        sentences=[],
        source=SOURCE_NONE,
        src_quality=source_quality(SOURCE_NONE, tiers=tiers),
        n_candidates=0,
        detail={"retrieval": "none", "note": "no context supplied; signals left neutral"},
    )


@dataclass
class EvidenceSignals:
    support: float
    src_quality: float
    conflict: float
    source: str
    n_passages: int
    detail: dict = field(default_factory=dict)

    def as_row(self) -> dict:
        return {
            "support": float(np.clip(self.support, 0.0, 1.0)),
            "src_quality": float(np.clip(self.src_quality, 0.0, 1.0)),
            "conflict": float(np.clip(self.conflict, 0.0, 1.0)),
            "evidence_source": self.source,
            "evidence_n_passages": int(self.n_passages),
        }


def score_claim(
    claim_text: str,
    context: str | None,
    scorer: NliScorer,
    embedder: Embedder,
    top_k: int = 3,
    aggregate: str = "max",
    tiers: list[tuple[str, float]] | None = None,
) -> EvidenceSignals:
    """NLI-check the claim against its retrieved evidence.

    ``aggregate="max"`` takes the single most supportive passage, which is what a human
    checker does: one passage that states the claim settles it. ``"mean"`` is available for
    the ablation that asks whether diluting across passages helps.
    """
    bundle = gather_evidence(claim_text, context, top_k=top_k, tiers=tiers)

    if not bundle.sentences:
        return EvidenceSignals(
            support=NEUTRAL_SUPPORT,
            src_quality=bundle.src_quality,
            conflict=NEUTRAL_CONFLICT,
            source=bundle.source,
            n_passages=0,
            detail=bundle.detail,
        )

    entailments, contradictions = [], []
    for sentence in bundle.sentences:
        result = scorer.score(sentence, claim_text)
        entailments.append(result.entailment)
        contradictions.append(result.contradiction)

    support = float(max(entailments) if aggregate == "max" else np.mean(entailments))
    conflict = float(max(contradictions))
    return EvidenceSignals(
        support=support,
        src_quality=bundle.src_quality,
        conflict=conflict,
        source=bundle.source,
        n_passages=len(bundle.sentences),
        detail={**bundle.detail, "n_nli_calls": len(bundle.sentences)},
    )


def score_frame(
    df: pd.DataFrame,
    scorer: NliScorer,
    embedder: Embedder,
    top_k: int = 3,
    aggregate: str = "max",
    context_column: str = "context",
    claim_column: str = "claim_text",
    tiers: list[tuple[str, float]] | None = None,
) -> pd.DataFrame:
    """Fill the three evidence signal columns for a frame of claims."""
    rows = []
    for _, row in df.iterrows():
        context = row.get(context_column) if context_column in df.columns else None
        if not isinstance(context, str) or not context.strip():
            context = None
        signals = score_claim(
            str(row[claim_column]), context, scorer, embedder, top_k=top_k,
            aggregate=aggregate, tiers=tiers,
        )
        r = signals.as_row()
        r["evidence_detail"] = signals.detail
        rows.append(r)

    out = df.copy()
    out[EVID_SIGNALS] = [[r["support"], r["src_quality"], r["conflict"]] for r in rows]
    out["evidence_source"] = [r["evidence_source"] for r in rows]
    out["evidence_n_passages"] = [r["evidence_n_passages"] for r in rows]
    out["evidence_detail"] = [r["evidence_detail"] for r in rows]
    return out


def summarise(df: pd.DataFrame) -> dict:
    if "evidence_source" not in df.columns:
        return {}
    counts = df["evidence_source"].value_counts().to_dict()
    return {
        "n_claims": int(len(df)),
        "sources": {str(k): int(v) for k, v in counts.items()},
        "mean_passages": round(float(df["evidence_n_passages"].mean()), 3),
        **{col: round(float(df[col].mean()), 4) for col in EVID_SIGNALS},
        "out_of_range": int((df[list(EVID_SIGNALS)] < 0).sum().sum()
                            + (df[list(EVID_SIGNALS)] > 1).sum().sum()),
    }

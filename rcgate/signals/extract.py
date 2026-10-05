"""Turn a benchmark's claims into the six signals (milestone M5).

This is the only module that writes signal columns. It orchestrates the three extractors --
cross-model, evidence, arithmetic -- over whatever frame a loader produced, using cached
scorers so a rerun costs nothing, and returns a frame that satisfies the data contract.

Order matters and is deliberate:

1. **cross-model** first, because the premise for each NLI call is built from the *other*
   generators' answers, which the claim frame does not carry.
2. **evidence** second, over the row's own context.
3. **arithmetic** last, because it folds a verdict into ``support``/``conflict``, which
   evidence has just written.
4. Contract coercion last of all, so the emitted columns are exactly ``SIGNAL_COLUMNS``
   plus a small, documented set of provenance columns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd

from ..data.schema import SIGNAL_COLUMNS, validate

#: Columns kept in the saved table. ``context`` and the verbose per-generator dumps are
#: dropped: they are large, and nothing downstream of the table reads them, but the raw
#: files they came from stay in ``data/raw`` so the build is re-derivable.
KEPT_EXTRA_COLUMNS = [
    "source",
    "task_type",
    "source_model",
    "label_types",
    "response_quality",
    "n_claims_in_answer",
    "claim_type_rule",
    "claim_type_confidence",
    "cross_n_others",
    "evidence_source",
    "evidence_n_passages",
    "arithmetic_verdict",
    "arithmetic_verified",
]


def premise_builder(top_k: int = 3):
    """Build an NLI premise from another generator's answer.

    A full RAGTruth answer is often 200+ tokens, and the cross-encoder truncates at 256, so
    feeding the whole answer lets the model see a claim's evidence and miss its
    contradiction. BM25 top-k keeps the sentences that actually discuss the claim.
    """

    from ..claims.dealias import split_sentences
    from .evidence import Bm25Index

    def build(text: str, claim: str) -> str:
        sentences = split_sentences(text)
        index = Bm25Index(sentences)
        hits = index.top(claim, k=top_k)
        chosen = [index.sentences[i] for i, _ in hits] or sentences[:top_k]
        return " ".join(chosen)

    return build


@dataclass
class ExtractionReport:
    """What the extraction cost and produced, written to the build log.

    The cache counters are *deltas over this call*, not the cache's lifetime totals: a
    rerun that recomputes nothing must be able to show that in its own log rather than
    replaying the numbers from whichever run happened to populate the cache first.
    """

    n_claims: int = 0
    seconds: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    compute_seconds: float = 0.0
    backend: str = ""
    sections: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "n_claims": self.n_claims,
            "seconds": round(self.seconds, 2),
            "backend": self.backend,
            "nli_cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "compute_seconds": round(self.compute_seconds, 2),
            },
            **self.sections,
        }


def extract_signals(
    frame: pd.DataFrame,
    cfg=None,
    answers_by_question: dict[str, dict[int, str]] | None = None,
    scorer=None,
    embedder=None,
    cache=None,
    report: ExtractionReport | None = None,
) -> tuple[pd.DataFrame, ExtractionReport]:
    """Fill the six signals and the provenance columns. Returns ``(frame, report)``.

    ``scorer``/``embedder`` are injected by the tests, which pass the lexical scorer so no
    model download and no network is involved.
    """
    from . import cross_model, evidence
    from .arithmetic_check import summarise as arithmetic_summary
    from .arithmetic_check import verify_frame
    from .nli import build_cached

    if scorer is None or embedder is None:
        scorer, embedder, cache = build_cached(cfg)

    before = dict(cache.report()) if cache is not None else {}
    evidence_top_k = int(cfg.get("signals.evidence_top_k", 3)) if cfg else 3
    premise_top_k = int(cfg.get("signals.premise_top_k", 3)) if cfg else 3
    aggregate = str(cfg.get("signals.evidence_aggregate", "max")) if cfg else "max"
    use_arithmetic = bool(cfg.get("signals.arithmetic", True)) if cfg else True

    started = time.perf_counter()
    out = frame.copy()

    out = cross_model.score_frame(
        out, answers_by_question or {}, scorer, embedder,
        premise_builder=premise_builder(premise_top_k),
    )
    out = evidence.score_frame(
        out, scorer, embedder, top_k=evidence_top_k, aggregate=aggregate,
        context_column="context",
    )
    if use_arithmetic:
        out = verify_frame(out)

    report = report or ExtractionReport()
    report.n_claims = len(out)
    report.backend = getattr(scorer, "name", "unknown")
    report.sections = {
        "cross_model": cross_model.summarise(out),
        "evidence": evidence.summarise(out),
        "arithmetic": arithmetic_summary(out) if use_arithmetic else {},
    }
    if cache is not None:
        after = dict(cache.report())
        report.cache_hits = int(after["hits"]) - int(before.get("hits", 0))
        report.cache_misses = int(after["misses"]) - int(before.get("misses", 0))
        report.compute_seconds = float(after["api_seconds"]) - float(
            before.get("api_seconds", 0.0)
        )
    report.seconds = time.perf_counter() - started
    return contract(out), report


def contract(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the canonical column set and validate."""
    extras = [c for c in KEPT_EXTRA_COLUMNS if c in df.columns]
    ordered = SIGNAL_COLUMNS + extras
    validate(df).raise_if_failed()
    return df[ordered].copy()

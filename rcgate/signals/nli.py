"""Black-box scorers: NLI entailment/contradiction and sentence embeddings.

Constraint C1 (black-box only) means these operate on *text*. No generator's hidden states,
logits or activations are ever read; the NLI cross-encoder is a separate public classifier
applied to two text strings.

Two backends, selected by ``signals.backend`` in the config:

``cross_encoder``
    A small DeBERTa MNLI cross-encoder plus a MiniLM sentence encoder. This is the backend
    the real experiments use. Models are downloaded once into ``.cache/models`` and cost
    nothing per call on CPU.

``lexical``
    A deterministic, dependency-free fallback using token overlap and a small negation /
    antonym cue list. It exists so the pipeline, the tests and the CI box can run with no
    model download and no network. **It is not NLI** and its scores are much weaker; results
    produced with it must be labelled ``backend=lexical`` in any table.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Protocol

from ..paths import MODEL_DIR
from .cache import Budget, DiskCache, make_key

# -- default models (small, CPU-friendly, per constraint C2) ----------------
DEFAULT_NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

os.environ.setdefault("HF_HOME", str(MODEL_DIR))
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

_NEGATION_CUES = {
    "not", "no", "never", "none", "cannot", "cant", "didnt", "doesnt", "isnt", "arent",
    "wasnt", "werent", "wont", "without", "neither", "nor", "failed", "unable", "false",
}

#: Word pairs that contradict each other in the financial/news domain this project uses.
_ANTONYM_CUES = {
    ("increase", "decrease"), ("rose", "fell"), ("rise", "fall"), ("grew", "shrank"),
    ("gain", "loss"), ("profit", "loss"), ("higher", "lower"), ("more", "less"),
    ("before", "after"), ("opened", "closed"), ("approved", "rejected"),
    ("acquired", "divested"), ("rose", "declined"), ("up", "down"),
    ("success", "failure"), ("above", "below"), ("peak", "trough"),
}

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-/]*(?:\.[0-9]+)?%?", re.IGNORECASE)


@dataclass
class NLIResult:
    """Probabilities over ``entailment``, ``contradiction`` and ``neutral``."""

    entailment: float
    contradiction: float
    neutral: float

    @property
    def entail(self) -> bool:
        return self.entailment >= self.contradiction

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.entailment, self.contradiction, self.neutral)


@dataclass
class NliScorer(Protocol):
    name: str

    def score(self, premise: str, hypothesis: str) -> NLIResult: ...


class LexicalScorer:
    """Deterministic offline fallback. Deterministic, explainable, and weak.

    Documented limitations, so nobody mistakes this for a trained classifier:

    * entailment is word-overlap between premise and hypothesis, so it rewards restatement
      and cannot tell paraphrase from topical similarity;
    * contradiction needs an explicit negation or antonym cue, so it misses contradictions
      expressed any other way;
    * numbers are compared as strings, so ``847`` and ``847.0`` do not match.
    """

    name = "lexical"

    def __init__(self, entail_threshold: float = 0.55) -> None:
        self.entail_threshold = entail_threshold

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [t.lower() for t in _WORD_RE.findall(text or "")]

    def score(self, premise: str, hypothesis: str) -> NLIResult:
        p_tokens, h_tokens = self._tokens(premise), self._tokens(hypothesis)
        if not p_tokens or not h_tokens:
            return NLIResult(0.0, 0.0, 1.0)

        p_set, h_set = set(p_tokens), set(h_tokens)
        overlap = len(p_set & h_set) / len(h_set or {1})
        entailment = float(min(1.0, overlap))

        p_antonyms = {a for a, b in _ANTONYM_CUES if b in p_set}
        p_antonyms |= {b for a, b in _ANTONYM_CUES if a in p_set}
        antonym_hits = len(p_antonyms & h_set)

        p_neg = len(set(p_tokens) & _NEGATION_CUES)
        h_neg = len(set(h_tokens) & _NEGATION_CUES)
        negation_mismatch = 1 if p_neg != h_neg else 0
        contradiction = min(
            1.0, 0.6 * antonym_hits + 0.3 * negation_mismatch + 0.35 * (1.0 - overlap)
        )

        entailment = max(0.0, entailment - 0.5 * contradiction)
        neutral = max(0.0, 1.0 - entailment - contradiction)
        total = entailment + contradiction + neutral
        return NLIResult(entailment / total, contradiction / total, neutral / total)


class CrossEncoderScorer:
    """A small MNLI cross-encoder plus a MiniLM sentence encoder, on CPU.

    Labels differ between checkpoints, so the index mapping is resolved once from the
    model's ``id2label`` rather than assumed.
    """

    name = "cross_encoder"

    def __init__(
        self,
        nli_model: str = DEFAULT_NLI_MODEL,
        embed_model: str = DEFAULT_EMBED_MODEL,
        device: str = "cpu",
        max_length: int = 256,
    ) -> None:
        import torch
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(nli_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(nli_model)
        self.model.eval()
        self.model.to(device)
        self.embedder = SentenceTransformer(embed_model, device=device)
        self.max_length = max_length
        self.label_index = self._resolve_labels(self.model.config.id2label)

    @staticmethod
    def _resolve_labels(id2label: dict[int, str]) -> dict[str, int]:
        wanted = {"entailment": 0, "contradiction": 0, "neutral": 0}
        for index, label in id2label.items():
            lowered = str(label).lower()
            for key in wanted:
                if lowered.startswith(key[:5]) or lowered == key:
                    wanted[key] = index
        if len(set(wanted.values())) != 3:
            raise RuntimeError(f"cannot map MNLI labels from {id2label}")
        return wanted

    def score(self, premise: str, hypothesis: str) -> NLIResult:
        torch = self._torch
        encoded = self.tokenizer(
            premise or "",
            hypothesis or "",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self.model(**encoded).logits[0]
        probs = torch.softmax(logits, dim=-1).tolist()
        result = NLIResult(
            entailment=probs[self.label_index["entailment"]],
            contradiction=probs[self.label_index["contradiction"]],
            neutral=probs[self.label_index["neutral"]],
        )
        total = result.entailment + result.contradiction + result.neutral
        return NLIResult(result.entailment / total, result.contradiction / total, result.neutral / total)

    def embed(self, texts: list[str]):
        return self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def similarity(self, a: str, b: str) -> float:
        vectors = self.embed([a, b])
        return _cosine(vectors[0], vectors[1])


class Embedder:
    """Sentence-embedding interface with a deterministic hashing fallback."""

    name = "hashing"

    def __init__(self, scorer, dim: int = 384) -> None:
        self._scorer = scorer
        self.dim = dim

    def embed(self, texts: list[str]):
        if hasattr(self._scorer, "embed"):
            return self._scorer.embed(texts)
        return _hashing_embed(texts, self.dim)

    def best_sentence_similarity(self, claim: str, sentences: list[str]) -> float:
        """Cosine similarity of the claim to its best-matching sentence.

        Returns 0.0 for an empty sentence list so ``sem_dist`` degrades to 1.0, i.e. "no
        evidence of similarity", rather than silently scoring perfect similarity.
        """
        sentences = [s for s in sentences if s and s.strip()]
        if not sentences:
            return 0.0
        vectors = self.embed([claim, *sentences])
        claim_vec = vectors[0]
        sims = [_cosine(claim_vec, v) for v in vectors[1:]]
        return float(max(0.0, min(1.0, max(sims))))


def _cosine(a, b) -> float:
    import numpy as np

    a = np.asarray(a, dtype="float64").ravel()
    b = np.asarray(b, dtype="float64").ravel()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


def _hashing_embed(texts: list[str], dim: int = 384):
    """Deterministic bag-of-trigrams hashing. No download, no randomness."""
    import numpy as np

    out = np.zeros((len(texts), dim), dtype="float64")
    for row, text in enumerate(texts):
        tokens = _WORD_RE.findall((text or "").lower())
        grams = list(zip(tokens, tokens[1:], tokens[2:], strict=False))
        grams += [(t,) for t in tokens]
        for gram in grams:
            key = " ".join(gram)
            index = int(hashlib_sha(key) % dim)
            out[row, index] += 1.0
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1.0
    return out / norms


def hashlib_sha(text: str) -> int:
    """Stable across processes, unlike ``hash()``."""
    import hashlib

    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def build_scorer(cfg=None) -> tuple:
    """Instantiate ``(scorer, embedder)`` from config, falling back on any load failure.

    A missing model download must not silently produce numbers that look like NLI scores,
    so a failure is logged loudly and the backend name is reported alongside the results.
    """
    backend = "cross_encoder"
    nli_model, embed_model = DEFAULT_NLI_MODEL, DEFAULT_EMBED_MODEL
    if cfg is not None:
        backend = str(cfg.get("signals.backend", backend))
        nli_model = str(cfg.get("signals.nli_model", nli_model))
        embed_model = str(cfg.get("signals.embed_model", embed_model))

    if backend == "lexical":
        scorer = LexicalScorer()
        return scorer, Embedder(scorer)

    try:
        scorer = CrossEncoderScorer(nli_model=nli_model, embed_model=embed_model)
        return scorer, Embedder(scorer)
    except Exception as exc:  # pragma: no cover - depends on model availability
        import warnings

        warnings.warn(
            f"could not load {nli_model} / {embed_model} ({type(exc).__name__}: {exc}); "
            "falling back to the lexical scorer. Results are NOT NLI-derived.",
            RuntimeWarning,
            stacklevel=2,
        )
        scorer = LexicalScorer()
        return scorer, Embedder(scorer)


def scorer_report(scorer) -> dict:
    """Backend provenance, recorded next to every results table."""
    return {"backend": getattr(scorer, "name", "unknown")}


# -- disk-cached wrappers ------------------------------------------------------
#
# NLI and embedding calls are pure functions of their two (or one) strings, so they are
# cached by content hash exactly like a paid API call would be. They live in their own
# cache root, separate from ``.cache/llm``: constraint C3 caps *spend*, and local CPU
# compute spends nothing, so it must not be charged against the API budget or blocked by
# ``budget.dry_run``. What it does get is a count and a duration, which the build log
# reports so the cost of a real run is still visible.


@dataclass
class CachedScorer:
    """An NLI scorer that computes each ``(premise, hypothesis)`` pair exactly once."""

    inner: NliScorer
    cache: DiskCache

    @property
    def name(self) -> str:
        return f"{getattr(self.inner, 'name', 'unknown')}+disk"

    def score(self, premise: str, hypothesis: str) -> NLIResult:
        def _compute(_prompt: str) -> list[float]:
            return [float(x) for x in self.inner.score(premise, hypothesis).as_tuple()]

        value = self.cache.call(
            "local-nli",
            getattr(self.inner, "name", "unknown"),
            f"{premise}\n\t{hypothesis}",
            _compute,
            params={"kind": "nli"},
        )
        return NLIResult(*(float(x) for x in value))


@dataclass
class CachedEmbedder:
    """An embedder that stores one vector per text under its own content hash."""

    inner: Embedder
    cache: DiskCache

    @property
    def name(self) -> str:
        return f"{getattr(self.inner, 'name', 'unknown')}+disk"

    @property
    def dim(self) -> int:
        return getattr(self.inner, "dim", 384)

    def _key(self, text: str) -> str:
        return make_key("local-embed", getattr(self.inner, "name", "unknown"), text,
                        {"kind": "embedding"})

    def embed(self, texts: list[str]):
        import numpy as np

        vectors: list[list[float] | None] = [None] * len(texts)
        pending: list[tuple[int, str]] = []
        for index, text in enumerate(texts):
            record = self.cache.get(self._key(text))
            if record is None:
                pending.append((index, text))
            else:
                vectors[index] = record["value"]
                self.cache.stats.hits += 1

        if pending:
            fresh = self.inner.embed([text for _, text in pending])
            for (index, text), vector in zip(pending, fresh, strict=True):
                row = [round(float(x), 6) for x in vector]
                self.cache.put(self._key(text), row, meta={"kind": "embedding"})
                self.cache.stats.misses += 1
                vectors[index] = row
        return np.asarray([v for v in vectors if v is not None], dtype="float64")

    def best_sentence_similarity(self, claim: str, sentences: list[str]) -> float:
        sentences = [s for s in sentences if s and s.strip()]
        if not sentences:
            return 0.0
        vectors = self.embed([claim, *sentences])
        claim_vec = vectors[0]
        return float(max(0.0, min(1.0, max(_cosine(claim_vec, v) for v in vectors[1:]))))


def build_cached(cfg=None, root=None) -> tuple[CachedScorer, CachedEmbedder, DiskCache]:
    """Build the real scorer, wrap both in disk caches, and hand back the cache object.

    The caller keeps the cache so the run can report hits, misses and CPU seconds.
    """
    scorer, embedder = build_scorer(cfg)
    cache = compute_cache(cfg, root=root)
    return CachedScorer(scorer, cache), CachedEmbedder(embedder, cache), cache


def compute_cache(cfg=None, root=None) -> DiskCache:
    """A cache for local CPU scorers. Uncapped and never dry-run: it spends nothing."""
    from ..paths import COMPUTE_CACHE_DIR

    if root is None and cfg is not None:
        configured = cfg.get("signals.compute_cache", None)
        if configured:
            from ..paths import PROJECT_ROOT

            root = PROJECT_ROOT / str(configured)
    return DiskCache(root=root or COMPUTE_CACHE_DIR, budget=Budget())

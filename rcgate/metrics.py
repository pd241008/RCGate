"""Metrics, threshold tuning, calibration error and bootstrap intervals.

Every number in a results table comes from here, so the definitions cannot drift between
variants. Constraint C6 is respected by construction: ``tune_threshold`` only ever sees
validation rows, and the test set is scored with the threshold returned from there.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import roc_auc_score

EPS = 1e-12


def auroc(y_true, y_score) -> float:
    """AUROC, or ``nan`` when the slice is single-class (an honest blank, not a 0.5)."""
    y_true = np.asarray(y_true)
    if np.unique(y_true).size < 2:
        return float("nan")
    return float(roc_auc_score(y_true, np.asarray(y_score, dtype="float64")))


def f1_at_threshold(y_true, y_score, threshold: float) -> float:
    y_pred = (np.asarray(y_score, dtype="float64") >= threshold).astype(int)
    return float(_prf(y_true, y_pred)["f1"])


def _prf(y_true, y_pred) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": (tp + tn) / max(len(y_true), 1),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def tune_threshold(y_val, p_val, quantile: float = 0.5, grid: int = 199) -> float:
    """Pick the F1-maximising threshold on validation data.

    The search runs over quantiles of the validation scores rather than over raw values so
    it behaves the same whether scores are logits, probabilities or badly scaled.
    """
    p_val = np.asarray(p_val, dtype="float64")
    if p_val.size == 0 or np.unique(p_val).size < 2:
        return 0.5
    lo, hi = float(p_val.min()), float(p_val.max())
    if hi - lo < EPS:
        return float(lo)
    lo_q, hi_q = np.quantile(p_val, [max(0.0, quantile - 0.4), min(1.0, quantile + 0.4)])
    candidates = np.unique(np.concatenate([np.linspace(lo_q, hi_q, grid), [0.5]]))
    best_f1, best_t = -1.0, 0.5
    for t in candidates:
        f1 = f1_at_threshold(y_val, p_val, float(t))
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)
    return best_t


def expected_calibration_error(y_true, y_score, n_bins: int = 15) -> float:
    """Equal-width-bin ECE. Bins are ``[0, 1/n], ..., 1`` on the probability scale."""
    y_true = np.asarray(y_true, dtype="float64")
    p = np.asarray(y_score, dtype="float64")
    if p.size == 0:
        return float("nan")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        total += (mask.sum() / p.size) * abs(p[mask].mean() - y_true[mask].mean())
    return float(total)


@dataclass
class BootstrapCI:
    point: float
    lo: float
    hi: float
    n_resamples: int
    n_valid: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "point": round(self.point, 4),
            "ci_lo": round(self.lo, 4),
            "ci_hi": round(self.hi, 4),
            "n_bootstrap": self.n_resamples,
            "n": self.n_valid,
        }

    def __str__(self) -> str:
        return f"{self.point:.3f} [{self.lo:.3f}, {self.hi:.3f}]"


def bootstrap_auroc_ci(
    y_true,
    y_score,
    n_resamples: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> BootstrapCI:
    """Percentile bootstrap CI for AUROC, resampling *claims* with replacement.

    Resampling claims rather than questions is the conservative choice here: it ignores
    within-question clustering, so the interval is if anything too narrow. A cluster
    bootstrap over ``question_id`` is available as ``bootstrap_auroc_ci_grouped``.
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype="float64")
    point = auroc(y_true, y_score)
    if np.isnan(point) or y_true.size < 2:
        return BootstrapCI(point, float("nan"), float("nan"), 0, int(y_true.size))

    rng = np.random.default_rng(seed)
    stats = np.empty(n_resamples)
    n = y_true.size
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        stats[i] = auroc(y_true[idx], y_score[idx])
    stats = stats[~np.isnan(stats)]
    if stats.size == 0:
        return BootstrapCI(point, float("nan"), float("nan"), 0, int(n))
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(point, float(lo), float(hi), int(stats.size), int(n))


def bootstrap_auroc_ci_grouped(
    y_true,
    y_score,
    groups,
    n_resamples: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> BootstrapCI:
    """Cluster bootstrap that resamples whole questions, matching how the split was made."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype="float64")
    groups = np.asarray(groups).astype(str)
    point = auroc(y_true, y_score)
    unique = np.unique(groups)
    if np.isnan(point) or unique.size < 2:
        return BootstrapCI(point, float("nan"), float("nan"), 0, int(y_true.size))

    index_by_group = {g: np.flatnonzero(groups == g) for g in unique}
    rng = np.random.default_rng(seed)
    stats = np.empty(n_resamples)
    for i in range(n_resamples):
        picks = rng.integers(0, unique.size, unique.size)
        idx = np.concatenate([index_by_group[unique[p]] for p in picks])
        stats[i] = auroc(y_true[idx], y_score[idx])
    stats = stats[~np.isnan(stats)]
    if stats.size == 0:
        return BootstrapCI(point, float("nan"), float("nan"), 0, int(y_true.size))
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(point, float(lo), float(hi), int(stats.size), int(y_true.size))


@dataclass
class SliceMetrics:
    name: str
    n: int
    positive_rate: float
    auroc: float
    ci_lo: float = float("nan")
    ci_hi: float = float("nan")
    f1: float = float("nan")
    precision: float = float("nan")
    recall: float = float("nan")
    ece: float = float("nan")
    mean_prob: float = float("nan")
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        out = {
            "slice": self.name,
            "n": self.n,
            "positive_rate": round(self.positive_rate, 4),
            "auroc": None if np.isnan(self.auroc) else round(self.auroc, 4),
            "auroc_ci_lo": None if np.isnan(self.ci_lo) else round(self.ci_lo, 4),
            "auroc_ci_hi": None if np.isnan(self.ci_hi) else round(self.ci_hi, 4),
            "f1": None if np.isnan(self.f1) else round(self.f1, 4),
            "precision": None if np.isnan(self.precision) else round(self.precision, 4),
            "recall": None if np.isnan(self.recall) else round(self.recall, 4),
            "ece": None if np.isnan(self.ece) else round(self.ece, 4),
            "mean_prob": None if np.isnan(self.mean_prob) else round(self.mean_prob, 4),
        }
        out.update(self.extra)
        return out


def slice_metrics(
    y_true,
    y_score,
    name: str,
    threshold: float,
    n_bins: int = 15,
    ci: BootstrapCI | None = None,
    extra: dict | None = None,
) -> SliceMetrics:
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype="float64")
    prf = _prf(y_true, (y_score >= threshold).astype(int))
    return SliceMetrics(
        name=name,
        n=int(y_true.size),
        positive_rate=float(y_true.mean()) if y_true.size else float("nan"),
        auroc=auroc(y_true, y_score),
        ci_lo=ci.lo if ci else float("nan"),
        ci_hi=ci.hi if ci else float("nan"),
        f1=prf["f1"],
        precision=prf["precision"],
        recall=prf["recall"],
        ece=expected_calibration_error(y_true, y_score, n_bins),
        mean_prob=float(y_score.mean()) if y_score.size else float("nan"),
        extra=dict(extra or {}),
    )


def paired_bootstrap_delta(
    y_true,
    score_a,
    score_b,
    n_resamples: int = 1000,
    seed: int = 0,
) -> dict[str, float]:
    """CI on ``AUROC(a) - AUROC(b)`` resampled once per row.

    This is the test that matters for H2: two models scored on the same claims, one
    shared resample, so the difference is paired and much tighter than two separate CIs.
    """
    y_true = np.asarray(y_true)
    a = np.asarray(score_a, dtype="float64")
    b = np.asarray(score_b, dtype="float64")
    point = auroc(y_true, a) - auroc(y_true, b)
    rng = np.random.default_rng(seed)
    stats = np.empty(n_resamples)
    n = y_true.size
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        stats[i] = auroc(y_true[idx], a[idx]) - auroc(y_true[idx], b[idx])
    stats = stats[~np.isnan(stats)]
    if stats.size == 0:
        return {"delta": round(point, 4), "lo": None, "hi": None, "p_gt_0": None}
    lo, hi = np.quantile(stats, [0.025, 0.975])
    return {
        "delta": round(point, 4),
        "lo": round(float(lo), 4),
        "hi": round(float(hi), 4),
        "p_gt_0": round(float((stats > 0).mean()), 4),
    }

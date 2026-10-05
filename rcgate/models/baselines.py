"""Baselines A0-A4 and A8 (spec section 7).

All of them read the same signal table and the same grouped splits as RC-Gate, so every
comparison in the results is apples to apples. Scalers are fit on train rows only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from ..data.schema import CROSS_SIGNALS, EVID_SIGNALS, SIGNALS, onehot_meta
from ..metrics import auroc, tune_threshold

MAX_ITER = 2000


class SignalModel:
    """Interface every variant implements. ``fit`` returns an info dict for the log."""

    name: str = "base"
    needs_threshold: bool = True

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg) -> dict:  # pragma: no cover
        raise NotImplementedError

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def info(self) -> dict:
        return {}


def _lr(class_weight, C: float = 1.0, seed: int = 0) -> LogisticRegression:
    return LogisticRegression(
        C=C,
        max_iter=MAX_ITER,
        class_weight=class_weight,
        random_state=seed,
        solver="lbfgs",
    )


# ---------------------------------------------------------------------------
# A0 / A1 / A2: flat logistic regression on one or both signal families
# ---------------------------------------------------------------------------


@dataclass
class LogisticSignalModel(SignalModel):
    """A0 (all six signals), A1 (cross only), A2 (evidence only)."""

    columns: list[str]
    name: str = "A0"
    class_weight: object = None
    seed: int = 0
    _clf: LogisticRegression | None = field(default=None, repr=False)
    _means: np.ndarray | None = field(default=None, repr=False)
    _stds: np.ndarray | None = field(default=None, repr=False)

    def _x(self, df: pd.DataFrame) -> np.ndarray:
        return df[self.columns].to_numpy(dtype="float64")

    def _scale(self, x: np.ndarray, fit: bool) -> np.ndarray:
        if fit:
            self._means = x.mean(axis=0)
            self._stds = x.std(axis=0)
            self._stds[self._stds < 1e-8] = 1.0
        return (x - self._means) / self._stds

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg) -> dict:
        x_train = self._scale(self._x(train), fit=True)
        self._clf = _lr(self.class_weight, seed=self.seed).fit(x_train, train["label"].to_numpy())
        p_val = self.predict_proba(val)
        return {
            "val_auroc": auroc(val["label"].to_numpy(), p_val),
            "columns": list(self.columns),
            "coef": self._clf.coef_.round(3).tolist(),
        }

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        x = self._scale(self._x(df), fit=False)
        return self._clf.predict_proba(x)[:, 1]

    def predict_logits(self, df: pd.DataFrame) -> np.ndarray:
        x = self._scale(self._x(df), fit=False)
        return self._clf.decision_function(x)


# ---------------------------------------------------------------------------
# A3: static learned scalar alpha blending two frozen experts (Rowen-style)
# ---------------------------------------------------------------------------


@dataclass
class StaticAlphaBlend(SignalModel):
    """One scalar alpha for the whole dataset.

    ``logit = b + scale * (alpha * z_cross + (1 - alpha) * z_evid)``

    alpha is picked by grid search on validation AUROC. This is the control that separates
    *learning* a blend from *conditioning* the blend on metadata: A3 learns, A7 conditions.
    """

    name: str = "A3"
    seed: int = 0
    n_grid: int = 101
    _z_cross: LogisticSignalModel | None = field(default=None, repr=False)
    _z_evid: LogisticSignalModel | None = field(default=None, repr=False)
    _alpha: float = field(default=0.5, repr=False)
    _clf: LogisticRegression | None = field(default=None, repr=False)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg) -> dict:
        self._z_cross = LogisticSignalModel(list(CROSS_SIGNALS), name="expert_cross", seed=self.seed)
        self._z_evid = LogisticSignalModel(list(EVID_SIGNALS), name="expert_evid", seed=self.seed)
        self._z_cross.fit(train, val, cfg)
        self._z_evid.fit(train, val, cfg)

        zc_tr = self._z_cross.predict_logits(train)
        ze_tr = self._z_evid.predict_logits(train)
        zc_va = self._z_cross.predict_logits(val)
        ze_va = self._z_evid.predict_logits(val)
        y_va = val["label"].to_numpy()

        best = (-np.inf, 0.5, None)
        for alpha in np.linspace(0.0, 1.0, self.n_grid):
            clf = _lr(None, seed=self.seed).fit(self._blend(alpha, zc_tr, ze_tr), train["label"].to_numpy())
            score = auroc(y_va, self._blend(alpha, zc_va, ze_va))
            # ties break toward alpha = 0.5, i.e. toward the least committal blend
            if score > best[0] + 1e-9 or (abs(score - best[0]) <= 1e-9 and abs(alpha - 0.5) < abs(best[1] - 0.5)):
                best = (score, float(alpha), clf)

        self._alpha, self._clf = best[1], best[2]
        return {
            "alpha": self._alpha,
            "val_auroc": best[0],
            "n_grid": self.n_grid,
        }

    @staticmethod
    def _blend(alpha: float, zc: np.ndarray, ze: np.ndarray) -> np.ndarray:
        return (alpha * zc + (1.0 - alpha) * ze).reshape(-1, 1)

    def predict_logits(self, df: pd.DataFrame) -> np.ndarray:
        zc = self._z_cross.predict_logits(df)
        ze = self._z_evid.predict_logits(df)
        return self._clf.decision_function(self._blend(self._alpha, zc, ze))

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        z = self.predict_logits(df)
        return 1.0 / (1.0 + np.exp(-z))

    def info(self) -> dict:
        return {"alpha": round(self._alpha, 3)}


# ---------------------------------------------------------------------------
# A4: flat GBM on the six signals plus one-hot metadata (the leakage control)
# ---------------------------------------------------------------------------


@dataclass
class MetadataGBM(SignalModel):
    """Critical control: if this matches RC-Gate, the gate adds nothing.

    Given the same claim-type and generator metadata as RC-Gate, plus all six signals,
    with no gating structure at all. It is reported honestly whatever it scores.
    """

    name: str = "A4"
    n_generators: int = 3
    seed: int = 0
    max_iter: int = 300
    learning_rate: float = 0.08
    max_leaf_nodes: int = 31
    _clf: HistGradientBoostingClassifier | None = field(default=None, repr=False)

    def _x(self, df: pd.DataFrame) -> np.ndarray:
        signals = df[SIGNALS].to_numpy(dtype="float64")
        meta = np.asarray(onehot_meta(df, self.n_generators), dtype="float64")
        return np.hstack([signals, meta])

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg) -> dict:
        self.max_iter = int(cfg.get("baselines.a4_max_iter", self.max_iter))
        self.learning_rate = float(cfg.get("baselines.a4_learning_rate", self.learning_rate))
        self.max_leaf_nodes = int(cfg.get("baselines.a4_max_leaf_nodes", self.max_leaf_nodes))
        self._clf = HistGradientBoostingClassifier(
            max_iter=self.max_iter,
            learning_rate=self.learning_rate,
            max_leaf_nodes=self.max_leaf_nodes,
            early_stopping=False,
            random_state=self.seed,
        ).fit(self._x(train), train["label"].to_numpy())
        return {"val_auroc": auroc(val["label"].to_numpy(), self.predict_proba(val))}

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self._clf.predict_proba(self._x(df))[:, 1]


# ---------------------------------------------------------------------------
# A8: naive majority vote across judges, only when judge outputs are in the table
# ---------------------------------------------------------------------------


@dataclass
class MajorityVote(SignalModel):
    name: str = "A8"

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg) -> dict:
        for col in ("judge_votes", "judge_n"):
            if col not in train.columns:
                raise KeyError(f"A8 needs {col!r} in the signal table")
        return {"val_auroc": auroc(val["label"].to_numpy(), self.predict_proba(val))}

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        votes = df["judge_votes"].to_numpy(dtype="float64")
        n = np.maximum(df["judge_n"].to_numpy(dtype="float64"), 1.0)
        return np.clip(votes / n, 0.0, 1.0)


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------


def build_baseline(variant: str, cfg, seed: int = 0):
    """Instantiate a baseline by variant id. A5-A7 live in ``models.rcgate``."""
    baselines = cfg.get("baselines", {})
    if variant == "A0":
        return LogisticSignalModel(list(SIGNALS), name="A0", class_weight=baselines.get("a0_class_weight"), seed=seed)
    if variant == "A1":
        return LogisticSignalModel(list(CROSS_SIGNALS), name="A1", class_weight=baselines.get("a1_class_weight"), seed=seed)
    if variant == "A2":
        return LogisticSignalModel(list(EVID_SIGNALS), name="A2", class_weight=baselines.get("a2_class_weight"), seed=seed)
    if variant == "A3":
        return StaticAlphaBlend(name="A3", seed=seed)
    if variant == "A4":
        return MetadataGBM(
            name="A4",
            n_generators=int(cfg.get("model.n_generators", 3)),
            seed=seed,
        )
    if variant == "A8":
        return MajorityVote(name="A8")
    raise ValueError(f"{variant} is not a baseline; use models.rcgate for the gate variants")


def tune_threshold_for(model: SignalModel, val: pd.DataFrame, cfg) -> float:
    return tune_threshold(
        val["label"].to_numpy(),
        model.predict_proba(val),
        quantile=float(cfg.get("eval.threshold_quantile", 0.5)),
    )

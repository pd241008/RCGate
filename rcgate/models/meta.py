"""Fusion head and the prediction record (spec section 6, line 6).

Constraint C5: every inference call returns the gate weights alongside the probability.
:func:`sigmoid` of a bare number is not an acceptable return type anywhere in this
package, so the dataclass is what :meth:`RCGateModel.predict` hands back.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class Prediction:
    """One claim's verdict plus the reasoning that produced it.

    ``prob`` is ``P(hallucinated | claim)``. The remaining fields are not optional
    decoration: ``w_cross`` and ``w_evid`` are the gate's trust weights and must sum to 1,
    and the two expert logits are what those weights are being applied to.
    """

    prob: float
    w_cross: float
    w_evid: float
    z_cross: float
    z_evid: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.prob <= 1.0:
            raise ValueError(f"prob must be in [0, 1], got {self.prob}")

    @property
    def preferred_family(self) -> str:
        """Which signal family the gate trusted more. Used by the one-line explanation."""
        return "evidence" if self.w_evid >= self.w_cross else "cross-model"

    @property
    def margin(self) -> float:
        return self.w_evid - self.w_cross

    def as_dict(self) -> dict[str, float | str]:
        out: dict[str, float | str] = asdict(self)
        out["preferred_family"] = self.preferred_family
        return out


class FusionHead(nn.Module):
    """``Phi = Linear(2 -> 1)`` over ``[w_cross * z_cross, w_evid * z_evid]``.

    By default it carries a bias, which lets the model express a base hallucination rate
    independent of any claim. With ``bias=False`` the output is a pure re-scaling of the
    two weighted expert logits, which is the more literal reading of the spec.
    """

    def __init__(self, in_features: int = 2, bias: bool = True) -> None:
        super().__init__()
        self.linear = nn.Linear(in_features, 1, bias=bias)

    def forward(self, weighted: torch.Tensor) -> torch.Tensor:
        return self.linear(weighted).squeeze(-1)

    @property
    def weight(self) -> torch.Tensor:
        return self.linear.weight.detach().squeeze(-1)


def sigmoid(x: torch.Tensor) -> torch.Tensor:
    return torch.sigmoid(x)


def to_probability(logit: torch.Tensor) -> torch.Tensor:
    return torch.sigmoid(logit)

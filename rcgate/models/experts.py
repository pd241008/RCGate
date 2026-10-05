"""The two signal-family experts (spec section 6, lines 4-5).

Each expert is a single logistic unit over its own three signals, so its logit is
inspectable on its own and can be reported next to the gate weight in an explanation.
"""

from __future__ import annotations

import torch
from torch import nn


class SignalExpert(nn.Module):
    """``Linear(3 -> 1)`` over one signal family. Output is a logit, not a probability."""

    def __init__(self, n_inputs: int = 3) -> None:
        super().__init__()
        self.linear = nn.Linear(n_inputs, 1)

    def forward(self, s: torch.Tensor) -> torch.Tensor:
        if s.dim() != 2:
            raise ValueError(f"expected a (batch, n_signals) tensor, got shape {tuple(s.shape)}")
        return self.linear(s).squeeze(-1)

    @property
    def weight(self) -> torch.Tensor:
        return self.linear.weight.detach().squeeze(-1)

    @property
    def bias(self) -> float:
        return float(self.linear.bias.detach().item())


class CrossModelExpert(SignalExpert):
    """Scores ``[agree, contra, sem_dist]``."""

    def __init__(self) -> None:
        super().__init__(3)


class EvidenceExpert(SignalExpert):
    """Scores ``[support, src_quality, conflict]``."""

    def __init__(self) -> None:
        super().__init__(3)

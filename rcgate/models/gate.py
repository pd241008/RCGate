"""Metadata encoder and gating MLP (spec section 6, lines 1-3).

The gate sees claim syntax and API provenance only. Constraint C1 (black-box only) means
no hidden states, logits or activations from any generator may reach this module, and the
"gate sees signals too" ablation is an explicit, separately named opt-in rather than a
default that could creep in.
"""

from __future__ import annotations

import torch
from torch import nn

from ..data.schema import N_CLAIM_TYPES


class MetadataEncoder(nn.Module):
    """Embed ``claim_type`` and ``generator_id`` separately, then concatenate.

    ``generator_emb`` has ``n_generators + 1`` rows: the extra row is the ``UNK``
    sentinel the gate must handle at cold start (proposal, open challenge 5).
    """

    def __init__(
        self,
        n_generators: int,
        type_dim: int = 4,
        generator_dim: int = 4,
        see_signals: bool = False,
        n_signals: int = 0,
    ) -> None:
        super().__init__()
        self.n_generators = n_generators
        self.unk_index = n_generators
        self.type_dim = type_dim
        self.generator_dim = generator_dim
        self.see_signals = see_signals
        self.n_signals = n_signals if see_signals else 0

        self.type_emb = nn.Embedding(N_CLAIM_TYPES, type_dim) if type_dim else None
        self.gen_emb = nn.Embedding(n_generators + 1, generator_dim) if generator_dim else None

    @property
    def output_dim(self) -> int:
        return self.type_dim + self.generator_dim + self.n_signals

    def forward(
        self,
        claim_type: torch.Tensor,
        generator_id: torch.Tensor,
        signals: torch.Tensor | None = None,
    ) -> torch.Tensor:
        parts = []
        if self.type_emb is not None:
            parts.append(self.type_emb(claim_type))
        if self.gen_emb is not None:
            parts.append(self.gen_emb(generator_id))
        if self.see_signals:
            if signals is None:
                raise ValueError("gate was configured to see signals but none were supplied")
            parts.append(signals)
        return torch.cat(parts, dim=-1)


class Gate(nn.Module):
    """``MLP(d -> hidden -> 2)`` with ReLU, then ``softmax(logits / tau)``.

    ``tau`` comes from config and is held fixed by default: a learned temperature would let
    the model flatten its own weights toward uniform, which is exactly the collapse the
    interpretability claim (H3) is supposed to rule out.
    """

    def __init__(self, in_dim: int, hidden: int = 16, tau: float = 1.0, dropout: float = 0.0) -> None:
        super().__init__()
        if tau <= 0:
            raise ValueError(f"gate temperature tau must be > 0, got {tau}")
        layers: list[nn.Module] = [nn.Linear(in_dim, hidden), nn.ReLU()]
        if dropout > 0:
            layers.append(nn.Dropout(dropout))
        layers.append(nn.Linear(hidden, 2))
        self.net = nn.Sequential(*layers)
        self.tau = float(tau)

    def forward(self, x_meta: torch.Tensor) -> torch.Tensor:
        """Return per-row weights of shape ``(batch, 2)``, columns ``[w_cross, w_evid]``."""
        return torch.softmax(self.net(x_meta) / self.tau, dim=-1)

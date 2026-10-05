"""Model registry: variant id -> instance."""

from __future__ import annotations

from .baselines import (
    LogisticSignalModel,
    MajorityVote,
    MetadataGBM,
    SignalModel,
    StaticAlphaBlend,
    build_baseline,
)

#: Variants implemented as gated models rather than flat baselines.
GATE_VARIANTS = ["A5", "A6", "A7"]

__all__ = [
    "GATE_VARIANTS",
    "LogisticSignalModel",
    "MajorityVote",
    "MetadataGBM",
    "SignalModel",
    "StaticAlphaBlend",
    "build_baseline",
    "build_model",
]


def build_model(variant: str, cfg, seed: int = 0) -> SignalModel:
    """Build any variant. Gate variants are imported lazily to keep import cost low."""
    if variant in GATE_VARIANTS:
        from .rcgate import build_gate_variant

        return build_gate_variant(variant, cfg, seed=seed)
    return build_baseline(variant, cfg, seed=seed)

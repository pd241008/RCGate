"""Registry of every runnable variant, with the plain-language reason each exists.

Table in the spec, section 7. A8 is conditional on judge votes existing in the table.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Canonical order used by reports so rows never shuffle between runs.
ALL_VARIANTS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
DEFAULT_VARIANTS = ["A7"]


@dataclass(frozen=True)
class Variant:
    id: str
    name: str
    purpose: str
    needs_judge_votes: bool = False


VARIANTS: dict[str, Variant] = {
    v.id: v
    for v in [
        Variant("A0", "Flat LR on 6 signals", "naive fusion baseline the project must beat"),
        Variant("A1", "Cross-model only (LR)", "BEACON-style"),
        Variant("A2", "Evidence only (LR)", "Medico-style"),
        Variant("A3", "Static learned alpha blend", "Rowen-style; tests conditioning vs learning"),
        Variant(
            "A4",
            "Flat GBM on 6 signals + metadata",
            "critical control for metadata leakage; report honestly",
        ),
        Variant("A5", "Gate on claim type only", "isolates claim-type contribution"),
        Variant("A6", "Gate on generator only", "isolates generator contribution"),
        Variant("A7", "Full RC-Gate", "proposed method"),
        Variant("A8", "Naive majority vote", "skipped unless judge votes are in the table",
                needs_judge_votes=True),
    ]
}


def describe_variants() -> str:
    lines = []
    for vid in ALL_VARIANTS:
        v = VARIANTS[vid]
        lines.append(f"{vid}  {v.name:<34s} {v.purpose}")
    return "\n".join(lines)


def is_runnable(variant: str, df) -> tuple[bool, str]:
    """A8 needs ``judge_votes``/``judge_n`` columns; everything else always runs."""
    v = VARIANTS[variant]
    if v.needs_judge_votes:
        cols = set(df.columns)
        if not {"judge_votes", "judge_n"}.issubset(cols):
            return False, "no judge outputs in the signal table; A8 skipped by design"
    return True, ""

"""Claim extraction, de-aliasing and claim typing."""

from ..data.schema import CLAIM_TYPE_NAMES
from .claim_type import (
    Classification,
    accuracy_report,
    classify,
    classify_frame,
    numeric_evidence,
    span_overlap,
)
from .dealias import dealias_answer, dealias_claims

__all__ = [
    "CLAIM_TYPE_NAMES",
    "Classification",
    "accuracy_report",
    "classify",
    "classify_frame",
    "dealias_answer",
    "dealias_claims",
    "numeric_evidence",
    "span_overlap",
]

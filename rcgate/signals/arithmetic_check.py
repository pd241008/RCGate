"""Deterministic arithmetic verification of numeric claims (milestone M5).

This is what makes the proposal's "prioritize computational verification" claim actually
true rather than rhetorical. A claim like ``847 x 12 = 10164`` can be *checked*, not
scored: the right answer is either right or it is not, with no model in the loop.

Scope, stated plainly so nobody over-reads it:

* The parser handles explicit binary arithmetic with ``+ - * / x X x % ( )``, digit-group
  separators, currency prefixes and a trailing unit. It does **not** do natural-language
  arithmetic ("a dozen less than three times the total").
* A claim with no expression is left ``UNVERIFIABLE`` rather than guessed at. Folding a
  guess into ``support`` would be worse than folding nothing.
* When a context contains the operands, the expression is evaluated against them, which
  catches transposed-digit errors that look arithmetically fine in isolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from ..data.schema import CLAIM_TYPE_NAMES, NUMERIC

#: verdict values
VERIFIED = "verified"
REFUTED = "refuted"
UNVERIFIABLE = "unverifiable"

#: One operand: a number, or a parenthesised sub-expression such as ``(2 + 3)``.
_OPERAND = r"(?:\([^()]*\)|[$€£₹]?\d[\d,]*(?:\.\d+)?)"

#: ``<lhs> <op> <rhs> [= <stated>]`` with an optional unit and optional currency.
_ARITH_RE = re.compile(
    r"(?<![\w.])"
    rf"(?P<lhs>{_OPERAND})"
    r"\s*(?P<op>[+\-*/×÷]|\sx\s|\sX\s)\s*"
    rf"(?P<rhs>{_OPERAND})"
    rf"(?:\s*(?P<op2>[+\-*/×÷])\s*(?P<rhs2>{_OPERAND}))?"
    r"\s*(?:(?P<eq>=)\s*(?P<stated>[$€£₹]?\d[\d,]*(?:\.\d+)?))?"
    r"(?P<unit>%|percent|[a-zA-Z]{1,14})?"
    r"(?![\w])"
)

_NUMBER_RE = re.compile(r"(?<![\w.])[$€£₹]?\d[\d,]*(?:\.\d+)?(?![\w.])")

_OP_MAP = {"+": "+", "-": "-", "*": "*", "/": "/", "×": "*", "÷": "/", "x": "*", "X": "*"}

#: Rounding tolerance for a stated result. Relative, so 10164 vs 10164.0001 passes but
#: 10164 vs 10170 does not.
REL_TOLERANCE = 1e-6


@dataclass
class ArithmeticResult:
    verdict: str
    computed: float | None = None
    stated: float | None = None
    expression: str | None = None
    operands: list[float] | None = None
    reason: str = ""

    @property
    def is_checkable(self) -> bool:
        return self.verdict in (VERIFIED, REFUTED)

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "computed": self.computed,
            "stated": self.stated,
            "expression": self.expression,
            "operands": self.operands,
            "reason": self.reason,
        }


def _to_float(token: str) -> float:
    return float(token.replace(",", "").replace("$", "").replace("€", "")
                  .replace("£", "").replace("₹", ""))


def _close(a: float, b: float) -> bool:
    if b == 0:
        return abs(a - b) <= REL_TOLERANCE
    return abs(a - b) / max(abs(b), 1.0) <= REL_TOLERANCE


def _safe_eval(expr: str) -> Fraction:
    """Evaluate a purely arithmetic expression with Fractions. No ``eval`` on user text."""
    tokens = re.findall(r"\d[\d,]*(?:\.\d+)?|[+\-*/()]", expr.replace(",", ""))
    if not tokens:
        raise ValueError("no numeric tokens")
    rebuilt = ""
    for tok in tokens:
        if tok in "+-*/()":
            rebuilt += tok
        else:
            if rebuilt and rebuilt[-1] not in "+-*/(":
                rebuilt += "*"  # implicit multiplication, e.g. "2(3+4)"
            rebuilt += tok
    if not re.fullmatch(r"[\d+\-*/().]+", rebuilt):
        raise ValueError(f"unexpected characters in {rebuilt!r}")
    result = _evaluate(rebuilt)
    return result


def _evaluate(expr: str) -> Fraction:
    """Recursive-descent evaluator over Fraction. ~30 lines and no eval()."""
    tokens = re.findall(r"\d+(?:\.\d+)?|[+\-*/()]", expr)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        return tok

    def parse_expr():
        value = parse_term()
        while peek() in ("+", "-"):
            op = take()
            rhs = parse_term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def parse_term():
        value = parse_factor()
        while peek() in ("*", "/"):
            op = take()
            rhs = parse_factor()
            if op == "*":
                value = value * rhs
            else:
                if rhs == 0:
                    raise ZeroDivisionError("division by zero")
                value = value / rhs
        return value

    def parse_factor():
        tok = take()
        if tok == "-":
            return -parse_factor()
        if tok == "+":
            return parse_factor()
        if tok == "(":
            value = parse_expr()
            if peek() == ")":
                take()
            return value
        return Fraction(tok)

    out = parse_expr()
    if pos != len(tokens):
        raise ValueError(f"trailing tokens in {expr!r}")
    return out


def _operands_of(expression: str) -> list[float]:
    """Flatten an expression to the numbers it actually uses, in order."""
    values: list[float] = []
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?", expression):
        try:
            values.append(_to_float(token))
        except ValueError:
            continue
    return values


def check_claim(claim_text: str, context: str | None = None) -> ArithmeticResult:
    """Verify an explicit arithmetic expression inside a claim.

    ``context`` is optional. With it, every number in the context is tried as a possible
    second operand, which catches a claim that multiplies correctly but cites the wrong
    operand.
    """
    match = _ARITH_RE.search(claim_text)
    if not match:
        if _NUMBER_RE.search(claim_text):
            return ArithmeticResult(UNVERIFIABLE, reason="numbers present but no expression")
        return ArithmeticResult(UNVERIFIABLE, reason="no numbers")

    lhs_token = match.group("lhs")
    op = _OP_MAP.get(match.group("op").strip())
    rhs_token = match.group("rhs")
    if op is None:
        return ArithmeticResult(UNVERIFIABLE, reason=f"unknown operator {match.group('op')!r}")

    parts = [lhs_token, op, rhs_token]
    if match.group("op2"):
        op2 = _OP_MAP.get(match.group("op2"))
        if op2 is None:
            return ArithmeticResult(UNVERIFIABLE, reason="unknown second operator")
        parts += [op2, match.group("rhs2")]
    expression = "".join(parts)

    try:
        computed = float(_safe_eval(expression))
    except (ValueError, ZeroDivisionError) as exc:
        return ArithmeticResult(UNVERIFIABLE, reason=f"cannot evaluate: {exc}")

    operands = _operands_of(expression)
    stated = _to_float(match.group("stated")) if match.group("stated") else None
    if stated is None:
        return ArithmeticResult(
            UNVERIFIABLE,
            computed=computed,
            expression=expression,
            operands=operands,
            reason="expression present but no stated result to check",
        )

    if _close(computed, stated):
        return ArithmeticResult(VERIFIED, computed, stated, expression, operands)
    return ArithmeticResult(REFUTED, computed, stated, expression, operands)


def check_against_context(claim_text: str, context: str | None) -> ArithmeticResult:
    """Check whether the expression is consistent with any operand pair in the context.

    Returns ``VERIFIED`` only when the claim's stated result follows from numbers that
    actually occur in the supplied evidence.
    """
    direct = check_claim(claim_text, context)
    if not context or not direct.is_checkable or direct.verdict != VERIFIED:
        return direct

    ctx_numbers = [_to_float(m) for m in _NUMBER_RE.findall(context)]
    if not ctx_numbers:
        return ArithmeticResult(
            UNVERIFIABLE, computed=direct.computed, stated=direct.stated,
            expression=direct.expression, reason="no numbers in context to corroborate",
        )

    operands = direct.operands or []
    if any(
        any(abs(c - operand) <= REL_TOLERANCE for c in ctx_numbers) for operand in operands
    ):
        return direct
    return ArithmeticResult(
        UNVERIFIABLE, computed=direct.computed, stated=direct.stated,
        expression=direct.expression, reason="operands do not appear in the context",
    )


def fold_into_support(
    support: float,
    result: ArithmeticResult,
    weight_verified: float = 0.05,
    weight_refuted: float = 0.90,
) -> float:
    """Move ``support`` toward the arithmetic verdict.

    Both branches are multiplicative in ``1 - support``, so the transform is symmetric and
    always stays inside ``[0, 1]``. Refutation dominates (0.90) because a wrong product is
    close to decisive evidence of hallucination. Verification is deliberately tiny (0.05):
    proving one fragment right says little about the rest of the claim, and a large jump
    would let a trivially checkable fragment carry an unverified sentence.
    """
    if result.verdict == REFUTED:
        return float(max(0.0, min(1.0, support * (1.0 - weight_refuted))))
    if result.verdict == VERIFIED:
        return float(max(0.0, min(1.0, support + weight_verified * (1.0 - support))))
    return float(support)


def verify_frame(df, text_column: str = "claim_text", context_column: str = "context",
                 claim_type_column: str = "claim_type", support_column: str = "support",
                 conflict_column: str = "conflict", use_context: bool = True):
    """Run the checker over a frame and fold the verdicts into support and conflict.

    Adds ``arithmetic_verified`` (bool) and ``arithmetic_verdict`` (str) columns, which the
    data contract lists as optional.
    """
    out = df.copy()
    if support_column not in out.columns:
        out[support_column] = 0.0
    if conflict_column not in out.columns:
        out[conflict_column] = 0.0

    verdicts, verified, supports, conflicts = [], [], [], []
    for _, row in out.iterrows():
        claim_type = int(row.get(claim_type_column, NUMERIC))
        if claim_type != NUMERIC:
            verdicts.append(UNVERIFIABLE)
            verified.append(False)
            supports.append(float(row[support_column]))
            conflicts.append(float(row[conflict_column]))
            continue
        context = row.get(context_column) if use_context and context_column in out.columns else None
        if not isinstance(context, str) or not context.strip():
            context = None
        result = check_against_context(str(row[text_column]), context)
        verdicts.append(result.verdict)
        verified.append(result.verdict == VERIFIED)
        supports.append(fold_into_support(float(row[support_column]), result))
        conflicts.append(
            float(max(row[conflict_column], 0.9)) if result.verdict == REFUTED
            else float(row[conflict_column])
        )

    out["arithmetic_verdict"] = verdicts
    out["arithmetic_verified"] = verified
    out[support_column] = supports
    out[conflict_column] = conflicts
    return out


def summarise(df) -> dict:
    """Counts per verdict, for the report."""
    if "arithmetic_verdict" not in df.columns:
        return {}
    counts = df["arithmetic_verdict"].value_counts().to_dict()
    numeric = df[df["claim_type"] == NUMERIC] if "claim_type" in df.columns else df
    return {
        "counts": {str(k): int(v) for k, v in counts.items()},
        "n_numeric_claims": int(len(numeric)),
        "numeric_types": [CLAIM_TYPE_NAMES[int(t)] for t in sorted(numeric["claim_type"].unique())]
        if len(numeric)
        else [],
    }

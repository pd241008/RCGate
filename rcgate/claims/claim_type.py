"""Rule-based claim typing (milestone M5).

Four types, matching the survey rather than the proposal's three:

    0 numeric      - asserts a quantity, rate, date arithmetic or computed value
    1 entity       - asserts something about a named thing
    2 extractive   - text lifted from the supplied context
    3 abstractive  - a paraphrase or synthesis not present in the context

Rules only. The spec says not to reach for an LLM here unless the rules are clearly
inadequate; ``tests/test_claim_type.py`` measures their accuracy on a hand-labelled sample
so that decision can be made on evidence.

Precedence is the interesting part. A claim copied verbatim from the context can also
contain a number and a proper noun, so "is it a quantity" and "where did it come from" are
different questions. ``rule_order`` in the config decides which wins; the accuracy test is
run under both settings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..data.schema import ABSTRACTIVE, ENTITY, EXTRACTIVE, NUMERIC

# -- lexical resources --------------------------------------------------------

UNITS = [
    "percent", "per cent", "%", "percentage points", "basis points", "bps",
    "million", "billion", "trillion", "thousand", "lakh", "crore",
    "tonne", "tonnes", "ton", "tons", "kilogram", "kg", "gram", "g",
    "litre", "litres", "liter", "liters", "gallon", "ml", "l",
    "metre", "meter", "meters", "metres", "km", "kilometre", "kilometres", "mile", "miles",
    "cm", "mm", "foot", "feet", "inch", "inches", "yard",
    "second", "seconds", "minute", "minutes", "hour", "hours", "day", "days",
    "week", "weeks", "month", "months", "quarter", "quarters", "year", "years",
    "celsius", "fahrenheit", "kelvin", "watt", "watts", "kw", "mw", "gw", "kwh", "mwh",
    "volt", "volts", "amp", "amps", "ohm", "joule", "joules", "calorie", "calories",
    "usd", "eur", "gbp", "inr", "jpy", "dollar", "dollars", "euro", "euros", "pound",
    "shares", "share", "units", "unit", "seats", "employees", "staff", "customers",
    "degrees", "degree", "points", "point", "bp", "kbps", "mbps", "gbps",
]

OPERATORS = ["+", "-", "*", "/", "×", "÷", "=", "%", "^", "±", "<", ">", "≤", "≥"]

RATIO_WORDS = [
    "increase", "decrease", "growth", "decline", "rise", "rose", "fell", "fall",
    "ratio", "rate", "share", "average", "mean", "median", "total", "sum",
    "difference", "times", "per", "percent", "percentage", "margin", "yield",
    "up", "down", "higher", "lower", "more", "less", "fewer", "greater",
]

#: Cardinal number words. Ordinals ("first", "second", "fifth") and vague multipliers
#: ("half", "double", "triple") are deliberately excluded: "in the second half" and "the
#: second-largest" are not quantity assertions, and including them put eight of the
#: hand-labelled abstractive claims into the numeric class.
NUMBER_WORDS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "million", "billion", "trillion",
]

#: A number token: digits with separators, decimals, or a number word.
NUM_RE = re.compile(
    r"(?<!\w)(?:[$€£₹]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[$€£₹]?\d+(?:\.\d+)?)(?!\w)"
)
#: A computed expression such as ``847 * 12`` or ``847 × 12``. A spaced ASCII ``x`` is
#: accepted because real answers write multiplication that way, but only when spaced.
MATH_EXPR_RE = re.compile(
    r"(?<![\w.])\d[\d,\.]*\s*(?:[+\-*/×÷]|\s[xX]\s)\s*\d[\d,\.]*\s*(?:[+\-*/×÷]|\s[xX]\s)?\d[\d,\.]*"
    r"(?:\s*(?:%|[a-zA-Z]{1,12}))?"
)
RANGE_RE = re.compile(
    r"(?<![\w.])[$€£₹]?\d[\d,\.]*\s*(?:-|–|to|and)\s*[$€£₹]?\d[\d,\.]*(?![\w.])"
)
YEAR_RE = re.compile(r"\b(1[6-9]\d{2}|20\d{2})\b")
PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|per\s+cent)(?!\w)")

#: Units that only ever appear as calendar words. "updated in 2019" is not a quantity.
TEMPORAL_UNITS = {
    "second", "seconds", "minute", "minutes", "hour", "hours", "day", "days",
    "week", "weeks", "month", "months", "quarter", "quarters", "year", "years",
}

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "is", "are", "was", "were",
    "be", "been", "by", "with", "from", "as", "that", "this", "these", "those", "it",
    "its", "and", "or", "but", "which", "who", "whom", "whose", "there", "their",
    "they", "he", "she", "his", "her", "has", "have", "had", "will", "would", "can",
    "could", "should", "not", "no", "than", "then", "when", "while", "during", "over",
    "about", "into", "up", "down", "out", "so", "such", "also", "both", "each", "any",
}

#: A word-ish token. The trailing "." is only kept when digits follow it, so a sentence
#: final period never glues onto the last token: an earlier version produced "15.1%." in a
#: claim and "15.1%" in its context, which silently defeated every extractive match.
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-/]*(?:\.[0-9]+)?%?", re.IGNORECASE)


def content_words(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(text.lower()) if w not in STOPWORDS and len(w) > 1]


def _normalise(text: str) -> str:
    """Collapse whitespace and unify quote/dash variants so span matching is not brittle."""
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


# -- individual rules ---------------------------------------------------------


def _find_units(text: str) -> list[str]:
    """Units present, ignoring capitalised matches.

    "the River Kelvin" is a place, not a temperature: a unit written as a proper noun is
    not a unit. Units are conventionally lowercase, so a capitalised match is discarded.
    Symbolic units (``%``) are always accepted.
    """
    low = _normalise(text)
    found: list[str] = []
    for unit in UNITS:
        for match in re.finditer(rf"(?<!\w){re.escape(unit)}(?!\w)", low, re.IGNORECASE):
            original = text[match.start() : match.end()]
            symbolic = not original[:1].isalpha()
            if symbolic or original[:1].islower():
                found.append(unit)
                break
    return found


#: Evidence strength by hit type.
HIT_STRENGTH = {
    "digit": 2.0,
    "expression": 3.0,
    "range": 2.5,
    "percentage": 2.5,
    "unit": 1.0,
    "ratio": 1.0,
    "bare_year": 0.0,
    "number_word": 1.0,
}


def numeric_evidence(text: str) -> dict[str, object]:
    """How strongly this claim reads as an assertion about a quantity.

    Three things are deliberately *not* evidence on their own:

    * a bare calendar year -- "The policy was updated in 2019" asserts nothing measurable;
    * a unit with no number beside it -- "the following year", "the second half";
    * a ratio word with no number beside it -- "more complex than the summary suggests",
      "the main constraint on growth".

    Those three alone accounted for 12 of the 21 initial misclassifications. Quantities are
    claims about magnitudes, and a magnitude needs a magnitude token.
    """
    low = _normalise(text)
    numbers = NUM_RE.findall(text)
    years = YEAR_RE.findall(text)

    # The only numbers present are bare years -> temporal, not quantitative.
    only_years = bool(years) and all(n.strip() in {y for y in years} for n in numbers)
    has_number = bool(numbers) and not only_years

    hits: list[str] = []
    if has_number:
        hits.append("digit")
    if MATH_EXPR_RE.search(text):
        hits.append("expression")
    if RANGE_RE.search(text):
        hits.append("range")
    if PERCENT_RE.search(text):
        hits.append("percentage")
    if only_years:
        hits.append("bare_year")

    number_words = [w for w in NUMBER_WORDS if re.search(rf"\b{re.escape(w)}\b", low)]
    has_number_word = bool(number_words) and not only_years

    units = _find_units(text)
    if units and (has_number or has_number_word):
        measure_units = [u for u in units if u not in TEMPORAL_UNITS or not only_years]
        if measure_units:
            hits.append("unit:" + ",".join(measure_units[:3]))

    ratio = [w for w in RATIO_WORDS if re.search(rf"\b{re.escape(w)}\b", low)]
    if ratio and (has_number or has_number_word):
        hits.append("ratio:" + ",".join(ratio[:3]))

    if number_words and not has_number:
        hits.append("number_word:" + ",".join(number_words[:2]))

    strength = sum(HIT_STRENGTH.get(h.split(":")[0], 0.0) for h in hits)
    return {"hits": hits, "strength": strength}


def proper_nouns(text: str) -> list[str]:
    """Capitalised tokens that are not simply the first word of the claim."""
    tokens = re.findall(r"[A-Za-z][\w'\-]*", text)
    found: list[str] = []
    for i, tok in enumerate(tokens):
        if i == 0:
            continue
        if tok[:1].isupper() and tok.lower() not in _common_lowercase:
            found.append(tok)
    # ALLCAPS acronyms of 2+ letters count as proper nouns too.
    found += [t for t in re.findall(r"\b[A-Z]{2,}\b", text)]
    seen: list[str] = []
    for t in found:
        if t not in seen:
            seen.append(t)
    return seen


_common_lowercase = {
    "the", "a", "an", "it", "they", "this", "that", "these", "those", "he", "she",
    "in", "on", "at", "to", "for", "of", "and", "or", "but", "was", "were", "is",
    "are", "be", "been", "by", "with", "from", "as", "its", "his", "her", "their",
    "we", "our", "you", "your", "i", "my", "not", "no", "if", "when", "while",
    "however", "therefore", "although", "there", "then", "than", "so", "such",
}


def span_overlap(claim_text: str, context: str | None, min_words: int = 5) -> dict[str, object]:
    """How much of the claim is copied verbatim out of the context.

    ``longest_run`` counts the longest run of *consecutive claim content words* that all
    appear somewhere in the context. It deliberately does **not** require them to be
    adjacent in the context as well: a claim lifted from a passage usually gains or loses
    a connective ("reached", "according to the report"), and demanding context adjacency
    cut the measured extractive recall to 0.53 because a single inserted word broke the run.

    Stopwords and function words are already excluded from both sides by
    :func:`content_words`.
    """
    if not context:
        return {"longest_run": 0, "coverage": 0.0, "matched": []}
    claim_words = content_words(claim_text)
    ctx_words = content_words(context)
    if not claim_words or not ctx_words:
        return {"longest_run": 0, "coverage": 0.0, "matched": []}

    ctx_set = set(ctx_words)
    present = [w for w in claim_words if w in ctx_set]
    coverage = len(present) / len(claim_words)

    best: list[str] = []
    current: list[str] = []
    for word in claim_words:
        if word in ctx_set:
            current.append(word)
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    return {"longest_run": len(best), "coverage": coverage, "matched": best}


# -- classifier ---------------------------------------------------------------

#: Rule precedence. ``extractive`` is tried first on purpose.
#:
#: A claim copied verbatim out of the supplied context is extractive *whatever it talks
#: about*. Twenty-four of the thirty hand-labelled extractive claims contain a quantity
#: ("total output of 847 tonnes across all sites"), and testing ``numeric`` first put all
#: but six of them in the numeric class, dropping extractive recall to 0.20. Provenance is
#: the more fundamental question and it is the one the gate actually needs: a lifted claim
#: is exactly the case where evidence checking works and cross-model agreement does not.
#:
#: The alternative order is measured too, in ``tests/test_claim_type.py``.
DEFAULT_RULE_ORDER = ("extractive", "numeric", "entity", "abstractive")

#: A verbatim span must be this long before "extractive" is allowed to fire. Without a
#: length floor, any claim whose words happen to appear in the context gets called
#: extractive.
MIN_EXTRACTIVE_RUN = 4
MIN_EXTRACTIVE_COVERAGE = 0.85


@dataclass
class Classification:
    claim_type: int
    rule: str
    confidence: float
    evidence: dict = field(default_factory=dict)
    alternatives: dict = field(default_factory=dict)


def classify(claim_text: str, context: str | None = None, rule_order=DEFAULT_RULE_ORDER) -> Classification:
    """Assign one of the four claim types, and say which rule decided it."""
    num = numeric_evidence(claim_text)
    span = span_overlap(claim_text, context, min_words=MIN_EXTRACTIVE_RUN)
    nouns = proper_nouns(claim_text)

    is_lifted = span["longest_run"] >= MIN_EXTRACTIVE_RUN and span["coverage"] >= MIN_EXTRACTIVE_COVERAGE

    scores: dict[str, float] = {
        "numeric": float(num["strength"]),
        "extractive": float(min(1.0, span["coverage"])) if is_lifted else 0.0,
        "entity": min(1.0, 0.35 * len(nouns)),
        "abstractive": 0.2,  # the fallback always has some claim on the text
    }

    chosen = "abstractive"
    for rule in rule_order:
        if rule == "abstractive":
            continue
        if scores[rule] > 0.0:
            chosen = rule
            break

    runner_up = sorted(
        (r for r in scores if r != chosen), key=lambda r: scores[r], reverse=True
    )
    top = scores[chosen]
    second = scores[runner_up[0]] if runner_up else 0.0
    confidence = 0.5 if top <= 0 else float(max(0.0, min(1.0, (top - second) / max(top, 1e-6))))

    name_to_id = {"numeric": NUMERIC, "entity": ENTITY, "extractive": EXTRACTIVE,
                  "abstractive": ABSTRACTIVE}
    return Classification(
        claim_type=name_to_id[chosen],
        rule=chosen,
        confidence=round(confidence, 3),
        evidence={
            "numeric": num,
            "span": span,
            "proper_nouns": nouns[:6],
            "scores": {k: round(v, 3) for k, v in scores.items()},
        },
        alternatives={r: round(scores[r], 3) for r in runner_up},
    )


def classify_frame(df, context_column: str = "context", text_column: str = "claim_text",
                   rule_order=DEFAULT_RULE_ORDER):
    """Add ``claim_type`` (and the deciding rule) to a frame of claims."""
    out = df.copy()
    types, rules, confs = [], [], []
    for _, row in out.iterrows():
        context = row.get(context_column) if context_column in out.columns else None
        if not isinstance(context, str) or not context.strip():
            context = None
        c = classify(str(row[text_column]), context, rule_order=rule_order)
        types.append(c.claim_type)
        rules.append(c.rule)
        confs.append(c.confidence)
    out["claim_type"] = types
    out["claim_type_rule"] = rules
    out["claim_type_confidence"] = confs
    return out


def accuracy_report(labels, predictions) -> dict:
    """Accuracy, per-class recall, and a confusion matrix.

    ``matrix[truth][predicted]``. ``support`` is the row sum, i.e. how many claims were
    actually of that type, so recall is the diagonal over the support.
    """
    labels = list(labels)
    predictions = list(predictions)
    if len(labels) != len(predictions):
        raise ValueError(f"{len(labels)} labels but {len(predictions)} predictions")
    names = ["numeric", "entity", "extractive", "abstractive"]
    matrix = {a: {b: 0 for b in names} for a in names}
    correct = 0
    for truth, pred in zip(labels, predictions, strict=True):
        matrix[names[truth]][names[pred]] += 1
        correct += int(truth == pred)
    support = {name: sum(matrix[name].values()) for name in names}
    return {
        "n": len(labels),
        "accuracy": correct / max(len(labels), 1),
        "confusion": matrix,
        "recall": {name: matrix[name][name] / max(support[name], 1) for name in names},
        "support": support,
    }

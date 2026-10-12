"""Navigation topics for the local library.

These rules are browse aids. They are not ground-truth topic labels, and they are not
RC-Gate's four claim types. A record that matches no rule stays unclassified and remains
searchable.
"""

from __future__ import annotations

import re

TOPIC_NOTE = (
    "Topics are navigation aids from deterministic keyword rules. "
    "They are not ground-truth labels and not RC-Gate's claim types."
)

# (id, label, phrases). Earlier rules win. Multi-word phrases are substrings;
# single words use a boundary so "war" does not match "warning".
_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "logic",
        "Logic and game theory",
        (
            "nash",
            "equilibrium",
            "game theory",
            "minimax",
            "maximin",
            "prisoner",
            "pareto",
            "syllogism",
            "zero-sum",
            "zero sum",
        ),
    ),
    (
        "law",
        "Law and government",
        (
            "supreme court",
            "constitution",
            "amendment",
            "congress",
            "senate",
            "statute",
            "lawsuit",
            "legal",
            "legislation",
            "government",
            "election",
            "parliament",
            "treaty",
            "citizenship",
            "supreme court",
            "federal court",
            "appeals court",
            "district court",
            "court ruled",
            "the court",
        ),
    ),
    (
        "mathematics",
        "Mathematics and calculations",
        (
            "how many",
            "how much",
            "how long",
            "calculate",
            "calculation",
            "average",
            "percent",
            "percentage",
            "mph",
            "miles per",
            "equation",
            "formula",
            "multiplied",
            "divided",
            "square root",
            "ratio",
        ),
    ),
    (
        "science",
        "Science and medicine",
        (
            "symptom",
            "disease",
            "cancer",
            "virus",
            "vaccine",
            "medical",
            "medicine",
            "dna",
            "gene",
            "protein",
            "chemical",
            "physics",
            "climate",
            "planet",
            "species",
            "bacteria",
            "infection",
            "anatomy",
            "calorie",
            "vitamin",
            "magnesium",
            "potassium",
            "calcium",
            "hospital",
            "patient",
        ),
    ),
    (
        "people",
        "People and biography",
        (
            "who is",
            "who was",
            "biography",
            "born in",
            "died in",
            "actor",
            "actress",
            "singer",
            "author",
            "prime minister",
        ),
    ),
    (
        "geography",
        "Geography and places",
        (
            "capital of",
            "country",
            "river",
            "mountain",
            "population",
            "continent",
            "where is",
            "located in",
            "border",
            "ocean",
            "island",
        ),
    ),
    (
        "history",
        "History and society",
        (
            "civil war",
            "world war",
            "holocaust",
            "revolution",
            "empire",
            "ancient",
            "dynasty",
            "colonial",
            "medieval",
            "century",
            "historical",
            "battle",
            "war",
            "king",
            "queen",
            "slavery",
        ),
    ),
    (
        "everyday",
        "Everyday facts",
        (
            "how to",
            "how do i",
            "how can i",
            "phone number",
            "recipe",
            "tips",
            "pros and cons",
            "what is the difference",
            "clean",
            "remove",
            "best way",
        ),
    ),
)

_BY_ID = {topic_id: label for topic_id, label, _phrases in _RULES}
_BY_ID["summarization"] = "Summarization"
_BY_ID["reviews"] = "Reviews and data-to-text"
_BY_ID["other"] = "Other or unclassified"

TOPIC_ORDER = [topic_id for topic_id, _label, _phrases in _RULES] + [
    "summarization",
    "reviews",
    "other",
]


def topic_label(topic_id: str) -> str:
    return _BY_ID.get(topic_id, _BY_ID["other"])


def _hit(text: str, phrase: str) -> bool:
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def assign_topic(task_type: str, text: str) -> tuple[str, str]:
    """Return ``(topic_id, label)`` for one source.

    Every Data-to-text record is a Yelp business overview, so those records use the
    reviews category directly. Summary and QA records use the keyword list, then a
    task fallback. Nothing is dropped.
    """
    if task_type == "Data2txt":
        return "reviews", _BY_ID["reviews"]
    lowered = (text or "").lower()
    for topic_id, label, phrases in _RULES:
        if any(_hit(lowered, phrase) for phrase in phrases):
            return topic_id, label
    if task_type == "Summary":
        return "summarization", _BY_ID["summarization"]
    return "other", _BY_ID["other"]

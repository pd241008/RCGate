"""Pronoun de-aliasing for extracted claims (milestone M5).

An LLM asked for atomic claims returns sentences full of "it", "they", "he" and "the
company". Left alone, every signal computed downstream (NLI, BM25, embedding similarity)
retrieves the wrong antecedent and the claim becomes unverifiable. This module rewrites
those references using the question and the preceding sentences of the same answer.

Only the pronoun *subject* is resolved. Possessives and demonstratives are handled
conservatively: an ambiguous one is left as-is and reported, never guessed, because a
silently wrong antecedent is worse than an obvious gap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Third-person pronouns, mapped to the grammatical role we need an antecedent for.
SUBJECT_PRONOUNS = {
    "it": "thing",
    "they": "plural",
    "he": "person",
    "she": "person",
    "him": "person",
    "her": "person",
    "them": "plural",
    "his": "person",
    "their": "plural",
    "its": "thing",
}

#: Reflexive and demonstrative forms.
OTHER_PRONOUNS = {
    "itself": "thing",
    "themselves": "plural",
    "himself": "person",
    "herself": "person",
    "this": None,
    "that": None,
    "these": None,
    "those": None,
    "the former": None,
    "the latter": None,
}

PRONOUN_RE = re.compile(
    r"\b(" + "|".join(sorted(set(SUBJECT_PRONOUNS) | set(OTHER_PRONOUNS), key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

#: Words that look like pronoun subjects but head an organisation or a known entity.
FALSE_FRIENDS = {
    "it": {"italy", "italian"},
}

#: Copular / existential constructions where a pronoun IS the subject and should stay.
KEEP_AS_IS = re.compile(
    r"^\s*(?:there\s+(?:is|are|was|were)|it\s+(?:is|was)\s+(?:not|also|still|true|false)"
    r"|they\s+(?:are|were)\s+(?:not|the\s+only))\b",
    re.IGNORECASE,
)


@dataclass
class Antecedent:
    text: str
    kind: str  # "thing" | "person" | "plural"
    source: str  # "question" | "prior_sentence" | "explicit"
    confident: bool = True


@dataclass
class DealiasResult:
    text: str
    replacements: list[dict] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    @property
    def n_changed(self) -> int:
        return len(self.replacements)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text.strip()) if s.strip()]


def _looks_like_organisation(sentence: str) -> bool:
    """Heuristic for 'the company' / 'Aurora Systems' style subjects."""
    return bool(re.search(r"\b(company|firm|group|bank|corporation|inc\.?|ltd\.?|llc|plc|"
                          r"university|ministry|department|agency|committee|council|"
                          r"government|authority|commission|fund|trust|society|association)\b",
                          sentence, re.IGNORECASE))


def _subject_of(sentence: str) -> Antecedent | None:
    """Guess the grammatical subject of a sentence, with its kind."""
    stripped = re.sub(r"^(?:and|but|so|however|moreover|furthermore|also)\s+", "", sentence.strip(),
                      flags=re.IGNORECASE)
    match = re.match(r"^(?:the\s+|a\s+|an\s+)?([A-Z][\w'\-]*(?:\s+[A-Z][\w'\-]*)*)", stripped)
    if match:
        candidate = match.group(1).strip()
        if candidate.lower() in {"i", "we", "you", "he", "she", "it", "they"}:
            return None
        kind = "person" if _person_like(candidate) else "thing"
        return Antecedent(text=candidate, kind=kind, source="prior_sentence")

    if _looks_like_organisation(stripped):
        head = re.match(r"^(?:the\s+)?([a-z][\w\s]{0,30}?)\b(?=\s+(?:was|were|is|are|has|have|had))",
                        stripped, re.IGNORECASE)
        if head:
            kind = "plural" if head.group(1).strip().endswith("s") else "thing"
            return Antecedent(text=head.group(1).strip(), kind=kind, source="prior_sentence")
    return None


def _person_like(candidate: str) -> bool:
    words = candidate.split()
    if len(words) == 1 and candidate[:1].isupper():
        return False
    titles = {"mr", "mrs", "ms", "dr", "prof", "professor", "sir", "lord", "lady", "senator"}
    return bool(words and words[0].lower().strip(".") in titles) or len(words) >= 2


def find_antecedents(question: str, prior_sentences: list[str]) -> dict[str, Antecedent]:
    """Collect candidate antecedents, nearest first: prior sentences then the question."""
    found: dict[str, Antecedent] = {}
    for sentence in reversed(prior_sentences):
        subject = _subject_of(sentence)
        if subject is None:
            continue
        for pron, kind in SUBJECT_PRONOUNS.items():
            if pron in found:
                continue
            if subject.kind == kind or (kind == "thing" and subject.kind == "thing"):
                found[pron] = Antecedent(subject.text, kind, "prior_sentence")
    q_subject = _subject_of(question) if question else None
    if q_subject is not None:
        for pron, kind in SUBJECT_PRONOUNS.items():
            if pron not in found and (q_subject.kind == kind or pron in ("it", "they")):
                found[pron] = Antecedent(q_subject.text, q_subject.kind, "question")
    return found


def dealias_sentence(
    sentence: str,
    question: str = "",
    prior_sentences: list[str] | None = None,
    resolve: bool = True,
) -> DealiasResult:
    """Rewrite pronoun subjects in one claim sentence.

    ``resolve=False`` returns the sentence unchanged, which is what the ablation wants.
    """
    result = DealiasResult(text=sentence)
    if not resolve or not sentence.strip():
        return result

    if KEEP_AS_IS.match(sentence):
        result.unresolved.append(sentence.strip().split()[0].lower())
        return result

    antecedents = find_antecedents(question, prior_sentences or [])

    def _sub(match: re.Match) -> str:
        word = match.group(0)
        key = word.lower()
        if key in OTHER_PRONOUNS:
            result.unresolved.append(word)
            return word
        ante = antecedents.get(key)
        if ante is None:
            result.unresolved.append(word)
            return word
        replacement = ante.text
        # Match the pronoun's capitalisation so sentence-initial pronouns stay natural.
        if word[:1].isupper():
            replacement = replacement[:1].upper() + replacement[1:]
        result.replacements.append(
            {"from": word, "to": replacement, "source": ante.source, "kind": ante.kind}
        )
        return replacement

    result.text = PRONOUN_RE.sub(_sub, sentence)
    return result


def dealias_claims(
    claims: list[str],
    question: str = "",
    prior_sentences: list[str] | None = None,
    resolve: bool = True,
) -> list[DealiasResult]:
    """De-alias a list of claims that were extracted from one answer.

    Each claim is processed with the sentences that preceded it, so "it" in the third
    claim resolves against the second claim rather than against nothing.
    """
    results: list[DealiasResult] = []
    context_sentences = list(prior_sentences or [])
    for claim in claims:
        results.append(dealias_sentence(claim, question, context_sentences, resolve=resolve))
        context_sentences.append(claim)
    return results


def dealias_answer(answer: str, question: str = "", resolve: bool = True) -> list[DealiasResult]:
    """Split an answer into sentences and de-alias each in order."""
    return dealias_claims(split_sentences(answer), question=question, resolve=resolve)

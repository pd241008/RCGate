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

#: Closed classes that can open a sentence and still not name anything.
#: ``_subject_of`` used to take whatever capitalised token it saw first, so an
#: instruction adverb ("Briefly") or an imperative ("Summarize") became the
#: antecedent for "it". These lists are the grammatical categories, not a
#: denylist of the two words observed in one RAGTruth slice.
QUESTION_WORDS = frozenset({
    "what", "who", "whom", "whose", "which", "when", "where", "why", "how",
})
AUXILIARIES = frozenset({
    "did", "does", "do", "is", "are", "was", "were", "has", "have", "had",
    "can", "could", "should", "would", "will", "may", "might", "shall",
})
INSTRUCTION_ADVERBS = frozenset({
    "briefly", "please", "kindly", "carefully", "simply", "concisely", "shortly", "just",
})
INSTRUCTION_VERBS = frozenset({
    "summarize", "summarise", "answer", "write", "explain", "describe", "list",
    "provide", "give", "tell", "discuss", "outline", "identify", "compare",
    "generate", "produce", "create", "draft", "rewrite", "paraphrase", "extract",
    "respond", "reply",
})
DISCOURSE_FRAMING = frozenset({
    "based", "given", "according", "following", "using", "regarding", "instruction",
})
NON_NOMINAL_HEADS = (
    QUESTION_WORDS | AUXILIARIES | INSTRUCTION_ADVERBS | INSTRUCTION_VERBS | DISCOURSE_FRAMING
    | {"i", "we", "you", "he", "she", "it", "they", "the", "a", "an"}
)
_LEADING_SKIP = NON_NOMINAL_HEADS | {
    "of", "to", "for", "in", "on", "and", "or", "this", "that", "these", "those",
}

#: An instruction clause ends at a colon or a newline. The verb has to be one of
#: the directive verbs above; a capitalised proper name does not match.
_INSTRUCTION_LEAD = re.compile(
    r"^(?:please\s+|kindly\s+|just\s+)?"
    r"(?:briefly\s+|carefully\s+|simply\s+|concisely\s+|shortly\s+)?"
    r"(?:instruction\s*:\s*)?"
    r"(?:summarize|summarise|answer|write|explain|describe|list|provide|give|tell|"
    r"discuss|outline|identify|compare|generate|produce|create|draft|rewrite|"
    r"paraphrase|extract|respond|reply)\b"
    r"[^\n:]{0,240}"
    r"(?::\s*|\n+)",
    re.IGNORECASE,
)
#: RAGTruth prompts paste the evidence after this framing. That text is not the question.
_PASSAGE_CUT = re.compile(
    r"\b(?:bear in mind that|strictly based on the following|based on the following|passage\s*1\s*:)",
    re.IGNORECASE,
)

#: Antecedent rule used by the corrected RAGTruth pipeline. Recorded in the build log.
ANTECEDENT_VERSION = "nominal-question-subject-1"

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


def _is_non_nominal_head(candidate: str) -> bool:
    """True when every token is instruction, discourse, interrogative, or auxiliary.

    A nominal antecedent is an entity or a subject noun. "Briefly", "Summarize",
    "What" and "Based" are not subjects, even though they are capitalised when
    they open a prompt.
    """
    tokens = [tok.lower().strip(".") for tok in candidate.split() if tok.strip(".")]
    return bool(tokens) and all(tok in NON_NOMINAL_HEADS for tok in tokens)


def _subject_of(sentence: str) -> Antecedent | None:
    """Guess the grammatical subject of a sentence, with its kind.

    A leading capitalised token is returned only when it is a nominal. Instruction
    verbs, sentence adverbs, question words and discourse framing fall through
    instead of becoming the antecedent.
    """
    stripped = re.sub(r"^(?:and|but|so|however|moreover|furthermore|also)\s+", "", sentence.strip(),
                      flags=re.IGNORECASE)
    match = re.match(r"^(?:the\s+|a\s+|an\s+)?([A-Z][\w'\-]*(?:\s+[A-Z][\w'\-]*)*)", stripped)
    if match:
        candidate = match.group(1).strip()
        if not _is_non_nominal_head(candidate):
            kind = "person" if _person_like(candidate) else "thing"
            return Antecedent(text=candidate, kind=kind, source="prior_sentence")

    if _looks_like_organisation(stripped):
        head = re.match(r"^(?:the\s+)?([a-z][\w\s]{0,30}?)\b(?=\s+(?:was|were|is|are|has|have|had))",
                        stripped, re.IGNORECASE)
        if head:
            kind = "plural" if head.group(1).strip().endswith("s") else "thing"
            return Antecedent(text=head.group(1).strip(), kind=kind, source="prior_sentence")
    return None


def _instruction_framed(text: str) -> bool:
    return _INSTRUCTION_LEAD.match(text.lstrip()) is not None


def extract_question_payload(question: str) -> str:
    """Drop instruction text and pasted passages, leaving the question clause.

    "Briefly answer the following question: what did Aurora Systems report?"
    yields the question. The passages after "Bear in mind" are evidence, not
    a subject. A prompt that is already a question is returned unchanged.
    """
    text = question.strip()
    if not text:
        return ""
    cut = _PASSAGE_CUT.split(text, maxsplit=1)[0].strip()
    return _INSTRUCTION_LEAD.sub("", cut, count=1).strip()


def _is_pasted_passage(text: str) -> bool:
    """A summary article pasted after the instruction is not a question subject."""
    if not text:
        return False
    if len(text.split()) > 40:
        return True
    return len(split_sentences(text)) >= 3


def _looks_like_question(text: str) -> bool:
    if "?" in text:
        return True
    first = re.match(r"[A-Za-z]+", text.strip())
    return bool(first and first.group(0).lower() in QUESTION_WORDS)


def _scan_proper_subject(text: str) -> Antecedent | None:
    """First proper-name sequence after leading question words and auxiliaries."""
    clause = split_sentences(text)[0] if split_sentences(text) else text
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]*", clause)
    index = 0
    while index < len(tokens) and tokens[index].lower() in _LEADING_SKIP:
        index += 1
    if index >= len(tokens) or not tokens[index][:1].isupper():
        return None
    name = [tokens[index]]
    cursor = index + 1
    while cursor < len(tokens) and tokens[cursor][:1].isupper() and tokens[cursor].lower() not in _LEADING_SKIP:
        name.append(tokens[cursor])
        cursor += 1
    candidate = " ".join(name)
    if _is_non_nominal_head(candidate):
        return None
    kind = "person" if _person_like(candidate) else "thing"
    return Antecedent(text=candidate, kind=kind, source="question")


def question_subject(question: str) -> Antecedent | None:
    """Nominal subject of a question, never an instruction verb or adverb.

    Instruction-framed prompts contribute a subject only from a short question
    clause ("what did Aurora Systems report?"). A news article pasted after
    "Summarize the following..." does not donate its first noun.
    """
    if not question or not question.strip():
        return None
    raw = question.strip()
    framed = _instruction_framed(raw)
    payload = extract_question_payload(raw)
    if not payload:
        return None
    if framed and (_is_pasted_passage(payload) or not _looks_like_question(payload)):
        return None
    if _is_pasted_passage(payload):
        return None
    direct = _subject_of(payload)
    if direct is not None:
        return Antecedent(text=direct.text, kind=direct.kind, source="question")
    return _scan_proper_subject(payload)


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
    q_subject = question_subject(question) if question else None
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

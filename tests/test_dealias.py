"""Pronoun de-aliasing: instruction text is not an antecedent.

The RAGTruth prompts open with "Briefly answer..." and "Summarize the following...".
Those words are directives. A capitalised token at the start of a prompt is an
antecedent only when it names something.
"""

from __future__ import annotations

from rcgate.claims.dealias import dealias_sentence, question_subject

BRIEFLY = (
    "Briefly answer the following question:\n"
    "butcher shop phone number\n"
    "Bear in mind that your response should be strictly based on the following three passages:\n"
    "passage 1: Paris is the capital of France."
)
SUMMARIZE = (
    "Summarize the following news within 80 words:\n"
    "Seventy years ago, Anne Frank died of typhus in a Nazi concentration camp. "
    "The camp was liberated two weeks later. Historians revisited the date."
)
IMPERATIVE = (
    "Instruction: Write an objective overview about the following local business:\n"
    "Aurora Systems sells sensors in three cities."
)


def _text(sentence: str, question: str, prior: list[str] | None = None) -> str:
    return dealias_sentence(sentence, question=question, prior_sentences=prior).text


def test_briefly_is_not_substituted_for_a_pronoun():
    sentence = "Based on the given passages, it can be inferred that the shop is open."
    result = dealias_sentence(sentence, question=BRIEFLY)
    assert "Briefly" not in result.text
    assert result.text == sentence
    assert question_subject(BRIEFLY) is None


def test_summarize_is_not_substituted_for_a_pronoun():
    sentence = "It describes the last weeks of the diarist."
    result = dealias_sentence(sentence, question=SUMMARIZE)
    assert "Summarize" not in result.text
    assert result.text == sentence


def test_imperative_prompt_does_not_donate_its_verb():
    sentence = "It opened a second workshop in 2019."
    result = dealias_sentence(sentence, question=IMPERATIVE)
    assert "Write" not in result.text.split()
    assert "Instruction" not in result.text
    assert result.replacements == []


def test_a_single_proper_name_in_a_question_still_resolves():
    question = "Briefly answer the following question:\nwhat did France announce?"
    result = dealias_sentence("It revised the forecast.", question=question)
    assert result.text == "France revised the forecast."
    assert "Briefly" not in result.text


def test_a_proper_name_that_is_not_the_subject_is_not_grabbed():
    """'France' is a modifier here, not the subject. Do not mine the question for it."""
    question = "What is the capital of France?"
    result = dealias_sentence("It has been the seat of government for centuries.", question=question)
    assert "France" not in result.text
    assert result.replacements == []


def test_a_named_entity_in_the_question_is_still_an_antecedent():
    question = "What did Aurora Systems report?"
    result = dealias_sentence("It raised full-year guidance.", question=question)
    assert result.text == "Aurora Systems raised full-year guidance."
    assert result.replacements[0]["source"] == "question"
    assert question_subject(question).text == "Aurora Systems"


def test_a_question_subject_still_resolves_when_the_prompt_is_a_declarative():
    question = "Aurora Systems filed its annual accounts."
    result = dealias_sentence("It disclosed a loss.", question=question)
    assert result.text == "Aurora Systems disclosed a loss."


def test_an_instruction_wrapped_question_still_resolves_its_named_subject():
    question = (
        "Briefly answer the following question:\n"
        "what did Aurora Systems report?\n"
        "Bear in mind that your response should be strictly based on the following passages:\n"
        "passage 1: guidance was raised."
    )
    result = dealias_sentence(
        "Based on the given passages, it can be inferred that guidance changed.",
        question=question,
    )
    assert "Briefly" not in result.text
    assert result.text.startswith("Based on the given passages, Aurora Systems can be inferred")


def test_a_prior_sentence_subject_beats_the_question():
    result = dealias_sentence(
        "It revised the outlook.",
        question="What did Aurora Systems report?",
        prior_sentences=["Bellweather published the figures."],
    )
    assert result.text == "Bellweather revised the outlook."
    assert result.replacements[0]["source"] == "prior_sentence"


def test_ambiguous_demonstratives_stay_unresolved():
    result = dealias_sentence("This increased costs.", question="What did Aurora Systems report?")
    assert result.text == "This increased costs."
    assert result.replacements == []
    assert result.unresolved


def test_no_antecedent_leaves_the_pronoun_in_place():
    result = dealias_sentence("It rose.", question="Briefly answer the following question:\nhow to cook rice")
    assert result.text == "It rose."
    assert result.replacements == []

    bare = dealias_sentence("It rose.", question="")
    assert bare.text == "It rose."
    assert bare.replacements == []


def test_discourse_framing_in_a_prior_sentence_is_not_an_entity():
    result = dealias_sentence(
        "It can be checked against the filing.",
        question="",
        prior_sentences=["Based on the given passages, revenue rose."],
    )
    assert "Based" not in result.text
    assert result.text == "It can be checked against the filing."

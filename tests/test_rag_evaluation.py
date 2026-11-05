import pytest

from rag_answer import PetCareAnswerService
from rag_retrieval import KnowledgeBase


EVALUATION_CASES = [
	(
		"What scratching options are suitable for a cat?",
		"cat",
		"cat-enrichment-scratching",
		"stable scratching post",
	),
	(
		"How often should I brush a cat?",
		"cat",
		"cat-grooming-basics",
		"one or two brushings per week",
	),
	(
		"What exercise and play can help a dog stay mentally stimulated?",
		"dog",
		"dog-exercise-and-play",
		"mental stimulation",
	),
	(
		"How often should I brush a dog?",
		"dog",
		"dog-grooming-basics",
		"depends on coat type",
	),
]


@pytest.mark.parametrize(
	("query", "species", "expected_document_id", "expected_evidence"),
	EVALUATION_CASES,
)
def test_representative_questions_retrieve_and_cite_expected_evidence(
	monkeypatch,
	query: str,
	species: str,
	expected_document_id: str,
	expected_evidence: str,
) -> None:
	monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
	passages = KnowledgeBase().retrieve(query, species=species)
	answer = PetCareAnswerService().answer(query, species=species)

	assert passages
	assert passages[0].document_id == expected_document_id
	assert answer.status == "answered"
	assert answer.sources
	assert answer.sources[0].document_id == expected_document_id
	assert expected_evidence in answer.answer
	assert answer.sources[0].url in answer.answer
	assert "not veterinary advice" in answer.answer

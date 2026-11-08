from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import rag_answer
from anthropic import APIError
from rag_answer import PetCareAnswerService


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch) -> None:
	monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")


def test_missing_api_key_uses_local_extractive_answer(monkeypatch) -> None:
	monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
	anthropic_factory = Mock()
	monkeypatch.setattr(rag_answer, "Anthropic", anthropic_factory)

	result = PetCareAnswerService().answer("cat scratching post")

	assert result.status == "answered"
	assert result.sources
	assert "Offer cats appropriate places to scratch" in result.answer
	assert result.sources[0].url in result.answer
	assert "not veterinary advice" in result.answer
	assert result.evidence_match_score is not None
	assert 0.0 <= result.evidence_match_score <= 1.0
	anthropic_factory.assert_not_called()


def test_configured_api_key_uses_anthropic_and_cites_retrieved_source(
	monkeypatch,
) -> None:
	monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
	client = Mock()
	client.messages.create.return_value = SimpleNamespace(
		content=[SimpleNamespace(type="text", text="Use a stable scratching post [1].")]
	)
	anthropic_factory = Mock(return_value=client)
	monkeypatch.setattr(rag_answer, "Anthropic", anthropic_factory)
	service = PetCareAnswerService(model="test-model")

	result = service.answer("cat scratching post")

	assert result.status == "answered"
	assert not result.needs_veterinarian
	assert result.sources
	assert result.sources[0].title == "General Cat Care"
	assert result.sources[0].publisher == "ASPCA"
	assert result.sources[0].url.startswith("https://")
	assert "Use a stable scratching post [1]." in result.answer
	assert result.sources[0].url in result.answer
	assert "not veterinary advice" in result.answer
	assert result.evidence_match_score == 1.0
	anthropic_factory.assert_called_once_with(api_key="test-api-key")
	request = client.messages.create.call_args.kwargs
	assert request["model"] == "test-model"
	assert "using only the supplied reviewed source passages" in request["system"]
	assert "cat scratching post" in request["messages"][0]["content"]
	assert "Offer cats appropriate places to scratch" in request["messages"][0]["content"]


def test_anthropic_answer_with_invalid_citation_uses_local_grounded_fallback(
	monkeypatch,
	caplog,
) -> None:
	monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
	client = Mock()
	client.messages.create.return_value = SimpleNamespace(
		content=[SimpleNamespace(type="text", text="Use any product you like [9].")]
	)

	result = PetCareAnswerService(client=client).answer("cat scratching post")

	assert "Offer cats appropriate places to scratch" in result.answer
	assert "[9]" not in result.answer
	assert "invalid passage citations" in caplog.text
	assert result.evidence_match_score is not None


def test_species_filter_is_applied_to_answer() -> None:
	client = Mock()
	client.messages.create.return_value = SimpleNamespace(
		content=[
			SimpleNamespace(
				type="text",
				text="Brushing frequency depends on coat type [1].",
			)
		]
	)
	result = PetCareAnswerService(client=client).answer(
		"grooming routine",
		species="dog",
	)

	assert result.status == "answered"
	assert all(source.document_id.startswith("dog-") for source in result.sources)
	assert "dog-grooming-basics" in {
		source.document_id for source in result.sources
	}


def test_unsupported_question_returns_limitation_without_sources() -> None:
	client = Mock()
	result = PetCareAnswerService(client=client).answer("spacecraft engine repair")

	assert result.status == "insufficient_evidence"
	assert result.sources == ()
	assert result.evidence_match_score is None
	assert "can't answer this from PawPal+'s knowledge base" in result.answer
	client.messages.create.assert_not_called()


@pytest.mark.parametrize(
	"query",
	[
		"Why is my cat vomiting?",
		"Can I give my dog medication?",
		"How do I diagnose this wound?",
	],
)
def test_medical_questions_are_referred_to_veterinarian(query) -> None:
	client = Mock()
	result = PetCareAnswerService(client=client).answer(query)

	assert result.status == "veterinary_referral"
	assert result.needs_veterinarian
	assert result.sources == ()
	assert result.evidence_match_score is None
	assert "contact your veterinarian" in result.answer.lower()
	assert "diagnose" in result.answer.lower()
	client.messages.create.assert_not_called()


@pytest.mark.parametrize(
	"query",
	[
		"My cat swallowed a toy",
		"My dog ate something toxic",
		"My pet is having trouble breathing",
		"My dog is choking",
	],
)
def test_urgent_questions_get_immediate_referral(query) -> None:
	client = Mock()
	result = PetCareAnswerService(client=client).answer(query)

	assert result.status == "veterinary_referral"
	assert result.needs_veterinarian
	assert "now" in result.answer
	assert "don't wait" in result.answer
	client.messages.create.assert_not_called()


def test_empty_question_raises_value_error() -> None:
	with pytest.raises(ValueError, match="Query must not be empty"):
		PetCareAnswerService().answer(" ")


def test_anthropic_empty_response_raises_explicit_error() -> None:
	client = Mock()
	client.messages.create.return_value = SimpleNamespace(content=[])

	with pytest.raises(RuntimeError, match="Anthropic returned no text"):
		PetCareAnswerService(client=client).answer("cat scratching post")


def test_anthropic_api_errors_are_logged_and_not_silently_suppressed(
	caplog,
) -> None:
	client = Mock()
	client.messages.create.side_effect = APIError(
		"provider unavailable",
		request=Mock(),
		body=None,
	)

	with pytest.raises(APIError, match="provider unavailable"):
		PetCareAnswerService(client=client).answer("cat scratching post")
	assert "Anthropic request failed" in caplog.text

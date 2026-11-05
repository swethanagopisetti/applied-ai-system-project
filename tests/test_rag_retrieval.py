import json

import pytest

from rag_retrieval import KNOWLEDGE_BASE_PATH, KnowledgeBase


def test_retrieves_relevant_passages_with_source_metadata() -> None:
	results = KnowledgeBase().retrieve("cat enrichment ideas")

	assert results
	assert results[0].document_id == "cat-enrichment-scratching"
	assert results[0].source_title == "General Cat Care"
	assert results[0].publisher == "ASPCA"
	assert results[0].source_url.startswith("https://")
	assert results[0].source_section == "Scratching; Cat Supply Checklist"
	assert results[0].relevance > 0


def test_species_filter_excludes_other_species() -> None:
	results = KnowledgeBase().retrieve(
		"grooming routine",
		species="CAT",
	)

	assert results
	assert all("cat" in result.species for result in results)
	assert {result.document_id for result in results} == {"cat-grooming-basics"}


def test_results_are_ranked_cut_off_and_limited() -> None:
	knowledge_base = KnowledgeBase()
	results = knowledge_base.retrieve("cat grooming", top_k=1, min_relevance=0.25)

	assert len(results) == 1
	assert results[0].document_id == "cat-grooming-basics"
	assert results[0].relevance >= 0.25
	assert knowledge_base.retrieve(
		"cat grooming symptoms",
		min_relevance=0.75,
	) == []


def test_irrelevant_query_returns_no_passages() -> None:
	assert KnowledgeBase().retrieve("spacecraft engine repair") == []


def test_retrieval_uses_default_dataset_from_any_working_directory() -> None:
	assert KNOWLEDGE_BASE_PATH.is_absolute()
	assert KnowledgeBase().retrieve("dog exercise", species="dog")


@pytest.mark.parametrize(
	("query", "options"),
	[
		("", {}),
		("the and are", {}),
		("cat grooming", {"top_k": 0}),
		("cat grooming", {"min_relevance": 1.1}),
		("cat grooming", {"species": " "}),
	],
)
def test_invalid_retrieval_inputs_raise_value_error(query, options) -> None:
	with pytest.raises(ValueError):
		KnowledgeBase().retrieve(query, **options)


def test_invalid_knowledge_base_schema_raises_value_error(tmp_path) -> None:
	document = json.loads(KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8"))[0]
	document["species"] = "cat"
	path = tmp_path / "invalid.json"
	path.write_text(json.dumps([document]), encoding="utf-8")

	with pytest.raises(ValueError, match="string lists"):
		KnowledgeBase(path)

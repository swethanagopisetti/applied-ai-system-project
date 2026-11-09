import json
import os

import pytest

from rag_retrieval import KNOWLEDGE_BASE_PATH, KnowledgeBase


def _write_custom_document(path, document_id, phrase) -> None:
	document = {
		"document_id": document_id,
		"source_title": "Example Custom Guide",
		"publisher": "Example publisher",
		"source_url": "https://example.org/custom-guide",
		"source_section": "Demonstration only",
		"species": ["dog"],
		"topics": ["enrichment"],
		"reviewed_on": "2026-11-08",
		"content": f"Demonstration custom passage includes {phrase}.",
	}
	path.write_text(json.dumps([document]), encoding="utf-8")


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


@pytest.mark.parametrize(
	("query", "species"),
	[
		("dog walking schedule", "dog"),
		("cat exercise routine", "cat"),
		("cat scratching spaceship", "cat"),
	],
)
def test_weak_or_unmatched_evidence_is_filtered(query, species) -> None:
	assert KnowledgeBase().retrieve(query, species=species) == []


def test_retrieval_uses_default_dataset_from_any_working_directory() -> None:
	assert KNOWLEDGE_BASE_PATH.is_absolute()
	assert KnowledgeBase().retrieve("dog exercise", species="dog")


def test_custom_json_sources_extend_default_retrieval(tmp_path) -> None:
	first_source = tmp_path / "custom_one.json"
	second_source = tmp_path / "custom_two.json"
	_write_custom_document(first_source, "custom-snuffle-mat", "snuffle mat")
	_write_custom_document(second_source, "custom-puzzle-feeder", "puzzle feeder")

	assert KnowledgeBase().retrieve("snuffle mat", species="dog") == []

	knowledge_base = KnowledgeBase(
		[KNOWLEDGE_BASE_PATH, first_source, second_source]
	)
	snuffle_results = knowledge_base.retrieve("snuffle mat", species="dog")
	puzzle_results = knowledge_base.retrieve("puzzle feeder", species="dog")

	assert snuffle_results[0].document_id == "custom-snuffle-mat"
	assert snuffle_results[0].source_title == "Example Custom Guide"
	assert puzzle_results[0].document_id == "custom-puzzle-feeder"


def test_environment_configured_sources_are_added_to_default_dataset(
	tmp_path,
	monkeypatch,
) -> None:
	first_source = tmp_path / "custom_one.json"
	second_source = tmp_path / "custom_two.json"
	_write_custom_document(first_source, "custom-snuffle-mat", "snuffle mat")
	_write_custom_document(second_source, "custom-puzzle-feeder", "puzzle feeder")
	monkeypatch.setenv(
		"PAWPAL_KNOWLEDGE_BASE_PATHS",
		os.pathsep.join((str(first_source), str(second_source))),
	)

	knowledge_base = KnowledgeBase()

	assert knowledge_base.retrieve("dog exercise", species="dog")
	assert knowledge_base.retrieve("snuffle mat", species="dog")[0].document_id == (
		"custom-snuffle-mat"
	)
	assert knowledge_base.retrieve(
		"puzzle feeder",
		species="dog",
	)[0].document_id == "custom-puzzle-feeder"


def test_readme_custom_source_example_is_retrievable() -> None:
	example_path = (
		KNOWLEDGE_BASE_PATH.parent / "example_custom_pet_care.json"
	)
	query = "dog enrichment snuffle mat activity"

	assert KnowledgeBase().retrieve(query, species="dog") == []

	knowledge_base = KnowledgeBase([KNOWLEDGE_BASE_PATH, example_path])
	results = knowledge_base.retrieve(query, species="dog")

	assert results
	assert results[0].document_id == "example-dog-snuffle-mat"
	assert results[0].source_title == "PawPal+ Custom-Source Demo"
	assert "Supervise the dog" in results[0].content


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

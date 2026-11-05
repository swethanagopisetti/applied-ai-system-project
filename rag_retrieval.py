from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


KNOWLEDGE_BASE_PATH = (
	Path(__file__).parent / "data" / "pet_care_knowledge_base.json"
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
	"a",
	"an",
	"and",
	"are",
	"can",
	"for",
	"how",
	"i",
	"in",
	"is",
	"me",
	"my",
	"often",
	"of",
	"some",
	"should",
	"the",
	"to",
	"what",
	"with",
}


@dataclass(frozen=True)
class KnowledgeDocument:
	document_id: str
	source_title: str
	publisher: str
	source_url: str
	source_section: str
	species: tuple[str, ...]
	topics: tuple[str, ...]
	reviewed_on: str
	content: str


@dataclass(frozen=True)
class RetrievedPassage:
	document_id: str
	content: str
	source_title: str
	publisher: str
	source_url: str
	source_section: str
	species: tuple[str, ...]
	topics: tuple[str, ...]
	relevance: float


class KnowledgeBase:
	"""Load and lexically retrieve reviewed passages from the local knowledge base."""

	def __init__(self, path: Path = KNOWLEDGE_BASE_PATH) -> None:
		self._documents = self._load_documents(path)

	@staticmethod
	def _load_documents(path: Path) -> tuple[KnowledgeDocument, ...]:
		raw_documents = json.loads(path.read_text(encoding="utf-8"))
		if not isinstance(raw_documents, list):
			raise ValueError("Knowledge base must contain a JSON list of documents.")

		documents = []
		seen_ids = set()
		required_text_fields = (
			"document_id",
			"source_title",
			"publisher",
			"source_url",
			"source_section",
			"reviewed_on",
			"content",
		)
		for index, raw_document in enumerate(raw_documents):
			if not isinstance(raw_document, dict):
				raise ValueError(f"Knowledge-base document {index} must be an object.")
			for field_name in required_text_fields:
				if not isinstance(raw_document.get(field_name), str) or not raw_document[
					field_name
				].strip():
					raise ValueError(
						f"Knowledge-base document {index} requires non-empty "
						f"text field {field_name!r}."
					)

			document_id = raw_document["document_id"]
			if document_id in seen_ids:
				raise ValueError(f"Duplicate knowledge-base document ID: {document_id}")
			seen_ids.add(document_id)

			species = raw_document.get("species")
			topics = raw_document.get("topics")
			if not _is_string_list(species) or not _is_string_list(topics):
				raise ValueError(
					f"Knowledge-base document {index} must have string lists for "
					"'species' and 'topics'."
				)
			if not raw_document["source_url"].startswith("https://"):
				raise ValueError(
					f"Knowledge-base document {index} must use an HTTPS source URL."
				)

			documents.append(
				KnowledgeDocument(
					document_id=document_id,
					source_title=raw_document["source_title"],
					publisher=raw_document["publisher"],
					source_url=raw_document["source_url"],
					source_section=raw_document["source_section"],
					species=tuple(value.casefold() for value in species),
					topics=tuple(topics),
					reviewed_on=raw_document["reviewed_on"],
					content=raw_document["content"],
				)
			)

		return tuple(documents)

	def retrieve(
		self,
		query: str,
		*,
		species: str | None = None,
		top_k: int = 3,
		min_relevance: float = 0.2,
	) -> list[RetrievedPassage]:
		"""Return the best-matching passages, or an empty list if none meet the cutoff.

		Relevance is the fraction of meaningful query tokens found in the passage
		or its searchable metadata. Retrieval is lexical and does not infer synonyms.
		"""
		if not query.strip():
			raise ValueError("Query must not be empty.")
		if top_k < 1:
			raise ValueError("top_k must be at least 1.")
		if not 0.0 <= min_relevance <= 1.0:
			raise ValueError("min_relevance must be between 0 and 1.")

		normalized_species = species.casefold() if species is not None else None
		if normalized_species is not None and not normalized_species.strip():
			raise ValueError("Species must not be empty when provided.")

		query_tokens = {
			_normalize_token(token)
			for token in _tokens(query)
			if token not in _STOP_WORDS
		}
		if not query_tokens:
			raise ValueError("Query must contain at least one meaningful term.")

		results = []
		for document in self._documents:
			if (
				normalized_species is not None
				and normalized_species not in document.species
			):
				continue

			searchable_text = " ".join(
				(
					document.content,
					document.source_title,
					document.source_section,
					" ".join(document.species),
					" ".join(document.topics),
				)
			)
			matched_tokens = query_tokens.intersection(
				_normalize_token(token) for token in _tokens(searchable_text)
			)
			relevance = len(matched_tokens) / len(query_tokens)
			if relevance < min_relevance:
				continue

			results.append(
				RetrievedPassage(
					document_id=document.document_id,
					content=document.content,
					source_title=document.source_title,
					publisher=document.publisher,
					source_url=document.source_url,
					source_section=document.source_section,
					species=document.species,
					topics=document.topics,
					relevance=relevance,
				)
			)

		results.sort(key=lambda result: (-result.relevance, result.document_id))
		return results[:top_k]


def _is_string_list(value: object) -> bool:
	return isinstance(value, list) and all(
		isinstance(item, str) and item.strip() for item in value
	)


def _tokens(text: str) -> set[str]:
	return set(_TOKEN_PATTERN.findall(text.casefold()))


def _normalize_token(token: str) -> str:
	if len(token) > 5 and token.endswith("ing"):
		return token[:-3]
	return token

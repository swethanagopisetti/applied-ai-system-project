from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


KNOWLEDGE_BASE_PATH = (
	Path(__file__).parent / "data" / "pet_care_knowledge_base.json"
)
KNOWLEDGE_BASE_PATHS_ENV = "PAWPAL_KNOWLEDGE_BASE_PATHS"

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
	"a",
	"an",
	"and",
	"are",
	"can",
	"frequency",
	"for",
	"help",
	"how",
	"i",
	"ideas",
	"in",
	"is",
	"mentally",
	"me",
	"my",
	"often",
	"of",
	"options",
	"some",
	"should",
	"stay",
	"suitable",
	"the",
	"to",
	"what",
	"with",
	"routine",
	"schedule",
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
	"""Load and lexically retrieve reviewed passages from local JSON sources."""

	def __init__(self, path: Path | Iterable[Path] | None = None) -> None:
		if path is None:
			paths = (KNOWLEDGE_BASE_PATH, *self._configured_extra_paths())
		elif isinstance(path, Path):
			paths = (path,)
		else:
			paths = tuple(path)
		if not paths:
			raise ValueError("At least one knowledge-base JSON path is required.")
		self._documents = self._load_documents(paths)

	@staticmethod
	def _configured_extra_paths() -> tuple[Path, ...]:
		configured_paths = os.getenv(KNOWLEDGE_BASE_PATHS_ENV, "").strip()
		if not configured_paths:
			return ()
		path_values = configured_paths.split(os.pathsep)
		if any(not value.strip() for value in path_values):
			raise ValueError(
				f"{KNOWLEDGE_BASE_PATHS_ENV} must contain non-empty paths "
				f"separated by {os.pathsep!r}."
			)
		return tuple(Path(value.strip()) for value in path_values)

	@staticmethod
	def _load_documents(paths: Iterable[Path]) -> tuple[KnowledgeDocument, ...]:
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
		for path in paths:
			raw_documents = json.loads(path.read_text(encoding="utf-8"))
			if not isinstance(raw_documents, list):
				raise ValueError(
					f"Knowledge base {path} must contain a JSON list of documents."
				)

			for index, raw_document in enumerate(raw_documents):
				if not isinstance(raw_document, dict):
					raise ValueError(
						f"Knowledge-base document {index} in {path} must be an object."
					)
				for field_name in required_text_fields:
					if (
						not isinstance(raw_document.get(field_name), str)
						or not raw_document[field_name].strip()
					):
						raise ValueError(
							f"Knowledge-base document {index} in {path} requires "
							f"non-empty text field {field_name!r}."
						)

				document_id = raw_document["document_id"]
				if document_id in seen_ids:
					raise ValueError(
						f"Duplicate knowledge-base document ID: {document_id}"
					)
				seen_ids.add(document_id)

				species = raw_document.get("species")
				topics = raw_document.get("topics")
				if not _is_string_list(species) or not _is_string_list(topics):
					raise ValueError(
						f"Knowledge-base document {index} in {path} must have string "
						"lists for 'species' and 'topics'."
					)
				if not raw_document["source_url"].startswith("https://"):
					raise ValueError(
						f"Knowledge-base document {index} in {path} must use an "
						"HTTPS source URL."
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
		min_relevance: float = 0.6,
	) -> list[RetrievedPassage]:
		"""Return passages with enough overlap in content and relevant topic tags.

		Content matches count fully; topic-tag matches count three-quarters.
		Species and source-title metadata do not increase relevance. Matching is
		lexical and does not infer general synonyms.
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
			if token not in _STOP_WORDS and token not in {"cat", "dog"}
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

			content_tokens = {
				_normalize_token(token) for token in _tokens(document.content)
			}
			topic_tokens = {
				_normalize_token(token)
				for token in _tokens(" ".join(document.topics))
			}
			content_matches = query_tokens.intersection(content_tokens)
			topic_matches = query_tokens.intersection(topic_tokens) - content_matches
			if not (content_matches - {"cat", "dog"} or topic_matches):
				continue
			relevance = (
				len(content_matches) + 0.75 * len(topic_matches)
			) / len(query_tokens)
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
		token = token[:-3]
	if len(token) > 4 and token.endswith("ies"):
		return token[:-3] + "y"
	if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
		return token[:-1]
	return token

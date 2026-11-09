import pytest


@pytest.fixture(autouse=True)
def clear_custom_knowledge_sources(monkeypatch) -> None:
	monkeypatch.delenv("PAWPAL_KNOWLEDGE_BASE_PATHS", raising=False)

import pytest

from src.config import load_config
from src.retriever import Retriever


@pytest.fixture(scope="module")
def retriever():
    return Retriever(load_config())


def test_known_query_finds_right_doc(retriever):
    hits = retriever.retrieve("How do I reset my password?")
    assert hits, "expected hits for an in-domain query"
    assert hits[0]["doc_id"] == "password-reset"


def test_rate_limit_query(retriever):
    hits = retriever.retrieve("What is the API rate limit per minute?")
    assert hits[0]["doc_id"] == "api-rate-limits"


def test_metadata_filter_doc_type(retriever):
    hits = retriever.retrieve("limits", doc_type="reference")
    assert hits, "expected hits when filtering by doc_type"
    assert all(h["doc_type"] == "reference" for h in hits)
    assert any(h["doc_id"] == "api-rate-limits" for h in hits)


def test_metadata_filter_no_match(retriever):
    hits = retriever.retrieve("limits", doc_type="nonexistent-type")
    assert hits == []

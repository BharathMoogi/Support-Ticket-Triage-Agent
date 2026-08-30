"""tests/test_retrieval.py — Unit tests for agent/retrieval.py"""

import pytest
from pathlib import Path
from agent.retrieval import search_docs, chunk_markdown_file, tokenize, get_or_build_index


def test_tokenize_extracts_clean_tokens():
    tokens = tokenize("How do I fix ERR_WS_DISCONNECTED_502 on wss://sync.flowboard.app?")
    assert "err_ws_disconnected_502" in tokens
    assert "sync" in tokens
    assert "how" not in tokens  # stop word


def test_search_docs_returns_relevant_csv_chunk():
    results = search_docs("How to export cards into a CSV spreadsheet?", k=2)
    assert len(results) > 0
    assert results[0]["doc_name"] == "data-export-and-backup.md"
    assert "CSV" in results[0]["content"]


def test_search_docs_returns_refund_policy():
    results = search_docs("Can I get a refund on annual plan after 20 days?", k=2)
    assert len(results) > 0
    assert results[0]["doc_name"] == "refund-policy.md"
    assert "Annual" in results[0]["heading"] or "Refund" in results[0]["heading"]


def test_search_docs_top_k_respected():
    results = search_docs("billing invoice payment", k=1)
    assert len(results) == 1


def test_search_docs_empty_query_returns_empty():
    results = search_docs("", k=3)
    assert results == []

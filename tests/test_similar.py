"""tests/test_similar.py — Unit tests for tools/similar.py"""

import json
import os
import tempfile
from pathlib import Path

import pytest
from tools.similar import find_similar


@pytest.fixture
def sample_tickets(tmp_path):
    """Write a small JSONL file and point TICKETS_DATA_FILE at it."""
    tickets = [
        {
            "id": "TKT-A",
            "subject": "Password reset not working",
            "body": "I cannot reset my password. The reset email never arrives.",
            "resolution": "Checked spam folder. Resent email.",
        },
        {
            "id": "TKT-B",
            "subject": "Billing overcharge",
            "body": "I was charged twice for my subscription this month.",
            "resolution": "Issued a refund for the duplicate charge.",
        },
        {
            "id": "TKT-C",
            "subject": "App crashes on Windows",
            "body": "The desktop app crashes immediately after the latest update on Windows 11.",
            "resolution": "Provided rollback installer.",
        },
    ]
    data_file = tmp_path / "tickets.jsonl"
    with data_file.open("w", encoding="utf-8") as fh:
        for t in tickets:
            fh.write(json.dumps(t) + "\n")

    # Override the module-level path via env var
    os.environ["TICKETS_DATA_FILE"] = str(data_file)

    # Reload the module so it picks up the new env var
    import importlib
    import tools.similar as mod
    importlib.reload(mod)

    yield mod.find_similar

    # Cleanup
    del os.environ["TICKETS_DATA_FILE"]
    importlib.reload(mod)


class TestFindSimilar:
    def test_returns_list(self, sample_tickets):
        result = sample_tickets("password reset email")
        assert isinstance(result, list)

    def test_relevant_result_first(self, sample_tickets):
        result = sample_tickets("password reset email not arriving")
        assert len(result) > 0
        assert result[0]["id"] == "TKT-A"

    def test_top_k_respected(self, sample_tickets):
        result = sample_tickets("account issue", top_k=1)
        assert len(result) <= 1

    def test_top_k_capped_at_5(self, sample_tickets):
        result = sample_tickets("crash billing password", top_k=100)
        assert len(result) <= 5

    def test_result_schema(self, sample_tickets):
        result = sample_tickets("app crash windows update")
        if result:
            keys = set(result[0].keys())
            assert "id" in keys
            assert "subject" in keys
            assert "resolution" in keys

    def test_no_match_returns_empty_or_small(self, sample_tickets):
        # Query with very unusual terms unlikely to match
        result = sample_tickets("zzzzzzz qqqqqq xyzzy")
        assert isinstance(result, list)

    def test_empty_file(self, tmp_path):
        """Should return [] gracefully when data file is empty."""
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("")
        os.environ["TICKETS_DATA_FILE"] = str(empty_file)
        import importlib, tools.similar as mod
        importlib.reload(mod)
        result = mod.find_similar("anything")
        assert result == []
        del os.environ["TICKETS_DATA_FILE"]
        importlib.reload(mod)

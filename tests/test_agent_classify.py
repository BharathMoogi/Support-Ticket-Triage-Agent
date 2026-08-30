"""tests/test_agent_classify.py — Unit tests for agent/classify.py schema and fallbacks"""

import pytest
from agent.classify import CLASSIFICATION_TOOL, classify_ticket


def test_classification_tool_schema():
    props = CLASSIFICATION_TOOL["input_schema"]["properties"]
    assert "category" in props
    assert "urgency" in props
    assert set(props["category"]["enum"]) == {"billing", "bug", "how-to", "other"}
    assert set(props["urgency"]["enum"]) == {"low", "medium", "high"}
    assert set(CLASSIFICATION_TOOL["input_schema"]["required"]) == {"category", "urgency"}


def test_classify_empty_string_returns_fallback():
    result = classify_ticket("")
    assert result == {"category": "other", "urgency": "low"}

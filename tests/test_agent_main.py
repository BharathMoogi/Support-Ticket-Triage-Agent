"""tests/test_agent_main.py — Unit tests for agent/main.py tools and dispatching"""

import pytest
from agent.main import AGENT_TOOLS, _dispatch_tool


def test_agent_tools_schema_definition():
    tool_names = {t["name"] for t in AGENT_TOOLS}
    assert "classify_ticket" in tool_names
    assert "search_docs" in tool_names
    assert "get_customer_context" in tool_names


def test_dispatch_search_docs_tool():
    res = _dispatch_tool("search_docs", {"query": "how to export board CSV", "k": 1}, client=None)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["doc_name"] == "data-export-and-backup.md"


def test_dispatch_get_customer_context_tool():
    res = _dispatch_tool("get_customer_context", {"customer_id": "CUST-101"}, client=None)
    assert isinstance(res, dict)
    assert res["customer_id"] == "CUST-101"
    assert res["plan"] == "Pro"


def test_dispatch_get_customer_context_not_found():
    res = _dispatch_tool("get_customer_context", {"customer_id": "CUST-999"}, client=None)
    assert isinstance(res, dict)
    assert "error" in res


def test_dispatch_unknown_tool():
    res = _dispatch_tool("non_existent_tool", {}, client=None)
    assert isinstance(res, dict)
    assert "error" in res

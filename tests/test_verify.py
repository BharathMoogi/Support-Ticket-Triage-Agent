"""tests/test_verify.py — Unit tests for agent/verify.py schema, formatting, and logic"""

import pytest
from agent.verify import VERIFICATION_TOOL, _format_context_text, verify_draft


def test_verification_tool_schema():
    props = VERIFICATION_TOOL["input_schema"]["properties"]
    assert "is_grounded" in props
    assert "unsupported_claims" in props
    assert "action" in props
    assert set(props["action"]["enum"]) == {"approved", "rewrite_needed", "flag_human_review"}
    assert set(VERIFICATION_TOOL["input_schema"]["required"]) == {"is_grounded", "unsupported_claims", "action", "summary"}


def test_format_context_text_handles_empty():
    text = _format_context_text([], None)
    assert "No documentation was retrieved" in text


def test_format_context_text_includes_chunks_and_profile():
    chunks = [
        {"doc_name": "refund-policy.md", "heading": "Refunds", "content": "14-day policy"}
    ]
    ctx = {"customer_id": "CUST-101", "plan": "Pro", "signup_date": "2025-01-01", "past_ticket_count": 2}
    text = _format_context_text(chunks, ctx)
    assert "refund-policy.md" in text
    assert "14-day policy" in text
    assert "CUST-101" in text
    assert "Pro" in text


def test_verify_empty_draft_flags_review():
    result = verify_draft("", [])
    assert result["is_grounded"] is False
    assert result["action"] == "flag_human_review"

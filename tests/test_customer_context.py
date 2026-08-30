"""tests/test_customer_context.py — Unit tests for agent/customer_context.py"""

import pytest
from agent.customer_context import get_customer_context


def test_lookup_existing_pro_customer():
    ctx = get_customer_context("CUST-101")
    assert ctx is not None
    assert ctx["customer_id"] == "CUST-101"
    assert ctx["plan"] == "Pro"
    assert ctx["signup_date"] == "2025-09-12"
    assert ctx["past_ticket_count"] == 2


def test_lookup_existing_team_customer():
    ctx = get_customer_context("CUST-104")
    assert ctx is not None
    assert ctx["customer_id"] == "CUST-104"
    assert ctx["plan"] == "Team"
    assert ctx["past_ticket_count"] == 4


def test_lookup_case_insensitivity():
    ctx = get_customer_context("cust-114")
    assert ctx is not None
    assert ctx["customer_id"] == "CUST-114"
    assert ctx["plan"] == "Team"
    assert ctx["past_ticket_count"] == 6


def test_lookup_non_existent_customer():
    ctx = get_customer_context("CUST-999")
    assert ctx is None

"""
agent/classification.py — Stub for ticket classification, priority, and routing logic.
To be implemented during the hackathon.
"""

from __future__ import annotations
from typing import Any


def classify_ticket(ticket: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Classify category, SLA priority (P1-P4), and routing destination team
    grounded on ticket content and customer plan tier.
    """
    raise NotImplementedError("Classification module will be implemented during agent build.")

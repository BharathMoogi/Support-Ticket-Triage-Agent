"""
tools/draft_reply.py — Assemble gathered context into a structured bundle.

This tool does NOT write the final reply — Claude composes that from the
bundle returned here. The bundle is logged in the trajectory so the human
reviewer can see exactly what information Claude had access to.
"""

from __future__ import annotations

import textwrap


def build_draft_context(
    summary: str,
    classification: dict,
    similar_tickets: list[dict] | None = None,
    kb_articles: list[dict] | None = None,
) -> dict:
    """
    Bundle triage context for Claude to use when writing the final draft reply.

    Args:
        summary: Condensed ticket summary (from summarize_ticket).
        classification: {category, priority, sentiment} from classify_ticket.
        similar_tickets: List of similar resolved tickets (may be empty).
        kb_articles: List of relevant KB articles (may be empty).

    Returns:
        A structured dict with sections Claude should reference.
    """
    similar_tickets = similar_tickets or []
    kb_articles = kb_articles or []

    similar_section = []
    for t in similar_tickets:
        similar_section.append(
            {
                "id": t.get("id", ""),
                "subject": t.get("subject", ""),
                "resolution": t.get("resolution", ""),
            }
        )

    kb_section = []
    for a in kb_articles:
        kb_section.append(
            {
                "title": a.get("title", ""),
                "excerpt": a.get("excerpt", ""),
                "url": a.get("url", ""),
            }
        )

    return {
        "ticket_summary": summary,
        "classification": classification,
        "similar_resolutions": similar_section,
        "kb_references": kb_section,
        "instruction": (
            "Using the above context, write a professional, empathetic reply "
            "to the customer. Reference specific KB articles or resolutions "
            "where relevant. Do NOT invent facts outside this context."
        ),
    }

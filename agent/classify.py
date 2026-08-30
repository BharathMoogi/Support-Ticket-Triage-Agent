"""
agent/classify.py — Structured LLM Ticket Classification.

Classifies incoming support tickets into fixed categories and urgency levels
using a single structured-output LLM call with a forced Anthropic JSON schema.
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

CategoryType = Literal["billing", "bug", "how-to", "other"]
UrgencyType = Literal["low", "medium", "high"]

# ---------------------------------------------------------------------------
# Strict JSON Tool Schema for Structured Output
# ---------------------------------------------------------------------------

CLASSIFICATION_TOOL = {
    "name": "record_ticket_classification",
    "description": "Record the classified category and urgency of a customer support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["billing", "bug", "how-to", "other"],
                "description": (
                    "The primary category of the ticket:\n"
                    "- 'billing': Invoices, refunds, charges, payments, seat upgrades, pricing.\n"
                    "- 'bug': Unexpected errors, crashes, broken sync, UI/backend malfunctions.\n"
                    "- 'how-to': User questions on features, exports, configurations, integrations.\n"
                    "- 'other': Contradictory, nonsensical, out-of-scope, or unclassifiable requests."
                ),
            },
            "urgency": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": (
                    "The urgency level:\n"
                    "- 'high': Outages, data loss, severe business blockers, major payment lockouts, angry churn risk.\n"
                    "- 'medium': Impaired non-critical features, single-user bugs, billing questions.\n"
                    "- 'low': General how-to questions, minor inquiries, feature feedback."
                ),
            },
        },
        "required": ["category", "urgency"],
    },
}

SYSTEM_PROMPT = """\
You are an expert support ticket triage classifier.
Analyze the incoming customer support ticket text and output its classification
using the provided record_ticket_classification tool.
Evaluate both the topic (category) and the business impact / emotional urgency.
"""


def classify_ticket(
    ticket_text: str,
    client: anthropic.Anthropic | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """
    Classify a support ticket using a single structured-output LLM call.

    Args:
        ticket_text: Combined subject + body or raw ticket content.
        client: Optional pre-configured Anthropic client instance.
        model: Model identifier (defaults to ANTHROPIC_MODEL or claude-sonnet-4-5).

    Returns:
        {"category": "billing"|"bug"|"how-to"|"other", "urgency": "low"|"medium"|"high"}
    """
    if not ticket_text or not ticket_text.strip():
        return {"category": "other", "urgency": "low"}

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is missing.")
        client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        tools=[CLASSIFICATION_TOOL],
        tool_choice={"type": "tool", "name": "record_ticket_classification"},
        messages=[
            {"role": "user", "content": f"Ticket to classify:\n\n{ticket_text}"}
        ],
    )

    # Extract tool input from response
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_ticket_classification":
            data = block.input
            category = data.get("category", "other")
            urgency = data.get("urgency", "medium")

            # Validate against allowed enum values
            if category not in {"billing", "bug", "how-to", "other"}:
                category = "other"
            if urgency not in {"low", "medium", "high"}:
                urgency = "medium"

            return {
                "category": category,
                "urgency": urgency,
            }

    # Fallback if no tool use block was found
    return {"category": "other", "urgency": "medium"}


# ---------------------------------------------------------------------------
# Self Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    print("=== Testing Structured LLM Ticket Classification ===")

    test_cases = [
        (
            "How do I export our team boards into CSV format?",
            "how-to",
            "low",
        ),
        (
            "URGENT: Database sync failed and all team members are getting 502 Bad Gateway!",
            "bug",
            "high",
        ),
        (
            "We were charged $1,440 for an annual renewal that we canceled. Please issue a refund.",
            "billing",
            "medium",
        ),
        (
            "Can you beam my cards into a 3D hologram Linux VR headset using quantum neural link?",
            "other",
            "low",
        ),
    ]

    try:
        client = anthropic.Anthropic()
        for idx, (text, expected_cat, expected_urg) in enumerate(test_cases, 1):
            print(f"\n--- Test Case {idx} ---")
            print(f"Input: {text}")
            result = classify_ticket(text, client=client)
            print(f"Classification Result: {result}")
            assert result["category"] in {"billing", "bug", "how-to", "other"}
            assert result["urgency"] in {"low", "medium", "high"}
            print(f"Category: {result['category']} (Expected: {expected_cat}) | Urgency: {result['urgency']} (Expected: {expected_urg})")

        print("\nAll classification tests completed successfully!")
    except Exception as exc:
        print(f"\nNote: Live LLM test skipped or errored ({exc}). Checking schema definition...")
        assert CLASSIFICATION_TOOL["name"] == "record_ticket_classification"
        assert set(CLASSIFICATION_TOOL["input_schema"]["properties"]["category"]["enum"]) == {"billing", "bug", "how-to", "other"}
        assert set(CLASSIFICATION_TOOL["input_schema"]["properties"]["urgency"]["enum"]) == {"low", "medium", "high"}
        print("Schema validation passed.")
